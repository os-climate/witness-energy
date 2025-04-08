'''
Copyright 2022 Airbus SAS
Modifications on 2023/09/13-2023/11/16 Copyright 2023 Capgemini

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
from energy_models.core.stream_type.energy_models.liquid_fuel import LiquidFuel
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.energy_models.solid_fuel import SolidFuel
from energy_models.core.stream_type.energy_type import EnergyType
from energy_models.glossaryenergy import GlossaryEnergy


def compute_fossil_data(data_name):
    '''
    Compute fossil data from a mean of oil, coal and gas data
    '''
    prod_solid_fuel = 45000.  # TWh
    prod_liquid_fuel = 53000.  # TWh
    prod_methane = 39106.77  # TWh
    prod_fossil = prod_solid_fuel + prod_liquid_fuel + prod_methane
    energy_data = (SolidFuel.data_energy_dict[data_name] * prod_solid_fuel +
                   LiquidFuel.data_energy_dict[data_name] * prod_liquid_fuel +
                   Methane.data_energy_dict[data_name] * prod_methane) / prod_fossil

    return energy_data


class Fossil(EnergyType):
    name = GlossaryEnergy.fossil
    default_techno_list = [GlossaryEnergy.FossilSimpleTechno]
    data_energy_dict = {GlossaryEnergy.CO2PerUse: compute_fossil_data(GlossaryEnergy.CO2PerUse),  # mean of CO2 per use of fossil energies
                        'CO2_per_use_unit': 'kg/kg',
                        'density': compute_fossil_data('density'),
                        'density_unit': 'kg/m^3',
                        'calorific_value': compute_fossil_data('calorific_value'),
                        'calorific_value_unit': 'kWh/kg',
                        'high_calorific_value': compute_fossil_data('high_calorific_value'),
                        'high_calorific_value_unit': 'kWh/kg',
                        # around 14% of oil is used for petrochemical plants
                        # around 8% of oil is used for construction (asphalt)
                        # or other use
                        'petrochemical_use_part': 0.14,
                        'construction_use_part': 0.08
                        }

    net_production = 90717.76  # TWh
    raw_production = 136917.16  # TWh
    raw_to_net_production = net_production / raw_production

