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
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary


class Glycerol(BaseStream):
    """Glycerol also called glycerine or glycerin) is a simple polyol compound.
    It is a colorless, odorless, viscous liquid that is sweet-tasting and non-toxic."""
    name = ResourceGlossary.Glycerol['name']
    data_energy_dict = {
        'reference': 'https://en.wikipedia.org/wiki/Glycerol',
        'chemical_formula': 'C3H8O3',
        'maturity': 5,

        # Density	1.261 g/cm3
        'density': 1261,
        'density_unit': 'kg/m^3',

        'molar_mass': 92.094,
        'molar_mass_unit': 'g/mol',

        # Glycerol reveals a relatively high calorific value (16.1–22.6 MJ/kg depending on the raw material used to biodiesel production).
        # https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html
        'calorific_value': 5.28,
        'calorific_value_unit': 'kWh/kg',
        'high_calorific_value': 5.28,
        'high_calorific_value_unit': 'kWh/kg'

    }
