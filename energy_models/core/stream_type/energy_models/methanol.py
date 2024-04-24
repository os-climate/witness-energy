'''
Copyright 2022 Airbus SAS
Modifications on 2024/01/31-2024/02/01 Copyright 2024 Capgemini
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
from energy_models.core.stream_type.energy_type import EnergyType
from energy_models.glossaryenergy import GlossaryEnergy


class Methanol(EnergyType):
    # Methanol (CH3OH) is the simplest alcohol, and is also known as methyl alcohol.
    # It is mostly used in the production of chemicals, as well as in the manufacturing of
    # polyester fibers, acrylic plastics, and various pharmaceuticals.
    # It can also be used as an alternative fuel through combustion reaction
    # Source: J.M.K.C. Donev et al. (2018). Energy Education - Methanol [Online].
    # Available: https://energyeducation.ca/encyclopedia/Methanol. [Accessed: June 20, 2022].
    name = f'{GlossaryEnergy.fuel}.methanol'
    short_name = 'methanol'
    default_techno_list = ['CO2Hydrogenation']
    data_energy_dict = {'maturity': 5,

                        # Engineering ToolBox, (2009).Combustion of Fuels - Carbon Dioxide Emission.[online]
                        # Available at: (https://www.engineeringtoolbox.com/co2-emission-fuels-d_1085.html)
                        # [Accessed 20/06/2022].
                        GlossaryEnergy.CO2PerUse: 1.37,
                        'CO2_per_use_unit': 'kg/kg',

                        'density': 792,
                        'density_unit': 'kg/m^3',

                        # CH3OH
                        'molar_mass': 32.04,
                        'molar_mass_unit': 'g/mol',

                        # Engineering ToolBox, (2018). Methanol - Dynamic and Kinematic Viscosity vs. Temperature and Pressure. [online]
                        # Available at: (https://www.engineeringtoolbox.com/methanol-dynamic-kinematic-viscosity-temperature-pressure-d_2093.html)
                        # [Accessed 20/06/2022].
                        # viscosity at 50 C
                        'viscosity': 0.5142,
                        'viscosity_unit': 'mm2/s',

                        # Engineering ToolBox, (2009). Higher and Lower Calorific Values. [online]
                        # https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html
                        # [Accessed 20/06/2022]
                        'calorific_value': 5.54,
                        'calorific_value_unit': 'kWh/kg',
                        'high_calorific_value': 6.39,
                        'high_calorific_value_unit': 'kWh/kg'
                        }
