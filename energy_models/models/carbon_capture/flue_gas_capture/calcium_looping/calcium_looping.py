'''
Copyright 2022 Airbus SAS
Modifications on 2023/10/23-2023/11/16 Copyright 2023 Capgemini

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

from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.carbon_capture.flue_gas_capture.generic_flue_gas_techno_model import GenericFlueGasTechnoModel


class CalciumLooping(GenericFlueGasTechnoModel):

    def compute_CO2_emissions_from_input_resources(self):
        '''
        Need to take into account  CO2 from Methane and electricity consumption
        '''

        self.carbon_intensity[Electricity.name] = self.energy_CO2_emissions[Electricity.name] * self.cost_details[f'{GlossaryEnergy.electricity}_needs']

        return self.carbon_intensity[Electricity.name] - 1.0
