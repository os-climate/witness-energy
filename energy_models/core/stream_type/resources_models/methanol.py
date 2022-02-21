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


class Methanol(BaseStream):
    """Methanol, also known as methyl alcohol amongst other names, is a chemical with the formula CH3OH (a methyl group linked to a hydroxyl group, often abbreviated MeOH).
    It is a light, volatile, colourless, flammable liquid with a distinctive alcoholic odour similar to that of ethanol."""
    name = 'Methanol'
    data_energy_dict = {
        'reference': 'https://en.wikipedia.org/wiki/Methanol',
        'chemical_formula': 'CH3OH',
        'maturity': 5,

        # Density	0.792 g/cm3
        'density': 792,
        'density_unit': 'kg/m^3',

        'molar_mass': 32.04,
        'molar_mass_unit': 'g/mol',

        # https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html
        'calorific_value': 5.54,
        'calorific_value_unit': 'kWh/kg',
        'high_calorific_value': 6.39,
        'high_calorific_value_unit': 'kWh/kg'

        # price https://www.methanol.org/methanol-price-supply-demand/

    }
