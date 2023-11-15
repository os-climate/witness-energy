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
from energy_models.core.stream_type.energy_models.methanol import Methanol
from energy_models.core.techno_type.base_techno_models.methanol_techno import MethanolTechno
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import GaseousHydrogen
from energy_models.core.stream_type.resources_models.water import Water
from energy_models.core.stream_type.energy_models.electricity import Electricity

import numpy as np


class CO2Hydrogenation(MethanolTechno):

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs to produce 1kWh of methanol
        """
        self.cost_details[f'{CarbonCapture.name}_needs'] = self.get_theoretical_co2_needs()
        self.cost_details[f'{GaseousHydrogen.name}_needs'] = self.get_theoretical_hydrogen_needs()
        self.cost_details[f'{Water.name}_needs'] = self.get_theoretical_water_needs()
        self.cost_details[f'{Electricity.name}_needs'] = self.get_theoretical_electricity_needs()

        self.cost_details[f'{CarbonCapture.name}'] = \
            self.prices[f'{CarbonCapture.name}'] * \
            self.cost_details[f'{CarbonCapture.name}_needs'] / \
            self.cost_details['efficiency']

        self.cost_details[f'{GaseousHydrogen.name}'] = \
            self.prices[f'{GaseousHydrogen.name}'] * \
            self.cost_details[f'{GaseousHydrogen.name}_needs'] / \
            self.cost_details['efficiency']

        self.cost_details[f'{Water.name}'] = \
            self.resources_prices[f'{Water.name}'] * \
            self.cost_details[f'{Water.name}_needs'] / \
            self.cost_details['efficiency']

        self.cost_details[f'{Electricity.name}'] = \
            self.prices[Electricity.name] * \
            self.cost_details[f'{Electricity.name}_needs'] / \
            self.cost_details['efficiency']

        return self.cost_details[f'{CarbonCapture.name}'] + self.cost_details[f'{GaseousHydrogen.name}'] + \
        self.cost_details[f'{Water.name}'] + self.cost_details[f'{Electricity.name}']

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices 
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        co2_needs = self.get_theoretical_co2_needs()
        hydrogen_needs = self.get_theoretical_hydrogen_needs()
        elec_needs = self.get_theoretical_electricity_needs()
        efficiency = self.techno_infos_dict['efficiency']
        return {
            CarbonCapture.name: np.identity(len(self.years)) * co2_needs / efficiency,
            GaseousHydrogen.name: np.identity(len(self.years)) * hydrogen_needs / efficiency,
            Electricity.name: np.identity(len(self.years)) * elec_needs / efficiency,
                }

    def grad_price_vs_resources_price(self):
        '''
        Compute the gradient of global price vs resources prices
        '''
        efficiency = self.techno_infos_dict['efficiency']
        water_needs = self.get_theoretical_water_needs()

        return {Water.name: np.identity(len(self.years)) * water_needs / efficiency,
                }

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        """

        

        # Consumption

        self.consumption_detailed[f'{CarbonCapture.name} ({self.product_energy_unit})'] = \
            self.cost_details[f'{CarbonCapture.name}_needs'] * \
            self.production_detailed[f'{Methanol.name} ({self.product_energy_unit})'] / \
            self.cost_details['efficiency']

        self.consumption_detailed[f'{GaseousHydrogen.name} ({self.product_energy_unit})'] = \
            self.cost_details[f'{GaseousHydrogen.name}_needs'] * \
            self.production_detailed[f'{Methanol.name} ({self.product_energy_unit})'] / \
            self.cost_details['efficiency']

        self.consumption_detailed[f'{Electricity.name} ({self.product_energy_unit})'] = \
            self.cost_details[f'{Electricity.name}_needs'] * \
            self.production_detailed[f'{Methanol.name} ({self.product_energy_unit})'] / \
            self.cost_details['efficiency']

        self.consumption_detailed[f'{Water.name} ({self.mass_unit})'] = \
            self.cost_details[f'{Water.name}_needs'] * \
            self.production_detailed[f'{Methanol.name} ({self.product_energy_unit})'] / \
            self.cost_details['efficiency']

    def compute_CO2_emissions_from_input_resources(self):
        '''
        Need to take into account CO2 from electricity/fuel production
        '''

        self.carbon_intensity[CarbonCapture.name] = \
            self.energy_CO2_emissions[CarbonCapture.name] * \
            self.cost_details[f'{CarbonCapture.name}_needs'] / \
            self.cost_details['efficiency']

        self.carbon_intensity[GaseousHydrogen.name] = \
            self.energy_CO2_emissions[GaseousHydrogen.name] * \
            self.cost_details[f'{GaseousHydrogen.name}_needs'] / \
            self.cost_details['efficiency']

        self.carbon_intensity[f'{Electricity.name}'] = \
            self.energy_CO2_emissions[f'{Electricity.name}'] * \
            self.cost_details[f'{Electricity.name}_needs'] / \
            self.cost_details['efficiency']

        self.carbon_intensity[Water.name] = \
            self.resources_CO2_emissions[Water.name] * \
            self.cost_details[f'{Water.name}_needs'] / \
            self.cost_details['efficiency']

        return self.carbon_intensity[f'{CarbonCapture.name}'] + self.carbon_intensity[f'{GaseousHydrogen.name}'] + \
               self.carbon_intensity[f'{Electricity.name}'] + self.carbon_intensity[Water.name]

    def get_theoretical_co2_needs(self):
        """
        """
        carbon_capture_demand = self.techno_infos_dict['carbon_capture_demand']
        carbon_capture_calorific_value = CarbonCapture.data_energy_dict['calorific_value']  # kWh/kg
        methanol_calorific_value = Methanol.data_energy_dict['calorific_value']  # kWh/kg

        carbon_capture_needs = carbon_capture_demand * carbon_capture_calorific_value / methanol_calorific_value #kWh/kWh
        return carbon_capture_needs

    def get_theoretical_hydrogen_needs(self):
        """
        """
        hydrogen_demand = self.techno_infos_dict['hydrogen_demand'] # kg/kg
        hydrogen_calorific_value = GaseousHydrogen.data_energy_dict['calorific_value']  # kWh/kg
        methanol_calorific_value = Methanol.data_energy_dict['calorific_value']  # kWh/kg

        hydrogen_needs = hydrogen_demand * hydrogen_calorific_value / methanol_calorific_value # kWh/kWh
        return hydrogen_needs

    def get_theoretical_water_needs(self):
        """
        """
        water_demand = self.techno_infos_dict['water_demand']                    # kg/kg
        methanol_calorific_value = Methanol.data_energy_dict['calorific_value']   # kWh/kg

        water_needs = water_demand / methanol_calorific_value #kg/kWh = Mt/TWh
        return water_needs

    def get_theoretical_electricity_needs(self):
        """
        """
        elec_demand = self.techno_infos_dict['elec_demand']                       # kWh/kg
        methanol_calorific_value = Methanol.data_energy_dict['calorific_value']   # kWh/kg

        electricity_needs = elec_demand / methanol_calorific_value #kWh/kWh

        return electricity_needs