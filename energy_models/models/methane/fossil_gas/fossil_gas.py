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
        if self.inputs['techno_infos_dict']['fuel_demand'] != 0.0:
            fuel_need = self.check_energy_demand_unit(self.inputs['techno_infos_dict']['fuel_demand_unit'],
                                                      self.inputs['techno_infos_dict']['fuel_demand'])

        else:
            fuel_need = 0.0

        return fuel_need

    def compute_cost_of_resources_usage(self):
        """
        Cost of resource R = need of resource R x price of resource R

        Does not take natural gas price into account
        """
        cost_of_resource_usage = {
            GlossaryEnergy.Years: self.years,
        }
        self.outputs[f"{GlossaryEnergy.CostOfResourceUsageValue}:{GlossaryEnergy.Years}"] = self.years
        self.outputs[f"{GlossaryEnergy.CostOfResourceUsageValue}:Total"] = self.zeros_array
        for resource in self.inputs[GlossaryEnergy.ResourcesUsedForProductionValue]:
            if resource == GlossaryEnergy.NaturalGasResource:
                # Skip NaturalGasResource so not to count it twice
                self.outputs[f"{GlossaryEnergy.CostOfResourceUsageValue}:{resource}"] = 0.0
            else:
                self.outputs[f"{GlossaryEnergy.CostOfResourceUsageValue}:{resource}"] = self.outputs[f"{GlossaryEnergy.TechnoDetailedPricesValue}:{resource}_needs"].values * self.inputs[f"{GlossaryEnergy.ResourcesPriceValue}:{resource}"]
            self.outputs[f"{GlossaryEnergy.CostOfResourceUsageValue}:Total"] += self.outputs[f"{GlossaryEnergy.CostOfResourceUsageValue}:{resource}"]


    def compute_resources_needs(self):
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.NATURAL_GAS_RESOURCE_NAME}_needs'] = self.get_fuel_needs() / Methane.data_energy_dict['calorific_value']  # kg/kWh

    def compute_energies_needs(self):
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.electricity}_needs'] = self.get_electricity_needs()
        # needs in [kWh/kWh] divided by calorific value in [kWh/kg] to have
        # needs in [kg/kWh]

    def compute_co2_from_flue_gas_intensity_scope_1(self):
        return self.inputs['techno_infos_dict']['CO2_flue_gas_intensity_by_prod_unit'] / self.inputs['data_fuel_dict']['calorific_value']

    def compute_byproducts_production(self):
        pass
        # self.production[f'{GlossaryEnergy.hightemperatureheat_energyname}] ({self.product_unit})'] = ((1 - self.inputs['techno_infos_dict']['efficiency']) * \
        #      self.production[f'{Methane.name} ({self.product_unit})']) / \
        #       self.inputs['techno_infos_dict']['efficiency']
