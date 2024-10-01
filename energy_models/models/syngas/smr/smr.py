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


from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.resources_models.water import Water
from energy_models.core.techno_type.base_techno_models.syngas_techno import SyngasTechno
from energy_models.glossaryenergy import GlossaryEnergy


class SMR(SyngasTechno):
    syngas_COH2_ratio = 1.0 / 3.0 * 100.0

    def compute_resources_needs(self):
        # need in kwh to produce 1kwh of syngas
        self.cost_details[f'{Water.name}_needs'] = self.get_theoretical_water_needs() / self.cost_details['efficiency']

    def compute_other_streams_needs(self):
        self.cost_details[f'{GlossaryEnergy.electricity}_needs'] = self.get_electricity_needs()
        # need in kg to produce 1kwh of syngas
        self.cost_details[f'{Methane.name}_needs'] = self.get_theoretical_CH4_needs() / self.cost_details['efficiency']


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

    def compute_byproducts_production(self):
        # self.production[f'{highheattechno.energy_name} ({self.product_unit})'] = \
        #     self.techno_infos_dict['high_heat_production'] * \
        #     self.production[f'{SyngasTechno.energy_name} ({self.product_unit})']
        pass
