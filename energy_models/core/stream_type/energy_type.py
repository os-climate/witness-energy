'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2023/11/09 Copyright 2023 Capgemini

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
import pandas as pd

from climateeconomics.core.core_emissions.ghg_emissions_model import GHGEmissions
from energy_models.core.stream_type.base_stream import BaseStream
from energy_models.glossaryenergy import GlossaryEnergy


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
        self.data_energy_dict_input = None

    def configure(self, inputs_dict):
        self.configure_parameters(inputs_dict)
        self.configure_parameters_update(inputs_dict)

    def configure_parameters(self, inputs_dict):
        '''
        Configure at init
        '''
        self.subelements_list = inputs_dict[GlossaryEnergy.techno_list]

        BaseStream.configure_parameters(self, inputs_dict)

    def configure_parameters_update(self, inputs_dict):
        '''
        Configure before each run
        '''
        self.carbon_tax = inputs_dict[GlossaryEnergy.CO2TaxesValue]
        BaseStream.configure_parameters_update(self, inputs_dict)
        self.data_energy_dict_input = inputs_dict['data_fuel_dict']
        for element in self.subelements_list:
            self.sub_carbon_emissions[element] = inputs_dict[f'{element}.{GlossaryEnergy.CO2EmissionsValue}'][element]

    def compute_carbon_emissions(self):
        '''
        Compute the CO2 emissions in kg/kWh of the total depending on its subelements
        '''
        self.total_carbon_emissions[self.name] = 0.
        for element in self.subelements_list:

            self.total_carbon_emissions[self.name] += self.sub_carbon_emissions[element] * \
                self.mix_weights[element] / 100.0

        return self.total_carbon_emissions

    def compute_ghg_emissions_per_use(self):
        ghg_dict = {}
        for ghg_type in GHGEmissions.GHG_TYPE_LIST:
            ghg_dict[f'{ghg_type}_per_use'] = pd.DataFrame(
                {GlossaryEnergy.Years: self.years})
            ghg_dict[f'{ghg_type}_per_use'][f'{ghg_type}_per_use'] = 0.0
            if f'{ghg_type}_per_use' in self.data_energy_dict:
                ghg_dict[f'{ghg_type}_per_use'][f'{ghg_type}_per_use'] = self.compute_ghg_per_use(
                    ghg_type)

        return ghg_dict

    def compute_ghg_per_use(self, ghg_type):

        if self.data_energy_dict_input[f'{ghg_type}_per_use_unit'] == 'kg/kg':
            ghg_type_per_use = self.data_energy_dict_input[f'{ghg_type}_per_use'] / \
                self.data_energy_dict_input['high_calorific_value']
        elif self.data_energy_dict_input[f'{ghg_type}_per_use_unit'] == 'kg/kWh' or self.data_energy_dict_input[f'{ghg_type}_per_use_unit'] == 'Mt/TWh':
            ghg_type_per_use = self.data_energy_dict_input[f'{ghg_type}_per_use']

        return ghg_type_per_use
