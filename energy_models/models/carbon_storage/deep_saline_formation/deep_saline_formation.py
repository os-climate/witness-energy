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

from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.techno_type.base_techno_models.carbon_storage_techno import CSTechno


class DeepSalineFormation(CSTechno):

    def compute_crf(self, data_config):
        return 1

    def compute_other_primary_energy_costs(self):
        return 0

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """

        # Consumption

        self.consumption_detailed[f'{CarbonCapture.name} ({self.product_energy_unit})'] = self.production_detailed[
            f'{CSTechno.energy_name} ({self.product_energy_unit})']
