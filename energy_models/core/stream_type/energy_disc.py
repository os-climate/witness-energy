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

import numpy as np

from climateeconomics.glossarycore import GlossaryCore
from energy_models.core.stream_type.stream_disc import StreamDiscipline
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart
from energy_models.glossaryenergy import GlossaryEnergy


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
        'CO2_emissions': {'type': 'dataframe', 'unit': 'kg/kWh'},
        'CO2_per_use': {'type': 'dataframe', 'unit': 'kg/kWh'},
        'CH4_per_use': {'type': 'dataframe', 'unit': 'kg/kWh'},
        'N2O_per_use': {'type': 'dataframe', 'unit': 'kg/kWh'}}

    DESC_OUT.update(StreamDiscipline.DESC_OUT)

    _maturity = 'Research'
    energy_name = 'energy'

    def setup_sos_disciplines(self):
        dynamic_inputs = {}
        if 'technologies_list' in self.get_data_in():
            techno_list = self.get_sosdisc_inputs('technologies_list')
            self.update_default_technology_list()
            if techno_list is not None:
                techno_list = self.get_sosdisc_inputs('technologies_list')
                for techno in techno_list:
                    dynamic_inputs[f'{techno}.techno_consumption'] = {
                        'type': 'dataframe', 'unit': 'TWh or Mt',
                        'dataframe_descriptor': {'years': ('float', None, True),
                                                 'biomass_dry (TWh)': ('float', None, True),
                                                 'electricity (TWh)': ('float', None, True),
                                                 'methane (TWh)': ('float', None, True),
                                                 'water (Mt)': ('float', None, True),
                                                 'CO2_resource (Mt)': ('float', None, True),
                                                 'copper_resource (Mt)': ('float', None, True),
                                                 'uranium_resource (Mt)': ('float', None, True),
                                                 'biogas (TWh)': ('float', None, True),
                                                 'solid_fuel (TWh)': ('float', None, True),
                                                 'fuel.liquid_fuel (TWh)': ('float', None, True),
                                                 'water_resource (Mt)': ('float', None, True),
                                                 'hydrogen.gaseous_hydrogen (TWh)': ('float', None, True),
                                                 'syngas (TWh)': ('float', None, True),
                                                 'platinum_resource (Mt)': ('float', None, True),
                                                 'oil_resource (Mt)': ('float', None, True),
                                                 'carbon_capture (Mt)': ('float', None, True),
                                                 'carbon_storage (Mt)': ('float', None, True),
                                                 'natural_gas_resource (Mt)': ('float', None, True),
                                                 'mono_ethanol_amine_resource (Mt)': ('float', None, True),
                                                 'coal_resource (Mt)': ('float', None, True),
                                                 'carbon_capture (TWh)': ('float', None, True),
                                                 }}
                    dynamic_inputs[f'{techno}.techno_consumption_woratio'] = {
                        'type': 'dataframe', 'unit': 'TWh or Mt',
                        'dataframe_descriptor': {'years': ('float', None, True),
                                                 'electricity (TWh)': ('float', None, True),
                                                 'water (Mt)': ('float', None, True),
                                                 'CO2_resource (Mt)': ('float', None, True),
                                                 'methane (TWh)': ('float', None, True),
                                                 'copper_resource (Mt)': ('float', None, True),
                                                 'uranium_resource (Mt)': ('float', None, True),
                                                 'biogas (TWh)': ('float', None, True),
                                                 'solid_fuel (TWh)': ('float', None, True),
                                                 'fuel.liquid_fuel (TWh)': ('float', None, True),
                                                 'water_resource (Mt)': ('float', None, True),
                                                 'biomass_dry (TWh)': ('float', None, True),
                                                 'hydrogen.gaseous_hydrogen (TWh)': ('float', None, True),
                                                 'syngas (TWh)': ('float', None, True),
                                                 'platinum_resource (Mt)': ('float', None, True),
                                                 'oil_resource (Mt)': ('float', None, True),
                                                 'carbon_capture (Mt)': ('float', None, True),
                                                 'carbon_storage (Mt)': ('float', None, True),
                                                 'natural_gas_resource (Mt)': ('float', None, True),
                                                 'mono_ethanol_amine_resource (Mt)': ('float', None, True),
                                                 'coal_resource (Mt)': ('float', None, True),
                                                 'carbon_capture (TWh)': ('float', None, True),
                                                 }}
                    dynamic_inputs[f'{techno}.techno_production'] = {
                        'type': 'dataframe', 'unit': 'TWh or Mt',
                        'dataframe_descriptor': {'years': ('float', None, True),
                                                 'biomass_dry (TWh)': ('float', None, True),
                                                 'hydrogen.gaseous_hydrogen (TWh)': ('float', None, True),
                                                 'CO2 (Mt)': ('float', None, True),
                                                 'O2 (Mt)': ('float', None, True),
                                                 'C (Mt)': ('float', None, True),
                                                 'renewable (TWh)': ('float', None, True),
                                                 'fossil (TWh)': ('float', None, True),
                                                 'CO2 from Flue Gas (Mt)': ('float', None, True),
                                                 'CH4 (Mt)': ('float', None, True),
                                                 'electricity (TWh)': ('float', None, True),
                                                 'CO2_resource (Mt)': ('float', None, True),
                                                 'N2O (Mt)': ('float', None, True),
                                                 'heat.hightemperatureheat (TWh)': ('float', None, True),
                                                 'carbon_resource (Mt)': ('float', None, True),
                                                 'fuel.liquid_fuel (TWh)': ('float', None, True),
                                                 'kerosene (TWh)': ('float', None, True),
                                                 'gasoline (TWh)': ('float', None, True),
                                                 'liquefied_petroleum_gas (TWh)': ('float', None, True),
                                                 'heating_oil (TWh)': ('float', None, True),
                                                 'ultra_low_sulfur_diesel (TWh)': ('float', None, True),
                                                 'water_resource (Mt)': ('float', None, True),
                                                 'methane (TWh)': ('float', None, True),
                                                 'carbon_capture (Mt)': ('float', None, True),
                                                 'carbon_storage (Mt)': ('float', None, True),
                                                 'fuel.methanol (TWh)': ('float', None, True),
                                                 'solid_fuel (TWh)': ('float', None, True),
                                                 'hydrogen.liquid_hydrogen (TWh)': ('float', None, True),
                                                 }}
                    dynamic_inputs[f'{techno}.techno_prices'] = {
                        'type': 'dataframe', 'unit': '$/MWh',
                        'dataframe_descriptor': {'years': ('float', None, True),
                                                 'Crop': ('float', None, True),
                                                 'Crop_wotaxes': ('float', None, True),
                                                 'Forest_wotaxes': ('float', None, True),
                                                 'Forest': ('float', None, True),
                                                 'WaterGasShift': ('float', None, True),
                                                 'WaterGasShift_wotaxes': ('float', None, True),
                                                 'Electrolysis.PEM': ('float', None, True),
                                                 'Electrolysis.PEM_wotaxes': ('float', None, True),
                                                 'PlasmaCracking': ('float', None, True),
                                                 'PlasmaCracking_wotaxes': ('float', None, True),
                                                 'RenewableSimpleTechno': ('float', None, True),
                                                 'RenewableSimpleTechno_wotaxes': ('float', None, True),
                                                 'FossilSimpleTechno': ('float', None, True),
                                                 'FossilSimpleTechno_wotaxes': ('float', None, True),
                                                 'Hydropower': ('float', None, True),
                                                 'CHPHighHeat': ('float', None, True),
                                                 'CHPHighHeat_wotaxes': ('float', None, True),
                                                 'Hydropower_wotaxes': ('float', None, True),
                                                 'HydrogenBoilerHighHeat': ('float', None, True),
                                                 'HydrogenBoilerHighHeat_wotaxes': ('float', None, True),
                                                 'GasTurbine': ('float', None, True),
                                                 'GasTurbine_wotaxes': ('float', None, True),
                                                 'ManagedWood': ('float', None, True),
                                                 'ManagedWood_wotaxes': ('float', None, True),
                                                 'UnmanagedWood': ('float', None, True),
                                                 'UnmanagedWood_wotaxes': ('float', None, True),
                                                 'CropEnergy': ('float', None, True),
                                                 'CropEnergy_wotaxes': ('float', None, True),
                                                 'WindOffshore': ('float', None, True),
                                                 'WindOffshore_wotaxes': ('float', None, True),
                                                 'WindOnshore': ('float', None, True),
                                                 'WindOnshore_wotaxes': ('float', None, True),
                                                 'SolarPv': ('float', None, True),
                                                 'SolarPv_wotaxes': ('float', None, True),
                                                 'SolarThermal': ('float', None, True),
                                                 'SolarThermal_wotaxes': ('float', None, True),
                                                 'Nuclear': ('float', None, True),
                                                 'Nuclear_wotaxes': ('float', None, True),
                                                 'CombinedCycleGasTurbine': ('float', None, True),
                                                 'CombinedCycleGasTurbine_wotaxes': ('float', None, True),
                                                 'BiogasFired': ('float', None, True),
                                                 'BiogasFired_wotaxes': ('float', None, True),
                                                 'Geothermal': ('float', None, True),
                                                 'Geothermal_wotaxes': ('float', None, True),
                                                 'GeothermalHighHeat': ('float', None, True),
                                                 'GeothermalHighHeat_wotaxes': ('float', None, True),
                                                 'HeatPumpHighHeat': ('float', None, True),
                                                 'HeatPumpHighHeat_wotaxes': ('float', None, True),
                                                 'ElectricBoilerHighHeat': ('float', None, True),
                                                 'ElectricBoilerHighHeat_wotaxes': ('float', None, True),
                                                 'NaturalGasBoilerHighHeat': ('float', None, True),
                                                 'NaturalGasBoilerHighHeat_wotaxes': ('float', None, True),
                                                 'CoalGen': ('float', None, True),
                                                 'CoalGen_wotaxes': ('float', None, True),
                                                 'OilGen': ('float', None, True),
                                                 'OilGen_wotaxes': ('float', None, True),
                                                 'BiomassFired': ('float', None, True),
                                                 'BiomassFired_wotaxes': ('float', None, True),
                                                 'Electrolysis.SOEC': ('float', None, True),
                                                 'Electrolysis.SOEC_wotaxes': ('float', None, True),
                                                 'Electrolysis.AWE': ('float', None, True),
                                                 'Electrolysis.AWE_wotaxes': ('float', None, True),
                                                 'Refinery': ('float', None, True),
                                                 'Refinery_wotaxes': ('float', None, True),
                                                 'FischerTropsch': ('float', None, True),
                                                 'FischerTropsch_wotaxes': ('float', None, True),
                                                 'FossilGas': ('float', None, True),
                                                 'FossilGas_wotaxes': ('float', None, True),
                                                 'UpgradingBiogas': ('float', None, True),
                                                 'UpgradingBiogas_wotaxes': ('float', None, True),
                                                 'CO2Hydrogenation': ('float', None, True),
                                                 'CO2Hydrogenation_wotaxes': ('float', None, True),
                                                 'CoalExtraction': ('float', None, True),
                                                 'CoalExtraction_wotaxes': ('float', None, True),
                                                 'Pelletizing': ('float', None, True),
                                                 'Pelletizing_wotaxes': ('float', None, True),
                                                 'HydrogenLiquefaction': ('float', None, True),
                                                 'HydrogenLiquefaction_wotaxes': ('float', None, True),
                                                 }}
                    dynamic_inputs[f'{techno}.CO2_emissions'] = {
                        'type': 'dataframe', 'unit': 'kg/kWh',
                        'dataframe_descriptor': {'years': ('float', None, True),
                                                 'Crop': ('float', None, True),
                                                 'Forest': ('float', None, True),
                                                 'PlasmaCracking': ('float', None, True),
                                                 'Electrolysis.PEM': ('float', None, True),
                                                 'WaterGasShift': ('float', None, True),
                                                 'RenewableSimpleTechno': ('float', None, True),
                                                 'FossilSimpleTechno': ('float', None, True),
                                                 'Hydropower': ('float', None, True),
                                                 'GasTurbine': ('float', None, True),
                                                 'ManagedWood': ('float', None, True),
                                                 'UnmanagedWood': ('float', None, True),
                                                 'CropEnergy': ('float', None, True),
                                                 'WindOffshore': ('float', None, True),
                                                 'WindOnshore': ('float', None, True),
                                                 'SolarPv': ('float', None, True),
                                                 'SolarThermal': ('float', None, True),
                                                 'Nuclear': ('float', None, True),
                                                 'CombinedCycleGasTurbine': ('float', None, True),
                                                 'BiogasFired': ('float', None, True),
                                                 'Geothermal': ('float', None, True),
                                                 'CHPHighHeat': ('float', None, True),
                                                 'CoalGen': ('float', None, True),
                                                 'OilGen': ('float', None, True),
                                                 'BiomassFired': ('float', None, True),
                                                 'syngas': ('float', None, True),
                                                 'electricity': ('float', None, True),
                                                 'production': ('float', None, True),
                                                 'carbon storage': ('float', None, True),
                                                 'methane': ('float', None, True),
                                                 'HydrogenBoilerHighHeat': ('float', None, True),
                                                 'GeothermalHighHeat': ('float', None, True),
                                                 'ElectricBoilerHighHeat': ('float', None, True),
                                                 'NaturalGasBoilerHighHeat': ('float', None, True),
                                                 'HeatPumpHighHeat': ('float', None, True),
                                                 'Electrolysis.SOEC': ('float', None, True),
                                                 'Electrolysis.AWE': ('float', None, True),
                                                 'Refinery': ('float', None, True),
                                                 'FischerTropsch': ('float', None, True),
                                                 'FossilGas': ('float', None, True),
                                                 'UpgradingBiogas': ('float', None, True),
                                                 'CO2Hydrogenation': ('float', None, True),
                                                 'CoalExtraction': ('float', None, True),
                                                 'Pelletizing': ('float', None, True),
                                                 'HydrogenLiquefaction': ('float', None, True),
                                                 }}
                    dynamic_inputs[f'{techno}.land_use_required'] = {
                        'type': 'dataframe', 'unit': 'Gha',
                        'dataframe_descriptor': {'years': ('float', None, True),
                                                 'Crop (Gha)': ('float', None, True),
                                                 'HydrogenBoilerHighHeat (Gha)': ('float', None, True),
                                                 'Crop for Food (Gha)': ('float', None, True),
                                                 'Forest (Gha)': ('float', None, True),
                                                 'WaterGasShift (Gha)': ('float', None, True),
                                                 'RenewableSimpleTechno (Gha)': ('float', None, True),
                                                 'FossilSimpleTechno (Gha)': ('float', None, True),
                                                 'Electrolysis.PEM (Gha)': ('float', None, True),
                                                 'PlasmaCracking (Gha)': ('float', None, True),
                                                 'CHPHighHeat (Gha)': ('float', None, True),
                                                 'GeothermalHighHeat (Gha)': ('float', None, True),
                                                 'HeatPumpHighHeat (Gha)': ('float', None, True),
                                                 'ElectricBoilerHighHeat (Gha)': ('float', None, True),
                                                 'NaturalGasBoilerHighHeat (Gha)': ('float', None, True),
                                                 'Hydropower (Gha)': ('float', None, True),
                                                 'GasTurbine (Gha)': ('float', None, True),
                                                 'ManagedWood (Gha)': ('float', None, True),
                                                 'UnmanagedWood (Gha)': ('float', None, True),
                                                 'CropEnergy (Gha)': ('float', None, True),
                                                 'WindOffshore (Gha)': ('float', None, True),
                                                 'WindOnshore (Gha)': ('float', None, True),
                                                 'SolarPv (Gha)': ('float', None, True),
                                                 'SolarThermal (Gha)': ('float', None, True),
                                                 'Nuclear (Gha)': ('float', None, True),
                                                 'CombinedCycleGasTurbine (Gha)': ('float', None, True),
                                                 'BiogasFired (Gha)': ('float', None, True),
                                                 'Geothermal (Gha)': ('float', None, True),
                                                 'CoalGen (Gha)': ('float', None, True),
                                                 'OilGen (Gha)': ('float', None, True),
                                                 'BiomassFired (Gha)': ('float', None, True),
                                                 'Electrolysis.SOEC (Gha)': ('float', None, True),
                                                 'Electrolysis.AWE (Gha)': ('float', None, True),
                                                 'Refinery (Gha)': ('float', None, True),
                                                 'FischerTropsch (Gha)': ('float', None, True),
                                                 'FossilGas (Gha)': ('float', None, True),
                                                 'UpgradingBiogas (Gha)': ('float', None, True),
                                                 'CO2Hydrogenation (Gha)': ('float', None, True),
                                                 'CoalExtraction (Gha)': ('float', None, True),
                                                 'Pelletizing (Gha)': ('float', None, True),
                                                 'HydrogenLiquefaction (Gha)': ('float', None, True),
                                                 }}

        self.add_inputs(dynamic_inputs)

    def update_default_technology_list(self):
        '''
        Update the default value of technologies list with techno discipline below the energy node and in possible values
        '''

        found_technos = self.found_technos_under_energy()
        self.set_dynamic_default_values({'technologies_list': found_technos})

    def found_technos_under_energy(self):
        '''
        Set the default value of the technology list with discipline under the energy which are in possible values
        '''
        my_name = self.get_disc_full_name()
        possible_technos = self.get_data_in()['technologies_list'][self.POSSIBLE_VALUES]
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

        outputs_dict = {'CO2_emissions': CO2_emissions}

        outputs_dict.update(ghg_per_use)
        # -- store outputs
        self.store_sos_outputs_values(outputs_dict)

    def compute_sos_jacobian(self):

        StreamDiscipline.compute_sos_jacobian(self)

        inputs_dict = self.get_sosdisc_inputs()
        outputs_dict = self.get_sosdisc_outputs()
        years = np.arange(inputs_dict['year_start'],
                          inputs_dict['year_end'] + 1)
        technos_list = inputs_dict['technologies_list']
        list_columns_co2_emissions = list(
            outputs_dict['CO2_emissions'].columns)
        mix_weight = outputs_dict['techno_mix']
        for techno in technos_list:
            list_columnstechnoprod = list(
                inputs_dict[f'{techno}.techno_production'].columns)

            mix_weight_techno = mix_weight[techno].values / 100.0
            self.set_partial_derivative_for_other_types(
                ('CO2_emissions', self.energy_name), (f'{techno}.CO2_emissions', techno), np.diag(outputs_dict['techno_mix'][techno].values / 100))

            for column_name in list_columnstechnoprod:
                if column_name.startswith(self.energy_name):
                    # The mix_weight_techno is zero means that the techno is negligible else we do nothing
                    # np.sign gives 0 if zero and 1 if value so it suits well
                    # with our needs
                    #                     grad_techno_mix_vs_prod = (
                    #                         outputs_dict[GlossaryCore.EnergyProductionValue][self.energy_name].values -
                    #                         inputs_dict[f'{techno}.techno_production'][column_name].values
                    #                     ) / outputs_dict[GlossaryCore.EnergyProductionValue][self.energy_name].values**2
                    grad_techno_mix_vs_prod = self.grad_techno_mix_vs_prod_dict[techno]
                    grad_techno_mix_vs_prod = grad_techno_mix_vs_prod * \
                        np.sign(mix_weight_techno)

                    grad_co2_vs_prod = inputs_dict[f'{techno}.CO2_emissions'][techno].values * \
                        grad_techno_mix_vs_prod

                    for techno_other in technos_list:
                        if techno_other != techno:
                            mix_weight_techno_other = mix_weight[techno_other].values / 100.0
