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


from energy_models.core.stream_type.resources_models.dioxygen import Dioxygen
from energy_models.core.stream_type.resources_models.water import Water
from energy_models.core.techno_type.base_techno_models.gaseous_hydrogen_techno import (
    GaseousHydrogenTechno,
)
from energy_models.glossaryenergy import GlossaryEnergy


class ElectrolysisPEM(GaseousHydrogenTechno):
    """
    electrolysis class
    """
    def compute_resources_needs(self):
        self.outputs[f"{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.WaterResource}_needs"] = self.get_water_needs()
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.PlatinumResource}_needs'] = self.get_theoretical_platinum_needs()

    def compute_other_streams_needs(self):
        # Efficiency ifor electrolysis means electric efficiency and is here to
        # compute the elec needs in kWh/kWh 1/efficiency
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.electricity}_needs'] = 1.0 / self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

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
                      (mol_H2 * self.inputs['data_fuel_dict']['molar_mass'] *
                       self.inputs['data_fuel_dict']['calorific_value'])

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
                       (mol_H2 * self.inputs['data_fuel_dict']['molar_mass'] *
                        self.inputs['data_fuel_dict']['calorific_value'])

        return oxygen_needs

    def get_theoretical_platinum_needs(self):
        """
        Get platinum needs in kg platinum /kWh H2
        
        https://www.energy.gov/sites/prod/files/2016/03/f30/At_A_GLANCE%20%28FCTO%29.pdf
        According to the Fuel Cell Technologies Office, 1g of platinum enables the production of 8K of H2

        Need to convert in kg/kWh ~ Mt/TWh
        """
        platinum_needs = self.inputs['techno_infos_dict']['platinum_needs'] / 1000 / self.inputs['techno_infos_dict'][
            'full_load_hours']  # kg of platinum needed for 1 kWh of H2

        return platinum_needs

    def compute_byproducts_production(self):
        o2_needs = self.get_oxygen_produced()
        self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:O2 ({GlossaryEnergy.mass_unit})'] = o2_needs / \
                                                             self.inputs['data_fuel_dict']['calorific_value'] * \
                                                             self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:'
                                                                 f'{GaseousHydrogenTechno.stream_name} ({self.product_unit})']
        # Production
        # self.production[f'{lowheattechno.stream_name} ({self.product_unit})'] = \
        #     self.consumption[f'{GlossaryEnergy.electricity} ({self.product_unit})'] \
        #     - self.production[f'{GaseousHydrogenTechno.stream_name} ({self.product_unit})']  # in TWH
