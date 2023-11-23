'''
Copyright 2023 Capgemini

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

from energy_models.core.stream_type.energy_models.heat import lowtemperatureheat
from energy_models.core.techno_type.techno_type import TechnoType
from energy_models.glossaryenergy import GlossaryEnergy


class lowheattechno(TechnoType):
    energy_name = lowtemperatureheat.name

    def compute_transport(self):
        # Electricity has no Calorific value overload
        # Warning transport cost unit must be in $/MWh
        transport_cost = self.transport_cost['transport'] * \
                         self.transport_margin[GlossaryEnergy.MarginValue] / 100.0

        return transport_cost

    @abstractmethod
    def compute_other_primary_energy_costs(self):
        '''
        Compute other energy costs which will depend on the techno reaction (elec for electrolysis or methane for SMR by example)
        '''

    @abstractmethod
    def get_theoretical_co2_prod(self, unit='kg/kWh'):
        '''
        Get the theoretical CO2 production for a given technology,
        Need to be overloaded in each technology model (example in SMR)
        '''
        return 0.0

