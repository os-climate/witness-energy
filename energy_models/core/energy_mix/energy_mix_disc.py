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
from copy import deepcopy

import numpy as np
import pandas as pd
from plotly import graph_objects as go

from climateeconomics.core.core_witness.climateeco_discipline import ClimateEcoDiscipline
from climateeconomics.sos_wrapping.sos_wrapping_agriculture.agriculture.agriculture_mix_disc import \
    AgricultureMixDiscipline
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.core.stream_type.carbon_models.carbon_storage import CarbonStorage
from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import GaseousHydrogen
from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from energy_models.core.stream_type.energy_models.heat import lowtemperatureheat
from energy_models.core.stream_type.energy_models.heat import mediumtemperatureheat
from energy_models.core.stream_type.energy_models.liquid_fuel import LiquidFuel
from energy_models.core.stream_type.energy_models.liquid_hydrogen import LiquidHydrogen
from energy_models.core.stream_type.energy_models.solid_fuel import SolidFuel
from energy_models.core.stream_type.energy_models.syngas import Syngas
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.liquid_fuel.refinery.refinery_disc import RefineryDiscipline
from energy_models.models.methane.fossil_gas.fossil_gas_disc import FossilGasDiscipline
from sostrades_core.execution_engine.sos_wrapp import SoSWrapp
from sostrades_core.tools.base_functions.exp_min import compute_dfunc_with_exp_min, \
    compute_func_with_exp_min
from sostrades_core.tools.cst_manager.func_manager_common import get_dsmooth_dvariable
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart
from sostrades_core.tools.post_processing.pie_charts.instanciated_pie_chart import InstanciatedPieChart
from sostrades_core.tools.post_processing.plotly_native_charts.instantiated_plotly_native_chart import \
    InstantiatedPlotlyNativeChart
from sostrades_core.tools.post_processing.tables.instanciated_table import InstanciatedTable


