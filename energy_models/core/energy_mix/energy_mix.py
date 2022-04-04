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
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary


class EnergyMix(BaseStream):
    """
    Class Energy mix
    """
    name = 'EnergyMix'
    PRODUCTION = 'production'
    TOTAL_PRODUCTION = 'Total production'
    CO2_TAX_MINUS_CCS_CONSTRAINT_DF = 'CO2_tax_minus_CCS_constraint_df'
    TOTAL_PROD_MINUS_MIN_PROD_CONSTRAINT_DF = 'total_prod_minus_min_prod_constraint_df'
    TOTAL_PROD_MINUS_MIN_PROD_CONSTRAINT = 'total_prod_minus_min_prod_constraint'
    CONSTRAINT_PROD_H2_LIQUID = 'total_prod_h2_liquid'
    CONSTRAINT_PROD_SOLID_FUEL_ELEC = 'total_prod_solid_fuel_elec'
    CONSTRAINT_PROD_HYDROELECTRIC = 'total_prod_hydroelectric'
    CO2_TAX_OBJECTIVE = 'CO2_tax_objective'
    SYNGAS_PROD_OBJECTIVE = 'syngas_prod_objective'
    RESOURCE_LIST = ['natural_gas_resource',
                     'uranium_resource', 'coal_resource', 'oil_resource']
    RESOURCE_CONSUMPTION_UNIT = ResourceGlossary.UNITS['consumption']
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
        super(EnergyMix, self).__init__(name)

        self.total_co2_emissions = None
        self.total_co2_emissions_Gt = None
        self.co2_for_food = None
        self.losses_percentage_dict = {}

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
        self.subelements_list = inputs_dict['energy_list']
        BaseStream.configure_parameters(self, inputs_dict)

        # Specific configure for energy mix
        self.co2_per_use = {}
        self.CCS_price = pd.DataFrame(
            {'years': np.arange(inputs_dict['year_start'], inputs_dict['year_end'] + 1)})
        self.CO2_tax_minus_CCS_constraint = pd.DataFrame(
            {'years': np.arange(inputs_dict['year_start'], inputs_dict['year_end'] + 1)})
        self.total_prod_minus_min_prod_constraint_df = pd.DataFrame(
            {'years': np.arange(inputs_dict['year_start'], inputs_dict['year_end'] + 1)})
        self.minimum_energy_production = inputs_dict['minimum_energy_production']
        self.production_threshold = inputs_dict['production_threshold']
        self.scaling_factor_energy_production = inputs_dict['scaling_factor_energy_production']
        self.scaling_factor_energy_consumption = inputs_dict['scaling_factor_energy_consumption']
        self.solid_fuel_elec_percentage = inputs_dict['solid_fuel_elec_percentage']
        self.solid_fuel_elec_constraint_ref = inputs_dict['solid_fuel_elec_constraint_ref']
        self.liquid_hydrogen_percentage = inputs_dict['liquid_hydrogen_percentage']
        self.liquid_hydrogen_constraint_ref = inputs_dict['liquid_hydrogen_constraint_ref']
        self.syngas_prod_ref = inputs_dict['syngas_prod_ref']
        self.co2_for_food = pd.DataFrame({'years': np.arange(inputs_dict['year_start'], inputs_dict['year_end'] + 1),
                                          f'{CO2.name} for food (Mt)': 0.0})
        self.ratio_norm_value = inputs_dict['ratio_ref']

        self.heat_losses_percentage = inputs_dict['heat_losses_percentage']

        if self.subelements_list is not None:
            for energy in self.subelements_list:
                if f'{energy}.losses_percentage' in inputs_dict:
                    self.losses_percentage_dict[energy] = inputs_dict[f'{energy}.losses_percentage']

    def configure_parameters_update(self, inputs_dict):
        '''
        COnfigure parameters with possible update (variables that does change during the run)
        '''
        self.scaling_factor_energy_production = inputs_dict['scaling_factor_energy_production']
        self.scaling_factor_energy_consumption = inputs_dict['scaling_factor_energy_consumption']
        self.carbon_tax = inputs_dict['CO2_taxes']
        self.subelements_list = inputs_dict['energy_list'] + \
            inputs_dict['ccs_list']
        self.subelements_list_energy = inputs_dict['energy_list']
        self.total_prod_minus_min_prod_constraint_ref = inputs_dict[
            'total_prod_minus_min_prod_constraint_ref']
        # Specific configure for energy mix
        self.co2_per_use = {}
        self.data_fuel_dict = {}

        for energy in self.subelements_list:
            self.sub_prices[energy] = inputs_dict[f'{energy}.energy_prices'][energy]
            self.sub_production_dict[energy] = inputs_dict[f'{energy}.energy_production'] * \
                self.scaling_factor_energy_production
            self.sub_consumption_dict[energy] = inputs_dict[f'{energy}.energy_consumption'] * \
                self.scaling_factor_energy_consumption
            self.sub_consumption_woratio_dict[energy] = inputs_dict[f'{energy}.energy_consumption_woratio'] * \
                self.scaling_factor_energy_consumption
            self.sub_land_use_required_dict[energy] = inputs_dict[f'{energy}.land_use_required']

            if energy in self.energy_class_dict:
                self.sub_carbon_emissions[energy] = inputs_dict[f'{energy}.CO2_emissions'][energy]
                self.co2_per_use[energy] = inputs_dict[f'{energy}.CO2_per_use']
                self.data_fuel_dict[energy] = inputs_dict[f'{energy}.data_fuel_dict']
        if 'syngas' in self.subelements_list:
            self.data_fuel_dict['syngas']['high_calorific_value'] = compute_calorific_value(
                inputs_dict['syngas_ratio'] / 100.0)

        self.co2_emissions = self.sub_carbon_emissions.copy(deep=True)
        self.energy_prices = self.sub_prices.copy(deep=True)
        self.energy_prices_after_carbon_tax = pd.DataFrame(
            {'years': self.energy_prices['years'].values})

        # dataframe resource demand
        self.all_resource_demand = pd.DataFrame(
            {'years': self.energy_prices['years'].values})
        for elements in self.resource_list:
            if elements in self.resource_list:
                self.all_resource_demand[elements] = np.linspace(
                    0, 0, len(self.all_resource_demand.index)) * 100.
        for energy in self.subelements_list:
            for resource in self.resource_list:
                if f'{resource} ({self.RESOURCE_CONSUMPTION_UNIT})' in self.sub_consumption_dict[energy].columns:
                    self.all_resource_demand[resource] = self.all_resource_demand[resource] + \
                        inputs_dict[f'{energy}.energy_consumption'][f'{resource} ({self.RESOURCE_CONSUMPTION_UNIT})'].values * \
                        self.scaling_factor_energy_consumption

        # DataFrame stream demand
        self.all_streams_demand_ratio = pd.DataFrame(
            {'years': self.energy_prices['years'].values})
        for energy in self.subelements_list:
            self.all_streams_demand_ratio[energy] = np.ones(
                len(self.all_streams_demand_ratio['years'].values)) * 100.

    def set_energy_prices_in(self, energy_prices):
        '''
        Setter method
        '''
        self.energy_prices_in = energy_prices

    def set_co2_emissions_in(self, co2_emissions):
        '''
        Setter method
        '''
        self.co2_emissions_in = co2_emissions

    def compute_energy_net_and_raw_production(self):
        """
        Compute the energy net production and the energy raw production
        If the value of total energy production is under the specified min_energy value
        an exponential decrease toward the limit is applied to always remain
        above it
        """
        for energy in self.subelements_list:
            self.production[f'{self.PRODUCTION} {energy} ({self.stream_class_dict[energy].unit})'] = pd.Series(
                self.sub_production_dict[energy][energy].values)
            self.production_raw[f'{self.PRODUCTION} {energy} ({self.stream_class_dict[energy].unit})'] = pd.Series(
                self.sub_production_dict[energy][energy].values)
            for idx, consu in self.sub_consumption_dict.items():
                if f'{energy} ({self.stream_class_dict[energy].unit})' in consu.columns:
                    self.production[f'{self.PRODUCTION} {energy} ({self.stream_class_dict[energy].unit})'] -= consu[
                        f'{energy} ({self.stream_class_dict[energy].unit})'].values
                else:
                    wrong_columns = [
                        column for column in consu.columns if energy in column]
                    if len(wrong_columns) != 0:
                        logging.warning(
                            f'The columns {wrong_columns} in the energy_consumption out of {idx} cannot be taken into account for an error of unity')

        self.substract_losses_by_energy()
        # Sum on netenergy production
        self.production['Total production'] = self.production[[
            column for column in self.production if column.endswith('(TWh)')]].sum(axis=1)

        # sum of positive energy production --> raw total production
        self.production_raw['Total production'] = self.production_raw[[
            column for column in self.production_raw if column.endswith('(TWh)')]].sum(axis=1)

        # substract a percentage of raw production into net production
        self.substract_energy_heat_losses()

        self.production['Total production (uncut)'] = self.production['Total production'].values
        min_energy = self.minimum_energy_production
        for year in self.production.index:
            if self.production.at[year, 'Total production'] < min_energy:
                # To avoid underflow : exp(-200) is considered to be the
                # minimum value for the exp
                production_year = max(
                    self.production.at[year, 'Total production'], -200.0 * min_energy)
                self.production.loc[year, 'Total production'] = min_energy / 10. * \
                    (9 + np.exp(production_year / min_energy) * np.exp(-1))

    def substract_energy_heat_losses(self):
        '''
        Substract heat losses due to heat stream (not implemented yet) 
        '''
        self.production['Total production'] -= self.production_raw['Total production'] * \
            self.heat_losses_percentage / 100.0

    def substract_losses_by_energy(self):
        '''
        Substract energy losses percentage to each net energy production before the sum of total net production
        '''
        for energy, percentage in self.losses_percentage_dict.items():
            self.production[f'production {energy} (TWh)'] -= self.production_raw[f'production {energy} (TWh)'] * \
                percentage / 100.0

    def compute_price_after_carbon_tax(self):
        '''
        Compute the energy price after carbon tax with all technology prices and technology weights computed with energy production 
        '''

        for energy in self.subelements_list:

            if energy in self.energy_class_dict:
                self.energy_prices_after_carbon_tax[energy] = self.sub_prices[energy].values + \
                    self.co2_per_use[energy]['CO2_per_use'].values * \
                    self.carbon_tax['CO2_tax'].values

    def compute_CO2_emissions_ratio(self):
        '''
        Compute the CO2 emission_ratio in kgCO2/kWh for the MDA
        '''
        self.carbon_emissions_after_use = pd.DataFrame(
            {'years': self.total_carbon_emissions['years'].values})
        for energy in self.subelements_list:
            if energy in self.energy_class_dict:
                self.total_carbon_emissions[energy] = self.sub_carbon_emissions[energy]
                self.carbon_emissions_after_use[energy] = self.total_carbon_emissions[energy] + \
                    self.co2_per_use[energy]['CO2_per_use']

    def compute_CO2_emissions(self):
        '''
        Compute CO2 total emissions
        '''
        # Initialize dataframes
        self.total_co2_emissions = pd.DataFrame(
            {'years': self.production['years']})
        self.co2_production = pd.DataFrame({'years': self.production['years']})
        self.co2_consumption = pd.DataFrame(
            {'years': self.production['years']})
        self.emissions_by_energy = pd.DataFrame(
            {'years': self.production['years']})
        # Do not loop over carbon capture and carbon storage which will be
        # handled differently

        for energy in self.subelements_list:
            self.emissions_by_energy[energy] = np.zeros_like(
                self.production['years'].values)
            if energy in self.only_energy_list:

                # gather all production columns with a CO2 name in it
                for col, production in self.sub_production_dict[energy].items():
                    if col in self.CO2_list:
                        self.co2_production[f'{energy} {col}'] = production.values
                        self.emissions_by_energy[
                            energy] += self.co2_production[f'{energy} {col}'].values
                # gather all consumption columns with a CO2 name in it
                for col, consumption in self.sub_consumption_dict[energy].items():
                    if col in self.CO2_list:
                        self.co2_consumption[f'{energy} {col}'] = consumption.values
                        self.emissions_by_energy[
                            energy] -= self.co2_consumption[f'{energy} {col}'].values
                # Compute the CO2 emitted during the use of the net energy
                # If net energy is negative, CO2 by use is equals to zero

                self.co2_production[f'{energy} CO2 by use (Mt)'] = self.co2_per_use[energy]['CO2_per_use'] * np.maximum(
                    0.0, self.production[f'production {energy} ({self.energy_class_dict[energy].unit})'].values)
                self.emissions_by_energy[
                    energy] += self.co2_production[f'{energy} CO2 by use (Mt)'].values

        ''' CARBON CAPTURE needed by energy mix
        Total carbon capture needed by energy mix if a technology needs carbon_capture
         Ex :Sabatier process or RWGS in FischerTropsch technology 
        '''
        energy_needing_carbon_capture = self.co2_consumption[[
            col for col in self.co2_consumption if col.endswith(f'{CarbonCapture.name} (Mt)')]]
        energy_needing_carbon_capture_list = [key.replace(
            f' {CarbonCapture.name} (Mt)', '') for key in energy_needing_carbon_capture]
        if len(energy_needing_carbon_capture_list) != 0:
            self.total_co2_emissions[f'{CarbonCapture.name} needed by energy mix (Mt)'] = energy_needing_carbon_capture.sum(
                axis=1).values
        else:
            self.total_co2_emissions[
                f'{CarbonCapture.name} needed by energy mix (Mt)'] = 0.0

        # Put in Gt carbon capture needed by energy mix
        self.co2_emissions_needed_by_energy_mix = pd.DataFrame(
            {'years': self.production['years'],
             f'{CarbonCapture.name} needed by energy mix (Gt)': self.total_co2_emissions[f'{CarbonCapture.name} needed by energy mix (Mt)'].values / 1e3})

    def compute_mean_price(self, exp_min=True):
        '''
        Compute energy mean price and price of each energy after carbon tax
        returns energy_mean price
                type:dataframe (years,energy_price)
                production_energy_pos (years,energies)
        '''
        energy_mean_price = pd.DataFrame(
            columns=['years', 'energy_price'])
        energy_mean_price['years'] = self.production['years']
        energy_mean_price['energy_price'] = 0.0

        production_energy_net_pos = pd.DataFrame(
            {'years': self.production['years'].values})
        for energy in self.subelements_list:
            if energy != CarbonCapture.name and energy != CarbonStorage.name:
                # We take only positive net production from energy different from
                # carbon capture and storage
                production_energy_net_pos[energy] = np.maximum(
                    0.0, self.production[f'production {energy} ({self.energy_class_dict[energy].unit})'])
        production_energy_net_pos['Total production'] = production_energy_net_pos.drop(
            'years', axis=1).sum(axis=1)

        element_list = [energy for energy in self.subelements_list if energy !=
                        CarbonCapture.name and energy != CarbonStorage.name]
        full_element_list = [
            f'production {energy} ({self.energy_class_dict[energy].unit})' for energy in element_list]
        element_dict = dict(zip(element_list, full_element_list))
        production_by_energy = pd.DataFrame(
            {'years': self.production['years'].values})
        for key, value in element_dict.items():
            if key != CarbonCapture.name and key != CarbonStorage.name:
                # We take only positive net production from energy different from
                # carbon capture and storage
                production_by_energy[value] = np.maximum(
                    0.0, self.production[value].values)
        production_by_energy['Total production'] = production_by_energy.drop(
            'years', axis=1).sum(axis=1)
        if exp_min:
            prod_element, prod_total_for_mix_weight = self.compute_prod_with_exp_min(
                production_by_energy, element_dict, self.production_threshold)
        else:
            prod_element, prod_total_for_mix_weight = self.compute_prod_wcutoff(
                production_by_energy, element_dict, self.production_threshold)
        for element in element_list:
            # compute mix weights for each energy
            mix_weight = prod_element[element] / \
                prod_total_for_mix_weight
            # If the element is negligible do not take into account this element
            # It is negligible if tol = 0.1%
            tol = 1e-3
            mix_weight[mix_weight < tol] = 0.0
            energy_mean_price['energy_price'] += self.energy_prices_after_carbon_tax[element].values * \
                mix_weight
            self.mix_weights[element] = mix_weight
        # In case all the technologies are below the threshold assign a
        # placeholder price
        if not exp_min:
            for year in energy_mean_price['years'].values:
                if np.real(energy_mean_price.loc[energy_mean_price['years'] == year]['energy_price'].values) == 0.0:
                    year_energy_prices = self.energy_prices_after_carbon_tax[
                        element_list].loc[energy_mean_price['years'] == year]
                    min_energy_price = min(
                        val for val in year_energy_prices.values[0] if val > 0.0)
                    min_energy_name = [
                        name for name in year_energy_prices.columns if year_energy_prices[name].values == min_energy_price][0]
                    energy_mean_price.loc[energy_mean_price['years'] ==
                                          year, 'energy_price'] = min_energy_price
                    for element in element_list:
                        self.mix_weights.loc[self.mix_weights['years'] == year,
                                             element] = 1. if element == min_energy_name else 0.0

        production_energy_net_pos['energy_price_pond'] = energy_mean_price['energy_price']
        return energy_mean_price, production_energy_net_pos

    def compute_total_prod_minus_min_prod_constraint(self):
        '''
        Compute constraint for total production. Calculated on production before exponential decrease towards the limit.
        Input: self.production['Total production (uncut)'], self.minimum_energy_production
        Output: total_prod_minus_min_prod_constraint_df
        '''

        self.total_prod_minus_min_prod_constraint_df[self.TOTAL_PROD_MINUS_MIN_PROD_CONSTRAINT] = (
            self.production['Total production (uncut)'].values - self.minimum_energy_production) / self.total_prod_minus_min_prod_constraint_ref

    def compute_constraint_h2(self):
        '''

        '''
        self.constraint_liquid_hydrogen = pd.DataFrame(
            {'years': self.production['years'].values})
        self.constraint_liquid_hydrogen['constraint_liquid_hydrogen'] = 0.
        hydrogen_name_list = [
            self.gaseousHydrogen_name, self.liquidHydrogen_name]
        # compute total H2 production
        for energy in hydrogen_name_list:
            if f'{self.PRODUCTION} {energy} ({self.energy_class_dict[energy].unit})' in self.production.columns:
                self.constraint_liquid_hydrogen['constraint_liquid_hydrogen'] += self.production[
                    f'{self.PRODUCTION} {energy} ({self.energy_class_dict[energy].unit})'].values
        if f'{self.PRODUCTION} {self.liquidHydrogen_name} ({self.energy_class_dict[self.liquidHydrogen_name].unit})' in self.production.columns:
            self.constraint_liquid_hydrogen['constraint_liquid_hydrogen'] = - (self.liquid_hydrogen_percentage * self.constraint_liquid_hydrogen['constraint_liquid_hydrogen'].values -
                                                                               self.production[f'{self.PRODUCTION} {self.liquidHydrogen_name} ({self.energy_class_dict[self.liquidHydrogen_name].unit})'].values) / self.liquid_hydrogen_constraint_ref

    def compute_constraint_solid_fuel_elec(self):
        '''

        '''
        self.constraint_solid_fuel_elec = pd.DataFrame(
            {'years': self.production['years'].values})
        self.constraint_solid_fuel_elec['constraint_solid_fuel_elec'] = 0.

        for energy in self.energy_constraint_list:
            if f'{self.PRODUCTION} {energy} ({self.energy_class_dict[energy].unit})' in self.production.columns:
                self.constraint_solid_fuel_elec['constraint_solid_fuel_elec'] += self.production[
                    f'{self.PRODUCTION} {energy} ({self.energy_class_dict[energy].unit})'].values
        self.constraint_solid_fuel_elec['constraint_solid_fuel_elec'] = - (self.constraint_solid_fuel_elec['constraint_solid_fuel_elec'].values - self.solid_fuel_elec_percentage *
                                                                           self.production[self.TOTAL_PRODUCTION].values) / self.solid_fuel_elec_constraint_ref

    def compute_syngas_prod_objective(self):
        '''
        Compute Syngas production objective
        '''
        if f'{self.PRODUCTION} {self.syngas_name} ({self.energy_class_dict[self.syngas_name].unit})' in self.production:
            self.syngas_prod_objective = np.sign(self.production[f'{self.PRODUCTION} {self.syngas_name} ({self.energy_class_dict[self.syngas_name].unit})'].values) * \
                self.production[f'{self.PRODUCTION} {self.syngas_name} ({self.energy_class_dict[self.syngas_name].unit})'].values / \
                self.syngas_prod_ref
        else:
            self.syngas_prod_objective = np.zeros(len(self.years))

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

    def compute_ratio_objective(self):

        ratio_arrays = self.all_streams_demand_ratio[self.subelements_list].values
        # Objective is to minimize the difference between 100 and all ratios
        # We give as objective the highest difference to start with the max of
        # the difference

        smooth_max = smooth_maximum(100.0 - ratio_arrays.flatten(), 3)
        self.ratio_objective = np.asarray(
            [smooth_max / self.ratio_norm_value])

    def compute_grad_CO2_emissions(self, net_production, co2_emissions, alpha):
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
        for energy in self.subelements_list:
            if energy in self.only_energy_list:

                # gather all production columns with a CO2 name in it
                for col, production in self.sub_production_dict[energy].items():
                    if col in self.CO2_list:
                        co2_production[f'{energy} {col}'] = production.values
                # gather all consumption columns with a CO2 name in it
                for col, consumption in self.sub_consumption_dict[energy].items():
                    if col in self.CO2_list:
                        co2_consumption[f'{energy} {col}'] = consumption.values

