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


class LiquefiedPetroleumGas(EnergyType):
    """
    hydrocarbon gas liquid. mix of 48% propane, 50% butane, 2% pentane
    """

    name = 'liquefied_petroleum_gas'
    data_energy_dict = {'maturity': 5,
                        'WACC': 0.1,
                        # ADEME, CO2 per kg combustion in Europe = 3.15
                        # https://www.bilans-ges.ademe.fr/documentation/UPLOAD_DOC_EN/index.htm?new_liquides.htm
                        'CO2_per_use': 2.82,
                        'CO2_per_use_unit': 'kg/kg',
                        'cost_now': 0.35,  # around half of kero_price
                        'cost_now_unit': '$/kg',
                        'density': 535.66,  # weighted average of propane/butane/pentane
                        'density_unit': 'kg/m^3',
                        'molar_mass': 51.6,  # weighted average of propane/butane/pentane
                        'molar_mass_unit': 'g/mol',
                        # Engineering ToolBox, (2003). Fuels - Higher and Lower Calorific Values. [online]
                        # Available at: https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html
                        # [Accessed 16/12/2021].
                        'calorific_value': 12.8,  # weighted average of propane/butane/pentane
                        'calorific_value_unit': 'kWh/kg',
                        'high_calorific_value': 12.83,  # weighted average of propane/butane/pentane
                        'high_calorific_value_unit': 'kWh/kg'}
