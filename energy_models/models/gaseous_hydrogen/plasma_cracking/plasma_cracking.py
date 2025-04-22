'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2024/06/26 Copyright 2023 Capgemini

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

from energy_models.core.stream_type.carbon_models.carbon import Carbon
from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.resources_models.resource_glossary import (
    ResourceGlossary,
)
from energy_models.core.techno_type.base_techno_models.gaseous_hydrogen_techno import (
    GaseousHydrogenTechno,
)
from energy_models.glossaryenergy import GlossaryEnergy


class PlasmaCracking(GaseousHydrogenTechno):
    """
    Plasmacracking class
    """
    def compute(self):
        super().compute()
        self.compute_revenues()
        self.compute_percentage_resource()
        self.add_percentage_resource_to_price()

    def add_percentage_resource_to_price(self):
        '''
        Add a percentage to the total price
        (for plasma cracking case we take only a percentage because the techno also creates graphene)
        '''
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.name}'] *= self.outputs[f'percentage_resource:{self.stream_name}'] / 100.
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.name}_wotaxes'] *= self.outputs[f'percentage_resource:{self.stream_name}'] / 100.

    def compute_energies_needs(self):
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.electricity}_needs'] = self.get_electricity_needs()
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.methane}_needs'] = self.get_theoretical_methane_needs() / self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

    def compute_byproducts_production(self):
        C_per_h2 = self.get_theoretical_solid_carbon_production()

        self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:{GlossaryEnergy.SolidCarbon} ({GlossaryEnergy.mass_unit})'] = \
            C_per_h2 * self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:{self.stream_name}']

    def get_theoretical_solid_carbon_production(self):
        '''
        Get methane needs in kg C /kWh H2
        1 mol of C for 2 mol of H2
        Warning : molar mass is in g/mol but we divide and multiply by one
        '''

        mol_C = 1.0
        mol_H2 = 2.0

        carbon_data = Carbon.data_energy_dict
        methane_needs = mol_C * carbon_data['molar_mass'] / \
                        (mol_H2 * self.inputs['data_fuel_dict']['molar_mass'] *
                         self.inputs['data_fuel_dict']['calorific_value'])

        return methane_needs

    def get_theoretical_methane_needs(self):
        '''
        Get methane needs in kWh CH4 /kWh H2
        1 mol of CH4 for 2 mol of H2
        Warning : molar mass is in g/mol but we divide and multiply by one
        '''

        mol_CH4 = 1.0
        mol_H2 = 2.0

        methane_data = Methane.data_energy_dict
        methane_needs = mol_CH4 * methane_data['molar_mass'] * methane_data['calorific_value'] / \
                        (mol_H2 * self.inputs['data_fuel_dict']['molar_mass'] *
                         self.inputs['data_fuel_dict']['calorific_value'])

        return methane_needs

    def get_theoretical_cO2_prod(self):
        '''
        Need to model the fact that carbon is created but not CO2
        '''

        return 0.0

    def compute_percentage_resource(self):

        self.outputs[f'percentage_resource:{GlossaryEnergy.Years}'] = self.years
        self.outputs['percentage_resource:total_revenues'] = \
            self.temp_variables['quantity:hydrogen_sales_revenues'] + \
            self.temp_variables['quantity:carbon_sales_revenues'] + \
            self.temp_variables['quantity:carbon_storage_revenues']

        self.outputs[f'percentage_resource:{self.stream_name}'] = \
            self.temp_variables['quantity:hydrogen_sales_revenues'] / \
            self.outputs['percentage_resource:total_revenues'] * 100.

    def compute_revenues(self):
        '''Carbon storage for carbon production higher than carbon demand'''
        self.temp_variables[f'quantity:{GlossaryEnergy.Years}'] = self.years
        self.temp_variables['quantity:carbon_production'] = self.outputs[f'{GlossaryEnergy.TechnoProductionValue}:{GlossaryEnergy.SolidCarbon} ({GlossaryEnergy.mass_unit})'] * 1e3
        self.temp_variables['quantity:hydrogen_production'] = self.outputs[f'{GlossaryEnergy.TechnoProductionValue}:{self.stream_name}'] * 1e3
        self.temp_variables['quantity:carbon_demand'] = self.inputs['market_demand:carbon_demand']
        self.temp_variables['quantity:CO2_credits'] = self.inputs['CO2_credits:CO2_credits']
        self.temp_variables['quantity:hydrogen_price'] = self.inputs[f'{GlossaryEnergy.StreamPricesValue}:{self.stream_name}']
        self.temp_variables['quantity:carbon_price'] = ResourceGlossary.Carbon['price']
        self.temp_variables['quantity:is_prod_inf_demand'] = False
        self.temp_variables['quantity:is_storage_inf_storage_max'] = False

        self.temp_variables['quantity:carbon_sales'] = (self.temp_variables['quantity:carbon_production'] - self.np.maximum(
            (self.temp_variables['quantity:carbon_production'] - self.temp_variables['quantity:carbon_demand']), 0.))
        self.temp_variables[f'quantity:{GlossaryEnergy.carbon_storage}'] = self.np.maximum(
            (self.temp_variables['quantity:carbon_production'] - self.temp_variables['quantity:carbon_demand']), 0.)

        self.temp_variables['quantity:carbon_sales_revenues'] = self.temp_variables['quantity:carbon_sales'] * \
                                                                self.temp_variables['quantity:carbon_price']
        self.temp_variables['quantity:carbon_storage_revenues'] = self.temp_variables[f'quantity:{GlossaryEnergy.carbon_storage}'] * \
                                                                  Carbon.data_energy_dict['molar_mass'] / \
                                                                  CO2.data_energy_dict['molar_mass'] * self.temp_variables['quantity:CO2_credits']

        self.temp_variables['quantity:hydrogen_sales_revenues'] = self.temp_variables['quantity:hydrogen_production'] * \
                                                                  self.temp_variables['quantity:hydrogen_price']

        self.outputs[f'carbon_quantity_to_be_stored:{GlossaryEnergy.Years}'] = self.years
        self.outputs[f'carbon_quantity_to_be_stored:{GlossaryEnergy.carbon_storage}'] = self.temp_variables[f'quantity:{GlossaryEnergy.carbon_storage}']


