'''
Copyright 2022 Airbus SAS

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''
from energy_models.core.stream_type.carbon_models.flue_gas import FlueGas
from sos_trades_core.execution_engine.sos_discipline import SoSDiscipline
from sos_trades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sos_trades_core.tools.post_processing.charts.two_axes_instanciated_chart import TwoAxesInstanciatedChart, \
    InstanciatedSeries
import numpy as np

from sos_trades_core.tools.post_processing.tables.instanciated_table import InstanciatedTable


class FlueGasDiscipline(SoSDiscipline):

    # ontology information
    _ontology_data = {
        'label': 'Flue Gas Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-cloud fa-fw',
        'version': '',
    }
    DESC_IN = {'year_start': {'type': 'int', 'default': 2020, 'unit': '[-]', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
               'year_end': {'type': 'int', 'default': 2050, 'unit': '[-]', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
               'technologies_list': {'type': 'string_list', 'possible_values': ['electricity.CoalGen',
                                                                                'electricity.GasTurbine',
                                                                                'electricity.CombinedCycleGasTurbine',
                                                                                'hydrogen.gaseous_hydrogen.WaterGasShift',
                                                                                'liquid_fuel.FischerTropsch',
                                                                                'liquid_fuel.Refinery',
                                                                                'methane.FossilGas',
                                                                                'solid_fuel.Pelletizing',
                                                                                'syngas.CoalGasification',
                                                                                'syngas.Pyrolysis',
                                                                                'fossil.FossilSimpleTechno'],
                                     'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_flue_gas', 'structuring': True},
               'scaling_factor_techno_consumption': {'type': 'float', 'default': 1e3, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public', 'user_level': 2},
               'scaling_factor_techno_production': {'type': 'float', 'default': 1e3, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public', 'user_level': 2}}

    energy_name = FlueGas.name

    DESC_OUT = {'flue_gas_mean': {'type': 'dataframe',
                                  'visibility': SoSDiscipline.SHARED_VISIBILITY,
                                  'namespace': 'ns_flue_gas', 'unit': ''},
                'flue_gas_production': {'type': 'dataframe',
                                        'visibility': SoSDiscipline.SHARED_VISIBILITY,
                                        'namespace': 'ns_flue_gas', 'unit': 'Mt'},
                'flue_gas_prod_ratio': {'type': 'dataframe',
                                        'visibility': SoSDiscipline.SHARED_VISIBILITY,
                                        'namespace': 'ns_flue_gas', 'unit': ''}}

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.energy_model = FlueGas(self.energy_name)
        self.energy_model.configure_parameters(inputs_dict)

    def setup_sos_disciplines(self):
        dynamic_inputs = {}

        if 'technologies_list' in self._data_in:
            techno_list = self.get_sosdisc_inputs('technologies_list')
            if techno_list is not None:
                for techno in techno_list:
                    dynamic_inputs[f'{techno}.techno_production'] = {
                        'type': 'dataframe', 'unit': 'TWh or Mt',
                        'visibility': SoSDiscipline.SHARED_VISIBILITY,
                        'namespace': 'ns_energy_mix'}
                    dynamic_inputs[f'{techno}.flue_gas_co2_ratio'] = {'type': 'array',
                                                                      'visibility': SoSDiscipline.SHARED_VISIBILITY,
                                                                      'namespace': 'ns_energy_mix', 'unit': ''}
        self.add_inputs(dynamic_inputs)

    def run(self):
        # -- get inputs
        inputs_dict = self.get_sosdisc_inputs()
        # -- configure class with inputs
        self.energy_model.configure_parameters_update(inputs_dict)
        # -- compute informations
        flue_gas_mean = self.energy_model.compute()

        outputs_dict = {
            'flue_gas_mean': flue_gas_mean,
            'flue_gas_production': self.energy_model.get_total_flue_gas_production(),
            'flue_gas_prod_ratio': self.energy_model.get_total_flue_gas_prod_ratio()}
        # -- store outputs
        self.store_sos_outputs_values(outputs_dict)

    def compute_sos_jacobian(self):
        '''
             Compute gradient of coupling outputs vs coupling inputs
        '''
        inputs_dict = self.get_sosdisc_inputs()
        technologies_list = inputs_dict['technologies_list']
        mix_weights = self.get_sosdisc_outputs('flue_gas_prod_ratio')

        total_prod = self.get_sosdisc_outputs('flue_gas_production')[
            self.energy_model.name].values
        len_matrix = len(total_prod)

        for techno in technologies_list:

            self.set_partial_derivative_for_other_types(
                ('flue_gas_mean',
                 'flue_gas_mean'), (f'{techno}.flue_gas_co2_ratio',),
                np.reshape(mix_weights[techno].values, (len_matrix, 1)))

            # An array of one value because GEMS needs array
            flue_gas_co2_ratio = self.get_sosdisc_inputs(
                f'{techno}.flue_gas_co2_ratio')[0]

            grad_prod = (
                total_prod - self.energy_model.production[f'{self.energy_model.name} {techno} (Mt)'].values) / total_prod**2

            self.set_partial_derivative_for_other_types(
                ('flue_gas_prod_ratio', techno),
                (f'{techno}.techno_production',
                 f'{self.energy_model.name} (Mt)'),
                inputs_dict['scaling_factor_techno_production'] * np.identity(len_matrix) * grad_prod)

            grad_fluegas_prod = flue_gas_co2_ratio * grad_prod
            for techno_other in technologies_list:
                if techno != techno_other:
                    flue_gas_co2_ratio_other = self.get_sosdisc_inputs(
                        f'{techno_other}.flue_gas_co2_ratio')[0]

                    grad_flue_gas_prod_ratio = -self.energy_model.production[f'{self.energy_model.name} {techno} (Mt)'].values / \
                        total_prod ** 2
                    self.set_partial_derivative_for_other_types(
                        ('flue_gas_prod_ratio', techno),
                        (f'{techno_other}.techno_production',
                         f'{self.energy_model.name} (Mt)'),
                        inputs_dict['scaling_factor_techno_production'] * np.identity(len_matrix) * grad_flue_gas_prod_ratio)

                    grad_fluegas_prod -=  \
                        flue_gas_co2_ratio_other * self.energy_model.production[f'{self.energy_model.name} {techno_other} (Mt)'].values / \
                        total_prod ** 2

            self.set_partial_derivative_for_other_types(
                ('flue_gas_mean', 'flue_gas_mean'),
                (f'{techno}.techno_production',
                 f'{self.energy_model.name} (Mt)'),
                inputs_dict['scaling_factor_techno_production'] * np.identity(len_matrix) * grad_fluegas_prod)

            self.set_partial_derivative_for_other_types(
                ('flue_gas_production', self.energy_model.name),
                (f'{techno}.techno_production',
                 f'{self.energy_model.name} (Mt)'),
                inputs_dict['scaling_factor_techno_production'] * np.identity(len_matrix))

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['Average CO2 concentration in Flue gases',
                      'Technologies CO2 concentration',
                      'Flue gas production']
        chart_filters.append(ChartFilter(
            'Charts', chart_list, chart_list, 'charts'))

        return chart_filters

    def get_post_processing_list(self, filters=None):

        # For the outputs, making a graph for block fuel vs range and blocktime vs
        # range

        instanciated_charts = []
        charts = []
        # Overload default value with chart filter
        if filters is not None:
            for chart_filter in filters:
                if chart_filter.filter_key == 'charts':
                    charts = chart_filter.selected_values

        if 'Flue gas production' in charts:
            new_chart = self.get_flue_gas_production()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'Average CO2 concentration in Flue gases' in charts:
            new_chart = self.get_chart_average_co2_concentration()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'Technologies CO2 concentration' in charts:
            new_chart = self.get_table_technology_co2_concentration()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_flue_gas_production(self):
        flue_gas_total = self.get_sosdisc_outputs(
            'flue_gas_production')[self.energy_name].values
        flue_gas_prod_ratio = self.get_sosdisc_outputs('flue_gas_prod_ratio')
        technologies_list = self.get_sosdisc_inputs('technologies_list')
        years = flue_gas_prod_ratio['years'].values
        chart_name = f'Flue gas emissions by technology'
        new_chart = TwoAxesInstanciatedChart(
            'years', 'Flue gas emissions [Mt]', chart_name=chart_name, stacked_bar=True)

        for techno in technologies_list:
            flue_gas_prod = flue_gas_total * flue_gas_prod_ratio[techno].values
            serie = InstanciatedSeries(
                years.tolist(),
                flue_gas_prod.tolist(), techno.split('.')[-1], 'bar')
            new_chart.series.append(serie)

        serie = InstanciatedSeries(
            years.tolist(),
            flue_gas_total.tolist(), 'Total', 'lines')
        new_chart.series.append(serie)

        return new_chart

    def get_chart_average_co2_concentration(self):
        flue_gas_co2_concentration = self.get_sosdisc_outputs('flue_gas_mean')

        chart_name = f'Average CO2 concentration in Flue gases'
        new_chart = TwoAxesInstanciatedChart(
            'years', 'CO2 concentration [%]', chart_name=chart_name)

        serie = InstanciatedSeries(
            flue_gas_co2_concentration['years'].values.tolist(),
            (flue_gas_co2_concentration['flue_gas_mean'].values * 100).tolist(), f'CO2 concentration', 'lines')

        new_chart.series.append(serie)
        return new_chart

    def get_table_technology_co2_concentration(self):
        table_name = 'Concentration of CO2 in all flue gas streams'
        technologies_list = self.get_sosdisc_inputs('technologies_list')

        headers = ['Technology', 'CO2 concentration']
        cells = []
        cells.append(technologies_list)

        col_data = []
        for techno in technologies_list:
            val_co2 = round(self.get_sosdisc_inputs(
                f'{techno}.flue_gas_co2_ratio')[0] * 100, 2)
            col_data.append([f'{val_co2} %'])
        cells.append(col_data)

        new_table = InstanciatedTable(table_name, headers, cells)

        return new_table
