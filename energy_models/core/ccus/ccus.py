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

import logging
import re

import numpy as np
import pandas as pd

from energy_models.core.stream_type.base_stream import BaseStream
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.core.stream_type.carbon_models.carbon_storage import CarbonStorage
from energy_models.core.stream_type.energy_models.biodiesel import BioDiesel
from energy_models.core.stream_type.energy_models.biogas import BioGas
from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import GaseousHydrogen
from energy_models.core.stream_type.energy_models.liquid_fuel import LiquidFuel
from energy_models.core.stream_type.energy_models.hydrotreated_oil_fuel import HydrotreatedOilFuel
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.energy_models.solid_fuel import SolidFuel
from energy_models.core.stream_type.energy_models.liquid_hydrogen import LiquidHydrogen
from energy_models.core.stream_type.energy_models.syngas import Syngas,\
    compute_calorific_value
from energy_models.core.stream_type.carbon_models.carbon import Carbon
from energy_models.core.stream_type.energy_models.renewable import Renewable
from energy_models.core.stream_type.energy_models.fossil import Fossil
from copy import deepcopy
from sos_trades_core.tools.base_functions.exp_min import compute_func_with_exp_min
from sos_trades_core.tools.cst_manager.func_manager_common import smooth_maximum


class CCUS(BaseStream):
    """
    Class CCUS
    """
    name = 'CCUS'
    PRODUCTION = 'production'
    DEMAND_VIOLATION = 'demand_violation'
    DELTA_ENERGY_PRICES = 'delta_energy_prices'
    DELTA_CO2_EMISSIONS = 'delta_co2_emissions'
    DEMAND_MAX_PRODUCTION = 'demand_max_production'
    TOTAL_PRODUCTION = 'Total production'
    CO2_TAX_MINUS_CCS_CONSTRAINT_DF = 'CO2_tax_minus_CCS_constraint_df'
    CO2_TAX_MINUS_CCS_CONSTRAINT = 'CO2_tax_minus_CCS_constraint'
    TOTAL_PROD_MINUS_MIN_PROD_CONSTRAINT_DF = 'total_prod_minus_min_prod_constraint_df'
    TOTAL_PROD_MINUS_MIN_PROD_CONSTRAINT = 'total_prod_minus_min_prod_constraint'
    CONSTRAINT_PROD_H2_LIQUID = 'total_prod_h2_liquid'
    CONSTRAINT_PROD_SOLID_FUEL_ELEC = 'total_prod_solid_fuel_elec'
    CONSTRAINT_PROD_HYDROELECTRIC = 'total_prod_hydroelectric'
    CO2_TAX_OBJECTIVE = 'CO2_tax_objective'
    SYNGAS_PROD_OBJECTIVE = 'syngas_prod_objective'
    RESOURCE_LIST = ['natural_gas_resource',
                     'uranium_resource', 'coal_resource', 'oil_resource']
    CARBON_STORAGE_CONSTRAINT = 'carbon_storage_constraint'
    energy_class_dict = {GaseousHydrogen.name: GaseousHydrogen,
                         LiquidFuel.name: LiquidFuel,
                         HydrotreatedOilFuel.name: HydrotreatedOilFuel,
                         Electricity.name: Electricity,
                         Methane.name: Methane,
                         BioGas.name: BioGas,
                         BioDiesel.name: BioDiesel,
                         SolidFuel.name: SolidFuel,
                         Syngas.name: Syngas,
                         BiomassDry.name: BiomassDry,
                         LiquidHydrogen.name: LiquidHydrogen,
                         Renewable.name: Renewable,
                         Fossil.name: Fossil}

    only_energy_list = list(energy_class_dict.keys())

    stream_class_dict = {CarbonCapture.name: CarbonCapture,
                         CarbonStorage.name: CarbonStorage, }
    stream_class_dict.update(energy_class_dict)

    energy_list = list(stream_class_dict.keys())
    resource_list = RESOURCE_LIST
    CO2_list = [f'{CarbonCapture.name} (Mt)',
                f'{CarbonCapture.flue_gas_name} (Mt)',
                f'{CarbonStorage.name} (Mt)',
                f'{CO2.name} (Mt)',
                f'{Carbon.name} (Mt)']
    solidFuel_name = SolidFuel.name
    electricity_name = Electricity.name
    gaseousHydrogen_name = GaseousHydrogen.name
    liquidHydrogen_name = LiquidHydrogen.name
    biomass_name = BiomassDry.name
    syngas_name = Syngas.name

    energy_constraint_list = [solidFuel_name,
                              electricity_name, biomass_name]
    movable_fuel_list = [liquidHydrogen_name,
                         LiquidFuel.name, BioDiesel.name, Methane.name]

    def __init__(self, name):
        '''
        Constructor 
        '''
        super(CCUS, self).__init__(name)

        self.total_co2_emissions = pd.DataFrame()
        self.total_co2_emissions_Gt = None
        self.co2_for_food = None
        self.ratio_available_carbon_capture = None
        self.scaling_factor_energy_production = None
        self.scaling_factor_energy_consumption = None
        self.co2_emissions_needed_by_energy_mix = None
        self.co2_emissions_from_energy_mix = None

    def configure(self, inputs_dict):
        '''
        Configure method 
        '''
        self.configure_parameters(inputs_dict)
        self.configure_parameters_update(inputs_dict)

    def configure_parameters(self, inputs_dict):
        '''
        COnfigure parameters (variables that does not change during the run
        '''
        self.subelements_list = inputs_dict['ccs_list']
        BaseStream.configure_parameters(self, inputs_dict)

        self.co2_for_food = inputs_dict['co2_for_food']
        self.CCS_price = pd.DataFrame(
            {'years': np.arange(inputs_dict['year_start'], inputs_dict['year_end'] + 1)})
        self.carbonstorage_limit = inputs_dict['carbonstorage_limit']
        self.carbonstorage_constraint_ref = inputs_dict['carbonstorage_constraint_ref']
        self.ratio_norm_value = inputs_dict['ratio_ref']

    def configure_parameters_update(self, inputs_dict):
        '''
        COnfigure parameters with possible update (variables that does change during the run)
        '''
        self.subelements_list = inputs_dict['ccs_list']

        # Specific configure for energy mix
        self.scaling_factor_energy_production = inputs_dict['scaling_factor_energy_production']
        self.scaling_factor_energy_consumption = inputs_dict['scaling_factor_energy_consumption']
        for energy in self.subelements_list:
            self.sub_prices[energy] = inputs_dict[f'{energy}.energy_prices'][energy]
            self.sub_production_dict[energy] = inputs_dict[f'{energy}.energy_production'] * \
                self.scaling_factor_energy_production
            self.sub_consumption_dict[energy] = inputs_dict[f'{energy}.energy_consumption'] * \
                self.scaling_factor_energy_consumption
            self.sub_consumption_woratio_dict[energy] = inputs_dict[f'{energy}.energy_consumption_woratio'] * \
                self.scaling_factor_energy_consumption

        self.energy_prices = self.sub_prices.copy(deep=True)

        # dataframe resource demand
        self.all_resource_demand = pd.DataFrame(
            {'years': self.energy_prices['years'].values})
        for elements in self.resource_list:
            if elements in self.resource_list:
                self.all_resource_demand[elements] = np.linspace(
                    0, 0, len(self.all_resource_demand.index)) * 100.
        for energy in self.subelements_list:
            for elements in self.sub_consumption_dict[energy]:
                if elements in self.resource_list:
                    self.all_resource_demand[elements] = self.all_resource_demand[elements] + \
                        inputs_dict[f'{energy}.energy_consumption'][elements].values * \
                        self.scaling_factor_energy_consumption

        # DataFrame stream demand
        self.all_streams_demand_ratio = pd.DataFrame(
            {'years': self.energy_prices['years'].values})
        for energy in self.subelements_list:
            self.all_streams_demand_ratio[energy] = np.ones(
                len(self.all_streams_demand_ratio['years'].values)) * 100.

        # initialize ratio available carbon capture
        self.ratio_available_carbon_capture = pd.DataFrame({'years': np.arange(inputs_dict['year_start'], inputs_dict['year_end'] + 1),
                                                            f'ratio': 1.0})
        self.co2_for_food = inputs_dict['co2_for_food']
        self.co2_emissions_needed_by_energy_mix = inputs_dict['co2_emissions_needed_by_energy_mix']
        self.co2_emissions_from_energy_mix = inputs_dict['co2_emissions_from_energy_mix']
        #self.co2_emissions = inputs_dict['co2_emissions']

    def compute_CO2_emissions(self):
        '''
        Compute CO2 total emissions
        '''
        # Initialize dataframes

        self.co2_production = pd.DataFrame({'years': self.production['years']})
        self.co2_consumption = pd.DataFrame(
            {'years': self.production['years']})
        self.emissions_by_energy = pd.DataFrame(
            {'years': self.production['years']})
        # Do not loop over carbon capture and carbon storage which will be
        # handled differently

        ''' CARBON STORAGE 
         Total carbon storage is production of carbon storage
         Solid carbon is gaseous equivalent in the production for
         solidcarbonstorage technology
        '''
        if CarbonStorage.name in self.sub_production_dict:

            self.total_co2_emissions[f'{CarbonStorage.name} (Mt)'] = self.sub_production_dict[
                CarbonStorage.name][CarbonStorage.name].values
        else:
            self.total_co2_emissions[f'{CarbonStorage.name} (Mt)'] = 0.0

        ''' CARBON CAPTURE from CC technos       
         Total carbon capture = carbon captured from carboncapture stream +
         carbon captured from energies (can be negative if FischerTropsch needs carbon
         captured)
        '''
        if CarbonCapture.name in self.sub_production_dict:

            self.total_co2_emissions[f'{CarbonCapture.name} (Mt) from CC technos'] = self.sub_production_dict[
                CarbonCapture.name][CarbonCapture.name].values
        else:
            self.total_co2_emissions[f'{CarbonCapture.name} (Mt) from CC technos'] = 0.0

        ''' Carbon captured that needs to be stored
            sum of the one from CC technos and the one directly captured 
            we delete the one needed by energy mix and potentially later the CO2 for food
        '''

        self.total_co2_emissions[f'{CarbonCapture.name} to be stored (Mt)'] = self.total_co2_emissions[f'{CarbonCapture.name} (Mt) from CC technos'] + \
            self.co2_emissions_from_energy_mix[f'{CarbonCapture.name} from energy mix (Mt)'] - \
            self.co2_emissions_needed_by_energy_mix[f'{CarbonCapture.name} needed by energy mix (Mt)'] -\
            self.co2_for_food[f'{CO2.name} for food (Mt)']

        cc_to_be_stored = self.total_co2_emissions[
            f'{CarbonCapture.name} to be stored (Mt)'].values
        # if the carbon to be stored is lower than zero that means that we need
        # more carbon capture for energy mix than the one created by CC technos
        # or upgrading biogas
        if cc_to_be_stored.min() < 0:
            cc_needed = self.co2_emissions_needed_by_energy_mix[
                f'{CarbonCapture.name} needed by energy mix (Mt)'].values
            # if cc_needed is lower than 1.0e-15 we put one to the ratio (do
            # not care about small needs lower than 1.0e-15)
            if cc_to_be_stored.dtype != cc_needed.dtype:
                cc_needed = cc_needed.astype(cc_to_be_stored.dtype)
            self.ratio_available_carbon_capture['ratio'] = np.divide(cc_to_be_stored + cc_needed, cc_needed,
                                                                     out=np.ones_like(cc_needed), where=cc_needed > 1.0e-15)

        # Waiting for production ratio effect we clip the prod
        carbon_to_be_stored = self.total_co2_emissions[
            f'{CarbonCapture.name} to be stored (Mt)'].values
        carbon_to_be_stored[carbon_to_be_stored.real < 0.0] = 0.0
        self.total_co2_emissions[f'{CarbonCapture.name} to be stored (Mt)'] = carbon_to_be_stored

        '''
            Solid Carbon to be stored to limit the carbon solid storage
        '''
        energy_producing_solid_carbon = self.co2_production[[
            col for col in self.co2_production if col.endswith(f'{Carbon.name} (Mt)')]]
        energy_producing_solid_carbon_list = [key.replace(
            f' {Carbon.name} (Mt)', '') for key in energy_producing_solid_carbon]
        if len(energy_producing_solid_carbon_list) != 0:
            self.total_co2_emissions[f'{Carbon.name} to be stored (Mt)'] = energy_producing_solid_carbon.sum(
                axis=1).values
        else:
            self.total_co2_emissions[
                f'{Carbon.name} to be stored (Mt)'] = 0.0

        '''
            Solid Carbon storage 
        '''
        self.total_co2_emissions[f'Solid {Carbon.name} storage (Mt)'] = 0.0
        if CarbonStorage.name in self.sub_consumption_dict:
            if f'{Carbon.name} (Mt)' in self.sub_consumption_dict[CarbonStorage.name]:
                self.total_co2_emissions[f'Solid {Carbon.name} storage (Mt)'] = self.sub_consumption_dict[
                    CarbonStorage.name][f'{Carbon.name} (Mt)'].values

        '''
            The carbon stored by invest is limited by the carbon previously captured to be stored
            for gaseous and solid carbon storage
            Solid carbon storage is taken into account into carbon storage 
            need to delete it before using the minimum
        '''

        self.total_co2_emissions[f'{CarbonStorage.name} Limited by capture (Mt)'] = np.minimum(
            self.total_co2_emissions[f'{CarbonCapture.name} to be stored (Mt)'].values,
            self.total_co2_emissions[f'{CarbonStorage.name} (Mt)'].values - self.total_co2_emissions[f'Solid {Carbon.name} storage (Mt)'].values * Carbon.data_energy_dict['CO2_per_use']) + \
            np.minimum(
            self.total_co2_emissions[f'{Carbon.name} to be stored (Mt)'].values,
            self.total_co2_emissions[f'Solid {Carbon.name} storage (Mt)'].values) * Carbon.data_energy_dict['CO2_per_use']

        self.total_co2_emissions_Gt = pd.DataFrame(
            {'years': self.production['years'],
             f'{CarbonStorage.name} Limited by capture (Mt)': self.total_co2_emissions[f'{CarbonStorage.name} Limited by capture (Mt)'].values / 1e3})

    def compute_CCS_price(self):
        '''
        Compute CCS_price 
        '''
        self.CCS_price['ccs_price_per_tCO2'] = 0.
        if CarbonCapture.name in self.sub_prices:
            self.CCS_price['ccs_price_per_tCO2'] += self.energy_prices[CarbonCapture.name]
        if CarbonStorage.name in self.sub_prices:
            self.CCS_price['ccs_price_per_tCO2'] += self.sub_prices[CarbonStorage.name]

    def compute_carbon_storage_constraint(self):
        '''
        Compute carbon storage constraint
        '''

        self.carbon_storage_constraint = np.array([- (self.total_co2_emissions[f'{CarbonStorage.name} Limited by capture (Mt)'].sum(
        ) - self.carbonstorage_limit) / self.carbonstorage_constraint_ref])

    def compute_ratio_objective(self):

        ratio_arrays = self.all_streams_demand_ratio[self.subelements_list].values
        # Objective is to minimize the difference between 100 and all ratios
        # We give as objective the highest difference to start with the max of
        # the difference

        smooth_max = smooth_maximum(100.0 - ratio_arrays.flatten(), 3)
        self.ratio_objective = np.asarray(
            [smooth_max / self.ratio_norm_value])

    def compute_all_streams_demand_ratio(self):
        '''! Computes the demand_ratio dataframe. 
        The ratio is calculated using the production and consumption WITHOUT the ratio applied
        The value of the ratio is capped to 100.0
        '''
        demand_ratio_df = pd.DataFrame(
            {'years': self.years})

        for energy in self.subelements_list:

            # Prod with ratio
            energy_production = deepcopy(
                self.sub_production_dict[f'{energy}'][f'{energy}'].values)
            # consumption without ratio
            sub_cons = self.sub_consumption_woratio_dict

            energy_consumption = np.zeros(len(self.years))
            for idx, consu in sub_cons.items():
                if f'{energy} ({self.stream_class_dict[energy].unit})' in consu.columns:
                    energy_consumption = np.sum([energy_consumption, consu[
                        f'{energy} ({self.stream_class_dict[energy].unit})'].values], axis=0)
            energy_prod_limited = compute_func_with_exp_min(
                energy_production, 1.0e-10)
            energy_cons_limited = compute_func_with_exp_min(
                energy_consumption, 1.0e-10)

            demand_ratio_df[f'{energy}'] = np.minimum(
                energy_prod_limited / energy_cons_limited, 1.0) * 100.0
        self.all_streams_demand_ratio = demand_ratio_df

        # COmpute ratio_objective
        self.compute_ratio_objective()

    def compute_grad_CO2_emissions(self, co2_emissions, alpha):
        '''
        Compute CO2 total emissions
        '''
        # Initialize dataframes
        len_years = len(self.production['years'])

        co2_production = pd.DataFrame({'years': self.production['years']})
        co2_consumption = pd.DataFrame(
            {'years': self.production['years']})

        dtot_CO2_emissions = {}
        # Do not loop over carbon capture and carbon storage which will be
        # handled differently

        ''' CARBON STORAGE 
         Total carbon storage is production of carbon storage
         Solid carbon is gaseous equivalent in the production for
         solidcarbonstorage technology
        '''
        if CarbonStorage.name in self.sub_production_dict:
            dtot_CO2_emissions[f'{CarbonStorage.name} (Mt) vs {CarbonStorage.name}#{CarbonStorage.name}#prod'] = np.ones(
                len_years)
