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
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.techno_type.base_techno_models.methane_techno import MethaneTechno
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
import numpy as np

class FossilGas(MethaneTechno):
    NATURAL_GAS_RESOURCE_NAME = ResourceGlossary.NaturalGas['name']
    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs to produce 1kg of CH4
        """

        self.cost_details['elec_needs'] = self.get_electricity_needs()
        self.cost_details[f'{self.NATURAL_GAS_RESOURCE_NAME}_needs'] = np.ones(len(self.years)) / Methane.data_energy_dict['calorific_value'] #kg/kWh
        self.cost_details[f'{Electricity.name}'] = list(
            self.prices[f'{Electricity.name}'] * self.cost_details['elec_needs'])
        self.cost_details[f'{self.NATURAL_GAS_RESOURCE_NAME}'] = list(
            self.resources_prices[f'{self.NATURAL_GAS_RESOURCE_NAME}'] * self.cost_details[f'{self.NATURAL_GAS_RESOURCE_NAME}_needs'])
        # cost to produce 1Kwh of methane
        return self.cost_details[f'{Electricity.name}'] + self.cost_details[f'{self.NATURAL_GAS_RESOURCE_NAME}']

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices 
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        elec_needs = self.get_electricity_needs()
        return {Electricity.name: np.identity(len(self.years)) * elec_needs,
                }

    def grad_price_vs_resource_price(self):
        '''
        Compute the gradient of global price vs resource prices
        Work also for total CO2_emissions vs resource CO2 emissions
        '''
        natural_gas_needs = 1 / Methane.data_energy_dict['calorific_value'] #kg/kWh
        return {self.NATURAL_GAS_RESOURCE_NAME: np.identity(len(self.years)) * natural_gas_needs,
                }

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """

        # compute CH4 production in kWh
        self.compute_primary_energy_production()
        self.consumption[f'{Electricity.name} ({self.product_energy_unit})'] = self.cost_details['elec_needs'] * \
            self.production[f'{MethaneTechno.energy_name} ({self.product_energy_unit})']  # in kWH

        # kg/kWh corresponds to Mt/TWh
        self.production[f'{CarbonCapture.flue_gas_name} ({self.mass_unit})'] = self.techno_infos_dict['CO2_from_production'] / \
            self.data_energy_dict['calorific_value'] * \
            self.production[f'{MethaneTechno.energy_name} ({self.product_energy_unit})']

        # consumption fossil gas
        self.consumption[f'{self.NATURAL_GAS_RESOURCE_NAME} ({self.mass_unit})'] = self.production[
            f'{MethaneTechno.energy_name} ({self.product_energy_unit})'] / Methane.data_energy_dict['calorific_value']  # in Mt

    def compute_CO2_emissions_from_input_resources(self):
        '''
        Need to take into account  CO2 from electricity production 
        '''

        self.carbon_emissions[f'{Electricity.name}'] = self.energy_CO2_emissions[f'{Electricity.name}'] * \
            self.cost_details['elec_needs']

        return self.carbon_emissions[f'{Electricity.name}']
