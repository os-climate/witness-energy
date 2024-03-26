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


class CrudeOil(BaseStream):
    name = ResourceGlossary.CrudeOilResource
    data_energy_dict = {'reference': 'engineeringtoolbox',
                        'maturity': 5,
                        'WACC': 0.1,
                        'CO2_per_use': 3.15,  # Same as kerosene ?
                        'CO2_per_use_unit': 'kg/kg',
                        'density': 980.0,  # at atmospheric pressure and 298K
                        'density_unit': 'kg/m^3',
                        'molar_mass': 170.0,  # Same as kerosene ?
                        'molar_mass_unit': 'g/mol',
                        'calorific_value': 10.83,  # for kerosene
                        'calorific_value_unit': 'kWh/kg',
                        'high_calorific_value': 11.61,  # for kerosene
                        'high_calorific_value_unit': 'kWh/kg'}
