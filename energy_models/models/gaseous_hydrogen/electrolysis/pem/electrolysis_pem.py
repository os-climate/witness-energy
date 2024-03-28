'''
Copyright 2022 Airbus SAS
Modifications on 2023/10/10-2023/11/16 Copyright 2023 Capgemini

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
from energy_models.core.stream_type.resources_models.dioxygen import Dioxygen
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
from energy_models.core.stream_type.resources_models.water import Water
from energy_models.core.techno_type.base_techno_models.gaseous_hydrogen_techno import GaseousHydrogenTechno


class ElectrolysisPEM(GaseousHydrogenTechno):
    """
    electrolysis class


    """

    PLATINUM_RESOURCE_NAME = ResourceGlossary.PlatinumResource

    def compute_resources_needs(self):
        self.cost_details[f"{ResourceGlossary.WaterResource}_needs"] = self.get_water_needs()

        self.cost_details[f'{self.PLATINUM_RESOURCE_NAME}_needs'] = self.get_theoretical_platinum_needs()

    def compute_cost_of_other_energies_usage(self):
        self.cost_details[Electricity.name] = self.cost_details['elec_needs'] * \
                                              self.prices[Electricity.name]
    
    def compute_other_energies_needs(self):
        # Efficiency ifor electrolysis means electric efficiency and is here to
        # compute the elec needs in kWh/kWh 1/efficiency
        self.cost_details['elec_needs'] = 1.0 / self.cost_details['efficiency']


    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs which depends on the technology 
        """
        super().compute_other_primary_energy_costs()

        return self.cost_details[Electricity.name] + self.cost_of_resources_usage[Water.name] + self.cost_of_resources_usage[self.PLATINUM_RESOURCE_NAME]

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices 
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        efficiency = self.compute_efficiency()

        return {Electricity.name: np.identity(len(self.years)) / efficiency.values,
                }

    def grad_price_vs_resources_price(self):
        '''
        Compute the gradient of global price vs resources prices
        '''
        water_needs = self.get_water_needs()
        platinum_needs = self.get_theoretical_platinum_needs()
        return {
            Water.name: np.identity(len(self.years)) * water_needs,
            self.PLATINUM_RESOURCE_NAME: np.identity(len(self.years)) * platinum_needs
        }

    def compute_CO2_emissions_from_input_resources(self):
        ''' 
        Need to take into account positive CO2 from methane and elec prod
        Carbon capture (Methane is not burned but transformed is not taken into account)
        '''

        self.carbon_intensity[Electricity.name] = self.energy_CO2_emissions[Electricity.name] * \
                                                  self.cost_details['elec_needs']
        self.carbon_intensity[Water.name] = self.resources_CO2_emissions[Water.name] * \
                                            self.cost_details[f"{ResourceGlossary.WaterResource}_needs"]
        self.carbon_intensity[self.PLATINUM_RESOURCE_NAME] = self.resources_CO2_emissions[self.PLATINUM_RESOURCE_NAME] * \
                                                             self.cost_details[f'{self.PLATINUM_RESOURCE_NAME}_needs']

        return self.carbon_intensity[Electricity.name] + self.carbon_intensity[Water.name] + self.carbon_intensity[
            self.PLATINUM_RESOURCE_NAME]

    def get_water_needs(self):
        ''' 
        Get water needs in kg Water /kWh H2
        1 mol of H20 for 1 mol of H2
        Warning : molar mass is in g/mol but we divide and multiply by one
        '''

        mol_H20 = 1.0
        mol_H2 = 1.0
        water_data = Water.data_energy_dict
        water_needs = mol_H20 * water_data['molar_mass'] / \
                      (mol_H2 * self.data_energy_dict['molar_mass'] *
                       self.data_energy_dict['calorific_value'])

        return water_needs

    def get_oxygen_produced(self):
        ''' 
        Get oxygen needs in kg O2 /kWh H2
        1 mol of O2 for 2 mol of H2
        Warning : molar mass is in g/mol but we divide and multiply by one
        '''

        mol_O2 = 1.0
        mol_H2 = 2.0
        oxygen_data = Dioxygen.data_energy_dict
        oxygen_needs = mol_O2 * oxygen_data['molar_mass'] / \
                       (mol_H2 * self.data_energy_dict['molar_mass'] *
                        self.data_energy_dict['calorific_value'])

        return oxygen_needs

    def get_theoretical_platinum_needs(self):
        """
        Get platinum needs in kg platinum /kWh H2
        
        https://www.energy.gov/sites/prod/files/2016/03/f30/At_A_GLANCE%20%28FCTO%29.pdf
        According to the Fuel Cell Technologies Office, 1g of platinum enables the production of 8K of H2

        Need to convert in kg/kWh ~ Mt/TWh
        """
        platinum_needs = self.techno_infos_dict['platinum_needs'] / 1000 / self.techno_infos_dict[
            'full_load_hours']  # kg of platinum needed for 1 kWh of H2

        return platinum_needs

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """

        o2_needs = self.get_oxygen_produced()
        self.production_detailed[f'O2 ({self.mass_unit})'] = o2_needs / \
                                                             self.data_energy_dict['calorific_value'] * \
                                                             self.production_detailed[
                                                                 f'{GaseousHydrogenTechno.energy_name} ({self.product_energy_unit})']

        # Consumption
        self.consumption_detailed[f'{Electricity.name} ({self.product_energy_unit})'] = self.cost_details[
                                                                                            'elec_needs'] * \
                                                                                        self.production_detailed[
                                                                                            f'{GaseousHydrogenTechno.energy_name} ({self.product_energy_unit})']  # in TWH

        self.consumption_detailed[f'{Water.name} ({self.mass_unit})'] = self.cost_details[f"{ResourceGlossary.WaterResource}_needs"] * \
                                                                        self.production_detailed[
                                                                            f'{GaseousHydrogenTechno.energy_name} ({self.product_energy_unit})']  # in Mt

        self.consumption_detailed[f'{self.PLATINUM_RESOURCE_NAME} ({self.mass_unit})'] = self.cost_details[
                                                                                             f'{self.PLATINUM_RESOURCE_NAME}_needs'] * \
                                                                                         self.production_detailed[
                                                                                             f'{GaseousHydrogenTechno.energy_name} ({self.product_energy_unit})']  # in Mt

        # Production
        # self.production[f'{lowheattechno.energy_name} ({self.product_energy_unit})'] = \
        #     self.consumption[f'{Electricity.name} ({self.product_energy_unit})'] \
        #     - self.production[f'{GaseousHydrogenTechno.energy_name} ({self.product_energy_unit})']  # in TWH