#             self.total_co2_emissions[f'{CarbonStorage.name} (Mt)'] = self.sub_production_dict[
#                 CarbonStorage.name][CarbonStorage.name].values
#         else:
#             self.total_co2_emissions[f'{CarbonStorage.name} (Mt)'] = 0.0

        ''' CARBON CAPTURE from CC technos       
         Total carbon capture = carbon captured from carboncapture stream +
         carbon captured from energies (can be negative if FischerTropsch needs carbon
         captured)
        '''
        if CarbonCapture.name in self.sub_production_dict:
            dtot_CO2_emissions[f'{CarbonCapture.name} (Mt) from CC technos vs {CarbonCapture.name}#{CarbonCapture.name}#prod'] = np.ones(
                len_years)
#             self.total_co2_emissions[f'{CarbonCapture.name} (Mt) from CC technos'] = self.sub_production_dict[
#                 CarbonCapture.name][CarbonCapture.name].values
#         else:
#             self.total_co2_emissions[f'{CarbonCapture.name} (Mt) from CC technos'] = 0.0

        ''' CARBON CAPTURE from energy mix
        Total carbon capture from energy mix if the technology offers carbon_capture
         Ex : upgrading biogas technology is the same as Amine Scrubbing but
         on a different gas (biogas for upgrading biogas and flue gas for
         Amien scrubbing)
        '''
        energy_producing_carbon_capture = co2_production[[
            col for col in co2_production if col.endswith(f'{CarbonCapture.name} (Mt)')]]
        energy_producing_carbon_capture_list = [key.replace(
            f' {CarbonCapture.name} (Mt)', '') for key in energy_producing_carbon_capture]
        if len(energy_producing_carbon_capture_list) != 0:
            for energy1 in energy_producing_carbon_capture_list:
                dtot_CO2_emissions[
                    f'{CarbonCapture.name} from energy mix (Mt) vs {energy1}#{CarbonCapture.name} (Mt)#prod'] = np.ones(len_years)
