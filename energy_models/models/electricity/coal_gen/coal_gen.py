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
import numpy as np

from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.carbon_models.nitrous_oxide import N2O
from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from energy_models.core.stream_type.energy_models.solid_fuel import SolidFuel
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
from energy_models.core.stream_type.resources_models.water import Water
from energy_models.core.techno_type.base_techno_models.electricity_techno import ElectricityTechno


class CoalGen(ElectricityTechno):
    COPPER_RESOURCE_NAME = ResourceGlossary.Copper['name']

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs which depends on the technology 
        """

        # in kwh of fuel by kwh of electricity
        self.cost_details['solid_fuel_needs'] = self.techno_infos_dict['fuel_demand'] / \
                                                self.cost_details['efficiency']

        # need in kg/kWh
        self.cost_details['water_needs'] = self.techno_infos_dict['water_demand']

        # Cost of solid_fuel for 1 kWH of electricity - Efficiency removed as data is
        # the process global solid_fuel consumption
        self.cost_details[SolidFuel.name] = list(
            self.prices[SolidFuel.name] * self.cost_details['solid_fuel_needs'])

        # Cost of water for 1 kWH of electricity - Efficiency removed as data
        # is the process global water consumption
        self.cost_details[Water.name] = list(
            self.resources_prices[Water.name] * self.cost_details['water_needs'])

        # + self.cost_details[GlossaryEnergy.electricity]
        return self.cost_details[SolidFuel.name] + self.cost_details[Water.name]

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        """

        elec_needs = self.get_electricity_needs()

        # Consumption
        self.consumption_detailed[f'{SolidFuel.name} ({self.product_energy_unit})'] = self.cost_details[
                                                                                          'solid_fuel_needs'] * \
                                                                                      self.production_detailed[
                                                                                          f'{ElectricityTechno.energy_name} ({self.product_energy_unit})']  # in kWH
        self.consumption_detailed[f'{Water.name} ({self.mass_unit})'] = self.cost_details['water_needs'] * \
                                                                        self.production_detailed[
                                                                            f'{ElectricityTechno.energy_name} ({self.product_energy_unit})']  # in kg

        self.production_detailed[f'{ElectricityTechno.energy_name} ({self.product_energy_unit})'] = \
            self.production_detailed[
                f'{ElectricityTechno.energy_name} ({self.product_energy_unit})'] * (1.0 - elec_needs)
        self.production_detailed[f'{CarbonCapture.flue_gas_name} ({self.mass_unit})'] = self.techno_infos_dict[
                                                                                            'CO2_from_production'] * \
                                                                                        self.production_detailed[
                                                                                            f'{ElectricityTechno.energy_name} ({self.product_energy_unit})']
        self.production_detailed[f'{hightemperatureheat.name} ({self.product_energy_unit})'] = \
            self.consumption_detailed[f'{SolidFuel.name} ({self.product_energy_unit})'] - \
            self.production_detailed[f'{ElectricityTechno.energy_name} ({self.product_energy_unit})']

        self.compute_ghg_emissions(N2O.name, related_to=SolidFuel.name)

    def compute_consumption_and_installed_power(self):
        """
        Compute the resource consumption and the power installed (MW) of the technology for a given investment
        """

        # FOR ALL_RESOURCES DISCIPLINE

        copper_needs = self.get_theoretical_copper_needs(self)
        self.consumption_detailed[f'{self.COPPER_RESOURCE_NAME} ({self.mass_unit})'] = copper_needs * \
                                                                                       self.installed_power[
                                                                                           'new_power_production']  # in Mt

    @staticmethod
    def get_theoretical_copper_needs(self):
        """
        According to the IEA, Coal powered stations need 1150 kg of copper for each MW implemented
        Computing the need in Mt/MW
        """
        copper_need = self.techno_infos_dict['copper_needs'] / 1000 / 1000 / 1000

        return copper_need

    def compute_CO2_emissions_from_input_resources(self):
        '''
        Need to take into account  CO2 from coal extraction and electricity production
        '''

        self.carbon_intensity[SolidFuel.name] = self.energy_CO2_emissions[SolidFuel.name] * \
                                                self.cost_details['solid_fuel_needs']
        self.carbon_intensity[Water.name] = self.resources_CO2_emissions[Water.name] * \
                                            self.cost_details['water_needs']

        return self.carbon_intensity[SolidFuel.name] + self.carbon_intensity[Water.name]

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices 
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        solid_fuel_needs = self.techno_infos_dict['fuel_demand']
        efficiency = self.configure_efficiency()
        return {SolidFuel.name: np.identity(len(self.years)) * solid_fuel_needs / efficiency.values[:, np.newaxis]}

    def grad_price_vs_resources_price(self):
        '''
        Compute the gradient of global price vs resources prices
        '''
        water_needs = self.techno_infos_dict['water_demand']
        return {Water.name: np.identity(len(self.years)) * water_needs}

    def compute_dprod_dinvest(self, capex_list, invest_list, invest_before_year_start, techno_dict,
                              dcapex_list_dinvest_list):
        dprod_dinvest = ElectricityTechno.compute_dprod_dinvest(
            self, capex_list, invest_list, invest_before_year_start, techno_dict, dcapex_list_dinvest_list)
        elec_needs = self.get_electricity_needs()

        return dprod_dinvest * (1.0 - elec_needs)
