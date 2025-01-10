'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2023/11/16 Copyright 2023 Capgemini

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

import pandas as pd

from energy_models.core.stream_type.carbon_models.carbon import Carbon
from energy_models.core.techno_type.base_techno_models.carbon_storage_techno import (
    CSTechno,
)
from energy_models.glossaryenergy import GlossaryEnergy


class PureCarbonSS(CSTechno):
    CARBON_TO_BE_STORED_CONSTRAINT = 'carbon_to_be_stored_constraint'

    def __init__(self, name):
        super().__init__(name)
        self.carbon_to_be_stored_constraint = None

    def compute_resources_needs(self):
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.SolidCarbon}_needs'] = 1 / Carbon.data_energy_dict[GlossaryEnergy.CO2PerUse]

    def compute(self):
        super().compute()
        self.compute_constraint()

    def compute_constraint(self):
        """
        Compute the constraint: consumption > carbon_quantity_to_be_stored from plasma cracking
        """

        constraint = self.outputs[f'{GlossaryEnergy.TechnoConsumptionValue}:{GlossaryEnergy.SolidCarbon} ({GlossaryEnergy.mass_unit})'] - self.inputs[f'carbon_quantity_to_be_stored:{GlossaryEnergy.carbon_storage}']
        self.outputs[f'carbon_to_be_stored_constraint:{GlossaryEnergy.Years}'] = self.years
        self.outputs[f'carbon_to_be_stored_constraint:{GlossaryEnergy.Years}'] = constraint
