'''
Copyright 2022 Airbus SAS
Modifications on 2023/10/10-2023/11/15 Copyright 2023 Capgemini

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


from energy_models.core.stream_type.energy_models.gaseous_hydrogen import (
    GaseousHydrogen,
)
from energy_models.core.techno_type.base_techno_models.liquid_hydrogen_techno import (
    LiquidHydrogenTechno,
)
from energy_models.glossaryenergy import GlossaryEnergy


class HydrogenLiquefaction(LiquidHydrogenTechno):
    """
    hydrogen_liquefaction class

    inputs

    """
    def compute_other_streams_needs(self):
        self.cost_details[f'{GlossaryEnergy.electricity}_needs'] = self.get_electricity_needs()

        # for 1kwh of gas hydrogen, we get 0.98
        self.cost_details[f'{GaseousHydrogen.name}_needs'] = 1 / \
                                              self.cost_details['efficiency']

    def compute_byproducts_production(self):
        pass
        # self.production[f'{lowtemperatureheat.name} ({self.product_unit})'] = (1 - self.techno_infos_dict['efficiency']) * \
        #     self.consumption[f'{GaseousHydrogen.name} ({self.product_unit})']/\
        #     self.techno_infos_dict['efficiency']

        # self.production[f'{lowtemperatureheat.name} ({self.product_unit})'] = \
        #     self.consumption[f'{GlossaryEnergy.electricity} ({self.product_unit})'] * self.techno_infos_dict['heat_recovery_factor']
