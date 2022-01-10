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

from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.core.techno_type.base_techno_models.solid_fuel_techno import SolidFuelTechno
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.ressources_models.oil import CrudeOil
from energy_models.core.stream_type.energy_models.solid_fuel import SolidFuel

import numpy as np


class CoalExtraction(SolidFuelTechno):

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs which depends on the technology 
        """

        self.cost_details['elec_needs'] = self.get_electricity_needs()

        self.cost_details[Electricity.name] = list(self.prices[Electricity.name] * self.cost_details['elec_needs']
                                                   / self.cost_details['efficiency'])

        self.cost_details['fuel_needs'] = self.get_fuel_needs()
        self.cost_details[CrudeOil.name] = list(self.ressources_prices[CrudeOil.name] * self.cost_details['fuel_needs']
                                                / self.cost_details['efficiency'])

        return self.cost_details[Electricity.name] + self.cost_details[CrudeOil.name]

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices 
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        elec_needs = self.get_electricity_needs()
        oil_needs = self.get_fuel_needs()
        efficiency = self.techno_infos_dict['efficiency']
        return {Electricity.name: np.identity(len(self.years)) * elec_needs / efficiency,
                }

    def grad_ressources(self):
        oil_needs = self.get_fuel_needs()
        efficiency = self.techno_infos_dict['efficiency']
        return {CrudeOil.name: np.identity(len(self.years)) * oil_needs / efficiency}

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """

        self.compute_primary_energy_production()

        self.production[f'{CO2.name} ({self.mass_unit})'] = self.techno_infos_dict['CO2_from_production'] / \
            self.data_energy_dict['high_calorific_value'] * \
            self.production[f'{SolidFuelTechno.energy_name} ({self.product_energy_unit})']

        # Consumption
        self.consumption[f'{Electricity.name} ({self.product_energy_unit})'] = self.cost_details['elec_needs'] * \
            self.production[f'{SolidFuelTechno.energy_name} ({self.product_energy_unit})']  # in kWH

        self.consumption[f'{CrudeOil.name} ({self.product_energy_unit})'] = self.cost_details['fuel_needs'] * \
            self.production[f'{SolidFuelTechno.energy_name} ({self.product_energy_unit})'] / \
            self.cost_details['efficiency']  # in kWH

        # Coal Consumption
        self.consumption[f'coal_resource'] = self.production[f'{SolidFuelTechno.energy_name} ({self.product_energy_unit})'] / \
            self.cost_details['efficiency'] / \
            SolidFuel.data_energy_dict['calorific_value']  # in Mt

    def compute_CO2_emissions_from_input_ressources(self):
        '''
        Need to take into account  CO2 from electricity/fuel production
        '''

        self.carbon_emissions[f'{Electricity.name}'] = self.energy_CO2_emissions[f'{Electricity.name}'] * \
            self.cost_details['elec_needs']

        if CrudeOil.name in self.energy_CO2_emissions:
            self.carbon_emissions[CrudeOil.name] = self.ressources_CO2_emissions[f'{CrudeOil.name}'] * \
                self.cost_details['fuel_needs']
        else:
            self.carbon_emissions[CrudeOil.name] = 25.33 * \
                self.cost_details['fuel_needs']
        return self.carbon_emissions[f'{Electricity.name}'] + self.carbon_emissions[CrudeOil.name]
