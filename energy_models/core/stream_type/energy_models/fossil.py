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
from energy_models.core.stream_type.energy_models.solid_fuel import SolidFuel
from energy_models.core.stream_type.energy_models.liquid_fuel import LiquidFuel
from energy_models.core.stream_type.energy_models.methane import Methane


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
    name = 'fossil'
    default_techno_list = ['FossilSimpleTechno']
    data_energy_dict = {'CO2_per_use': compute_fossil_data('CO2_per_use'),  # mean of CO2 per use of fossil energies
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

    # net_production = 90717.76  # TWh
    # raw_production = 136917.16  # TWh
    raw_to_net_production = 1.0  # net_production / raw_production

    def compute_ghg_per_use(self, ghg_type):
        '''
        Specific computation for the CO2 per use taking into account the use of oil in petrochemical plants (plastic and textile) and construction


        We only take into account energy emissions and not industrial emissions in energy mix
        --> CO2 per use petrochemical and construction will be used in an industrial co2 emissions model
        '''

        #         kgcoal_per_kgsteel = 1 / 1.7
        #         kgcoal_per_kgcement = 0.25
        #
        #         kgco2_per_kgsteel = 1.852
        #         kgco2_per_kgcement = 0.9
        #
        #         co2_per_use_steel = kgco2_per_kgsteel / kgcoal_per_kgsteel
        #         co2_per_use_cement = kgco2_per_kgcement / kgcoal_per_kgcement

        if ghg_type == 'CO2':
            co2_per_use_kgkg = self.data_energy_dict_input['CO2_per_use'] * \
                               (1.0 - self.data_energy_dict_input['petrochemical_use_part'] -
                                self.data_energy_dict_input['construction_use_part'])

            ghg_per_use = co2_per_use_kgkg / \
                          self.data_energy_dict_input['high_calorific_value']
        else:
            ghg_per_use = EnergyType.compute_ghg_per_use(self, ghg_type)

        return ghg_per_use


"""
    def compute_ghg_per_use(self, data_energy_dict):
        '''
        Specific computation for the CO2 per use taking into account the use of fossil in 
        petrochemical plants (plastic and textile), construction, cement and steel 


        We only take into account energy emissions and not industrial emissions in energy mix 
        --> CO2 per use petrochemical and construction will be used in an industrial co2 emissions model 

        This CO2_per_use is used in CO2 emitted by net energy
        '''
        prod_solid_fuel = 45000.  # TWh
        prod_liquid_fuel = 53000.  # TWh
        prod_methane = 39106.77  # TWh
        prod_fossil = prod_solid_fuel + prod_liquid_fuel + prod_methane

        industry_percent = prod_solid_fuel / prod_fossil * (SolidFuel.data_energy_dict['ironsteel_use_part'] +
                                                            SolidFuel.data_energy_dict['cement_use_part'] +
                                                            SolidFuel.data_energy_dict['chemicals_use_part']) +\
            prod_liquid_fuel / prod_fossil * (LiquidFuel.data_energy_dict['petrochemical_use_part'] +
                                              LiquidFuel.data_energy_dict['construction_use_part'])
        print('***')
        co2_per_use_kgkg = data_energy_dict['CO2_per_use'] * \
            (1.0 - industry_percent)

        self.co2_per_use['CO2_per_use'] = co2_per_use_kgkg / \
            data_energy_dict['high_calorific_value']

        return self.co2_per_use
"""