#             self.total_co2_emissions[f'{CarbonCapture.name} from energy mix (Mt)'] = energy_producing_carbon_capture.sum(
#                 axis=1).values
#         else:
#             self.total_co2_emissions[
#                 f'{CarbonCapture.name} from energy mix (Mt)'] = 0.0

        ''' CARBON CAPTURE needed by energy mix
        Total carbon capture needed by energy mix if a technology needs carbon_capture
         Ex :Sabatier process or RWGS in FischerTropsch technology 
        '''
        energy_needing_carbon_capture = co2_consumption[[
            col for col in co2_consumption if col.endswith(f'{CarbonCapture.name} (Mt)')]]
        energy_needing_carbon_capture_list = [key.replace(
            f' {CarbonCapture.name} (Mt)', '') for key in energy_needing_carbon_capture]
        if len(energy_needing_carbon_capture_list) != 0:
            for energy1 in energy_needing_carbon_capture_list:
                dtot_CO2_emissions[
                    f'{CarbonCapture.name} needed by energy mix (Mt) vs {energy1}#{CarbonCapture.name} (Mt)#cons'] = np.ones(len_years)
#             self.total_co2_emissions[f'{CarbonCapture.name} needed by energy mix (Mt)'] = energy_needing_carbon_capture.sum(
#                 axis=1).values
#         else:
#             self.total_co2_emissions[
#                 f'{CarbonCapture.name} needed by energy mix (Mt)'] = 0.0

        ''' CO2 from energy mix       
         CO2 expelled by energy mix technologies during the process 
         i.e. for machinery or tractors 
        '''
        energy_producing_co2 = co2_production[[
            col for col in co2_production if col.endswith(f'{CO2.name} (Mt)')]]
        energy_producing_co2_list = [key.replace(
            f' {CO2.name} (Mt)', '') for key in energy_producing_co2]
        if len(energy_producing_co2_list) != 0:
            for energy1 in energy_producing_co2_list:
                dtot_CO2_emissions[
                    f'{CO2.name} from energy mix (Mt) vs {energy1}#{CO2.name} (Mt)#prod'] = np.ones(len_years)

