'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/09-2023/11/15 Copyright 2023 Capgemini

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

from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.energy_models.fossil import Fossil
from energy_models.core.stream_type.energy_models.renewable import Renewable
from energy_models.core.techno_type.base_techno_models.carbon_capture_techno import CCTechno


class DirectAirCaptureTechno(CCTechno):


    def compute_cost_of_other_energies_usage(self):
        self.cost_details[Renewable.name] = list(self.prices[Renewable.name] * self.cost_details['elec_needs'])
        self.cost_details[Fossil.name] = list(self.prices[Fossil.name] * self.cost_details['heat_needs'])
    
    def compute_other_energies_needs(self):
        self.cost_details['elec_needs'] = self.get_electricity_needs()
        self.cost_details['heat_needs'] = self.get_heat_needs()


    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs which depends on the technology 

        """

        super().compute_other_primary_energy_costs()

        return self.cost_details[Renewable.name] + self.cost_details[Fossil.name]

    def compute_CO2_emissions_from_input_resources(self):
        '''
        Need to take into account  CO2 from coal extraction and electricity production
        '''

        self.carbon_intensity[Fossil.name] = self.energy_CO2_emissions[Fossil.name] * self.cost_details['heat_needs']

        self.carbon_intensity[Renewable.name] = self.energy_CO2_emissions[Renewable.name] * self.cost_details[
            'elec_needs']

        return self.carbon_intensity[Fossil.name] + self.carbon_intensity[Renewable.name] - 1.0

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices 
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        elec_needs = self.get_electricity_needs()
        heat_needs = self.get_heat_needs()
        return {Renewable.name: np.identity(len(self.years)) * elec_needs,
                Fossil.name: np.identity(len(self.years)) * heat_needs,
                }

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """

        # Consumption

        self.consumption_detailed[f'{Renewable.name} ({self.energy_unit})'] = self.cost_details['elec_needs'] * \
                                                                              self.production_detailed[
                                                                                  f'{CCTechno.energy_name} ({self.product_energy_unit})']  # in kWH

        self.consumption_detailed[f'{Fossil.name} ({self.energy_unit})'] = self.cost_details['heat_needs'] * \
                                                                           self.production_detailed[
                                                                               f'{CCTechno.energy_name} ({self.product_energy_unit})']  # in kWH

        self.production_detailed[f'{CarbonCapture.flue_gas_name} ({self.mass_unit})'] = self.cost_details[
                                                                                            'heat_needs'] * \
                                                                                        self.production_detailed[
                                                                                            f'{CCTechno.energy_name} ({self.product_energy_unit})'] * \
                                                                                        Fossil.data_energy_dict[
                                                                                            'CO2_per_use'] / \
                                                                                        Fossil.data_energy_dict[
                                                                                            'calorific_value']
