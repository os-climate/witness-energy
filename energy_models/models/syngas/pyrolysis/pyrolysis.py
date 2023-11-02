'''
Copyright 2022 Airbus SAS
Modifications on 2023/09/25-2023/11/02 Copyright 2023 Capgemini

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

from energy_models.core.techno_type.base_techno_models.syngas_techno import SyngasTechno
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
import numpy as np
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
from energy_models.core.techno_type.base_techno_models.medium_heat_techno import mediumheattechno


class Pyrolysis(SyngasTechno):
    syngas_COH2_ratio = 0.5 / 0.45 * 100.0  # in %

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs which depends on the technology 
        """

        # wood needed to produce 1kwh of syngas

        # syngas produced in kg by 1kg of wood
        syngas_kg = 1.0 * self.techno_infos_dict['syngas_yield']

        # kwh produced by 1kg of wood

        syngas_kwh = self.data_energy_dict['calorific_value'] * syngas_kg

        # wood needs in kg to produce 1kWh of syngas
        self.cost_details['wood_needs'] = 1 / syngas_kwh

        # Cost of wood for 1 kWh of syngas
        self.cost_details[ResourceGlossary.Wood['name']] = list(
            self.resources_prices[ResourceGlossary.Wood['name']] * self.cost_details['wood_needs'])

        return self.cost_details[ResourceGlossary.Wood['name']]

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """

        self.compute_primary_energy_production()

        self.production[f'{CarbonCapture.flue_gas_name} ({self.mass_unit})'] = self.techno_infos_dict['CO2_from_production'] / \
            self.data_energy_dict['calorific_value'] * \
            self.production[f'{SyngasTechno.energy_name} ({self.product_energy_unit})']

        self.production[f'char ({self.mass_unit})'] = self.production[f'{SyngasTechno.energy_name} ({self.product_energy_unit})'] * \
            self.techno_infos_dict['char_yield'] / \
            self.techno_infos_dict['syngas_yield']

        self.production[f'bio_oil ({self.mass_unit})'] = self.production[f'{SyngasTechno.energy_name} ({self.product_energy_unit})'] * \
            self.techno_infos_dict['bio_oil_yield'] / \
            self.techno_infos_dict['syngas_yield']

        self.consumption[f'wood ({self.mass_unit})'] = self.cost_details['wood_needs'] * \
            self.production[f'{SyngasTechno.energy_name} ({self.product_energy_unit})']

        # self.consumption[f'{mediumheattechno.energy_name} ({self.product_energy_unit})'] = \
        #     self.techno_infos_dict['medium_heat_production'] * \
        #     self.production[f'{SyngasTechno.energy_name} ({self.product_energy_unit})']  # in TWH


    def compute_CO2_emissions_from_input_resources(self):
        ''' 
        Need to take into account negative CO2 from CO2 and positive from elec
        Oxygen is not taken into account
        '''

        self.carbon_emissions[ResourceGlossary.Wood['name']] = self.resources_CO2_emissions[ResourceGlossary.Wood['name']] * \
            self.cost_details['wood_needs']

        return self.carbon_emissions[ResourceGlossary.Wood['name']]

    def grad_price_vs_energy_price(self):
        '''
        Overwrite techno_type method
        '''
        return {SyngasTechno.energy_name: 0 * np.identity(len(self.years))}

    def grad_price_vs_resources_price(self):
        '''
        Compute the gradient of global price vs resources prices
        '''
        syngas_kg = 1.0 * self.techno_infos_dict['syngas_yield']
        syngas_kwh = self.data_energy_dict['calorific_value'] * syngas_kg
        wood_needs = 1 / syngas_kwh
        return {ResourceGlossary.Wood['name']: np.identity(len(self.years)) * wood_needs}
