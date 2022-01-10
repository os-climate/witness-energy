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

from energy_models.core.stream_type.base_stream import BaseStream


class EnergyType(BaseStream):
    """
    Class for energy production technology type
    """
    name = ''
    unit = 'TWh'
    data_energy_dict = {}

    def __init__(self, name):

        BaseStream.__init__(self, name)

        self.carbon_tax = None

    def configure(self, inputs_dict):
        self.configure_parameters(inputs_dict)
        self.configure_parameters_update(inputs_dict)

    def configure_parameters(self, inputs_dict):
        '''
        Configure at init
        '''
        self.subelements_list = inputs_dict['technologies_list']

        BaseStream.configure_parameters(self, inputs_dict)

    def configure_parameters_update(self, inputs_dict):
        '''
        Configure before each run
        '''
        self.carbon_tax = inputs_dict['CO2_taxes']
        BaseStream.configure_parameters_update(self, inputs_dict)

        for element in self.subelements_list:
            self.sub_carbon_emissions[element] = inputs_dict[f'{element}.CO2_emissions'][element]

    def compute_carbon_emissions(self):
        '''
        Compute the CO2 emissions in kg/kWh of the total depending on its subelements
        '''
        self.total_carbon_emissions[self.name] = 0.
        for element in self.subelements_list:

            self.total_carbon_emissions[self.name] += self.sub_carbon_emissions[element] * \
                self.mix_weights[element] / 100.0

        return self.total_carbon_emissions

    def compute_co2_per_use(self, data_energy_dict):
        self.co2_per_use['CO2_per_use'] = 0.0
        if 'CO2_per_use' in self.data_energy_dict:
            if data_energy_dict['CO2_per_use_unit'] == 'kg/kg':
                self.co2_per_use['CO2_per_use'] = data_energy_dict['CO2_per_use'] / \
                    data_energy_dict['high_calorific_value']
            elif data_energy_dict['CO2_per_use_unit'] == 'kg/kWh':
                self.co2_per_use['CO2_per_use'] = data_energy_dict['CO2_per_use']

        return self.co2_per_use
