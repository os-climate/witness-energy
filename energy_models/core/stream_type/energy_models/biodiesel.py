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


class BioDiesel(EnergyType):
    # Biodiesel is a fuel comprised of mono-alkyl esters of long chain fatty acids derived from vegetable oils or animal fats, designated B100, and meeting the requirements of ASTM D 6751.
    # fatty acid methyl esters (FAME).
    name = 'fuel.biodiesel'
    short_name = 'biodiesel'
    default_techno_list = ['Transesterification']
    data_energy_dict = {'maturity': 5,

                        # Coronado, C.R., de Carvalho Jr, J.A. and Silveira, J.L., 2009.
                        # Biodiesel CO2 emissions: A comparison with the main fuels in the Brazilian market.
                        # Fuel Processing Technology, 90(2), pp.204-211.
                        # https://getec.unifei.edu.br/wp/wp-content/uploads/2016/10/15.pdf
                        # Engineering ToolBox, (2009). Combustion of Fuels - Carbon Dioxide Emission. [online]
                        # Available at: https://www.engineeringtoolbox.com/co2-emission-fuels-d_1085.html
                        # [Accessed 09 05 2022].
                        'CO2_per_use': 2.85,
                        'CO2_per_use_unit': 'kg/kg',

                        'density': 880,
                        'density_unit': 'kg/m^3',
                        # Murtonen, T. and Aakko-Saksa, P., 2009.
                        # Alternative fuels with heavy-duty engines and vehicles. VTTs Contribution.
                        # Julkaisija Utgivare Publisher, VTT Working Papers, 128, pp.109-117.
                        # Available at: https://www.vttresearch.com/sites/default/files/pdf/workingpapers/2009/W128.pdf [Accessed 14/12/2021]
                        # C19H34O2
                        'molar_mass': 294,
                        'molar_mass_unit': 'g/mol',

                        # viscosity at 40 C
                        'viscosity': 4.5,
                        'viscosity_unit': 'mm2/s',

                        'cetane_number': 56.0,
                        'lower_heating_value': 34,
                        'lower_heating_value_unit': 'MJ/kg',

                        # Around 1.2l of biodiesel (FAME) is energy equivalent to 1l of diesel
                        # Engineering ToolBox, (2003). Fuels - Higher and Lower Calorific Values. [online]
                        # Available at:
                        # https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html
                        # [Accessed 14/12/2021].
                        'calorific_value': 10.42,
                        'calorific_value_unit': 'kWh/kg',
                        'high_calorific_value': 11.17,
                        'high_calorific_value_unit': 'kWh/kg'

                        }
