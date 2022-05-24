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
from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.methane import Methane

from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary

import numpy as np


class Amine(CCTechno):

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs which depends on the technology 

        """

        self.cost_details['elec_needs'] = self.get_electricity_needs()

        self.cost_details[Electricity.name] = list(self.prices[Electricity.name] * self.cost_details['elec_needs']
                                                   / self.cost_details['efficiency'])

        self.cost_details['amine_needs'] = self.compute_amine_need()

        self.cost_details[ResourceGlossary.Amine['name']] = list(
            self.resources_prices[ResourceGlossary.Amine['name']] * self.cost_details['amine_needs'] / self.cost_details['efficiency'])

        self.cost_details['heat_needs'] = self.get_heat_needs()

        self.cost_details[Methane.name] = list(self.prices[Methane.name] * self.cost_details['heat_needs']
                                                   / self.cost_details['efficiency'])

        return self.cost_details[Electricity.name] + self.cost_details[ResourceGlossary.Amine['name']] + self.cost_details[Methane.name]

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices 
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        elec_needs = self.get_electricity_needs()
        heat_needs = self.get_heat_needs()
        efficiency = self.configure_efficiency()
        return {Electricity.name: np.identity(len(self.years)) * elec_needs / efficiency,
                Methane.name: np.identity(len(self.years)) * heat_needs / efficiency
                }

    def grad_price_vs_resources_price(self):
        '''
        Compute the gradient of global price vs resources prices
        '''
        amine_needs = self.compute_amine_need()
        efficiency = self.configure_efficiency()
        return {ResourceGlossary.Amine['name']: np.identity(len(self.years)) * amine_needs / efficiency,
                }

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """
        self.compute_primary_energy_production()
        # Consumption

        self.consumption[f'{Electricity.name} ({self.energy_unit})'] = self.cost_details['elec_needs'] * \
            self.production[f'{CCTechno.energy_name} ({self.product_energy_unit})']  # in kWH

        self.consumption[f'{Methane.name} ({self.energy_unit})'] = self.cost_details['heat_needs'] * \
            self.production[f'{CCTechno.energy_name} ({self.product_energy_unit})']  # in kWH

        self.consumption[f'amine ({self.mass_unit})'] = self.cost_details['amine_needs'] * \
            self.production[f'{CCTechno.energy_name} ({self.product_energy_unit})'] / \
            self.techno_infos_dict['energy_efficiency']  # in kWH

    def compute_amine_need(self):
        """
        'reaction': 'RNH2(Amine) + CO2 <--> (RNHCOO-) + (H+)'
        unit : kg_Amine/kg_CO2
        """
        # Buijs, W. and De Flart, S., 2017.
        # Direct air capture of CO2 with an amine resin: A molecular modeling study of the CO2 capturing process.
        # Industrial & engineering chemistry research, 56(43), pp.12297-12304.
        # https://pubs.acs.org/doi/pdf/10.1021/acs.iecr.7b02613 amine
        # efficiency
        CO2_mol_per_kg_amine = 1.1
        CO2_molar_mass = 44.0

        kg_CO2_per_kg_amine = CO2_mol_per_kg_amine * CO2_molar_mass

        return 1 / kg_CO2_per_kg_amine
