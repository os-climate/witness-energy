'''
Copyright 2022 Airbus SAS
Modifications on 2023/09/19-2023/11/03 Copyright 2023 Capgemini

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
from climateeconomics.glossarycore import GlossaryCore
from energy_models.core.techno_type.base_techno_models.carbon_capture_techno import CCTechno
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.resources_models.potassium_hydroxide import PotassiumHydroxide
from energy_models.core.stream_type.resources_models.calcium_oxide import CalciumOxide
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2

import numpy as np


class CalciumPotassium(CCTechno):

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs which depends on the technology 

        """

        self.cost_details['elec_needs'] = self.get_electricity_needs()

        self.cost_details[Electricity.name] = list(self.prices[Electricity.name] * self.cost_details['elec_needs']
                                                   )

        self.cost_details['potassium_needs'] = self.compute_potassium_need() / self.techno_infos_dict[GlossaryCore.EnergyEfficiency]

        self.cost_details['potassium'] = list(self.resources_prices[ResourceGlossary.Potassium['name']] * self.cost_details['potassium_needs']
                                              )

        self.cost_details['calcium_needs'] = self.compute_calcium_need() / self.techno_infos_dict[GlossaryCore.EnergyEfficiency]

        self.cost_details['calcium'] = list(self.resources_prices[ResourceGlossary.Calcium['name']] * self.cost_details['calcium_needs']
                                            )
        self.cost_details['heat_needs'] = self.get_heat_needs()

        self.cost_details[Methane.name] = list(self.prices[Methane.name] * self.cost_details['heat_needs']
                                                   )

        return self.cost_details[Electricity.name] + self.cost_details['potassium'] + self.cost_details['calcium'] + self.cost_details[Methane.name]


    def compute_CO2_emissions_from_input_resources(self):
        '''
        Need to take into account  CO2 from coal extraction and electricity production
        '''

        self.carbon_emissions[Methane.name] = self.energy_CO2_emissions[Methane.name] * self.cost_details['heat_needs']

        self.carbon_emissions[Electricity.name] = self.energy_CO2_emissions[Electricity.name] * self.cost_details['elec_needs']

        self.carbon_emissions[ResourceGlossary.Potassium['name']] = self.resources_CO2_emissions[ResourceGlossary.Potassium['name']] * \
                                                            self.cost_details['potassium_needs']

        self.carbon_emissions[ResourceGlossary.Calcium['name']] = self.resources_CO2_emissions[ResourceGlossary.Calcium['name']] * \
                                                            self.cost_details['calcium_needs']



        return self.carbon_emissions[Methane.name] + self.carbon_emissions[Electricity.name] + self.carbon_emissions[ResourceGlossary.Potassium['name']] + self.carbon_emissions[ResourceGlossary.Calcium['name']]


    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices 
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        elec_needs = self.get_electricity_needs()
        heat_needs = self.get_heat_needs()

        return {Electricity.name: np.identity(len(self.years)) * elec_needs ,
                Methane.name: np.identity(len(self.years)) * heat_needs
                }

    def grad_price_vs_resources_price(self):
        '''
        Compute the gradient of global price vs resources prices
        '''
        calcium_needs = self.compute_calcium_need()
        potassium_needs = self.compute_potassium_need()
        efficiency = self.techno_infos_dict[GlossaryCore.EnergyEfficiency]
        return {
            ResourceGlossary.Calcium['name']: np.identity(len(self.years)) * calcium_needs / efficiency,
            ResourceGlossary.Potassium['name']: np.identity(len(self.years)) * potassium_needs / efficiency,
                }

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """

        
        # Consumption

        self.consumption_detailed[f'{Electricity.name} ({self.energy_unit})'] = self.cost_details['elec_needs'] * \
                                                                                self.production_detailed[f'{CCTechno.energy_name} ({self.product_energy_unit})'] # in kWH

        self.consumption_detailed[f'{Methane.name} ({self.energy_unit})'] = self.cost_details['heat_needs'] * \
                                                                            self.production_detailed[f'{CCTechno.energy_name} ({self.product_energy_unit})']  # in kWH

        self.consumption_detailed[f'calcium ({self.mass_unit})'] = self.cost_details['calcium_needs'] * \
                                                                   self.production_detailed[f'{CCTechno.energy_name} ({self.product_energy_unit})']   # in kWH

        self.consumption_detailed[f'potassium ({self.mass_unit})'] = self.cost_details['potassium_needs'] * \
                                                                     self.production_detailed[f'{CCTechno.energy_name} ({self.product_energy_unit})']  # in kWH

        self.production_detailed[f'{CarbonCapture.flue_gas_name} ({self.mass_unit})'] = self.cost_details['heat_needs'] * \
                                                                                        self.production_detailed[
                                                                                   f'{CCTechno.energy_name} ({self.product_energy_unit})'] * \
                                                                                        Methane.data_energy_dict['CO2_per_use'] / \
                                                                                        Methane.data_energy_dict[
                                                                                   'calorific_value']
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
