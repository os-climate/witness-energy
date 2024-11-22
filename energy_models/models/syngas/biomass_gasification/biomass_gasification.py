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

from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.techno_type.base_techno_models.syngas_techno import SyngasTechno
from energy_models.glossaryenergy import GlossaryEnergy


class BiomassGasification(SyngasTechno):
    syngas_COH2_ratio = 26.0 / 31.0 * 100.0  # in %

    def compute_resources_needs(self):
        self.cost_details[f'{GlossaryEnergy.WaterResource}_needs'] = self.techno_infos_dict['kgH20_perkgSyngas'] / \
                                                                        self.data_energy_dict['calorific_value']

    def compute_other_streams_needs(self):
        self.cost_details[f'{GlossaryEnergy.electricity}_needs'] = self.get_electricity_needs()
        # in kwh of fuel by kwh of syngas

        self.cost_details[f'{BiomassDry.name}_needs'] = self.techno_infos_dict['biomass_demand']


    def compute_byproducts_production(self):
        self.compute_ghg_emissions(Methane.emission_name)