#             self.total_co2_emissions[f'{CO2.name} from energy mix (Mt)'] = energy_producing_co2.sum(
#                 axis=1).values
#         else:
#             self.total_co2_emissions[
#                 f'{CO2.name} from energy mix (Mt)'] = 0.0

        ''' CO2 removed by energy mix       
         CO2 removed by energy mix technologies during the process 
         i.e. biomass processes as managed wood or crop energy
        '''
        energy_removing_co2 = co2_consumption[[
            col for col in co2_consumption if col.endswith(f'{CO2.name} (Mt)')]]
        energy_removing_co2_list = [key.replace(
            f' {CO2.name} (Mt)', '') for key in energy_removing_co2]
        if len(energy_removing_co2_list) != 0:
            for energy1 in energy_removing_co2_list:
                dtot_CO2_emissions[
                    f'{CO2.name} removed by energy mix (Mt) vs {energy1}#{CO2.name} (Mt)#cons'] = np.ones(len_years)
#             self.total_co2_emissions[f'{CO2.name} removed by energy mix (Mt)'] = energy_removing_co2.sum(
#                 axis=1).values
#         else:
#             self.total_co2_emissions[
#                 f'{CO2.name} removed energy mix (Mt)'] = 0.0

        ''' Total C02 from Flue gas
            sum of all production of flue gas 
            it could be equal to carbon capture from CC technos if enough investment but not sure
        '''
