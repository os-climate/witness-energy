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

from energy_models.core.techno_type.base_techno_models.electricity_techno import (
    ElectricityTechno,
)
from energy_models.glossaryenergy import GlossaryEnergy


class SolarThermal(ElectricityTechno):
    def compute_land_use(self):
        '''
        Compute required land for solar_pv
        '''
        self.outputs[f'{GlossaryEnergy.LandUseRequiredValue}:{GlossaryEnergy.Years}'] = self.years
        density_per_ha = self.inputs['techno_infos_dict']['density_per_ha']

        self.outputs[f'{GlossaryEnergy.LandUseRequiredValue}:Land use'] = \
            self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:{self.stream_name}'] / \
            density_per_ha

    def compute_byproducts_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ?
        """

        self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:{GlossaryEnergy.hightemperatureheat_energyname}'] =\
            ((1 - self.inputs['techno_infos_dict']['efficiency']) *
             self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:{self.stream_name}']) \
            / self.inputs['techno_infos_dict']['efficiency']
