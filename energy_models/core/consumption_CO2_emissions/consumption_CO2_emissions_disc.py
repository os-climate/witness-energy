'''
Copyright 2022 Airbus SAS
Modifications on 2023/04/21-2023/11/16 Copyright 2023 Capgemini

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
from climateeconomics.glossarycore import GlossaryCore
from climateeconomics.sos_wrapping.sos_wrapping_agriculture.agriculture.agriculture_mix_disc import \
    AgricultureMixDiscipline
from energy_models.core.ccus.ccus import CCUS
from energy_models.core.consumption_CO2_emissions.consumption_CO2_emissions import ConsumptionCO2Emissions
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
from sostrades_core.execution_engine.sos_wrapp import SoSWrapp
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart


class ConsumptionCO2EmissionsDiscipline(SoSWrapp):
    # ontology information
    _ontology_data = {
        'label': 'CO2 emissions consumption Model',
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

    DESC_IN = {
        GlossaryCore.YearStart: ClimateEcoDiscipline.YEAR_START_DESC_IN,
        GlossaryCore.YearEnd: ClimateEcoDiscipline.YEAR_END_DESC_IN,
        GlossaryCore.energy_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                        'possible_values': EnergyMix.energy_list,
                        'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy_study',
                        'editable': False, 'structuring': True},
        GlossaryCore.ccs_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'}, 'possible_values': CCUS.ccs_list,
                     'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy_study', 'editable': False,
                     'structuring': True},
        'scaling_factor_energy_production': {'type': 'float', 'default': 1e3, 'unit': '-', 'user_level': 2,
                                             'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'scaling_factor_energy_consumption': {'type': 'float', 'default': 1e3, 'unit': '-', 'user_level': 2,
                                              'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        GlossaryCore.EnergyProductionDetailedValue: {'type': 'dataframe', 'unit': 'TWh', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                                       'namespace': 'ns_energy',
                                       'dataframe_descriptor': {GlossaryCore.Years: ('float', None, True),
                                                                'production methane (TWh)': ('float', None, True),
                                                                'production hydrogen.gaseous_hydrogen (TWh)': ('float', None, True),
                                                                'production biogas (TWh)': ('float', None, True),
                                                                'production syngas (TWh)': ('float', None, True),
                                                                'production fuel.liquid_fuel (TWh)': ('float', None, True),
                                                                'production fuel.hydrotreated_oil_fuel (TWh)': ('float', None, True),
                                                                'production solid_fuel (TWh)': ('float', None, True),
                                                                'production biomass_dry (TWh)': ('float', None, True),
                                                                'production electricity (TWh)': ('float', None, True),
                                                                'production fuel.biodiesel (TWh)': ('float', None, True),
                                                                'production hydrogen.liquid_hydrogen (TWh)': ('float', None, True),
                                                                'production carbon_capture (Mt)': ('float', None, True),
                                                                'production carbon_storage (Mt)': ('float', None, True),
                                                                'Total production': ('float', None, True),
                                                                'Total production (uncut)': ('float', None, True), }
                                       },
    }

    DESC_OUT = {
        'CO2_emissions_by_use_sources': {'type': 'dataframe', 'unit': 'Gt',
                                         'visibility': SoSWrapp.SHARED_VISIBILITY,
                                         'namespace': 'ns_ccs'},
        'CO2_emissions_by_use_sinks': {'type': 'dataframe', 'unit': 'Gt',
                                       'visibility': SoSWrapp.SHARED_VISIBILITY,
                                       'namespace': 'ns_ccs'},
    }

    model_name = ConsumptionCO2Emissions.name

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.model = ConsumptionCO2Emissions(self.model_name)
        self.model.configure_parameters(inputs_dict)

    def setup_sos_disciplines(self):

        dynamic_inputs = {}
        dynamic_outputs = {}

        if GlossaryCore.energy_list in self.get_data_in():
            energy_list = self.get_sosdisc_inputs(GlossaryCore.energy_list)
            if energy_list is not None:
                for energy in energy_list:
                    if energy == BiomassDry.name:
                        dynamic_inputs[f'{AgricultureMixDiscipline.name}.CO2_per_use'] = {
                            'type': 'dataframe', 'unit': 'kg/kWh', 'namespace': 'ns_witness',
                            'visibility': SoSWrapp.SHARED_VISIBILITY,
                            'dataframe_descriptor': {GlossaryCore.Years: ('float', None, True),
                                                     'CO2_per_use': ('float', None, True),}}
                        dynamic_inputs[f'{AgricultureMixDiscipline.name}.{GlossaryCore.EnergyConsumptionValue}'] = {
                            'type': 'dataframe', 'unit': 'PWh', 'namespace': 'ns_witness',
                            'visibility': SoSWrapp.SHARED_VISIBILITY,
                            'dataframe_descriptor': {GlossaryCore.Years: ('float', None, True),
                                                     'electricity (TWh)': ('float', None, True),
                                                     'CO2_resource (Mt)': ('float', None, True),
                                                     }}
                        dynamic_inputs[f'{AgricultureMixDiscipline.name}.{GlossaryCore.EnergyProductionValue}'] = {
                            'type': 'dataframe', 'unit': 'PWh', 'namespace': 'ns_witness',
                            'visibility': SoSWrapp.SHARED_VISIBILITY,
                            'dataframe_descriptor': {GlossaryCore.Years: ('float', None, True),
                                                     'biomass_dry': ('float', None, True),
                                                     'CO2_resource (Mt)': ('float', None, True),}}
                    else:
                        dynamic_inputs[f'{energy}.CO2_per_use'] = {
                            'type': 'dataframe', 'unit': 'kg/kWh',
                            'visibility': SoSWrapp.SHARED_VISIBILITY,
                            'namespace': 'ns_energy',
                            'dataframe_descriptor': {GlossaryCore.Years: ('float', None, True),
                                                     'CO2_per_use': ('float', None, True),}}
                        dynamic_inputs[f'{energy}.{GlossaryCore.EnergyConsumptionValue}'] = {
                            'type': 'dataframe', 'unit': 'PWh',
                            'visibility': SoSWrapp.SHARED_VISIBILITY,
                            'namespace': 'ns_energy',
                            'dataframe_descriptor': {GlossaryCore.Years: ('float', None, True),
                                                    'syngas (TWh)': ('float', None, True),
                                                    'platinum_resource (Mt)': ('float', None, True),
                                                    'oil_resource (Mt)': ('float', None, True),
                                                    'copper_resource (Mt)': ('float', None, True),
                                                    'uranium_resource (Mt)': ('float', None, True),
                                                    'fuel.liquid_fuel (TWh)': ('float', None, True),
                                                    'natural_gas_resource (Mt)': ('float', None, True),
                                                    'biogas (TWh)': ('float', None, True),
                                                    'mono_ethanol_amine_resource (Mt)': ('float', None, True),
                                                    'wet_biomass (Mt)': ('float', None, True),
                                                    'sodium_hydroxide_resource (Mt)': ('float', None, True),
                                                    'natural_oil_resource (TWh)': ('float', None, True),
                                                    'methanol_resource (Mt)': ('float', None, True),
                                                    'coal_resource (Mt)': ('float', None, True),
                                                    'biomass_dry (TWh)': ('float', None, True),
                                                     'water_resource (Mt)': ('float', None, True),
                                                    'methane (TWh)': ('float', None, True),
                                                    'solid_fuel (TWh)': ('float', None, True),
                                                    'wood (Mt)': ('float', None, True),
                                                    'carbon_capture (Mt)': ('float', None, True),
                                                    'dioxygen_resource (Mt)': ('float', None, True),
                                                    'electricity (TWh)': ('float', None, True),
                                                    'hydrogen.gaseous_hydrogen (TWh)': ('float', None, True),}}
                        dynamic_inputs[f'{energy}.{GlossaryCore.EnergyProductionValue}'] = {
                            'type': 'dataframe', 'unit': 'PWh',
                            'visibility': SoSWrapp.SHARED_VISIBILITY,
                            'namespace': 'ns_energy',
                            'dataframe_descriptor': {GlossaryCore.Years: ('float', None, True),
                                                     'hydrogen.gaseous_hydrogen': ('float', None, True),
                                                    'O2 (Mt)': ('float', None, True),
                                                    'carbon_resource (Mt)': ('float', None, True),
                                                    'fuel.liquid_fuel': ('float', None, True),
                                                    'kerosene (TWh)': ('float', None, True),
                                                    'gasoline (TWh)': ('float', None, True),
                                                    'liquefied_petroleum_gas (TWh)': ('float', None, True),
                                                    'heating_oil (TWh)': ('float', None, True),
                                                    'ultra_low_sulfur_diesel (TWh)': ('float', None, True),
                                                    'fuel.hydrotreated_oil_fuel': ('float', None, True),
                                                    'electricity': ('float', None, True),
                                                    'N2O (Mt)': ('float', None, True),
                                                    'methane': ('float', None, True),
                                                    'carbon_capture (Mt)': ('float', None, True),
                                                    'biogas': ('float', None, True),
                                                    'fuel.biodiesel': ('float', None, True),
                                                    'glycerol_resource (Mt)': ('float', None, True),
                                                    'solid_fuel': ('float', None, True),
                                                    'CO2_resource (Mt)': ('float', None, True),
                                                    'CH4 (Mt)': ('float', None, True),
                                                    'CO2 from Flue Gas (Mt)': ('float', None, True),
                                                    'syngas': ('float', None, True),
                                                    'char (Mt)': ('float', None, True),
                                                    'bio_oil (Mt)': ('float', None, True),
                                                    'water_resource (Mt)': ('float', None, True),
                                                    'dioxygen_resource (Mt)': ('float', None, True),
                                                    'hydrogen.liquid_hydrogen': ('float', None, True),}}

        if GlossaryCore.ccs_list in self.get_data_in():
            ccs_list = self.get_sosdisc_inputs(GlossaryCore.ccs_list)
            if ccs_list is not None:
                for ccs in ccs_list:
                    dynamic_inputs[f'{ccs}.{GlossaryCore.EnergyProductionValue}'] = {
                        'type': 'dataframe', 'unit': 'PWh',
                        'visibility': SoSWrapp.SHARED_VISIBILITY,
                        'namespace': 'ns_ccs',
                        'dataframe_descriptor': {GlossaryCore.Years: ('float', None, True),
                                                 'carbon_capture': ('float', None, True),
                                                 'carbon_storage': ('float', None, True),
                                                 'CO2 from Flue Gas (Mt)': ('float', None, True),

                                                 }
                                                 }


        self.add_inputs(dynamic_inputs)
        self.add_outputs(dynamic_outputs)

    def run(self):
        # -- get inputs
        inputs_dict_orig = self.get_sosdisc_inputs()
        # -- configure class with inputs
        # -- biomass dry values are coming from agriculture mix discipline, but needs to be used in model with biomass dry name
        inputs_dict = {}
        inputs_dict.update(inputs_dict_orig)
        energy_list = self.get_sosdisc_inputs(GlossaryCore.energy_list)
        if 'biomass_dry' in energy_list:
            inputs_dict[f'{BiomassDry.name}.{GlossaryCore.EnergyConsumptionValue}'] = inputs_dict_orig.pop(
                f'{AgricultureMixDiscipline.name}.{GlossaryCore.EnergyConsumptionValue}')
            inputs_dict[f'{BiomassDry.name}.{GlossaryCore.EnergyProductionValue}'] = inputs_dict_orig.pop(
                f'{AgricultureMixDiscipline.name}.{GlossaryCore.EnergyProductionValue}')
            inputs_dict[f'{BiomassDry.name}.CO2_per_use'] = inputs_dict_orig.pop(
                f'{AgricultureMixDiscipline.name}.CO2_per_use')
        self.model.configure_parameters_update(inputs_dict)
        CO2_sources, CO2_sinks = self.model.compute_CO2_emissions()

        outputs_dict = {
            'CO2_emissions_by_use_sources': CO2_sources,
            'CO2_emissions_by_use_sinks': CO2_sinks,
        }
        self.store_sos_outputs_values(outputs_dict)

    def compute_sos_jacobian(self):
        inputs_dict = self.get_sosdisc_inputs()
        outputs_dict = self.get_sosdisc_outputs()
        years = np.arange(inputs_dict[GlossaryCore.YearStart],
                          inputs_dict[GlossaryCore.YearEnd] + 1)
        energy_list = inputs_dict[GlossaryCore.energy_list]
        ccs_list = inputs_dict[GlossaryCore.ccs_list]
        scaling_factor_energy_production = inputs_dict['scaling_factor_energy_production']
        scaling_factor_energy_consumption = inputs_dict['scaling_factor_energy_consumption']
        CO2_emissions_by_use_sources = outputs_dict['CO2_emissions_by_use_sources']
        CO2_emissions_by_use_sinks = outputs_dict['CO2_emissions_by_use_sinks']
        energy_production_detailed = self.get_sosdisc_inputs(
            GlossaryCore.EnergyProductionDetailedValue)

        # ------------------------------------#
        # -- CO2 emissions sources gradients--#
        # ------------------------------------#
        dtot_co2_emissions_sources = self.model.compute_grad_CO2_emissions_sources(
            energy_production_detailed)

        for key, value in dtot_co2_emissions_sources.items():
            co2_emission_column = key.split(' vs ')[0]
            energy_prod_info = key.split(' vs ')[1]
            energy = energy_prod_info.split('#')[0]
            last_part_key = energy_prod_info.split('#')[1]
            if co2_emission_column in CO2_emissions_by_use_sources.columns and energy in energy_list:
                ns_energy = energy
                if energy == BiomassDry.name:
                    ns_energy = AgricultureMixDiscipline.name
                if last_part_key == 'prod':
                    if 'Total CO2 by use' in co2_emission_column:
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_by_use_sources',
                             co2_emission_column), (GlossaryCore.EnergyProductionDetailedValue, f'production {energy} (TWh)'),
                            np.identity(len(years)) * value / 1e3)
                    else:
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_by_use_sources',
                             co2_emission_column), (f'{ns_energy}.{GlossaryCore.EnergyProductionValue}', energy),
                            np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)
                elif last_part_key == 'cons':
                    for energy_df in energy_list:
                        list_columnsenergycons = list(
                            inputs_dict[f'{energy_df}.{GlossaryCore.EnergyConsumptionValue}'].columns)
                        if f'{energy} (TWh)' in list_columnsenergycons:
                            self.set_partial_derivative_for_other_types(
                                ('CO2_emissions_by_use_sources', co2_emission_column), (
                                    f'{energy_df}.{GlossaryCore.EnergyConsumptionValue}', f'{energy} (TWh)'),
                                np.identity(len(years)) * scaling_factor_energy_consumption * value / 1e3)
                elif last_part_key == 'co2_per_use':
                    self.set_partial_derivative_for_other_types(
                        ('CO2_emissions_by_use_sources',
                         co2_emission_column), (f'{ns_energy}.CO2_per_use', 'CO2_per_use'),
                        np.identity(len(years)) * value / 1e3)

                else:
                    very_last_part_key = energy_prod_info.split('#')[2]
                    if very_last_part_key == 'prod':
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_by_use_sources', co2_emission_column), (
                                f'{ns_energy}.{GlossaryCore.EnergyProductionValue}', last_part_key),
                            np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)
                    elif very_last_part_key == 'cons':
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_by_use_sources', co2_emission_column), (
                                f'{ns_energy}.{GlossaryCore.EnergyConsumptionValue}', last_part_key),
                            np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)

            # gradient for carbone capture and storage technos producing co2
            elif co2_emission_column in CO2_emissions_by_use_sources.columns and energy in ccs_list:
                ns_energy = energy
                if last_part_key not in ['co2_per_use', 'cons', 'prod']:
                    very_last_part_key = energy_prod_info.split('#')[2]
                    if very_last_part_key == 'prod':
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_by_use_sources', co2_emission_column), (
                                f'{ns_energy}.{GlossaryCore.EnergyProductionValue}', last_part_key),
                            np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)

        # ------------------------------------#
        # -- CO2 emissions sinks gradients--#
        # ------------------------------------#
        dtot_co2_emissions_sinks = self.model.compute_grad_CO2_emissions_sinks(
            energy_production_detailed)

        for key, value in dtot_co2_emissions_sinks.items():
            co2_emission_column = key.split(' vs ')[0]
            energy_prod_info = key.split(' vs ')[1]
            energy = energy_prod_info.split('#')[0]
            last_part_key = energy_prod_info.split('#')[1]
            if co2_emission_column in CO2_emissions_by_use_sinks.columns and energy in energy_list:
                ns_energy = energy
                if energy == BiomassDry.name:
                    ns_energy = AgricultureMixDiscipline.name
                if last_part_key == 'prod':
                    self.set_partial_derivative_for_other_types(
                        ('CO2_emissions_by_use_sinks',
                         co2_emission_column), (f'{ns_energy}.{GlossaryCore.EnergyProductionValue}', energy),
                        np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)
                elif last_part_key == 'cons':
                    for energy_df in energy_list:
                        list_columnsenergycons = list(
                            inputs_dict[f'{energy_df}.{GlossaryCore.EnergyConsumptionValue}'].columns)
                        if f'{energy} (TWh)' in list_columnsenergycons:
                            self.set_partial_derivative_for_other_types(
                                ('CO2_emissions_by_use_sinks', co2_emission_column), (
                                    f'{energy_df}.{GlossaryCore.EnergyConsumptionValue}', f'{energy} (TWh)'),
                                np.identity(len(years)) * scaling_factor_energy_consumption * value / 1e3)
                elif last_part_key == 'co2_per_use':
                    self.set_partial_derivative_for_other_types(
                        ('CO2_emissions_by_use_sinks',
                         co2_emission_column), (f'{ns_energy}.CO2_per_use', 'CO2_per_use'),
                        np.identity(len(years)) * value / 1e3)

                else:
                    very_last_part_key = energy_prod_info.split('#')[2]
                    if very_last_part_key == 'prod':
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_by_use_sinks', co2_emission_column), (
                                f'{ns_energy}.{GlossaryCore.EnergyProductionValue}', last_part_key),
                            np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)
                    elif very_last_part_key == 'cons':
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_by_use_sinks', co2_emission_column), (
                                f'{ns_energy}.{GlossaryCore.EnergyConsumptionValue}', last_part_key),
                            np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['CO2 sources', 'CO2 sinks']

        chart_filters.append(ChartFilter(
            'Charts', chart_list, chart_list, 'charts'))

        return chart_filters

    def get_post_processing_list(self, filters=None):

        # For the outputs, making a graph for block fuel vs range and blocktime vs
        # range

        instanciated_charts = []
        charts = []
        if filters is not None:
            for chart_filter in filters:
                charts = chart_filter.selected_values

        if 'CO2 sources' in charts:

            new_chart = self.get_chart_CO2_sources()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'CO2 sinks' in charts:
            new_chart = self.get_chart_CO2_sinks()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_chart_CO2_sources(self):
        CO2_emissions_by_use_sources = self.get_sosdisc_outputs(
            'CO2_emissions_by_use_sources')

        chart_name = f'CO2 emissions by consumption - Sources'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryCore.Years, 'CO2 emissions (Gt)', chart_name=chart_name)

        for col in CO2_emissions_by_use_sources:
            if col != GlossaryCore.Years:
                new_serie = InstanciatedSeries(list(CO2_emissions_by_use_sources[GlossaryCore.Years].values),
                                               list(CO2_emissions_by_use_sources[col].values),
                                               col, 'lines')

                new_chart.series.append(new_serie)

        return new_chart

    def get_chart_CO2_sinks(self):
        CO2_emissions_by_use_sinks = self.get_sosdisc_outputs(
            'CO2_emissions_by_use_sinks')

        chart_name = f'CO2 emissions by consumption - Sinks'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryCore.Years, 'CO2 emissions (Gt)', chart_name=chart_name)

        for col in CO2_emissions_by_use_sinks:
            if col != GlossaryCore.Years:
                new_serie = InstanciatedSeries(list(CO2_emissions_by_use_sinks[GlossaryCore.Years].values),
                                               list(CO2_emissions_by_use_sinks[col].values),
                                               col, 'lines')

                new_chart.series.append(new_serie)

        return new_chart