class Energy_Mix_Discipline(SoSWrapp):
    # ontology information
    _ontology_data = {
        'label': 'Energy Mix Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-battery-full fa-fw',
        'version': '',
    }
    # All values used to calibrate heat loss percentage
    heat_tfc_2019 = 3561.87
    # + heat losses for transmission,distrib and transport
    heat_use_energy_2019 = 14181. + 232.59
    total_raw_prod_2019 = 183316.
    # total_losses_2019 = 2654.
    heat_losses_percentage_default = (heat_use_energy_2019 -
                                      heat_tfc_2019) / total_raw_prod_2019 * 100

    loss_percentage_default_dict = {
        energy: 0.0 for energy in EnergyMix.energy_list}
    loss_percentage_default_dict[GlossaryEnergy.methane] = 289.21 / \
                                              FossilGasDiscipline.initial_production * 100.0
    loss_percentage_default_dict[GlossaryEnergy.electricity] = 2012.15 / 24600.0 * 100.0
    loss_percentage_default_dict[f'{GlossaryEnergy.fuel}.{GlossaryEnergy.liquid_fuel}'] = 90.15 / \
                                                       RefineryDiscipline.initial_production * 100.0

    DESC_IN = {GlossaryEnergy.energy_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                                            'possible_values': EnergyMix.energy_list,
                                            'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy_study',
                                            'editable': False, 'structuring': True},
               GlossaryEnergy.ccs_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                                         'possible_values': EnergyMix.ccs_list,
                                         'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy_study',
                                         'editable': False, 'structuring': True},
               GlossaryEnergy.YearStart: ClimateEcoDiscipline.YEAR_START_DESC_IN,
               GlossaryEnergy.YearEnd: ClimateEcoDiscipline.YEAR_END_DESC_IN,
               'alpha': {'type': 'float', 'range': [0., 1.], 'default': 0.5, 'unit': '-',
                         'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy_study'},
               'primary_energy_percentage': {'type': 'float', 'range': [0., 1.], 'unit': '-', 'default': 0.8,
                                             'visibility': SoSWrapp.SHARED_VISIBILITY,
                                             'namespace': GlossaryEnergy.NS_REFERENCE},
               'normalization_value_demand_constraints': {'type': 'float', 'default': 1000.0, 'unit': 'Twh',
                                                          'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                          'namespace': GlossaryEnergy.NS_REFERENCE},
               GlossaryEnergy.CO2Taxes['var_name']: GlossaryEnergy.CO2Taxes,
               'minimum_energy_production': {'type': 'float', 'default': 1e4,
                                             'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_public',
                                             'unit': 'TWh'},
               'total_prod_minus_min_prod_constraint_ref': {'type': 'float', 'default': 1e4, 'unit': 'Twh',
                                                            'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                            'namespace': GlossaryEnergy.NS_REFERENCE},
               'exp_min': {'type': 'bool', 'default': True, 'user_level': 2},
               'production_threshold': {'type': 'float', 'default': 1e-3, 'unit': 'Twh'},
               'scaling_factor_energy_production': {'type': 'float', 'default': 1e3, 'unit': '-', 'user_level': 2,
                                                    'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                    'namespace': 'ns_public'},
               'scaling_factor_energy_consumption': {'type': 'float', 'default': 1e3, 'unit': '-', 'user_level': 2,
                                                     'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                     'namespace': 'ns_public'},
               'solid_fuel_elec_percentage': {'type': 'float', 'default': 0.75, 'unit': '-', 'user_level': 2,
                                              'visibility': SoSWrapp.SHARED_VISIBILITY,
                                              'namespace': GlossaryEnergy.NS_REFERENCE},
               'solid_fuel_elec_constraint_ref': {'type': 'float', 'default': 10000., 'unit': 'Twh', 'user_level': 2,
                                                  'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                  'namespace': GlossaryEnergy.NS_REFERENCE},
               'liquid_hydrogen_percentage': {'type': 'array', 'user_level': 2, 'unit': '%',
                                              'visibility': SoSWrapp.SHARED_VISIBILITY,
                                              'namespace': GlossaryEnergy.NS_REFERENCE},
               'liquid_hydrogen_constraint_ref': {'type': 'float', 'default': 1000., 'unit': 'Twh', 'user_level': 2,
                                                  'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                  'namespace': GlossaryEnergy.NS_REFERENCE},
               'syngas_prod_ref': {'type': 'float', 'default': 10000., 'unit': 'TWh', 'user_level': 2,
                                   'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': GlossaryEnergy.NS_REFERENCE},
               'syngas_prod_constraint_limit': {'type': 'float', 'default': 10000., 'unit': 'TWh', 'user_level': 2,
                                                'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                'namespace': GlossaryEnergy.NS_REFERENCE},

               'ratio_ref': {'type': 'float', 'default': 500., 'unit': '-', 'user_level': 2,
                             'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': GlossaryEnergy.NS_REFERENCE},
               'heat_losses_percentage': {'type': 'float', 'default': heat_losses_percentage_default, 'unit': '%',
                                          'range': [0., 100.]}, }

    DESC_OUT = {
        GlossaryEnergy.EnergyPricesValue: {'type': 'dataframe', 'unit': '$/MWh'},
        GlossaryEnergy.TargetProductionConstraintValue: GlossaryEnergy.TargetProductionConstraint,
        GlossaryEnergy.EnergyCO2EmissionsValue: {'type': 'dataframe', 'unit': 'kg/kWh'},
        'energy_CO2_emissions_after_use': {'type': 'dataframe', 'unit': 'kg/kWh'},
        'co2_emissions_by_energy': {'type': 'dataframe', 'unit': 'Mt'},
        GlossaryEnergy.EnergyProductionValue: {'type': 'dataframe', 'unit': 'PWh'},
        GlossaryEnergy.EnergyProductionDetailedValue: {'type': 'dataframe', 'unit': 'TWh'},
        'energy_production_brut': {'type': 'dataframe', 'unit': 'TWh'},
        'energy_production_brut_detailed': {'type': 'dataframe', 'unit': 'TWh'},
        'energy_mix': {'type': 'dataframe', 'unit': '%'},
        'energy_prices_after_tax': {'type': 'dataframe', 'unit': '$/MWh'},
        'energy_production_objective': {'type': 'array', 'unit': '-', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                                        'namespace': GlossaryEnergy.NS_FUNCTIONS},
        'primary_energies_production': {'type': 'dataframe', 'unit': 'TWh',
                                        'visibility': SoSWrapp.SHARED_VISIBILITY,
                                        'namespace': GlossaryEnergy.NS_FUNCTIONS},
        'land_demand_df': {'type': 'dataframe', 'unit': 'Gha'},
        GlossaryEnergy.EnergyMeanPriceValue: GlossaryEnergy.EnergyMeanPrice,
        'production_energy_net_positive': {'type': 'dataframe', 'unit': 'TWh'},
        EnergyMix.TOTAL_PROD_MINUS_MIN_PROD_CONSTRAINT_DF: {
            'type': 'dataframe', 'unit': 'TWh',
            'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': GlossaryEnergy.NS_FUNCTIONS},
        EnergyMix.CONSTRAINT_PROD_H2_LIQUID: {
            'type': 'dataframe', 'unit': 'TWh',
            'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': GlossaryEnergy.NS_FUNCTIONS
        },
        EnergyMix.CONSTRAINT_PROD_SOLID_FUEL_ELEC: {
            'type': 'dataframe', 'unit': 'TWh',
            'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': GlossaryEnergy.NS_FUNCTIONS
        },

        EnergyMix.SYNGAS_PROD_OBJECTIVE: {'type': 'array', 'unit': 'TWh',
                                          'visibility': SoSWrapp.SHARED_VISIBILITY,
                                          'namespace': GlossaryEnergy.NS_FUNCTIONS},
        EnergyMix.SYNGAS_PROD_CONSTRAINT: {'type': 'array', 'unit': 'TWh',
                                           'visibility': SoSWrapp.SHARED_VISIBILITY,
                                           'namespace': GlossaryEnergy.NS_FUNCTIONS},
        GlossaryEnergy.AllStreamsDemandRatioValue: {'type': 'dataframe', 'unit': '-',
                                                    'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                    'namespace': 'ns_energy',
                                                    'dataframe_descriptor': {GlossaryEnergy.Years: (
                                                    'int', [1900, GlossaryEnergy.YeartEndDefault], False),
                                                                             GlossaryEnergy.CO2Tax: (
                                                                             'float', None, True)}
                                                    },
        'ratio_objective': {'type': 'array', 'unit': '-', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                            'namespace': GlossaryEnergy.NS_FUNCTIONS},
        'resources_demand': {'type': 'dataframe', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                             'namespace': 'ns_resource', 'unit': 'Mt'},
        'resources_demand_woratio': {'type': 'dataframe', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                                     'namespace': 'ns_resource', 'unit': 'Mt'},
        'co2_emissions_needed_by_energy_mix': {'type': 'dataframe', 'unit': 'Gt',
                                               'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy'},
        'carbon_capture_from_energy_mix': {'type': 'dataframe', 'unit': 'Gt',
                                           'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy'},
        GlossaryEnergy.EnergyCapitalDfValue: GlossaryEnergy.EnergyCapitalDf
    }

    energy_name = EnergyMix.name
    energy_class_dict = EnergyMix.energy_class_dict
    stream_class_dict = EnergyMix.stream_class_dict
    SYNGAS_NAME = Syngas.name
    BIOMASS_DRY_NAME = BiomassDry.name
    LIQUID_FUEL_NAME = LiquidFuel.name
    HYDROGEN_NAME = GaseousHydrogen.name
    LIQUID_HYDROGEN_NAME = LiquidHydrogen.name
    SOLIDFUEL_NAME = SolidFuel.name
    ELECTRICITY_NAME = Electricity.name
    GASEOUS_HYDROGEN_NAME = GaseousHydrogen.name
    LowTemperatureHeat_name = lowtemperatureheat.name
    MediumTemperatureHeat_name = mediumtemperatureheat.name
    HighTemperatureHeat_name = hightemperatureheat.name

    energy_constraint_list = EnergyMix.energy_constraint_list
    movable_fuel_list = EnergyMix.movable_fuel_list

    def __init__(self, sos_name, logger: logging.Logger):
        super().__init__(sos_name, logger)
        self.energy_model = None
        self.grad_energy_mix_vs_prod_dict = None

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.energy_model = EnergyMix(self.energy_name)
        self.energy_model.configure_parameters(inputs_dict)

    def setup_sos_disciplines(self):

        dynamic_inputs = {}
        dynamic_outputs = {}
        inputs_dict = self.get_sosdisc_inputs()
        if GlossaryEnergy.YearStart in self.get_data_in():
            year_start, year_end = self.get_sosdisc_inputs(
                [GlossaryEnergy.YearStart, GlossaryEnergy.YearEnd])
            years = np.arange(year_start, year_end + 1)
            default_target_energy_production = pd.DataFrame({GlossaryEnergy.Years: years,
                                                             GlossaryEnergy.TargetEnergyProductionValue: np.zeros_like(
                                                                 years)})
            self.set_dynamic_default_values(
                {GlossaryEnergy.TargetEnergyProductionValue: default_target_energy_production})
        if GlossaryEnergy.energy_list in self.get_data_in():
            energy_list = inputs_dict[GlossaryEnergy.energy_list]
            self.update_default_energy_list()
            if energy_list is not None:
                for energy in energy_list:
                    # Biomass energy is computed by the agriculture model
                    ns_energy = self.get_ns_energy(energy)

                    dynamic_inputs[f'{ns_energy}.{GlossaryEnergy.EnergyConsumptionValue}'] = {
                        'type': 'dataframe', 'unit': 'PWh',
                        "dynamic_dataframe_columns": True}
                    dynamic_inputs[f'{ns_energy}.{GlossaryEnergy.EnergyConsumptionWithoutRatioValue}'] = {
                        'type': 'dataframe', 'unit': 'PWh', "dynamic_dataframe_columns": True}
                    dynamic_inputs[f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}'] = {
                        'type': 'dataframe', 'unit': 'PWh', "dynamic_dataframe_columns": True}
                    dynamic_inputs[f'{ns_energy}.{GlossaryEnergy.EnergyPricesValue}'] = {
                        'type': 'dataframe', 'unit': '$/MWh', "dynamic_dataframe_columns": True}
                    dynamic_inputs[f'{ns_energy}.{GlossaryEnergy.LandUseRequiredValue}'] = {
                        'type': 'dataframe', 'unit': 'Gha', "dynamic_dataframe_columns": True}

                    dynamic_inputs[f'{ns_energy}.{GlossaryEnergy.EnergyTypeCapitalDfValue}'] = \
                        GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.EnergyTypeCapitalDf)
                    # If the name is different than the energy then the namespace is also different
                    # Valid for biomass which is in agriculture node
                    if ns_energy != energy:
                        for new_var in [f'{ns_energy}.{GlossaryEnergy.EnergyConsumptionValue}',
                                        f'{ns_energy}.{GlossaryEnergy.EnergyConsumptionWithoutRatioValue}',
                                        f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}',
                                        f'{ns_energy}.{GlossaryEnergy.EnergyPricesValue}',
                                        f'{ns_energy}.{GlossaryEnergy.LandUseRequiredValue}']:
                            dynamic_inputs[new_var].update({'namespace': GlossaryEnergy.NS_WITNESS,
                                                            'visibility': SoSWrapp.SHARED_VISIBILITY})

                    if energy in self.energy_class_dict:
                        # Biomass energy is computed by the agriculture model
                        dynamic_inputs[f'{ns_energy}.{GlossaryEnergy.CO2EmissionsValue}'] = {
                            'type': 'dataframe', 'unit': 'kg/kWh', "dynamic_dataframe_columns": True}
                        dynamic_inputs[f'{ns_energy}.CO2_per_use'] = {
                            'type': 'dataframe', 'unit': 'kg/kWh',
                            'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                     GlossaryEnergy.CO2Tax: ('float', None, True),
                                                     'CO2_per_use': ('float', None, True),
                                                     },
                        }
                        dynamic_inputs[f'{ns_energy}.losses_percentage'] = {
                            'type': 'float', 'unit': '%', 'default': self.loss_percentage_default_dict[energy],
                            'range': [0., 100.],
                            'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                     'years7': ('float', None, True), },
                        }
                        # If the name is different than the energy then the namespace is also different
                        # Valid for biomass which is in agriculture node
                        if ns_energy != energy:
                            for new_var in [f'{ns_energy}.{GlossaryEnergy.CO2EmissionsValue}',
                                            f'{ns_energy}.CO2_per_use',
                                            f'{ns_energy}.losses_percentage']:
                                dynamic_inputs[new_var].update({'namespace': GlossaryEnergy.NS_WITNESS,
                                                                'visibility': SoSWrapp.SHARED_VISIBILITY})

                if GlossaryEnergy.syngas in energy_list:
                    dynamic_inputs[f'syngas_ratio'] = {
                        'type': 'array', 'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_syngas',
                        'unit': '%'}

            if GlossaryEnergy.ccs_list in self.get_data_in():
                ccs_list = inputs_dict[GlossaryEnergy.ccs_list]
                if ccs_list is not None:
                    for ccs_name in ccs_list:
                        etcp = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.EnergyTypeCapitalDf)
                        etcp.update({"namespace": "ns_ccs",
                                     "visibility": "Shared"})
                        dynamic_inputs[f'{ccs_name}.{GlossaryEnergy.EnergyTypeCapitalDfValue}'] = etcp

                        dynamic_inputs[f'{ccs_name}.{GlossaryEnergy.EnergyConsumptionValue}'] = {
                            'type': 'dataframe', 'unit': 'PWh', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                            'namespace': GlossaryEnergy.NS_CCS,
                            'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                     f'{GlossaryEnergy.renewable} (TWh)': ('float', None, True),
                                                     f'{GlossaryEnergy.fossil} (TWh)': ('float', None, True),
                                                     f'{GlossaryEnergy.carbon_capture} (Mt)': ('float', None, True), }}
                        dynamic_inputs[f'{ccs_name}.{GlossaryEnergy.EnergyConsumptionWithoutRatioValue}'] = {
                            'type': 'dataframe', 'unit': 'PWh', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                            'namespace': GlossaryEnergy.NS_CCS,
                            'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                     f'{GlossaryEnergy.renewable} (TWh)': ('float', None, True),
                                                     f'{GlossaryEnergy.fossil} (TWh)': ('float', None, True),
                                                     f'{GlossaryEnergy.carbon_capture} (Mt)': ('float', None, True), }}
                        dynamic_inputs[f'{ccs_name}.{GlossaryEnergy.EnergyProductionValue}'] = {
                            'type': 'dataframe', 'unit': 'PWh', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                            'namespace': GlossaryEnergy.NS_CCS,
                            'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                     GlossaryEnergy.carbon_capture: ('float', None, True),
                                                     'CO2 from Flue Gas (Mt)': ('float', None, True),
                                                     GlossaryEnergy.carbon_storage: ('float', None, True), }}
                        dynamic_inputs[f'{ccs_name}.{GlossaryEnergy.EnergyPricesValue}'] = {
                            'type': 'dataframe', 'unit': '$/MWh', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                            'namespace': GlossaryEnergy.NS_CCS,
                            'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                     GlossaryEnergy.carbon_capture: ('float', None, True),
                                                     'carbon_capture_wotaxes': ('float', None, True),
                                                     GlossaryEnergy.carbon_storage: ('float', None, True),
                                                     'carbon_storage_wotaxes': ('float', None, True), }}
                        dynamic_inputs[f'{ccs_name}.{GlossaryEnergy.LandUseRequiredValue}'] = {
                            'type': 'dataframe', 'unit': 'Gha', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                            'namespace': GlossaryEnergy.NS_CCS,
                            'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                     'direct_air_capture': ('float', None, True),
                                                     f'{GlossaryEnergy.flue_gas_capture}.FlueGasTechno (Gha)': ('float', None, True),
                                                     'CarbonStorageTechno (Gha)': ('float', None, True),
                                                     f'{GlossaryEnergy.direct_air_capture}.DirectAirCaptureTechno (Gha)': (
                                                         'float', None, True), }}

        self.update_default_with_years(inputs_dict)

        self.add_inputs(dynamic_inputs)
        self.add_outputs(dynamic_outputs)

    def update_default_with_years(self, inputs_dict):
        '''
        Update default variables knowing the year start and the year end 
        '''
        if GlossaryEnergy.YearStart in inputs_dict:
            years = np.arange(inputs_dict[GlossaryEnergy.YearStart], inputs_dict[GlossaryEnergy.YearEnd] + 1)
            lh_perc_default = np.concatenate(
                (np.ones(5) * 1e-4, np.ones(len(years) - 5) / 4), axis=None)
            self.set_dynamic_default_values(
                {'liquid_hydrogen_percentage': lh_perc_default})

    def update_default_energy_list(self):
        '''
        Update the default value of technologies list with techno discipline below the energy node and in possible values
        '''

        found_energies = self.found_energy_under_energymix()
        self.set_dynamic_default_values({GlossaryEnergy.energy_list: found_energies})

    def found_energy_under_energymix(self):
        '''
        Set the default value of the energy list and the ccs_list with discipline under the energy_mix which are in possible values
        '''
        my_name = self.get_disc_full_name()
        possible_energy = EnergyMix.energy_list
        found_energy_list = self.dm.get_discipline_names_with_starting_name(
            my_name)
        short_energy_list = [name.split(
            f'{my_name}.')[-1] for name in found_energy_list if f'{my_name}.' in name]

        possible_short_energy_list = [
            techno for techno in short_energy_list if techno in possible_energy]

        return possible_short_energy_list

    def run(self):
        # -- get inputs
        inputs_dict_orig = self.get_sosdisc_inputs()
        # -- configure class with inputs
        # -- biomass dry values are coming from agriculture mix discipline, but needs to be used in model with biomass dry name
        inputs_dict = {}
        inputs_dict.update(inputs_dict_orig)
        self.update_biomass_dry_name(inputs_dict_orig, inputs_dict)

        self.energy_model.compute(inputs_dict)

        # -- Compute objectives with alpha trades
        alpha = inputs_dict['alpha']
        delta_years = inputs_dict[GlossaryEnergy.YearEnd] - inputs_dict[GlossaryEnergy.YearStart] + 1

        energy_production_objective = np.asarray(
            [(1. - alpha) * self.energy_model.production[GlossaryEnergy.TotalProductionValue][0] * delta_years
             / self.energy_model.production[GlossaryEnergy.TotalProductionValue].sum(), ])

        
        if EnergyMix.PRODUCTION in self.energy_model.energy_prices:
            self.energy_model.energy_prices.drop(
                columns=[EnergyMix.PRODUCTION], inplace=True)
        # energy_production stored in PetaWh for coupling variables scaling
        scaled_energy_production = pd.DataFrame(
            {GlossaryEnergy.Years: self.energy_model.production[GlossaryEnergy.Years].values,
             GlossaryEnergy.TotalProductionValue: self.energy_model.production[
                                                      GlossaryEnergy.TotalProductionValue].values /
                                                  inputs_dict[
                                                      'scaling_factor_energy_production']})

        outputs_dict = {GlossaryEnergy.EnergyPricesValue: self.energy_model.energy_prices,
                        'co2_emissions_by_energy': self.energy_model.emissions_by_energy,
                        GlossaryEnergy.EnergyCO2EmissionsValue: self.energy_model.total_carbon_emissions,
                        'energy_CO2_emissions_after_use': self.energy_model.carbon_emissions_after_use,
                        GlossaryEnergy.EnergyProductionValue: scaled_energy_production,
                        GlossaryEnergy.EnergyProductionDetailedValue: self.energy_model.production,
                        'energy_production_brut': self.energy_model.production_raw[
                            [GlossaryEnergy.Years, GlossaryEnergy.TotalProductionValue]],
                        'energy_production_brut_detailed': self.energy_model.production_raw,
                        'energy_mix': self.energy_model.mix_weights,
                        'energy_prices_after_tax': self.energy_model.price_by_energy,
                        'energy_production_objective': energy_production_objective,
                        'land_demand_df': self.energy_model.land_use_required,
                        GlossaryEnergy.EnergyMeanPriceValue: self.energy_model.energy_mean_price,
                        'production_energy_net_positive': self.energy_model.net_positive_consumable_energy_production,
                        self.energy_model.TOTAL_PROD_MINUS_MIN_PROD_CONSTRAINT_DF: self.energy_model.total_prod_minus_min_prod_constraint_df,
                        EnergyMix.CONSTRAINT_PROD_H2_LIQUID: self.energy_model.constraint_liquid_hydrogen,
                        EnergyMix.CONSTRAINT_PROD_SOLID_FUEL_ELEC: self.energy_model.constraint_solid_fuel_elec,
                        EnergyMix.SYNGAS_PROD_OBJECTIVE: self.energy_model.syngas_prod_objective,
                        EnergyMix.SYNGAS_PROD_CONSTRAINT: self.energy_model.syngas_prod_constraint,
                        GlossaryEnergy.AllStreamsDemandRatioValue: self.energy_model.all_streams_demand_ratio,
                        'ratio_objective': self.energy_model.ratio_objective,
                        'resources_demand': self.energy_model.resources_demand,
                        'resources_demand_woratio': self.energy_model.resources_demand_woratio,
                        'co2_emissions_needed_by_energy_mix': self.energy_model.co2_emissions_needed_by_energy_mix,
                        'carbon_capture_from_energy_mix': self.energy_model.carbon_capture_from_energy_mix,
                        GlossaryEnergy.EnergyCapitalDfValue: self.energy_model.energy_capital,
                        GlossaryEnergy.TargetProductionConstraintValue: self.energy_model.target_production_constraint,
                        }

        primary_energy_percentage = inputs_dict['primary_energy_percentage']

        if f'production {self.LIQUID_FUEL_NAME} (TWh)' in self.energy_model.production and \
                f'production {self.HYDROGEN_NAME} (TWh)' in self.energy_model.production and\
                f'production {GlossaryEnergy.hydrogen}.{GlossaryEnergy.liquid_hydrogen} (TWh)' in self.energy_model.production:
            production_liquid_fuel = self.energy_model.production[f'production {self.LIQUID_FUEL_NAME} (TWh)']
            production_hydrogen = self.energy_model.production[f'production {self.HYDROGEN_NAME} (TWh)']
            production_liquid_hydrogen = self.energy_model.production[f'production {GlossaryEnergy.hydrogen}.{GlossaryEnergy.liquid_hydrogen} (TWh)']
            sum_energies_production = production_liquid_fuel + production_hydrogen + production_liquid_hydrogen

            energies_production_constraint = sum_energies_production - \
                                             primary_energy_percentage * \
                                             self.energy_model.production[GlossaryEnergy.TotalProductionValue]

            outputs_dict['primary_energies_production'] = energies_production_constraint.to_frame('primary_energies')
        else:
            outputs_dict['primary_energies_production'] = pd.DataFrame()

        

        self.store_sos_outputs_values(outputs_dict)

    def update_biomass_dry_name(self, inputs_dict_orig, inputs_dict):
        '''
        Update the agriculture name in the inputs dict with the correct energy name

        '''
        energy_list = inputs_dict_orig[GlossaryEnergy.energy_list]
        agri_name = AgricultureMixDiscipline.name
        if GlossaryEnergy.biomass_dry in energy_list:
            inputs_dict[f'{BiomassDry.name}.{GlossaryEnergy.EnergyConsumptionValue}'] = inputs_dict_orig.pop(
                f'{agri_name}.{GlossaryEnergy.EnergyConsumptionValue}')
            inputs_dict[
                f'{BiomassDry.name}.{GlossaryEnergy.EnergyConsumptionWithoutRatioValue}'] = inputs_dict_orig.pop(
                f'{agri_name}.{GlossaryEnergy.EnergyConsumptionWithoutRatioValue}')
            inputs_dict[f'{BiomassDry.name}.{GlossaryEnergy.EnergyProductionValue}'] = inputs_dict_orig.pop(
                f'{agri_name}.{GlossaryEnergy.EnergyProductionValue}')
            inputs_dict[f'{BiomassDry.name}.{GlossaryEnergy.EnergyPricesValue}'] = inputs_dict_orig.pop(
                f'{agri_name}.{GlossaryEnergy.EnergyPricesValue}')
            inputs_dict[f'{BiomassDry.name}.{GlossaryEnergy.LandUseRequiredValue}'] = inputs_dict_orig.pop(
                f'{agri_name}.{GlossaryEnergy.LandUseRequiredValue}')
            inputs_dict[f'{BiomassDry.name}.{GlossaryEnergy.CO2EmissionsValue}'] = inputs_dict_orig.pop(
                f'{agri_name}.{GlossaryEnergy.CO2EmissionsValue}')
            inputs_dict[f'{BiomassDry.name}.CO2_per_use'] = inputs_dict_orig.pop(
                f'{agri_name}.CO2_per_use')
            inputs_dict[f'{BiomassDry.name}.losses_percentage'] = inputs_dict_orig.pop(
                f'{agri_name}.losses_percentage')

    def compute_sos_jacobian(self):

        inputs_dict_orig = self.get_sosdisc_inputs()
        # -- biomass dry values are coming from agriculture mix discipline, but needs to be used in model with biomass dry name
        inputs_dict = {}
        inputs_dict.update(inputs_dict_orig)
        energy_list = inputs_dict[GlossaryEnergy.energy_list] + inputs_dict[GlossaryEnergy.ccs_list]
        self.update_biomass_dry_name(inputs_dict_orig, inputs_dict)
        outputs_dict = self.get_sosdisc_outputs()
        stream_class_dict = EnergyMix.stream_class_dict
        years = np.arange(inputs_dict[GlossaryEnergy.YearStart],
                          inputs_dict[GlossaryEnergy.YearEnd] + 1)
        identity = np.eye(len(years))

        heat_losses_percentage = inputs_dict['heat_losses_percentage'] / 100.0
        primary_energy_percentage = inputs_dict['primary_energy_percentage']
        production_detailed_df = outputs_dict[GlossaryEnergy.EnergyProductionDetailedValue]
        minimum_energy_production = inputs_dict['minimum_energy_production']
        production_threshold = inputs_dict['production_threshold']
        total_prod_minus_min_prod_constraint_ref = inputs_dict[
            'total_prod_minus_min_prod_constraint_ref']
        production_energy_net_pos = outputs_dict['production_energy_net_positive']
        energies = [j for j in energy_list if j not in [
            GlossaryEnergy.carbon_storage, GlossaryEnergy.carbon_capture]]
        mix_weight = outputs_dict['energy_mix']
        scaling_factor_energy_production = inputs_dict['scaling_factor_energy_production']
        scaling_factor_energy_consumption = inputs_dict['scaling_factor_energy_consumption']
        energy_price_after_tax = outputs_dict['energy_prices_after_tax']
        solid_fuel_elec_percentage = inputs_dict['solid_fuel_elec_percentage']
        solid_fuel_elec_constraint_ref = inputs_dict['solid_fuel_elec_constraint_ref']
        liquid_hydrogen_percentage = inputs_dict['liquid_hydrogen_percentage']
        liquid_hydrogen_constraint_ref = inputs_dict['liquid_hydrogen_constraint_ref']
        syngas_prod_ref = inputs_dict['syngas_prod_ref']
        sub_production_dict, sub_consumption_dict = {}, {}
        sub_consumption_woratio_dict = self.energy_model.sub_consumption_woratio_dict
        for energy in energy_list:
            sub_production_dict[energy] = inputs_dict[f'{energy}.{GlossaryEnergy.EnergyProductionValue}'] * \
                                          scaling_factor_energy_production
            sub_consumption_dict[energy] = inputs_dict[f'{energy}.{GlossaryEnergy.EnergyConsumptionValue}'] * \
                                           scaling_factor_energy_consumption

        # -------------------------------------------#
        # ---- Production / Consumption gradients----#
        # -------------------------------------------#
        for energy in inputs_dict[GlossaryEnergy.energy_list] + inputs_dict[GlossaryEnergy.ccs_list]:
            ns_energy = self.get_ns_energy(energy)
            self.set_partial_derivative_for_other_types(
                (GlossaryEnergy.EnergyCapitalDfValue, GlossaryEnergy.Capital),
                (f'{ns_energy}.{GlossaryEnergy.EnergyTypeCapitalDfValue}', GlossaryEnergy.Capital),
                identity / 1e3
            )

        for energy in energy_list:
            ns_energy = self.get_ns_energy(energy)

            if energy in energies:
                loss_percentage = inputs_dict[f'{ns_energy}.losses_percentage'] / 100.0
                # To model raw to net percentage for witness coarse energies
                if energy in self.energy_model.raw_tonet_dict:
                    loss_percentage += (1.0 -
                                        self.energy_model.raw_tonet_dict[energy])
                loss_percent = heat_losses_percentage + loss_percentage

                # ---- Production gradients----#
                dtotal_prod_denergy_prod = self.compute_dtotal_production_denergy_production(
                    production_detailed_df, minimum_energy_production, loss_percent)
                dprod_objective_dprod = self.compute_denergy_production_objective_dprod(
                    dtotal_prod_denergy_prod, inputs_dict['alpha'], outputs_dict[GlossaryEnergy.EnergyProductionValue],
                    years)
                self.set_partial_derivative_for_other_types(
                    (GlossaryEnergy.EnergyProductionValue,
                     GlossaryEnergy.TotalProductionValue),
                    (f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', energy),
                    dtotal_prod_denergy_prod)
                self.set_partial_derivative_for_other_types(
                    (GlossaryEnergy.EnergyProductionDetailedValue,
                     GlossaryEnergy.TotalProductionValue),
                    (f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', energy),
                    dtotal_prod_denergy_prod * scaling_factor_energy_production)
                self.set_partial_derivative_for_other_types(
                    (GlossaryEnergy.EnergyProductionDetailedValue, 'Total production (uncut)'),
                    (f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', energy),
                    np.identity(len(years)) * scaling_factor_energy_production * (1.0 - loss_percent))
                self.set_partial_derivative_for_other_types(
                    (GlossaryEnergy.EnergyProductionDetailedValue,
                     f'production {energy} ({stream_class_dict[energy].unit})'),
                    (f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', energy),
                    np.identity(len(years)) * scaling_factor_energy_production * (1.0 - loss_percentage))
                self.set_partial_derivative_for_other_types(
                    ('energy_production_brut',
                     GlossaryEnergy.TotalProductionValue),
                    (f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', energy),
                    scaling_factor_energy_production * np.identity(len(years)))
                self.set_partial_derivative_for_other_types(
                    ('energy_production_objective',), (f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', energy),
                    dprod_objective_dprod)
                if f'production {self.LIQUID_FUEL_NAME} (TWh)' in production_detailed_df.columns and\
                        f'production {self.HYDROGEN_NAME} (TWh)' in production_detailed_df.columns and\
                        f'production {GlossaryEnergy.hydrogen}.{GlossaryEnergy.liquid_hydrogen} (TWh)' in production_detailed_df.columns:
                    if energy in [self.HYDROGEN_NAME, f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.liquid_hydrogen}', self.LIQUID_FUEL_NAME]:
                        self.set_partial_derivative_for_other_types(
                            ('primary_energies_production', 'primary_energies'),
                            (f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', energy),
                            (np.identity(len(years)) * (1 - loss_percentage) - primary_energy_percentage * dtotal_prod_denergy_prod) * scaling_factor_energy_production)
                    else:
                        self.set_partial_derivative_for_other_types(('primary_energies_production', 'primary_energies'),
                                                                    (
                                                                        f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}',
                                                                        energy),
                                                                    -scaling_factor_energy_production * primary_energy_percentage * dtotal_prod_denergy_prod)

                # constraint solid_fuel + elec gradient
                if energy in self.energy_model.energy_constraint_list:
                    self.set_partial_derivative_for_other_types(
                        (f'{EnergyMix.CONSTRAINT_PROD_SOLID_FUEL_ELEC}', 'constraint_solid_fuel_elec'), (
                            f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', energy),
                        (- scaling_factor_energy_production * ((
                                                                       1 - loss_percentage) - solid_fuel_elec_percentage * dtotal_prod_denergy_prod) / solid_fuel_elec_constraint_ref) * np.identity(
                            len(years)))
                else:
                    self.set_partial_derivative_for_other_types(
                        (f'{EnergyMix.CONSTRAINT_PROD_SOLID_FUEL_ELEC}', 'constraint_solid_fuel_elec'), (
                            f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', energy),
                        scaling_factor_energy_production * solid_fuel_elec_percentage * dtotal_prod_denergy_prod / solid_fuel_elec_constraint_ref * np.identity(
                            len(years)))

                if energy == self.SYNGAS_NAME:
                    self.set_partial_derivative_for_other_types(
                        (EnergyMix.SYNGAS_PROD_OBJECTIVE,
                         ), (f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', energy),
                        scaling_factor_energy_production * np.sign(
                            production_detailed_df[f'production {GlossaryEnergy.syngas} (TWh)'].values) * np.identity(
                            len(years)) / syngas_prod_ref)

                    self.set_partial_derivative_for_other_types(
                        (EnergyMix.SYNGAS_PROD_CONSTRAINT,
                         ), (f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', energy),
                        - scaling_factor_energy_production * np.identity(len(years)) / syngas_prod_ref)

                # constraint liquid hydrogen

                if energy == f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.liquid_hydrogen}':
                    self.set_partial_derivative_for_other_types(
                        (f'{EnergyMix.CONSTRAINT_PROD_H2_LIQUID}', 'constraint_liquid_hydrogen'), (
                            f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', energy),
                        (- scaling_factor_energy_production * (
                                liquid_hydrogen_percentage - 1) / liquid_hydrogen_constraint_ref) * np.identity(
                            len(years)))
                elif energy == self.GASEOUS_HYDROGEN_NAME:
                    self.set_partial_derivative_for_other_types(
                        (f'{EnergyMix.CONSTRAINT_PROD_H2_LIQUID}', 'constraint_liquid_hydrogen'), (
                            f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', energy), (
                                                                                                    - scaling_factor_energy_production * liquid_hydrogen_percentage / liquid_hydrogen_constraint_ref) * np.identity(
                            len(years)))
                # ---- Loop on energy again to differentiate production and consumption ----#
                for energy_input in energy_list:
                    ns_energy_input = self.get_ns_energy(energy_input)
                    list_columns_energy_consumption = list(
                        inputs_dict[f'{energy_input}.{GlossaryEnergy.EnergyConsumptionValue}'].columns)
                    if f'{energy} ({stream_class_dict[energy].unit})' in list_columns_energy_consumption:
                        # ---- Consumption gradients----#
                        dtotal_prod_denergy_cons = - \
                            self.compute_dtotal_production_denergy_production(
                                production_detailed_df, minimum_energy_production, 0.0)
                        dprod_objective_dcons = self.compute_denergy_production_objective_dprod(
                            dtotal_prod_denergy_cons, inputs_dict['alpha'],
                            outputs_dict[GlossaryEnergy.EnergyProductionValue], years)
                        self.set_partial_derivative_for_other_types(
                            (GlossaryEnergy.EnergyProductionValue, GlossaryEnergy.TotalProductionValue), (
                                f'{ns_energy_input}.{GlossaryEnergy.EnergyConsumptionValue}',
                                f'{energy} ({stream_class_dict[energy].unit})'),
                            scaling_factor_energy_consumption * dtotal_prod_denergy_cons / scaling_factor_energy_production)
                        self.set_partial_derivative_for_other_types(
                            (GlossaryEnergy.EnergyProductionDetailedValue, GlossaryEnergy.TotalProductionValue),
                            (f'{ns_energy_input}.{GlossaryEnergy.EnergyConsumptionValue}',
                             f'{energy} ({stream_class_dict[energy].unit})'),
                            scaling_factor_energy_consumption * dtotal_prod_denergy_cons / scaling_factor_energy_production * scaling_factor_energy_production)
                        self.set_partial_derivative_for_other_types(
                            (GlossaryEnergy.EnergyProductionDetailedValue,
                             'Total production (uncut)'),
                            (f'{ns_energy_input}.{GlossaryEnergy.EnergyConsumptionValue}',
                             f'{energy} ({stream_class_dict[energy].unit})'),
                            -scaling_factor_energy_consumption * np.identity(
                                len(years)) / scaling_factor_energy_production * scaling_factor_energy_production)
                        self.set_partial_derivative_for_other_types(
                            (GlossaryEnergy.EnergyProductionDetailedValue,
                             f'production {energy} ({stream_class_dict[energy].unit})'),
                            (f'{ns_energy_input}.{GlossaryEnergy.EnergyConsumptionValue}',
                             f'{energy} ({stream_class_dict[energy].unit})'),
                            -scaling_factor_energy_consumption * np.identity(
                                len(years)) / scaling_factor_energy_production * scaling_factor_energy_production)

                        self.set_partial_derivative_for_other_types(
                            ('energy_production_objective',),
                            (f'{ns_energy_input}.{GlossaryEnergy.EnergyConsumptionValue}',
                             f'{energy} ({stream_class_dict[energy].unit})'),
                            scaling_factor_energy_consumption * dprod_objective_dcons / scaling_factor_energy_production)
                        if f'production {self.LIQUID_FUEL_NAME} (TWh)' in production_detailed_df.columns and\
                                f'production {self.HYDROGEN_NAME} (TWh)' in production_detailed_df.columns and\
                                f'production {GlossaryEnergy.hydrogen}.{GlossaryEnergy.liquid_hydrogen} (TWh)' in production_detailed_df.columns:
                            if energy in [self.HYDROGEN_NAME, f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.liquid_hydrogen}', self.LIQUID_FUEL_NAME]:
                                self.set_partial_derivative_for_other_types(
                                    ('primary_energies_production', 'primary_energies'),
                                    (f'{ns_energy_input}.{GlossaryEnergy.EnergyConsumptionValue}', f'{energy} ({stream_class_dict[energy].unit})'),
                                    -scaling_factor_energy_consumption * (
                                            primary_energy_percentage * dtotal_prod_denergy_cons + np.identity(
                                        len(years))))
                            else:
                                self.set_partial_derivative_for_other_types(
                                    ('primary_energies_production', 'primary_energies'), (
                                        f'{ns_energy_input}.{GlossaryEnergy.EnergyConsumptionValue}',
                                        f'{energy} ({stream_class_dict[energy].unit})'),
                                    -scaling_factor_energy_consumption * primary_energy_percentage * dtotal_prod_denergy_cons)
                        # constraint solid_fuel + elec gradient

                        if energy in self.energy_model.energy_constraint_list:
                            self.set_partial_derivative_for_other_types(
                                (f'{EnergyMix.CONSTRAINT_PROD_SOLID_FUEL_ELEC}', 'constraint_solid_fuel_elec'), (
                                    f'{ns_energy_input}.{GlossaryEnergy.EnergyConsumptionValue}',
                                    f'{energy} ({stream_class_dict[energy].unit})'), (
                                                                                             scaling_factor_energy_consumption * (
                                                                                             1 + solid_fuel_elec_percentage * dtotal_prod_denergy_cons) / solid_fuel_elec_constraint_ref) * np.identity(
                                    len(years)))
                        else:
                            self.set_partial_derivative_for_other_types(
                                (f'{EnergyMix.CONSTRAINT_PROD_SOLID_FUEL_ELEC}', 'constraint_solid_fuel_elec'), (
                                    f'{ns_energy_input}.{GlossaryEnergy.EnergyConsumptionValue}',
                                    f'{energy} ({stream_class_dict[energy].unit})'),
                                scaling_factor_energy_consumption * solid_fuel_elec_percentage * dtotal_prod_denergy_cons / solid_fuel_elec_constraint_ref * np.identity(
                                    len(years)))

                        if energy == f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.liquid_hydrogen}':
                            self.set_partial_derivative_for_other_types(
                                (f'{EnergyMix.CONSTRAINT_PROD_H2_LIQUID}', 'constraint_liquid_hydrogen'), (
                                    f'{ns_energy_input}.{GlossaryEnergy.EnergyConsumptionValue}',
                                    f'{energy} ({stream_class_dict[energy].unit})'), (
                                                                                             scaling_factor_energy_production * (
                                                                                             liquid_hydrogen_percentage - 1) / liquid_hydrogen_constraint_ref) * np.identity(
                                    len(years)))
                        elif energy == self.GASEOUS_HYDROGEN_NAME:
                            self.set_partial_derivative_for_other_types(
                                (f'{EnergyMix.CONSTRAINT_PROD_H2_LIQUID}', 'constraint_liquid_hydrogen'), (
                                    f'{ns_energy_input}.{GlossaryEnergy.EnergyConsumptionValue}',
                                    f'{energy} ({stream_class_dict[energy].unit})'), (
                                                                                             scaling_factor_energy_production * liquid_hydrogen_percentage / liquid_hydrogen_constraint_ref) * np.identity(
                                    len(years)))

                        if energy == self.SYNGAS_NAME:
                            self.set_partial_derivative_for_other_types(
                                (EnergyMix.SYNGAS_PROD_OBJECTIVE,), (
                                    f'{ns_energy_input}.{GlossaryEnergy.EnergyConsumptionValue}',
                                    f'{energy} ({stream_class_dict[energy].unit})'),
                                - scaling_factor_energy_production * np.sign(
                                    production_detailed_df[f'production {GlossaryEnergy.syngas} (TWh)'].values) * np.identity(
                                    len(years)) / syngas_prod_ref)

                            self.set_partial_derivative_for_other_types(
                                (EnergyMix.SYNGAS_PROD_CONSTRAINT,), (
                                    f'{ns_energy_input}.{GlossaryEnergy.EnergyConsumptionValue}',
                                    f'{energy} ({stream_class_dict[energy].unit})'),
                                scaling_factor_energy_production * np.identity(len(years)) / syngas_prod_ref)

            else:
                # CCUS
                self.set_partial_derivative_for_other_types(
                    (GlossaryEnergy.EnergyProductionDetailedValue,
                     f'production {energy} ({stream_class_dict[energy].unit})'),
                    (f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', energy),
                    np.identity(len(years)) * scaling_factor_energy_production)
                # ---- Loop on energy again to differentiate production and consumption ----#
                for energy_input in energy_list:
                    ns_energy_input = self.get_ns_energy(energy_input)
                    list_columns_energy_consumption = list(
                        inputs_dict[f'{energy_input}.{GlossaryEnergy.EnergyConsumptionValue}'].columns)
                    if f'{energy} ({stream_class_dict[energy].unit})' in list_columns_energy_consumption:
                        self.set_partial_derivative_for_other_types(
                            (GlossaryEnergy.EnergyProductionDetailedValue,
                             f'production {energy} ({stream_class_dict[energy].unit})'),
                            (f'{ns_energy_input}.{GlossaryEnergy.EnergyConsumptionValue}',
                             f'{energy} ({stream_class_dict[energy].unit})'),
                            -scaling_factor_energy_consumption * np.identity(
                                len(years)) / scaling_factor_energy_production * scaling_factor_energy_production)
        # -------------------------#
        # ---- Prices gradients----#
        # -------------------------#
        for energy in energy_list:
            ns_energy = self.get_ns_energy(energy)
            if energy in energies:
                self.set_partial_derivative_for_other_types(
                    ('energy_prices_after_tax',
                     energy), (f'{ns_energy}.{GlossaryEnergy.EnergyPricesValue}', energy),
                    np.identity(len(years)))
                self.set_partial_derivative_for_other_types(
                    ('energy_prices_after_tax', energy), (GlossaryEnergy.CO2TaxesValue, GlossaryEnergy.CO2Tax),
                    inputs_dict[f'{energy}.CO2_per_use']['CO2_per_use'].values *
                    np.identity(len(years)))
                self.set_partial_derivative_for_other_types(
                    ('energy_prices_after_tax',
                     energy), (f'{ns_energy}.CO2_per_use', 'CO2_per_use'),
                    inputs_dict[GlossaryEnergy.CO2TaxesValue][GlossaryEnergy.CO2Tax].values *
                    np.identity(len(years)))
            self.set_partial_derivative_for_other_types(
                (GlossaryEnergy.EnergyPricesValue, energy), (f'{ns_energy}.{GlossaryEnergy.EnergyPricesValue}', energy),
                np.identity(len(years)))

        # -------------------------------#
        # ---Resource Demand gradients---#
        # -------------------------------#

        resource_list = EnergyMix.RESOURCE_LIST
        for energy in energy_list:
            ns_energy = self.get_ns_energy(energy)
            for resource in inputs_dict[f'{energy}.{GlossaryEnergy.EnergyConsumptionValue}']:
                resource_wo_unit = resource.replace(
                    f" ({ResourceGlossary.UNITS['consumption']})", '')
                if resource_wo_unit in resource_list:
                    self.set_partial_derivative_for_other_types(('resources_demand', resource_wo_unit), (
                        f'{ns_energy}.{GlossaryEnergy.EnergyConsumptionValue}', resource),
                                                                scaling_factor_energy_consumption * np.identity(
                                                                    len(years)))
                    self.set_partial_derivative_for_other_types(('resources_demand_woratio', resource_wo_unit), (
                        f'{ns_energy}.{GlossaryEnergy.EnergyConsumptionWithoutRatioValue}', resource),
                                                                scaling_factor_energy_consumption * np.identity(
                                                                    len(years)))
        # -----------------------------#
        # ---- Mean Price gradients----#
        # -----------------------------#
        element_dict = dict(zip(energies, energies))
        self.grad_energy_mix_vs_prod_dict = self.energy_model.compute_grad_element_mix_vs_prod(
            deepcopy(production_energy_net_pos), element_dict, exp_min=inputs_dict['exp_min'],
            min_prod=production_threshold)
        dmean_price_dco2_tax = np.zeros((len(years), len(years)))
        for energy in energy_list:
            ns_energy = self.get_ns_energy(energy)
            if energy in energies:
                mix_weight_energy = mix_weight[energy].values
                dmean_price_dco2_tax += inputs_dict[f'{energy}.CO2_per_use']['CO2_per_use'].values * \
                                        mix_weight_energy
                self.set_partial_derivative_for_other_types(
                    (GlossaryEnergy.EnergyMeanPriceValue,
                     GlossaryEnergy.EnergyPriceValue), (f'{ns_energy}.{GlossaryEnergy.EnergyPricesValue}', energy),
                    mix_weight_energy * np.identity(len(years)))
                self.set_partial_derivative_for_other_types(
                    (GlossaryEnergy.EnergyMeanPriceValue,
                     GlossaryEnergy.EnergyPriceValue), (f'{ns_energy}.CO2_per_use', 'CO2_per_use'),
                    inputs_dict[GlossaryEnergy.CO2TaxesValue][GlossaryEnergy.CO2Tax].values *
                    mix_weight_energy * np.identity(len(years)))
                dmean_price_dprod = self.compute_dmean_price_dprod(
                    energy, energies,
                    mix_weight, energy_price_after_tax,
                    production_energy_net_pos, production_detailed_df)

                loss_percentage = inputs_dict[f'{ns_energy}.losses_percentage'] / 100.0
                # To model raw to net percentage for witness coarse energies
                if energy in self.energy_model.raw_tonet_dict:
                    loss_percentage += (1.0 -
                                        self.energy_model.raw_tonet_dict[energy])
                self.set_partial_derivative_for_other_types(
                    (GlossaryEnergy.EnergyMeanPriceValue, GlossaryEnergy.EnergyPriceValue),
                    (f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', energy),
                    scaling_factor_energy_production * dmean_price_dprod * (1.0 - loss_percentage))

            for energy_input in energy_list:
                if energy_input in energies:
                    ns_energy_input = self.get_ns_energy(energy_input)
                    list_columns_energy_consumption = list(
                        inputs_dict[f'{energy_input}.{GlossaryEnergy.EnergyConsumptionValue}'].columns)
                    if f'{energy} ({stream_class_dict[energy].unit})' in list_columns_energy_consumption:
                        if energy in energies:
                            dmean_price_dcons = self.compute_dmean_price_dprod(energy, energies, mix_weight,
                                                                               energy_price_after_tax,
                                                                               production_energy_net_pos,
                                                                               production_detailed_df, cons=True)
                            self.set_partial_derivative_for_other_types(
                                (GlossaryEnergy.EnergyMeanPriceValue, GlossaryEnergy.EnergyPriceValue),
                                (f'{ns_energy_input}.{GlossaryEnergy.EnergyConsumptionValue}',
                                 f'{energy} ({stream_class_dict[energy].unit})'),
                                scaling_factor_energy_consumption * dmean_price_dcons)
        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.EnergyMeanPriceValue, GlossaryEnergy.EnergyPriceValue),
            (GlossaryEnergy.CO2TaxesValue, GlossaryEnergy.CO2Tax),
            dmean_price_dco2_tax * np.identity(len(years)))

        # --------------------------------#
        # -- New CO2 emissions gradients--#
        # --------------------------------#

        co2_emissions_needed_by_energy_mix = outputs_dict['co2_emissions_needed_by_energy_mix']
        carbon_capture_from_energy_mix = outputs_dict['carbon_capture_from_energy_mix']
        self.energy_model.configure_parameters_update(inputs_dict)
        dtot_co2_emissions = self.energy_model.compute_grad_CO2_emissions()

        for key, value in dtot_co2_emissions.items():
            co2_emission_column = key.split(' vs ')[0]
            energy_prod_info = key.split(' vs ')[1]
            energy = energy_prod_info.split('#')[0]
            last_part_key = energy_prod_info.split('#')[1]
            if energy in energy_list:
                self.set_gradient_for_co2_emissions('co2_emissions_needed_by_energy_mix',
                                                    co2_emissions_needed_by_energy_mix, co2_emission_column, energy,
                                                    energy_prod_info, last_part_key, value, inputs_dict, years)
                self.set_gradient_for_co2_emissions('carbon_capture_from_energy_mix',
                                                    carbon_capture_from_energy_mix, co2_emission_column, energy,
                                                    energy_prod_info, last_part_key, value, inputs_dict, years)
        # -----------------------------------#
        # ---- Demand Violation gradients----#
        # -----------------------------------#
        for energy in energies:
            ns_energy = self.get_ns_energy(energy)
            if energy in outputs_dict[GlossaryEnergy.EnergyCO2EmissionsValue].keys():
                self.set_partial_derivative_for_other_types(
                    (GlossaryEnergy.EnergyCO2EmissionsValue, energy),
                    (f'{ns_energy}.{GlossaryEnergy.CO2EmissionsValue}', energy), np.identity(len(years)))
            for energy_input in energy_list:
                ns_energy_input = self.get_ns_energy(energy_input)
                list_columnsenergyprod = list(
                    inputs_dict[f'{energy_input}.{GlossaryEnergy.EnergyProductionValue}'].columns)
                list_columns_energy_consumption = list(
                    inputs_dict[f'{energy_input}.{GlossaryEnergy.EnergyConsumptionValue}'].columns)
                list_index_prod = [j == energy for j in list_columnsenergyprod]
                list_index_conso = [
                    j == f'{energy} ({self.stream_class_dict[energy].unit})' for j in list_columns_energy_consumption]

                if True in list_index_prod:
                    loss_percentage = inputs_dict[f'{ns_energy}.losses_percentage'] / 100.0
                    # To model raw to net percentage for witness coarse
                    # energies
                    if energy in self.energy_model.raw_tonet_dict:
                        loss_percentage += (1.0 -
                                            self.energy_model.raw_tonet_dict[energy])
                    loss_percent = heat_losses_percentage + loss_percentage

                    self.set_partial_derivative_for_other_types((EnergyMix.TOTAL_PROD_MINUS_MIN_PROD_CONSTRAINT_DF,
                                                                 EnergyMix.TOTAL_PROD_MINUS_MIN_PROD_CONSTRAINT),
                                                                (
                                                                f'{ns_energy_input}.{GlossaryEnergy.EnergyProductionValue}',
                                                                energy),
                                                                scaling_factor_energy_production * np.identity(
                                                                    len(years)) / total_prod_minus_min_prod_constraint_ref * (
                                                                        1.0 - loss_percent))

                if True in list_index_conso:
                    self.set_partial_derivative_for_other_types((EnergyMix.TOTAL_PROD_MINUS_MIN_PROD_CONSTRAINT_DF,
                                                                 EnergyMix.TOTAL_PROD_MINUS_MIN_PROD_CONSTRAINT),
                                                                (
                                                                f'{ns_energy_input}.{GlossaryEnergy.EnergyConsumptionValue}',
                                                                list_columns_energy_consumption[
                                                                    list_index_conso.index(True)]),
                                                                -scaling_factor_energy_consumption * np.identity(
                                                                    len(years)) / total_prod_minus_min_prod_constraint_ref)

        # --------------------------------------#
        # ---- Stream Demand ratio gradients ---#
        # --------------------------------------#
        all_streams_demand_ratio = outputs_dict[GlossaryEnergy.AllStreamsDemandRatioValue]
        energy_production_brut_detailed = outputs_dict['energy_production_brut_detailed']
        ratio_ref = inputs_dict['ratio_ref']
        # Loop on streams
        dobjective_dratio = self.compute_dratio_objective(
            all_streams_demand_ratio, ratio_ref, energy_list)
        ienergy = 0
        for energy in energy_list:
            ns_energy = self.get_ns_energy(energy)
            ddemand_ratio_denergy_prod, ddemand_ratio_denergy_cons = self.compute_ddemand_ratio_denergy_production(
                energy, sub_production_dict, sub_consumption_woratio_dict,
                scaling_factor_energy_production, years, energy_production_brut_detailed)
            self.set_partial_derivative_for_other_types(
                (GlossaryEnergy.AllStreamsDemandRatioValue,
                 f'{energy}'), (f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', energy),
                ddemand_ratio_denergy_prod)
            dobjective_dratio_energy = np.array([dobjective_dratio[ienergy + iyear * len(
                energy_list)] for iyear in range(len(years))]).reshape((1, len(years)))
            dobjective_dprod = np.matmul(
                dobjective_dratio_energy, ddemand_ratio_denergy_prod)

            self.set_partial_derivative_for_other_types(
                ('ratio_objective',), (f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', energy), dobjective_dprod)
            # ---- Loop on energy again to differentiate production and consumption ----#
            for energy_input in energy_list:
                ns_energy_input = self.get_ns_energy(energy_input)
                list_columns_energy_consumption = list(
                    inputs_dict[f'{energy_input}.{GlossaryEnergy.EnergyConsumptionValue}'].columns)
                if f'{energy} ({stream_class_dict[energy].unit})' in list_columns_energy_consumption:
                    self.set_partial_derivative_for_other_types(
                        (GlossaryEnergy.AllStreamsDemandRatioValue, f'{energy}'), (
                            f'{ns_energy_input}.{GlossaryEnergy.EnergyConsumptionWithoutRatioValue}',
                            f'{energy} ({stream_class_dict[energy].unit})'), ddemand_ratio_denergy_cons)
                    dobjective_dcons = np.matmul(
                        dobjective_dratio_energy, ddemand_ratio_denergy_cons)
                    self.set_partial_derivative_for_other_types(
                        ('ratio_objective',), (
                            f'{ns_energy_input}.{GlossaryEnergy.EnergyConsumptionWithoutRatioValue}',
                            f'{energy} ({stream_class_dict[energy].unit})'), dobjective_dcons)
            ienergy += 1
        # --------------------------------------#
        # ---- Land use constraint gradients----#
        # --------------------------------------#

        for energy in energy_list:
            ns_energy = self.get_ns_energy(energy)
            for key in outputs_dict['land_demand_df']:
                if key in inputs_dict[
                    f'{energy}.{GlossaryEnergy.LandUseRequiredValue}'] and key != GlossaryEnergy.Years:
                    self.set_partial_derivative_for_other_types(('land_demand_df', key),
                                                                (f'{ns_energy}.{GlossaryEnergy.LandUseRequiredValue}',
                                                                 key),
                                                                np.identity(len(years)))

    def set_gradient_for_co2_emissions(self, co2_variable, co2_emissions, co2_emission_column, energy, energy_prod_info,
                                       last_part_key, value, inputs_dict, years):

        if co2_emission_column in co2_emissions.columns:

            ns_energy = self.get_ns_energy(energy)

            '''
            Needed by energy mix gradient
            '''

            if last_part_key == 'prod':
                self.set_partial_derivative_for_other_types(
                    (co2_variable,
                     co2_emission_column), (f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', energy),
                    np.identity(len(years)) * inputs_dict['scaling_factor_energy_production'] * value / 1.0e3)
            elif last_part_key == 'cons':
                for energy_df in inputs_dict[GlossaryEnergy.energy_list]:
                    ns_energy_df = self.get_ns_energy(energy_df)
                    list_columnsenergycons = list(
                        inputs_dict[f'{energy_df}.{GlossaryEnergy.EnergyConsumptionValue}'].columns)
                    if f'{energy} (TWh)' in list_columnsenergycons:
                        self.set_partial_derivative_for_other_types(
                            (co2_variable, co2_emission_column),
                            (f'{ns_energy_df}.{GlossaryEnergy.EnergyConsumptionValue}',
                             f'{energy} (TWh)'),
                            np.identity(len(years)) * inputs_dict['scaling_factor_energy_consumption'] * value / 1.0e3)
            elif last_part_key == 'co2_per_use':
                self.set_partial_derivative_for_other_types(
                    (co2_variable,
                     co2_emission_column), (f'{ns_energy}.CO2_per_use', 'CO2_per_use'),
                    np.identity(len(years)) * value / 1.0e3)

            else:
                very_last_part_key = energy_prod_info.split('#')[2]
                if very_last_part_key == 'prod':
                    self.set_partial_derivative_for_other_types(
                        (co2_variable, co2_emission_column), (
                            f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', last_part_key),
                        np.identity(len(years)) * inputs_dict['scaling_factor_energy_production'] * value / 1.0e3)
                elif very_last_part_key == 'cons':
                    self.set_partial_derivative_for_other_types(
                        (co2_variable, co2_emission_column), (
                            f'{ns_energy}.{GlossaryEnergy.EnergyConsumptionValue}', last_part_key),
                        np.identity(len(years)) * inputs_dict['scaling_factor_energy_production'] * value / 1.0e3)

    def compute_dratio_objective(self, stream_ratios, ratio_ref, energy_list):
        '''
        Compute the ratio_objective with the gradient of stream_ratios vs any input and the ratio ojective value 
        obj = smooth_maximum(100.0 - ratio_arrays, 3)/ratio_ref

        dobj/dratio = -dsmooth_max(100.0 - ratio_arrays, 3)/ratio_ref
        '''

        dsmooth_dvar = get_dsmooth_dvariable(
            100.0 - stream_ratios[energy_list].values.flatten(), 3)
        dobjective_dratio = -np.asarray(dsmooth_dvar) / ratio_ref

        return dobjective_dratio

    def compute_denergy_production_objective_dprod(self, dtotal_production_denergy_production, alpha, prod, years):
        ''' energy_production_objective = np.asarray([(1. - alpha) * self.energy_model.production[GlossaryEnergy.TotalProductionValue][0] * delta_years
                                                  / self.energy_model.production[GlossaryEnergy.TotalProductionValue].sum(), ])
        '''

        tot_energy_production_sum = prod[GlossaryEnergy.TotalProductionValue].sum()
        dtot_energy_production_sum = dtotal_production_denergy_production.sum(
            axis=0)
        tot_energy_production_0 = prod[GlossaryEnergy.TotalProductionValue][0]
        dtot_energy_production_0 = dtotal_production_denergy_production[0]

        delta_years = (years[-1] - years[0] + 1)

        u = (1. - alpha) * \
            tot_energy_production_0 * delta_years
        v = tot_energy_production_sum
        u_prime = (1. - alpha) * dtot_energy_production_0 * \
                  delta_years
        v_prime = dtot_energy_production_sum
        dprod_objective_dprod = u_prime / v - u * v_prime / v ** 2

        return dprod_objective_dprod

    def compute_dproduction_net_denergy_production(self, energy, production_df, energy_price):
        '''
        energy_mean = sum(energy*1e6*prod*1e6)/total*1e6
        '''

        denergy_mean_prod = (
                                    energy_price[energy] * 1e6 * production_df[GlossaryEnergy.TotalProductionValue] -
                                    production_df[
                                        'energy_price_pond']) / (
                                    1e6 * (production_df[GlossaryEnergy.TotalProductionValue]) ** 2)

        # derivative of negative prod is 0
        index_l = production_df[production_df[f'production {energy} (TWh)']
                                == 0].index
        denergy_mean_prod.loc[index_l] = 0
        return denergy_mean_prod

    def compute_dtotal_production_denergy_production(self, production_detailed_df, min_energy, total_loss_percent):
        '''
        Compute gradient of production[GlossaryEnergy.TotalProductionValue] by {energy}.energy_prod[{energy}] taking into account
        the exponential decrease towards the limit applied on the calculation of the total net energy production
        Inputs: minimum_energy_production, production_df
        Outputs:dtotal_production_denergy_production
        '''
        years = production_detailed_df[GlossaryEnergy.Years]
        dtotal_production_denergy_production = np.ones(len(years))
        dtotal_production_denergy_production *= (
                1.0 - total_loss_percent)

        total_prod = production_detailed_df['Total production (uncut)'].values
        if total_prod.min() < min_energy:
            # To avoid underflow : exp(-200) is considered to be the
            # minimum value for the exp
            total_prod[total_prod < -200.0 * min_energy] = -200.0 * min_energy
            dtotal_production_denergy_production[total_prod < min_energy] = np.exp(
                total_prod[total_prod < min_energy] / min_energy) * np.exp(-1) / 10.0 * (1.0 - total_loss_percent)

        return np.identity(len(years)) * dtotal_production_denergy_production

    def compute_ddemand_ratio_denergy_production(self, energy, sub_production_dict, sub_consumption_dict,
                                                 scaling_factor_production, years, energy_production_brut_detailed):
        '''! Compute the gradient of the demand ratio vs energy production function :
                 -the ratio is capped to one if energy_prod>energy_cons, hence the special condition.
                 -the function is designed to be used even if no energy_input is specified (to get ddemand_ratio_denergy_prod gradient alone)
        @param energy: string, name of the energy 
        @param sub_production_dict: dictionary with the raw production for all the energies 
        @param sub_consumption_dict: dictionary with the raw consumption for all energies
        @param scaling_factor_production: float used to scale the energy production at input/output of the model
        @return ddemand_ratio_denergy_prod, ddemand_ratio_denergy_cons: numpy.arrays, shape=(len(years),len(years)) with the gradients
        :param years:
        :type years:
        :param energy_production_brut_detailed:
        :type energy_production_brut_detailed:
        '''

        # Calculate energy production and consumption
        energy_production = sub_production_dict[f'{energy}'][f'{energy}'].values
        if energy in EnergyMix.raw_tonet_dict.keys():
            column_name = f'{EnergyMix.PRODUCTION} {energy} ({self.stream_class_dict[energy].unit})'

            prod_raw_to_substract = energy_production_brut_detailed[column_name].values * \
                                    (1.0 - EnergyMix.raw_tonet_dict[energy])
            energy_production -= prod_raw_to_substract
        energy_consumption = np.zeros(len(years))
        for consu in sub_consumption_dict.values():
            if f'{energy} ({self.stream_class_dict[energy].unit})' in consu.columns:
                energy_consumption = np.sum([energy_consumption, consu[
                    f'{energy} ({self.stream_class_dict[energy].unit})'].values], axis=0)

        # If prod < cons, set the identity element for the given year to the
        # corresponding value
        denergy_prod_limited = compute_dfunc_with_exp_min(
            energy_production, 1.0e-10)
        energy_prod_limited = compute_func_with_exp_min(
            energy_production, 1.0e-10)

        # If prod < cons, set the identity element for the given year to
        # the corresponding value
        denergy_cons_limited = compute_dfunc_with_exp_min(
            energy_consumption, 1.0e-10)
        energy_cons_limited = compute_func_with_exp_min(
            energy_consumption, 1.0e-10)
        ddemand_ratio_denergy_cons = np.identity(len(years)) * 100.0 * \
                                     np.where((energy_prod_limited <= energy_cons_limited) * (
                                             energy_prod_limited / energy_cons_limited > 1E-15),
                                              -scaling_factor_production * energy_prod_limited * denergy_cons_limited /
                                              energy_cons_limited ** 2,
                                              0.0)

        if energy in EnergyMix.raw_tonet_dict.keys():

            denergy_prod_limited = np.identity(len(years)) * 100.0 * \
                                   np.where((energy_prod_limited <= energy_cons_limited) * (
                                           energy_prod_limited / energy_cons_limited > 1E-15),
                                            denergy_prod_limited * scaling_factor_production * EnergyMix.raw_tonet_dict[
                                                energy] /
                                            energy_cons_limited,
                                            0.0)
        else:
            denergy_prod_limited = np.identity(len(years)) * 100.0 * \
                                   np.where((energy_prod_limited <= energy_cons_limited) * (
                                           energy_prod_limited / energy_cons_limited > 1E-15),
                                            denergy_prod_limited * scaling_factor_production /
                                            energy_cons_limited,
                                            0.0)

        return denergy_prod_limited, ddemand_ratio_denergy_cons

    def compute_dmean_price_dprod(self, energy, energies, mix_weight, energy_price_after_tax,
                                  production_energy_net_pos_consumable, production_detailed_df, cons=False):
        """
        Function that returns the gradient of mean_price compared to energy_prod
        Params: 
            - energy: name of the energy derived by
            - energies: list of all the energies
            - mix_weight: dataframe of the energies ratio
            - energy_price_after_tax: dataframe with values 
            - production_energy_net_pos_consumable: dataframe with values
            - production_detailed_df: dataframe with values 
        Output:
            - dmean_price_dprod
        """
        mix_weight_energy = mix_weight[energy].values
        # The mix_weight_techno is zero means that the techno is negligible else we do nothing
        # np.sign gives 0 if zero and 1 if value so it suits well
        # with our needs
        grad_energy_mix_vs_prod = self.grad_energy_mix_vs_prod_dict[energy] * \
                                  np.sign(mix_weight_energy)
        grad_price_vs_prod = energy_price_after_tax[energy].values * \
                             grad_energy_mix_vs_prod
        for energy_other in energies:
            if energy_other != energy:
                mix_weight_techno_other = mix_weight[energy_other].values
                grad_energy_mix_vs_prod = self.grad_energy_mix_vs_prod_dict[
                                              f'{energy} {energy_other}'] * np.sign(mix_weight_techno_other)
                grad_price_vs_prod += energy_price_after_tax[energy_other].values * \
                                      grad_energy_mix_vs_prod
        # If the prod is negative then there is no gradient
        # BUT if the prod is zero a gradient in 0+ exists
        # then we check the sign of prod but if zero the gradient
        # should not be zero
        gradient_sign = np.sign(production_energy_net_pos_consumable[energy].values) + (
                production_detailed_df[f'production {energy} (TWh)'].values == 0.0)
        years = production_detailed_df[GlossaryEnergy.Years].values

        dmean_price_dprod = grad_price_vs_prod * \
                            gradient_sign * np.identity(len(years))
        # if dmean_price_dcons
        if cons:
            dmean_price_dprod = -grad_price_vs_prod * \
                                np.sign(
                                    production_energy_net_pos_consumable[energy].values) * np.identity(len(years))
        return dmean_price_dprod

    #

    def get_ns_energy(self, energy):
        '''
        Returns the namespace of the energy
        In case  of biomass , it is computed in agriculture model

        '''

        if energy == BiomassDry.name:
            ns_energy = AgricultureMixDiscipline.name
        else:
            ns_energy = energy

        return ns_energy

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['Energy price', 'Energy mean price', 'Energy mix',
                      'production', 'CO2 emissions', 'Carbon intensity', 'CO2 taxes over the years',
                      'Solid energy and electricity production constraint',
                      'Liquid hydrogen production constraint', 'Stream ratio', 'Energy mix losses']
        chart_filters.append(ChartFilter(
            'Charts', chart_list, chart_list, 'charts'))

        price_unit_list = ['$/MWh', '$/t']
        chart_filters.append(ChartFilter(
            'Price unit', price_unit_list, price_unit_list, 'price_unit'))

        year_start, year_end = self.get_sosdisc_inputs(
            [GlossaryEnergy.YearStart, GlossaryEnergy.YearEnd])
        years = list(np.arange(year_start, year_end + 1, 5))
        chart_filters.append(ChartFilter(
            'Years for energy mix', years, [year_start, year_end], GlossaryEnergy.Years))
        return chart_filters

    def get_post_processing_list(self, filters=None):

        # For the outputs, making a graph for block fuel vs range and blocktime vs
        # range

        instanciated_charts = []
        charts = []

        price_unit_list = ['$/MWh', '$/t']
        years_list = [self.get_sosdisc_inputs(GlossaryEnergy.YearStart)]
        energy_list = self.get_sosdisc_inputs(GlossaryEnergy.energy_list)
        # Overload default value with chart filter
        if filters is not None:
            for chart_filter in filters:
                if chart_filter.filter_key == 'charts':
                    charts = chart_filter.selected_values
                if chart_filter.filter_key == 'price_unit':
                    price_unit_list = chart_filter.selected_values
                if chart_filter.filter_key == GlossaryEnergy.Years:
                    years_list = chart_filter.selected_values

        if 'Energy price' in charts and '$/MWh' in price_unit_list:

            new_chart = self.get_chart_energy_price_in_dollar_kwh_without_production_taxes()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

            new_chart = self.get_chart_energy_price_in_dollar_kwh()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

            new_chart = self.get_chart_energy_price_after_co2_tax_in_dollar_kwh()
            if new_chart is not None:
                instanciated_charts.append(new_chart)
        if 'Energy mean price' in charts:

            new_chart = self.get_chart_energy_mean_price_in_dollar_mwh()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'Energy price' in charts and '$/t' in price_unit_list:

            new_chart = self.get_chart_energy_price_in_dollar_t()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'CO2 emissions' in charts:
            new_chart = self.get_chart_co2_needed_by_energy_mix()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'Carbon intensity' in charts:
            new_charts = self.get_chart_comparison_carbon_intensity()
            for new_chart in new_charts:
                if new_chart is not None:
                    instanciated_charts.append(new_chart)

        if 'production' in charts:
            new_chart = self.get_chart_energies_net_production()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

            new_chart = self.get_chart_energies_brut_production()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

            new_chart = self.get_chart_energies_net_raw_production_and_limit()
            if new_chart is not None:
                instanciated_charts.append(new_chart)
        if 'Energy mix' in charts:
            new_charts = self.get_pie_charts_production(years_list)
            for new_chart in new_charts:
                if new_chart is not None:
                    instanciated_charts.append(new_chart)

        if 'Solid energy and electricity production constraint' in charts and len(
                list(set(self.energy_constraint_list).intersection(energy_list))) > 0:
            new_chart = self.get_chart_solid_energy_elec_constraint()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'Liquid hydrogen production constraint' in charts and f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.liquid_hydrogen}' in energy_list:
            new_chart = self.get_chart_liquid_hydrogen_constraint()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'Stream ratio' in charts:
            new_chart = self.get_chart_stream_ratio()
            if new_chart is not None:
                instanciated_charts.append(new_chart)
        # Need data not in data_io of the discipline
        # TODO move this chart in a namespace post processing
        # new_chart = self.get_chart_stream_consumed_by_techno()
        # if new_chart is not None:
        #     instanciated_charts.append(new_chart)

        if 'Energy mix losses' in charts:

            new_chart = self.get_chart_energy_mix_losses(energy_list)
            if new_chart is not None:
                instanciated_charts.append(new_chart)
        return instanciated_charts

    def get_chart_solid_energy_elec_constraint(self):
        energy_production_detailed = self.get_sosdisc_outputs(
            GlossaryEnergy.EnergyProductionDetailedValue)
        solid_fuel_elec_percentage = self.get_sosdisc_inputs(
            'solid_fuel_elec_percentage')
        chart_name = f'Solid energy and electricity production constraint'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'Energy (TWh)', chart_name=chart_name)

        sum_solid_fuel_elec = energy_production_detailed[f'production {GlossaryEnergy.solid_fuel} (TWh)'].values + \
                              energy_production_detailed[f'production {GlossaryEnergy.electricity} (TWh)'].values
        new_serie = InstanciatedSeries(list(energy_production_detailed[GlossaryEnergy.Years].values),
                                       list(sum_solid_fuel_elec),
                                       'Sum of solid fuel and electricity productions', 'lines')
        new_chart.series.append(new_serie)

        new_serie = InstanciatedSeries(list(energy_production_detailed[GlossaryEnergy.Years].values), list(
            energy_production_detailed[GlossaryEnergy.TotalProductionValue].values * solid_fuel_elec_percentage),
                                       f'{100 * solid_fuel_elec_percentage}% of total production', 'lines')

        new_chart.series.append(new_serie)
        return new_chart

    def get_chart_liquid_hydrogen_constraint(self):
        energy_production_detailed = self.get_sosdisc_outputs(
            GlossaryEnergy.EnergyProductionDetailedValue)
        liquid_hydrogen_percentage = self.get_sosdisc_inputs(
            'liquid_hydrogen_percentage')
        chart_name = f'Liquid hydrogen production constraint'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'Energy (TWh)', chart_name=chart_name)

        new_serie = InstanciatedSeries(list(energy_production_detailed[GlossaryEnergy.Years].values), list(
            energy_production_detailed[f'production {GlossaryEnergy.hydrogen}.{GlossaryEnergy.liquid_hydrogen} (TWh)'].values),
                                       'Liquid hydrogen production', 'lines')
        new_chart.series.append(new_serie)
        new_serie = InstanciatedSeries(list(energy_production_detailed[GlossaryEnergy.Years].values), list(
            energy_production_detailed[f'production {GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen} (TWh)'].values +
            energy_production_detailed[f'production {GlossaryEnergy.hydrogen}.{GlossaryEnergy.liquid_hydrogen} (TWh)'].values),
                                       'Total hydrogen production', 'lines')
        new_chart.series.append(new_serie)
        constraint = liquid_hydrogen_percentage * \
                     (energy_production_detailed[f'production {GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen} (TWh)'].values +
                      energy_production_detailed[f'production {GlossaryEnergy.hydrogen}.{GlossaryEnergy.liquid_hydrogen} (TWh)'].values)
        new_serie = InstanciatedSeries(list(energy_production_detailed[GlossaryEnergy.Years].values), list(constraint),
                                       f'percentage of total hydrogen production', 'lines')
        new_chart.series.append(new_serie)
        return new_chart

    def get_chart_comparison_carbon_intensity(self):
        new_charts = []
        energy_co2_emissions = self.get_sosdisc_outputs(GlossaryEnergy.EnergyCO2EmissionsValue)
        chart_name = f'Comparison of carbon intensity for production of all energies'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'CO2 emissions [kg/kWh]', chart_name=chart_name)

        energy_list = self.get_sosdisc_inputs(GlossaryEnergy.energy_list)

        for energy in energy_list:
            if self.stream_class_dict[energy].unit == 'TWh':
                year_list = energy_co2_emissions[GlossaryEnergy.Years].values.tolist()
                emission_list = energy_co2_emissions[energy].values.tolist()
                serie = InstanciatedSeries(
                    year_list, emission_list, energy, 'lines')
                new_chart.series.append(serie)

        new_charts.append(new_chart)

        chart_name = f'Comparison of carbon intensity of all energies (production + use)'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'CO2 emissions [kg/kWh]', chart_name=chart_name)

        energy_co2_emissions = self.get_sosdisc_outputs(
            'energy_CO2_emissions_after_use')
        energy_list = self.get_sosdisc_inputs(GlossaryEnergy.energy_list)

        for energy in energy_list:
            if self.stream_class_dict[energy].unit == 'TWh':
                year_list = energy_co2_emissions[GlossaryEnergy.Years].values.tolist()
                emission_list = energy_co2_emissions[energy].values.tolist()
                serie = InstanciatedSeries(
                    year_list, emission_list, energy, 'lines')
                new_chart.series.append(serie)

        new_charts.append(new_chart)
        return new_charts

    def get_chart_energy_price_in_dollar_kwh(self):
        energy_prices = self.get_sosdisc_outputs(GlossaryEnergy.EnergyPricesValue)

        chart_name = 'Detailed prices of energy mix with CO2 taxes<br>from production (used for technology prices)'
        energy_list = self.get_sosdisc_inputs(GlossaryEnergy.energy_list)
        max_value = 0
        for energy in energy_list:
            if self.stream_class_dict[energy].unit == 'TWh':
                max_value = max(
                    max(energy_prices[energy].values.tolist()), max_value)

        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'Prices [$/MWh]', primary_ordinate_axis_range=[0, max_value], chart_name=chart_name)

        for energy in energy_list:
            ns_energy = self.get_ns_energy(energy)
            if self.stream_class_dict[energy].unit == 'TWh':
                techno_price = self.get_sosdisc_inputs(
                    f'{ns_energy}.{GlossaryEnergy.EnergyPricesValue}')
                serie = InstanciatedSeries(
                    energy_prices[GlossaryEnergy.Years].values.tolist(),
                    techno_price[energy].values.tolist(), energy, 'lines')
                new_chart.series.append(serie)

        return new_chart

    def get_chart_energy_price_in_dollar_kwh_without_production_taxes(self):
        energy_prices = self.get_sosdisc_outputs(GlossaryEnergy.EnergyPricesValue)
        chart_name = 'Detailed prices of energy mix without CO2 taxes from production'
        energy_list = self.get_sosdisc_inputs(GlossaryEnergy.energy_list)
        max_value = 0
        for energy in energy_list:
            if self.stream_class_dict[energy].unit == 'TWh':
                max_value = max(
                    max(energy_prices[energy].values.tolist()), max_value)

        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'Prices [$/MWh]', primary_ordinate_axis_range=[0, max_value], chart_name=chart_name)

        for energy in energy_list:
            ns_energy = self.get_ns_energy(energy)
            if self.stream_class_dict[energy].unit == 'TWh':
                techno_price = self.get_sosdisc_inputs(
                    f'{ns_energy}.{GlossaryEnergy.EnergyPricesValue}')
                serie = InstanciatedSeries(
                    energy_prices[GlossaryEnergy.Years].values.tolist(),
                    techno_price[f'{energy}_wotaxes'].values.tolist(), energy, 'lines')
                new_chart.series.append(serie)

        return new_chart

    def get_chart_energy_price_after_co2_tax_in_dollar_kwh(self):

        energy_prices_after_tax = self.get_sosdisc_outputs(
            'energy_prices_after_tax')

        chart_name = 'Detailed prices of energy mix after carbon taxes due to combustion'

        max_value = 0
        for energy in energy_prices_after_tax:
            if energy != GlossaryEnergy.Years:
                if self.stream_class_dict[energy].unit == 'TWh':
                    max_value = max(
                        max(energy_prices_after_tax[energy].values.tolist()), max_value)

        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'Prices [$/MWh]', primary_ordinate_axis_range=[0, max_value], chart_name=chart_name)
        for energy in energy_prices_after_tax:
            if energy != GlossaryEnergy.Years:
                if self.stream_class_dict[energy].unit == 'TWh':
                    serie = InstanciatedSeries(
                        energy_prices_after_tax[GlossaryEnergy.Years].values.tolist(),
                        energy_prices_after_tax[energy].values.tolist(), energy, 'lines')
                    new_chart.series.append(serie)

        return new_chart

    def get_chart_energy_price_in_dollar_t(self):
        energy_prices = self.get_sosdisc_outputs(GlossaryEnergy.EnergyPricesValue)

        chart_name = 'Detailed prices of Carbon Capture and Storage'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'Prices [$/t]', chart_name=chart_name)

        ccs_list = self.get_sosdisc_inputs(GlossaryEnergy.ccs_list)

        for ccs_name in ccs_list:
            techno_price = self.get_sosdisc_inputs(
                f'{ccs_name}.{GlossaryEnergy.EnergyPricesValue}')
            serie = InstanciatedSeries(
                energy_prices[GlossaryEnergy.Years].values.tolist(),
                techno_price[ccs_name].values.tolist(), ccs_name, 'lines')
            new_chart.series.append(serie)

        return new_chart

    def get_chart_energy_mean_price_in_dollar_mwh(self):
        energy_mean_price = self.get_sosdisc_outputs(GlossaryEnergy.EnergyMeanPriceValue)

        chart_name = 'Mean price out of energy mix'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'Prices [$/MWh]', chart_name=chart_name)

        serie = InstanciatedSeries(
            energy_mean_price[GlossaryEnergy.Years].values.tolist(),
            energy_mean_price[GlossaryEnergy.EnergyPriceValue].values.tolist(), 'mean energy', 'lines')
        new_chart.series.append(serie)

        return new_chart

    def get_chart_co2_emissions_by_energy(self):
        co2_emissions = self.get_sosdisc_outputs('co2_emissions_by_energy')
        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'CO2 emissions (Gt)', [], [
        ], 'CO2 emissions by energy (Gt)', stacked_bar=True)
        x_serie_1 = co2_emissions[GlossaryEnergy.Years].values.tolist()

        # for idx in co2_emissions.columns:

        for energy in co2_emissions:
            if energy != GlossaryEnergy.Years:
                co2_emissions_array = co2_emissions[energy].values / 1.0e3

                y_serie_1 = co2_emissions_array.tolist()

                serie = InstanciatedSeries(
                    x_serie_1,
                    y_serie_1, energy, display_type='bar')
                new_chart.add_series(serie)

        return new_chart

    def get_chart_energies_net_production(self):
        energy_production_detailed = self.get_sosdisc_outputs(
            GlossaryEnergy.EnergyProductionDetailedValue)
        chart_name = 'Net Energies production/consumption'
        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Net Energy [TWh]',
                                             chart_name=chart_name, stacked_bar=True)

        for reactant in energy_production_detailed.columns:
            if reactant not in [GlossaryEnergy.Years, GlossaryEnergy.TotalProductionValue, 'Total production (uncut)'] \
                    and GlossaryEnergy.carbon_capture not in reactant \
                    and GlossaryEnergy.carbon_storage not in reactant:
                energy_twh = energy_production_detailed[reactant].values
                legend_title = f'{reactant}'.replace(
                    "(TWh)", "").replace('production', '')
                serie = InstanciatedSeries(
                    energy_production_detailed[GlossaryEnergy.Years].values.tolist(),
                    energy_twh.tolist(), legend_title, 'bar')

                new_chart.series.append(serie)

        return new_chart

    def get_chart_energies_net_raw_production_and_limit(self):
        energy_production_detailed = self.get_sosdisc_outputs(
            GlossaryEnergy.EnergyProductionDetailedValue)
        minimum_energy_production = self.get_sosdisc_inputs(
            'minimum_energy_production')
        chart_name = 'Energy Total Production and Minimum Net Energy Limit'
        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Energy [TWh]',
                                             chart_name=chart_name)

        energy_prod_raw = self.get_sosdisc_outputs(
            'energy_production_brut')
        serie = InstanciatedSeries(
            energy_prod_raw[GlossaryEnergy.Years].values.tolist(),
            list(
                energy_prod_raw[GlossaryEnergy.TotalProductionValue].values.tolist()),
            'Raw Production', 'lines')

        new_chart.series.append(serie)
        serie = InstanciatedSeries(
            energy_production_detailed[GlossaryEnergy.Years].values.tolist(),
            list(
                energy_production_detailed[GlossaryEnergy.TotalProductionValue].values.tolist()),
            'Net Production', 'lines')
        new_chart.series.append(serie)

        serie = InstanciatedSeries(
            energy_production_detailed[GlossaryEnergy.Years].values.tolist(),
            list(
                energy_production_detailed['Total production (uncut)'].values.tolist()),
            'Net Production (uncut)', 'lines')
        new_chart.series.append(serie)

        serie = InstanciatedSeries(
            energy_production_detailed[GlossaryEnergy.Years].values.tolist(),
            list([minimum_energy_production for _ in range(
                len(energy_production_detailed[GlossaryEnergy.Years]))]),
            'Minimum net energy', 'lines')
        new_chart.series.append(serie)

        return new_chart

    def get_chart_energies_brut_production(self):
        energy_production_detailed = self.get_sosdisc_outputs(
            'energy_production_brut_detailed')
        chart_name = 'Raw Energies production'
        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Raw Energy [TWh]',
                                             chart_name=chart_name, stacked_bar=True)

        for reactant in energy_production_detailed.columns:
            if reactant not in [GlossaryEnergy.Years, GlossaryEnergy.TotalProductionValue] \
                    and GlossaryEnergy.carbon_capture not in reactant \
                    and GlossaryEnergy.carbon_storage not in reactant:
                energy_twh = energy_production_detailed[reactant].values
                legend_title = f'{reactant}'.replace(
                    "(TWh)", "").replace('production', '')
                serie = InstanciatedSeries(
                    energy_production_detailed[GlossaryEnergy.Years].values.tolist(),
                    energy_twh.tolist(), legend_title, 'bar')

                new_chart.series.append(serie)

        return new_chart

    def get_pie_charts_production(self, years_list):
        instanciated_charts = []
        energy_list = self.get_sosdisc_inputs(GlossaryEnergy.energy_list)
        energy_production_detailed = self.get_sosdisc_outputs(
            GlossaryEnergy.EnergyProductionDetailedValue)
        techno_production = energy_production_detailed[[GlossaryEnergy.Years]]

        for energy in energy_list:
            if self.stream_class_dict[energy].unit == 'TWh':
                techno_title = [
                    col for col in energy_production_detailed if col.endswith(f'{energy} (TWh)')]
                techno_production.loc[:,
                energy] = energy_production_detailed[techno_title[0]]

        for year in years_list:
            energy_pie_chart = [energy for energy in energy_list if
                                self.stream_class_dict[energy].unit == 'TWh']

            values = [techno_production.loc[techno_production[GlossaryEnergy.Years]
                                            == year][energy].sum() for energy in energy_pie_chart]
            values = list(np.maximum(0.0, np.array(values)))
            pie_chart = InstanciatedPieChart(
                f'Energy productions in {year}', energy_pie_chart, values)
            instanciated_charts.append(pie_chart)
        return instanciated_charts

    def get_chart_co2_streams(self):
        '''
        Plot the total co2 emissions sources - sinks
        '''
        chart_name = 'Total CO2 emissions before and after CCS'
        co2_emissions = self.get_sosdisc_outputs('co2_emissions')
        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'CO2 emissions (Gt)',
                                             chart_name=chart_name)

        x_serie_1 = co2_emissions[GlossaryEnergy.Years].values.tolist()

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions['CO2 emissions sources'].values / 1.0e3).tolist(), 'CO2 emissions sources')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions['CO2 emissions sinks'].values / 1.0e3).tolist(), 'CO2 emissions sinks')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions['Total CO2 emissions'].values / 1.0e3).tolist(), 'CO2 emissions after CCUS')
        new_chart.add_series(serie)

        return new_chart

    def get_chart_co2_to_store(self):
        '''
        Plot a graph to understand CO2 to store
        '''
        chart_name = 'CO2 emissions captured, used and to store'
        co2_emissions = self.get_sosdisc_outputs('co2_emissions')
        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'CO2 emissions (Gt)',
                                             chart_name=chart_name)

        x_serie_1 = co2_emissions[GlossaryEnergy.Years].values.tolist()

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'{CarbonCapture.name} (Mt) from CC technos'].values / 1.0e3).tolist(),
            'CO2 captured from CC technos')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (-co2_emissions[f'{CarbonCapture.name} needed by energy mix (Mt)'].values / 1.0e3).tolist(),
            f'{CarbonCapture.name} used by energy mix')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (-co2_emissions[f'{CO2.name} for food (Mt)'].values / 1.0e3).tolist(), f'{CO2.name} used for food')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'{CarbonCapture.name} to be stored (Mt)'].values / 1.0e3).tolist(), f'CO2 to store')
        new_chart.add_series(serie)

        return new_chart

    def get_chart_co2_limited_storage(self):
        '''
        Plot a graph to understand storage
        '''
        chart_name = 'CO2 emissions storage limited by CO2 to store'
        co2_emissions = self.get_sosdisc_outputs('co2_emissions')
        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'CO2 emissions (Gt)',
                                             chart_name=chart_name)

        x_serie_1 = co2_emissions[GlossaryEnergy.Years].values.tolist()
        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'{CarbonCapture.name} to be stored (Mt)'].values / 1.0e3).tolist(), f'CO2 to store')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'{CarbonStorage.name} (Mt)'].values / 1.0e3).tolist(), f'CO2 storage by invest')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'{CarbonStorage.name} Limited by capture (Mt)'].values / 1.0e3).tolist(),
            f'CO2 storage limited by CO2 to store')
        new_chart.add_series(serie)

        return new_chart

    def get_chart_co2_emissions_sources(self):
        '''
        Plot all CO2 emissions sources 
        '''
        chart_name = 'CO2 emissions sources'
        co2_emissions = self.get_sosdisc_outputs('co2_emissions')
        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'CO2 emissions (Gt)',
                                             chart_name=chart_name)

        x_serie_1 = co2_emissions[GlossaryEnergy.Years].values.tolist()

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions['Total CO2 by use (Mt)'].values / 1.0e3).tolist(), 'CO2 by use (net production burned)')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'Total {CarbonCapture.flue_gas_name} (Mt)'].values / 1.0e3).tolist(),
            'Flue gas from plants')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1, (
                    co2_emissions[f'{CarbonCapture.name} from energy mix (Mt)'].values / 1.0e3).tolist(),
            'Carbon capture from energy mix (FT or Sabatier)')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'{CO2.name} from energy mix (Mt)'].values / 1.0e3).tolist(),
            'CO2 from energy mix (machinery fuels)')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions['CO2 emissions sources'].values / 1.0e3).tolist(), 'Total sources')
        new_chart.add_series(serie)

        return new_chart

    def get_chart_co2_needed_by_energy_mix(self):
        '''
        Plot all CO2 emissions sinks 
        '''
        chart_name = 'CO2 emissions sinks'
        co2_emissions = self.get_sosdisc_outputs(
            'co2_emissions_needed_by_energy_mix')
        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'CO2 emissions (Gt)',
                                             chart_name=chart_name)

        x_serie_1 = co2_emissions[GlossaryEnergy.Years].values.tolist()

        serie = InstanciatedSeries(
            x_serie_1, (-co2_emissions[f'{CarbonCapture.name} needed by energy mix (Gt)'].values).tolist(),
            f'{CarbonCapture.name} needed by energy mix')
        new_chart.add_series(serie)

        return new_chart

    def get_chart_stream_ratio(self):
        '''
        Plot stream ratio chart
        '''
        chart_name = f'Stream Ratio Map'

        all_streams_demand_ratio = self.get_sosdisc_outputs(
            GlossaryEnergy.AllStreamsDemandRatioValue)

        years = all_streams_demand_ratio[GlossaryEnergy.Years].values
        streams = [
            col for col in all_streams_demand_ratio.columns if col not in [GlossaryEnergy.Years, ]]

        min_objective_energy_loc = all_streams_demand_ratio[streams].min(
        ).idxmin()
        min_objective_year_loc = all_streams_demand_ratio[GlossaryEnergy.Years][
            all_streams_demand_ratio[streams].idxmin()[
                min_objective_energy_loc]]
        chart_name += f'\n Minimum ratio is at year {min_objective_year_loc} for {min_objective_energy_loc}'
        z = np.asarray(all_streams_demand_ratio[streams].values).T
        fig = go.Figure()
        fig.add_trace(go.Heatmap(z=list(z), x=list(years), y=list(streams),
                                 type='heatmap', colorscale=['red', 'white'],
                                 colorbar={'title': 'Value of ratio'},
                                 opacity=0.5, zmax=100.0, zmin=0.0, ))
        new_chart = InstantiatedPlotlyNativeChart(
            fig, chart_name=chart_name, default_title=True)
        return new_chart

    def get_chart_energy_mix_losses(self, energy_list):
        '''
        Plot chart on energy mix heat losses 
        '''

        chart_name = f'Energy mix losses'

        raw_prod = self.get_sosdisc_outputs(
            'energy_production_brut')
        raw_prod_detailed = self.get_sosdisc_outputs(
            'energy_production_brut_detailed')

        inputs_dict = self.get_sosdisc_inputs()
        heat_losses_percentage = inputs_dict['heat_losses_percentage']
        years = raw_prod[GlossaryEnergy.Years].values.tolist()

        heat_losses = heat_losses_percentage / \
                      100.0 * raw_prod[GlossaryEnergy.TotalProductionValue].values
        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Energy losses (TWh)',
                                             chart_name=chart_name)

        for energy in energy_list:
            percentage_loss_name = f'{energy}.losses_percentage'
            if percentage_loss_name in inputs_dict:
                percentage = inputs_dict[percentage_loss_name]
                if percentage != 0.0:
                    losses = percentage / 100.0 * \
                             raw_prod_detailed[f'production {energy} (TWh)'].values
                    serie = InstanciatedSeries(
                        years, losses.tolist(), f'Distribution Transmission and Transport losses for {energy}')
                    new_chart.add_series(serie)

        serie = InstanciatedSeries(
            years, heat_losses.tolist(), f'Global energy losses from heat production')
        new_chart.add_series(serie)
        return new_chart

    def get_chart_stream_consumed_by_techno(self):
        '''
        Plot a table connecting all the streams in the ratio dataframe (left column)
        with the technologies consuming them (right column).
        '''
        chart_name = f'Stream consumption by technologies table'

        all_streams_demand_ratio = self.get_sosdisc_outputs(
            GlossaryEnergy.AllStreamsDemandRatioValue)

        streams = [
            col for col in all_streams_demand_ratio.columns if col not in [GlossaryEnergy.Years, ]]

        technologies_list = []
        for stream in streams:
            technologies_list_namespace_list = self.ee.dm.get_all_namespaces_from_var_name(
                stream + '.technologies_list')
            if len(technologies_list_namespace_list) != 0:
                technologies_list += self.ee.dm.get_data(
                    technologies_list_namespace_list[0])['value']
        techno_cons_dict = {}
        for techno in technologies_list:
            techno_disc = self.ee.dm.get_disciplines_with_name(self.ee.dm.get_all_namespaces_from_var_name(
                f'{techno}.{GlossaryEnergy.TechnoProductionValue}')[0][
                                                               :-len('.{GlossaryEnergy.TechnoProductionValue}')])[0]
            cons_col = techno_disc.get_sosdisc_outputs(
                GlossaryEnergy.TechnoDetailedConsumptionValue).columns
            consummed_stream = [col.split(' ')[0]
                                for col in cons_col if col not in [GlossaryEnergy.Years]]
            techno_cons_dict[techno] = consummed_stream
        table_data = []
        for stream in streams:
            table_data_line = []
            for techno in technologies_list:
                if stream in techno_cons_dict[techno]:
                    table_data_line += [techno]
            table_data += [[stream, str(table_data_line).strip('[]')]]

        header = list(['stream', 'technologies consuming this stream'])
        cells = list(np.asarray(table_data).T)

        new_chart = InstanciatedTable(
            table_name=chart_name, header=header, cells=cells)

        return new_chart
