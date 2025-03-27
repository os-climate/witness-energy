'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/09-2023/11/14 Copyright 2023 Capgemini

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
from energy_models.core.stream_type.energy_models.fossil import Fossil
from energy_models.core.techno_type.base_techno_models.fossil_techno import FossilTechno
from energy_models.glossaryenergy import GlossaryEnergy


class FossilSimpleTechno(FossilTechno):


    def compute_specifif_costs_of_technos(self):
        self.outputs[f"{GlossaryEnergy.SpecificCostsForProductionValue}:{GlossaryEnergy.Years}"] = self.years
        self.outputs[f"{GlossaryEnergy.SpecificCostsForProductionValue}:{GlossaryEnergy.ResourcesPriceValue}"] = self.zeros_array + self.inputs['techno_infos_dict']['resource_price']
        self.outputs[f"{GlossaryEnergy.SpecificCostsForProductionValue}:Total"] = self.zeros_array + self.inputs['techno_infos_dict']['resource_price']


    def compute_co2_from_flue_gas_intensity_scope_1(self):
        # co2_from_raw_to_net will represent the co2 emitted from the use of
        # the fossil energy into other fossil energies. For example generation
        # of fossil electricity from fossil fuels

        co2_per_use = self.inputs['data_fuel_dict'][GlossaryEnergy.CO2PerUse] / \
                      self.inputs['data_fuel_dict']['calorific_value']
        co2_from_raw_to_net = (1.0 - Fossil.raw_to_net_production) * co2_per_use
        return (
                self.inputs['techno_infos_dict']['CO2_flue_gas_intensity_by_prod_unit'] / self.inputs['data_fuel_dict']['calorific_value'] +
                co2_from_raw_to_net
            )
