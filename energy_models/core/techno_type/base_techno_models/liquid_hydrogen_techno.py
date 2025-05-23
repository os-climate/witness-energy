'''
Copyright 2022 Airbus SAS
Modifications on 27/03/2024 Copyright 2024 Capgemini
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

from energy_models.core.stream_type.energy_models.liquid_hydrogen import LiquidHydrogen
from energy_models.core.techno_type.techno_type import TechnoType


class LiquidHydrogenTechno(TechnoType):
    stream_name = LiquidHydrogen.name

    def __init__(self, name):
        TechnoType.__init__(self, name)
