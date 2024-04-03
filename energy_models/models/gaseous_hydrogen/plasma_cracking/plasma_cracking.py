'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2023/11/16 Copyright 2023 Capgemini

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
import pandas as pd

from energy_models.core.stream_type.carbon_models.carbon import Carbon
from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.energy_type import EnergyType
from energy_models.core.techno_type.base_techno_models.gaseous_hydrogen_techno import GaseousHydrogenTechno
from energy_models.glossaryenergy import GlossaryEnergy


class PlasmaCracking(GaseousHydrogenTechno):
    """
    Plasmacracking class
    """

    def compute_other_energies_needs(self):
        self.cost_details[f'{GlossaryEnergy.electricity}_needs'] = self.get_electricity_needs()
        self.cost_details[f'{GlossaryEnergy.methane}_needs'] = self.get_theoretical_methane_needs() / self.cost_details['efficiency']


    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices 
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        elec_needs = self.get_electricity_needs()
        methane_needs = self.get_theoretical_methane_needs()
        efficiency = self.compute_efficiency()
        return {Electricity.name: np.identity(len(self.years)) * elec_needs,
                Methane.name: np.identity(len(self.years)) * methane_needs / efficiency.values}

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ?
        """

        C_per_h2 = self.get_theoretical_graphene_production()

        self.production_detailed[f'{Carbon.name} ({self.mass_unit})'] = C_per_h2 * \
                                                                        self.production_detailed[
                                                                            f'{GaseousHydrogenTechno.energy_name} ({self.product_energy_unit})']

        # Consumption
        self.consumption_detailed[f'{Electricity.name} ({self.product_energy_unit})'] = self.cost_details[
                                                                                            f'{GlossaryEnergy.electricity}_needs'] * \
                                                                                        self.production_detailed[
                                                                                            f'{GaseousHydrogenTechno.energy_name} ({self.product_energy_unit})']  # in kWH

        self.consumption_detailed[f'{Methane.name} ({self.product_energy_unit})'] = self.cost_details[f'{GlossaryEnergy.methane}_needs'] * \
                                                                                    self.production_detailed[
                                                                                        f'{GaseousHydrogenTechno.energy_name} ({self.product_energy_unit})'] / \
                                                                                    self.cost_details[
                                                                                        'efficiency']  # in kWH

    def compute_CO2_emissions_from_input_resources(self):
        ''' 
        Need to take into account positive CO2 from methane and elec prod
        Carbon capture (Methane is not burned but transformed is not taken into account)
        '''

        self.carbon_intensity[Electricity.name] = self.energy_CO2_emissions[Electricity.name] * \
                                                  self.cost_details[f'{GlossaryEnergy.electricity}_needs']

        self.carbon_intensity[Methane.name] = self.energy_CO2_emissions[Methane.name] * \
                                              self.cost_details[f'{GlossaryEnergy.methane}_needs'] / self.cost_details['efficiency']

        # self.energy_CO2_emissions[GlossaryEnergy.carbon_storage]
        C_per_h2 = self.get_theoretical_graphene_production()
        self.carbon_intensity['carbon storage'] = -C_per_h2 * \
                                                  CO2.data_energy_dict['molar_mass'] / \
                                                  Carbon.data_energy_dict['molar_mass']
        return self.carbon_intensity[Electricity.name] + self.carbon_intensity[Methane.name] + self.carbon_intensity[
            'carbon storage']

    def get_theoretical_graphene_production(self):
        ''' 
        Get methane needs in kg C /kWh H2
        1 mol of C for 2 mol of H2
        Warning : molar mass is in g/mol but we divide and multiply by one
        '''

        mol_C = 1.0
        mol_H2 = 2.0

        carbon_data = Carbon.data_energy_dict
        methane_needs = mol_C * carbon_data['molar_mass'] / \
                        (mol_H2 * self.data_energy_dict['molar_mass'] *
                         self.data_energy_dict['calorific_value'])

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
                        (mol_H2 * self.data_energy_dict['molar_mass'] *
                         self.data_energy_dict['calorific_value'])

        return methane_needs

    def get_theoretical_cO2_prod(self):
        ''' 
        Need to model the fact that carbon is created but not CO2
        '''

        return 0.0

    def compute_percentage_resource(self, CO2_credits, carbon_market_demand, ):

        percentage_resource = self.compute_revenues(
            CO2_credits, carbon_market_demand)

        percentage_resource['total_revenues'] = percentage_resource['hydrogen_sales_revenues'] + \
                                                percentage_resource['carbon_sales_revenues'] + \
                                                percentage_resource['carbon_storage_revenues']
        percentage_resource[GaseousHydrogenTechno.energy_name] = percentage_resource['hydrogen_sales_revenues'] / \
                                                                 percentage_resource['total_revenues'] * 100.

        return percentage_resource[[GlossaryEnergy.Years, GaseousHydrogenTechno.energy_name]]

    def compute_revenues(self, CO2_credits, carbon_market_demand):
        '''
        Carbon storage for carbon production higher than carbon demand
        '''
        quantity = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                 'carbon_production': self.production_detailed[
                                                          f'{Carbon.name} ({self.mass_unit})'].values * self.scaling_factor_techno_production,
                                 'hydrogen_production': self.production_detailed[
                                                            f'{GaseousHydrogenTechno.energy_name} ({EnergyType.unit})'] * self.scaling_factor_techno_production,
                                 'carbon_demand': carbon_market_demand['carbon_demand'].values,
                                 'CO2_credits': CO2_credits['CO2_credits'].values,
                                 'hydrogen_price': self.energy_prices[GaseousHydrogenTechno.energy_name],
                                 # 'carbon_price': ResourceGlossary.Carbon['price'],
                                 'carbon_price': self.resources_prices[Carbon.name],
                                 'is_prod_inf_demand': False,
                                 'is_storage_inf_storage_max': False
                                 })

        quantity['carbon_sales'] = (quantity['carbon_production'] - np.maximum(
            (quantity['carbon_production'] - quantity['carbon_demand']), 0.))
        quantity[GlossaryEnergy.carbon_storage] = np.maximum(
            (quantity['carbon_production'] - quantity['carbon_demand']), 0.)

        quantity['carbon_sales_revenues'] = quantity['carbon_sales'] * \
                                            quantity['carbon_price']
        quantity['carbon_storage_revenues'] = quantity[GlossaryEnergy.carbon_storage] * \
                                              Carbon.data_energy_dict['molar_mass'] / \
                                              CO2.data_energy_dict['molar_mass'] * quantity['CO2_credits']

        quantity['hydrogen_sales_revenues'] = quantity['hydrogen_production'] * \
                                              quantity['hydrogen_price']

        quantity['carbon_demand_sales_revenues'] = self.compute_revenue_gradient(quantity)
        quantity['carbon_storage_sales_revenues'] = self.compute_revenue_gradient(quantity)

        quantity.loc[quantity['carbon_production'] <=
                     quantity['carbon_demand'], 'is_prod_inf_demand'] = True

        return quantity

    '''
   GRADIENT PERCENTAGE RESOURCE
    '''

    def compute_revenue_gradient(self, quantity):
        a = quantity['carbon_production'] * Carbon.data_energy_dict['molar_mass'] * \
            quantity['CO2_credits'] / CO2.data_energy_dict['molar_mass']
        b = quantity['carbon_demand'] * (quantity['carbon_price'] - Carbon.data_energy_dict['molar_mass']
                                         * quantity['CO2_credits'] / CO2.data_energy_dict['molar_mass'])
        return a + b

    def grad_hydrogen_price_vs_energy_prices(self, energy):
        energy_prices = self.energy_prices
        if energy == GaseousHydrogenTechno.energy_name:
            return np.identity(len(energy_prices))
        else:
            return np.array(
                [[0] * len(energy_prices)] * len(energy_prices))

    def grad_percentage_resource_vs_energy_prices(self, CO2_credits, carbon_market_demand, energy):
        # search production and rename it
        # cols_carbon = [
        #     col for col in self.production.columns if 'carbon' in col]
        # cols_hydrogen = [
        #     col for col in self.production.columns if GaseousHydrogenTechno.energy_name in col]
        # techno_production = self.production[[GlossaryEnergy.Years, cols_carbon[0], cols_hydrogen[0]]].rename(columns={
        #     cols_carbon[0]: "carbon_production", cols_hydrogen[0]: "hydrogen_production"})
        # hydrogen_production = techno_production['hydrogen_production'].values
        quantity = self.compute_revenues(
            CO2_credits, carbon_market_demand)
        hydrogen_production = quantity['hydrogen_production'].values

        dhydrogen_price_denergy_prices = self.grad_hydrogen_price_vs_energy_prices(
            energy)

        # if carbon_production < carbon_demand
        quantity.loc[quantity['is_prod_inf_demand'] == True,
                     'A_value'] = quantity['carbon_sales_revenues']
        # if carbon_production > carbon_demand
        # carbon_storage
        quantity.loc[(quantity['is_prod_inf_demand'] == False),
                     'A_value'] = quantity['carbon_demand_sales_revenues']

        a = hydrogen_production * quantity['A_value'].values
        x = np.array([a, ] * len(self.years)).transpose()

        c = (
            np.power(quantity['hydrogen_sales_revenues'] + quantity['A_value'], 2)).values
        z = np.array([c, ] * len(self.years)).transpose()
        grad = np.divide((dhydrogen_price_denergy_prices * x), z,
                         out=np.zeros_like((dhydrogen_price_denergy_prices * x)), where=z != 0)
        return grad

    def grad_percentage_resource_vs_invest(self, CO2_credits, carbon_market_demand, dhydro_prod_dinvest,
                                           dcarbon_prod_dinvest):

        quantity = self.compute_revenues(
            CO2_credits, carbon_market_demand)
        hydrogen_price = quantity['hydrogen_price']

        # if carbon_production < carbon_demand
        quantity.loc[(quantity['is_prod_inf_demand'] == True),
                     'A_value'] = quantity['carbon_sales_revenues']

        # if carbon_production > carbon_demand
        # carbon_storage
        quantity.loc[(quantity['is_prod_inf_demand'] == False),
                     'A_value'] = quantity['carbon_demand_sales_revenues']

        # if carbon_production < carbon_demand
        quantity.loc[quantity['is_prod_inf_demand'] == True,
                     'B_value'] = quantity['carbon_price']
        # if carbon_production > carbon_demand
        # carbon_storage
        quantity.loc[(quantity['is_prod_inf_demand'] == False),
                     'B_value'] = Carbon.data_energy_dict['molar_mass'] / CO2.data_energy_dict['molar_mass'] * quantity[
            'CO2_credits']

        a = hydrogen_price.values * quantity['A_value'].values
        x = np.array([a, ] * len(self.years)).transpose()

        b = quantity['B_value'].values * \
            quantity['hydrogen_sales_revenues'].values
        y = np.array([b, ] * len(self.years)).transpose()

        c = (
            np.power(quantity['hydrogen_sales_revenues'] + quantity['A_value'], 2)).values
        z = np.array([c, ] * len(self.years)).transpose()

        grad = np.divide((dhydro_prod_dinvest * x - dcarbon_prod_dinvest * y), z,
                         out=np.zeros_like((dhydro_prod_dinvest * x - dcarbon_prod_dinvest * y)), where=z != 0)
        grad_wratio = (grad.T * list(self.applied_ratio['applied_ratio'])).T
        return grad_wratio

    def grad_percentage_resource_vs_ratio(self, CO2_credits, carbon_market_demand, dhydro_prod_dratio,
                                          dcarbon_prod_dratio):

        quantity = self.compute_revenues(
            CO2_credits, carbon_market_demand)
        hydrogen_price = quantity['hydrogen_price']

        # if carbon_production < carbon_demand
        quantity.loc[(quantity['is_prod_inf_demand'] == True),
                     'A_value'] = quantity['carbon_sales_revenues']

        # if carbon_production > carbon_demand
        # carbon_storage
        quantity.loc[(quantity['is_prod_inf_demand'] == False),
                     'A_value'] = quantity['carbon_demand_sales_revenues']

        # if carbon_production < carbon_demand
        quantity.loc[quantity['is_prod_inf_demand'] == True,
                     'B_value'] = quantity['carbon_price']
        # if carbon_production > carbon_demand
        # carbon_storage
        quantity.loc[(quantity['is_prod_inf_demand'] == False),
                     'B_value'] = Carbon.data_energy_dict['molar_mass'] / CO2.data_energy_dict['molar_mass'] * quantity[
            'CO2_credits']

        a = hydrogen_price.values * quantity['A_value'].values
        x = np.array([a, ] * len(self.years)).transpose()

        b = quantity['B_value'].values * \
            quantity['hydrogen_sales_revenues'].values
        y = np.array([b, ] * len(self.years)).transpose()

        c = (
            np.power(quantity['hydrogen_sales_revenues'] + quantity['A_value'], 2)).values
        z = np.array([c, ] * len(self.years)).transpose()

        grad = np.divide((dhydro_prod_dratio * x - dcarbon_prod_dratio * y), z,
                         out=np.zeros_like((dhydro_prod_dratio * x - dcarbon_prod_dratio * y)), where=z != 0)
        return grad

    def grad_percentage_resource_vs_resources_price(self, CO2_credits, carbon_market_demand,
                                                    dcarbon_price_dresources_price):

        quantity = self.compute_revenues(
            CO2_credits, carbon_market_demand)
        # hydrogen_price = quantity['hydrogen_price']

        # if carbon_production < carbon_demand
        quantity.loc[quantity['is_prod_inf_demand'] == True,
                     'A_value'] = quantity['carbon_sales_revenues']
        # if carbon_production > carbon_demand
        # carbon_storage
        quantity.loc[(quantity['is_prod_inf_demand'] == False),
                     'A_value'] = quantity['carbon_demand_sales_revenues']

        # if carbon_production < carbon_demand
        quantity.loc[(quantity['is_prod_inf_demand'] == True),
                     'B'] = quantity['carbon_sales']

        # if carbon_production > carbon_demand
        # carbon_storage
        quantity.loc[(quantity['is_prod_inf_demand'] == False),
                     'B'] = quantity['carbon_demand']

        a = quantity['hydrogen_sales_revenues'].values * \
            quantity['B'].values
        x = np.array([a, ] * len(self.years)).transpose()

        c = (
            np.power(quantity['hydrogen_sales_revenues'] + quantity['A_value'], 2)).values
        z = np.array([c, ] * len(self.years)).transpose()

        grad = np.divide(- dcarbon_price_dresources_price * x, z,
                         out=np.zeros_like((dcarbon_price_dresources_price * x)), where=z != 0)
        return grad
