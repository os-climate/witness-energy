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
from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.core.techno_type.base_techno_models.methane_techno import MethaneTechno
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import GaseousHydrogen
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.ressources_models.water import Water

import numpy as np


class Methanation(MethaneTechno):

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs to produce 1kg of CH4
        """

        # in kWh of H2 for kWh of CH4
        self.cost_details['hydrogen_needs'] = self.get_theoretical_hydrogen_needs()

        # in kg of CO2 for kWh of CH4
        self.cost_details['dioxide_needs'] = self.get_theoretical_co2_needs()

        # Cost of H2 for 1 kg of CH4 (in kg), price is in $/kg
        self.cost_details[GaseousHydrogen.name] = list(
            self.prices[GaseousHydrogen.name] * self.cost_details['hydrogen_needs'] / self.cost_details['efficiency'])

        # Cost of CO2 for 1 kg of CH4 (in kg), price is in $/kg
        self.cost_details[CO2.name] = list(self.ressources_prices[CO2.name] * self.cost_details['dioxide_needs'] /
                                           self.cost_details['efficiency'])

        # cost to produce 1Kwh of methane
        return self.cost_details[GaseousHydrogen.name] + self.cost_details[CO2.name]

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices 
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        CO2_needs = self.get_theoretical_co2_needs()
        hydrogen_needs = self.get_theoretical_hydrogen_needs()
        efficiency = self.configure_efficiency()
        return {
            GaseousHydrogen.name: np.identity(
                len(self.years)) * hydrogen_needs / efficiency[:, np.newaxis]
        }

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """

        # compute CH4 production in kWh
        self.compute_primary_energy_production()

        # kg of H2O produced with 1kWh of CH4
        H2Oprod = self.get_h2o_production()

        # total H2O production
        self.production[f'{Water.name} ({self.mass_unit})'] = self.production[f'{MethaneTechno.energy_name} ({self.product_energy_unit})'] * \
            H2Oprod

        # Consumption
        self.consumption[f'{CarbonCapture.name} ({self.mass_unit})'] = self.cost_details['dioxide_needs'] * \
            self.production[f'{MethaneTechno.energy_name} ({self.product_energy_unit})'] / \
            self.cost_details['efficiency']

        self.consumption[f'{GaseousHydrogen.name} ({self.product_energy_unit})'] = self.cost_details['hydrogen_needs'] * \
            self.production[f'{MethaneTechno.energy_name} ({self.product_energy_unit})'] / \
            self.cost_details['efficiency']

    def compute_CO2_emissions_from_input_ressources(self):
        '''
        Need to take into account  CO2 from hydrogen
        '''

        self.carbon_emissions[f'{GaseousHydrogen.name}'] = self.energy_CO2_emissions[f'{GaseousHydrogen.name}'] * \
            self.cost_details['hydrogen_needs'] / \
            self.cost_details['efficiency']

        return self.carbon_emissions[f'{GaseousHydrogen.name}']

    def get_h2o_production(self):
        """
        Get water produced when producing 1kWh of CH4
        """

        # water created when producing 1kg of CH4
        mol_H20 = 2
        mol_CH4 = 1.0
        water_data = Water.data_energy_dict
        production_for_1kg = mol_H20 * \
            water_data['molar_mass'] / \
            (mol_CH4 * self.data_energy_dict['molar_mass']
             * self.data_energy_dict['calorific_value'])

        return production_for_1kg

    def get_theoretical_hydrogen_needs(self):
        ''' 
        Get hydrogen needs in kWhH2 /kWh CH4
        4 mol of H2 for 1 mol of CH4
        Warning : molar mass is in g/mol but we divide and multiply by one
        '''

        mol_H2 = 4.0
        mol_CH4 = 1.0
        h2_data = GaseousHydrogen.data_energy_dict
        h2_needs = mol_H2 * h2_data['molar_mass'] * h2_data['calorific_value'] / \
            (mol_CH4 * self.data_energy_dict['molar_mass'] *
             self.data_energy_dict['calorific_value'])

        return h2_needs

    def get_theoretical_co2_needs(self):
        ''' 
        Get hydrogen needs in kWhH2 /kWh CH4
        4 mol of H2 for 1 mol of CH4
        Warning : molar mass is in g/mol but we divide and multiply by one
        '''

        mol_CO2 = 1.0
        mol_CH4 = 1.0
        co2_data = CO2.data_energy_dict
        co2_needs = mol_CO2 * co2_data['molar_mass'] / \
            (mol_CH4 * self.data_energy_dict['molar_mass'] *
             self.data_energy_dict['calorific_value'])

        return co2_needs

    def get_theoretical_co2_prod(self, unit='kg/kWh'):
        co2_needs = self.get_theoretical_co2_needs()

        if unit == 'kg/kWh':
            co2_prod = -co2_needs
        elif unit == 'kg/kg':
            co2_prod = -co2_needs * self.data_energy_dict['calorific_value']

        return co2_prod
