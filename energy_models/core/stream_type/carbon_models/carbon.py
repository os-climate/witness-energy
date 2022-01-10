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


class Carbon(BaseStream):
    name = 'carbon'
    data_energy_dict = {'maturity': 5,
                        'WACC': 0.1,
                        'CO2_per_use': 44.01 / 12.0,
                        'CO2_per_use_unit': 'kg/kg',
                        'density': 2267.0,
                        'density_unit': 'kg/m^3',
                        'molar_mass': 12.011,
                        'molar_mass_unit': 'g/mol',
                        'calorific_value': 0.0,
                        'calorific_value_unit': 'kWh/kg',
                        'high_calorific_value': 0.0,
                        'high_calorific_value_unit': 'kWh/kg'}
