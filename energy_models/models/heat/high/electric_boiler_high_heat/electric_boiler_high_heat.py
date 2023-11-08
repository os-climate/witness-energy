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
from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from energy_models.core.techno_type.base_techno_models.high_heat_techno import highheattechno
from energy_models.core.stream_type.energy_models.electricity import Electricity
import numpy as np
import pandas as pd


class ElectricBoilerHighHeat(highheattechno):

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs to produce 1kWh of heat
        """

        self.cost_details[f'{Electricity.name}_needs'] = self.get_theoretical_electricity_needs()


        self.cost_details[f'{Electricity.name}'] = \
            self.prices[Electricity.name] * \
            self.cost_details[f'{Electricity.name}_needs'] / \
            self.cost_details['efficiency']

        #print(self.cost_details[f'{Electricity.name}'])

        return self.cost_details[f'{Electricity.name}']

    def configure_input(self, inputs_dict):
        '''
        Configure with inputs_dict from the discipline
        '''
        self.land_rate = inputs_dict['flux_input_dict']['land_rate']

    def compute_heat_flux(self):
        land_rate = self.land_rate
        heat_price = self.compute_other_primary_energy_costs()
        self.heat_flux = land_rate/heat_price
        self.heat_flux_distribution = pd.DataFrame({GlossaryCore.Years: self.cost_details[GlossaryCore.Years],
                                               'heat_flux': self.heat_flux})
        return self.heat_flux_distribution

    def compute(self):
        """
        computing
        """
        self.compute_consumption_and_production()
        self.compute_other_primary_energy_costs()

        self.grad_price_vs_energy_price()
    def grad_price_vs_energy_price_calc(self):
        '''
        Compute the gradient of global price vs energy prices
        '''
        elec_needs = self.get_theoretical_electricity_needs()
        efficiency = self.techno_infos_dict['efficiency']
        return {'natural_gas_resource': np.identity(len(self.years)) * elec_needs / efficiency,
                }

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        """
        self.compute_primary_energy_production()
        # Consumption
        self.consumption[f'{Electricity.name} ({self.product_energy_unit})'] = self.cost_details[f'{Electricity.name}_needs'] * \
            self.production[f'{hightemperatureheat.name} ({self.product_energy_unit})']

    def get_theoretical_electricity_needs(self):
        # we need as output kwh/kwh
        elec_demand = self.techno_infos_dict['elec_demand']

        return elec_demand



