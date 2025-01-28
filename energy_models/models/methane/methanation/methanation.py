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

from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import (
    GaseousHydrogen,
)
from energy_models.core.stream_type.resources_models.water import Water
from energy_models.core.techno_type.base_techno_models.methane_techno import (
    MethaneTechno,
)
from energy_models.glossaryenergy import GlossaryEnergy


class Methanation(MethaneTechno):


    def compute_resources_needs(self):
        # in kg of CO2 for kWh of CH4
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.carbon_capture}_needs'] = self.get_theoretical_co2_needs() / self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

    def compute_other_streams_needs(self):
        # in kWh of H2 for kWh of CH4
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GaseousHydrogen.name}_needs'] = self.get_theoretical_hydrogen_needs() / self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

    def compute_byproducts_production(self):
        # kg of H2O produced with 1kWh of CH4
        H2Oprod = self.get_h2o_production()

        # total H2O production
        self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:{Water.name} ({GlossaryEnergy.mass_unit})'] = self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:'
                                                                           f'{MethaneTechno.stream_name} ({self.product_unit})'] * \
                                                                       H2Oprod

    def get_h2o_production(self):
        """
        Get water produced when producing 1kWh of CH4
        """

        # water created when producing 1kg of CH4
        mol_H20 = 2
        mol_CH4 = 1.0
        water_data = Water.data_energy_dict
        production_for_1kg = mol_H20 * \
                             water_data['molar_mass'] / \
                             (mol_CH4 * self.inputs['data_fuel_dict']['molar_mass']
                              * self.inputs['data_fuel_dict']['calorific_value'])

        return production_for_1kg

    def get_theoretical_hydrogen_needs(self):
        ''' 
        Get hydrogen needs in kWhH2 /kWh CH4
        4 mol of H2 for 1 mol of CH4
        Warning : molar mass is in g/mol but we divide and multiply by one
        '''

        mol_H2 = 4.0
        mol_CH4 = 1.0
        h2_data = GaseousHydrogen.data_energy_dict
        h2_needs = mol_H2 * h2_data['molar_mass'] * h2_data['calorific_value'] / \
                   (mol_CH4 * self.inputs['data_fuel_dict']['molar_mass'] *
                    self.inputs['data_fuel_dict']['calorific_value'])

        return h2_needs

    def get_theoretical_co2_needs(self):
        ''' 
        Get hydrogen needs in kWhH2 /kWh CH4
        4 mol of H2 for 1 mol of CH4
        Warning : molar mass is in g/mol but we divide and multiply by one
        '''

        mol_CO2 = 1.0
        mol_CH4 = 1.0
        co2_data = CO2.data_energy_dict
        co2_needs = mol_CO2 * co2_data['molar_mass'] / \
                    (mol_CH4 * self.inputs['data_fuel_dict']['molar_mass'] *
                     self.inputs['data_fuel_dict']['calorific_value'])

        return co2_needs

    def get_theoretical_co2_prod(self, unit='kg/kWh'):
        co2_needs = self.get_theoretical_co2_needs()

        if unit == 'kg/kWh':
            co2_prod = -co2_needs
        elif unit == 'kg/kg':
            co2_prod = -co2_needs * self.inputs['data_fuel_dict']['calorific_value']
        else:
            raise Exception("unit not handled")
        return co2_prod
