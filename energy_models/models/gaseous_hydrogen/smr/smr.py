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
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.resources_models.water import Water
from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.energy_models.electricity import Electricity


class SMR(GaseousHydrogenTechno):

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs which depends on the technology 
        """

        self.cost_details['elec_needs'] = self.get_electricity_needs()
        # in kwh of fuel by kwh of H2

        self.cost_details['methane_needs'] = self.get_theoretical_methane_needs()

        # need in kg
        self.cost_details['water_needs'] = self.get_theoretical_water_needs()

        # Cost of electricity for 1 kWH of H2
        self.cost_details['electricity'] = list(self.prices['electricity'] * self.cost_details['elec_needs']
                                                )
        # Cost of methane for 1 kWH of H2
        self.cost_details['methane'] = list(self.prices['methane'] * self.cost_details['methane_needs']
                                            / self.cost_details['efficiency'])

        # Cost of water for 1 kWH of H2
        self.cost_details['water'] = list(self.resources_prices['water'] * self.cost_details['water_needs']
                                          / self.cost_details['efficiency'])

        return self.cost_details['electricity'] + self.cost_details['methane'] + self.cost_details['water']

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """

        self.compute_primary_energy_production()

        co2_prod = self.get_theoretical_co2_prod()
        self.production[f'{CarbonCapture.flue_gas_name} ({self.mass_unit})'] = co2_prod * \
            self.production[f'{GaseousHydrogenTechno.energy_name} ({self.product_energy_unit})']

        # Consumption
        self.consumption[f'electricity ({self.product_energy_unit})'] = self.cost_details['elec_needs'] * \
            self.production[f'{GaseousHydrogenTechno.energy_name} ({self.product_energy_unit})']  # in kWH
        self.consumption[f'methane ({self.product_energy_unit})'] = self.cost_details['methane_needs'] * \
            self.production[f'{GaseousHydrogenTechno.energy_name} ({self.product_energy_unit})'] / \
            self.cost_details['efficiency']  # in kWH
        th_water_needs = self.get_theoretical_water_needs()
        self.consumption[f'water ({self.mass_unit})'] = th_water_needs * \
            self.production[f'{GaseousHydrogenTechno.energy_name} ({self.product_energy_unit})'] / \
            self.cost_details['efficiency']  # in kg

    def compute_CO2_emissions_from_input_resources(self):
        ''' 
        Need to take into account negative CO2 from CO2 and methane
        Oxygen is not taken into account
        '''

        self.carbon_emissions[f'{Methane.name}'] = self.energy_CO2_emissions[f'{Methane.name}'] * \
            self.cost_details['methane_needs'] / \
            self.cost_details['efficiency']

        self.carbon_emissions[f'{Electricity.name}'] = self.energy_CO2_emissions[f'{Electricity.name}'] * \
            self.cost_details['elec_needs']

        return self.carbon_emissions[f'{Methane.name}'] + self.carbon_emissions[f'{Electricity.name}']

    def get_theoretical_methane_needs(self):
        ''' 
        Get methane needs in kWh CH4 /kWh H2
        1 mol of CH4 for 4 mol of H2
        Warning : molar mass is in g/mol but we divide and multiply by one
        '''

        mol_CH4 = 1.0
        mol_H2 = 4.0
        methane_data = Methane.data_energy_dict
        methane_needs = mol_CH4 * methane_data['molar_mass'] * methane_data['calorific_value'] / \
            (mol_H2 * self.data_energy_dict['molar_mass'] *
             self.data_energy_dict['calorific_value'])

        return methane_needs

    def get_theoretical_water_needs(self):
        ''' 
        Get water needs in kg Water /kWh H2
        2 mol of H20 for 4 mol of H2
        Warning : molar mass is in g/mol but we divide and multiply by one
        '''

        mol_H20 = 2.0
        mol_H2 = 4.0
        water_data = Water.data_energy_dict
        water_needs = mol_H20 * water_data['molar_mass'] / \
            (mol_H2 * self.data_energy_dict['molar_mass'] *
             self.data_energy_dict['calorific_value'])

        return water_needs

    def get_theoretical_co2_prod(self, unit='kg/kWh'):
        ''' 
        Get co2 needs in kg co2 /kWh H2
        1 mol of CO2 for 4 mol of H2
        Warning : molar mass is in g/mol but we divide and multiply by one
        '''

        mol_CO2 = 1.0
        mol_H2 = 4.0
        co2_data = CO2.data_energy_dict

        if unit == 'kg/kWh':
            co2_prod = mol_CO2 * co2_data['molar_mass'] / \
                (mol_H2 * self.data_energy_dict['molar_mass'] *
                 self.data_energy_dict['calorific_value'])
        elif unit == 'kg/kg':
            co2_prod = mol_CO2 * co2_data['molar_mass'] / \
                (mol_H2 * self.data_energy_dict['molar_mass'])

        return co2_prod
