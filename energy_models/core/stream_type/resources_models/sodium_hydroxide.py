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
from energy_models.glossaryenergy import GlossaryEnergy


class SodiumHydroxide(BaseStream):
    """Sodium hydroxide, also known as lye and caustic soda is an inorganic compound with the formula NaOH.
    It is used as a catalyst in the transesterifiction process to produce biodiesel"""
    name = GlossaryEnergy.SodiumHydroxideResource
    data_energy_dict = {'reference': 'https://en.wikipedia.org/wiki/Sodium_hydroxide',
                        'chemical_formula': 'NaOH',
                        'maturity': 5,

                        # 2.13g/cm3
                        'density': 2130.0,
                        'density_unit': 'kg/m^3',

                        'molar_mass': 39.997,
                        'molar_mass_unit': 'g/mol',
                        }
