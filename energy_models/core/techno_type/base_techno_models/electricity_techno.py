'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2023/11/09 Copyright 2023 Capgemini

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

from energy_models.core.techno_type.techno_type import TechnoType
from energy_models.glossaryenergy import GlossaryEnergy


class ElectricityTechno(TechnoType):
    energy_name = GlossaryEnergy.electricity

    def compute_transport(self):
        # Electricity has no Calorific value overload
        # Warning transport cost unit must be in $/MWh
        transport_cost = self.transport_cost['transport'].values * \
                         self.transport_margin[GlossaryEnergy.MarginValue].values / 100.0

        return transport_cost
