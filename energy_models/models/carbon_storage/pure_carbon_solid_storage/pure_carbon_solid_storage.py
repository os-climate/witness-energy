'''
Copyright 2022 Airbus SAS

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
import numpy as np

from energy_models.core.techno_type.base_techno_models.carbon_storage_techno import CSTechno
from energy_models.core.stream_type.carbon_models.carbon import Carbon


class PureCarbonSS(CSTechno):

    CARBON_TO_BE_STORED_CONSTRAINT = 'carbon_to_be_stored_constraint'

    def compute_crf(self, data_config):
        return 1

    def compute_other_primary_energy_costs(self):
        return 0

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """

        self.compute_primary_energy_production()

        # Consumption
        # Production is gaseous CO2 equivalent
        # COnsumption is real Carbon storage (C)
        self.consumption[f'{Carbon.name} ({self.mass_unit})'] = self.production[f'{CSTechno.energy_name} ({self.product_energy_unit})'] / \
            Carbon.data_energy_dict['CO2_per_use']

    def compute_constraint(self, carbon_quantity_to_be_stored, consumption):
        """
        Compute the constraint: consumption > carbon_quantity_to_be_stored from plasma cracking
        """

        if (carbon_quantity_to_be_stored is not None) & (consumption is not None):
            constraint = consumption[f'{Carbon.name} ({self.mass_unit})'] - \
                carbon_quantity_to_be_stored['carbon_storage']
            self.carbon_to_be_stored_constraint = pd.DataFrame(
                {'years': self.years, 'carbon_to_be_stored_constraint': constraint})

        return self.carbon_to_be_stored_constraint
