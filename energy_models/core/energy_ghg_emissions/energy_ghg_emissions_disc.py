'''
Copyright 2022 Airbus SAS
Modifications on 2023/04/19-2023/11/16 Copyright 2023 Capgemini

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
import logging

import numpy as np

from climateeconomics.core.core_emissions.ghg_emissions_model import GHGEmissions
from climateeconomics.core.core_witness.climateeco_discipline import ClimateEcoDiscipline
from climateeconomics.sos_wrapping.sos_wrapping_agriculture.agriculture.agriculture_mix_disc import \
    AgricultureMixDiscipline
from climateeconomics.sos_wrapping.sos_wrapping_emissions.ghgemissions.ghgemissions_discipline import \
    GHGemissionsDiscipline
from energy_models.core.ccus.ccus import CCUS
from energy_models.core.energy_ghg_emissions.energy_ghg_emissions import EnergyGHGEmissions
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
from energy_models.glossaryenergy import GlossaryEnergy
from sostrades_core.execution_engine.sos_wrapp import SoSWrapp
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart


class EnergyGHGEmissionsDiscipline(SoSWrapp):
    # ontology information
    _ontology_data = {
        'label': 'Energy GHG emissions Model',
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
        GlossaryEnergy.YearStart: ClimateEcoDiscipline.YEAR_START_DESC_IN,
        GlossaryEnergy.YearEnd: GlossaryEnergy.YearEndVar,
        GlossaryEnergy.energy_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                                     'possible_values': EnergyMix.energy_list,
                                     'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy_study',
                                     'editable': False, 'structuring': True},
        'scaling_factor_energy_production': {'type': 'float', 'default': 1e3, 'unit': '-', 'user_level': 2,
                                             'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'scaling_factor_energy_consumption': {'type': 'float', 'default': 1e3, 'unit': '-', 'user_level': 2,
                                              'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'GHG_global_warming_potential20': {'type': 'dict', 'subtype_descriptor': {'dict': 'float'},
                                           'unit': 'kgCO2eq/kg',
                                           'default': ClimateEcoDiscipline.GWP_20_default,
                                           'visibility': ClimateEcoDiscipline.SHARED_VISIBILITY,
                                           'namespace': GlossaryEnergy.NS_WITNESS, 'user_level': 3},
        'GHG_global_warming_potential100': {'type': 'dict', 'subtype_descriptor': {'dict': 'float'},
                                            'unit': 'kgCO2eq/kg',
                                            'default': ClimateEcoDiscipline.GWP_100_default,
                                            'visibility': ClimateEcoDiscipline.SHARED_VISIBILITY,
                                            'namespace': GlossaryEnergy.NS_WITNESS, 'user_level': 3},
        GlossaryEnergy.EnergyProductionDetailedValue: {'type': 'dataframe', 'unit': 'TWh',
                                                       'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                       'namespace': 'ns_energy',
                                                       'dataframe_descriptor': {
                                                           GlossaryEnergy.Years: ('float', None, True),
                                                           f'production {GlossaryEnergy.methane} (TWh)': ('float', None, True),
                                                           f'production {GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen} (TWh)': ('float', None, True),
                                                           f'production {GlossaryEnergy.biogas} (TWh)': ('float', None, True),
                                                           f'production {GlossaryEnergy.syngas} (TWh)': ('float', None, True),
                                                           f'production {GlossaryEnergy.fuel}.{GlossaryEnergy.liquid_fuel} (TWh)': ('float', None, True),
                                                           f'production {GlossaryEnergy.fuel}.{GlossaryEnergy.hydrotreated_oil_fuel} (TWh)': ('float', None, True),
                                                           f'production {GlossaryEnergy.solid_fuel} (TWh)': ('float', None, True),
                                                           f'production {GlossaryEnergy.biomass_dry} (TWh)': ('float', None, True),
                                                           f'production {GlossaryEnergy.electricity} (TWh)': ('float', None, True),
                                                           f'production {GlossaryEnergy.fuel}.{GlossaryEnergy.biodiesel} (TWh)': ('float', None, True),
                                                           f'production {GlossaryEnergy.hydrogen}.{GlossaryEnergy.liquid_hydrogen} (TWh)': ('float', None, True),
                                                           f'production {GlossaryEnergy.carbon_capture} (Mt)': ('float', None, True),
                                                           f'production {GlossaryEnergy.carbon_storage} (Mt)': ('float', None, True),
                                                           'Total production': ('float', None, True),
                                                           'Total production (uncut)': ('float', None, True),
                                                           },
                                                       },
        'co2_emissions_ccus_Gt': {'type': 'dataframe', 'unit': 'Gt',
                                  'visibility': ClimateEcoDiscipline.SHARED_VISIBILITY,
                                  'namespace': GlossaryEnergy.NS_CCS,
                                  'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                           'carbon_storage Limited by capture (Gt)': (
                                                               'float', None, True), }, }
        ,
        'co2_emissions_needed_by_energy_mix': {'type': 'dataframe', 'unit': 'Gt',
                                               'visibility': ClimateEcoDiscipline.SHARED_VISIBILITY,
                                               'namespace': 'ns_energy',
                                               'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                                        'carbon_capture needed by energy mix (Gt)': (
                                                                        'float', None, True), }},
        GlossaryEnergy.ccs_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                                  'possible_values': CCUS.ccs_list,
                                  'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy_study',
                                  'editable': False,
                                  'structuring': True},
    }

    DESC_OUT = {
        'CO2_emissions_sources': {'type': 'dataframe', 'unit': 'Gt'},
        'CO2_emissions_sinks': {'type': 'dataframe', 'unit': 'Gt'},
        'GHG_total_energy_emissions': {'type': 'dataframe', 'unit': 'Gt',
                                       'visibility': ClimateEcoDiscipline.SHARED_VISIBILITY,
                                       'namespace': GlossaryEnergy.NS_WITNESS},
        'GHG_emissions_per_energy': {'type': 'dict', 'subtype_descriptor': {'dict': 'dataframe'}, 'unit': 'Gt'},
        'GWP_emissions': {'type': 'dataframe', 'unit': 'GtCO2eq'},
    }

    name = f'{GHGemissionsDiscipline.name}.Energy'

    def __init__(self, sos_name, logger: logging.Logger):
        super().__init__(sos_name, logger)
        self.model = None

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.model = EnergyGHGEmissions(self.name)
        self.model.configure_parameters(inputs_dict)

    def setup_sos_disciplines(self):

        dynamic_inputs = {}
        dynamic_outputs = {}

        if GlossaryEnergy.energy_list in self.get_data_in():
            energy_list = self.get_sosdisc_inputs(GlossaryEnergy.energy_list)
            if energy_list is not None:
                for energy in energy_list:
                    if energy == BiomassDry.name:
                        for ghg in GHGEmissions.GHG_TYPE_LIST:
                            dynamic_inputs[f'{AgricultureMixDiscipline.name}.{ghg}_per_use'] = {
                                'type': 'dataframe', 'unit': 'kg/kWh', 'namespace': GlossaryEnergy.NS_WITNESS,
                                'visibility': SoSWrapp.SHARED_VISIBILITY,
                                'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                         'N2O_per_use': ('float', None, True),
                                                         'CO2_per_use': ('float', None, True),
                                                         'CH4_per_use': ('float', None, True), }}
                        dynamic_inputs[f'{AgricultureMixDiscipline.name}.{GlossaryEnergy.EnergyConsumptionValue}'] = {
                            'type': 'dataframe', 'unit': 'PWh', 'namespace': GlossaryEnergy.NS_WITNESS,
                            'visibility': SoSWrapp.SHARED_VISIBILITY,
                            'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                     f'{GlossaryEnergy.electricity} (TWh)': ('float', None, True),
                                                     'CO2_resource (Mt)': ('float', None, True), }}

                        dynamic_inputs[f'{AgricultureMixDiscipline.name}.{GlossaryEnergy.EnergyProductionValue}'] = {
                            'type': 'dataframe', 'unit': 'PWh', 'namespace': GlossaryEnergy.NS_WITNESS,
                            'visibility': SoSWrapp.SHARED_VISIBILITY,
                            'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                     GlossaryEnergy.biomass_dry: ('float', None, True),
                                                     'CO2_resource (Mt)': ('float', None, True), }}
                    else:
                        for ghg in GHGEmissions.GHG_TYPE_LIST:
                            dynamic_inputs[f'{energy}.{ghg}_per_use'] = {
                                'type': 'dataframe', 'unit': 'kg/kWh',
                                'visibility': SoSWrapp.SHARED_VISIBILITY,
                                'namespace': 'ns_energy',
                                'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                         'N2O_per_use': ('float', None, True),
                                                         'CO2_per_use': ('float', None, True),
                                                         'CH4_per_use': ('float', None, True), }
                            }
                        dynamic_inputs[f'{energy}.{GlossaryEnergy.EnergyConsumptionValue}'] = {
                            'type': 'dataframe', 'unit': 'PWh',
                            'visibility': SoSWrapp.SHARED_VISIBILITY,
                            'namespace': 'ns_energy',
                            'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                     'platinum_resource (Mt)': ('float', None, True),
                                                     f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}': ('float', None, True),
                                                     'O2 (Mt)': ('float', None, True),
                                                     'carbon_resource (Mt)': ('float', None, True),
                                                     'oil_resource (Mt)': ('float', None, True),
                                                     f'{GlossaryEnergy.syngas} (TWh)': ('float', None, True),
                                                     f'{GlossaryEnergy.fuel}.{GlossaryEnergy.liquid_fuel}': ('float', None, True),
                                                     f'{GlossaryEnergy.kerosene} (TWh)': ('float', None, True),
                                                     f'{GlossaryEnergy.gasoline} (TWh)': ('float', None, True),
                                                     f'{GlossaryEnergy.liquefied_petroleum_gas} (TWh)': ('float', None, True),
                                                     f'{GlossaryEnergy.heating_oil} (TWh)': ('float', None, True),
                                                     f'{GlossaryEnergy.ultra_low_sulfur_diesel} (TWh)': ('float', None, True),
                                                     f'{GlossaryEnergy.fuel}.{GlossaryEnergy.hydrotreated_oil_fuel}': ('float', None, True),
                                                     'copper_resource (Mt)': ('float', None, True),
                                                     'uranium_resource (Mt)': ('float', None, True),
                                                     f'{GlossaryEnergy.fuel}.{GlossaryEnergy.liquid_fuel} (TWh)': ('float', None, True),
                                                     GlossaryEnergy.electricity: ('float', None, True),
                                                     'N2O (Mt)': ('float', None, True),
                                                     'natural_gas_resource (Mt)': ('float', None, True),
                                                     f'{GlossaryEnergy.biogas} (TWh)': ('float', None, True),
                                                     'mono_ethanol_amine_resource (Mt)': ('float', None, True),
                                                     GlossaryEnergy.methane: ('float', None, True),
                                                     f'{GlossaryEnergy.wet_biomass} (Mt)': ('float', None, True),
                                                     GlossaryEnergy.biogas: ('float', None, True),
                                                     'sodium_hydroxide_resource (Mt)': ('float', None, True),
                                                     'natural_oil_resource (TWh)': ('float', None, True),
                                                     'methanol_resource (Mt)': ('float', None, True),
                                                     f'{GlossaryEnergy.fuel}.{GlossaryEnergy.biodiesel}': ('float', None, True),
                                                     'glycerol_resource (Mt)': ('float', None, True),
                                                     'coal_resource (Mt)': ('float', None, True),
                                                     GlossaryEnergy.solid_fuel: ('float', None, True),
                                                     'CO2_resource (Mt)': ('float', None, True),
                                                     f'{GlossaryEnergy.methane} (TWh)': ('float', None, True),
                                                     f'{GlossaryEnergy.solid_fuel} (TWh)': ('float', None, True),
                                                     'wood (Mt)': ('float', None, True),
                                                     f'{GlossaryEnergy.carbon_capture} (Mt)': ('float', None, True),
                                                     GlossaryEnergy.syngas: ('float', None, True),
                                                     'char (Mt)': ('float', None, True),
                                                     'bio_oil (Mt)': ('float', None, True),
                                                     f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen} (TWh)': ('float', None, True),
                                                     f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.liquid_hydrogen}': ('float', None, True),
                                                     f'{GlossaryEnergy.biomass_dry} (TWh)': ('float', None, True),
                                                     f'{GlossaryEnergy.electricity} (TWh)': ('float', None, True),
                                                     'water_resource (Mt)': ('float', None, True),
                                                     'dioxygen_resource (Mt)': ('float', None, True),
                                                     }
                        }
                        dynamic_inputs[f'{energy}.{GlossaryEnergy.EnergyProductionValue}'] = {
                            'type': 'dataframe', 'unit': 'PWh',
                            'visibility': SoSWrapp.SHARED_VISIBILITY,
                            'namespace': 'ns_energy',
                            'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                     'platinum_resource (Mt)': ('float', None, True),
                                                     f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}': ('float', None, True),
                                                     'O2 (Mt)': ('float', None, True),
                                                     'carbon_resource (Mt)': ('float', None, True),
                                                     'oil_resource (Mt)': ('float', None, True),
                                                     f'{GlossaryEnergy.syngas} (TWh)': ('float', None, True),
                                                     f'{GlossaryEnergy.fuel}.{GlossaryEnergy.liquid_fuel}': ('float', None, True),
                                                     f'{GlossaryEnergy.kerosene} (TWh)': ('float', None, True),
                                                     f'{GlossaryEnergy.gasoline} (TWh)': ('float', None, True),
                                                     f'{GlossaryEnergy.liquefied_petroleum_gas} (TWh)': ('float', None, True),
                                                     f'{GlossaryEnergy.heating_oil} (TWh)': ('float', None, True),
                                                     f'{GlossaryEnergy.ultra_low_sulfur_diesel} (TWh)': ('float', None, True),
                                                     f'{GlossaryEnergy.fuel}.{GlossaryEnergy.hydrotreated_oil_fuel}': ('float', None, True),
                                                     'copper_resource (Mt)': ('float', None, True),
                                                     'uranium_resource (Mt)': ('float', None, True),
                                                     f'{GlossaryEnergy.fuel}.{GlossaryEnergy.liquid_fuel} (TWh)': ('float', None, True),
                                                     GlossaryEnergy.electricity: ('float', None, True),
                                                     'N2O (Mt)': ('float', None, True),
                                                     'natural_gas_resource (Mt)': ('float', None, True),
                                                     f'{GlossaryEnergy.biogas} (TWh)': ('float', None, True),
                                                     'mono_ethanol_amine_resource (Mt)': ('float', None, True),
                                                     GlossaryEnergy.methane: ('float', None, True),
                                                     f'{GlossaryEnergy.wet_biomass} (Mt)': ('float', None, True),
                                                     GlossaryEnergy.biogas: ('float', None, True),
                                                     'sodium_hydroxide_resource (Mt)': ('float', None, True),
                                                     'natural_oil_resource (TWh)': ('float', None, True),
                                                     'methanol_resource (Mt)': ('float', None, True),
                                                     f'{GlossaryEnergy.fuel}.{GlossaryEnergy.biodiesel}': ('float', None, True),
                                                     'glycerol_resource (Mt)': ('float', None, True),
                                                     'coal_resource (Mt)': ('float', None, True),
                                                     GlossaryEnergy.solid_fuel: ('float', None, True),
                                                     'CO2_resource (Mt)': ('float', None, True),
                                                     f'{GlossaryEnergy.methane} (TWh)': ('float', None, True),
                                                     f'{GlossaryEnergy.solid_fuel} (TWh)': ('float', None, True),
                                                     'wood (Mt)': ('float', None, True),
                                                     f'{GlossaryEnergy.carbon_capture} (Mt)': ('float', None, True),
                                                     GlossaryEnergy.syngas: ('float', None, True),
                                                     'char (Mt)': ('float', None, True),
                                                     'bio_oil (Mt)': ('float', None, True),
                                                     f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen} (TWh)': ('float', None, True),
                                                     f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.liquid_hydrogen}': ('float', None, True),
                                                     'CH4 (Mt)': ('float', None, True),
                                                     'CO2 from Flue Gas (Mt)': ('float', None, True),
                                                     'water_resource (Mt)': ('float', None, True),
                                                     'dioxygen_resource (Mt)': ('float', None, True),
                                                     }
                        }
            if GlossaryEnergy.ccs_list in self.get_data_in():
                ccs_list = self.get_sosdisc_inputs(GlossaryEnergy.ccs_list)
                if ccs_list is not None:
                    for ccs in ccs_list:
                        dynamic_inputs[f'{ccs}.{GlossaryEnergy.EnergyProductionValue}'] = {
                            'type': 'dataframe', 'unit': 'PWh',
                            'visibility': SoSWrapp.SHARED_VISIBILITY,
                            'namespace': GlossaryEnergy.NS_CCS,
                            'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                     GlossaryEnergy.carbon_capture: ('float', None, True),
                                                     GlossaryEnergy.carbon_storage: ('float', None, True),
                                                     'CO2 from Flue Gas (Mt)': ('float', None, True),
                                                     }
                        }

        self.add_inputs(dynamic_inputs)
        self.add_outputs(dynamic_outputs)

    def run(self):
        # -- get inputs
        inputs_dict = self.get_sosdisc_inputs()

        self.model.configure_parameters_update(inputs_dict)
        self.model.compute_ghg_emissions()

        outputs_dict = {
            'GHG_total_energy_emissions': self.model.ghg_total_emissions,
            'GHG_emissions_per_energy': self.model.ghg_production_dict,
            'CO2_emissions_sources': self.model.CO2_sources_Gt,
            'CO2_emissions_sinks': self.model.CO2_sinks_Gt,
            'GWP_emissions': self.model.gwp_emissions

        }
        self.store_sos_outputs_values(outputs_dict)

    def compute_sos_jacobian(self):
        inputs_dict = self.get_sosdisc_inputs()
        outputs_dict = self.get_sosdisc_outputs()
        years = np.arange(inputs_dict[GlossaryEnergy.YearStart],
                          inputs_dict[GlossaryEnergy.YearEnd] + 1)
        energy_list = inputs_dict[GlossaryEnergy.energy_list]
        ccs_list = inputs_dict[GlossaryEnergy.ccs_list]

        scaling_factor_energy_production = inputs_dict['scaling_factor_energy_production']
        scaling_factor_energy_consumption = inputs_dict['scaling_factor_energy_consumption']
        CO2_emissions_sources = outputs_dict['CO2_emissions_sources']
        CO2_emissions_sinks = outputs_dict['CO2_emissions_sinks']
        energy_production_detailed = inputs_dict[
            GlossaryEnergy.EnergyProductionDetailedValue]

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
            if co2_emission_column in CO2_emissions_sources.columns and energy in energy_list:
                ns_energy = energy
                if energy == BiomassDry.name:
                    ns_energy = AgricultureMixDiscipline.name
                if last_part_key == 'prod':
                    if 'Total CO2 by use' in co2_emission_column:
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_sources',
                             co2_emission_column),
                            (GlossaryEnergy.EnergyProductionDetailedValue, f'production {energy} (TWh)'),
                            np.identity(len(years)) * value / 1e3)
                    else:
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_sources',
                             co2_emission_column), (f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', energy),
                            np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)
                elif last_part_key == 'cons':
                    for energy_df in energy_list:
                        list_columnsenergycons = list(
                            inputs_dict[f'{energy_df}.{GlossaryEnergy.EnergyConsumptionValue}'].columns)
                        if f'{energy} (TWh)' in list_columnsenergycons:
                            self.set_partial_derivative_for_other_types(
                                ('CO2_emissions_sources', co2_emission_column), (
                                    f'{energy_df}.{GlossaryEnergy.EnergyConsumptionValue}', f'{energy} (TWh)'),
                                np.identity(len(years)) * scaling_factor_energy_consumption * value / 1e3)
                #                 elif last_part_key == 'co2_per_use':
                #                     self.set_partial_derivative_for_other_types(
                #                         ('CO2_emissions_sources',
                #                          co2_emission_column), (f'{ns_energy}.CO2_per_use', 'CO2_per_use'),
                #                         np.identity(len(years)) * value / 1e3)

                else:
                    very_last_part_key = energy_prod_info.split('#')[2]
                    if very_last_part_key == 'prod':
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_sources', co2_emission_column), (
                                f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', last_part_key),
                            np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)
                        self.set_partial_derivative_for_other_types(
                            ('GHG_total_energy_emissions', 'Total CO2 emissions'), (
                                f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', last_part_key),
                            np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)
                    elif very_last_part_key == 'cons':
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_sources', co2_emission_column), (
                                f'{ns_energy}.{GlossaryEnergy.EnergyConsumptionValue}', last_part_key),
                            np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)
                        self.set_partial_derivative_for_other_types(
                            ('GHG_total_energy_emissions', 'Total CO2 emissions'), (
                                f'{ns_energy}.{GlossaryEnergy.EnergyConsumptionValue}', last_part_key),
                            np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)

            elif co2_emission_column in CO2_emissions_sources.columns and energy in ccs_list:
                ns_energy = energy
                if last_part_key not in ['co2_per_use', 'cons', 'prod']:
                    very_last_part_key = energy_prod_info.split('#')[2]
                    if very_last_part_key == 'prod':
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_sources', co2_emission_column), (
                                f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', last_part_key),
                            np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)
                        self.set_partial_derivative_for_other_types(
                            ('GHG_total_energy_emissions', 'Total CO2 emissions'), (
                                f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', last_part_key),
                            np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)

        dtot_co2_emissions = self.model.compute_grad_total_co2_emissions(
            energy_production_detailed)

        for energy in energy_list:
            max_prod_grad = dtot_co2_emissions_sources[
                f'Total CO2 by use (Gt) vs {energy}#co2_per_use']
            if energy == GlossaryEnergy.biomass_dry:
                for ghg in self.model.GHG_TYPE_LIST:
                    self.set_partial_derivative_for_other_types(
                        ('GHG_total_energy_emissions',
                         f'Total {ghg} emissions'),
                        (f'{AgricultureMixDiscipline.name}.{ghg}_per_use', f'{ghg}_per_use'),
                        np.identity(len(years)) * max_prod_grad / 1e3)

            else:
                for ghg in self.model.GHG_TYPE_LIST:
                    self.set_partial_derivative_for_other_types(
                        ('GHG_total_energy_emissions',
                         f'Total {ghg} emissions'), (f'{energy}.{ghg}_per_use', f'{ghg}_per_use'),
                        np.identity(len(years)) * max_prod_grad / 1e3)
            for ghg in self.model.GHG_TYPE_LIST:
                value = dtot_co2_emissions[f'Total {ghg} emissions vs prod{energy}']
                self.set_partial_derivative_for_other_types(
                    ('GHG_total_energy_emissions',
                     f'Total {ghg} emissions'),
                    (GlossaryEnergy.EnergyProductionDetailedValue, f'production {energy} (TWh)'),
                    np.identity(len(years)) * value / 1e3)
            ns_energy = energy
            if energy == GlossaryEnergy.biomass_dry:
                ns_energy = AgricultureMixDiscipline.name
            for col in self.model.sub_production_dict[energy].keys():
                for ghg in self.model.GHG_TYPE_LIST:
                    if col == f'{ghg} {self.model.ghg_input_unit}':
                        self.set_partial_derivative_for_other_types(
                            ('GHG_total_energy_emissions',
                             f'Total {ghg} emissions'), (
                                f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', col),
                            np.identity(len(years)))

        # ------------------------------------#
        # -- CO2 emissions sinks gradients--#
        # ------------------------------------#
        dtot_co2_emissions_sinks = self.model.compute_grad_CO2_emissions_sinks()

        for key, value in dtot_co2_emissions_sinks.items():
            co2_emission_column = key.split(' vs ')[0]
            energy_prod_info = key.split(' vs ')[1]
            energy = energy_prod_info.split('#')[0]
            last_part_key = energy_prod_info.split('#')[1]
            if co2_emission_column in CO2_emissions_sinks.columns and energy in energy_list:
                ns_energy = energy
                if energy == BiomassDry.name:
                    ns_energy = AgricultureMixDiscipline.name
                if last_part_key == 'prod':
                    self.set_partial_derivative_for_other_types(
                        ('CO2_emissions_sinks',
                         co2_emission_column), (f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', energy),
                        np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)
                elif last_part_key == 'cons':
                    for energy_df in energy_list:
                        list_columnsenergycons = list(
                            inputs_dict[f'{energy_df}.{GlossaryEnergy.EnergyConsumptionValue}'].columns)
                        if f'{energy} (TWh)' in list_columnsenergycons:
                            self.set_partial_derivative_for_other_types(
                                ('CO2_emissions_sinks', co2_emission_column), (
                                    f'{energy_df}.{GlossaryEnergy.EnergyConsumptionValue}', f'{energy} (TWh)'),
                                np.identity(len(years)) * scaling_factor_energy_consumption * value / 1e3)
                elif last_part_key == 'co2_per_use':
                    self.set_partial_derivative_for_other_types(
                        ('CO2_emissions_sinks',
                         co2_emission_column), (f'{ns_energy}.CO2_per_use', 'CO2_per_use'),
                        np.identity(len(years)) * value / 1e3)
                else:
                    very_last_part_key = energy_prod_info.split('#')[2]
                    if very_last_part_key == 'prod':
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_sinks', co2_emission_column), (
                                f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', last_part_key),
                            np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)
                        self.set_partial_derivative_for_other_types(
                            ('GHG_total_energy_emissions',
                             f'Total CO2 emissions'), (
                                f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', last_part_key),
                            -np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)
                    elif very_last_part_key == 'cons':
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_sinks', co2_emission_column), (
                                f'{ns_energy}.{GlossaryEnergy.EnergyConsumptionValue}', last_part_key),
                            np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)
                        self.set_partial_derivative_for_other_types(
                            ('GHG_total_energy_emissions',
                             f'Total CO2 emissions'), (
                                f'{ns_energy}.{GlossaryEnergy.EnergyConsumptionValue}', last_part_key),
                            -np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)
        self.set_partial_derivative_for_other_types(
            ('GHG_total_energy_emissions',
             'Total CO2 emissions'), ('co2_emissions_ccus_Gt', 'carbon_storage Limited by capture (Gt)'),
            -np.identity(len(years)))
        self.set_partial_derivative_for_other_types(
            ('GHG_total_energy_emissions',
             'Total CO2 emissions'), ('co2_emissions_needed_by_energy_mix', 'carbon_capture needed by energy mix (Gt)'),
            -np.identity(len(years)))

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['Global Warming Potential', 'Total CO2 emissions',
                      'Emissions per energy',
                      'CO2 sources', 'CO2 sinks']

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

        if 'Global Warming Potential' in charts:
            for gwp_year in [20, 100]:
                new_chart = self.get_chart_gwp(gwp_year)
                if new_chart is not None:
                    instanciated_charts.append(new_chart)

        if 'Total CO2 emissions' in charts:

            new_chart = self.get_chart_total_co2_emissions()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'Emissions per energy' in charts:
            for ghg in EnergyGHGEmissions.GHG_TYPE_LIST:
                new_chart = self.get_chart_ghg_emissions_per_energy(ghg)
                if new_chart is not None:
                    instanciated_charts.append(new_chart)
        if 'CO2 sources' in charts:

            new_chart = self.get_chart_CO2_sources()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'CO2 sinks' in charts:
            new_chart = self.get_chart_CO2_sinks()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_chart_total_co2_emissions(self):
        GHG_total_energy_emissions = self.get_sosdisc_outputs(
            'GHG_total_energy_emissions')

        chart_name = f'Total CO2 emissions for energy sector'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'CO2 emissions [Gt]', chart_name=chart_name)

        new_serie = InstanciatedSeries(list(GHG_total_energy_emissions[GlossaryEnergy.Years].values),
                                       list(GHG_total_energy_emissions['Total CO2 emissions'].values),
                                       'lines')

        new_chart.series.append(new_serie)

        return new_chart

    def get_chart_gwp(self, gwp_year):
        GWP_emissions = self.get_sosdisc_outputs(
            'GWP_emissions')

        chart_name = f'Global warming potential for energy sector emissions at {gwp_year} years'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'GWP [GtCO2]', chart_name=chart_name, stacked_bar=True)

        for ghg in EnergyGHGEmissions.GHG_TYPE_LIST:
            new_serie = InstanciatedSeries(list(GWP_emissions[GlossaryEnergy.Years].values),
                                           list(GWP_emissions[f'{ghg}_{gwp_year}'].values),
                                           ghg, 'bar')

            new_chart.series.append(new_serie)

        return new_chart

    def get_chart_ghg_emissions_per_energy(self, ghg):
        GHG_emissions_per_energy = self.get_sosdisc_outputs(
            'GHG_emissions_per_energy')

        chart_name = f'{ghg} emissions per energy'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, f'{ghg} emissions [Mt]', chart_name=chart_name, stacked_bar=True)
        energy_list = self.get_sosdisc_inputs(GlossaryEnergy.energy_list)
        for energy in energy_list:
            ghg_energy = GHG_emissions_per_energy[ghg][[
                col for col in GHG_emissions_per_energy[ghg] if energy in col]].sum(axis=1).values
            if not (ghg_energy == 0).all():
                new_serie = InstanciatedSeries(list(GHG_emissions_per_energy[ghg][GlossaryEnergy.Years].values),
                                               list(ghg_energy),
                                               energy,
                                               'bar')

                new_chart.series.append(new_serie)

        return new_chart

    def get_chart_CO2_sources(self):
        CO2_emissions_sources = self.get_sosdisc_outputs(
            'CO2_emissions_sources')

        chart_name = f'CO2 emissions by consumption - Sources'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'CO2 emissions [Gt]', chart_name=chart_name)

        for col in CO2_emissions_sources:
            if col != GlossaryEnergy.Years:
                new_serie = InstanciatedSeries(list(CO2_emissions_sources[GlossaryEnergy.Years].values),
                                               list(CO2_emissions_sources[col].values),
                                               col, 'lines')

                new_chart.series.append(new_serie)

        return new_chart

    def get_chart_CO2_sinks(self):
        CO2_emissions_sinks = self.get_sosdisc_outputs(
            'CO2_emissions_sinks')

        chart_name = f'CO2 emissions by consumption - Sinks'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'CO2 emissions [Gt]', chart_name=chart_name)

        for col in CO2_emissions_sinks:
            if col != GlossaryEnergy.Years:
                new_serie = InstanciatedSeries(list(CO2_emissions_sinks[GlossaryEnergy.Years].values),
                                               list(CO2_emissions_sinks[col].values),
                                               col, 'lines')

                new_chart.series.append(new_serie)

        return new_chart
