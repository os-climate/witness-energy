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
from abc import abstractmethod

from climateeconomics.glossarycore import GlossaryCore
from energy_models.core.stream_type.energy_models.syngas import Syngas, compute_molar_mass, \
    compute_calorific_value, compute_density
from energy_models.core.techno_type.techno_type import TechnoType
from copy import deepcopy

class SyngasTechno(TechnoType):

    energy_name = Syngas.name
    syngas_COH2_ratio = None

    def configure_energy_data(self, inputs_dict):

        self.data_energy_dict = deepcopy(inputs_dict['data_fuel_dict'])

        molar_mass = compute_molar_mass(self.syngas_COH2_ratio / 100.)
        calorific_value = compute_calorific_value(
            self.syngas_COH2_ratio / 100.)
        density = compute_density(self.syngas_COH2_ratio / 100.)

        self.data_energy_dict['molar_mass'] = molar_mass
        self.data_energy_dict['calorific_value'] = calorific_value
        self.data_energy_dict['high_calorific_value'] = calorific_value
        self.data_energy_dict['density'] = density

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

    def compute_transport(self):
        # Electricity has no Calorific value overload
        # Warning transport cost unit must $/kWh
        transport_cost = self.transport_cost['transport'] * \
            self.transport_margin[GlossaryCore.MarginValue] / 100.0

        return transport_cost
