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

from energy_models.core.techno_type.base_techno_models.fossil_techno import FossilTechno
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture


class FossilSimpleTechno(FossilTechno):

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs which depends on the technology
        """
        return 0

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ?
        """
        self.compute_primary_energy_production()

        self.production[f'{CarbonCapture.flue_gas_name} ({self.mass_unit})'] = self.techno_infos_dict['CO2_from_production'] / \
            self.data_energy_dict['calorific_value'] * \
            self.production[f'{FossilTechno.energy_name} ({self.product_energy_unit})']
