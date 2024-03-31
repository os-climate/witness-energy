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

from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.heat import mediumtemperatureheat
from energy_models.core.techno_type.base_techno_models.medium_heat_techno import mediumheattechno
from energy_models.glossaryenergy import GlossaryEnergy


class ElectricBoilerMediumHeat(mediumheattechno):

    def __init__(self, name):
        super().__init__(name)
        self.land_rate = None
        self.heat_flux = None
        self.heat_flux_distribution = None

    def compute_other_energies_needs(self):
        self.cost_details[f'{Electricity.name}_needs'] = self.get_theoretical_electricity_needs() / self.cost_details['efficiency']


    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs to produce 1kWh of heat
        """
        super().compute_other_primary_energy_costs()

        return self.cost_of_energies_usage[Electricity.name]

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices
        '''
        elec_needs = self.get_theoretical_electricity_needs()
        efficiency = self.techno_infos_dict['efficiency']
        return {Electricity.name: np.identity(len(self.years)) * elec_needs / efficiency,
                }

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        """

        # Consumption
        self.consumption_detailed[f'{Electricity.name} ({self.product_energy_unit})'] = self.cost_details[
                                                                                            f'{Electricity.name}_needs'] * \
                                                                                        self.production_detailed[
                                                                                            f'{mediumtemperatureheat.name} ({self.product_energy_unit})']

    def get_theoretical_electricity_needs(self):
        # we need as output kwh/kwh
        elec_demand = self.techno_infos_dict['elec_demand']

        return elec_demand

    def configure_input(self, inputs_dict):
        '''
        Configure with inputs_dict from the discipline
        '''
        self.land_rate = inputs_dict['flux_input_dict']['land_rate']

    def compute_heat_flux(self):
        land_rate = self.land_rate
        heat_price = self.compute_other_primary_energy_costs()
        self.heat_flux = land_rate / heat_price
        self.heat_flux_distribution = pd.DataFrame({GlossaryEnergy.Years: self.cost_details[GlossaryEnergy.Years],
                                                    'heat_flux': self.heat_flux})
        return self.heat_flux_distribution
