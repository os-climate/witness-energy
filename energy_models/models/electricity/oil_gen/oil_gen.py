'''
Copyright 2022 Airbus SAS
Modifications on 2023/09/25-2023/11/02 Copyright 2023 Capgemini

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

from energy_models.core.techno_type.base_techno_models.electricity_techno import ElectricityTechno
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.resources_models.water import Water
from energy_models.core.stream_type.energy_models.liquid_fuel import LiquidFuel
from energy_models.core.stream_type.carbon_models.nitrous_oxide import N2O
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
from energy_models.core.stream_type.energy_models.heat import hightemperatureheat



class OilGen(ElectricityTechno):

    COPPER_RESOURCE_NAME = ResourceGlossary.Copper['name']

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs which depends on the technology 
        """

        # in kwh of fuel by kwh of electricity
        self.cost_details['liquid_fuel_needs'] = self.techno_infos_dict['fuel_demand'] / \
            self.cost_details['efficiency']

        # need in kg/kWh
        self.cost_details['water_needs'] = self.techno_infos_dict['water_demand']

        # Cost of liquid_fuel for 1 kWH of electricity - Efficiency removed as data is
        # the process global liquid_fuel consumption
        self.cost_details[LiquidFuel.name] = list(
            self.prices[LiquidFuel.name] * self.cost_details['liquid_fuel_needs'])

        # Cost of water for 1 kWH of electricity - Efficiency removed as data
        # is the process global water consumption
        self.cost_details[Water.name] = list(
            self.resources_prices[Water.name] * self.cost_details['water_needs'])

        # + self.cost_details['electricity']
        return self.cost_details[LiquidFuel.name] + self.cost_details[Water.name]

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        """

        self.compute_primary_energy_production()
        #self.compute_power_production()
        elec_needs = self.get_electricity_needs()

        # Consumption
        self.consumption[f'{LiquidFuel.name} ({self.product_energy_unit})'] = self.cost_details['liquid_fuel_needs'] * \
            self.production[f'{ElectricityTechno.energy_name} ({self.product_energy_unit})']  # in kWH
        self.consumption[f'{Water.name} ({self.mass_unit})'] = self.cost_details['water_needs'] * \
            self.production[f'{ElectricityTechno.energy_name} ({self.product_energy_unit})']  # in kg

        self.production[f'{ElectricityTechno.energy_name} ({self.product_energy_unit})'] = self.production[
            f'{ElectricityTechno.energy_name} ({self.product_energy_unit})'] * (1.0 - elec_needs)
        self.production[f'{CarbonCapture.flue_gas_name} ({self.mass_unit})'] = self.techno_infos_dict['CO2_from_production'] * \
            self.production[f'{ElectricityTechno.energy_name} ({self.product_energy_unit})']
        self.production[f'{hightemperatureheat.name} ({self.product_energy_unit})'] = self.consumption[f'{LiquidFuel.name} ({self.product_energy_unit})'] - \
            self.production[f'{ElectricityTechno.energy_name} ({self.product_energy_unit})']

        self.compute_ghg_emissions(N2O.name, related_to=LiquidFuel.name)
    
    def compute_consumption_and_power_production(self):
        """
        Compute the resource consumption and the power installed (MW) of the technology for a given investment
        """
        self.compute_primary_power_production()

        # FOR ALL_RESOURCES DISCIPLINE

        copper_needs = self.get_theoretical_copper_needs(self)
        self.consumption[f'{self.COPPER_RESOURCE_NAME} ({self.mass_unit})'] = copper_needs * self.power_production['new_power_production'] # in Mt

    @staticmethod
    def get_theoretical_copper_needs(self):
        """
        No data found, therefore we make the assumption that it needs at least a generator which uses the same amount of copper as a gaz powered station
        It needs 1100 kg / MW
        Computing the need in Mt/MW
        """
        copper_need = self.techno_infos_dict['copper_needs'] / 1000 / 1000 / 1000

        return copper_need

    def compute_CO2_emissions_from_input_resources(self):
        '''
        Need to take into account  CO2 from coal extraction and electricity production
        '''

        self.carbon_emissions[LiquidFuel.name] = self.energy_CO2_emissions[LiquidFuel.name] * \
            self.cost_details['liquid_fuel_needs']
        self.carbon_emissions[Water.name] = self.resources_CO2_emissions[Water.name] * \
            self.cost_details['water_needs']

        return self.carbon_emissions[LiquidFuel.name] + self.carbon_emissions[Water.name]

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices 
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        liquid_fuel_needs = self.techno_infos_dict['fuel_demand']
        efficiency = self.configure_efficiency()
        return {LiquidFuel.name: np.identity(len(self.years)) * liquid_fuel_needs / efficiency[:, np.newaxis]}

    def grad_price_vs_resources_price(self):
        '''
        Compute the gradient of global price vs resources prices
        '''
        water_needs = self.techno_infos_dict['water_demand']
        return {Water.name: np.identity(len(self.years)) * water_needs}

    def compute_dprod_dinvest(self, capex_list, invest_list, invest_before_year_start, techno_dict, dcapex_list_dinvest_list):

        dprod_dinvest = ElectricityTechno.compute_dprod_dinvest(
            self, capex_list, invest_list, invest_before_year_start, techno_dict, dcapex_list_dinvest_list)
        elec_needs = self.get_electricity_needs()

        return dprod_dinvest * (1.0 - elec_needs)
