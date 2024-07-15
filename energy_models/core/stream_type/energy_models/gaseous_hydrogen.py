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


class GaseousHydrogen(EnergyType):
    name = f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}'
    short_name = GlossaryEnergy.gaseous_hydrogen
    default_techno_list = [GlossaryEnergy.ElectrolysisPEM, GlossaryEnergy.ElectrolysisAWE,
                           GlossaryEnergy.ElectrolysisSOEC, GlossaryEnergy.WaterGasShift, GlossaryEnergy.PlasmaCracking]
    data_energy_dict = {'maturity': 10,
                        'WACC': 0.1,
                        'NOx_per_energy': 7.0,
                        'NOX_per_energy_unit': 'mg/kg',
                        # Density and calorific values taken from:
                        # Engineering ToolBox, (2003). Fuels - Higher and Lower Calorific Values. [online]
                        # Available at:
                        # https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html
                        # [Accessed 15/12/2021].
                        'density': 0.0808,  # Gaseous at 0 C, 1bar
                        'density_unit': 'kg/m^3',
                        'molar_mass': 2.01588,
                        'molar_mass_unit': 'g/mol',
                        'calorific_value': 33.3,
                        'calorific_value_unit': 'kWh/kg',
                        'high_calorific_value': 39.4,
                        'high_calorific_value_unit': 'kWh/kg',
                        # Barreto, L., Makihira, A. and Riahi, K., 2003.
                        # The hydrogen economy in the 21st century: a sustainable development scenario.
                        # International Journal of Hydrogen Energy, 28(3),
                        # pp.267-284.
                        'learning_rate': 0.2,
                        }
