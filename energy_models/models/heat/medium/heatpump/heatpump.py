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
from energy_models.core.stream_type.energy_models.heat import mediumtemperatureheat
from energy_models.core.techno_type.base_techno_models.heat_techno import mediumheattechno
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.heat import mediumtemperatureheat as mediumtempheat

import numpy as np


class HeatPump(mediumheattechno):

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
        heat_generated = self.get_theoretical_heat_generated()
        mean_temperature = mediumtemperatureheat.data_energy_dict['mean_temperature']
        output_temperature = mediumtemperatureheat.data_energy_dict['output_temperature']
        COP = output_temperature / (output_temperature - mean_temperature)
        efficiency = COP
        return {Electricity.name: np.identity(len(self.years)) * elec_needs / efficiency,
                mediumtemperatureheat.name: np.identity(len(self.years)) * heat_generated / efficiency,
                }
    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        """

        self.compute_primary_energy_production()

        # Production
        self.production[f'{mediumtempheat.name} ({self.product_energy_unit})'] = \
            self.production[f'{mediumtemperatureheat.name} ({self.product_energy_unit})'] / \
            self.cost_details['efficiency']

        # Consumption
        self.consumption[f'{Electricity.name} ({self.product_energy_unit})'] = self.cost_details[f'{Electricity.name}_needs'] * \
            self.production[f'{mediumtemperatureheat.name} ({self.product_energy_unit})'] / \
            self.cost_details['efficiency']


    def get_theoretical_electricity_needs(self):
        mean_temperature = self.techno_infos_dict['mean_temperature']
        output_temperature = self.techno_infos_dict['output_temperature']
        COP = output_temperature/(output_temperature - mean_temperature)
        electricity_needs = 1 / COP   # (heating_space*heat_required_per_meter_square) / COP

        return electricity_needs


