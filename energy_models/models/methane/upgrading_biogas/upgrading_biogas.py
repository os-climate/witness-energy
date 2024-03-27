'''
Copyright 2022 Airbus SAS
Modifications on 2023/10/10-2023/11/16 Copyright 2023 Capgemini

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
from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.core.stream_type.energy_models.biogas import BioGas
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.resources_models.monotethanolamine import Monotethanolamine
from energy_models.core.techno_type.base_techno_models.methane_techno import MethaneTechno
from energy_models.core.techno_type.base_techno_models.low_heat_techno import lowheattechno

class UpgradingBiogas(MethaneTechno):

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs to produce 1kg of CH4
        """

        self.cost_details['elec_needs'] = self.get_electricity_needs()
        # in kwh of fuel_production by kwh of H2

        self.cost_details['biogas_needs'] = self.get_biogas_needs()

        # Cost of electricity for 1 kWH of H2
        self.cost_details[Electricity.name] = list(
            self.prices[Electricity.name] * self.cost_details['elec_needs'])
        # Cost of methane for 1 kWH of H2
        self.cost_details[BioGas.name] = list(
            self.prices[BioGas.name] * self.cost_details['biogas_needs'])

        return self.cost_details[Electricity.name] + self.cost_details[BioGas.name]

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices 
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        elec_needs = self.get_electricity_needs()
        biogas_needs = self.get_biogas_needs()

        return {Electricity.name: np.identity(len(self.years)) * elec_needs,
                BioGas.name: np.identity(len(self.years)) * biogas_needs,
                }

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """

        # kg/kWh corresponds to Mt/TWh
        co2_prod = self.get_theoretical_co2_prod()
        self.production_detailed[f'{CarbonCapture.name} ({self.mass_unit})'] = co2_prod * \
                                                                               self.production_detailed[
                                                                                   f'{MethaneTechno.energy_name} ({self.product_energy_unit})']

        # Consumption
        self.consumption_detailed[f'{Electricity.name} ({self.product_energy_unit})'] = self.cost_details[
                                                                                            'elec_needs'] * \
                                                                                        self.production_detailed[
                                                                                            f'{MethaneTechno.energy_name} ({self.product_energy_unit})']  # in kWH
        self.consumption_detailed[f'{BioGas.name} ({self.product_energy_unit})'] = self.cost_details['biogas_needs'] * \
                                                                                   self.production_detailed[
                                                                                       f'{MethaneTechno.energy_name} ({self.product_energy_unit})']  # in kWH
        self.consumption_detailed[f'{Monotethanolamine.name} ({self.mass_unit})'] = self.get_MEA_loss() * \
                                                                                    self.production_detailed[
                                                                                        f'{MethaneTechno.energy_name} ({self.product_energy_unit})']

        # production
        self.production_detailed[f'{lowheattechno.energy_name} ({self.product_energy_unit})'] = \
            self.techno_infos_dict['low_heat_production'] * self.techno_infos_dict['useful_heat_recovery_factor']  * \
            self.production_detailed[f'{MethaneTechno.energy_name} ({self.product_energy_unit})']  # in TWH

    def get_biogas_needs(self):
        '''
        COmpute theoretical biogas needs with proportion of CO2 and CH4 given in biogas energy 
        Divide by efficiency for realistic demand
        '''
        biogas_data = BioGas.data_energy_dict
        mol_biogas = 1.0
        mol_CH4 = biogas_data['CH4_per_energy']
        biogas_needs = mol_biogas * biogas_data['molar_mass'] * biogas_data['calorific_value'] / \
                       (mol_CH4 * self.data_energy_dict['molar_mass'] *
                        self.data_energy_dict['calorific_value'])
        return biogas_needs / self.techno_infos_dict['efficiency']

    def get_MEA_loss(self):
        '''
        MonoEthanolAmine needs are in kg/m^3
        '''

        mea_loss = self.techno_infos_dict['MEA_needs'] / (
                self.data_energy_dict['density'] * self.data_energy_dict['calorific_value'])

        return mea_loss

    def get_theoretical_co2_prod(self, unit='kg/kWh'):
        ''' 
        Get CO2 prod from upgrading biogas
        With the fraction of CO2 in biogas considered
        '''
        biogas_data = BioGas.data_energy_dict
        mol_CO2 = 1.0 - biogas_data['CH4_per_energy']
        mol_CH4 = biogas_data['CH4_per_energy']
        co2_data = CO2.data_energy_dict

        co2_prod = 0

        if unit == 'kg/kWh':
            co2_prod = mol_CO2 * co2_data['molar_mass'] / \
                       (mol_CH4 * self.data_energy_dict['molar_mass'] *
                        self.data_energy_dict['calorific_value'])
        elif unit == 'kg/kg':
            co2_prod = mol_CO2 * co2_data['molar_mass'] / \
                       (mol_CH4 * self.data_energy_dict['molar_mass'])

        return co2_prod

    def compute_CO2_emissions_from_input_resources(self):
        '''
        Need to take into account  CO2 from electricity production and negative CO2 from biogas
        '''

        self.carbon_intensity[f'{BioGas.name}'] = self.energy_CO2_emissions[f'{BioGas.name}'] * \
                                                  self.cost_details['biogas_needs']

        self.carbon_intensity[Electricity.name] = self.energy_CO2_emissions[Electricity.name] * \
                                                  self.cost_details['elec_needs']

        # This CO2 is captured we do not take it into account in the CO2 emissions
        #         co2_prod = self.get_theoretical_co2_prod()
        #         self.carbon_emissions['CO2'] = -self.resources_CO2_emissions['CO2'] * \
        #             co2_prod
        # + self.carbon_emissions['CO2']
        return self.carbon_intensity[f'{BioGas.name}'] + self.carbon_intensity[Electricity.name]
