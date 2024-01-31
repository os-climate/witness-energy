'''
Copyright 2022 Airbus SAS
Modifications on 2023/09/25-2023/11/16 Copyright 2023 Capgemini

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

from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.resources_models.water import Water
from energy_models.core.techno_type.base_techno_models.syngas_techno import SyngasTechno


class SMR(SyngasTechno):
    syngas_COH2_ratio = 1.0 / 3.0 * 100.0

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs to produce 1kg of syngas 
        """

        self.cost_details['elec_needs'] = self.get_electricity_needs()

        # need in kg to produce 1kwh of syngas
        self.cost_details['CH4_needs'] = self.get_theoretical_CH4_needs()

        # need in kwh to produce 1kwh of syngas
        self.cost_details[f'{Water.name}_needs'] = self.get_theoretical_water_needs()

        # Cost of CO2 for 1 kWH of H2
        self.cost_details[f'{Methane.name}'] = list(self.prices[f'{Methane.name}'] * self.cost_details['CH4_needs']
                                                    / self.cost_details['efficiency'])

        # Cost of H20 for 1 kWH of H2
        self.cost_details[Water.name] = list(
            self.resources_prices[Water.name] * self.cost_details[f'{Water.name}_needs']
            / self.cost_details['efficiency'])

        self.cost_details['electricity'] = self.cost_details['elec_needs'] * \
                                           self.prices['electricity']

        return self.cost_details[Water.name] + self.cost_details[f'{Methane.name}'] + self.cost_details['electricity']

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices 
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        # CO2_needs = self.get_theoretical_CO2_needs()
        methane_needs = self.get_theoretical_CH4_needs()
        elec_needs = self.get_electricity_needs()
        # oxygen_needs = self.get_theoretical_O2_needs()
        efficiency = self.configure_efficiency()
        return {
            Methane.name: np.identity(
                len(self.years)) * methane_needs / efficiency[:, np.newaxis],
            Electricity.name: np.identity(
                len(self.years)) * elec_needs
        }

    def grad_price_vs_resources_price(self):
        '''
        Compute the gradient of global price vs resources prices 
        '''
        water_needs = self.get_theoretical_water_needs()
        efficiency = self.configure_efficiency()
        return {
            Water.name: np.identity(
                len(self.years)) * water_needs / efficiency[:, np.newaxis],
        }

    def compute_CO2_emissions_from_input_resources(self):
        ''' 
        Need to take into account negative CO2 from CO2 and methane
        Oxygen is not taken into account
        '''

        self.carbon_intensity[f'{Methane.name}'] = self.energy_CO2_emissions[f'{Methane.name}'] * \
                                                   self.cost_details['CH4_needs'] / \
                                                   self.cost_details['efficiency']

        self.carbon_intensity[Electricity.name] = self.energy_CO2_emissions[Electricity.name] * \
                                                  self.cost_details['elec_needs']

        self.carbon_intensity[Water.name] = self.resources_CO2_emissions[Water.name] * \
                                            self.cost_details[f'{Water.name}_needs'] / \
                                            self.cost_details['efficiency']

        return self.carbon_intensity[f'{Methane.name}'] + self.carbon_intensity[Electricity.name] + \
               self.carbon_intensity[Water.name]

    def get_theoretical_CH4_needs(self):
        ''' 
        Get CH4 needs in kWh CH4 /kWh syngas
        1 mol of CH4 for 1 mol of CO and 1 mol of H2
        Warning : molar mass is in g/mol but we divide and multiply by one
        CH4 + H20 --> 3(H2+1/3CO)
        '''
        mol_CH4 = 1.0
        mol_COH2 = 3.0
        methane_data = Methane.data_energy_dict
        methane_needs = mol_CH4 * methane_data['molar_mass'] * methane_data['calorific_value'] / \
                        (mol_COH2 * self.data_energy_dict['molar_mass'] *
                         self.data_energy_dict['calorific_value'])

        return methane_needs

    def get_theoretical_water_needs(self):
        ''' 
        Get water needs in kg water /kWh syngas
        1 mol of H2O for 1 mol of synags 
        Warning : molar mass is in g/mol but we divide and multiply by one
        '''

        mol_H2O = 1.0
        mol_COH2 = 3.0
        water_data = Water.data_energy_dict
        water_needs = mol_H2O * water_data['molar_mass'] / \
                      (mol_COH2 * self.data_energy_dict['molar_mass'] *
                       self.data_energy_dict['calorific_value'])

        return water_needs

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """

        # Consumption
        self.consumption_detailed[f'{Methane.name} ({self.product_energy_unit})'] = self.cost_details['CH4_needs'] * \
                                                                                    self.production_detailed[
                                                                                        f'{SyngasTechno.energy_name} ({self.product_energy_unit})'] / \
                                                                                    self.cost_details['efficiency']

        self.consumption_detailed[f'{Electricity.name} ({self.product_energy_unit})'] = self.cost_details[
                                                                                            'elec_needs'] * \
                                                                                        self.production_detailed[
                                                                                            f'{SyngasTechno.energy_name} ({self.product_energy_unit})']

        self.consumption_detailed[f'{Water.name} ({self.mass_unit})'] = self.cost_details[f'{Water.name}_needs'] * \
                                                                        self.production_detailed[
                                                                            f'{SyngasTechno.energy_name} ({self.product_energy_unit})'] / \
                                                                        self.cost_details['efficiency']

        # self.production[f'{highheattechno.energy_name} ({self.product_energy_unit})'] = \
        #     self.techno_infos_dict['high_heat_production'] * \
        #     self.production[f'{SyngasTechno.energy_name} ({self.product_energy_unit})']
