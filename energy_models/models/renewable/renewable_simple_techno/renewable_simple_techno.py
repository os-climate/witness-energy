'''
Copyright 2022 Airbus SAS
Modifications on 26/03/2024 Copyright 2024 Capgemini

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

from energy_models.core.techno_type.base_techno_models.renewable_techno import RenewableTechno


class RenewableSimpleTechno(RenewableTechno):

    def compute_specifif_costs_of_technos(self):
        self.cost_details['resource_price'] = self.techno_infos_dict['resource_price']

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs which depends on the technology
        """
        self.compute_specifif_costs_of_technos()

        return self.cost_details['resource_price']
