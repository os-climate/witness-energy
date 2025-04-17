'''
Copyright 2024 Capgemini

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

from energy_models.core.techno_type.base_techno_models.carbon_capture_techno import (
    CCTechno,
)
from energy_models.glossaryenergy import GlossaryEnergy


class GenericFlueGasTechnoModel(CCTechno):
    def compute_energies_needs(self):
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.electricity}_needs'] = self.get_electricity_needs() / self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency'] * self.compute_electricity_variation_from_fg_ratio(self.inputs[f'{GlossaryEnergy.FlueGasMean}:{GlossaryEnergy.FlueGasMean}'], self.inputs['fg_ratio_effect'])

    def compute_capex(self):
        capex = super().compute_capex()
        capex *= self.compute_capex_variation_from_fg_ratio(
            self.inputs[f'{GlossaryEnergy.FlueGasMean}:{GlossaryEnergy.FlueGasMean}'], self.inputs['fg_ratio_effect'])

        return capex

    def compute_energies_demand(self):
        # Consumption
        self.outputs[f'{GlossaryEnergy.TechnoEnergyDemandsValue}:{GlossaryEnergy.Years}'] = self.years
        self.outputs[f'{GlossaryEnergy.TechnoEnergyDemandsValue}:{GlossaryEnergy.electricity}'] = \
            self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.electricity}_needs'] * \
            self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:{self.stream_name}'] / \
            self.compute_electricity_variation_from_fg_ratio(
                self.inputs[f'{GlossaryEnergy.FlueGasMean}:{GlossaryEnergy.FlueGasMean}'], self.inputs['fg_ratio_effect'])

