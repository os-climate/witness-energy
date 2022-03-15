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
import pandas as pd

from energy_models.core.energy_mix.energy_mix import EnergyMix
from sos_trades_core.execution_engine.sos_discipline import SoSDiscipline
from sos_trades_core.tools.post_processing.charts.chart_filter import ChartFilter
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.core.stream_type.carbon_models.carbon_storage import CarbonStorage
from sos_trades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart
from sos_trades_core.tools.post_processing.pie_charts.instanciated_pie_chart import InstanciatedPieChart
from energy_models.core.stream_type.energy_models.syngas import Syngas
from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
from energy_models.core.stream_type.energy_models.liquid_fuel import LiquidFuel
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import GaseousHydrogen
from energy_models.core.stream_type.energy_models.liquid_hydrogen import LiquidHydrogen
from copy import deepcopy
from energy_models.core.stream_type.energy_models.solid_fuel import SolidFuel
from energy_models.core.stream_type.energy_models.electricity import Electricity
from sos_trades_core.tools.base_functions.exp_min import compute_dfunc_with_exp_min,\
    compute_func_with_exp_min
from plotly import graph_objects as go
from sos_trades_core.tools.post_processing.plotly_native_charts.instantiated_plotly_native_chart import InstantiatedPlotlyNativeChart
from sos_trades_core.tools.post_processing.tables.instanciated_table import InstanciatedTable
from sos_trades_core.tools.cst_manager.func_manager_common import get_dsmooth_dvariable,\
    get_dsmooth_dvariable_vect


