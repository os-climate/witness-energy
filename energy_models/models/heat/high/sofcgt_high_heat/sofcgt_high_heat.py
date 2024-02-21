'''
Copyright 2023 Capgemini

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
import numpy as np
import pandas as pd

from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from energy_models.core.techno_type.base_techno_models.high_heat_techno import highheattechno
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.core.stream_type.energy_models.solid_fuel import SolidFuel
from energy_models.core.stream_type.resources_models.water import Water


class SofcgtHighHeat(highheattechno):

    def __init__(self, name):
        super().__init__(name)
        self.land_rate = None
        self.heat_flux = None
        self.heat_flux_distribution = None

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs which depends on the technology 
        """

        # in kwh of fuel by kwh of electricity
        self.cost_details['solid_fuel_needs'] = self.techno_infos_dict['fuel_demand'] / \
                                                self.cost_details['efficiency']

        # need in kg/kWh
        self.cost_details['water_needs'] = self.techno_infos_dict['water_demand']
        
        # Cost of solid_fuel for 1 kWH of electricity - Efficiency removed as data is
        # the process global solid_fuel consumption
        self.cost_details[SolidFuel.name] = self.cost_details['solid_fuel_needs']
      
        # Cost of water for 1 kWH of electricity - Efficiency removed as data
        # is the process global water consumption
        
        self.cost_details[Water.name] = list(
            self.resources_prices[Water.name] * self.cost_details['water_needs'])

        # + self.cost_details[GlossaryEnergy.electricity]
        return self.cost_details[SolidFuel.name] + self.cost_details[Water.name]

    # def grad_price_vs_energy_price(self):
    #     '''
    #     Compute the gradient of global price vs energy prices
    #     '''
    #     elec_needs = self.get_theoretical_electricity_needs()
    #     efficiency = self.techno_infos_dict['efficiency']
    #     return {Electricity.name: np.identity(len(self.years)) * elec_needs / efficiency,
    #             }

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        """

        # Consumption
        #elec_needs = self.get_electricity_needs()

        # Consumption
        self.consumption_detailed[f'{SolidFuel.name} ({self.product_energy_unit})'] = self.cost_details[
                                                                                          'solid_fuel_needs'] * \
                                                                                      self.production_detailed[
                                                                                          f'{highheattechno.energy_name} ({self.product_energy_unit})']  # in kWH
        self.consumption_detailed[f'{Water.name} ({self.mass_unit})'] = self.cost_details['water_needs'] * \
                                                                        self.production_detailed[
                                                                            f'{highheattechno.energy_name} ({self.product_energy_unit})']  # in kg
        # Production
        self.production_detailed[f'{hightemperatureheat.name} ({self.product_energy_unit})'] = \
            self.consumption_detailed[f'{SolidFuel.name} ({self.product_energy_unit})'] - \
            self.production_detailed[f'{highheattechno.energy_name} ({self.product_energy_unit})']

    # def get_theoretical_electricity_needs(self):
    #     # we need as output kwh/kwh
    #     elec_demand = self.techno_infos_dict['elec_demand']

    #     return elec_demand
    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices 
        
        '''
        solid_fuel_needs = self.techno_infos_dict['fuel_demand']
        efficiency = self.configure_efficiency()
        return {SolidFuel.name: np.identity(len(self.years)) * solid_fuel_needs / efficiency[:, np.newaxis]}