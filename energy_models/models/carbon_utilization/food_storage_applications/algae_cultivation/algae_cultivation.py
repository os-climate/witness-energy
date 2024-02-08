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
from energy_models.core.stream_type.energy_models.heat import lowtemperatureheat
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
from energy_models.core.techno_type.base_techno_models.carbon_utilization_techno import CUTechno


class AlgaeCultivation(CUTechno):

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs which depends on the technology
        """

        self.cost_details['elec_needs'] = self.get_electricity_needs()

        self.cost_details['heat_needs'] = self.get_heat_needs()

        self.cost_details[Electricity.name] = list(self.prices[Electricity.name] * self.cost_details['elec_needs']
                                                   )

        self.cost_details['accelerated_carbonation_needs'] = self.compute_accelerated_carbonation_need() / self.cost_details['efficiency']

        self.cost_details[ResourceGlossary.AcceleratedCarbonation['name']] = list(
            self.resources_prices[ResourceGlossary.AcceleratedCarbonation['name']] * self.cost_details['accelerated_carbonation_needs'] )

        self.cost_details['heat_needs'] = self.get_heat_needs()

        return self.cost_details[Electricity.name] + self.cost_details[ResourceGlossary.AcceleratedCarbonation['name']]

    def compute_CO2_emissions_from_input_resources(self):
        '''
        Need to take into account CO2 from electricity consumption
        '''

        self.carbon_intensity[Electricity.name] = self.energy_CO2_emissions[Electricity.name] * self.cost_details['elec_needs']

        self.carbon_intensity[ResourceGlossary.AcceleratedCarbonation['name']] = self.resources_CO2_emissions[ResourceGlossary.AcceleratedCarbonation['name']] * \
                                                                self.cost_details['accelerated_carbonation_needs']
        return self.carbon_intensity[Electricity.name] + self.carbon_intensity[ResourceGlossary.AcceleratedCarbonation['name']] - 1.0

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices 
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        elec_needs = self.get_electricity_needs()
        heat_needs = self.get_heat_needs()
        return {Electricity.name: np.identity(len(self.years)) * elec_needs,
                lowtemperatureheat.name: np.identity(len(self.years)) * heat_needs
                }

    def grad_price_vs_resources_price(self):
        '''
        Compute the gradient of global price vs resources prices
        '''
        accelerated_carbonation_needs = self.compute_accelerated_carbonation_need()
        efficiency = self.configure_efficiency()
        return {ResourceGlossary.AcceleratedCarbonation['name']: np.identity(len(self.years)) * accelerated_carbonation_needs / efficiency,
                }

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """
        
        # Consumption

        self.compute_other_primary_energy_costs()

        self.consumption_detailed[f'{Electricity.name} ({self.energy_unit})'] = self.cost_details['elec_needs'] * \
                                                                                self.production_detailed[f'{CUTechno.energy_name} ({self.product_energy_unit})']  # in kWH

        self.consumption_detailed[f'{lowtemperatureheat.name} ({self.energy_unit})'] = self.cost_details['heat_needs'] * \
                                                                            self.production_detailed[f'{CUTechno.energy_name} ({self.product_energy_unit})']

        self.consumption_detailed[f'accelerated_carbonation ({self.mass_unit})'] = self.cost_details['accelerated_carbonation_needs'] * \
                                                                 self.production_detailed[f'{CUTechno.energy_name} ({self.product_energy_unit})']   # in kWH

        self.production_detailed[f'{CarbonUtilization.building_material_name} ({self.mass_unit})'] = self.cost_details['heat_needs'] * \
                                                                                        self.production_detailed[f'{CUTechno.energy_name} ({self.product_energy_unit})'] * \
                                                                                        self.consumption_detailed[f'accelerated_carbonation ({self.mass_unit})'] / \
                                                                                        self.consumption_detailed[f'{lowtemperatureheat.name} ({self.energy_unit})']

    def compute_accelerated_carbonation_need(self):
        """
        'reaction': 'Cao + CO2 <--> CaCO3'
        unit : kg_AC/kg_CO2
        """
        # Buijs, W. and De Flart, S., 2017.
        # Direct air capture of CO2 with an amine resin: A molecular modeling study of the CO2 capturing process.
        # Industrial & engineering chemistry research, 56(43), pp.12297-12304.
        # https://pubs.acs.org/doi/pdf/10.1021/acs.iecr.7b02613 amine
        # efficiency
        CO2_mol_per_kg_accelerated_carbonation = 1.1
        CO2_molar_mass = 44.0

        kg_CO2_per_kg_accelerated_carbonation = CO2_mol_per_kg_accelerated_carbonation * CO2_molar_mass

        return 1 / kg_CO2_per_kg_accelerated_carbonation
