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

from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import GaseousHydrogen
from energy_models.core.stream_type.energy_models.methanol import Methanol
from energy_models.core.stream_type.resources_models.water import Water
from energy_models.core.techno_type.base_techno_models.methanol_techno import MethanolTechno


class CO2Hydrogenation(MethanolTechno):

    def compute_resources_needs(self):
        self.cost_details[f'{Water.name}_needs'] = self.get_theoretical_water_needs() / self.cost_details['efficiency']

    def compute_other_energies_needs(self):
        self.cost_details[f'{CarbonCapture.name}_needs'] = self.get_theoretical_co2_needs() / self.cost_details['efficiency']
        self.cost_details[f'{GaseousHydrogen.name}_needs'] = self.get_theoretical_hydrogen_needs() / self.cost_details['efficiency']
        self.cost_details[f'{Electricity.name}_needs'] = self.get_theoretical_electricity_needs() / self.cost_details['efficiency']


    def compute_consumption(self):
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

    def get_theoretical_co2_needs(self):
        """
        """
        carbon_capture_demand = self.techno_infos_dict['carbon_capture_demand']
        carbon_capture_calorific_value = CarbonCapture.data_energy_dict['calorific_value']  # kWh/kg
        methanol_calorific_value = Methanol.data_energy_dict['calorific_value']  # kWh/kg

        carbon_capture_needs = carbon_capture_demand * carbon_capture_calorific_value / methanol_calorific_value  # kWh/kWh
        return carbon_capture_needs

    def get_theoretical_hydrogen_needs(self):
        """
        """
        hydrogen_demand = self.techno_infos_dict['hydrogen_demand']  # kg/kg
        hydrogen_calorific_value = GaseousHydrogen.data_energy_dict['calorific_value']  # kWh/kg
        methanol_calorific_value = Methanol.data_energy_dict['calorific_value']  # kWh/kg

        hydrogen_needs = hydrogen_demand * hydrogen_calorific_value / methanol_calorific_value  # kWh/kWh
        return hydrogen_needs

    def get_theoretical_water_needs(self):
        """
        """
        water_demand = self.techno_infos_dict['water_demand']  # kg/kg
        methanol_calorific_value = Methanol.data_energy_dict['calorific_value']  # kWh/kg

        water_needs = water_demand / methanol_calorific_value  # kg/kWh = Mt/TWh
        return water_needs

    def get_theoretical_electricity_needs(self):
        """
        """
        elec_demand = self.techno_infos_dict['elec_demand']  # kWh/kg
        methanol_calorific_value = Methanol.data_energy_dict['calorific_value']  # kWh/kg

        electricity_needs = elec_demand / methanol_calorific_value  # kWh/kWh

        return electricity_needs
