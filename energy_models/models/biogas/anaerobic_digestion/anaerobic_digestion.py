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


from energy_models.core.stream_type.energy_models.wet_biomass import WetBiomass
from energy_models.core.techno_type.base_techno_models.biogas_techno import BioGasTechno
from energy_models.glossaryenergy import GlossaryEnergy


class AnaerobicDigestion(BioGasTechno):

    def compute_resources_needs(self):
        # Wet biomass_needs are in kg/m^3
        self.cost_details[f"{WetBiomass.name}_needs"] = self.techno_infos_dict[f"{WetBiomass.name}_needs"] / \
                                                 self.data_energy_dict['density'] / \
                                                 self.data_energy_dict['calorific_value']

    def compute_other_streams_needs(self):
        self.cost_details[f'{GlossaryEnergy.electricity}_needs'] = self.get_electricity_needs()
