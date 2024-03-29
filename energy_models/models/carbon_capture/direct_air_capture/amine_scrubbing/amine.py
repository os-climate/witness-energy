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
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
from energy_models.core.techno_type.base_techno_models.carbon_capture_techno import CCTechno
from energy_models.glossaryenergy import GlossaryEnergy


class Amine(CCTechno):

    def compute_cost_of_other_energies_usage(self):
        self.cost_details[Electricity.name] = list(self.energy_prices[Electricity.name] * self.cost_details[f'{GlossaryEnergy.electricity}_needs'])
        self.cost_details[Methane.name] = list(self.energy_prices[Methane.name] * self.cost_details[f"{Methane.name}_needs"])

    
    def compute_other_energies_needs(self):
        self.cost_details[f'{GlossaryEnergy.electricity}_needs'] = self.get_electricity_needs()
        self.cost_details[f"{Methane.name}_needs"] = self.get_heat_needs()

    def compute_resources_needs(self):
        self.cost_details[f'{ResourceGlossary.AmineResource}_needs'] = self.compute_amine_need() / self.cost_details['efficiency']

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs which depends on the technology 

        """
        super().compute_other_primary_energy_costs()
        a = 1
        return self.cost_details[Electricity.name] + self.cost_of_resources_usage[ResourceGlossary.AmineResource] + \
               self.cost_details[Methane.name]

    def compute_CO2_emissions_from_input_resources(self):
        '''
        Need to take into account  CO2 from Methane and electricity consumption
        '''

        self.carbon_intensity[Methane.name] = self.energy_CO2_emissions[Methane.name] * self.cost_details[f"{Methane.name}_needs"]

        self.carbon_intensity[Electricity.name] = self.energy_CO2_emissions[Electricity.name] * self.cost_details[
            f'{GlossaryEnergy.electricity}_needs']

        self.carbon_intensity[ResourceGlossary.AmineResource] = self.resources_CO2_emissions[
                                                                    ResourceGlossary.AmineResource] * \
                                                                self.cost_details[f'{ResourceGlossary.AmineResource}_needs']
        return self.carbon_intensity[Methane.name] + self.carbon_intensity[Electricity.name] + self.carbon_intensity[
            ResourceGlossary.AmineResource] - 1.0

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices 
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        elec_needs = self.get_electricity_needs()
        heat_needs = self.get_heat_needs()
        return {Electricity.name: np.identity(len(self.years)) * elec_needs,
                Methane.name: np.identity(len(self.years)) * heat_needs
                }

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """

        # Consumption

        self.consumption_detailed[f'{Electricity.name} ({self.energy_unit})'] = self.cost_details[f'{GlossaryEnergy.electricity}_needs'] * \
                                                                                self.production_detailed[
                                                                                    f'{CCTechno.energy_name} ({self.product_energy_unit})']  # in kWH

        self.consumption_detailed[f'{Methane.name} ({self.energy_unit})'] = self.cost_details[f"{Methane.name}_needs"] * \
                                                                            self.production_detailed[
                                                                                f'{CCTechno.energy_name} ({self.product_energy_unit})']  # in kWH

        self.consumption_detailed[f'amine ({self.mass_unit})'] = self.cost_details[f'{ResourceGlossary.AmineResource}_needs'] * \
                                                                 self.production_detailed[
                                                                     f'{CCTechno.energy_name} ({self.product_energy_unit})']  # in kWH

        self.production_detailed[f'{CarbonCapture.flue_gas_name} ({self.mass_unit})'] = self.cost_details[
                                                                                            f"{Methane.name}_needs"] * \
                                                                                        self.production_detailed[
                                                                                            f'{CCTechno.energy_name} ({self.product_energy_unit})'] * \
                                                                                        Methane.data_energy_dict[
                                                                                            'CO2_per_use'] / \
                                                                                        Methane.data_energy_dict[
                                                                                            'calorific_value']

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
