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


class Gasoline(EnergyType):
    name = GlossaryEnergy.gasoline
    data_energy_dict = {'maturity': 5,
                        'WACC': 0.1,
                        # Engineering ToolBox, (2009).
                        # Combustion of Fuels - Carbon Dioxide Emission.
                        # Available at: https://www.engineeringtoolbox.com/co2-emission-fuels-d_1085.html
                        # [Accessed 12/12/2021].
                        # https://www.engineeringtoolbox.com/co2-emission-fuels-d_1085.html
                        'CO2_per_use': 3.60,  # before 15/12 : 3.6, # 3.15 + refinery
                        'CO2_per_use_unit': 'kg/kg',
                        'NOx_per_energy': 0.1,
                        'NOX_per_energy_unit': 'yy',
                        # Source for [cost of Gasoline]: IEA 2022, Energy Prices: Overview,
                        # https://www.iea.org/reports/energy-prices-overview
                        # License: CC BY 4.0.
                        'cost_now': 0.85,
                        'cost_now_unit': '$/kg',
                        'density': 750,  # at atmospheric pressure and 298K
                        'density_unit': 'kg/m^3',
                        'molar_mass': 114.232,
                        'molar_mass_unit': 'g/mol',
                        # Calorific values from:
                        # Engineering ToolBox, (2003).
                        # Fuels - Higher and Lower Calorific Values.
                        # Available at: https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html
                        # [Accessed 15/12/2021].
                        'calorific_value': 12.06,
                        'calorific_value_unit': 'kWh/kg',
                        'high_calorific_value': 12.89,
                        'high_calorific_value_unit': 'kWh/kg'}
