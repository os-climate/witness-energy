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
from energy_models.glossaryenergy import GlossaryEnergy


class Ethanol(EnergyType):
    # Ethanol (CH3CH2OH) is a renewable fuel made from various plant materials collectively known as "biomass."
    # Source: US Department of Energy (https://afdc.energy.gov/fuels/ethanol_fuel_basics.html)
    name = f'{GlossaryEnergy.fuel}.{GlossaryEnergy.ethanol}'
    short_name = 'ethanol'
    default_techno_list = ['BiomassFermentation']
    data_energy_dict = {'maturity': 5,

                        # Engineering ToolBox, (2009). Combustion of Fuels - Carbon Dioxide Emission. [online]
                        # Available at: https://www.engineeringtoolbox.com/co2-emission-fuels-d_1085.html
                        # [Accessed 09/05/2022]
                        'CO2_per_use': 1.91,
                        'CO2_per_use_unit': 'kg/kg',

                        'density': 789,
                        'density_unit': 'kg/m^3',

                        # CH3CH2OH
                        'molar_mass': 46.069,
                        'molar_mass_unit': 'g/mol',

                        # Engineering ToolBox, (2009). Ethanol Dynamic and Kinetic Viscosity Calculator. [online]
                        # https://www.engineeringtoolbox.com/ethanol-dynamic-kinematic-viscosity-temperature-pressure-d_2071.html
                        # [Accessed 09/05/2022]
                        # viscosity at 40 C
                        'viscosity': 1.056E-6,
                        'viscosity_unit': 'mm2/s',

                        'cetane_number': 54.0,

                        # Engineering ToolBox, (2009). Higher and Lower Calorific Values. [online]
                        # https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html
                        # [Accessed 09/05/2022]
                        'lower_heating_value': 26.7,
                        'lower_heating_value_unit': 'MJ/kg',
                        'higher_heating_value': 29.7,
                        'higher_heating_value_unit': 'MJ/kg',

                        # Engineering ToolBox, (2003). Fuels - Higher and Lower Calorific Values. [online]
                        # Available at:
                        # https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html
                        'calorific_value': 7.42,
                        'calorific_value_unit': 'kWh/kg',
                        'high_calorific_value': 8.25,
                        'high_calorific_value_unit': 'kWh/kg'

                        }
