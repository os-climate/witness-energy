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


class UltraLowSulfurDiesel(EnergyType):
    """
    """

    name = 'ultra_low_sulfur_diesel'
    data_energy_dict = {'maturity': 5,
                        'WACC': 0.1,
                        # Engineering ToolBox, (2009). Combustion of Fuels - Carbon Dioxide Emission.
                        # [online] Available at: https://www.engineeringtoolbox.com/co2-emission-fuels-d_1085.html
                        # [Accessed 17 12 2021]. Value for diesel
                        'CO2_per_use': 3.13,
                        'CO2_per_use_unit': 'kg/kg',
                        # Source: U.S. Energy Information Administration (13/12/2021)
                        # 2.6 dollar/gallon * (1/3.35) gallon/kg
                        'cost_now': 0.35,  #
                        'cost_now_unit': '$/kg',
                        'density': 876,  #
                        'density_unit': 'kg/m^3',
                        'molar_mass': 108.099,  #
                        'molar_mass_unit': 'g/mol',
                        # Engineering ToolBox, (2003). Fuels - Higher and Lower Calorific Values.
                        # [online] Available at: https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html
                        # [Accessed 17/12/2021]. Value for diesel
                        'calorific_value': 11.86,  #
                        'calorific_value_unit': 'kWh/kg',
                        'high_calorific_value': 11.86,  #
                        'high_calorific_value_unit': 'kWh/kg'}