#         self.total_co2_emissions[f'Total {CarbonCapture.flue_gas_name} (Mt)'] = self.co2_production[[
# col for col in self.co2_production if
# col.endswith(f'{CarbonCapture.flue_gas_name} (Mt)')]].sum(axis=1)
        for col in co2_production:
            if col.endswith(f'{CarbonCapture.flue_gas_name} (Mt)'):
                energy1 = col.replace(
                    f' {CarbonCapture.flue_gas_name} (Mt)', '')
                dtot_CO2_emissions[f'Total {CarbonCapture.flue_gas_name} (Mt) vs {energy1}#{CarbonCapture.flue_gas_name} (Mt)#prod'] = np.ones(
                    len_years)
        ''' Carbon captured that needs to be stored
            sum of the one from CC technos and the one directly captured 
            we delete the one needed by energy mix and potentially later the CO2 for food
        '''

#         self.total_co2_emissions[f'{CarbonCapture.name} to be stored (Mt)'] = self.total_co2_emissions[f'{CarbonCapture.name} (Mt) from CC technos'] + \
#             self.total_co2_emissions[f'{CarbonCapture.name} from energy mix (Mt)'] - \
#             self.total_co2_emissions[f'{CarbonCapture.name} needed by energy mix (Mt)'] -\
#             self.total_co2_emissions[f'{CO2.name} for food (Mt)'

        new_key = f'{CarbonCapture.name} to be stored (Mt)'
        dtot_CO2_emissions[f'{new_key} vs {CO2.name} for food (Mt)#carbon_capture'] = - np.ones(
            len_years)
        dtot_CO2_emissions[f'{new_key} vs {CarbonCapture.name} from energy mix (Mt)#carbon_capture'] = np.ones(
            len_years)
        dtot_CO2_emissions[f'{new_key} vs {CarbonCapture.name} needed by energy mix (Mt)#carbon_capture'] = - np.ones(
            len_years)
        key_dep_tuple_list = [(f'{CarbonCapture.name} (Mt) from CC technos', 1.0),
                              (f'{CarbonCapture.name} from energy mix (Mt)', 1.0),
                              (f'{CarbonCapture.name} needed by energy mix (Mt)', -1.0),
                              (f'{CO2.name} for food (Mt)', -1.0)]
        dtot_CO2_emissions = update_new_gradient(
            dtot_CO2_emissions, key_dep_tuple_list, new_key)

        cc_to_be_stored = co2_emissions[f'{CarbonCapture.name} (Mt) from CC technos'].values + \
            self.co2_emissions_from_energy_mix[f'{CarbonCapture.name} from energy mix (Mt)'].values - \
            self.co2_emissions_needed_by_energy_mix[f'{CarbonCapture.name} needed by energy mix (Mt)'].values -\
            self.co2_for_food[f'{CO2.name} for food (Mt)'].values
        # if the carbon to be stored is lower than zero that means that we need
        # more carbon capture for energy mix than the one created by CC technos
        # or upgrading biogas
        if cc_to_be_stored.min() < 0:
            cc_needed = self.co2_emissions_needed_by_energy_mix[
                f'{CarbonCapture.name} needed by energy mix (Mt)'].values
            cc_provided = co2_emissions[f'{CarbonCapture.name} (Mt) from CC technos'].values + \
                self.co2_emissions_from_energy_mix[
                    f'{CarbonCapture.name} from energy mix (Mt)'].values
            dtot_CO2_emissions_old = dtot_CO2_emissions.copy()
            dratio_dkey = {}
            # The gradient is (u/v)' = (u'v -uv')/v**2 = u'/v -uv'/v**2
            # u is the cc needed f'{CarbonCapture.name} needed by energy mix (Mt)'
            # v is the cc provided which is the sum of f'{CarbonCapture.name}
            # (Mt) from CC technos' and f'{CarbonCapture.name} from energy mix
            # (Mt)'

            for key, grad_cc in dtot_CO2_emissions_old.items():
                key_co2_emissions = key.split(' vs ')[0]
                grad_info_x = key.split(' vs ')[1]
                if key_co2_emissions == f'{CarbonCapture.name} needed by energy mix (Mt)':

                    if grad_info_x in dratio_dkey:
                        dratio_dkey[grad_info_x] -= np.divide(cc_provided * grad_cc, cc_needed**2,
                                                              out=np.zeros_like(cc_needed), where=cc_needed > 1.0e-15)
                    else:
                        dratio_dkey[grad_info_x] = - np.divide(cc_provided * grad_cc, cc_needed**2,
                                                               out=np.zeros_like(cc_needed), where=cc_needed > 1.0e-15)

                elif key_co2_emissions in [f'{CarbonCapture.name} (Mt) from CC technos',
                                           f'{CarbonCapture.name} from energy mix (Mt)']:

                    if grad_info_x in dratio_dkey:
                        dratio_dkey[grad_info_x] += np.divide(grad_cc, cc_needed,
                                                              out=np.zeros_like(cc_needed), where=cc_needed > 1.0e-15)
                    else:
                        dratio_dkey[grad_info_x] = np.divide(grad_cc, cc_needed,
                                                             out=np.zeros_like(cc_needed), where=cc_needed > 1.0e-15)
            # finally we can fill the dtotco2_emissions with the u'v-uv'/v**2
            for key, grad in dratio_dkey.items():
                key_dratio = f'ratio_available_carbon_capture vs {key}'
                dtot_CO2_emissions[key_dratio] = grad
