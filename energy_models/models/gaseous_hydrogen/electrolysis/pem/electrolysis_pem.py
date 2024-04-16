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
from energy_models.glossaryenergy import GlossaryEnergy


class ElectrolysisPEM(GaseousHydrogenTechno):
    """
    electrolysis class


    """

    PLATINUM_RESOURCE_NAME = ResourceGlossary.PlatinumResource

    def compute_resources_needs(self):
        self.cost_details[f"{ResourceGlossary.WaterResource}_needs"] = self.get_water_needs()

        self.cost_details[f'{self.PLATINUM_RESOURCE_NAME}_needs'] = self.get_theoretical_platinum_needs()
    def compute_other_energies_needs(self):
        # Efficiency ifor electrolysis means electric efficiency and is here to
        # compute the elec needs in kWh/kWh 1/efficiency
        self.cost_details[f'{GlossaryEnergy.electricity}_needs'] = 1.0 / self.cost_details['efficiency']


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

    def compute_production(self):
        o2_needs = self.get_oxygen_produced()
        self.production_detailed[f'O2 ({self.mass_unit})'] = o2_needs / \
                                                             self.data_energy_dict['calorific_value'] * \
                                                             self.production_detailed[
                                                                 f'{GaseousHydrogenTechno.energy_name} ({self.product_energy_unit})']
        # Production
        # self.production[f'{lowheattechno.energy_name} ({self.product_energy_unit})'] = \
        #     self.consumption[f'{Electricity.name} ({self.product_energy_unit})'] \
        #     - self.production[f'{GaseousHydrogenTechno.energy_name} ({self.product_energy_unit})']  # in TWH

    def compute_consumption(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """


        # Consumption
        self.consumption_detailed[f'{Electricity.name} ({self.product_energy_unit})'] = self.cost_details[
                                                                                            f'{GlossaryEnergy.electricity}_needs'] * \
                                                                                        self.production_detailed[
                                                                                            f'{GaseousHydrogenTechno.energy_name} ({self.product_energy_unit})']  # in TWH

        self.consumption_detailed[f'{Water.name} ({self.mass_unit})'] = self.cost_details[f"{ResourceGlossary.WaterResource}_needs"] * \
                                                                        self.production_detailed[
                                                                            f'{GaseousHydrogenTechno.energy_name} ({self.product_energy_unit})']  # in Mt

        self.consumption_detailed[f'{self.PLATINUM_RESOURCE_NAME} ({self.mass_unit})'] = self.cost_details[
                                                                                             f'{self.PLATINUM_RESOURCE_NAME}_needs'] * \
                                                                                         self.production_detailed[
                                                                                             f'{GaseousHydrogenTechno.energy_name} ({self.product_energy_unit})']  # in Mt
