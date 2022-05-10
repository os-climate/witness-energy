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
from energy_models.core.stream_type.energy_type import EnergyType


class HydrotreatedOilFuel(EnergyType):
    """
    Vegetable oil can be used as an alternative fuel in diesel engines and in heating oil burners. When vegetable
    oil is used directly as a fuel, in either modified or unmodified equipment, it is referred to as straight
    vegetable oil (SVO) or pure plant oil (PPO). Conventional diesel engines can be modified to help ensure that
    the viscosity of the vegetable oil is low enough to allow proper atomization of the fuel. This prevents
    incomplete combustion, which would damage the engine by causing a build-up of carbon. Straight vegetable
    oil can also be blended with conventional diesel or processed into biodiesel, HVO or bioliquids for use
    under a wider range of conditions. (Source: https://en.wikipedia.org/wiki/Vegetable_oil_fuel)
    """
    name = 'fuel.hydrotreated_oil_fuel'
    short_name = 'hydrotreated_oil_fuel'
    default_techno_list = ['HefaDecarboxylation', 'HefaDeoxygenation']
    data_energy_dict = {'maturity': 5,
                        # Ref: The swedish knowledge centre for renewable transportation fuels (f3)
                        # https://f3centre.se/en/fact-sheets/hefa-hvo-hydroprocessed-esters-and-fatty-acids/
                        'density': 780,
                        'density_unit': 'kg/m^3',
                        'cetane_number': 70,
                        # Aatola, H., Larmi, M., Sarjovaara, T. and Mikkonen, S., 2009. Hydrotreated Vegetable Oil (HVO) as a Renewable Diesel Fuel:
                        # Trade-off between NOx, Particulate Emission, and Fuel Consumption of a Heavy Duty Engine.
                        # SAE International Journal of Engines, 1(1), pp.1251-1262.
                        # https://www.etipbioenergy.eu/images/SAE_Study_Hydrotreated_Vegetable_Oil_HVO_as_a_Renewable_Diesel_Fuel.pdf
                        'CO2_per_use': 3.15,
                        'CO2_per_use_unit': 'kg/kg',
                        'lower_heating_value': 44,
                        'lower_heating_value_unit': 'MJ/kg',
                        'high_heating_value': 47.27,
                        'high_heating_value_unit': 'MJ/kg',
                        'calorific_value': 44 / 3.6,
                        'calorific_value_unit': 'kWh/kg',
                        'high_calorific_value': 47.27 / 3.6,
                        'high_calorific_value_unit': 'kWh/kg',

                        # C17H36 --> hydrogenation + deoxygenation
                        # 'molar_mass': 240.47,
                        # 'molar_mass_unit': 'g/mol',

                        # C18H38 --> hydrogenation + decarboxylation
                        # 'molar_mass': 254.49,
                        # 'molar_mass_unit': 'g/mol',

                        'molar_mass': (254.49 + 240.47) / 2,
                        'molar_mass_unit': 'g/mol',
                        }
