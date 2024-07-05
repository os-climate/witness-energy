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
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.carbon_models.carbon_storage import CarbonStorage
from energy_models.core.techno_type.techno_type import TechnoType


class CSTechno(TechnoType):
    energy_name = CarbonStorage.name

    def __init__(self, name):
        TechnoType.__init__(self, name)
        self.product_unit = 'Mt'

    def compute_capital_recovery_factor(self, data_config):
        return 1

    def compute_energies_consumption(self):
        # Consumption
        self.consumption_detailed[f'{CarbonCapture.name} ({self.product_unit})'] = self.production_detailed[
            f'{CSTechno.energy_name} ({self.product_unit})']

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
