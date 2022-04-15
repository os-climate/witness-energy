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
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.resources_models.potassium_hydroxide import PotassiumHydroxide
from energy_models.core.stream_type.resources_models.calcium_oxide import CalciumOxide
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary

import numpy as np


class CalciumPotassium(CCTechno):

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs which depends on the technology 

        """

        self.cost_details['elec_needs'] = self.get_electricity_needs()

        self.cost_details[Electricity.name] = list(self.prices[Electricity.name] * self.cost_details['elec_needs']
                                                   / self.techno_infos_dict['energy_efficiency'])

        self.cost_details['potassium_needs'] = self.compute_potassium_need()

        self.cost_details['potassium'] = list(self.resources_prices[ResourceGlossary.Potassium['name']] * self.cost_details['potassium_needs']
                                              / self.techno_infos_dict['energy_efficiency'])

        self.cost_details['calcium_needs'] = self.compute_calcium_need()

        self.cost_details['calcium'] = list(self.resources_prices[ResourceGlossary.Calcium['name']] * self.cost_details['calcium_needs']
                                            / self.techno_infos_dict['energy_efficiency'])

        return self.cost_details[Electricity.name] + self.cost_details['potassium'] + self.cost_details['calcium']

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices 
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        elec_needs = self.get_electricity_needs()
        return {Electricity.name: np.identity(len(self.years)) * elec_needs / self.techno_infos_dict['energy_efficiency'],
                }

    def grad_price_vs_resources_price(self):
        '''
        Compute the gradient of global price vs resources prices
        '''
        calcium_needs = self.compute_calcium_need()
        potassium_needs = self.compute_potassium_need()
        efficiency = self.techno_infos_dict['energy_efficiency']
        return {
            ResourceGlossary.Calcium['name']: np.identity(len(self.years)) * calcium_needs / efficiency,
            ResourceGlossary.Potassium['name']: np.identity(len(self.years)) * potassium_needs / efficiency,
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

        self.consumption[f'CaO ({self.mass_unit})'] = self.cost_details['calcium_needs'] * \
            self.production[f'{CCTechno.energy_name} ({self.product_energy_unit})'] / \
            self.cost_details['efficiency']  # in kWH

        self.consumption[f'KOH ({self.mass_unit})'] = self.cost_details['potassium_needs'] * \
            self.production[f'{CCTechno.energy_name} ({self.product_energy_unit})'] / \
            self.cost_details['efficiency']  # in kWH

    def compute_potassium_need(self):
        """
        'reaction': 'CO2 + 2KOH --> H2O + K2CO3'
        unit : kg_potassium/kg_CO2
        """
        # https://pubs.acs.org/doi/pdf/10.1021/acs.iecr.7b02613 amine
        # efficiency
        KOH_molar_mass = PotassiumHydroxide.data_energy_dict['molar_mass']
        CO2_molar_mass = CarbonCapture.data_energy_dict['molar_mass']

        KOH_need = 2 * KOH_molar_mass / CO2_molar_mass * \
            (1 - self.techno_infos_dict['potassium_refound_efficiency'])

        return(KOH_need)

    def compute_calcium_need(self):
        """
        'reaction': 'K2CO3 + Ca(OH)2 --> 2KOH + CaCO3'
        unit : kg_calcium/kg_CO2
        """

        # efficiency
        CaO_molar_mass = CalciumOxide.data_energy_dict['molar_mass']
        CO2_molar_mass = CarbonCapture.data_energy_dict['molar_mass']

        CaO_need = (CaO_molar_mass / CO2_molar_mass) * \
            (1 - self.techno_infos_dict['calcium_refound_efficiency'])

        return CaO_need
