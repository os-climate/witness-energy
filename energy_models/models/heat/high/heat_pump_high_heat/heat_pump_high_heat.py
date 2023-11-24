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
import numpy as np
import pandas as pd

from climateeconomics.glossarycore import GlossaryCore
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from energy_models.core.techno_type.base_techno_models.high_heat_techno import highheattechno


class HeatPump(highheattechno):
    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs to produce 1kWh of Heat Pump Heat Generation
        """
        self.cost_details[f'{Electricity.name}_needs'] = self.get_theoretical_electricity_needs()
        self.cost_details[f'{Electricity.name}'] = \
            self.prices[Electricity.name] * \
            self.cost_details[f'{Electricity.name}_needs'] / \
            self.cost_details['efficiency']

        return self.cost_details[f'{Electricity.name}']

    def grad_price_vs_energy_price(self):
        elec_needs = self.get_theoretical_electricity_needs()
        heat_generated = elec_needs #self.get_theoretical_heat_generated()
        mean_temperature = self.techno_infos_dict['mean_temperature']
        output_temperature = self.techno_infos_dict['output_temperature']
        COP = output_temperature / (output_temperature - mean_temperature)
        efficiency = COP
        return {Electricity.name: np.identity(len(self.years)) * elec_needs / efficiency,
               hightemperatureheat.name: np.identity(len(self.years)) * heat_generated / efficiency,
               }
    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        """
        
        # Production
        self.production_detailed[f'{hightemperatureheat.name} ({self.product_energy_unit})'] = \
            self.production_detailed[f'{hightemperatureheat.name} ({self.product_energy_unit})'] / \
            self.cost_details['efficiency']

        # Consumption
        self.consumption_detailed[f'{Electricity.name} ({self.product_energy_unit})'] = self.cost_details[f'{Electricity.name}_needs'] * \
                                                                                        self.production_detailed[f'{hightemperatureheat.name} ({self.product_energy_unit})'] / \
                                                                                        self.cost_details['efficiency']

    def get_theoretical_electricity_needs(self):

        mean_temperature = self.techno_infos_dict['mean_temperature']
        output_temperature = self.techno_infos_dict['output_temperature']
        COP = output_temperature/(output_temperature - mean_temperature)
        electricity_needs = 1 / COP   # (heating_space*heat_required_per_meter_square) / COP

        return electricity_needs

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
