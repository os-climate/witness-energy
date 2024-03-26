'''
Copyright 2022 Airbus SAS
Modifications on 26/03/2024 Copyright 2024 Capgemini

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


class Water(BaseStream):
    name = ResourceGlossary.WaterResource
    data_energy_dict = {'reference': '',
                        'maturity': 5,
                        'density': 997.0,
                        'density_unit': 'kg/m^3',
                        'molar_mass': 18.01528,
                        'molar_mass_unit': 'g/mol',
                        'calorific_value': 0.67,
                        'calorific_value_unit': 'kWh/kg',
                        'high_calorific_value': 0.67,
                        'high_calorific_value_unit': 'kWh/kg',
                        # industrial water use :
                        # https://www.pub.gov.sg/watersupply/waterprice
                        'cost_now': 1.5,
                        'cost_now_unit': '$/t'}
