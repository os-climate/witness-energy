'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/09-2023/11/15 Copyright 2023 Capgemini

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

from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.energy_models.solid_fuel import SolidFuel
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
from energy_models.core.techno_type.base_techno_models.solid_fuel_techno import SolidFuelTechno


class CoalExtraction(SolidFuelTechno):
    COAL_RESOURCE_NAME = ResourceGlossary.CoalResource

    def __init__(self, name):
        super().__init__(name)
        self.emission_factor_mt_twh = None

    def compute_resources_needs(self):
        # calorific value in kWh/kg * 1000 to have needs in t/kWh
        self.cost_details[f'{self.COAL_RESOURCE_NAME}_needs'] = np.ones(len(
            self.years)) / (SolidFuel.data_energy_dict['calorific_value'] * 1000.0)  # kg/kWh

    def compute_cost_of_other_energies_usage(self):
        self.cost_details[Electricity.name] = list(self.prices[Electricity.name] * self.cost_details['elec_needs']
                                                   / self.cost_details['efficiency'])

    def compute_other_energies_needs(self):
        self.cost_details['elec_needs'] = self.get_electricity_needs()


        # self.cost_details['fuel_needs'] = self.get_fuel_needs()
        # self.cost_details[LiquidFuel.name] = list(self.prices[LiquidFuel.name] * self.cost_details['fuel_needs']
        #                                         / self.cost_details['efficiency'])

        # + self.cost_details[LiquidFuel.name]

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs which depends on the technology 
        """

        super().compute_other_primary_energy_costs()

        return self.cost_details[Electricity.name] + self.cost_of_resources_usage[self.COAL_RESOURCE_NAME]

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices 
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        elec_needs = self.get_electricity_needs()
        efficiency = self.techno_infos_dict['efficiency']
        return {Electricity.name: np.identity(len(self.years)) * elec_needs / efficiency,
                # LiquidFuel.name: np.identity(len(self.years)) * fuel_needs /
                # efficiency,
                }

    def grad_price_vs_resources_price(self):
        '''
        Compute the gradient of global price vs resources prices
        '''
        coal_needs = self.cost_details[f'{self.COAL_RESOURCE_NAME}_needs'].values
        return {self.COAL_RESOURCE_NAME: np.identity(len(self.years)) * coal_needs, }

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """

        self.production_detailed[f'{CO2.name} ({self.mass_unit})'] = self.techno_infos_dict['CO2_from_production'] / \
                                                                     self.data_energy_dict['high_calorific_value'] * \
                                                                     self.production_detailed[
                                                                         f'{SolidFuelTechno.energy_name} ({self.product_energy_unit})']

        self.compute_ch4_emissions()
        # Consumption
        self.consumption_detailed[f'{Electricity.name} ({self.product_energy_unit})'] = self.cost_details[
                                                                                            'elec_needs'] * \
                                                                                        self.production_detailed[
                                                                                            f'{SolidFuelTechno.energy_name} ({self.product_energy_unit})']  # in kWH

        # self.consumption[f'{LiquidFuel.name} ({self.product_energy_unit})'] = self.cost_details['fuel_needs'] * \
        #     self.production[f'{SolidFuelTechno.energy_name} ({self.product_energy_unit})'] / \
        #     self.cost_details['efficiency']  # in kWH

        # Coal Consumption
        self.consumption_detailed[f'{self.COAL_RESOURCE_NAME} ({self.mass_unit})'] = self.production_detailed[
                                                                                         f'{SolidFuelTechno.energy_name} ({self.product_energy_unit})'] / \
                                                                                     self.cost_details['efficiency'] / \
                                                                                     SolidFuel.data_energy_dict[
                                                                                         'calorific_value']  # in Mt

    def compute_CO2_emissions_from_input_resources(self):
        '''
        Need to take into account  CO2 from electricity/fuel production
        '''

        self.carbon_intensity[Electricity.name] = self.energy_CO2_emissions[Electricity.name] * \
                                                  self.cost_details['elec_needs']
        self.carbon_intensity[self.COAL_RESOURCE_NAME] = self.resources_CO2_emissions[self.COAL_RESOURCE_NAME] * \
                                                         self.cost_details[f'{self.COAL_RESOURCE_NAME}_needs']

        # if LiquidFuel.name in self.energy_CO2_emissions:
        #     self.carbon_emissions[LiquidFuel.name] = self.energy_CO2_emissions[f'{LiquidFuel.name}'] * \
        #         self.cost_details['fuel_needs']
        # else:
        #     self.carbon_emissions[LiquidFuel.name] = 25.33 * \
        #         self.cost_details['fuel_needs']
        return self.carbon_intensity[Electricity.name] + self.carbon_intensity[self.COAL_RESOURCE_NAME]
        # + self.carbon_emissions[LiquidFuel.name]

    def compute_ch4_emissions(self):
        '''
        Method to compute CH4 emissions from coal mines
        The proposed V0 only depends on production. The V1 could depend on mining depth (deeper and deeper along the years)
        Equation is taken from the GAINS model
        https://gem.wiki/Estimating_methane_emissions_from_coal_mines#Model_for_Calculating_Coal_Mine_Methane_.28MC2M.29,
        Nazar Kholod &al Global methane emissions from coal mining to continue growing even with declining coal production,
         Journal of Cleaner Production, Volume 256, February 2020.
        '''
        emission_factor_coeff = self.techno_infos_dict['emission_factor_coefficient']

        # compute gas content with surface and underground_gas_content in m3/t
        underground_mining_gas_content = self.techno_infos_dict['underground_mining_gas_content']
        surface_mining_gas_content = self.techno_infos_dict['surface_mining_gas_content']
        gas_content = self.techno_infos_dict['underground_mining_percentage'] / \
                      100.0 * underground_mining_gas_content + \
                      (1. - self.techno_infos_dict['underground_mining_percentage'] /
                       100.0) * surface_mining_gas_content

        # gascontent must be passed in Mt/Twh
        self.emission_factor_mt_twh = gas_content * emission_factor_coeff * Methane.data_energy_dict['density'] / \
                                      self.data_energy_dict['calorific_value'] * 1e-3
        # need to multiply by 1e9 to be in m3 by density to be in kg and by 1e-9 to be in Mt
        # and add ch4 from abandoned mines
        self.production_detailed[f'{Methane.emission_name} ({self.mass_unit})'] = self.emission_factor_mt_twh * \
                                                                                  self.production_detailed[
                                                                                      f'{SolidFuelTechno.energy_name} ({self.product_energy_unit})'].values + \
                                                                                  self.techno_infos_dict[
                                                                                      'ch4_from_abandoned_mines']
