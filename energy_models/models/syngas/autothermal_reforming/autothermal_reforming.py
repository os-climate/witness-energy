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

from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.resources_models.dioxygen import Dioxygen
from energy_models.core.stream_type.resources_models.oxygen import Oxygen
from energy_models.core.stream_type.resources_models.water import Water
from energy_models.core.techno_type.base_techno_models.syngas_techno import SyngasTechno


class AutothermalReforming(SyngasTechno):
    syngas_COH2_ratio = 100.0  # in %

    def compute_resources_needs(self):
        # need in kg to produce 1kwh of syngas
        self.cost_details['CO2_needs'] = self.get_theoretical_CO2_needs() / self.cost_details['efficiency']
        # need in kg to produce 1kwh of syngas
        self.cost_details['oxygen_needs'] = self.get_theoretical_O2_needs() / self.cost_details['efficiency']

    def compute_cost_of_resources_usage(self):
        # Cost of oxygen for 1 kWH of H2
        self.cost_details[Oxygen.name] = list(
            self.resources_prices[f'{Oxygen.name}'] * self.cost_details['oxygen_needs'])

        # Cost of CO2 for 1 kWH of H2
        self.cost_details[CO2.name] = list(self.resources_prices[f'{CO2.name}'] * self.cost_details['CO2_needs'])

    def compute_cost_of_other_energies_usage(self):
        # Cost of methane for 1 kWH of H2
        self.cost_details[f'{Methane.name}'] = list(self.prices[f'{Methane.name}'] * self.cost_details['methane_needs']
                                                    / self.cost_details['efficiency'])

    def compute_other_energies_needs(self):
        # need in kwh to produce 1kwh of syngas
        self.cost_details['methane_needs'] = self.get_theoretical_CH4_needs()


    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs to produce 1kg of CH4
        """
        self.compute_resources_needs()
        self.compute_cost_of_resources_usage()
        self.compute_other_energies_needs()
        self.compute_cost_of_other_energies_usage()

        return self.cost_details[Oxygen.name] + self.cost_details[Methane.name] + self.cost_details[CO2.name]

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices 
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        # CO2_needs = self.get_theoretical_CO2_needs()
        methane_needs = self.get_theoretical_CH4_needs()
        # oxygen_needs = self.get_theoretical_O2_needs()
        efficiency = self.compute_efficiency()
        return {
            Methane.name: np.diag(methane_needs / efficiency)
        }

    def grad_price_vs_resources_price(self):
        '''
        Compute the gradient of global price vs resources prices
        '''
        co2_needs = self.get_theoretical_CO2_needs()
        oxygen_needs = self.get_theoretical_O2_needs()
        efficiency = self.compute_efficiency()
        init_grad = np.diag(1 / efficiency)
        return {
            CO2.name: init_grad * co2_needs,
            Oxygen.name: init_grad * oxygen_needs,
        }

    def compute_CO2_emissions_from_input_resources(self):
        ''' 
        Need to take into account negative CO2 from CO2 and methane
        Oxygen is not taken into account
        '''

        self.carbon_intensity[f'{Methane.name}'] = self.energy_CO2_emissions[f'{Methane.name}'] * \
                                                   self.cost_details['methane_needs'] / \
                                                   self.cost_details['efficiency']
        self.carbon_intensity[CO2.name] = self.resources_CO2_emissions[CO2.name] * \
                                          self.cost_details['CO2_needs']
        self.carbon_intensity[Oxygen.name] = self.resources_CO2_emissions[Oxygen.name] * \
                                             self.cost_details['oxygen_needs']

        return self.carbon_intensity[f'{Methane.name}'] + self.carbon_intensity[CO2.name] + self.carbon_intensity[
            Oxygen.name]

    def grad_co2_emissions_vs_resources_co2_emissions(self):
        '''
        Compute the gradient of global CO2 emissions vs resources CO2 emissions
        '''
        co2_needs = self.get_theoretical_CO2_needs()
        efficiency = self.compute_efficiency()
        return {
            CO2.name: np.diag(co2_needs / efficiency),
        }

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

        # kg of H2O produced with 1kg of CH4
        H2Oprod = self.get_h2o_production()

        # total H2O production
        self.production_detailed[f'{Water.name} ({self.mass_unit})'] = self.production_detailed[
                                                                           f'{SyngasTechno.energy_name} ({self.product_energy_unit})'] * \
                                                                       H2Oprod

        # Consumption
        self.consumption_detailed[f'{CarbonCapture.name} ({self.mass_unit})'] = self.cost_details['CO2_needs'] * \
                                                                                self.production_detailed[
                                                                                    f'{SyngasTechno.energy_name} ({self.product_energy_unit})'] / \
                                                                                self.cost_details['efficiency']

        self.consumption_detailed[f'{Dioxygen.name} ({self.mass_unit})'] = self.cost_details['oxygen_needs'] * \
                                                                           self.production_detailed[
                                                                               f'{SyngasTechno.energy_name} ({self.product_energy_unit})'] / \
                                                                           self.cost_details['efficiency']

        self.consumption_detailed[f'{Methane.name} ({self.product_energy_unit})'] = self.cost_details['methane_needs'] * \
                                                                                    self.production_detailed[
                                                                                        f'{SyngasTechno.energy_name} ({self.product_energy_unit})'] / \
                                                                                    self.cost_details['efficiency']

        # self.consumption[f'{hightemperatureheat.name} ({self.product_energy_unit})'] = self.cost_details['methane_needs'] * \
        #     self.production[f'{SyngasTechno.energy_name} ({self.product_energy_unit})'] / \
        #     self.cost_details['efficiency']

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
