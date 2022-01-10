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


class Fossil(EnergyType):
    name = 'fossil'
    data_energy_dict = {'maturity': 5,
                        'WACC': 0.1,
                        'CO2_per_use': 2.32,  # mean of CO2 per use of fossil energies
                        'CO2_per_use_unit': 'kg/kg',
                        'NOx_per_energy': 0.1,
                        'NOX_per_energy_unit': 'yy',

                        'cost_now': 0.76,
                        'cost_now_unit': '$/kg',
                        'density': 821.0,  # at atmospheric pressure and 298K
                        'density_unit': 'kg/m^3',
                        'molar_mass': 170.0,
                        'molar_mass_unit': 'g/mol',
                        'calorific_value': 11.9,
                        'calorific_value_unit': 'kWh/kg',
                        'high_calorific_value': 12.83,
                        'high_calorific_value_unit': 'kWh/kg',
                        'learning_rate': 0.25,
                        'produced_energy': 4477.212,
                        # or energy industry own use (sum of crude oil
                        # extraction and refinery)
                        'direct_energy': 210.457,
                        'total_final_consumption': 3970.182,  # for oil products
                        }
