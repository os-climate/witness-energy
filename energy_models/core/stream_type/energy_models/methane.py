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


class Methane(EnergyType):
    name = 'methane'
    default_techno_list = ['Methanation', 'UpgradingBiogas', 'FossilGas']
    data_energy_dict = {'maturity': 5,
                        'WACC': 0.1,
                        # Engineering ToolBox, (2009).
                        # Combustion of Fuels - Carbon Dioxide Emission. [online]
                        # Available at: https://www.engineeringtoolbox.com/co2-emission-fuels-d_1085.html
                        #[Accessed 17 12 2021].
                        'CO2_per_use': 2.75,
                        'CO2_per_use_unit': 'kg/kg',
                        'NOx_per_energy': 0.1,
                        'NOX_per_energy_unit': 'yy',
                        'density': 0.657,
                        'density_unit': 'kg/m^3',
                        'molar_mass': 16.04,
                        'molar_mass_unit': 'g/mol',
                        # Engineering ToolBox, (2003).
                        # Fuels - Higher and Lower Calorific Values. [online]
                        # Available at: https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html
                        #[Accessed 17 12 2021].
                        'calorific_value': 13.9,
                        'calorific_value_unit': 'kWh/kg',
                        'high_calorific_value': 15.4,
                        'high_calorific_value_unit': 'kWh/kg',
                        # Rokuhei Fukui, Carl Greenfield, Katie Pogue, Bob van der Zwaan,
                        # Experience curve for natural gas production by hydraulic fracturing,
                        # Energy Policy, Volume 105, 2017, Pages 263-268, ISSN 0301-4215,
                        # https://doi.org/10.1016/j.enpol.2017.02.027.
                        'learning_rate': 0.13,
                        }
