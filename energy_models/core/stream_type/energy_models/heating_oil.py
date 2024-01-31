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


class HeatingOil(EnergyType):
    """
    regroup different product of curde oil refinery, such as Naphtha and gas oil
    """

    name = 'heating_oil'
    data_energy_dict = {'maturity': 5,
                        'WACC': 0.1,
                        # CO2 emissions per U.S. Energy Information Administration
                        # https://www.eia.gov/environment/emissions/co2_vol_mass.php
                        # val_naphta = Naphtha for Petrochemical Feedstock Use * galon to kg factor
                        # val_oils = Other Oils for Petrochemical Feedstock Use * galon to kg factor
                        # CO2 per use = (val_naphta + val_oils)/2.0
                        # CO2 per use = (3.04 [10.26/3.37] + 3.37
                        # [8.5/2.52])/2.0
                        'CO2_per_use': 2.82,
                        'CO2_per_use_unit': 'kg/kg',
                        # Source: U.S. Energy Information Administration
                        # https://www.eia.gov/outlooks/steo/tables/pdf/2tab.pdf
                        'cost_now': 0.35,
                        'cost_now_unit': '$/kg',
                        'density': 740,  #
                        'density_unit': 'kg/m^3',
                        'molar_mass': 108.099,  #
                        'molar_mass_unit': 'g/mol',
                        # Source for [calorific value]: IEA 2022, Energy Statistics Manual,
                        # https://www.iea.org/reports/energy-statistics-manual-2
                        # License: CC BY 4.0.
                        # Calorific value = (cal_val Naphtha + cal_val Gas
                        # oil)/2.0 * (277.778/1000) [GJ/t to kWh/kg conversion]
                        'calorific_value': 12.47,  #
                        'calorific_value_unit': 'kWh/kg',
                        'high_calorific_value': 13.36,  #
                        'high_calorific_value_unit': 'kWh/kg'}
