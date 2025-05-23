'''
Copyright 2022 Airbus SAS
Modifications on 23/11/2023 Copyright 2023 Capgemini

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


class KeroseneTechno(TechnoType):
    stream_name = GlossaryEnergy.kerosene

    def __init__(self, name):
        TechnoType.__init__(self, name)
