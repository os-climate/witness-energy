'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/09-2023/11/15 Copyright 2023 Capgemini

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
from energy_models.core.techno_type.base_techno_models.wet_biomass_techno import (
    WetBiomassTechno,
)
from energy_models.glossaryenergy import GlossaryEnergy


class AnimalManure(WetBiomassTechno):

    def compute_energies_needs(self):
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.electricity}_needs'] = self.get_electricity_needs()

    def compute_byproducts_production(self):
        self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:{GlossaryEnergy.carbon_captured} (kg)'] = self.inputs['techno_infos_dict']['CO2_from_production'] / \
                                                                                                              self.inputs['data_energy_dict']['calorific_value'] * self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:{WetBiomassTechno.stream_name} (kWh)']