#             self.ratio_available_carbon_capture['ratio'] = np.divide(cc_to_be_stored + cc_needed, cc_needed,
# out=np.zeros_like(cc_needed), where=cc_needed > 1.0e-15)

        grad_max = np.maximum(0.0, np.sign(
            cc_to_be_stored))

        for key, value in dtot_CO2_emissions.items():
            if key.startswith(f'{CarbonCapture.name} to be stored (Mt)'):
                value *= grad_max
#         co2_emissions[f'{CarbonCapture.name} to be stored (Mt)'] = np.maximum(
# co2_emissions[f'{CarbonCapture.name} to be stored (Mt)'],
# 0.0)

        '''
            Solid Carbon to be stored to limit the carbon solid storage
        '''
#         energy_producing_solid_carbon = self.co2_production[[
#             col for col in self.co2_production if col.endswith(f'{Carbon.name} (Mt)')]]
#         energy_producing_solid_carbon_list = [key.replace(
#             f' {Carbon.name} (Mt)', '') for key in energy_producing_solid_carbon]
#         if len(energy_producing_solid_carbon_list) != 0:
#             co2_emissions[f'{Carbon.name} to be stored (Mt)'] = energy_producing_solid_carbon.sum(
#                 axis=1).values
#         else:
#             co2_emissions[
#                 f'{Carbon.name} to be stored (Mt)'] = 0.0

        for col in co2_production:
            if col.endswith(f'{Carbon.name} (Mt)'):
                energy1 = col.replace(f' {Carbon.name} (Mt)', '')
                dtot_CO2_emissions[f'{Carbon.name} to be stored (Mt) vs {energy1}#{Carbon.name} (Mt)#prod'] = np.ones(
                    len_years)
        '''
            Solid Carbon storage 
        '''

        if CarbonStorage.name in self.sub_consumption_dict:
            if f'{Carbon.name} (Mt)' in self.sub_consumption_dict[CarbonStorage.name]:
                dtot_CO2_emissions[f'Solid {Carbon.name} storage (Mt) vs {CarbonStorage.name}#{Carbon.name} (Mt)#cons'] = np.ones(
                    len_years)
