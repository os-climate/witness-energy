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

from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.techno_type.base_techno_models.electricity_techno import ElectricityTechno
from energy_models.core.techno_type.base_techno_models.high_heat_techno import highheattechno


class CHPHighHeat(highheattechno):
    def compute_other_energies_needs(self):
        self.cost_details[f'{Methane.name}_needs'] = self.get_theoretical_methane_needs()

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs to produce 1kWh of heat
        """
        super().compute_other_primary_energy_costs()

        return self.cost_of_energies_usage[Methane.name]

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        methane_needs = self.get_theoretical_methane_needs()
        efficiency = self.techno_infos_dict['efficiency']

        return {
            Methane.name: np.identity(len(self.years)) * methane_needs / efficiency
        }

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        """

        self.consumption_detailed[f'{Methane.name} ({self.product_energy_unit})'] = self.cost_details[
                                                                                        f'{Methane.name}_needs'] * \
                                                                                    self.production_detailed[
                                                                                        f'{hightemperatureheat.name} ({self.product_energy_unit})']

        # CO2 production
        self.production_detailed[f'{CarbonCapture.flue_gas_name} ({self.mass_unit})'] = Methane.data_energy_dict[
                                                                                            'CO2_per_use'] / \
                                                                                        Methane.data_energy_dict[
                                                                                            'calorific_value'] * \
                                                                                        self.consumption_detailed[
                                                                                            f'{Methane.name} ({self.product_energy_unit})']

        self.production_detailed[f'{ElectricityTechno.energy_name} ({self.product_energy_unit})'] = \
            (self.production_detailed[f'{hightemperatureheat.name} ({self.product_energy_unit})'] /
             (1 - self.techno_infos_dict['efficiency'])) - self.production_detailed[
                f'{hightemperatureheat.name} ({self.product_energy_unit})']

    def compute_CO2_emissions_from_input_resources(self):
        '''
        Need to take into account CO2 from Methane production
        '''

        self.carbon_intensity[Methane.name] = self.energy_CO2_emissions[Methane.name] * \
                                              self.cost_details[f'{Methane.name}_needs']

        return self.carbon_intensity[f'{Methane.name}']

    def get_theoretical_methane_needs(self):
        # we need as output kwh/kwh
        methane_demand = self.techno_infos_dict['methane_demand']

        methane_needs = methane_demand

        return methane_needs

    def get_theoretical_electricity_needs(self):
        # we need as output kwh/kwh
        elec_demand = self.techno_infos_dict['elec_demand']

        return elec_demand

    def get_theoretical_co2_prod(self, unit='kg/kWh'):
        co2_captured__production = self.techno_infos_dict['co2_captured__production']
        heat_density = Methane.data_energy_dict['density']  # kg/m^3
        heat_calorific_value = Methane.data_energy_dict['calorific_value']  # kWh/kg

        co2_prod = co2_captured__production / (heat_density * heat_calorific_value)

        return co2_prod
