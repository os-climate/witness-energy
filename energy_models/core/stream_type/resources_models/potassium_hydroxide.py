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


class PotassiumHydroxide(BaseStream):
    """Potassium hydroxide is an inorganic compound with the formula KOH, and is commonly called caustic potash.
    It is used as a catalyst in the transesterifiction process to produce biodiesel"""
    name = 'Potassium_Hydroxyde'
    data_energy_dict = {'reference': 'https://en.wikipedia.org/wiki/Potassium_hydroxide',
                        'chemical_formula': 'KOH',
                        'maturity': 5,

                        # 2.13g/cm3
                        'density': 2044.0,
                        'density_unit': 'kg/m^3',

                        'molar_mass': 56.11,
                        'molar_mass_unit': 'g/mol',
                        }
