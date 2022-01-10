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


class BioGas(EnergyType):
    # Bio gas is bioCH4 + CO2
    name = 'biogas'
    data_energy_dict = {'maturity': 5,
                        # IEA (2020), Outlook for biogas and biomethane: Prospects for organic growth, IEA, Paris
                        # https://www.iea.org/reports/outlook-for-biogas-and-biomethane-prospects-for-organic-growth
                        'CH4_per_energy': 0.6,
                        'CH4_per_energy_unit': 'kg/kg',
                        # Valerio Paolini, Francesco Petracchini, Marco Segreto, Laura Tomassetti,
                        # Nour Naja & Angelo Cecinato (2018) Environmental impact of biogas: A short review of current
                        # knowledge, Journal of Environmental Science and Health, Part A, 53:10, 899-906, DOI:
                        # 10.1080/10934529.2018.1459076
                        # https://www.tandfonline.com/doi/pdf/10.1080/10934529.2018.1459076
                        # 83.6 kg/GJ ---> /277.78 kg/kWh
                        'CO2_per_use': 83.6 / 277.78,
                        'CO2_per_use_unit': 'kg/kWh',
                        #                         'CO2_per_use': 0.4 * 1.98 + 2.86*0.657*0.6,
                        #                         'CO2_per_use_unit': 'kg/kg',

                        # Combination of CH4 and CO2 densities
                        'density': 0.657 * 0.6 + 0.4 * 1.98,
                        'density_unit': 'kg/m^3',
                        # Combination of CH4 and CO2 molar mass
                        'molar_mass': 16.04 * 0.6 + 0.4 * 44.01,
                        'molar_mass_unit': 'g/mol',
                        # IEA (2020), Outlook for biogas and biomethane: Prospects for organic growth, IEA, Paris
                        # https://www.iea.org/reports/outlook-for-biogas-and-biomethane-prospects-for-organic-growth
                        # between 16 MJ/m3 and 28 MJ/m3
                        # MJ/m^3 to kWh/kg you need to divide by 3.6 and by
                        # density
                        'calorific_value': 23.0 / 3.6 / (0.657 * 0.6 + 0.4 * 1.98),
                        'calorific_value_unit': 'kWh/kg',
                        'high_calorific_value': 27.6 / 3.6 / (0.657 * 0.6 + 0.4 * 1.98),
                        'high_calorific_value_unit': 'kWh/kg', }
