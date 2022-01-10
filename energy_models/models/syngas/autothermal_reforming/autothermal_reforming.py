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
from energy_models.core.techno_type.base_techno_models.syngas_techno import SyngasTechno
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.ressources_models.oxygen import Oxygen
from energy_models.core.stream_type.ressources_models.water import Water
from energy_models.core.stream_type.ressources_models.dioxygen import Dioxygen

import numpy as np


class AuthothermalReforming(SyngasTechno):

    syngas_COH2_ratio = 100.0  # in %

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs to produce 1kg of CH4
        """

        # need in kg to produce 1kwh of syngas
        self.cost_details['CO2_needs'] = self.get_theoretical_CO2_needs()

        # need in kwh to produce 1kwh of syngas
        self.cost_details['methane_needs'] = self.get_theoretical_CH4_needs()

        # need in kg to produce 1kwh of syngas
        self.cost_details['oxygen_needs'] = self.get_theoretical_O2_needs()

        # Cost of oxygen for 1 kWH of H2
        self.cost_details[Oxygen.name] = list(self.ressources_prices[f'{Oxygen.name}'] * self.cost_details['oxygen_needs']
                                              / self.cost_details['efficiency'])
        # Cost of methane for 1 kWH of H2
        self.cost_details[f'{Methane.name}'] = list(self.prices[f'{Methane.name}'] * self.cost_details['methane_needs']
                                                    / self.cost_details['efficiency'])

        # Cost of CO2 for 1 kWH of H2
        self.cost_details[CO2.name] = list(self.ressources_prices[f'{CO2.name}'] * self.cost_details['CO2_needs']
                                           / self.cost_details['efficiency'])

        return self.cost_details[Oxygen.name] + self.cost_details[Methane.name] + self.cost_details[CO2.name]

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices 
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        # CO2_needs = self.get_theoretical_CO2_needs()
        methane_needs = self.get_theoretical_CH4_needs()
        # oxygen_needs = self.get_theoretical_O2_needs()
        efficiency = self.configure_efficiency()
        return {
            Methane.name: np.identity(
                len(self.years)) * methane_needs / efficiency[:, np.newaxis]

        }

    def compute_CO2_emissions_from_input_ressources(self):
        ''' 
        Need to take into account negative CO2 from CO2 and methane
        Oxygen is not taken into account
        '''

        self.carbon_emissions[f'{Methane.name}'] = self.energy_CO2_emissions[f'{Methane.name}'] * \
            self.cost_details['methane_needs'] / \
            self.cost_details['efficiency']
        self.carbon_emissions[CO2.name] = self.ressources_CO2_emissions[CO2.name] * \
            self.cost_details['CO2_needs'] / self.cost_details['efficiency']

        return self.carbon_emissions[f'{Methane.name}'] + self.carbon_emissions[CO2.name]

    def get_theoretical_CH4_needs(self):
        """
        Get methane needs in kWh CH4 /kWh syngas
        2 mol of CH4 for 3 mol of H2 and 3 mol of CO
        Warning : molar mass is in g/mol but we divide and multiply by one
        """

        mol_CH4 = 2.0
        mol_COH2 = 3.0
        methane_data = Methane.data_energy_dict
        methane_needs = mol_CH4 * methane_data['molar_mass'] * methane_data['calorific_value'] / \
            (mol_COH2 * self.data_energy_dict['molar_mass'] *
             self.data_energy_dict['calorific_value'])

        return methane_needs

    def get_theoretical_CO2_needs(self):
        ''' 
        Get water needs in kg CO2 /kWh H2
        1 mol of CO2 for 3 mol of CO and 3 mol of H2
        Warning : molar mass is in g/mol but we divide and multiply by one
        '''

        mol_CO2 = 1.0
        mol_COH2 = 3.0
        water_data = CO2.data_energy_dict
        water_needs = mol_CO2 * water_data['molar_mass'] / \
            (mol_COH2 * self.data_energy_dict['molar_mass'] *
             self.data_energy_dict['calorific_value'])

        return water_needs

    def get_theoretical_O2_needs(self):
        ''' 
        Get water needs in kg O2 /kWh H2
        1 mol of O2 for 3 mol of CO and 3 mol of H2
        Warning : molar mass is in g/mol but we divide and multiply by one
        '''

        mol_O2 = 1.0
        mol_COH2 = 3.0
        oxygen_data = Oxygen.data_energy_dict
        water_needs = mol_O2 * oxygen_data['molar_mass'] / \
            (mol_COH2 * self.data_energy_dict['molar_mass'] *
             self.data_energy_dict['calorific_value'])

        return water_needs

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """

        self.compute_primary_energy_production()

        # kg of H2O produced with 1kg of CH4
        H2Oprod = self.get_h2o_production()

        # total H2O production
        self.production[f'{Water.name} ({self.mass_unit})'] = self.production[f'{SyngasTechno.energy_name} ({self.product_energy_unit})'] * \
            H2Oprod

        # Consumption
        self.consumption[f'{CarbonCapture.name} ({self.mass_unit})'] = self.cost_details['CO2_needs'] * \
            self.production[f'{SyngasTechno.energy_name} ({self.product_energy_unit})'] / \
            self.cost_details['efficiency']

        self.consumption[f'{Dioxygen.name} ({self.mass_unit})'] = self.cost_details['oxygen_needs'] * \
            self.production[f'{SyngasTechno.energy_name} ({self.product_energy_unit})'] / \
            self.cost_details['efficiency']

        self.consumption[f'{Methane.name} ({self.product_energy_unit})'] = self.cost_details['methane_needs'] * \
            self.production[f'{SyngasTechno.energy_name} ({self.product_energy_unit})'] / \
            self.cost_details['efficiency']

    def get_h2o_production(self):
        """
        Get water produced when producing 1kg of Syngas
        """

        # water created when producing 1kg of CH4
        mol_H20 = 1
        mol_syngas = 3.0
        water_data = Water.data_energy_dict
        production_for_1kg = mol_H20 * \
            water_data['molar_mass'] / \
            (mol_syngas * self.data_energy_dict['molar_mass']
             * self.data_energy_dict['calorific_value'])

        return production_for_1kg
