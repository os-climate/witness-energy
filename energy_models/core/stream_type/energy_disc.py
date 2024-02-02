'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/14-2023/11/16 Copyright 2023 Capgemini

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

from energy_models.core.stream_type.stream_disc import StreamDiscipline
from energy_models.glossaryenergy import GlossaryEnergy
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart


class EnergyDiscipline(StreamDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Core Energy Type Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': '',
        'version': '',
    }
    DESC_IN = {GlossaryEnergy.CO2Taxes['var_name']: GlossaryEnergy.CO2Taxes,
               }
    DESC_IN.update(StreamDiscipline.DESC_IN)

    # -- Here are the results of concatenation of each techno prices,consumption and production

    DESC_OUT = {
        GlossaryEnergy.CO2EmissionsValue: {'type': 'dataframe', 'unit': 'kg/kWh'},
        'CO2_per_use': {'type': 'dataframe', 'unit': 'kg/kWh'},
        'CH4_per_use': {'type': 'dataframe', 'unit': 'kg/kWh'},
        'N2O_per_use': {'type': 'dataframe', 'unit': 'kg/kWh'}}

    DESC_OUT.update(StreamDiscipline.DESC_OUT)

    _maturity = 'Research'
    energy_name = 'energy'

    def setup_sos_disciplines(self):
        dynamic_inputs = {}
        if GlossaryEnergy.techno_list in self.get_data_in():
            techno_list = self.get_sosdisc_inputs(GlossaryEnergy.techno_list)
            self.update_default_technology_list()
            if techno_list is not None:
                techno_list = self.get_sosdisc_inputs(GlossaryEnergy.techno_list)
                for techno in techno_list:
                    dynamic_inputs[
                        f'{techno}.{GlossaryEnergy.TechnoCapitalValue}'] = GlossaryEnergy.get_dynamic_variable(
                        GlossaryEnergy.TechnoCapitalDf)
                    dynamic_inputs[f'{techno}.{GlossaryEnergy.TechnoConsumptionValue}'] = {
                        'type': 'dataframe', 'unit': 'TWh or Mt',
                        "dynamic_dataframe_columns": True}
                    dynamic_inputs[f'{techno}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}'] = {
                        'type': 'dataframe', 'unit': 'TWh or Mt',
                        "dynamic_dataframe_columns": True}
                    dynamic_inputs[f'{techno}.{GlossaryEnergy.TechnoProductionValue}'] = {
                        'type': 'dataframe', 'unit': 'TWh or Mt',
                        "dynamic_dataframe_columns": True}
                    dynamic_inputs[f'{techno}.{GlossaryEnergy.TechnoPricesValue}'] = {
                        'type': 'dataframe', 'unit': '$/MWh',
                        "dynamic_dataframe_columns": True}
                    dynamic_inputs[f'{techno}.{GlossaryEnergy.CO2EmissionsValue}'] = {
                        'type': 'dataframe', 'unit': 'kg/kWh',
                        "dynamic_dataframe_columns": True}
                    dynamic_inputs[f'{techno}.{GlossaryEnergy.LandUseRequiredValue}'] = {
                        'type': 'dataframe', 'unit': 'Gha',
                        "dynamic_dataframe_columns": True}

        self.add_inputs(dynamic_inputs)

    def update_default_technology_list(self):
        '''
        Update the default value of technologies list with techno discipline below the energy node and in possible values
        '''

        found_technos = self.found_technos_under_energy()
        self.set_dynamic_default_values({GlossaryEnergy.techno_list: found_technos})

    def found_technos_under_energy(self):
        '''
        Set the default value of the technology list with discipline under the energy which are in possible values
        '''
        my_name = self.get_disc_full_name()
        possible_technos = self.get_data_in()[GlossaryEnergy.techno_list][self.POSSIBLE_VALUES]
        found_technos_list = self.dm.get_discipline_names_with_starting_name(
            my_name)
        short_technos_list = [name.split(
            f'{my_name}.')[-1] for name in found_technos_list if f'{my_name}.' in name]

        possible_short_technos_list = [
            techno for techno in short_technos_list if techno in possible_technos]
        return possible_short_technos_list

    def run(self):
        '''
        Run for all energy disciplines
        '''

        StreamDiscipline.run(self)
        # -- get inputs

        CO2_emissions = self.energy_model.compute_carbon_emissions()

        ghg_per_use = self.energy_model.compute_ghg_emissions_per_use()

        outputs_dict = {GlossaryEnergy.CO2EmissionsValue: CO2_emissions}

        outputs_dict.update(ghg_per_use)
        
        self.store_sos_outputs_values(outputs_dict)

    def compute_sos_jacobian(self):

        StreamDiscipline.compute_sos_jacobian(self)

        inputs_dict = self.get_sosdisc_inputs()
        outputs_dict = self.get_sosdisc_outputs()
        years = np.arange(inputs_dict[GlossaryEnergy.YearStart],
                          inputs_dict[GlossaryEnergy.YearEnd] + 1)
        technos_list = inputs_dict[GlossaryEnergy.techno_list]
        mix_weight = outputs_dict['techno_mix']
        for techno in technos_list:
            list_columnstechnoprod = list(
                inputs_dict[f'{techno}.{GlossaryEnergy.TechnoProductionValue}'].columns)

            mix_weight_techno = mix_weight[techno].values / 100.0
            self.set_partial_derivative_for_other_types(
                (GlossaryEnergy.CO2EmissionsValue, self.energy_name),
                (f'{techno}.{GlossaryEnergy.CO2EmissionsValue}', techno),
                np.diag(outputs_dict['techno_mix'][techno].values / 100))

            for column_name in list_columnstechnoprod:
                if column_name.startswith(self.energy_name):
                    # The mix_weight_techno is zero means that the techno is negligible else we do nothing
                    # np.sign gives 0 if zero and 1 if value so it suits well
                    # with our needs
                    #                     grad_techno_mix_vs_prod = (
                    #                         outputs_dict[GlossaryEnergy.EnergyProductionValue][self.energy_name].values -
                    #                         inputs_dict[f'{techno}.{GlossaryEnergy.TechnoProductionValue}'][column_name].values
                    #                     ) / outputs_dict[GlossaryEnergy.EnergyProductionValue][self.energy_name].values**2
                    grad_techno_mix_vs_prod = self.grad_techno_mix_vs_prod_dict[techno]
                    grad_techno_mix_vs_prod = grad_techno_mix_vs_prod * \
                                              np.sign(mix_weight_techno)

                    grad_co2_vs_prod = inputs_dict[f'{techno}.{GlossaryEnergy.CO2EmissionsValue}'][techno].values * \
                                       grad_techno_mix_vs_prod

                    for techno_other in technos_list:
                        if techno_other != techno:
                            mix_weight_techno_other = mix_weight[techno_other].values / 100.0
                            #                             grad_co2_vs_prod += -inputs_dict[f'{techno_other}.{GlossaryEnergy.CO2EmissionsValue}'][techno_other].values * \
                            #                                 mix_weight_techno_other / \
                            #                                 outputs_dict[GlossaryEnergy.EnergyProductionValue][self.energy_name].values
                            grad_techno_mix_vs_prod = self.grad_techno_mix_vs_prod_dict[
                                f'{techno} {techno_other}']
                            grad_techno_mix_vs_prod = grad_techno_mix_vs_prod * \
                                                      np.sign(mix_weight_techno_other)
                            grad_co2_vs_prod += inputs_dict[f'{techno_other}.{GlossaryEnergy.CO2EmissionsValue}'][
                                                    techno_other].values * grad_techno_mix_vs_prod
                    self.set_partial_derivative_for_other_types(
                        (GlossaryEnergy.CO2EmissionsValue, self.energy_name),
                        (f'{techno}.{GlossaryEnergy.TechnoProductionValue}', column_name),
                        inputs_dict['scaling_factor_techno_production'] * np.identity(len(years)) * grad_co2_vs_prod)

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['Energy price',
                      GlossaryEnergy.Capital,
                      'Technology mix',
                      'CO2 emissions',
                      'Consumption and production']
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

        instanciated_charts = StreamDiscipline.get_post_processing_list(
            self, filters)
        charts = []
        # Overload default value with chart filter
        if filters is not None:
            for chart_filter in filters:
                if chart_filter.filter_key == 'charts':
                    charts = chart_filter.selected_values

        if 'CO2 emissions' in charts:
            new_charts = self.get_chart_comparison_carbon_intensity()
            for new_chart in new_charts:
                if new_chart is not None:
                    instanciated_charts.append(new_chart)

            new_charts = self.get_chart_co2_emissions()
            for new_chart in new_charts:
                if new_chart is not None:
                    instanciated_charts.append(new_chart)
        return instanciated_charts

    def get_chart_comparison_carbon_intensity(self):
        new_charts = []
        chart_name = f'Comparison of carbon intensity due to production<br>of {self.energy_name} technologies'
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

    def get_chart_co2_emissions(self):
        new_charts = []
        chart_name = f'Comparison of CO2 emissions due to production and use<br>of {self.energy_name} technologies'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'CO2 emissions (Mt)', chart_name=chart_name, stacked_bar=True)

        technology_list = self.get_sosdisc_inputs(GlossaryEnergy.techno_list)

        co2_per_use = self.get_sosdisc_outputs(
            'CO2_per_use')

        energy_production = self.get_sosdisc_outputs(GlossaryEnergy.EnergyProductionValue)
        scaling_factor_energy_production = self.get_sosdisc_inputs(
            'scaling_factor_energy_production')
        for technology in technology_list:
            techno_emissions = self.get_sosdisc_inputs(
                f'{technology}.{GlossaryEnergy.CO2EmissionsValue}')
            year_list = techno_emissions[GlossaryEnergy.Years].values.tolist()
            emission_list = techno_emissions[technology].values * \
                            energy_production[self.energy_name].values * \
                            scaling_factor_energy_production
            serie = InstanciatedSeries(
                year_list, emission_list.tolist(), technology, 'bar')
            new_chart.series.append(serie)

        co2_per_use = co2_per_use['CO2_per_use'].values * \
                      energy_production[self.energy_name].values * \
                      scaling_factor_energy_production
        serie = InstanciatedSeries(
            year_list, co2_per_use.tolist(), 'CO2 from use of brut production', 'bar')
        new_chart.series.append(serie)
        new_charts.append(new_chart)

        return new_charts
