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


class Monotethanolamine(BaseStream):
    """Monoethanolamine(MEA) is an amine molecule used in amine scrubbing technology"""
    name = 'Monoethanolamine'
    data_energy_dict = {'reference': 'https://en.wikipedia.org/wiki/Ethanolamine',
                        'chemical_formula': 'C2H7NO',
                        'maturity': 5,
                        'density': 1.0117,
                        'density_unit': 'kg/m^3',

                        'molar_mass': 61.084,
                        'molar_mass_unit': 'g/mol',
                        }
