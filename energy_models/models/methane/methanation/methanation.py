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
from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import GaseousHydrogen
from energy_models.core.stream_type.resources_models.water import Water
from energy_models.core.techno_type.base_techno_models.methane_techno import MethaneTechno


class Methanation(MethaneTechno):


    def compute_resources_needs(self):
        # in kg of CO2 for kWh of CH4
        self.cost_details[f'{CO2.name}_needs'] = self.get_theoretical_co2_needs() / self.cost_details['efficiency']
    def compute_cost_of_other_energies_usage(self):
        # Cost of H2 for 1 kg of CH4 (in kg), price is in $/kg
        self.cost_details[GaseousHydrogen.name] = list(
            self.prices[GaseousHydrogen.name] * self.cost_details['hydrogen_needs'] / self.cost_details['efficiency'])

    def compute_other_energies_needs(self):
        # in kWh of H2 for kWh of CH4
        self.cost_details['hydrogen_needs'] = self.get_theoretical_hydrogen_needs()


    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs to produce 1kg of CH4
        """

        super().compute_other_primary_energy_costs()

        return self.cost_details[GaseousHydrogen.name] + self.cost_of_resources_usage[CO2.name]

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices 
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        hydrogen_needs = self.get_theoretical_hydrogen_needs()
        efficiency = self.compute_efficiency()
        return {
            GaseousHydrogen.name: np.diag(hydrogen_needs / efficiency)
        }

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """

        # compute CH4 production in kWh

        # kg of H2O produced with 1kWh of CH4
        H2Oprod = self.get_h2o_production()

        # total H2O production
        self.production_detailed[f'{Water.name} ({self.mass_unit})'] = self.production_detailed[
                                                                           f'{MethaneTechno.energy_name} ({self.product_energy_unit})'] * \
                                                                       H2Oprod

        # Consumption
        self.consumption_detailed[f'{CarbonCapture.name} ({self.mass_unit})'] = self.cost_details[f'{CO2.name}_needs'] * \
                                                                                self.production_detailed[
                                                                                    f'{MethaneTechno.energy_name} ({self.product_energy_unit})']

        self.consumption_detailed[f'{GaseousHydrogen.name} ({self.product_energy_unit})'] = self.cost_details[
                                                                                                'hydrogen_needs'] * \
                                                                                            self.production_detailed[
                                                                                                f'{MethaneTechno.energy_name} ({self.product_energy_unit})'] / \
                                                                                            self.cost_details[
                                                                                                'efficiency']

    def compute_CO2_emissions_from_input_resources(self):
        '''
        Need to take into account  CO2 from hydrogen
        '''

        self.carbon_intensity[GaseousHydrogen.name] = self.energy_CO2_emissions[GaseousHydrogen.name] * \
                                                      self.cost_details['hydrogen_needs'] / \
                                                      self.cost_details['efficiency']
        self.carbon_intensity[f'{CO2.name}'] = self.resources_CO2_emissions[f'{CO2.name}'] * \
                                               self.cost_details[f'{CO2.name}_needs']

        return self.carbon_intensity[GaseousHydrogen.name] + self.carbon_intensity[f'{CO2.name}']

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
