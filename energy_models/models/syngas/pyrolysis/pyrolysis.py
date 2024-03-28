'''
Copyright 2022 Airbus SAS
Modifications on 2023/09/25-2023/11/16 Copyright 2023 Capgemini

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
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
from energy_models.core.techno_type.base_techno_models.syngas_techno import SyngasTechno


class Pyrolysis(SyngasTechno):
    syngas_COH2_ratio = 0.5 / 0.45 * 100.0  # in %

    def compute_resources_needs(self):
        # syngas produced in kg by 1kg of wood
        syngas_kg = 1.0 * self.techno_infos_dict['syngas_yield']

        # kwh produced by 1kg of wood

        syngas_kwh = self.data_energy_dict['calorific_value'] * syngas_kg

        # wood needs in kg to produce 1kWh of syngas
        self.cost_details[f"{ResourceGlossary.WoodResource}_needs"] = 1 / syngas_kwh

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs which depends on the technology 
        """

        super().compute_other_primary_energy_costs()

        return self.cost_of_resources_usage[ResourceGlossary.WoodResource]

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """

        self.production_detailed[f'{CarbonCapture.flue_gas_name} ({self.mass_unit})'] = self.techno_infos_dict[
                                                                                            'CO2_from_production'] / \
                                                                                        self.data_energy_dict[
                                                                                            'calorific_value'] * \
                                                                                        self.production_detailed[
                                                                                            f'{SyngasTechno.energy_name} ({self.product_energy_unit})']

        self.production_detailed[f'char ({self.mass_unit})'] = self.production_detailed[
                                                                   f'{SyngasTechno.energy_name} ({self.product_energy_unit})'] * \
                                                               self.techno_infos_dict['char_yield'] / \
                                                               self.techno_infos_dict['syngas_yield']

        self.production_detailed[f'bio_oil ({self.mass_unit})'] = self.production_detailed[
                                                                      f'{SyngasTechno.energy_name} ({self.product_energy_unit})'] * \
                                                                  self.techno_infos_dict['bio_oil_yield'] / \
                                                                  self.techno_infos_dict['syngas_yield']

        self.consumption_detailed[f'wood ({self.mass_unit})'] = self.cost_details[f"{ResourceGlossary.WoodResource}_needs"] * \
                                                                self.production_detailed[
                                                                    f'{SyngasTechno.energy_name} ({self.product_energy_unit})']

        # self.consumption[f'{mediumheattechno.energy_name} ({self.product_energy_unit})'] = \
        #     self.techno_infos_dict['medium_heat_production'] * \
        #     self.production[f'{SyngasTechno.energy_name} ({self.product_energy_unit})']  # in TWH

    def compute_CO2_emissions_from_input_resources(self):
        ''' 
        Need to take into account negative CO2 from CO2 and positive from elec
        Oxygen is not taken into account
        '''

        self.carbon_intensity[ResourceGlossary.WoodResource] = self.resources_CO2_emissions[
                                                                   ResourceGlossary.WoodResource] * \
                                                               self.cost_details[f"{ResourceGlossary.WoodResource}_needs"]

        return self.carbon_intensity[ResourceGlossary.WoodResource]

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
        return {ResourceGlossary.WoodResource: np.identity(len(self.years)) * wood_needs}
