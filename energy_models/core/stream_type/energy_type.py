'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2024/06/24 Copyright 2023 Capgemini

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
from energy_models.glossaryenergy import GlossaryEnergy


class EnergyType(BaseStream):
    """
    Class for energy production technology type
    """
    name = ''
    unit = 'TWh'
    data_energy_dict = {}

    def compute_ghg_emissions_per_use(self):
        for ghg_type in GlossaryEnergy.GreenHouseGases:
            self.outputs[f'{ghg_type}_per_use:{GlossaryEnergy.Years}'] = self.years
            self.outputs[f'{ghg_type}_per_use:{ghg_type}_per_use'] = self.zeros_array
            if f'{ghg_type}_per_use' in self.inputs['data_fuel_dict']:
                self.outputs[f'{ghg_type}_per_use:{ghg_type}_per_use'] = self.compute_ghg_per_use(ghg_type)

    def compute_ghg_per_use(self, ghg_type):

        if self.inputs['data_fuel_dict'][f'{ghg_type}_per_use_unit'] == 'kg/kg':
            ghg_type_per_use = self.inputs['data_fuel_dict'][f'{ghg_type}_per_use'] / \
                               self.inputs['data_fuel_dict']['high_calorific_value']
        elif self.inputs['data_fuel_dict'][f'{ghg_type}_per_use_unit'] == 'kg/kWh' or self.inputs['data_fuel_dict'][
            f'{ghg_type}_per_use_unit'] == 'Mt/TWh':
            ghg_type_per_use = self.inputs['data_fuel_dict'][f'{ghg_type}_per_use']
        else :
            raise Exception("ghg per use unit is not handled")
        return ghg_type_per_use
