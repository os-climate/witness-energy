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

from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.resources_models.oxygen import Oxygen
from energy_models.core.stream_type.resources_models.resource_glossary import (
    ResourceGlossary,
)
from energy_models.core.stream_type.resources_models.water import Water
from energy_models.core.techno_type.base_techno_models.syngas_techno import SyngasTechno
from energy_models.glossaryenergy import GlossaryEnergy


class AutothermalReforming(SyngasTechno):
    syngas_COH2_ratio = 100.0  # in %

    def compute_resources_needs(self):
        # need in kg to produce 1kwh of syngas
        self.cost_details[f"{ResourceGlossary.CO2Resource}_needs"] = self.get_theoretical_CO2_needs() / self.cost_details['efficiency']
        # need in kg to produce 1kwh of syngas
        self.cost_details[f'{ResourceGlossary.OxygenResource}_needs'] = self.get_theoretical_O2_needs() / self.cost_details['efficiency']


    def compute_other_energies_needs(self):
        # need in kwh to produce 1kwh of syngas
        self.cost_details[f'{Methane.name}_needs'] = self.get_theoretical_CH4_needs() / self.cost_details['efficiency']


    def get_theoretical_CH4_needs(self):
        """
        Get methane needs in kWh CH4 /kWh syngas
        2 mol of CH4 for 3 mol of H2 and 3 mol of CO
        Warning : molar mass is in g/mol but we divide and multiply by one
        """

        mol_CH4 = 2.0
        mol_COH2 = 3.0
        methane_data = Methane.data_energy_dict
        methane_needs = mol_CH4 * methane_data['molar_mass'] * methane_data['calorific_value'] / \
                        (mol_COH2 * self.data_energy_dict['molar_mass'] *
                         self.data_energy_dict['calorific_value'])

        return methane_needs

    def get_theoretical_CO2_needs(self):
        ''' 
        Get water needs in kg CO2 /kWh H2
        1 mol of CO2 for 3 mol of CO and 3 mol of H2
        Warning : molar mass is in g/mol but we divide and multiply by one
        '''

        mol_CO2 = 1.0
        mol_COH2 = 3.0
        water_data = CO2.data_energy_dict
        water_needs = mol_CO2 * water_data['molar_mass'] / \
                      (mol_COH2 * self.data_energy_dict['molar_mass'] *
                       self.data_energy_dict['calorific_value'])

        return water_needs

    def get_theoretical_O2_needs(self):
        ''' 
        Get water needs in kg O2 /kWh H2
        1 mol of O2 for 3 mol of CO and 3 mol of H2
        Warning : molar mass is in g/mol but we divide and multiply by one
        '''

        mol_O2 = 1.0
        mol_COH2 = 3.0
        oxygen_data = Oxygen.data_energy_dict
        water_needs = mol_O2 * oxygen_data['molar_mass'] / \
                      (mol_COH2 * self.data_energy_dict['molar_mass'] *
                       self.data_energy_dict['calorific_value'])

        return water_needs

    def compute_production(self):
        # kg of H2O produced with 1kg of CH4
        H2Oprod = self.get_h2o_production()

        # total H2O production
        self.production_detailed[f'{Water.name} ({GlossaryEnergy.mass_unit})'] = self.production_detailed[
                                                                           f'{SyngasTechno.energy_name} ({self.product_unit})'] * \
                                                                       H2Oprod

    def get_h2o_production(self):
        """
        Get water produced when producing 1kg of Syngas
        """

        # water created when producing 1kg of CH4
        mol_H20 = 1
        mol_syngas = 3.0
        water_data = Water.data_energy_dict
        production_for_1kg = mol_H20 * \
                             water_data['molar_mass'] / \
                             (mol_syngas * self.data_energy_dict['molar_mass']
                              * self.data_energy_dict['calorific_value'])

        return production_for_1kg
