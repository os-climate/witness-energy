'''
Copyright 2022 Airbus SAS
Modifications on 2023/03/29-2023/11/16 Copyright 2023 Capgemini

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
import numpy as np

from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.stream_disc import StreamDiscipline
from energy_models.glossaryenergy import GlossaryEnergy
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart


class CarbonCaptureDiscipline(StreamDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Carbon Capture Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-air-freshener fa-fw',
        'version': '',
    }

    DESC_IN = {GlossaryEnergy.techno_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                                     'possible_values': CarbonCapture.default_techno_list,
                                     'visibility': 'Shared',
                                     'namespace': 'ns_carbon_capture', 'structuring': True, 'unit': '-'},
               'flue_gas_production': {'type': 'dataframe',
                                       'visibility': 'Shared',
                                       'namespace': 'ns_flue_gas', 'unit': 'Mt',
                                       'dataframe_descriptor': {GlossaryEnergy.Years: ('int', [1900, 2100], False),
                                                                'CO2 from Flue Gas': ('float', None, False)}},
               'flue_gas_prod_ratio': {'type': 'dataframe',
                                       'visibility': 'Shared',
                                       'namespace': 'ns_flue_gas', 'unit': '-',
                                       'dataframe_descriptor': {GlossaryEnergy.Years: ('int', [1900, 2100], False),
                                                                'electricity.CoalGen': ('float', None, True),
                                                                'electricity.GasTurbine': ('float', None, True),
                                                                'electricity.CombinedCycleGasTurbine': (
                                                                'float', None, True),
                                                                'hydrogen.gaseous_hydrogen.WaterGasShift': (
                                                                'float', None, True),
                                                                'liquid_fuel.FischerTropsch': ('float', None, True),
                                                                'liquid_fuel.Refinery': ('float', None, True),
                                                                'methane.FossilGas': ('float', None, True),
                                                                'solid_fuel.Pelletizing': ('float', None, True),
                                                                'syngas.CoalGasification': ('float', None, True),
                                                                'fossil.FossilSimpleTechno': ('float', None, True),
                                                                'carbon_capture.direct_air_capture.AmineScrubbing': (
                                                                'float', None, True),
                                                                'carbon_capture.direct_air_capture.CalciumPotassiumScrubbing': (
                                                                'float', None, True),
                                                                'carbon_capture.direct_air_capture.DirectAirCaptureTechno': (
                                                                'float', None, True),
                                                                }},
               'data_fuel_dict': {'type': 'dict', 'visibility': 'Shared',
                                  'namespace': 'ns_carbon_capture', 'default': CarbonCapture.data_energy_dict,
                                  'unit': 'defined in dict'},
               }

    DESC_IN.update(StreamDiscipline.DESC_IN.copy())

    energy_name = CarbonCapture.name

    DESC_OUT = StreamDiscipline.DESC_OUT.copy()

    DESC_OUT.update({'carbon_captured_type': {'type': 'dataframe', 'unit': 'Mt'},
                'carbon_captured_type_woratio': {'type': 'dataframe', 'unit': 'Mt'}})

    #DESC_OUT.update(StreamDiscipline.DESC_OUT)

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.energy_model = CarbonCapture(self.energy_name)
        self.energy_model.configure_parameters(inputs_dict)

    def run(self):
        '''
        Overwrite run to limit flue gas carbon capture 
        '''

        super().run()

        outputs_dict = {
            'carbon_captured_type': self.energy_model.carbon_captured_type,
            'carbon_captured_type_woratio': self.energy_model.carbon_captured_type_woratio,
        }
        # -- store outputs
        self.store_sos_outputs_values(outputs_dict)

    def compute_sos_jacobian(self):
        '''
             Compute gradient of coupling outputs vs coupling inputs
        '''
        super().compute_sos_jacobian()

        inputs_dict = self.get_sosdisc_inputs()
        outputs_dict = self.get_sosdisc_outputs()
        list_columns_energyprod = list(
            outputs_dict[GlossaryEnergy.EnergyProductionValue].columns)
        list_columns_consumption = list(
            outputs_dict[GlossaryEnergy.EnergyConsumptionValue].columns)
        technologies_list = inputs_dict[GlossaryEnergy.techno_list]
        carbon_captured_type = outputs_dict['carbon_captured_type']
        carbon_captured_type_woratio = outputs_dict['carbon_captured_type_woratio']

        mix_weight = outputs_dict['techno_mix']
        len_matrix = len(carbon_captured_type)
        scaling_factor_energy_production = inputs_dict['scaling_factor_energy_production']
        grad_vs_flue_gas_prod = {column: np.zeros(
            len_matrix) for column in list_columns_consumption if column != GlossaryEnergy.Years}
        grad_vs_flue_gas_prod_woratio = {column: np.zeros(
            len_matrix) for column in list_columns_consumption if column != GlossaryEnergy.Years}
        grad_cons_vs_prod = {column: np.zeros(
            len_matrix) for column in list_columns_consumption if column != GlossaryEnergy.Years}
        grad_cons_vs_prod_woratio = {column: np.zeros(
            len_matrix) for column in list_columns_consumption if column != GlossaryEnergy.Years}
        if self.energy_model.flue_gas_percentage is not None:
            dfluegas = self.energy_model.compute_dflue_gas_with_exp_min(np.divide(
                inputs_dict['flue_gas_production'][CarbonCapture.flue_gas_name].values,
                carbon_captured_type['flue gas'].values,
                out=np.zeros_like(
                    inputs_dict['flue_gas_production'][CarbonCapture.flue_gas_name].values),
                where=carbon_captured_type['flue gas'].values != 0.0))
            dfg_ratio = np.divide(- inputs_dict['flue_gas_production'][
                CarbonCapture.flue_gas_name].values * scaling_factor_energy_production,
                (carbon_captured_type['flue gas'].values)
                ** 2, out=np.zeros_like(
                -inputs_dict['flue_gas_production'][CarbonCapture.flue_gas_name].values),
                where=carbon_captured_type['flue gas'].values != 0.0)
            grad_price_vs_fg_prod = np.zeros(len_matrix)
            grad_price_wotaxes_vs_fg_prod = np.zeros(len_matrix)
        if self.energy_model.flue_gas_percentage_woratio is not None:
            dfluegas_woratio = self.energy_model.compute_dflue_gas_with_exp_min(np.divide(
                inputs_dict['flue_gas_production'][CarbonCapture.flue_gas_name].values,
                carbon_captured_type_woratio['flue gas'].values,
                out=np.zeros_like(
                    inputs_dict['flue_gas_production'][CarbonCapture.flue_gas_name].values),
                where=carbon_captured_type_woratio['flue gas'].values != 0.0))
            dfg_ratio_woratio = np.divide(- inputs_dict['flue_gas_production'][
                CarbonCapture.flue_gas_name].values * scaling_factor_energy_production,
                (carbon_captured_type_woratio['flue gas'].values)
                ** 2, out=np.zeros_like(
                -inputs_dict['flue_gas_production'][CarbonCapture.flue_gas_name].values),
                where=carbon_captured_type_woratio['flue gas'].values != 0.0)

            grad_price_vs_fg_prod = np.zeros(len_matrix)
            grad_price_wotaxes_vs_fg_prod = np.zeros(len_matrix)

        for techno in technologies_list:
            if techno.startswith('direct_air_capture'):
                self.set_partial_derivative_for_other_types(
                    ('carbon_captured_type',
                     'DAC'), (f'{techno}.{GlossaryEnergy.TechnoProductionValue}', f'{CarbonCapture.name} ({CarbonCapture.unit})'),
                    np.identity(len_matrix) * scaling_factor_energy_production)
                self.set_partial_derivative_for_other_types(
                    ('carbon_captured_type_woratio',
                     'DAC'), (f'{techno}.{GlossaryEnergy.TechnoProductionValue}', f'{CarbonCapture.name} ({CarbonCapture.unit})'),
                    np.identity(len_matrix) * scaling_factor_energy_production)
            elif techno.startswith('flue_gas_capture'):
                self.set_partial_derivative_for_other_types(
                    ('carbon_captured_type',
                     'flue gas'), (f'{techno}.{GlossaryEnergy.TechnoProductionValue}', f'{CarbonCapture.name} ({CarbonCapture.unit})'),
                    np.identity(len_matrix) * scaling_factor_energy_production)
                self.set_partial_derivative_for_other_types(
                    ('carbon_captured_type_woratio',
                     'flue gas'), (f'{techno}.{GlossaryEnergy.TechnoProductionValue}', f'{CarbonCapture.name} ({CarbonCapture.unit})'),
                    np.identity(len_matrix) * scaling_factor_energy_production)

                if self.energy_model.flue_gas_percentage is not None:
                    # if the prod of carbon capture is higher than flue gas production then
                    # total production of carbon capture is not influenced by
                    # flue gas capture
                    flue_gas_perc_grad_not_limited = np.where(
                        self.energy_model.flue_gas_percentage < 0.9991, 0.0, 0.9991)
                    flue_gas_perc_grad_limited = np.where(
                        self.energy_model.flue_gas_percentage < 0.9991, 1.0, 0.0)
                    grad_fluegas_limited = self.energy_model.flue_gas_percentage * scaling_factor_energy_production + \
                        carbon_captured_type['flue gas'].values * \
                        dfluegas * dfg_ratio
                    self.set_partial_derivative_for_other_types(
                        ('carbon_captured_type',
                         'flue gas limited'),
                        (f'{techno}.{GlossaryEnergy.TechnoProductionValue}',
                         f'{CarbonCapture.name} ({CarbonCapture.unit})'),
                        np.identity(len_matrix) * grad_fluegas_limited)

                    self.set_partial_derivative_for_other_types(
                        (GlossaryEnergy.LandUseRequiredValue, f'{techno} (Gha)'), (
                            f'{techno}.{GlossaryEnergy.LandUseRequiredValue}', f'{techno} (Gha)'),
                        np.identity(
                            len_matrix) * flue_gas_perc_grad_not_limited
                        + np.identity(len_matrix) * flue_gas_perc_grad_limited * self.energy_model.flue_gas_percentage)
                    list_columnstechnoprod = list(
                        inputs_dict[f'{techno}.{GlossaryEnergy.TechnoProductionValue}'].columns)
                    list_columnstechnocons = list(
                        inputs_dict[f'{techno}.{GlossaryEnergy.TechnoConsumptionValue}'].columns)
                    techno_prod_name_with_unit = [
                        tech for tech in list_columnstechnoprod if tech.startswith(self.energy_name)][0]
                    for column_name in list_columns_energyprod:

                        if column_name != GlossaryEnergy.Years:
                            if column_name == self.energy_name:
                                self.set_partial_derivative_for_other_types(
                                    (GlossaryEnergy.EnergyProductionValue, column_name), (
                                        f'{techno}.{GlossaryEnergy.TechnoProductionValue}', techno_prod_name_with_unit),
                                    np.identity(len_matrix) / scaling_factor_energy_production * grad_fluegas_limited)
                                self.set_partial_derivative_for_other_types(
                                    (GlossaryEnergy.EnergyProductionValue, column_name), (
                                        'flue_gas_production', CarbonCapture.flue_gas_name),
                                    np.identity(len_matrix) / scaling_factor_energy_production * dfluegas)
                            else:
                                for col_technoprod in list_columnstechnoprod:
                                    if column_name == col_technoprod:
                                        self.set_partial_derivative_for_other_types(
                                            (GlossaryEnergy.EnergyProductionValue, column_name), (
                                                f'{techno}.{GlossaryEnergy.TechnoProductionValue}', col_technoprod),
                                            inputs_dict['scaling_factor_techno_production'] * np.identity(
                                                len_matrix) / scaling_factor_energy_production * dfluegas)

                    for column_name in list_columns_consumption:

                        if column_name != GlossaryEnergy.Years:
                            # loop on resources
                            for col_technoprod in list_columnstechnocons:
                                if column_name == col_technoprod:
                                    self.set_partial_derivative_for_other_types(
                                        (GlossaryEnergy.EnergyConsumptionValue, column_name), (
                                            f'{techno}.{GlossaryEnergy.TechnoConsumptionValue}', col_technoprod),
                                        inputs_dict['scaling_factor_techno_consumption'] * np.identity(len_matrix) /
                                        inputs_dict[
                                            'scaling_factor_energy_consumption'] * self.energy_model.flue_gas_percentage)

                                    grad_cons_vs_prod[
                                        column_name] -= inputs_dict[f'{techno}.{GlossaryEnergy.TechnoConsumptionValue}'][
                                        column_name].values / inputs_dict[
                                        'scaling_factor_techno_consumption']
                    # Gradient vs flue gas production
                    for column_name in list_columnstechnocons:
                        if column_name != GlossaryEnergy.Years:
                            grad_vs_flue_gas_prod[column_name] += np.divide(
                                inputs_dict[f'{techno}.{GlossaryEnergy.TechnoConsumptionValue}'][column_name].values,
                                self.energy_model.carbon_captured_type['flue gas'].values *
                                flue_gas_perc_grad_limited,
                                out=np.zeros_like(
                                    inputs_dict[f'{techno}.{GlossaryEnergy.TechnoConsumptionValue}'][column_name].values),
                                where=self.energy_model.carbon_captured_type[
                                    'flue gas'].values * flue_gas_perc_grad_limited != 0)
                else:
                    self.set_partial_derivative_for_other_types(
                        ('carbon_captured_type',
                         'flue gas limited'),
                        (f'{techno}.{GlossaryEnergy.TechnoProductionValue}',
                         f'{CarbonCapture.name} ({CarbonCapture.unit})'),
                        np.identity(len_matrix) * scaling_factor_energy_production)

                # ---_woratio case (had to separate the two conditions)
                if self.energy_model.flue_gas_percentage_woratio is not None:
                    # if the prod of carbon capture is higher than flue gas production then
                    # total production of carbon capture is not influenced by
                    # flue gas capture
                    flue_gas_perc_woratio_grad_limited = np.where(
                        self.energy_model.flue_gas_percentage_woratio < 0.9991, 1.0, 0.0)
                    grad_fluegas_limited_woratio = self.energy_model.flue_gas_percentage_woratio * scaling_factor_energy_production + \
                        carbon_captured_type_woratio['flue gas'].values * \
                        dfluegas_woratio * dfg_ratio_woratio
                    self.set_partial_derivative_for_other_types(
                        ('carbon_captured_type_woratio',
                         'flue gas limited'),
                        (f'{techno}.{GlossaryEnergy.TechnoProductionValue}',
                         f'{CarbonCapture.name} ({CarbonCapture.unit})'),
                        np.identity(len_matrix) * grad_fluegas_limited_woratio)

                    list_columnstechnoprod = list(
                        inputs_dict[f'{techno}.{GlossaryEnergy.TechnoProductionValue}'].columns)
                    list_columnstechnocons = list(
                        inputs_dict[f'{techno}.{GlossaryEnergy.TechnoConsumptionValue}'].columns)
                    techno_prod_name_with_unit = [
                        tech for tech in list_columnstechnoprod if tech.startswith(self.energy_name)][0]

                    for column_name in list_columns_consumption:
                        if column_name != GlossaryEnergy.Years:
                            # loop on resources
                            for col_technoprod in list_columnstechnocons:
                                if column_name == col_technoprod:
                                    self.set_partial_derivative_for_other_types(
                                        (GlossaryEnergy.EnergyConsumptionWithoutRatioValue, column_name), (
                                            f'{techno}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}', col_technoprod),
                                        inputs_dict['scaling_factor_techno_consumption'] * np.identity(len_matrix) /
                                        inputs_dict[
                                            'scaling_factor_energy_consumption'] * self.energy_model.flue_gas_percentage_woratio)
                                    grad_cons_vs_prod_woratio[
                                        column_name] -= inputs_dict[f'{techno}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}'][
                                        column_name].values / inputs_dict[
                                        'scaling_factor_techno_consumption']
                    # Gradient vs flue gas production
                    for column_name in list_columnstechnocons:
                        if column_name != GlossaryEnergy.Years:
                            grad_vs_flue_gas_prod_woratio[column_name] += np.divide(
                                inputs_dict[f'{techno}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}'][column_name].values,
                                self.energy_model.carbon_captured_type_woratio[
                                    'flue gas'].values * flue_gas_perc_woratio_grad_limited, out=np.zeros_like(
                                    inputs_dict[f'{techno}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}'][column_name].values),
                                where=self.energy_model.carbon_captured_type_woratio[
                                    'flue gas'].values * flue_gas_perc_woratio_grad_limited != 0)
                else:
                    self.set_partial_derivative_for_other_types(
                        ('carbon_captured_type_woratio',
                         'flue gas limited'),
                        (f'{techno}.{GlossaryEnergy.TechnoProductionValue}',
                         f'{CarbonCapture.name} ({CarbonCapture.unit})'),
                        np.identity(len_matrix) * inputs_dict['scaling_factor_techno_production'])

            if self.energy_model.flue_gas_percentage is not None:
                mix_weight_techno = mix_weight[techno].values / 100.0

                grad_techno_mix_vs_fg_prod = self.grad_techno_mix_vs_prod_dict[
                    f'fg_prod {techno}']
                #                     grad_techno_mix_vs_prod = (
                #                         outputs_dict[GlossaryEnergy.EnergyProductionValue][self.energy_name].values -
                #                         inputs_dict[f'{techno}.{GlossaryEnergy.TechnoProductionValue}'][column_name].values
                #                     ) / outputs_dict[GlossaryEnergy.EnergyProductionValue][self.energy_name].values**2

                # The mix_weight_techno is zero means that the techno is negligible else we do nothing
                # np.sign gives 0 if zero and 1 if value so it suits well
                # with our needs
                grad_techno_mix_vs_fg_prod = grad_techno_mix_vs_fg_prod * \
                    np.sign(mix_weight_techno)

                self.set_partial_derivative_for_other_types(
                    ('techno_mix', techno), ('flue_gas_production',
                                             CarbonCapture.flue_gas_name),
                    np.identity(len_matrix) * 100.0 * grad_techno_mix_vs_fg_prod)

                grad_price_vs_fg_prod += inputs_dict[f'{techno}.{GlossaryEnergy.TechnoPricesValue}'][techno].values * \
                    grad_techno_mix_vs_fg_prod
                grad_price_wotaxes_vs_fg_prod += inputs_dict[f'{techno}.{GlossaryEnergy.TechnoPricesValue}'][f'{techno}_wotaxes'].values * \
                    grad_techno_mix_vs_fg_prod

        if self.energy_model.flue_gas_percentage is not None:

            self.set_partial_derivative_for_other_types(
                (GlossaryEnergy.EnergyPricesValue, self.energy_name), ('flue_gas_production',
                                                      CarbonCapture.flue_gas_name),
                np.identity(len_matrix) * grad_price_vs_fg_prod)

            self.set_partial_derivative_for_other_types(
                (GlossaryEnergy.EnergyPricesValue, f'{self.energy_name}_wotaxes'), (
                    'flue_gas_production', CarbonCapture.flue_gas_name),
                np.identity(len_matrix) * grad_price_wotaxes_vs_fg_prod)

            self.set_partial_derivative_for_other_types(
                ('carbon_captured_type',
                 'flue gas limited'), (f'flue_gas_production', CarbonCapture.flue_gas_name),
                np.identity(len_matrix) * dfluegas)

            # added
            self.set_partial_derivative_for_other_types(
                ('carbon_captured_type_woratio',
                 'flue gas limited'), (f'flue_gas_production', CarbonCapture.flue_gas_name),
                np.identity(len_matrix) * dfluegas_woratio)

            for column_name in list_columns_consumption:
                if column_name != GlossaryEnergy.Years:
                    self.set_partial_derivative_for_other_types(
                        (GlossaryEnergy.EnergyConsumptionValue, column_name), (
                            'flue_gas_production', CarbonCapture.flue_gas_name),
                        np.identity(len_matrix) * grad_vs_flue_gas_prod[column_name] * dfluegas)
                    for techno_cons in technologies_list:
                        if techno_cons.startswith('flue_gas_capture'):
                            self.set_partial_derivative_for_other_types(
                                (GlossaryEnergy.EnergyConsumptionValue, column_name), (
                                    f'{techno_cons}.{GlossaryEnergy.TechnoProductionValue}', techno_prod_name_with_unit),
                                -np.identity(len_matrix) *
                                inputs_dict['scaling_factor_energy_consumption'] * grad_cons_vs_prod[
                                    column_name] * dfg_ratio * dfluegas)

        if self.energy_model.flue_gas_percentage_woratio is not None:
            for column_name in list_columns_consumption:
                if column_name != GlossaryEnergy.Years:
                    self.set_partial_derivative_for_other_types(
                        (GlossaryEnergy.EnergyConsumptionWithoutRatioValue, column_name), (
                            'flue_gas_production', CarbonCapture.flue_gas_name),
                        np.identity(len_matrix) * grad_vs_flue_gas_prod_woratio[column_name] * dfluegas_woratio)
                    for techno_cons in technologies_list:
                        if techno_cons.startswith('flue_gas_capture'):
                            self.set_partial_derivative_for_other_types(
                                (GlossaryEnergy.EnergyConsumptionWithoutRatioValue, column_name), (
                                    f'{techno_cons}.{GlossaryEnergy.TechnoProductionValue}', techno_prod_name_with_unit),
                                -np.identity(len_matrix) *
                                inputs_dict['scaling_factor_energy_consumption'] * grad_cons_vs_prod_woratio[
                                    column_name] * dfg_ratio_woratio * dfluegas_woratio)

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['Energy price',
                      'Technology mix',
                      GlossaryEnergy.Capital,
                      'Consumption and production',
                      'Flue gas or DAC capture']
        chart_filters.append(ChartFilter(
            'Charts', chart_list, chart_list, 'charts'))

        price_unit_list = ['$/MWh', '$/t']
        chart_filters.append(ChartFilter(
            'Price unit', price_unit_list, price_unit_list, 'price_unit'))

        year_start, year_end = self.get_sosdisc_inputs(
            [GlossaryEnergy.YearStart, GlossaryEnergy.YearEnd])
        years = list(np.arange(year_start, year_end + 1, 5))
        chart_filters.append(ChartFilter(
            'Years for techno mix', years, [year_start, year_end], GlossaryEnergy.Years))
        return chart_filters

    def get_post_processing_list(self, filters=None):

        # For the outputs, making a graph for block fuel vs range and blocktime vs
        # range

        instanciated_charts = []
        charts = []
        price_unit_list = ['$/t']
        unit = 'Mt'
        years_list = [self.get_sosdisc_inputs(GlossaryEnergy.YearStart)]
        # Overload default value with chart filter
        if filters is not None:
            for chart_filter in filters:
                if chart_filter.filter_key == 'charts':
                    charts = chart_filter.selected_values
                if chart_filter.filter_key == 'price_unit':
                    price_unit_list = chart_filter.selected_values
                if chart_filter.filter_key == GlossaryEnergy.Years:
                    years_list = chart_filter.selected_values

        if 'Energy price' in charts and '$/t' in price_unit_list and 'calorific_value' in self.get_sosdisc_inputs(
                'data_fuel_dict'):
            new_chart = self.get_chart_energy_price_in_dollar_kg()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if GlossaryEnergy.Capital in charts:
            chart = self.get_capital_breakdown_by_technos()
            instanciated_charts.append(chart)

        if 'Consumption and production' in charts:
            new_charts = self.get_charts_consumption_and_production_mass_CO2()
            for new_chart in new_charts:
                if new_chart is not None:
                    instanciated_charts.append(new_chart)
            new_charts = self.get_charts_consumption_and_production_mass_resources()
            for new_chart in new_charts:
                if new_chart is not None:
                    instanciated_charts.append(new_chart)
            new_charts = self.get_charts_consumption_and_production_energy()
            for new_chart in new_charts:
                if new_chart is not None:
                    instanciated_charts.append(new_chart)

        if 'Technology mix' in charts:
            new_charts = self.get_chart_technology_mix( years_list)
            for new_chart in new_charts:
                if new_chart is not None:
                    instanciated_charts.append(new_chart)
            new_charts = self.get_charts_production_by_techno(unit)
            for new_chart in new_charts:
                if new_chart is not None:
                    instanciated_charts.append(new_chart)
        if 'Flue gas or DAC capture' in charts:
            new_chart = self.get_chart_flue_gas_limit()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_chart_energy_price_in_dollar_kwh(self):
        energy_prices = self.get_sosdisc_outputs(GlossaryEnergy.EnergyPricesValue)
        chart_name = f'Detailed prices of {self.energy_name} mix over the years'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'Prices [$/kWh]', chart_name=chart_name)

        serie = InstanciatedSeries(
            energy_prices[GlossaryEnergy.Years].values.tolist(),
            energy_prices[self.energy_name].values.tolist(), f'{self.energy_name} mix price', 'lines')

        new_chart.series.append(serie)

        technology_list = self.get_sosdisc_inputs(GlossaryEnergy.techno_list)

        for technology in technology_list:
            techno_price = self.get_sosdisc_inputs(
                f'{technology}.{GlossaryEnergy.TechnoPricesValue}')
            serie = InstanciatedSeries(
                energy_prices[GlossaryEnergy.Years].values.tolist(),
                techno_price[technology].values.tolist(), f'{technology} price', 'lines')
            new_chart.series.append(serie)

        return new_chart

    def get_chart_energy_price_in_dollar_kg(self):
        energy_prices = self.get_sosdisc_outputs(GlossaryEnergy.EnergyPricesValue)
        cut_energy_name = self.energy_name.split(".")
        display_energy_name = cut_energy_name[len(
            cut_energy_name) - 1].replace("_", " ")
        chart_name = f'Detailed prices of {display_energy_name} mix over the years'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'Prices [$/t]', chart_name=chart_name)
        total_price = energy_prices[self.energy_name].values * \
            self.get_sosdisc_inputs('data_fuel_dict')['calorific_value']
        serie = InstanciatedSeries(
            energy_prices[GlossaryEnergy.Years].values.tolist(),
            total_price.tolist(), f'{display_energy_name} mix price', 'lines')

        new_chart.series.append(serie)

        technology_list = self.get_sosdisc_inputs(GlossaryEnergy.techno_list)

        for technology in technology_list:
            techno_price = self.get_sosdisc_inputs(
                f'{technology}.{GlossaryEnergy.TechnoPricesValue}')
            cut_technology_name = technology.split(".")
            display_technology_name = cut_technology_name[len(
                cut_technology_name) - 1].replace("_", " ")
            techno_price_kg = techno_price[technology].values * \
                self.get_sosdisc_inputs('data_fuel_dict')['calorific_value']
            serie = InstanciatedSeries(
                energy_prices[GlossaryEnergy.Years].values.tolist(),
                techno_price_kg.tolist(), f'{display_technology_name} price', 'lines')
            new_chart.series.append(serie)

        return new_chart

    def get_charts_consumption_and_production_mass_CO2(self):
        instanciated_charts = []
        # Charts for consumption and prod
        energy_consumption = self.get_sosdisc_outputs(GlossaryEnergy.EnergyConsumptionValue)
        scaling_factor_energy_consumption = self.get_sosdisc_inputs(
            'scaling_factor_energy_consumption')
        energy_production = self.get_sosdisc_outputs(GlossaryEnergy.EnergyProductionValue)
        chart_name = f'CO2 captured<br>with input investments'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Mass [Mt]',
                                             chart_name=chart_name, stacked_bar=True)

        for reactant in energy_consumption.columns:
            if reactant != GlossaryEnergy.Years and reactant.endswith('(Mt)'):
                if reactant.startswith('CO2'):
                    energy_twh = - \
                        energy_consumption[reactant].values * \
                        scaling_factor_energy_consumption
                    legend_title = f'{reactant} consumption'.replace(
                        "(Mt)", "")
                    serie = InstanciatedSeries(
                        energy_consumption[GlossaryEnergy.Years].values.tolist(
                        ),
                        energy_twh.tolist(), legend_title, 'bar')

                    new_chart.series.append(serie)

        instanciated_charts.append(new_chart)
        return instanciated_charts

    def get_charts_consumption_and_production_mass_resources(self):
        instanciated_charts = []
        # Charts for consumption and prod
        energy_consumption = self.get_sosdisc_outputs(GlossaryEnergy.EnergyConsumptionValue)
        scaling_factor_energy_consumption = self.get_sosdisc_inputs(
            'scaling_factor_energy_consumption')
        energy_production = self.get_sosdisc_outputs(GlossaryEnergy.EnergyProductionValue)
        chart_name = f'resources used for CO2 capture <br>with input investments'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Mass [Mt]',
                                             chart_name=chart_name, stacked_bar=True)

        for reactant in energy_consumption.columns:
            if reactant != GlossaryEnergy.Years and reactant.endswith('(Mt)'):
                if reactant.startswith('CO2'):
                    pass
                else:
                    energy_twh = - \
                        energy_consumption[reactant].values * \
                        scaling_factor_energy_consumption
                    legend_title = f'{reactant} consumption'.replace(
                        "(Mt)", "")
                    serie = InstanciatedSeries(
                        energy_consumption[GlossaryEnergy.Years].values.tolist(
                        ),
                        energy_twh.tolist(), legend_title, 'bar')

                    new_chart.series.append(serie)

        instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_charts_consumption_and_production_energy(self):
        instanciated_charts = []
        # Charts for consumption and prod
        energy_consumption = self.get_sosdisc_outputs(GlossaryEnergy.EnergyConsumptionValue)
        energy_production = self.get_sosdisc_outputs(GlossaryEnergy.EnergyProductionValue)
        scaling_factor_energy_consumption = self.get_sosdisc_inputs(
            'scaling_factor_energy_consumption')
        scaling_factor_energy_production = self.get_sosdisc_inputs(
            'scaling_factor_energy_production')
        cut_energy_name = self.energy_name.split(".")
        display_energy_name = cut_energy_name[len(
            cut_energy_name) - 1].replace("_", " ").capitalize()
        chart_name = f'{display_energy_name} Energy consumption for CO2 capture<br>with input investments'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Energy [TWh]',
                                             chart_name=chart_name, stacked_bar=True)

        for reactant in energy_consumption.columns:

            if reactant != GlossaryEnergy.Years and reactant.endswith('(TWh)'):
                energy_twh = - \
                    energy_consumption[reactant].values * \
                    scaling_factor_energy_consumption
                legend_title = f'{reactant} consumption'.replace(
                    "(TWh)", "")
                serie = InstanciatedSeries(
                    energy_consumption[GlossaryEnergy.Years].values.tolist(),
                    energy_twh.tolist(), legend_title, 'bar')

                new_chart.series.append(serie)

        for products in energy_production.columns:
            # We do not plot technology H2 production on this graph
            # Pie charts are here to see difference of production between
            # technologies

            if products != GlossaryEnergy.Years and products.endswith('(kWh)') and self.energy_name not in products:
                energy_twh = energy_production[products].values * \
                    scaling_factor_energy_production
                legend_title = f'{products} production'.replace(
                    "(TWh)", "")
                serie = InstanciatedSeries(
                    energy_production[GlossaryEnergy.Years].values.tolist(),
                    energy_twh.tolist(), legend_title, 'bar')

                new_chart.series.append(serie)

        instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_chart_comparison_carbon_intensity(self):
        new_charts = []
        chart_name = f'Comparison of carbon intensity due to production of {self.energy_name} technologies'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'CO2 emissions [kg/kWh]', chart_name=chart_name)

        technology_list = self.get_sosdisc_inputs(GlossaryEnergy.techno_list)

        for technology in technology_list:
            techno_emissions = self.get_sosdisc_inputs(
                f'{technology}.{GlossaryEnergy.CO2EmissionsValue}')
            year_list = techno_emissions[GlossaryEnergy.Years].values.tolist()
            emission_list = techno_emissions[technology].values.tolist()
            serie = InstanciatedSeries(
                year_list, emission_list, technology, 'lines')
            new_chart.series.append(serie)
        new_charts.append(new_chart)
        chart_name = f'Comparison of carbon intensity for {self.energy_name} technologies (production + use)'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'CO2 emissions [kg/kWh]', chart_name=chart_name)

        co2_per_use = self.get_sosdisc_outputs(
            'CO2_per_use')

        for technology in technology_list:
            techno_emissions = self.get_sosdisc_inputs(
                f'{technology}.{GlossaryEnergy.CO2EmissionsValue}')
            year_list = techno_emissions[GlossaryEnergy.Years].values.tolist()
            emission_list = techno_emissions[technology].values + \
                co2_per_use['CO2_per_use']
            serie = InstanciatedSeries(
                year_list, emission_list.tolist(), technology, 'lines')
            new_chart.series.append(serie)

        new_charts.append(new_chart)
        return new_charts

    def get_chart_flue_gas_limit(self):
        '''
        Chart to check flue gas production limit on flue gas capture
        '''
        carbon_captured_type = self.get_sosdisc_outputs('carbon_captured_type')
        flue_gas_production = self.get_sosdisc_inputs('flue_gas_production')

        chart_name = f'Type of carbon capture production and flue gas production limit'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'Production [Mt]', chart_name=chart_name)

        serie = InstanciatedSeries(
            flue_gas_production[GlossaryEnergy.Years].values.tolist(),
            flue_gas_production[CarbonCapture.flue_gas_name].values.tolist(), 'Flue gas production', 'lines')
        new_chart.series.append(serie)

        if 'flue gas limited' in carbon_captured_type:
            serie = InstanciatedSeries(
                carbon_captured_type[GlossaryEnergy.Years].values.tolist(),
                carbon_captured_type['flue gas'].values.tolist(), 'CO2 captured by flue gas (by invest)', 'lines')
            new_chart.series.append(serie)

            serie = InstanciatedSeries(
                carbon_captured_type[GlossaryEnergy.Years].values.tolist(),
                carbon_captured_type['flue gas limited'].tolist(), 'CO2 captured by flue gas (limited)', 'lines')
            new_chart.series.append(serie)
        else:
            serie = InstanciatedSeries(
                carbon_captured_type[GlossaryEnergy.Years].values.tolist(),
                carbon_captured_type['flue gas'].values.tolist(), 'CO2 captured by flue gas', 'lines')
            new_chart.series.append(serie)

        serie = InstanciatedSeries(
            carbon_captured_type[GlossaryEnergy.Years].values.tolist(),
            carbon_captured_type['DAC'].values.tolist(), 'CO2 captured by DAC', 'lines')
        new_chart.series.append(serie)

        return new_chart
