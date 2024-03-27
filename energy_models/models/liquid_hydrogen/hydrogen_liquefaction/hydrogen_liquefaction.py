'''
Copyright 2022 Airbus SAS
Modifications on 2023/10/10-2023/11/15 Copyright 2023 Capgemini

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

from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import GaseousHydrogen
from energy_models.core.techno_type.base_techno_models.liquid_hydrogen_techno import LiquidHydrogenTechno


class HydrogenLiquefaction(LiquidHydrogenTechno):
    """
    hydrogen_liquefaction class

    inputs

    """
    def compute_cost_of_other_energies_usage(self):
        self.cost_details[Electricity.name] = self.cost_details['elec_needs'] * \
                                              self.prices[Electricity.name]

        # Cost of hydrogen for 1kwh of LH2
        self.cost_details[GaseousHydrogen.name] = self.prices[GaseousHydrogen.name] * \
                                                  self.cost_details['hydrogen_needs']


    def compute_other_energies_needs(self):
        self.cost_details['elec_needs'] = self.get_electricity_needs()

        # for 1kwh of gas hydrogen, we get 0.98
        self.cost_details['hydrogen_needs'] = 1 / \
                                              self.cost_details['efficiency']


    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs which depends on the technology 
        """
        super().compute_other_primary_energy_costs()


        return self.cost_details[Electricity.name] + self.cost_details[GaseousHydrogen.name]

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices 
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        elec_needs = self.get_electricity_needs()
        hydrogen_needs = 1.0 / self.compute_efficiency()

        return {Electricity.name: np.identity(len(self.years)) * elec_needs,
                GaseousHydrogen.name: np.identity(len(self.years)) * hydrogen_needs,
                }

    def compute_CO2_emissions_from_input_resources(self):
        ''' 
        Need to take into account positive CO2 from methane and elec prod
        Carbon capture (Methane is not burned but transformed is not taken into account)
        '''

        self.carbon_intensity[Electricity.name] = self.energy_CO2_emissions[Electricity.name] * \
                                                  self.cost_details['elec_needs']

        self.carbon_intensity[GaseousHydrogen.name] = self.energy_CO2_emissions[GaseousHydrogen.name] * \
                                                      self.cost_details['hydrogen_needs']

        return self.carbon_intensity[Electricity.name] + self.carbon_intensity[GaseousHydrogen.name]

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """

        # Consumption
        self.consumption_detailed[f'{Electricity.name} ({self.product_energy_unit})'] = self.cost_details[
                                                                                            'elec_needs'] * \
                                                                                        self.production_detailed[
                                                                                            f'{LiquidHydrogenTechno.energy_name} ({self.product_energy_unit})']  # in kWH

        self.consumption_detailed[f'{GaseousHydrogen.name} ({self.product_energy_unit})'] = self.cost_details[
                                                                                                'hydrogen_needs'] * \
                                                                                            self.production_detailed[
                                                                                                f'{LiquidHydrogenTechno.energy_name} ({self.product_energy_unit})']  # in kWH

        # self.production[f'{lowtemperatureheat.name} ({self.product_energy_unit})'] = (1 - self.techno_infos_dict['efficiency']) * \
        #     self.consumption[f'{GaseousHydrogen.name} ({self.product_energy_unit})']/\
        #     self.techno_infos_dict['efficiency']

        # self.production[f'{lowtemperatureheat.name} ({self.product_energy_unit})'] = \
        #     self.consumption[f'{Electricity.name} ({self.product_energy_unit})'] * self.techno_infos_dict['heat_recovery_factor']

        #
        # print('')
        # print(self.production.to_string())
        # print('')
        # print(self.consumption.to_string())