class Energy_Mix_Discipline(SoSDiscipline):

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

    DESC_IN = {'energy_list': {'type': 'string_list', 'possible_values': EnergyMix.energy_list,
                               'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_study', 'editable': False, 'structuring': True},
               'ccs_list': {'type': 'string_list', 'possible_values': [CarbonCapture.name, CarbonStorage.name],
                            'default': [CarbonCapture.name, CarbonStorage.name],
                            'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_study', 'editable': False, 'structuring': True},
               'year_start': {'type': 'int', 'default': 2020, 'unit': '[-]', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
               'year_end': {'type': 'int', 'default': 2050, 'unit': '[-]', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
               'alpha': {'type': 'float', 'range': [0., 1.], 'default': 0.5, 'unit': '-', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_study'},
               'primary_energy_percentage': {'type': 'float', 'range': [0., 1.], 'default': 0.8, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ref'},
               'normalization_value_demand_constraints': {'type': 'float', 'default': 1000.0, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ref'},
               'CO2_taxes': {'type': 'dataframe', 'unit': '$/tCO2', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_study',
                             'dataframe_descriptor': {'years': ('int',  [1900, 2100], False),
                                                      'CO2_tax': ('float',  None, True)},
                             'dataframe_edition_locked': False},
               'CCS_constraint_factor': {'type': 'array', 'user_level': 2},
               'delta_co2_price': {'type': 'float', 'default': 200., 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
               'minimum_energy_production': {'type': 'float', 'default': 1e4, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public',
                                             'unit': 'TWh'},
               'total_prod_minus_min_prod_constraint_ref': {'type': 'float', 'default': 1e4, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ref'},
               'tol_constraint': {'type': 'float', 'default': 1e-3},
               'exp_min': {'type': 'bool', 'default': True, 'user_level': 2},
               'production_threshold': {'type': 'float', 'default': 1e-3},
               'scaling_factor_energy_production': {'type': 'float', 'default': 1e3, 'user_level': 2, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
               'scaling_factor_energy_consumption': {'type': 'float', 'default': 1e3, 'user_level': 2, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
               'solid_fuel_elec_percentage': {'type': 'float', 'default': 0.75, 'user_level': 2, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ref'},
               'solid_fuel_elec_constraint_ref': {'type': 'float', 'default': 10000., 'user_level': 2, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ref'},
               'liquid_hydrogen_percentage': {'type': 'array', 'user_level': 2, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ref'},
               'liquid_hydrogen_constraint_ref': {'type': 'float', 'default': 1000., 'user_level': 2, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ref'},
               'CO2_tax_ref': {'type': 'float', 'default': 1.0, 'unit': '$/tCO2', 'visibility': SoSDiscipline.SHARED_VISIBILITY,
                               'namespace': 'ns_ref', 'user_level': 2},
               'syngas_prod_ref': {'type': 'float', 'default': 10000., 'unit': 'TWh', 'user_level': 2, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ref'},
               'ratio_ref': {'type': 'float', 'default': 500., 'unit': '', 'user_level': 2, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ref'},
               'carbonstorage_limit': {'type': 'float', 'default': 12e6, 'unit': 'MT', 'user_level': 2, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ref'},
               'carbonstorage_constraint_ref': {'type': 'float', 'default': 12e6, 'unit': 'MT', 'user_level': 2, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ref'},
               'losses_percentage': {'type': 'float', 'default': 2654. / 183316 * 100, 'unit': '%', 'range': [0., 100.]}
               }

    DESC_OUT = {
        'All_Demand': {'type': 'dataframe', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_resource'},
        'energy_prices': {'type': 'dataframe', 'unit': '$/MWh'},
        'energy_CO2_emissions': {'type': 'dataframe', 'unit': 'kg/kWh'},
        'energy_CO2_emissions_after_use': {'type': 'dataframe', 'unit': 'kg/kWh'},
        'co2_emissions': {'type': 'dataframe', 'unit': 'Mt'},
        'co2_emissions_by_energy': {'type': 'dataframe', 'unit': 'Mt'},
        #'co2_emissions_Gt': {'type': 'dataframe', 'unit': 'Gt'},
        # energy_production and energy_consumption stored in PetaWh for
        # coupling variables scaling
        'energy_production': {'type': 'dataframe', 'unit': 'PWh'},
        'energy_production_detailed': {'type': 'dataframe', 'unit': 'TWh'},
        'energy_production_brut': {'type': 'dataframe', 'unit': 'TWh'},
        'energy_production_brut_detailed': {'type': 'dataframe', 'unit': 'TWh'},
        'energy_mix': {'type': 'dataframe', 'unit': '%'},
        'energy_prices_after_tax': {'type': 'dataframe', 'unit': '$/MWh'},
        'energy_production_objective': {'type': 'array', 'unit': '-', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_functions'},
        'primary_energies_production': {'type': 'dataframe', 'unit': 'Twh', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_functions'},
        'land_demand_df': {'type': 'dataframe', 'unit': 'Gha'},
        'energy_mean_price': {'type': 'dataframe', 'unit': '$/Mwh'},
        'production_energy_net_positive': {'type': 'dataframe', 'unit': 'TWh'},
        EnergyMix.TOTAL_PROD_MINUS_MIN_PROD_CONSTRAINT_DF: {
            'type': 'dataframe', 'unit': 'TWh',
            'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_functions'},
        EnergyMix.CONSTRAINT_PROD_H2_LIQUID: {
            'type': 'dataframe', 'unit': 'TWh',
            'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_functions'
        },
        EnergyMix.CONSTRAINT_PROD_SOLID_FUEL_ELEC: {
            'type': 'dataframe', 'unit': 'TWh',
            'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_functions'
        },

        EnergyMix.SYNGAS_PROD_OBJECTIVE: {'type': 'array', 'unit': 'TWh',
                                          'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_functions'},
        #'ratio_available_carbon_capture': {'type': 'dataframe', 'unit': '-'},
        'all_streams_demand_ratio': {'type': 'dataframe', 'unit': '-', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy'},
        'ratio_objective': {'type': 'array', 'unit': '-', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_functions'},
        'co2_emissions_needed_by_energy_mix': {'type': 'dataframe', 'unit': 'Gt', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy'},

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

    energy_constraint_list = EnergyMix.energy_constraint_list
    movable_fuel_list = EnergyMix.movable_fuel_list

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.energy_model = EnergyMix(self.energy_name)
        self.energy_model.configure_parameters(inputs_dict)

    def setup_sos_disciplines(self):

        dynamic_inputs = {}
        dynamic_outputs = {}

        if 'energy_list' in self._data_in:
            energy_list = self.get_sosdisc_inputs('energy_list')
            if energy_list is not None:
                for energy in energy_list:
                    dynamic_inputs[f'{energy}.energy_consumption'] = {
                        'type': 'dataframe', 'unit': 'PWh'}
                    dynamic_inputs[f'{energy}.energy_consumption_woratio'] = {
                        'type': 'dataframe', 'unit': 'PWh'}
                    dynamic_inputs[f'{energy}.energy_production'] = {
                        'type': 'dataframe', 'unit': 'PWh'}
                    dynamic_inputs[f'{energy}.energy_prices'] = {
                        'type': 'dataframe', 'unit': '$/MWh'}
                    dynamic_inputs[f'{energy}.energy_demand'] = {'type': 'dataframe', 'unit': 'TWh',
                                                                 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_demand'}

                    dynamic_outputs[f'{energy}.{EnergyMix.DELTA_ENERGY_PRICES}'] = {
                        'type': 'dataframe', 'unit': '$/MWh', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_mix'}

                    dynamic_inputs[f'{energy}.land_use_required'] = {
                        'type': 'dataframe', 'unit': '(Gha)'}

                    dynamic_inputs[f'{energy}.data_fuel_dict'] = {
                        'type': 'dict', 'visibility': SoSDiscipline.SHARED_VISIBILITY,
                        'namespace': 'ns_energy_mix', 'default':  self.energy_class_dict[energy].data_energy_dict}

                    if energy in self.energy_class_dict:

                        dynamic_inputs[f'{energy}.CO2_emissions'] = {
                            'type': 'dataframe', 'unit': 'kgCO2/kWh'}
                        dynamic_inputs[f'{energy}.CO2_per_use'] = {
                            'type': 'dataframe', 'unit': 'kgCO2/kWh'}

                        if energy == self.SYNGAS_NAME or energy == self.BIOMASS_DRY_NAME:
                            dynamic_outputs[f'{energy}.{EnergyMix.DEMAND_MAX_PRODUCTION}'] = {
                                'type': 'dataframe', 'unit': 'TWh', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_mix'}

                        dynamic_outputs[f'{energy}.{EnergyMix.DEMAND_VIOLATION}'] = {
                            'type': 'dataframe', 'unit': 'TWh', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_mix'}
                        dynamic_outputs[f'{energy}.{EnergyMix.DELTA_CO2_EMISSIONS}'] = {
                            'type': 'dataframe', 'unit': 'kgCO2/kWh', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_mix'}

                if 'syngas' in energy_list:
                    dynamic_inputs[f'syngas_ratio'] = {
                        'type': 'array', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_syngas'}

            if 'ccs_list' in self._data_in:
                ccs_list = self.get_sosdisc_inputs('ccs_list')
                if ccs_list is not None:
                    for ccs_name in ccs_list:
                        dynamic_inputs[f'{ccs_name}.energy_consumption'] = {
                            'type': 'dataframe', 'unit': 'PWh', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ccs'}
                        dynamic_inputs[f'{ccs_name}.energy_consumption_woratio'] = {
                            'type': 'dataframe', 'unit': 'PWh', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ccs'}
                        dynamic_inputs[f'{ccs_name}.energy_production'] = {
                            'type': 'dataframe', 'unit': 'PWh', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ccs'}
                        dynamic_inputs[f'{ccs_name}.energy_prices'] = {
                            'type': 'dataframe', 'unit': '$/MWh', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ccs'}
                        dynamic_inputs[f'{ccs_name}.energy_demand'] = {'type': 'dataframe', 'unit': 'TWh',
                                                                       'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_demand'}

                        dynamic_outputs[f'{ccs_name}.{EnergyMix.DELTA_ENERGY_PRICES}'] = {
                            'type': 'dataframe', 'unit': '$/MWh', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ccs'}

                        dynamic_inputs[f'{ccs_name}.land_use_required'] = {
                            'type': 'dataframe', 'unit': '(Gha)', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ccs'}

                        dynamic_inputs[f'{ccs_name}.data_fuel_dict'] = {
                            'type': 'dict', 'visibility': SoSDiscipline.SHARED_VISIBILITY,
                            'namespace': f'ns_{ccs_name}', 'default': self.stream_class_dict[ccs_name].data_energy_dict}

        self.add_inputs(dynamic_inputs)
        self.add_outputs(dynamic_outputs)

    def run(self):
        #-- get inputs
        inputs_dict = self.get_sosdisc_inputs()
        #-- configure class with inputs
        #
        self.energy_model.configure_parameters_update(inputs_dict)

        energy_prices_in = self.dm.get_value(
            self._convert_to_namespace_name('energy_prices', self.IO_TYPE_OUT))
        if energy_prices_in is None:
            energy_prices_in = pd.DataFrame(columns=inputs_dict['energy_list'])
            energy_prices_in['years'] = self.energy_model.years
            energy_prices_in.fillna(0.0, inplace=True)
        co2_emissions_in = self.dm.get_value(
            self._convert_to_namespace_name('energy_CO2_emissions_after_use', self.IO_TYPE_OUT))
        if co2_emissions_in is None:
            co2_emissions_in = pd.DataFrame(columns=inputs_dict['energy_list'])
            co2_emissions_in['years'] = self.energy_model.years
            co2_emissions_in.fillna(0.0, inplace=True)
        self.energy_model.set_energy_prices_in(
            energy_prices_in.copy(deep=True))
        self.energy_model.set_co2_emissions_in(
            co2_emissions_in.copy(deep=True))
        #-- compute informations
        self.energy_model.compute_energy_net_production()
        self.energy_model.compute_energy_brut_production()
        self.energy_model.compute_price_after_carbon_tax()
        self.energy_model.compute_CO2_emissions()

        self.energy_model.compute_CO2_emissions_ratio()
        self.energy_model.compute_energy_demand_violation()

        self.energy_model.compute_delta_on_co2_emissions()
        self.energy_model.compute_delta_on_prices()

        self.energy_model.aggregate_land_use_required()

        self.energy_model.compute_CO2_tax_minus_CCS_constraint()

        self.energy_model.compute_total_prod_minus_min_prod_constraint()
        self.energy_model.compute_constraint_solid_fuel_elec()
        self.energy_model.compute_constraint_h2()
        self.energy_model.compute_syngas_prod_objective()

        self.energy_model.compute_all_streams_demand_ratio()

        mean_price_df, production_energy_net_positive = self.energy_model.compute_mean_price(
            exp_min=inputs_dict['exp_min'])

        #-- Compute objectives with alpha trades
        alpha = inputs_dict['alpha']
        delta_years = inputs_dict['year_end'] - inputs_dict['year_start'] + 1

        energy_production_objective = np.asarray([(1. - alpha) * self.energy_model.production['Total production'][0] * delta_years
                                                  / self.energy_model.production['Total production'].sum(), ])

        #-- store outputs
        if EnergyMix.PRODUCTION in self.energy_model.energy_prices:
            self.energy_model.energy_prices.drop(
                columns=[EnergyMix.PRODUCTION], inplace=True)
        # energy_production stored in PetaWh for coupling variables scaling
        scaled_energy_production = pd.DataFrame(
            {'years': self.energy_model.production['years'].values,
             'Total production': self.energy_model.production['Total production'].values / inputs_dict['scaling_factor_energy_production']})
        self.energy_model.compute_constraint_h2()
        outputs_dict = {'All_Demand': self.energy_model.all_resource_demand,
                        'energy_prices': self.energy_model.energy_prices,
                        'co2_emissions': self.energy_model.total_co2_emissions,
                        #'co2_emissions_Gt': self.energy_model.total_co2_emissions_Gt,
                        'co2_emissions_by_energy': self.energy_model.emissions_by_energy,
                        'energy_CO2_emissions': self.energy_model.total_carbon_emissions,
                        'energy_CO2_emissions_after_use': self.energy_model.carbon_emissions_after_use,
                        'energy_production': scaled_energy_production,
                        'energy_production_detailed': self.energy_model.production,
                        'energy_production_brut': self.energy_model.production_brut[['years', 'Total production']],
                        'energy_production_brut_detailed': self.energy_model.production_brut,
                        'energy_mix': self.energy_model.mix_weights,
                        'energy_prices_after_tax': self.energy_model.energy_prices_after_carbon_tax,
                        'energy_production_objective':  energy_production_objective,
                        'land_demand_df': self.energy_model.land_use_required,
                        'energy_mean_price': mean_price_df,
                        'production_energy_net_positive': production_energy_net_positive,
                        self.energy_model.TOTAL_PROD_MINUS_MIN_PROD_CONSTRAINT_DF: self.energy_model.total_prod_minus_min_prod_constraint_df,
                        EnergyMix.CONSTRAINT_PROD_H2_LIQUID: self.energy_model.constraint_liquid_hydrogen,
                        EnergyMix.CONSTRAINT_PROD_SOLID_FUEL_ELEC: self.energy_model.constraint_solid_fuel_elec,
                        EnergyMix.SYNGAS_PROD_OBJECTIVE: self.energy_model.syngas_prod_objective,
                        'all_streams_demand_ratio': self.energy_model.all_streams_demand_ratio,
                        'ratio_objective': self.energy_model.ratio_objective,
                        'co2_emissions_needed_by_energy_mix': self.energy_model.co2_emissions_needed_by_energy_mix,
                        }
        normalization_value = inputs_dict['normalization_value_demand_constraints']
        energy_list = inputs_dict['energy_list']
        ccs_list = inputs_dict['ccs_list']
        primary_energy_percentage = inputs_dict['primary_energy_percentage']

        for e_name in energy_list:
            energy_demand_violation = self.energy_model.demand_viol[e_name]
            if e_name == self.SYNGAS_NAME or e_name == self.BIOMASS_DRY_NAME:
                energy_demand_max = self.energy_model.demand_max_production[e_name]
                energy_demand_max[EnergyMix.DEMAND_MAX_PRODUCTION] = energy_demand_max[
                    EnergyMix.DEMAND_MAX_PRODUCTION] / normalization_value
                outputs_dict[f'{e_name}.{EnergyMix.DEMAND_MAX_PRODUCTION}'] = energy_demand_max

            energy_demand_violation['demand_violation'] = energy_demand_violation['demand_violation'] / \
                normalization_value

            # energy demand violation, for each energy (not for streams)
            outputs_dict[f'{e_name}.{EnergyMix.DEMAND_VIOLATION}'] = energy_demand_violation

            outputs_dict[f'{e_name}.{EnergyMix.DELTA_CO2_EMISSIONS}'] = self.energy_model.delta_co2_emissions[e_name]

            # delta on computed energy prices
            outputs_dict[f'{e_name}.{EnergyMix.DELTA_ENERGY_PRICES}'] = self.energy_model.delta_energy_prices[e_name]

        for ccs_name in ccs_list:
            # delta on computed energy prices
            outputs_dict[f'{ccs_name}.{EnergyMix.DELTA_ENERGY_PRICES}'] = self.energy_model.delta_energy_prices[ccs_name]

        if 'production ' + self.LIQUID_FUEL_NAME + ' (TWh)' in self.energy_model.production and 'production ' + self.HYDROGEN_NAME + ' (TWh)' in self.energy_model.production and 'production ' + self.LIQUID_HYDROGEN_NAME + ' (TWh)' in self.energy_model.production:
            production_liquid_fuel = self.energy_model.production[
                'production ' + self.LIQUID_FUEL_NAME + ' (TWh)']
            production_hydrogen = self.energy_model.production[
                'production ' + self.HYDROGEN_NAME + ' (TWh)']
            production_liquid_hydrogen = self.energy_model.production[
                'production ' + self.LIQUID_HYDROGEN_NAME + ' (TWh)']
            sum_energies_production = production_liquid_fuel + \
                production_hydrogen + production_liquid_hydrogen

            energies_production_constraint = sum_energies_production - \
                primary_energy_percentage * \
                self.energy_model.production['Total production']

            outputs_dict['primary_energies_production'] = energies_production_constraint.to_frame(
                'primary_energies')
        else:
            outputs_dict['primary_energies_production'] = pd.DataFrame()

        #-- store outputs

        self.store_sos_outputs_values(outputs_dict)

    def compute_sos_jacobian(self):

        inputs_dict = self.get_sosdisc_inputs()
        outputs_dict = self.get_sosdisc_outputs()
        stream_class_dict = EnergyMix.stream_class_dict
        years = np.arange(inputs_dict['year_start'],
                          inputs_dict['year_end'] + 1)
        energy_list = inputs_dict['energy_list'] + inputs_dict['ccs_list']
        primary_energy_percentage = inputs_dict['primary_energy_percentage']
        normalization_value = inputs_dict['normalization_value_demand_constraints']
        production_detailed_df = outputs_dict['energy_production_detailed']
        minimum_energy_production = inputs_dict['minimum_energy_production']
        production_threshold = inputs_dict['production_threshold']
        total_prod_minus_min_prod_constraint_ref = inputs_dict[
            'total_prod_minus_min_prod_constraint_ref']
        production_energy_net_pos = outputs_dict['production_energy_net_positive']
        energies = [j for j in energy_list if j not in [
            'carbon_storage', 'carbon_capture']]
        mix_weight = self.get_sosdisc_outputs('energy_mix')
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
            sub_production_dict[energy] = inputs_dict[f'{energy}.energy_production'] * \
                scaling_factor_energy_production
            sub_consumption_dict[energy] = inputs_dict[f'{energy}.energy_consumption'] * \
                scaling_factor_energy_consumption

        #-------------------------------------------#
        #---- Production / Consumption gradients----#
        #-------------------------------------------#
        for energy in energy_list:
            if energy in energies:
                #---- Production gradients----#
                dtotal_prod_denergy_prod = self.compute_dtotal_production_denergy_production(
                    production_detailed_df, minimum_energy_production)
                dprod_objective_dprod = self.compute_denergy_production_objective_dprod(
                    dtotal_prod_denergy_prod)
                self.set_partial_derivative_for_other_types(
                    ('energy_production', 'Total production'), (f'{energy}.energy_production', energy),  dtotal_prod_denergy_prod)
                self.set_partial_derivative_for_other_types(
                    ('energy_production_detailed', 'Total production'), (f'{energy}.energy_production', energy), dtotal_prod_denergy_prod * scaling_factor_energy_production)
                self.set_partial_derivative_for_other_types(
                    ('energy_production_detailed', 'Total production (uncut)'), (f'{energy}.energy_production', energy), np.identity(len(years)) * scaling_factor_energy_production)
                self.set_partial_derivative_for_other_types(
                    ('energy_production_detailed', f'production {energy} ({stream_class_dict[energy].unit})'), (f'{energy}.energy_production', energy), np.identity(len(years)) * scaling_factor_energy_production)
                self.set_partial_derivative_for_other_types(
                    ('energy_production_brut', 'Total production'), (f'{energy}.energy_production', energy),  scaling_factor_energy_production * np.identity(len(years)))
                self.set_partial_derivative_for_other_types(
                    ('energy_production_objective',), (f'{energy}.energy_production', energy),  dprod_objective_dprod)
                if 'production ' + self.LIQUID_FUEL_NAME + ' (TWh)' in production_detailed_df.columns and 'production ' + self.HYDROGEN_NAME + ' (TWh)' in production_detailed_df.columns and 'production ' + self.LIQUID_HYDROGEN_NAME + ' (TWh)' in production_detailed_df.columns:
                    if energy == self.HYDROGEN_NAME or energy == self.LIQUID_HYDROGEN_NAME or energy == self.LIQUID_FUEL_NAME:
                        self.set_partial_derivative_for_other_types(('primary_energies_production', 'primary_energies'), (
                            f'{energy}.energy_production', energy), (np.identity(len(years)) - primary_energy_percentage * dtotal_prod_denergy_prod) * scaling_factor_energy_production)
                    else:
                        self.set_partial_derivative_for_other_types(('primary_energies_production', 'primary_energies'), (
                            f'{energy}.energy_production', energy), -scaling_factor_energy_production * primary_energy_percentage * dtotal_prod_denergy_prod)

                # constraint solid_fuel + elec gradient
                if energy in self.energy_model.energy_constraint_list:
                    self.set_partial_derivative_for_other_types((f'{EnergyMix.CONSTRAINT_PROD_SOLID_FUEL_ELEC}', 'constraint_solid_fuel_elec'), (
                        f'{energy}.energy_production', energy), (- scaling_factor_energy_production * (1 - solid_fuel_elec_percentage * dtotal_prod_denergy_prod) / solid_fuel_elec_constraint_ref) * np.identity(len(years)))
                else:
                    self.set_partial_derivative_for_other_types((f'{EnergyMix.CONSTRAINT_PROD_SOLID_FUEL_ELEC}', 'constraint_solid_fuel_elec'), (
                        f'{energy}.energy_production', energy),  scaling_factor_energy_production * solid_fuel_elec_percentage * dtotal_prod_denergy_prod / solid_fuel_elec_constraint_ref * np.identity(len(years)))

                if energy == self.SYNGAS_NAME:
                    self.set_partial_derivative_for_other_types(
                        (EnergyMix.SYNGAS_PROD_OBJECTIVE,), (f'{energy}.energy_production', energy),  scaling_factor_energy_production * np.sign(production_detailed_df['production syngas (TWh)'].values) * np.identity(len(years)) / syngas_prod_ref)
                # constraint liquid hydrogen

                if energy == self.LIQUID_HYDROGEN_NAME:
                    self.set_partial_derivative_for_other_types((f'{EnergyMix.CONSTRAINT_PROD_H2_LIQUID}', 'constraint_liquid_hydrogen'), (
                        f'{energy}.energy_production', energy), (- scaling_factor_energy_production * (liquid_hydrogen_percentage - 1) / liquid_hydrogen_constraint_ref) * np.identity(len(years)))
                elif energy == self.GASEOUS_HYDROGEN_NAME:
                    self.set_partial_derivative_for_other_types((f'{EnergyMix.CONSTRAINT_PROD_H2_LIQUID}', 'constraint_liquid_hydrogen'), (
                        f'{energy}.energy_production', energy), (- scaling_factor_energy_production * liquid_hydrogen_percentage / liquid_hydrogen_constraint_ref) * np.identity(len(years)))
                #---- Loop on energy again to differentiate production and consumption ----#
                for energy_input in energy_list:
                    list_columnsenergycons = list(
                        inputs_dict[f'{energy_input}.energy_consumption'].columns)
                    if f'{energy} ({stream_class_dict[energy].unit})' in list_columnsenergycons:
                        #---- Consumption gradients----#
                        dtotal_prod_denergy_cons = - \
                            self.compute_dtotal_production_denergy_production(
                                production_detailed_df, minimum_energy_production)
                        dprod_objective_dcons = self.compute_denergy_production_objective_dprod(
                            dtotal_prod_denergy_cons)
                        self.set_partial_derivative_for_other_types(
                            ('energy_production', 'Total production'), (
                                f'{energy_input}.energy_consumption', f'{energy} ({stream_class_dict[energy].unit})'),
                            scaling_factor_energy_consumption * dtotal_prod_denergy_cons / scaling_factor_energy_production)
                        self.set_partial_derivative_for_other_types(
                            ('energy_production_detailed', 'Total production'),
                            (f'{energy_input}.energy_consumption',
                             f'{energy} ({stream_class_dict[energy].unit})'),
                            scaling_factor_energy_consumption * dtotal_prod_denergy_cons / scaling_factor_energy_production * scaling_factor_energy_production)
                        self.set_partial_derivative_for_other_types(
                            ('energy_production_detailed',
                             'Total production (uncut)'),
                            (f'{energy_input}.energy_consumption',
                             f'{energy} ({stream_class_dict[energy].unit})'),
                            -scaling_factor_energy_consumption * np.identity(len(years)) / scaling_factor_energy_production * scaling_factor_energy_production)
                        self.set_partial_derivative_for_other_types(
                            ('energy_production_detailed',
                             f'production {energy} ({stream_class_dict[energy].unit})'),
                            (f'{energy_input}.energy_consumption',
                             f'{energy} ({stream_class_dict[energy].unit})'),
                            -scaling_factor_energy_consumption * np.identity(len(years)) / scaling_factor_energy_production * scaling_factor_energy_production)

                        self.set_partial_derivative_for_other_types(
                            ('energy_production_objective', ), (f'{energy_input}.energy_consumption', f'{energy} ({stream_class_dict[energy].unit})'), scaling_factor_energy_consumption * dprod_objective_dcons / scaling_factor_energy_production)
                        if 'production ' + self.LIQUID_FUEL_NAME + ' (TWh)' in production_detailed_df.columns and 'production ' + self.HYDROGEN_NAME + ' (TWh)' in production_detailed_df.columns and 'production ' + self.LIQUID_HYDROGEN_NAME + ' (TWh)' in production_detailed_df.columns:
                            if energy == self.HYDROGEN_NAME or energy == self.LIQUID_HYDROGEN_NAME or energy == self.LIQUID_FUEL_NAME:
                                self.set_partial_derivative_for_other_types(
                                    ('primary_energies_production', 'primary_energies'), (f'{energy_input}.energy_consumption', f'{energy} ({stream_class_dict[energy].unit})'),  scaling_factor_energy_consumption * (primary_energy_percentage * dtotal_prod_denergy_prod - np.identity(len(years))))
                            else:
                                self.set_partial_derivative_for_other_types(
                                    ('primary_energies_production', 'primary_energies'), (f'{energy_input}.energy_consumption', f'{energy} ({stream_class_dict[energy].unit})'),  scaling_factor_energy_consumption * primary_energy_percentage * dtotal_prod_denergy_prod)
                        # constraint solid_fuel + elec gradient

                        if energy in self.energy_model.energy_constraint_list:
                            self.set_partial_derivative_for_other_types((f'{EnergyMix.CONSTRAINT_PROD_SOLID_FUEL_ELEC}', 'constraint_solid_fuel_elec'), (
                                f'{energy_input}.energy_consumption', f'{energy} ({stream_class_dict[energy].unit})'), (scaling_factor_energy_consumption * (1 - solid_fuel_elec_percentage * dtotal_prod_denergy_prod) / solid_fuel_elec_constraint_ref) * np.identity(len(years)))
                        else:
                            self.set_partial_derivative_for_other_types((f'{EnergyMix.CONSTRAINT_PROD_SOLID_FUEL_ELEC}', 'constraint_solid_fuel_elec'), (
                                f'{energy_input}.energy_consumption', f'{energy} ({stream_class_dict[energy].unit})'), - scaling_factor_energy_consumption * solid_fuel_elec_percentage * dtotal_prod_denergy_prod / solid_fuel_elec_constraint_ref * np.identity(len(years)))

                        if energy == self.LIQUID_HYDROGEN_NAME:
                            self.set_partial_derivative_for_other_types((f'{EnergyMix.CONSTRAINT_PROD_H2_LIQUID}', 'constraint_liquid_hydrogen'), (
                                f'{energy_input}.energy_consumption', f'{energy} ({stream_class_dict[energy].unit})'), (scaling_factor_energy_production * (liquid_hydrogen_percentage - 1) / liquid_hydrogen_constraint_ref) * np.identity(len(years)))
                        elif energy == self.GASEOUS_HYDROGEN_NAME:
                            self.set_partial_derivative_for_other_types((f'{EnergyMix.CONSTRAINT_PROD_H2_LIQUID}', 'constraint_liquid_hydrogen'), (
                                f'{energy_input}.energy_consumption', f'{energy} ({stream_class_dict[energy].unit})'), (scaling_factor_energy_production * liquid_hydrogen_percentage / liquid_hydrogen_constraint_ref) * np.identity(len(years)))

                        if energy == self.SYNGAS_NAME:
                            self.set_partial_derivative_for_other_types(
                                (EnergyMix.SYNGAS_PROD_OBJECTIVE,), (
                                    f'{energy_input}.energy_consumption', f'{energy} ({stream_class_dict[energy].unit})'),  - scaling_factor_energy_production * np.sign(production_detailed_df['production syngas (TWh)'].values) * np.identity(len(years)) / syngas_prod_ref)
            else:
                # CCUS
                self.set_partial_derivative_for_other_types(
                    ('energy_production_detailed',
                     f'production {energy} ({stream_class_dict[energy].unit})'),
                    (f'{energy}.energy_production', energy), np.identity(len(years)) * scaling_factor_energy_production)
                # ---- Loop on energy again to differentiate production and consumption ----#
                for energy_input in energy_list:
                    list_columnsenergycons = list(
                        inputs_dict[f'{energy_input}.energy_consumption'].columns)
                    if f'{energy} ({stream_class_dict[energy].unit})' in list_columnsenergycons:
                        self.set_partial_derivative_for_other_types(
                            ('energy_production_detailed',
                             f'production {energy} ({stream_class_dict[energy].unit})'),
                            (f'{energy_input}.energy_consumption',
                             f'{energy} ({stream_class_dict[energy].unit})'),
                            -scaling_factor_energy_consumption * np.identity(
                                len(years)) / scaling_factor_energy_production * scaling_factor_energy_production)
        #-------------------------#
        #---- Prices gradients----#
        #-------------------------#
        for energy in energy_list:
            if energy in energies:
                self.set_partial_derivative_for_other_types(
                    ('energy_prices_after_tax', energy), (f'{energy}.energy_prices', energy),  np.identity(len(years)))
                self.set_partial_derivative_for_other_types(
                    ('energy_prices_after_tax', energy), (f'CO2_taxes', 'CO2_tax'),  inputs_dict[f'{energy}.CO2_per_use']['CO2_per_use'].values *
                    np.identity(len(years)))
                self.set_partial_derivative_for_other_types(
                    ('energy_prices_after_tax', energy), (f'{energy}.CO2_per_use', 'CO2_per_use'), inputs_dict[f'CO2_taxes']['CO2_tax'].values *
                    np.identity(len(years)))
            self.set_partial_derivative_for_other_types(
                ('energy_prices', energy), (f'{energy}.energy_prices', energy), np.identity(len(years)))

        #-------------------------------#
        #---Resource Demand gradients---#
        #-------------------------------#
        resource_list = EnergyMix.RESOURCE_LIST
        for energy in energy_list:
            for resource in inputs_dict[f'{energy}.energy_consumption']:
                if resource in resource_list:
                    self.set_partial_derivative_for_other_types(('All_Demand', resource), (
                        f'{energy}.energy_consumption', resource), scaling_factor_energy_consumption * np.identity(len(years)))
        #-----------------------------#
        #---- Mean Price gradients----#
        #-----------------------------#
        element_dict = dict(zip(energies, energies))
        self.grad_energy_mix_vs_prod_dict = self.energy_model.compute_grad_element_mix_vs_prod(
            deepcopy(production_energy_net_pos), element_dict, exp_min=inputs_dict['exp_min'], min_prod=production_threshold)
        dmean_price_dco2_tax = np.zeros((len(years), len(years)))
        for energy in energy_list:
            if energy in energies:
                mix_weight_energy = mix_weight[energy].values
                dmean_price_dco2_tax += inputs_dict[f'{energy}.CO2_per_use']['CO2_per_use'].values * \
                    mix_weight_energy
                self.set_partial_derivative_for_other_types(
                    ('energy_mean_price', 'energy_price'), (f'{energy}.energy_prices', energy), mix_weight_energy * np.identity(len(years)))
                self.set_partial_derivative_for_other_types(
                    ('energy_mean_price', 'energy_price'), (f'{energy}.CO2_per_use', 'CO2_per_use'), inputs_dict[f'CO2_taxes']['CO2_tax'].values *
                    mix_weight_energy * np.identity(len(years)))
                dmean_price_dprod = self.compute_dmean_price_dprod(energy, energies, mix_weight, energy_price_after_tax,
                                                                   production_energy_net_pos, production_detailed_df)
                self.set_partial_derivative_for_other_types(
                    ('energy_mean_price', 'energy_price'), (f'{energy}.energy_production', energy), scaling_factor_energy_production * dmean_price_dprod)

            for energy_input in energy_list:
                list_columnsenergycons = list(
                    inputs_dict[f'{energy_input}.energy_consumption'].columns)
                if f'{energy} ({stream_class_dict[energy].unit})' in list_columnsenergycons:
                    if energy in energies:
                        dmean_price_dcons = self.compute_dmean_price_dprod(energy, energies, mix_weight, energy_price_after_tax,
                                                                           production_energy_net_pos, production_detailed_df, cons=True)
                        self.set_partial_derivative_for_other_types(
                            ('energy_mean_price', 'energy_price'),
                            (f'{energy_input}.energy_consumption',
                             f'{energy} ({stream_class_dict[energy].unit})'),
                            scaling_factor_energy_consumption * dmean_price_dcons)
        self.set_partial_derivative_for_other_types(
            ('energy_mean_price', 'energy_price'), (f'CO2_taxes', 'CO2_tax'), dmean_price_dco2_tax * np.identity(len(years)))

        #--------------------------------#
        #-- New CO2 emissions gradients--#
        #--------------------------------#

        energy_production_detailed = self.get_sosdisc_outputs(
            'energy_production_detailed')
        alpha = self.get_sosdisc_inputs('alpha')
        co2_emissions = self.get_sosdisc_outputs('co2_emissions')
        self.energy_model.configure_parameters_update(inputs_dict)
        dtot_co2_emissions = self.energy_model.compute_grad_CO2_emissions(
            energy_production_detailed, co2_emissions, alpha)

        for key, value in dtot_co2_emissions.items():
            co2_emission_column = key.split(' vs ')[0]
            energy_prod_info = key.split(' vs ')[1]
            energy = energy_prod_info.split('#')[0]
            last_part_key = energy_prod_info.split('#')[1]
            if co2_emission_column in co2_emissions.columns and energy in energy_list:

                '''
                Needed by energy mix gradient
                '''
                if co2_emission_column == 'carbon_capture needed by energy mix (Mt)':
                    co2_emission_column_new = 'carbon_capture needed by energy mix (Gt)'
                    if last_part_key == 'prod':
                        self.set_partial_derivative_for_other_types(
                            ('co2_emissions_needed_by_energy_mix', co2_emission_column_new), (f'{energy}.energy_production', energy), np.identity(len(years)) * scaling_factor_energy_production * value / 1.0e3)
                    elif last_part_key == 'cons':
                        for energy_df in energy_list:
                            list_columnsenergycons = list(
                                inputs_dict[f'{energy_df}.energy_consumption'].columns)
                            if f'{energy} (TWh)' in list_columnsenergycons:
                                self.set_partial_derivative_for_other_types(
                                    ('co2_emissions_needed_by_energy_mix', co2_emission_column_new), (f'{energy_df}.energy_consumption', f'{energy} (TWh)'), np.identity(len(years)) * scaling_factor_energy_consumption * value / 1.0e3)
                    elif last_part_key == 'co2_per_use':
                        self.set_partial_derivative_for_other_types(
                            ('co2_emissions_needed_by_energy_mix', co2_emission_column_new), (f'{energy}.CO2_per_use', 'CO2_per_use'), np.identity(len(years)) * value / 1.0e3)

                    else:
                        very_last_part_key = energy_prod_info.split('#')[2]
                        if very_last_part_key == 'prod':
                            self.set_partial_derivative_for_other_types(
                                ('co2_emissions_needed_by_energy_mix', co2_emission_column_new), (f'{energy}.energy_production', last_part_key), np.identity(len(years)) * scaling_factor_energy_production * value / 1.0e3)
                        elif very_last_part_key == 'cons':
                            self.set_partial_derivative_for_other_types(
                                ('co2_emissions_needed_by_energy_mix', co2_emission_column_new), (f'{energy}.energy_consumption', last_part_key), np.identity(len(years)) * scaling_factor_energy_production * value / 1.0e3)

        #-----------------------------------#
        #---- Demand Violation gradients----#
        #-----------------------------------#
        for energy in energies:
            self.set_partial_derivative_for_other_types((f'{energy}.demand_violation', 'demand_violation'),
                                                        (f'{energy}.energy_demand',
                                                         'demand'), -np.identity(len(years)) / normalization_value)
            if energy in outputs_dict['energy_CO2_emissions'].keys():
                self.set_partial_derivative_for_other_types(
                    ('energy_CO2_emissions', energy), (f'{energy}.CO2_emissions', energy), np.identity(len(years)))
            for energy_input in energy_list:
                list_columnsenergyprod = list(
                    inputs_dict[f'{energy_input}.energy_production'].columns)
                list_columnsenergycons = list(
                    inputs_dict[f'{energy_input}.energy_consumption'].columns)
                list_index_prod = [j == energy for j in list_columnsenergyprod]
                list_index_conso = [
                    j == f'{energy} ({self.stream_class_dict[energy].unit})' for j in list_columnsenergycons]

                if True in list_index_prod:
                    dtotal_prod_denergy_prod = self.compute_dtotal_production_denergy_production(
                        production_detailed_df, minimum_energy_production)
                    self.set_partial_derivative_for_other_types((f'{energy}.demand_violation', 'demand_violation'),
                                                                (f'{energy_input}.energy_production',
                                                                 energy), scaling_factor_energy_production * np.identity(len(years)) / normalization_value)
                    self.set_partial_derivative_for_other_types((EnergyMix.TOTAL_PROD_MINUS_MIN_PROD_CONSTRAINT_DF,
                                                                 EnergyMix.TOTAL_PROD_MINUS_MIN_PROD_CONSTRAINT),
                                                                (f'{energy_input}.energy_production',
                                                                 energy), scaling_factor_energy_production * np.identity(len(years)) / total_prod_minus_min_prod_constraint_ref)
                    if energy == self.SYNGAS_NAME or energy == self.BIOMASS_DRY_NAME:
                        self.set_partial_derivative_for_other_types((f'{energy}.{EnergyMix.DEMAND_MAX_PRODUCTION}', 'demand_max_production'),
                                                                    (f'{energy_input}.energy_production',
                                                                     energy), - scaling_factor_energy_production * dtotal_prod_denergy_prod / normalization_value)

                if True in list_index_conso:
                    dtotal_prod_denergy_cons = - \
                        self.compute_dtotal_production_denergy_production(
                            production_detailed_df, minimum_energy_production)
                    self.set_partial_derivative_for_other_types((f'{energy}.demand_violation', 'demand_violation'),
                                                                (f'{energy_input}.energy_consumption',
                                                                 list_columnsenergycons[list_index_conso.index(True)]),
                                                                -scaling_factor_energy_consumption * np.identity(len(years)) / normalization_value)
                    self.set_partial_derivative_for_other_types((EnergyMix.TOTAL_PROD_MINUS_MIN_PROD_CONSTRAINT_DF,
                                                                 EnergyMix.TOTAL_PROD_MINUS_MIN_PROD_CONSTRAINT),
                                                                (f'{energy_input}.energy_consumption',
                                                                 list_columnsenergycons[list_index_conso.index(True)]),
                                                                -scaling_factor_energy_consumption * np.identity(len(years)) / total_prod_minus_min_prod_constraint_ref)
                    if energy == self.SYNGAS_NAME or energy == self.BIOMASS_DRY_NAME:

                        self.set_partial_derivative_for_other_types((f'{energy}.{EnergyMix.DEMAND_MAX_PRODUCTION}', 'demand_max_production'),
                                                                    (f'{energy_input}.energy_consumption',
                                                                     list_columnsenergycons[list_index_conso.index(True)]),
                                                                    scaling_factor_energy_consumption * dtotal_prod_denergy_cons / normalization_value)

        #--------------------------------------#
        #---- Stream Demand ratio gradients ---#
        #--------------------------------------#
        all_streams_demand_ratio = self.get_sosdisc_outputs(
            'all_streams_demand_ratio')
        ratio_ref = self.get_sosdisc_inputs('ratio_ref')
        # Loop on streams
        dobjective_dratio = self.compute_dratio_objective(
            all_streams_demand_ratio, ratio_ref, energy_list)
        ienergy = 0
        for energy in energy_list:

            ddemand_ratio_denergy_prod, ddemand_ratio_denergy_cons = self.compute_ddemand_ratio_denergy_production(
                energy, sub_production_dict, sub_consumption_woratio_dict, stream_class_dict, scaling_factor_energy_production, years)
            self.set_partial_derivative_for_other_types(
                ('all_streams_demand_ratio', f'{energy}'), (f'{energy}.energy_production', energy),  ddemand_ratio_denergy_prod)
            dobjective_dratio_energy = np.array([dobjective_dratio[ienergy + iyear * len(
                energy_list)] for iyear in range(len(years))]).reshape((1, len(years)))
            dobjective_dprod = np.matmul(
                dobjective_dratio_energy, ddemand_ratio_denergy_prod)

            self.set_partial_derivative_for_other_types(
                ('ratio_objective',), (f'{energy}.energy_production', energy), dobjective_dprod)
            #---- Loop on energy again to differentiate production and consumption ----#
            for energy_input in energy_list:
                list_columnsenergycons = list(
                    inputs_dict[f'{energy_input}.energy_consumption'].columns)
                if f'{energy} ({stream_class_dict[energy].unit})' in list_columnsenergycons:
                    self.set_partial_derivative_for_other_types(
                        ('all_streams_demand_ratio', f'{energy}'), (
                            f'{energy_input}.energy_consumption_woratio', f'{energy} ({stream_class_dict[energy].unit})'), ddemand_ratio_denergy_cons)
                    dobjective_dcons = np.matmul(
                        dobjective_dratio_energy, ddemand_ratio_denergy_cons)
                    self.set_partial_derivative_for_other_types(
                        ('ratio_objective',), (
                            f'{energy_input}.energy_consumption_woratio', f'{energy} ({stream_class_dict[energy].unit})'),  dobjective_dcons)
            ienergy += 1
        #--------------------------------------#
        #---- Land use constraint gradients----#
        #--------------------------------------#

        for energy in energy_list:
            for key in outputs_dict['land_demand_df']:
                if key in inputs_dict[f'{energy}.land_use_required'] and key != 'years':
                    self.set_partial_derivative_for_other_types(('land_demand_df', key),
                                                                (f'{energy}.land_use_required', key), np.identity(len(years)))

    def compute_dratio_objective(self, stream_ratios,  ratio_ref, energy_list):
        '''
        Compute the ratio_objective with the gradient of stream_ratios vs any input and the ratio ojective value 
        obj = smooth_maximum(100.0 - ratio_arrays, 3)/ratio_ref

        dobj/dratio = -dsmooth_max(100.0 - ratio_arrays, 3)/ratio_ref
        '''

        dsmooth_dvar = get_dsmooth_dvariable(
            100.0 - stream_ratios[energy_list].values.flatten(), 3)
        dobjective_dratio = -np.asarray(dsmooth_dvar) / ratio_ref

        return dobjective_dratio

    def compute_ddelta_energy_prices(self, energy):

        years = np.arange(self.get_sosdisc_inputs('year_start'),
                          self.get_sosdisc_inputs('year_end') + 1)

        self.set_partial_derivative(
            f'{energy}.{EnergyMix.DELTA_ENERGY_PRICES}', (f'{energy}.energy_prices', energy), -np.identity(len(years)))

    def compute_ddelta_emissions_co2(self, energy):

        years = np.arange(self.get_sosdisc_inputs('year_start'),
                          self.get_sosdisc_inputs('year_end') + 1)

        self.set_partial_derivative(
            f'{energy}.{EnergyMix.DELTA_CO2_EMISSIONS}', (f'{energy}.CO2_emissions', energy), -np.identity(len(years)))

    def compute_denergy_production_objective_dprod(self, dtotal_production_denergy_production):
        ''' energy_production_objective = np.asarray([(1. - alpha) * self.energy_model.production['Total production'][0] * delta_years
                                                  / self.energy_model.production['Total production'].sum(), ])
        '''
        alpha = self.get_sosdisc_inputs('alpha')
        tot_energy_production_sum = self.get_sosdisc_outputs(
            'energy_production')['Total production'].sum()
        dtot_energy_production_sum = dtotal_production_denergy_production.sum(
            axis=0)
        tot_energy_production_0 = self.get_sosdisc_outputs(
            'energy_production')['Total production'][0]
        dtot_energy_production_0 = dtotal_production_denergy_production[0]
        years = np.arange(self.get_sosdisc_inputs('year_start'),
                          self.get_sosdisc_inputs('year_end') + 1)
        delta_years = (years[-1] - years[0] + 1)

        u = (1. - alpha) * \
            tot_energy_production_0 * delta_years
        v = tot_energy_production_sum
        u_prime = (1. - alpha) * dtot_energy_production_0 * \
            delta_years
        v_prime = dtot_energy_production_sum
        dprod_objective_dprod = u_prime / v - u * v_prime / v**2

        return dprod_objective_dprod

    def compute_dproduction_net_denergy_production(self, energy, production_df, energy_price):
        '''
        energy_mean = sum(energy*1e6*prod*1e6)/total*1e6
        '''

        denergy_mean_prod = (
            energy_price[energy] * 1e6 * production_df['Total production'] - production_df['energy_price_pond']) / (1e6 * (production_df['Total production'])**2)

        # derivative of negative prod is 0
        index_l = production_df[production_df[f'production {energy} (TWh)']
                                == 0].index
        denergy_mean_prod.loc[index_l] = 0
        return denergy_mean_prod

    def compute_dtotal_production_denergy_production(self, production_detailed_df, min_energy):
        '''
        Compute gradient of production['Total production'] by {energy}.energy_prod[{energy}] taking into account 
        the exponential decrease towards the limit applied on the calculation of the total net energy production
        Inputs: minimum_energy_production, production_df
        Outputs:dtotal_production_denergy_production
        '''
        years = production_detailed_df['years']
        dtotal_production_denergy_production = np.ones(len(years))

        pre_limit_total_production = pd.DataFrame({'years': years,
                                                   'Total production': 0.0})
        pre_limit_total_production['Total production'] = production_detailed_df[[
            column for column in production_detailed_df if column.endswith('(TWh)')]].sum(axis=1)

        total_prod = pre_limit_total_production['Total production'].values
        if total_prod.min() < min_energy:
                # To avoid underflow : exp(-200) is considered to be the
                # minimum value for the exp
            total_prod[total_prod < -200.0 * min_energy] = -200.0 * min_energy
            dtotal_production_denergy_production[total_prod < min_energy] = np.exp(
                total_prod[total_prod < min_energy] / min_energy) * np.exp(-1) / 10.0

        return np.identity(len(years)) * dtotal_production_denergy_production

    def compute_ddemand_ratio_denergy_production(self, energy, sub_production_dict, sub_consumption_dict, stream_class_dict,
                                                 scaling_factor_production, years):
        '''! Compute the gradient of the demand ratio vs energy production function :
                 -the ratio is capped to one if energy_prod>energy_cons, hence the special condition.
                 -the function is designed to be used even if no energy_input is specified (to get ddemand_ratio_denergy_prod gradient alone)
        @param energy: string, name of the energy 
        @param sub_production_dict: dictionary with the raw production for all the energies 
        @param sub_consumption_dict: dictionary with the raw consumption for all energies
        @param stream_class_dict: dictionary with informations on the energies
        @param scaling_factor_production: float used to scale the energy production at input/output of the model
        @return ddemand_ratio_denergy_prod, ddemand_ratio_denergy_cons: numpy.arrays, shape=(len(years),len(years)) with the gradients
        '''

        # Calculate energy production and consumption
        energy_production = sub_production_dict[f'{energy}'][f'{energy}'].values
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
        energy_cons_limited = compute_func_with_exp_min(
            energy_consumption, 1.0e-10)
        ddemand_ratio_denergy_prod = np.identity(len(years)) * 100.0 *\
            np.where(energy_prod_limited <= energy_cons_limited,
                     scaling_factor_production * denergy_prod_limited / energy_cons_limited,
                     0.0)

        # If prod < cons, set the identity element for the given year to
        # the corresponding value
        denergy_cons_limited = compute_dfunc_with_exp_min(
            energy_consumption, 1.0e-10)
        energy_cons_limited = compute_func_with_exp_min(
            energy_consumption, 1.0e-10)
        ddemand_ratio_denergy_cons = np.identity(len(years)) * 100.0 *\
            np.where(energy_prod_limited <= energy_cons_limited,
                     -scaling_factor_production * energy_prod_limited * denergy_cons_limited /
                     energy_cons_limited**2,
                     0.0)

        return ddemand_ratio_denergy_prod, ddemand_ratio_denergy_cons

    def compute_dmean_price_dprod(self, energy, energies, mix_weight, energy_price_after_tax,
                                  production_energy_net_pos, production_detailed_df, cons=False):
        """
        Function that returns the gradient of mean_price compared to energy_prod
        Params: 
            - energy: name of the energy derived by
            - energies: list of all the energies
            - mix_weight: dataframe of the energies ratio
            - energy_price_after_tax: dataframe with values 
            - production_energy_net_pos: dataframe with values 
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
        gradient_sign = np.sign(production_energy_net_pos[energy].values) + (
            production_detailed_df[f'production {energy} (TWh)'].values == 0.0)
        years = production_detailed_df['years'].values

        dmean_price_dprod = grad_price_vs_prod * \
            gradient_sign * np.identity(len(years))
        # if dmean_price_dcons
        if cons:
            dmean_price_dprod = -grad_price_vs_prod * \
                np.sign(
                    production_energy_net_pos[energy].values) * np.identity(len(years))
        return dmean_price_dprod

#

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['Energy price', 'Energy mean price', 'Energy mix',
                      'production', 'CO2 emissions', 'Carbon intensity', 'Demand violation',
                      'Delta price', 'CO2 taxes over the years', 'Solid energy and electricity production constraint',
                      'Liquid hydrogen production constraint', 'Stream ratio']
        chart_filters.append(ChartFilter(
            'Charts', chart_list, chart_list, 'charts'))

        price_unit_list = ['$/MWh', '$/t']
        chart_filters.append(ChartFilter(
            'Price unit', price_unit_list, price_unit_list, 'price_unit'))

        year_start, year_end = self.get_sosdisc_inputs(
            ['year_start', 'year_end'])
        years = list(np.arange(year_start, year_end + 1, 5))
        chart_filters.append(ChartFilter(
            'Years for energy mix', years, [year_start, year_end], 'years'))
        return chart_filters

    def get_post_processing_list(self, filters=None):

        # For the outputs, making a graph for block fuel vs range and blocktime vs
        # range

        instanciated_charts = []
        charts = []

        price_unit_list = ['$/MWh', '$/t']
        years_list = [self.get_sosdisc_inputs('year_start')]
        energy_list = self.get_sosdisc_inputs('energy_list')
        # Overload default value with chart filter
        if filters is not None:
            for chart_filter in filters:
                if chart_filter.filter_key == 'charts':
                    charts = chart_filter.selected_values
                if chart_filter.filter_key == 'price_unit':
                    price_unit_list = chart_filter.selected_values
                if chart_filter.filter_key == 'years':
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

            new_chart = self.get_chart_energies_net_production_limit()
            if new_chart is not None:
                instanciated_charts.append(new_chart)
        if 'Energy mix' in charts:
            new_charts = self.get_pie_charts_production(years_list)
            for new_chart in new_charts:
                if new_chart is not None:
                    instanciated_charts.append(new_chart)

        if 'Demand violation' in charts and '$/MWh' in price_unit_list:
            new_chart = self.get_chart_demand_violation_kwh()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'Delta price' in charts:
            new_chart = self.get_chart_delta_price()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'Solid energy and electricity production constraint' in charts and len(list(set(self.energy_constraint_list).intersection(energy_list))) > 0:
            new_chart = self.get_chart_solid_energy_elec_constraint()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'Liquid hydrogen production constraint' in charts and self.LIQUID_HYDROGEN_NAME in energy_list:
            new_chart = self.get_chart_liquid_hydrogen_constraint()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'Stream ratio' in charts:
            new_chart = self.get_chart_stream_ratio()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

            new_chart = self.get_chart_stream_consumed_by_techno()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_chart_solid_energy_elec_constraint(self):
        energy_production_detailed = self.get_sosdisc_outputs(
            'energy_production_detailed')
        solid_fuel_elec_percentage = self.get_sosdisc_inputs(
            'solid_fuel_elec_percentage')
        chart_name = f'Solid energy and electricity production constraint'
        new_chart = TwoAxesInstanciatedChart(
            'years', 'Energy (TWh)', chart_name=chart_name)

        sum_solid_fuel_elec = energy_production_detailed['production solid_fuel (TWh)'].values + \
            energy_production_detailed['production electricity (TWh)'].values
        new_serie = InstanciatedSeries(list(energy_production_detailed['years'].values), list(sum_solid_fuel_elec),
                                       'Sum of solid fuel and electricity productions', 'lines')
        new_chart.series.append(new_serie)

        new_serie = InstanciatedSeries(list(energy_production_detailed['years'].values), list(energy_production_detailed['Total production'].values * solid_fuel_elec_percentage),
                                       f'{100*solid_fuel_elec_percentage}% of total production', 'lines')

        new_chart.series.append(new_serie)
        return new_chart

    def get_chart_liquid_hydrogen_constraint(self):
        energy_production_detailed = self.get_sosdisc_outputs(
            'energy_production_detailed')
        liquid_hydrogen_percentage = self.get_sosdisc_inputs(
            'liquid_hydrogen_percentage')
        chart_name = f'Liquid hydrogen production constraint'
        new_chart = TwoAxesInstanciatedChart(
            'years', 'Energy (TWh)', chart_name=chart_name)

        new_serie = InstanciatedSeries(list(energy_production_detailed['years'].values), list(energy_production_detailed['production hydrogen.liquid_hydrogen (TWh)'].values),
                                       'Liquid hydrogen production', 'lines')
        new_chart.series.append(new_serie)
        new_serie = InstanciatedSeries(list(energy_production_detailed['years'].values), list(energy_production_detailed['production hydrogen.gaseous_hydrogen (TWh)'].values),
                                       'Gaseous hydrogen production', 'lines')
        new_chart.series.append(new_serie)
        constraint = liquid_hydrogen_percentage * \
            (energy_production_detailed['production hydrogen.gaseous_hydrogen (TWh)'].values +
             energy_production_detailed['production hydrogen.liquid_hydrogen (TWh)'].values)
        new_serie = InstanciatedSeries(list(energy_production_detailed['years'].values), list(constraint),
                                       f'{100*liquid_hydrogen_percentage}% of total hydrogen production', 'lines')
        new_chart.series.append(new_serie)
        return new_chart

    def get_chart_comparison_carbon_intensity(self):
        new_charts = []
        energy_co2_emissions = self.get_sosdisc_outputs('energy_CO2_emissions')
        chart_name = f'Comparison of carbon intensity for production of all energies'
        new_chart = TwoAxesInstanciatedChart(
            'years', 'CO2 emissions [kg/kWh]', chart_name=chart_name)

        energy_list = self.get_sosdisc_inputs('energy_list')

        for energy in energy_list:
            if self.stream_class_dict[energy].unit == 'TWh':
                year_list = energy_co2_emissions['years'].values.tolist()
                emission_list = energy_co2_emissions[energy].values.tolist()
                serie = InstanciatedSeries(
                    year_list, emission_list, energy, 'lines')
                new_chart.series.append(serie)

        new_charts.append(new_chart)

        chart_name = f'Comparison of carbon intensity of all energies (production + use)'
        new_chart = TwoAxesInstanciatedChart(
            'years', 'CO2 emissions [kg/kWh]', chart_name=chart_name)

        energy_co2_emissions = self.get_sosdisc_outputs(
            'energy_CO2_emissions_after_use')
        energy_list = self.get_sosdisc_inputs('energy_list')

        for energy in energy_list:
            if self.stream_class_dict[energy].unit == 'TWh':
                year_list = energy_co2_emissions['years'].values.tolist()
                emission_list = energy_co2_emissions[energy].values.tolist()
                serie = InstanciatedSeries(
                    year_list, emission_list, energy, 'lines')
                new_chart.series.append(serie)

        new_charts.append(new_chart)
        return new_charts

    def get_chart_energy_price_in_dollar_kwh(self):
        energy_prices = self.get_sosdisc_outputs('energy_prices')

        chart_name = 'Detailed prices of energy mix with CO2 taxes<br>from production (used for technology prices)'
        energy_list = self.get_sosdisc_inputs('energy_list')
        max_value = 0
        for energy in energy_list:
            if self.stream_class_dict[energy].unit == 'TWh':
                techno_price = self.get_sosdisc_inputs(
                    f'{energy}.energy_prices')
                max_value = max(
                    max(energy_prices[energy].values.tolist()), max_value)

        new_chart = TwoAxesInstanciatedChart(
            'years', 'Prices [$/MWh]', primary_ordinate_axis_range=[0, max_value], chart_name=chart_name)

        for energy in energy_list:
            if self.stream_class_dict[energy].unit == 'TWh':
                techno_price = self.get_sosdisc_inputs(
                    f'{energy}.energy_prices')
                serie = InstanciatedSeries(
                    energy_prices['years'].values.tolist(),
                    techno_price[energy].values.tolist(), energy, 'lines')
                new_chart.series.append(serie)

        return new_chart

    def get_chart_energy_price_in_dollar_kwh_without_production_taxes(self):
        energy_prices = self.get_sosdisc_outputs('energy_prices')

        chart_name = 'Detailed prices of energy mix without CO2 taxes from production'
        energy_list = self.get_sosdisc_inputs('energy_list')
        max_value = 0
        for energy in energy_list:
            if self.stream_class_dict[energy].unit == 'TWh':
                max_value = max(
                    max(energy_prices[energy].values.tolist()), max_value)

        new_chart = TwoAxesInstanciatedChart(
            'years', 'Prices [$/MWh]', primary_ordinate_axis_range=[0, max_value], chart_name=chart_name)

        for energy in energy_list:
            if self.stream_class_dict[energy].unit == 'TWh':
                techno_price = self.get_sosdisc_inputs(
                    f'{energy}.energy_prices')
                serie = InstanciatedSeries(
                    energy_prices['years'].values.tolist(),
                    techno_price[f'{energy}_wotaxes'].values.tolist(), energy, 'lines')
                new_chart.series.append(serie)

        return new_chart

    def get_chart_energy_price_after_co2_tax_in_dollar_kwh(self):

        energy_prices_after_tax = self.get_sosdisc_outputs(
            'energy_prices_after_tax')

        chart_name = 'Detailed prices of energy mix after carbon taxes due to combustion'

        max_value = 0
        for energy in energy_prices_after_tax:
            if energy != 'years':
                if self.stream_class_dict[energy].unit == 'TWh':
                    max_value = max(
                        max(energy_prices_after_tax[energy].values.tolist()), max_value)

        new_chart = TwoAxesInstanciatedChart(
            'years', 'Prices [$/MWh]', primary_ordinate_axis_range=[0, max_value], chart_name=chart_name)
        for energy in energy_prices_after_tax:
            if energy != 'years':
                if self.stream_class_dict[energy].unit == 'TWh':
                    serie = InstanciatedSeries(
                        energy_prices_after_tax['years'].values.tolist(),
                        energy_prices_after_tax[energy].values.tolist(), energy, 'lines')
                    new_chart.series.append(serie)

        return new_chart

    def get_chart_energy_price_in_dollar_t(self):
        energy_prices = self.get_sosdisc_outputs('energy_prices')

        chart_name = 'Detailed prices of Carbon Capture and Storage'
        new_chart = TwoAxesInstanciatedChart(
            'years', 'Prices [$/t]', chart_name=chart_name)

        ccs_list = self.get_sosdisc_inputs('ccs_list')

        for ccs_name in ccs_list:
            techno_price = self.get_sosdisc_inputs(
                f'{ccs_name}.energy_prices')
            serie = InstanciatedSeries(
                energy_prices['years'].values.tolist(),
                techno_price[ccs_name].values.tolist(), ccs_name, 'lines')
            new_chart.series.append(serie)

        return new_chart

    def get_chart_energy_mean_price_in_dollar_mwh(self):
        energy_mean_price = self.get_sosdisc_outputs('energy_mean_price')

        chart_name = 'Mean price out of energy mix'
        new_chart = TwoAxesInstanciatedChart(
            'years', 'Prices [$/MWh]', chart_name=chart_name)

        serie = InstanciatedSeries(
            energy_mean_price['years'].values.tolist(),
            energy_mean_price['energy_price'].values.tolist(), 'mean energy', 'lines')
        new_chart.series.append(serie)

        return new_chart

    def get_chart_co2_emissions_by_energy(self):
        co2_emissions = self.get_sosdisc_outputs('co2_emissions_by_energy')
        new_chart = TwoAxesInstanciatedChart('years', 'CO2 emissions (Gt)', [], [
        ], 'CO2 emissions by energy (Gt)', stacked_bar=True)
        x_serie_1 = co2_emissions['years'].values.tolist()

        # for idx in co2_emissions.columns:

        for energy in co2_emissions:
            if energy != 'years':

                co2_emissions_array = co2_emissions[energy].values / 1.0e3

                y_serie_1 = co2_emissions_array.tolist()

                serie = InstanciatedSeries(
                    x_serie_1,
                    y_serie_1, energy, display_type='bar')
                new_chart.add_series(serie)

        return new_chart

    def get_chart_energies_net_production(self):
        energy_production_detailed = self.get_sosdisc_outputs(
            'energy_production_detailed')
        chart_name = 'Net Energies production/consumption'
        new_chart = TwoAxesInstanciatedChart('years', 'Net Energy [TWh]',
                                             chart_name=chart_name, stacked_bar=True)

        for reactant in energy_production_detailed.columns:
            if reactant not in ['years', 'Total production', 'Total production (uncut)'] \
                    and 'carbon_capture' not in reactant\
                    and 'carbon_storage' not in reactant:
                energy_twh = energy_production_detailed[reactant].values
                legend_title = f'{reactant}'.replace(
                    "(TWh)", "").replace('production', '')
                serie = InstanciatedSeries(
                    energy_production_detailed['years'].values.tolist(),
                    energy_twh.tolist(), legend_title, 'bar')

                new_chart.series.append(serie)

        return new_chart

    def get_chart_energies_net_production_limit(self):
        energy_production_detailed = self.get_sosdisc_outputs(
            'energy_production_detailed')
        minimum_energy_production = self.get_sosdisc_inputs(
            'minimum_energy_production')
        chart_name = 'Net Energies Total Production and Limit'
        new_chart = TwoAxesInstanciatedChart('years', 'Net Energy [TWh]',
                                             chart_name=chart_name)

        serie = InstanciatedSeries(
            energy_production_detailed['years'].values.tolist(),
            list(
                energy_production_detailed['Total production'].values.tolist()),
            'Total Production', 'lines')
        new_chart.series.append(serie)

        serie = InstanciatedSeries(
            energy_production_detailed['years'].values.tolist(),
            list(
                energy_production_detailed['Total production (uncut)'].values.tolist()),
            'Total Production (uncut)', 'lines')
        new_chart.series.append(serie)

        serie = InstanciatedSeries(
            energy_production_detailed['years'].values.tolist(),
            list([minimum_energy_production for _ in range(
                len(energy_production_detailed['years']))]),
            'min energy', 'lines')
        new_chart.series.append(serie)

        return new_chart

    def get_chart_energies_brut_production(self):
        energy_production_detailed = self.get_sosdisc_outputs(
            'energy_production_brut_detailed')
        chart_name = 'Raw Energies production'
        new_chart = TwoAxesInstanciatedChart('years', 'Raw Energy [TWh]',
                                             chart_name=chart_name, stacked_bar=True)

        for reactant in energy_production_detailed.columns:
            if reactant not in ['years', 'Total production'] \
                    and 'carbon_capture' not in reactant\
                    and 'carbon_storage' not in reactant:
                energy_twh = energy_production_detailed[reactant].values
                legend_title = f'{reactant}'.replace(
                    "(TWh)", "").replace('production', '')
                serie = InstanciatedSeries(
                    energy_production_detailed['years'].values.tolist(),
                    energy_twh.tolist(), legend_title, 'bar')

                new_chart.series.append(serie)

        return new_chart

    def get_pie_charts_production(self, years_list):
        instanciated_charts = []
        energy_list = self.get_sosdisc_inputs('energy_list')
        energy_production_detailed = self.get_sosdisc_outputs(
            'energy_production_detailed')
        techno_production = energy_production_detailed[['years']]

        for energy in energy_list:
            if self.stream_class_dict[energy].unit == 'TWh':
                techno_title = [
                    col for col in energy_production_detailed if col.endswith(f'{energy} (TWh)')]
                techno_production.loc[:,
                                      energy] = energy_production_detailed[techno_title[0]]

        for year in years_list:

            energy_pie_chart = [energy for energy in energy_list if
                                self.stream_class_dict[energy].unit == 'TWh']

            values = [techno_production.loc[techno_production['years']
                                            == year][energy].sum() for energy in energy_pie_chart]
            values = list(np.maximum(0.0, np.array(values)))
            pie_chart = InstanciatedPieChart(
                f'Energy productions in {year}', energy_pie_chart, values)
            instanciated_charts.append(pie_chart)
        return instanciated_charts

    def get_chart_demand_violation_kwh(self):
        chart_name = 'Demand violation chart'
        energy_list = self.get_sosdisc_inputs('energy_list')
        demand_violation = pd.DataFrame()
        new_chart = TwoAxesInstanciatedChart('years', 'Demand violation',
                                             chart_name=chart_name, stacked_bar=True)
        for energy in energy_list:
            if self.stream_class_dict[energy].unit == 'TWh':
                demand_violation_df = self.get_sosdisc_outputs(
                    f'{energy}.demand_violation')
                demand_violation[energy] = demand_violation_df['demand_violation']

                serie = InstanciatedSeries(
                    demand_violation_df['years'].values.tolist(),
                    demand_violation[energy].values.tolist(), f'{energy}', 'bar')
                new_chart.series.append(serie)
        return new_chart

    def get_chart_delta_price(self):
        chart_name = 'Delta price'
        energy_list = self.get_sosdisc_inputs('energy_list')
        new_chart = TwoAxesInstanciatedChart('years', 'Delta price [$/MWh]',
                                             chart_name=chart_name, stacked_bar=True)
        for energy in energy_list:
            if self.stream_class_dict[energy].unit == 'TWh':
                delta_price_df = self.get_sosdisc_outputs(
                    f'{energy}.{EnergyMix.DELTA_ENERGY_PRICES}')

                serie = InstanciatedSeries(
                    delta_price_df['years'].values.tolist(),
                    delta_price_df[energy].values.tolist(), f'{energy}', 'bar')
                new_chart.series.append(serie)
        return new_chart

    def get_chart_co2_streams(self):
        '''
        Plot the total co2 emissions sources - sinks
        '''
        chart_name = 'Total CO2 emissions before and after CCS'
        co2_emissions = self.get_sosdisc_outputs('co2_emissions')
        new_chart = TwoAxesInstanciatedChart('years', 'CO2 emissions (Gt)',
                                             chart_name=chart_name)

        x_serie_1 = co2_emissions['years'].values.tolist()

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
        new_chart = TwoAxesInstanciatedChart('years', 'CO2 emissions (Gt)',
                                             chart_name=chart_name)

        x_serie_1 = co2_emissions['years'].values.tolist()

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'{CarbonCapture.name} (Mt) from CC technos'].values / 1.0e3).tolist(), 'CO2 captured from CC technos')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (-co2_emissions[f'{CarbonCapture.name} needed by energy mix (Mt)'].values / 1.0e3).tolist(), f'{CarbonCapture.name} used by energy mix')
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
        new_chart = TwoAxesInstanciatedChart('years', 'CO2 emissions (Gt)',
                                             chart_name=chart_name)

        x_serie_1 = co2_emissions['years'].values.tolist()
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
            (co2_emissions[f'{CarbonStorage.name} Limited by capture (Mt)'].values / 1.0e3).tolist(), f'CO2 storage limited by CO2 to store')
        new_chart.add_series(serie)

        return new_chart

    def get_chart_co2_emissions_sources(self):
        '''
        Plot all CO2 emissions sources 
        '''
        chart_name = 'CO2 emissions sources'
        co2_emissions = self.get_sosdisc_outputs('co2_emissions')
        new_chart = TwoAxesInstanciatedChart('years', 'CO2 emissions (Gt)',
                                             chart_name=chart_name)

        x_serie_1 = co2_emissions['years'].values.tolist()

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions['Total CO2 by use (Mt)'].values / 1.0e3).tolist(), 'CO2 by use (net production burned)')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'Total {CarbonCapture.flue_gas_name} (Mt)'].values / 1.0e3).tolist(), 'Flue gas from plants')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1, (co2_emissions[f'{CarbonCapture.name} from energy mix (Mt)'].values / 1.0e3).tolist(), 'Carbon capture from energy mix (FT or Sabatier)')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'{CO2.name} from energy mix (Mt)'].values / 1.0e3).tolist(), 'CO2 from energy mix (machinery fuels)')
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
        new_chart = TwoAxesInstanciatedChart('years', 'CO2 emissions (Gt)',
                                             chart_name=chart_name)

        x_serie_1 = co2_emissions['years'].values.tolist()

        serie = InstanciatedSeries(
            x_serie_1, (-co2_emissions[f'{CarbonCapture.name} needed by energy mix (Gt)'].values).tolist(), f'{CarbonCapture.name} needed by energy mix')
        new_chart.add_series(serie)

        return new_chart

    def get_chart_stream_ratio(self):
        '''
        Plot stream ratio chart
        '''
        chart_name = f'Stream Ratio Map'

        all_streams_demand_ratio = self.get_sosdisc_outputs(
            'all_streams_demand_ratio')

        years = all_streams_demand_ratio['years'].values
        streams = [
            col for col in all_streams_demand_ratio.columns if col not in ['years', ]]

        z = np.asarray(all_streams_demand_ratio[streams].values).T
        fig = go.Figure()
        fig.add_trace(go.Heatmap(z=list(z), x=list(years), y=list(streams),
                                 type='heatmap', colorscale=['red', 'white'],
                                 colorbar={'title': 'Value of ratio'},
                                 opacity=0.5, zmax=100.0, zmin=0.0,))
        new_chart = InstantiatedPlotlyNativeChart(
            fig, chart_name=chart_name, default_title=True)
        return new_chart

    def get_chart_stream_consumed_by_techno(self):
        '''
        Plot a table connecting all the streams in the ratio dataframe (left column)
        with the technologies consuming them (right column).
        '''
        chart_name = f'Stream consumption by technologies table'

        all_streams_demand_ratio = self.get_sosdisc_outputs(
            'all_streams_demand_ratio')

        streams = [
            col for col in all_streams_demand_ratio.columns if col not in ['years', ]]

        technologies_list = []
        for stream in streams:
            technologies_list_namespace = self.ee.dm.get_all_namespaces_from_var_name(
                stream + '.technologies_list')[0]
            technologies_list += self.ee.dm.get_data(
                technologies_list_namespace)['value']
        techno_cons_dict = {}
        for techno in technologies_list:
            techno_disc = self.ee.dm.get_disciplines_with_name(self.ee.dm.get_all_namespaces_from_var_name(
                f'{techno}.techno_production')[0][:-len('.techno_production')])[0]
            cons_col = techno_disc.get_sosdisc_outputs(
                'techno_detailed_consumption').columns
            consummed_stream = [col.split(' ')[0]
                                for col in cons_col if col not in ['years']]
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
