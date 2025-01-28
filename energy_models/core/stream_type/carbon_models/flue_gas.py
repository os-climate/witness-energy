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

from energy_models.core.stream_type.base_stream import BaseStream
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.glossaryenergy import GlossaryEnergy


class FlueGas(BaseStream):
    name = CarbonCapture.flue_gas_name
    node_name = 'flue_gas_capture'
    unit = 'Mt'

    def compute(self):
        """Compute function which compute flue gas production and flue gas mean ratio"""
        self.configure_parameters()
        self.compute_productions()
        self.compute_techno_mix()
        self.compute_flue_gas_ratio()

    def compute_flue_gas_ratio(self):
        """Method to compute flue gas ratio using production by"""
        self.outputs[f"{GlossaryEnergy.FlueGasMean}:{GlossaryEnergy.Years}"] = self.years
        self.outputs[f"{GlossaryEnergy.FlueGasMean}:{GlossaryEnergy.FlueGasMean}"] = self.zeros_array
        for techno in self.inputs[GlossaryEnergy.techno_list]:
            self.outputs[f"{GlossaryEnergy.FlueGasMean}:{GlossaryEnergy.FlueGasMean}"] += \
                self.inputs[f'{techno}.flue_gas_co2_ratio'][0] * self.outputs[f'techno_mix:{techno}']
