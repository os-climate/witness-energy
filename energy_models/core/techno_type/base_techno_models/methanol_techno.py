'''
Copyright 2022 Airbus SAS
Modifications on 2024/01/31 Copyright 2024 Capgemini
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
from abc import abstractmethod

from energy_models.core.stream_type.energy_models.methanol import Methanol
from energy_models.core.techno_type.techno_type import TechnoType


class MethanolTechno(TechnoType):
    def __init__(self, name):
        TechnoType.__init__(self, name)
        self.energy_name = Methanol.name

    @abstractmethod
    def get_theoretical_co2_prod(self, unit='kg/kWh'):
        ''' 
        Get the theoretical CO2 production for a given technology,
        Need to be overloaded in each technology model (example in SMR)
        '''
        return 0.0
