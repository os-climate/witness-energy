'''
Copyright 2023 Capgemini

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
from energy_models.core.stream_type.energy_models.heat import mediumtemperatureheat
from energy_models.core.techno_type.base_techno_models.medium_heat_techno import mediumheattechno
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture

import numpy as np
import pandas as pd

class NaturalGasMediumHeat(mediumheattechno):

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs to produce 1kWh of heat
        """
        self.cost_details[f'{Methane.name}_needs'] = self.get_theoretical_methane_needs()

        self.cost_details[f'{Methane.name}'] = \
            self.prices[f'{Methane.name}'] * \
            self.cost_details[f'{Methane.name}_needs'] / \
            self.cost_details['efficiency']

        # methane_needs

        # output needed in this method is in $/kwh of heat
        # to do so I need to know how much methane is used to produce 1kwh of heat (i need this information in kwh) : methane_needs is in kwh of methane/kwh of heat
        # kwh/kwh * price of methane ($/kwh) : kwh/kwh * $/kwh  ----> $/kwh  : price of methane is in self.prices[f'{Methane.name}']
        # and then we divide by efficiency


        return self.cost_details[f'{Methane.name}']

    def grad_price_vs_energy_price_calc(self):
        '''
        Compute the gradient of global price vs energy prices
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        methane_needs = self.get_theoretical_methane_needs()
        efficiency = self.techno_infos_dict['efficiency']

        return {
                'natural_gas_resource': np.identity(len(self.years)) * methane_needs / efficiency
                }

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        """

        self.compute_primary_energy_production()

        # Consumption

        self.consumption[f'{Methane.name} ({self.product_energy_unit})'] = self.cost_details[f'{Methane.name}_needs'] * \
            self.production[f'{mediumtemperatureheat.name} ({self.product_energy_unit})']

        # CO2 production
        self.production[f'{CarbonCapture.flue_gas_name} ({self.mass_unit})'] = Methane.data_energy_dict['CO2_per_use'] / \
                                                                               Methane.data_energy_dict['calorific_value'] * \
            self.consumption[f'{Methane.name} ({self.product_energy_unit})']

    def compute_CO2_emissions_from_input_resources(self):
        '''
        Need to take into account CO2 from Methane production
        '''

        self.carbon_emissions[Methane.name] = self.energy_CO2_emissions[Methane.name] * \
            self.cost_details[f'{Methane.name}_needs']

        return self.carbon_emissions[f'{Methane.name}']

    def get_theoretical_methane_needs(self):
        # we need as output kwh/kwh
        methane_demand = self.techno_infos_dict['methane_demand']

        methane_needs = methane_demand

        return methane_needs

    def get_theoretical_co2_prod(self, unit='kg/kWh'):
        co2_captured__production = self.techno_infos_dict['co2_captured__production']
        heat_density = Methane.data_energy_dict['density']  # kg/m^3
        heat_calorific_value = Methane.data_energy_dict['calorific_value']  # kWh/kg

        co2_prod = co2_captured__production / (heat_density * heat_calorific_value)

        return co2_prod

    def configure_input(self, inputs_dict):
        '''
        Configure with inputs_dict from the discipline
        '''
        self.land_rate = inputs_dict['flux_input_dict']['land_rate']

    def compute_heat_flux(self):
        land_rate = self.land_rate
        heat_price = self.compute_other_primary_energy_costs()
        self.heat_flux = land_rate/heat_price
        self.heat_flux_distribution = pd.DataFrame({GlossaryCore.Years: self.cost_details[GlossaryCore.Years],
                                               'heat_flux': self.heat_flux})
        return self.heat_flux_distribution