#                 co2_emissions[f'Solid {Carbon.name} storage (Mt)'] = self.sub_consumption_dict[
#                     CarbonStorage.name][f'{Carbon.name} (Mt)'].values

        '''
            The carbon stored by invest is limited by the carbon previously captured to be stored
            for gaseous and solid carbon storage
            Solid carbon storage is taken into account into carbon storage 
            need to delete it before using the minimum
        '''
        # if abs (min(a,b)-a) = 0.0 then the minimum is a else the minimum is b
        # and the sign of abs (min(a,b)-a) is one
        mini1 = np.minimum(
            co2_emissions[f'{CarbonCapture.name} to be stored (Mt)'].values,
            co2_emissions[f'{CarbonStorage.name} (Mt)'].values - co2_emissions[f'Solid {Carbon.name} storage (Mt)'].values * Carbon.data_energy_dict['CO2_per_use'])
        limit_is_storage = np.maximum(0.0, np.sign(np.abs(
            mini1 - co2_emissions[f'{CarbonCapture.name} to be stored (Mt)'].values)))
        limit_is_to_be_stored = np.ones(len_years) - limit_is_storage

        # if abs (min(a,b)-a) = 0.0 then the minimum is a else the minimum is b
        # and the sign of abs (min(a,b)-a) is one
        mini2 = np.minimum(
            co2_emissions[f'{Carbon.name} to be stored (Mt)'].values,
            co2_emissions[f'Solid {Carbon.name} storage (Mt)'].values) * Carbon.data_energy_dict['CO2_per_use']

        limit_is_solid_storage = np.maximum(0.0, np.sign(np.abs(
            mini2 - co2_emissions[f'{Carbon.name} to be stored (Mt)'].values * Carbon.data_energy_dict['CO2_per_use'])))
        limit_is_solid_to_be_stored = np.ones(
            len_years) - limit_is_solid_storage
        new_key = f'{CarbonStorage.name} Limited by capture (Mt)'
        key_dep_tuple_list = [(f'{CarbonCapture.name} to be stored (Mt)', limit_is_to_be_stored),
                              (f'{Carbon.name} to be stored (Mt)',
                               limit_is_solid_to_be_stored * Carbon.data_energy_dict['CO2_per_use']),
                              (f'{CarbonStorage.name} (Mt)', limit_is_storage),
                              (f'Solid {Carbon.name} storage (Mt)', (-limit_is_storage + limit_is_solid_storage) * Carbon.data_energy_dict['CO2_per_use'])]
        dtot_CO2_emissions = update_new_gradient(
            dtot_CO2_emissions, key_dep_tuple_list, new_key)


