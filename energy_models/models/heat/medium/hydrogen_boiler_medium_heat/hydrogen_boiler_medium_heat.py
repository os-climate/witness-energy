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
from energy_models.core.stream_type.energy_models.heat import mediumtemperatureheat
from energy_models.core.techno_type.base_techno_models.medium_heat_techno import mediumheattechno
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import GaseousHydrogen

import pandas as pd


class HydrogenBoilerMediumHeat(mediumheattechno):

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs to produce 1kWh of heat
        """
        self.cost_details[f'{GaseousHydrogen.name}_needs'] = self.get_theoretical_hydrogen_needs()
        self.cost_details[f'{GaseousHydrogen.name}'] = \
            self.prices[f'{GaseousHydrogen.name}'] * \
            self.cost_details[f'{GaseousHydrogen.name}_needs'] / \
            self.cost_details['efficiency']

        # hydrogen_needs

        # output needed in this method is in $/kwh of heat
        # to do so I need to know how much hydrogen is used to produce 1kwh of heat (i need this information in kwh) : hydrogen_needs is in kwh of hydrogen/kwh of heat
        # kwh/kwh * price of hydrogen ($/kwh) : kwh/kwh * $/kwh  ----> $/kwh  : price of hydrogen is in self.prices[f'{GaseousHydrogen.name}']
        # and then we divide by efficiency
        return self.cost_details[f'{GaseousHydrogen.name}']

    def grad_price_vs_energy_price_calc(self):
        '''
        Compute the gradient of global price vs energy prices
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        hydrogen_needs = self.get_theoretical_hydrogen_needs()
        efficiency = self.techno_infos_dict['efficiency']

        # return {
        #         GaseousHydrogen.name: np.identity(len(self.years)) * hydrogen_needs / efficiency
        #         }
        return {}

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        """

        self.compute_primary_energy_production()

        # Consumption

        self.consumption[f'{GaseousHydrogen.name} ({self.product_energy_unit})'] = self.cost_details[f'{GaseousHydrogen.name}_needs'] * \
            self.production[f'{mediumtemperatureheat.name} ({self.product_energy_unit})']

    def get_theoretical_hydrogen_needs(self):
        # we need as output kwh/kwh
        hydrogen_demand = self.techno_infos_dict['hydrogen_demand']

        hydrogen_needs = hydrogen_demand

        return hydrogen_needs

    def configure_input(self, inputs_dict):
        '''
        Configure with inputs_dict from the discipline
        '''
        self.land_rate = inputs_dict['flux_input_dict']['land_rate']

    def compute_heat_flux(self):
        land_rate = self.land_rate
        heat_price = self.compute_other_primary_energy_costs()
        self.heat_flux = land_rate/heat_price
        self.heat_flux_distribution = pd.DataFrame({'years': self.cost_details['years'],
                                               'heat_flux': self.heat_flux})

        return self.heat_flux_distribution