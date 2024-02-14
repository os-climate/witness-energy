'''
Copyright 2022 Airbus SAS
Modifications on 2024/02/01 Copyright 2024 Capgemini
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


class LiquidHydrogen(EnergyType):
    """
    """
    name = f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.liquid_hydrogen}'
    short_name = GlossaryEnergy.liquid_hydrogen
    default_techno_list = ['HydrogenLiquefaction']
    unit = 'TWh'
    data_energy_dict = {'maturity': 5,
                        'WACC': 0.1,
                        'CO2_per_use': 0.0,
                        'CO2_per_use_unit': 'kg/kg',
                        # 'cost_now': 14.24,  #
                        # 'cost_now_unit': '$/kg',
                        'density': 71.0,  #
                        'density_unit': 'kg/m^3',
                        'molar_mass': 2.016,  #
                        'molar_mass_unit': 'g/mol',
                        # Engineering ToolBox, (2003). Fuels - Higher and Lower Calorific Values. [online]
                        # Available at: https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html
                        # [Accessed 16/12/2021].
                        'calorific_value': 33.3,
                        'calorific_value_unit': 'kWh/kg',
                        'high_calorific_value': 39.4,
                        'high_calorific_value_unit': 'kWh/kg'}
