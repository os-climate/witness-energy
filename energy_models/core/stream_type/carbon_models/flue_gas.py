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

from sostrades_optimization_plugins.models.differentiable_model import (
    DifferentiableModel,
)

from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.glossaryenergy import GlossaryEnergy


class FlueGas(DifferentiableModel):
    name = CarbonCapture.flue_gas_name
    node_name = 'flue_gas_capture'
    unit = 'Mt'

    @property
    def zeros_array(self):
        return self.years * 0.
    def configure_parameters(self):
        self.year_start = self.inputs[GlossaryEnergy.YearStart]
        self.year_end = self.inputs[GlossaryEnergy.YearEnd]
        self.years = self.np.arange(self.year_start, self.year_end + 1)
        self.inputs[GlossaryEnergy.techno_list] = self.inputs['energy_techno_list']

    def compute(self):
        """Compute function which compute flue gas production and flue gas mean ratio"""
        self.configure_parameters()
        self.compute_productions()
        self.compute_techno_mix()
        self.compute_flue_gas_ratio()

    def compute_productions(self):
        """Sum all the productions from technos of the stream (main stream and by products)"""
        self.outputs[f"{GlossaryEnergy.StreamProductionValue}:{GlossaryEnergy.Years}"] = self.years
        self.outputs[f"{GlossaryEnergy.StreamProductionDetailedValue}:{GlossaryEnergy.Years}"] = self.years

        conversion_factor = GlossaryEnergy.conversion_dict[GlossaryEnergy.TechnoFlueGasProduction['unit']]['Mt']
        for techno in self.inputs[GlossaryEnergy.techno_list]:
            self.outputs[f"{GlossaryEnergy.StreamProductionDetailedValue}:{techno}"] = \
                self.inputs[f'{techno}.{GlossaryEnergy.TechnoFlueGasProductionValue}:{GlossaryEnergy.CO2FromFlueGas}'] * conversion_factor

        self.outputs[f"{GlossaryEnergy.StreamProductionValue}:Total"] = self.sum_cols(
            self.get_cols_output_dataframe(
                df_name=GlossaryEnergy.StreamProductionDetailedValue,
                expect_years=True
            )
        )

    def compute_techno_mix(self):
        """Compute the contribution of each techno for the production of the main stream (in %) [0, 100]"""
        self.outputs[f'techno_mix:{GlossaryEnergy.Years}'] = self.years
        stream_total_prod = self.outputs[f'{GlossaryEnergy.StreamProductionValue}:Total']
        for techno in self.inputs[GlossaryEnergy.techno_list]:
            techno_share_of_total_stream_prod = \
                self.inputs[f'{techno}.{GlossaryEnergy.TechnoFlueGasProductionValue}:{self.name}'] / stream_total_prod
            self.outputs[f'techno_mix:{techno}'] = techno_share_of_total_stream_prod * 100.

    def compute_flue_gas_ratio(self):
        """Method to compute flue gas ratio using production by"""
        self.outputs[f"{GlossaryEnergy.FlueGasMean}:{GlossaryEnergy.Years}"] = self.years
        self.outputs[f"{GlossaryEnergy.FlueGasMean}:{GlossaryEnergy.FlueGasMean}"] = self.zeros_array
        for techno in self.inputs[GlossaryEnergy.techno_list]:
            self.outputs[f"{GlossaryEnergy.FlueGasMean}:{GlossaryEnergy.FlueGasMean}"] += \
                self.inputs[f'{techno}.flue_gas_co2_ratio'][0] * self.outputs[f'techno_mix:{techno}'] / 100.