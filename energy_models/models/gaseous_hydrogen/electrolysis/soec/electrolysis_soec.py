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

from energy_models.core.techno_type.base_techno_models.gaseous_hydrogen_techno import GaseousHydrogenTechno
from energy_models.core.stream_type.ressources_models.dioxygen import Dioxygen
from energy_models.core.stream_type.ressources_models.water import Water
from energy_models.core.stream_type.energy_models.electricity import Electricity

import numpy as np


class ElectrolysisSOEC(GaseousHydrogenTechno):
    """
    electrolysis class

    """

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs which depends on the technology 
        """

        # Efficiency ifor electrolysis means electric efficiency and is here to
        # compute the elec needs in kWh/kWh 1/efficiency
        self.cost_details['elec_needs'] = 1.0 / self.cost_details['efficiency']

        self.cost_details['water_needs'] = self.get_water_needs()

        self.data_config_creation = self.techno_infos_dict

        self.cost_details[Electricity.name] = self.cost_details['elec_needs'] * \
            self.prices[Electricity.name]

        # Cost of water for 1 kWH of H2
        self.cost_details[Water.name] = list(
            self.ressources_prices[Water.name] * self.cost_details['water_needs'])

        return self.cost_details[Electricity.name] + self.cost_details[Water.name]

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices 
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        efficiency = self.configure_efficiency()

        return {Electricity.name: np.identity(len(self.years)) / efficiency.values,
                }

    def compute_CO2_emissions_from_input_ressources(self):
        ''' 
        Need to take into account positive CO2 from methane and elec prod
        Carbon capture (Methane is not burned but transformed is not taken into account)
        '''

        self.carbon_emissions[Electricity.name] = self.energy_CO2_emissions[Electricity.name] * \
            self.cost_details['elec_needs']

        return self.carbon_emissions[Electricity.name]

    def get_water_needs(self):
        ''' 
        Get water needs in kg Water /kWh H2
        1 mol of H20 for 1 mol of H2
        Warning : molar mass is in g/mol but we divide and multiply by one
        '''

        mol_H20 = 1.0
        mol_H2 = 1.0
        water_data = Water.data_energy_dict
        water_needs = mol_H20 * water_data['molar_mass'] / \
            (mol_H2 * self.data_energy_dict['molar_mass'] *
             self.data_energy_dict['calorific_value'])

        return water_needs

    def get_oxygen_produced(self):
        ''' 
        Get oxygen needs in kg O2 /kWh H2
        1 mol of O2 for 2 mol of H2
        Warning : molar mass is in g/mol but we divide and multiply by one
        '''

        mol_O2 = 1.0
        mol_H2 = 2.0
        oxygen_data = Dioxygen.data_energy_dict
        water_needs = mol_O2 * oxygen_data['molar_mass'] / \
            (mol_H2 * self.data_energy_dict['molar_mass'] *
             self.data_energy_dict['calorific_value'])

        return water_needs

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """

        self.compute_primary_energy_production()

        o2_needs = self.get_oxygen_produced()
        self.production[f'O2 ({self.mass_unit})'] = o2_needs / \
            self.data_energy_dict['calorific_value'] * \
            self.production[f'{GaseousHydrogenTechno.energy_name} ({self.product_energy_unit})']

        # Consumption
        self.consumption[f'{Electricity.name} ({self.product_energy_unit})'] = self.cost_details['elec_needs'] * \
            self.production[f'{GaseousHydrogenTechno.energy_name} ({self.product_energy_unit})']  # in kWH

        self.consumption[f'{Water.name} ({self.mass_unit})'] = self.cost_details['water_needs'] / \
            self.data_energy_dict['calorific_value'] * \
            self.production[f'{GaseousHydrogenTechno.energy_name} ({self.product_energy_unit})']  # in kg
