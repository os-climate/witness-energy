'''
Copyright 2024 Capgemini

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

from climateeconomics.core.core_witness.climateeco_discipline import ClimateEcoDiscipline
from energy_models.core.ccus.ccus import CCUS
from energy_models.core.stream_type.carbon_models.food_storage import FoodStorage
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.carbon_utilization.food_storage_applications.algae_cultivation.algae_cultivation_disc import AlgaeCultivationDiscipline
from energy_models.models.carbon_utilization.food_storage_applications.beverage_carbonation.beverage_carbonation_disc import BeverageCarbonationDiscipline
from energy_models.models.carbon_utilization.food_storage_applications.carbonated_water.carbonated_water_disc import CarbonatedWaterDiscipline
from energy_models.models.carbon_utilization.food_storage_applications.food_storage_applications_techno.food_storage_applications_techno_disc import FoodStorageApplicationsTechnoDiscipline

from sostrades_core.execution_engine.sos_wrapp import SoSWrapp
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import TwoAxesInstanciatedChart, \
    InstanciatedSeries
from sostrades_core.tools.post_processing.tables.instanciated_table import InstanciatedTable


class FoodStorageDiscipline(SoSWrapp):
    # ontology information
    _ontology_data = {
        'label': 'Food Storage Model',
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
    POSSIBLE_FOOD_STORAGE_TECHNOS = {
                                 'carbon_utilization.food_storage_applications.AlgaeCultivation': AlgaeCultivationDiscipline.FOOD_STORAGE_RATIO,
                                 'carbon_utilization.food_storage_applications.BeverageCarbonation': BeverageCarbonationDiscipline.FOOD_STORAGE_RATIO,
                                 'carbon_utilization.food_storage_applications.CarbonatedWater': CarbonatedWaterDiscipline.FOOD_STORAGE_RATIO,
        'carbon_utilization.food_storage_applications.FoodStorageApplicationsTechno': FoodStorageApplicationsTechnoDiscipline.FOOD_STORAGE_RATIO

    }

    DESC_IN = {GlossaryEnergy.YearStart: ClimateEcoDiscipline.YEAR_START_DESC_IN,
               GlossaryEnergy.YearEnd: GlossaryEnergy.YearEndVar,
               GlossaryEnergy.techno_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                                     'possible_values': list(POSSIBLE_FOOD_STORAGE_TECHNOS.keys()),
                                     'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_food_storage',
                                     'structuring': True, 'unit': '-'},
               'scaling_factor_techno_production': {'type': 'float', 'default': 1e3, 'unit': '-', 'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_public', 'user_level': 2},
               GlossaryEnergy.ccs_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'}, 'possible_values': CCUS.ccs_list,
                            'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy_study',
                            'editable': False,
                            'structuring': True,
                            'unit': '-'},
               }

    energy_name = FoodStorage.name

    DESC_OUT = {GlossaryEnergy.FoodStorageMean: {'type': 'dataframe',
                                  'visibility': SoSWrapp.SHARED_VISIBILITY,
                                  'namespace': 'ns_food_storage', 'unit': '%'},
                'food_storage_production': {'type': 'dataframe',
                                        'visibility': SoSWrapp.SHARED_VISIBILITY,
                                        'namespace': 'ns_food_storage', 'unit': 'Mt'},
                'food_storage_prod_ratio': {'type': 'dataframe',
                                        'visibility': SoSWrapp.SHARED_VISIBILITY,
                                        'namespace': 'ns_food_storage', 'unit': '%'}}

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.energy_model = FoodStorage(self.energy_name)
        self.energy_model.configure_parameters(inputs_dict)

    def setup_sos_disciplines(self):
        dynamic_inputs = {}

        if GlossaryEnergy.techno_list in self.get_data_in() and GlossaryEnergy.ccs_list in self.get_data_in():
            techno_list = self.get_sosdisc_inputs(GlossaryEnergy.techno_list)
            ccs_list = self.get_sosdisc_inputs(GlossaryEnergy.ccs_list)

            if techno_list is not None and ccs_list is not None:
                for techno in techno_list:
                    # check if techno not in ccs_list, namespace is
                    # ns_energy_mix
                    if techno.split('.')[0] not in ccs_list:
                        ns_variable = GlossaryEnergy.NS_ENERGY_MIX

                    # techno in ccs_list, use different namespace
                    else:
                        ns_variable = GlossaryEnergy.NS_CCS

                    dynamic_inputs[f'{techno}.{GlossaryEnergy.TechnoProductionValue}'] = {
                        'type': 'dataframe', 'unit': 'TWh or Mt',
                        'visibility': SoSWrapp.SHARED_VISIBILITY,
                        'namespace': ns_variable,
                        'dataframe_descriptor': {GlossaryEnergy.Years: ('int', [1900, GlossaryEnergy.YeartEndDefault], False),
                                                 'beverage food (Mt)': ('float', None, False),
                                                 }
                    }

                    #dynamic_inputs[f'{techno}.{GlossaryEnergy.TechnoCapitalDfValue}'] = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.TechnoCapitalDf)
                    dynamic_inputs[f'{techno}.food_storage_co2_ratio'] = {'type': 'array',
                                                                      'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                                      'namespace': ns_variable, 'unit': '',
                                                                      'default': self.POSSIBLE_FOOD_STORAGE_TECHNOS[techno]}

        self.add_inputs(dynamic_inputs)

    def run(self):
        # -- get inputs
        inputs_dict = self.get_sosdisc_inputs()
        # -- configure class with inputs
        # -- configure class with inputs
        self.energy_model.configure_parameters_update(inputs_dict)
        # -- compute informations
        food_storage_mean = self.energy_model.compute(inputs_dict)

        outputs_dict = {
            GlossaryEnergy.FoodStorageMean: food_storage_mean,
            'food_storage_production': self.energy_model.get_total_food_storage_production(),
            'food_storage_prod_ratio': self.energy_model.get_total_food_storage_prod_ratio()}
        # -- store outputs
        self.store_sos_outputs_values(outputs_dict)

    def compute_sos_jacobian(self):
        '''
             Compute gradient of coupling outputs vs coupling inputs
        '''
        inputs_dict = self.get_sosdisc_inputs()
        technologies_list = inputs_dict[GlossaryEnergy.techno_list]
        ccs_list = inputs_dict[GlossaryEnergy.ccs_list]
        mix_weights = self.get_sosdisc_outputs('food_storage_prod_ratio')

        total_prod = self.get_sosdisc_outputs('food_storage_production')[
            self.energy_model.name].values
        len_matrix = len(total_prod)
        for techno in technologies_list:

            self.set_partial_derivative_for_other_types(
                (GlossaryEnergy.FoodStorageMean,
                 GlossaryEnergy.FoodStorageMean), (f'{techno}.food_storage_co2_ratio',),
                np.reshape(mix_weights[techno].values, (len_matrix, 1)))

            # self.set_partial_derivative_for_other_types(
            #     (GlossaryEnergy.FlueGasMean,
            #      GlossaryEnergy.FlueGasMean), (f'{techno}.food_storage_co2_ratio',),
            #     np.reshape(mix_weights1[techno].values, (len_matrix, 1)))

            # An array of one value because GEMS needs array
            food_storage_co2_ratio = self.get_sosdisc_inputs(
                f'{techno}.food_storage_co2_ratio')[0]

            grad_prod = (
                total_prod - self.energy_model.production[
                    f'{self.energy_model.name} {techno} (Mt)'].values) / total_prod ** 2

            self.set_partial_derivative_for_other_types(
                ('food_storage_prod_ratio', techno),
                (f'{techno}.{GlossaryEnergy.TechnoProductionValue}',
                 f'{self.energy_model.name} (Mt)'),
                inputs_dict['scaling_factor_techno_production'] * np.identity(len_matrix) * grad_prod)

            grad_foodstorage_prod = food_storage_co2_ratio * grad_prod
            for techno_other in technologies_list:
                if techno != techno_other:
                    food_storage_co2_ratio_other = self.get_sosdisc_inputs(
                        f'{techno_other}.food_storage_co2_ratio')[0]

                    grad_food_storage_prod_ratio = -self.energy_model.production[
                        f'{self.energy_model.name} {techno} (Mt)'].values / \
                        total_prod ** 2
                    self.set_partial_derivative_for_other_types(
                        ('food_storage_prod_ratio', techno),
                        (f'{techno_other}.{GlossaryEnergy.TechnoProductionValue}',
                         f'{self.energy_model.name} (Mt)'),
                        inputs_dict['scaling_factor_techno_production'] * np.identity(
                            len_matrix) * grad_food_storage_prod_ratio)

                    grad_foodstorage_prod -= \
                        food_storage_co2_ratio_other * self.energy_model.production[
                            f'{self.energy_model.name} {techno_other} (Mt)'].values / \
                        total_prod ** 2

            self.set_partial_derivative_for_other_types(
                (GlossaryEnergy.FoodStorageMean, GlossaryEnergy.FoodStorageMean),
                (f'{techno}.{GlossaryEnergy.TechnoProductionValue}',
                 f'{self.energy_model.name} (Mt)'),
                inputs_dict['scaling_factor_techno_production'] * np.identity(len_matrix) * grad_foodstorage_prod)

            self.set_partial_derivative_for_other_types(
                ('food_storage_production', self.energy_model.name),
                (f'{techno}.{GlossaryEnergy.TechnoProductionValue}',
                 f'{self.energy_model.name} (Mt)'),
                inputs_dict['scaling_factor_techno_production'] * np.identity(len_matrix))

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['Average CO2 concentration in Food storages',
                      'Technologies CO2 concentration',
                      'Food storage production'
                      ]
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

        if 'Food storage production' in charts:
            new_chart = self.get_food_storage_production()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'Average CO2 concentration in Food storages' in charts:
            new_chart = self.get_chart_average_co2_concentration()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'Technologies CO2 concentration' in charts:
            new_chart = self.get_table_technology_co2_concentration()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_food_storage_production(self):
        food_storage_total = self.get_sosdisc_outputs(
            'food_storage_production')[self.energy_name].values
        food_storage_prod_ratio = self.get_sosdisc_outputs('food_storage_prod_ratio')
        technologies_list = self.get_sosdisc_inputs(GlossaryEnergy.techno_list)
        years = food_storage_prod_ratio[GlossaryEnergy.Years].values
        chart_name = f'Food storage emissions by technology'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'Food storage emissions [Mt]', chart_name=chart_name, stacked_bar=True)

        for techno in technologies_list:
            food_storage_prod = food_storage_total * food_storage_prod_ratio[techno].values
            serie = InstanciatedSeries(
                years.tolist(),
                food_storage_prod.tolist(), techno.split('.')[-1], 'bar')
            new_chart.series.append(serie)

        serie = InstanciatedSeries(
            years.tolist(),
            food_storage_total.tolist(), 'Total', 'lines')
        new_chart.series.append(serie)

        return new_chart

    def get_chart_average_co2_concentration(self):
        food_storage_co2_concentration = self.get_sosdisc_outputs(GlossaryEnergy.FoodStorageMean)

        chart_name = f'Average CO2 concentration in Food storages'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'CO2 concentration [%]', chart_name=chart_name)

        serie = InstanciatedSeries(
            food_storage_co2_concentration[GlossaryEnergy.Years].values.tolist(),
            (food_storage_co2_concentration[GlossaryEnergy.FoodStorageMean].values * 100).tolist(), f'CO2 concentration', 'lines')

        new_chart.series.append(serie)
        return new_chart

    def get_table_technology_co2_concentration(self):
        table_name = 'Concentration of CO2 in all food storage streams'
        technologies_list = self.get_sosdisc_inputs(GlossaryEnergy.techno_list)

        headers = ['Technology', 'CO2 concentration']
        cells = []
        cells.append(technologies_list)

        col_data = []
        for techno in technologies_list:
            val_co2 = round(self.get_sosdisc_inputs(
                f'{techno}.food_storage_co2_ratio')[0] * 100, 2)
            col_data.append([f'{val_co2} %'])
        cells.append(col_data)

        new_table = InstanciatedTable(table_name, headers, cells)

        return new_table