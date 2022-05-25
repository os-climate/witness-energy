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

from energy_models.core.techno_type.base_techno_models.carbon_capture_techno import CCTechno
from energy_models.core.stream_type.energy_models.renewable import Renewable
from energy_models.core.stream_type.energy_models.fossil import Fossil

import numpy as np


class DirectAirCaptureTechno(CCTechno):



    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs which depends on the technology 

        """

        self.cost_details['elec_needs'] = self.get_electricity_needs()

        self.cost_details[Renewable.name] = list(self.prices[Renewable.name] * self.cost_details['elec_needs']
                                                 / self.cost_details['efficiency'])
        self.cost_details['heat_needs'] = self.get_heat_needs()
        self.cost_details[Fossil.name] = list(self.prices[Fossil.name] * self.cost_details['heat_needs']
                                                 / self.cost_details['efficiency'])
        return self.cost_details[Renewable.name] + self.cost_details[Fossil.name]

    def compute_CO2_emissions_from_input_resources(self):
        '''
        Need to take into account  CO2 from coal extraction and electricity production
        '''

        self.carbon_emissions[Fossil.name] = self.energy_CO2_emissions[Fossil.name] * self.cost_details['heat_needs']

        self.carbon_emissions[Renewable.name] = self.energy_CO2_emissions[Renewable.name] * self.cost_details['elec_needs']

        return self.carbon_emissions[Fossil.name] + self.carbon_emissions[Renewable.name]

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices 
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        elec_needs = self.get_electricity_needs()
        heat_needs = self.get_heat_needs()
        efficiency = self.configure_efficiency()
        return {Renewable.name: np.identity(len(self.years)) * elec_needs / efficiency,
                Fossil.name: np.identity(len(self.years)) * heat_needs / efficiency,
                }

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """
        self.compute_primary_energy_production()
        # Consumption

        self.consumption[f'{Renewable.name} ({self.energy_unit})'] = self.cost_details['elec_needs'] * \
            self.production[f'{CCTechno.energy_name} ({self.product_energy_unit})']  # in kWH

        self.consumption[f'{Fossil.name} ({self.energy_unit})'] = self.cost_details['heat_needs'] * \
            self.production[f'{CCTechno.energy_name} ({self.product_energy_unit})']  # in kWH