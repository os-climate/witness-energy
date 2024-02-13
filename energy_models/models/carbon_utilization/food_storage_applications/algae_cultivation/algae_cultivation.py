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

from energy_models.core.stream_type.carbon_models.carbon_utilization import CarbonUtilization
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
from energy_models.core.techno_type.base_techno_models.carbon_utilization_techno import CUTechno
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
from energy_models.core.stream_type.resources_models.water import Water


class AlgaeCultivation(CUTechno):

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs which depends on the technology
        """

        self.cost_details['elec_needs'] = self.get_electricity_needs()

        self.cost_details[Electricity.name] = list(self.prices[Electricity.name] * self.cost_details['elec_needs']
                                                   )
        self.cost_details[f'{Water.name}_needs'] = self.get_theoretical_water_needs()
        self.cost_details[Water.name] = \
            self.resources_prices[Water.name] * \
            self.cost_details[f'{Water.name}_needs'] / \
            self.cost_details['efficiency']

        self.cost_details['phosphorus_needs'] = self.compute_phosphorus_need() / self.techno_infos_dict[
            GlossaryEnergy.EnergyEfficiency]

        self.cost_details['nitrogen_needs'] = self.compute_nitrogen_need() / self.techno_infos_dict[
            GlossaryEnergy.EnergyEfficiency]

        return self.cost_details[Electricity.name] + self.cost_details[Water.name]

    def compute_CO2_emissions_from_input_resources(self):
        '''
        Need to take into account CO2 from electricity consumption
        '''

        self.carbon_intensity[Electricity.name] = self.energy_CO2_emissions[Electricity.name] * self.cost_details['elec_needs']

        self.carbon_intensity[ResourceGlossary.Phosphorus['name']] = self.resources_CO2_emissions[
                                                                        ResourceGlossary.Phosphorus['name']] * \
                                                                    self.cost_details['phosphorus_needs']

        self.carbon_intensity[ResourceGlossary.Nitrogen['name']] = self.resources_CO2_emissions[
                                                                      ResourceGlossary.Nitrogen['name']] * \
                                                                  self.cost_details['nitrogen_needs']

        return self.carbon_intensity[Electricity.name] + self.carbon_intensity[ResourceGlossary.Phosphorus['name']] + self.carbon_intensity[ResourceGlossary.Nitrogen['name']]

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        elec_needs = self.get_electricity_needs()

        return {Electricity.name: np.identity(len(self.years)) * elec_needs}

    def grad_price_vs_resources_price(self):
        '''
        Compute the gradient of global price vs resources prices
        '''
        efficiency = self.techno_infos_dict['efficiency']
        water_needs = self.get_theoretical_water_needs()

        return {Water.name: np.identity(len(self.years)) * water_needs / efficiency,
                }

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ?
        """

        # Production
        self.production_detailed[f'{BiomassDry.name} ({self.mass_unit})'] = self.production_detailed[f'{CUTechno.energy_name} ({self.product_energy_unit})']

        # Consumption

        self.compute_other_primary_energy_costs()

        self.consumption_detailed[f'{Electricity.name} ({self.energy_unit})'] = self.cost_details['elec_needs'] * \
                                                                                self.production_detailed[f'{CUTechno.energy_name} ({self.product_energy_unit})']  # in kWH

        self.consumption_detailed[f'nitrogen ({self.mass_unit})'] = self.techno_infos_dict['nitrogen_needs'] * \
                                                                   self.production_detailed[
                                                                       f'{CUTechno.energy_name} ({self.product_energy_unit})']  # in kWH

        self.consumption_detailed[f'phosphorus ({self.mass_unit})'] = self.techno_infos_dict['phosphorus_needs'] * \
                                                                     self.production_detailed[
                                                                         f'{CUTechno.energy_name} ({self.mass_unit})']  # in kWH

        self.consumption_detailed[f'{Water.name} ({self.mass_unit})'] = self.cost_details[f'{Water.name}_needs'] * \
                                                                        self.production_detailed[f'{CUTechno.energy_name} ({self.product_energy_unit})'] / \
                                                                        self.cost_details['efficiency']

        self.consumption_detailed[f'{CarbonUtilization.food_storage_name} ({self.mass_unit})'] = self.techno_infos_dict['co2_needs'] * \
                                                                                        self.production_detailed[f'{CUTechno.energy_name} ({self.product_energy_unit})']


    def compute_nitrogen_need(self):

        nitrogen_demand = self.techno_infos_dict['nitrogen_needs']

        nitrogen_needs = nitrogen_demand

        return nitrogen_needs

    def compute_phosphorus_need(self):
        phosphorus_demand = self.techno_infos_dict['phosphorus_needs']

        phosphorus_needs = phosphorus_demand

        return phosphorus_needs

    def get_theoretical_water_needs(self):

        water_demand = self.techno_infos_dict['water_demand']

        water_needs = water_demand

        return water_needs