#                 # Compute the CO2 emitted during the use of the net energy
#                 # If net energy is negative, CO2 by use is equals to zero
#                 net_prod = net_production[
#                     f'production {energy} ({self.energy_class_dict[energy].unit})'].values
#
#                 dtot_CO2_emissions[f'Total CO2 by use (Mt) vs {energy}#co2_per_use'] = np.maximum(
#                     0, net_prod)
#
#                 # Specific case when net prod is equal to zero
#                 # if we increase the prod of an energy the net prod will react
#                 # however if we decrease the cons it does nothing
#                 net_prod_sign = net_prod.copy()
#                 net_prod_sign[net_prod_sign == 0] = 1
#                 dtot_CO2_emissions[f'Total CO2 by use (Mt) vs {energy}#prod'] = self.co2_per_use[energy]['CO2_per_use'].values * \
#                     np.maximum(0, np.sign(net_prod_sign))
#                 dtot_CO2_emissions[f'Total CO2 by use (Mt) vs {energy}#cons'] = - self.co2_per_use[energy]['CO2_per_use'].values * \
#                     np.maximum(0, np.sign(net_prod))
# #                         co2_production[f'{energy} CO2 by use (Mt)'] = self.stream_class_dict[energy].data_energy_dict['CO2_per_use'] / \
# #                             high_calorific_value * np.maximum(
# 0.0, self.production[f'production {energy}
# ({self.energy_class_dict[energy].unit})'].values)

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
                    f'{CarbonCapture.name} needed by energy mix (Gt) vs {energy1}#{CarbonCapture.name} (Mt)#cons'] = np.ones(len_years)
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
        key_dep_tuple_list = [(f'{CarbonCapture.name} (Mt) from CC technos', 1.0),
                              (f'{CarbonCapture.name} from energy mix (Mt)', 1.0),
                              (f'{CarbonCapture.name} needed by energy mix (Mt)', -1.0)]
        dtot_CO2_emissions = update_new_gradient(
            dtot_CO2_emissions, key_dep_tuple_list, new_key)

        return dtot_CO2_emissions


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