#         self.total_co2_emissions[f'{CarbonStorage.name} Limited by capture (Mt)'] = np.minimum(
#             self.total_co2_emissions[f'{CarbonCapture.name} to be stored (Mt)'].values,
#             self.total_co2_emissions[f'{CarbonStorage.name} (Mt)'].values - self.total_co2_emissions[f'Solid {Carbon.name} storage (Mt)'].values * Carbon.data_energy_dict['CO2_per_use']) + \
#             np.minimum(
#             self.total_co2_emissions[f'{Carbon.name} to be stored (Mt)'].values,
# self.total_co2_emissions[f'Solid {Carbon.name} storage (Mt)'].values) *
# Carbon.data_energy_dict['CO2_per_use']

        '''  CO2 EMISSIONS SINKS
        Only carbon stored or used or removed is deduced from total CO2 emissions
        '''

        new_key = 'CO2 emissions sinks'
        key_dep_tuple_list = [(f'{CarbonStorage.name} Limited by capture (Mt)', 1.0),
                              (f'{CO2.name} removed by energy mix (Mt)', 1.0),
                              (f'{CarbonCapture.name} needed by energy mix (Mt)', 1.0)]
        dtot_CO2_emissions = update_new_gradient(
            dtot_CO2_emissions, key_dep_tuple_list, new_key)

#         self.total_co2_emissions['CO2 emissions sinks'] = self.total_co2_emissions[f'{CarbonStorage.name} Limited by capture (Mt)'] + \
#             self.total_co2_emissions[f'{CO2.name} removed by energy mix (Mt)'] + \
#             self.total_co2_emissions[f'{CarbonCapture.name} needed by energy mix (Mt)']

        '''  CO2 EMISSIONS SOURCES
        All sources of carbon emissions by energy including : 
            - the flue gas from technos
            - the carbon captured from technos (maybe not stored)
            - the carbon emitted by the energy mix (cannot be stored)
            - the carbon emitted after use of net production
            
        '''
        new_key = 'CO2 emissions sources'
        key_dep_tuple_list = [(f'Total {CarbonCapture.flue_gas_name} (Mt)', 1.0),
                              (f'{CarbonCapture.name} from energy mix (Mt)', 1.0),
                              (f'{CO2.name} from energy mix (Mt)', 1.0),
                              (f'Total CO2 by use (Mt)', 1.0)]
        dtot_CO2_emissions = update_new_gradient(
            dtot_CO2_emissions, key_dep_tuple_list, new_key)

#         self.total_co2_emissions['CO2 emissions sources'] =  \
#             self.total_co2_emissions[f'Total {CarbonCapture.flue_gas_name} (Mt)'] + \
#             self.total_co2_emissions[f'{CarbonCapture.name} from energy mix (Mt)'] + \
#             self.total_co2_emissions[f'{CO2.name} from energy mix (Mt)'] + \
#             self.total_co2_emissions[f'Total CO2 by use (Mt)']

        # Total is sources minus sinks
#         self.total_co2_emissions['Total CO2 emissions'] = self.total_co2_emissions['CO2 emissions sources'] - \
#             self.total_co2_emissions['CO2 emissions sinks']

        dtot_final_CO2_emissions = dtot_CO2_emissions.copy()
        for key, gradient in dtot_CO2_emissions.items():

            if key.startswith(f'{CarbonStorage.name} Limited by capture (Mt)'):
                new_key = key.replace(
                    f'{CarbonStorage.name} Limited by capture (Mt)', 'Carbon storage constraint')
                dtot_final_CO2_emissions[new_key] = - \
                    gradient / self.carbonstorage_constraint_ref

        return dtot_final_CO2_emissions


def update_new_gradient(grad_dict, key_dep_tuple_list, new_key):
    '''
        Update new gradient which are dependent of old ones by simple sum or difference
    '''
    new_grad_dict = grad_dict.copy()
    for key in grad_dict:
        for old_key, factor in key_dep_tuple_list:
            if key.startswith(old_key):
                    # the grad of old key is equivalent to the new key because its
                    # a sum
                new_grad_key = key.replace(old_key, new_key)
                if new_grad_key in new_grad_dict:
                    new_grad_dict[new_grad_key] = new_grad_dict[new_grad_key] + \
                        grad_dict[key] * factor
                else:
                    new_grad_dict[new_grad_key] = grad_dict[key] * factor

    return new_grad_dict