#                             grad_co2_vs_prod += -inputs_dict[f'{techno_other}.CO2_emissions'][techno_other].values * \
#                                 mix_weight_techno_other / \
#                                 outputs_dict[GlossaryCore.EnergyProductionValue][self.energy_name].values
                            grad_techno_mix_vs_prod = self.grad_techno_mix_vs_prod_dict[
                                f'{techno} {techno_other}']
                            grad_techno_mix_vs_prod = grad_techno_mix_vs_prod * \
                                np.sign(mix_weight_techno_other)
                            grad_co2_vs_prod += inputs_dict[f'{techno_other}.CO2_emissions'][
                                techno_other].values * grad_techno_mix_vs_prod
                    self.set_partial_derivative_for_other_types(
                        ('CO2_emissions', self.energy_name), (f'{techno}.techno_production', column_name), inputs_dict['scaling_factor_techno_production'] * np.identity(len(years)) * grad_co2_vs_prod)

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['Energy price', 'Technology mix', 'CO2 emissions',
                      'Consumption and production']
        chart_filters.append(ChartFilter(
            'Charts', chart_list, chart_list, 'charts'))

        price_unit_list = ['$/MWh', '$/t']
        chart_filters.append(ChartFilter(
            'Price unit', price_unit_list, price_unit_list, 'price_unit'))

        year_start, year_end = self.get_sosdisc_inputs(
            ['year_start', 'year_end'])
        years = list(np.arange(year_start, year_end + 1, 5))
        chart_filters.append(ChartFilter(
            'Years for techno mix', years, [year_start, year_end], 'years'))
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
            'years', 'CO2 emissions [kg/kWh]', chart_name=chart_name)

        technology_list = self.get_sosdisc_inputs('technologies_list')

        for technology in technology_list:
            techno_emissions = self.get_sosdisc_inputs(
                f'{technology}.CO2_emissions')
            year_list = techno_emissions['years'].values.tolist()
            emission_list = techno_emissions[technology].values.tolist()
            serie = InstanciatedSeries(
                year_list, emission_list, technology, 'lines')
            new_chart.series.append(serie)
        new_charts.append(new_chart)
        chart_name = f'Comparison of carbon intensity for {self.energy_name} technologies (production + use)'
        new_chart = TwoAxesInstanciatedChart(
            'years', 'CO2 emissions [kg/kWh]', chart_name=chart_name)

        co2_per_use = self.get_sosdisc_outputs(
            'CO2_per_use')

        for technology in technology_list:
            techno_emissions = self.get_sosdisc_inputs(
                f'{technology}.CO2_emissions')
            year_list = techno_emissions['years'].values.tolist()
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
            'years', 'CO2 emissions (Mt)', chart_name=chart_name, stacked_bar=True)

        technology_list = self.get_sosdisc_inputs('technologies_list')

        co2_per_use = self.get_sosdisc_outputs(
            'CO2_per_use')

        energy_production = self.get_sosdisc_outputs(GlossaryCore.EnergyProductionValue)
        scaling_factor_energy_production = self.get_sosdisc_inputs(
            'scaling_factor_energy_production')
        for technology in technology_list:
            techno_emissions = self.get_sosdisc_inputs(
                f'{technology}.CO2_emissions')
            year_list = techno_emissions['years'].values.tolist()
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
