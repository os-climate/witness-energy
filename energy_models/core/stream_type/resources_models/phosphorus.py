'''
Copyright 2024 Capgemini

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
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary


class Phosphorus(BaseStream):
    name = ResourceGlossary.Phosphorus['name']
    data_energy_dict = {
        'maturity': 10,
        'WACC': 0.1,
        'molar_mass': 30,
        'molar_mass_unit': 'g/mol',
        'calorific_value': 2.38,
        'calorific_value_unit': 'kWh/kg',
    }
