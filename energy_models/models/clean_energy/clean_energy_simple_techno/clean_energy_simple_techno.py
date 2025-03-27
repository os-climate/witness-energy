'''
Copyright 2022 Airbus SAS
Modifications on 26/03/2024 Copyright 2024 Capgemini

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
from energy_models.core.techno_type.base_techno_models.renewable_techno import (
    RenewableTechno,
)
from energy_models.glossaryenergy import GlossaryEnergy


class CleanEnergySimpleTechno(RenewableTechno):

    def compute_specifif_costs_of_technos(self):
        self.outputs[f"{GlossaryEnergy.SpecificCostsForProductionValue}:{GlossaryEnergy.Years}"] = self.years
        self.outputs[f"{GlossaryEnergy.SpecificCostsForProductionValue}:{GlossaryEnergy.ResourcesPriceValue}"] = self.zeros_array + self.inputs['techno_infos_dict']['resource_price']
        self.outputs[f"{GlossaryEnergy.SpecificCostsForProductionValue}:Total"] = self.zeros_array + self.inputs['techno_infos_dict']['resource_price']
