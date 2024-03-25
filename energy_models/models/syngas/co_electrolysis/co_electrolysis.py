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
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.resources_models.dioxygen import Dioxygen
from energy_models.core.stream_type.resources_models.water import Water
from energy_models.core.techno_type.base_techno_models.syngas_techno import SyngasTechno


class CoElectrolysis(SyngasTechno):
    syngas_COH2_ratio = 100.0  # in %

    def compute_resources_needs(self):
        # need in kg to produce 1kwh of syngas
        self.cost_details['CO2_needs'] = self.get_theoretical_CO2_needs()

        # need in kwh to produce 1kwh of syngas
        self.cost_details['water_needs'] = self.get_theoretical_water_needs()

    def compute_cost_of_resources_usage(self):
        # Cost of CO2 for 1 kWH of H2
        self.cost_details[CO2.name] = list(self.resources_prices[f'{CO2.name}'] * self.cost_details['CO2_needs']
                                           / self.cost_details['efficiency'])

        # Cost of H20 for 1 kWH of H2
        self.cost_details[Water.name] = list(self.resources_prices[Water.name] * self.cost_details['water_needs']
                                             / self.cost_details['efficiency'])

    def compute_cost_of_other_energies_needs(self):
        self.cost_details['elec_needs'] = self.get_electricity_needs()

        self.cost_details[Electricity.name] = self.cost_details['elec_needs'] * \
                                              self.prices[Electricity.name]

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs to produce 1kg of syngas 
        """

        self.compute_resources_needs()
        self.compute_cost_of_resources_usage()
        self.compute_cost_of_other_energies_needs()

        return self.cost_details[Water.name] + self.cost_details[CO2.name] + self.cost_details[Electricity.name]

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices 
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        elec_needs = self.get_electricity_needs()
        return {Electricity.name: np.identity(len(self.years)) * elec_needs,
                }

    def grad_price_vs_resources_price(self):
        '''
        Compute the gradient of global price vs resources prices
        '''
        co2_needs = self.get_theoretical_CO2_needs()
        water_needs = self.get_theoretical_water_needs()
        efficiency = self.configure_efficiency()
        init_grad = np.identity(len(self.years)) / efficiency[:, np.newaxis]
        return {
            CO2.name: init_grad * co2_needs,
            Water.name: init_grad * water_needs,
        }

    def compute_CO2_emissions_from_input_resources(self):
        ''' 
        Need to take into account negative CO2 from CO2 and positive from elec
        Oxygen is not taken into account
        '''

        self.carbon_intensity[f'{CO2.name}'] = self.resources_CO2_emissions[f'{CO2.name}'] * \
                                               self.cost_details['CO2_needs'] / \
                                               self.cost_details['efficiency']

        self.carbon_intensity[Water.name] = self.resources_CO2_emissions[Water.name] * \
                                            self.cost_details['water_needs'] / self.cost_details['efficiency']

        self.carbon_intensity[Electricity.name] = self.energy_CO2_emissions[Electricity.name] * \
                                                  self.cost_details['elec_needs']

        return self.carbon_intensity[f'{CO2.name}'] + self.carbon_intensity[Water.name] + \
            self.carbon_intensity[Electricity.name]

    def grad_co2_emissions_vs_resources_co2_emissions(self):
        '''
        Compute the gradient of global CO2 emissions vs resources CO2 emissions
        '''
        co2_needs = self.get_theoretical_CO2_needs()
        efficiency = self.configure_efficiency()
        return {
            CO2.name: np.identity(len(self.years)) * co2_needs / efficiency.values[:, np.newaxis],
        }

    def get_theoretical_CO2_needs(self):
        ''' 
        Get water needs in kg CO2 /kWh syngas
        1 mol of CO2 for 1 mol of CO and 1 mol of H2
        Warning : molar mass is in g/mol but we divide and multiply by one
        '''

        mol_CO2 = 1.0
        mol_COH2 = 1.0
        co2_data = CO2.data_energy_dict
        co2_needs = mol_CO2 * co2_data['molar_mass'] / \
                    (mol_COH2 * self.data_energy_dict['molar_mass'] *
                     self.data_energy_dict['calorific_value'])

        return co2_needs

    def get_theoretical_water_needs(self):
        ''' 
        Get water needs in kg water /kWh syngas
        1 mol of H2O for 1 mol of CO and 1 mol of H2
        Warning : molar mass is in g/mol but we divide and multiply by one
        '''

        mol_H2O = 1.0
        mol_COH2 = 1.0
        water_data = Water.data_energy_dict
        water_needs = mol_H2O * water_data['molar_mass'] / \
                      (mol_COH2 * self.data_energy_dict['molar_mass'] *
                       self.data_energy_dict['calorific_value'])

        return water_needs

    def get_oxygen_production(self):
        """
        Get dioxygen produced in kg with 1kwh of Syngas, 1 mol of O2 with 1 mol of Syngas(1 mol of CO + 1 mol of H2)
        """

        mol_O2 = 1.0
        mol_COH2 = 1.0
        oxygen_data = Dioxygen.data_energy_dict
        oxygen_production = mol_O2 * oxygen_data['molar_mass'] / \
                            (mol_COH2 * self.data_energy_dict['molar_mass'] *
                             self.data_energy_dict['calorific_value'])

        return oxygen_production

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """

        o2_production = self.get_oxygen_production()

        self.production_detailed[f'{Dioxygen.name} ({self.mass_unit})'] = o2_production / \
                                                                          self.data_energy_dict['calorific_value'] * \
                                                                          self.production_detailed[
                                                                              f'{SyngasTechno.energy_name} ({self.product_energy_unit})']

        # Consumption
        self.consumption_detailed[f'{CarbonCapture.name} ({self.mass_unit})'] = self.cost_details['CO2_needs'] * \
                                                                                self.production_detailed[
                                                                                    f'{SyngasTechno.energy_name} ({self.product_energy_unit})'] / \
                                                                                self.cost_details['efficiency']

        self.consumption_detailed[f'{Water.name} ({self.mass_unit})'] = self.cost_details['water_needs'] * \
                                                                        self.production_detailed[
                                                                            f'{SyngasTechno.energy_name} ({self.product_energy_unit})'] / \
                                                                        self.cost_details['efficiency']

        self.consumption_detailed[f'{Electricity.name} ({self.product_energy_unit})'] = \
            self.cost_details['elec_needs'] * \
            self.production_detailed[f'{SyngasTechno.energy_name} ({self.product_energy_unit})']

        # self.consumption[f'{hightemperatureheat.name} ({self.mass_unit})'] = self.cost_details['CO2_needs'] * \
        #      self.production[f'{SyngasTechno.energy_name} ({self.product_energy_unit})'] / \
        #      self.cost_details['efficiency']

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
