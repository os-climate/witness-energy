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

from energy_models.core.stream_type.carbon_models.carbon_storage import CarbonStorage
from energy_models.core.techno_type.techno_type import TechnoType


class CSTechno(TechnoType):
    energy_name = CarbonStorage.name

    def __init__(self, name):
        TechnoType.__init__(self, name)
        self.product_energy_unit = 'Mt'

    def check_capex_unity(self, data_tocheck):
        """
        Put all capex in $/kgCO2
        """

        if data_tocheck['Capex_init_unit'] == '$/kgCO2':

            capex_init = data_tocheck['Capex_init']
        # add elif unit conversion if necessary

        else:
            capex_unit = data_tocheck['Capex_init_unit']
            raise Exception(
                f'The CAPEX unity {capex_unit} is not handled yet in techno_type')
        return capex_init * 1000.0

    def check_energy_demand_unit(self, energy_demand_unit, energy_demand):
        """
        Compute energy demand in kWh/kgCO2
        """

        if energy_demand_unit == 'kWh/kgCO2':
            pass
        # add elif unit conversion if necessary
        else:
            raise Exception(
                f'The unity of the energy demand {energy_demand_unit} is not handled with conversions')

        return energy_demand

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
