'''
Copyright 2022 Airbus SAS
Modifications on 2023/10/10-2023/11/16 Copyright 2023 Capgemini

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

from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.techno_type.base_techno_models.methane_techno import (
    MethaneTechno,
)
from energy_models.glossaryenergy import GlossaryEnergy


class FossilGas(MethaneTechno):
    NATURAL_GAS_RESOURCE_NAME = GlossaryEnergy.NaturalGasResource

    def get_fuel_needs(self):
        """
        Get the fuel needs for 1 kwh of the energy producted by the technology
        """
        if self.techno_infos_dict['fuel_demand'] != 0.0:
            fuel_need = self.check_energy_demand_unit(self.techno_infos_dict['fuel_demand_unit'],
                                                      self.techno_infos_dict['fuel_demand'])

        else:
            fuel_need = 0.0

        return fuel_need

    def compute_resources_needs(self):
        self.cost_details[f'{self.NATURAL_GAS_RESOURCE_NAME}_needs'] = self.get_fuel_needs() / Methane.data_energy_dict['calorific_value']  # kg/kWh

    def compute_other_energies_needs(self):
        self.cost_details[f'{GlossaryEnergy.electricity}_needs'] = self.get_electricity_needs()
        # needs in [kWh/kWh] divided by calorific value in [kWh/kg] to have
        # needs in [kg/kWh]


    def compute_production(self):
        # kg/kWh corresponds to Mt/TWh
        self.production_detailed[f'{CarbonCapture.flue_gas_name} ({GlossaryEnergy.mass_unit})'] = self.techno_infos_dict[
                                                                                            'CO2_from_production'] / \
                                                                                        self.data_energy_dict[
                                                                                            'calorific_value'] * \
                                                                                        self.production_detailed[
                                                                                            f'{MethaneTechno.energy_name} ({self.product_unit})']
        self.compute_ghg_emissions(Methane.emission_name)
        # self.production[f'{hightemperatureheat.name}] ({self.product_unit})'] = ((1 - self.techno_infos_dict['efficiency']) * \
        #      self.production[f'{Methane.name} ({self.product_unit})']) / \
        #       self.techno_infos_dict['efficiency']
