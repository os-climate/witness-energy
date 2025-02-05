'''
Copyright 2022 Airbus SAS
Modifications on 2023/09/13-2023/11/16 Copyright 2023 Capgemini

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

import numpy as np
from sostrades_optimization_plugins.models.differentiable_model import (
    DifferentiableModel,
)

from energy_models.glossaryenergy import GlossaryEnergy


class BaseStream(DifferentiableModel):
    """Class for energy production technology type"""
    name = ''
    unit = ''
    default_techno_list = []

    def __init__(self, name):
        super().__init__()
        self.years = None
        self.name = name
        self.year_start = None
        self.year_end = None

    @property
    def zeros_array(self):
        return self.years * 0.

    def configure_parameters(self):
        '''
        Configure at init
        '''
        self.year_start = self.inputs[GlossaryEnergy.YearStart]
        self.year_end = self.inputs[GlossaryEnergy.YearEnd]
        self.years = np.arange(self.year_start, self.year_end + 1)

    def compute(self):
        self.configure_parameters()
        self.compute_productions()
        self.compute_consumptions()
        self.compute_consumptions_wo_ratios()
        self.compute_techno_mix()
        self.compute_price()
        self.aggregate_land_use_required()
        self.compute_energy_type_capital()

    def compute_productions(self):
        """Sum all the productions from technos of the stream (main stream and by products)"""
        self.outputs[f"{GlossaryEnergy.StreamProductionValue}:{GlossaryEnergy.Years}"] = self.years
        self.outputs[f"{GlossaryEnergy.StreamProductionDetailedValue}:{GlossaryEnergy.Years}"] = self.years

        for techno in self.inputs[GlossaryEnergy.techno_list]:
            self.outputs[f"{GlossaryEnergy.StreamProductionDetailedValue}:{techno} ({self.unit})"] = \
                self.inputs[f'{techno}.{GlossaryEnergy.TechnoProductionValue}:{self.name} ({self.unit})'] * 1e3
            techno_products = self.get_colnames_input_dataframe(df_name=f'{techno}.{GlossaryEnergy.TechnoProductionValue}', expect_years=True)
            for techno_product in techno_products:
                output_path = f"{GlossaryEnergy.StreamProductionValue}:{techno_product}"
                if output_path in self.outputs:
                    self.outputs[output_path] = self.outputs[output_path] + self.inputs[f'{techno}.{GlossaryEnergy.TechnoProductionValue}:{techno_product}']
                else:
                    self.outputs[output_path] = self.zeros_array + self.inputs[f'{techno}.{GlossaryEnergy.TechnoProductionValue}:{techno_product}']

    def compute_energy_type_capital(self):
        technos = self.inputs[GlossaryEnergy.techno_list]
        capitals = [
            self.inputs[f"{techno}.{GlossaryEnergy.TechnoCapitalValue}:{GlossaryEnergy.Capital}"] for techno in technos
        ]
        sum_technos_capital = np.sum(capitals, axis=0)

        non_use_capitals = [
            self.inputs[f"{techno}.{GlossaryEnergy.TechnoCapitalValue}:{GlossaryEnergy.NonUseCapital}"] for techno in technos
        ]
        sum_technos_non_use_capital = np.sum(non_use_capitals, axis=0)

        self.outputs[f"{GlossaryEnergy.EnergyTypeCapitalDfValue}:{GlossaryEnergy.Years}"] = self.years
        self.outputs[f"{GlossaryEnergy.EnergyTypeCapitalDfValue}:{GlossaryEnergy.Capital}"] = sum_technos_capital
        self.outputs[f"{GlossaryEnergy.EnergyTypeCapitalDfValue}:{GlossaryEnergy.NonUseCapital}"] = sum_technos_non_use_capital

    def compute_price(self):
        '''
        Compute the price with all sub_prices and sub weights computed with total production 
        '''
        self.outputs[f'{GlossaryEnergy.StreamPricesValue}:{GlossaryEnergy.Years}'] = self.years
        self.outputs[f'energy_detailed_techno_prices:{GlossaryEnergy.Years}'] = self.years
        self.outputs[f'{GlossaryEnergy.StreamPricesValue}:{self.name}'] = self.zeros_array
        self.outputs[f'{GlossaryEnergy.StreamPricesValue}:{self.name}_wotaxes'] = self.zeros_array

        for techno in self.inputs[GlossaryEnergy.techno_list]:
            self.outputs[f'energy_detailed_techno_prices:{techno}'] = self.inputs[f'{techno}.{GlossaryEnergy.TechnoPricesValue}:{techno}']
            techno_share_of_total_stream_prod = self.outputs[f'techno_mix:{techno}'] / 100.

            self.outputs[f'{GlossaryEnergy.StreamPricesValue}:{self.name}'] = \
                self.outputs[f'{GlossaryEnergy.StreamPricesValue}:{self.name}']  + \
                self.inputs[f'{techno}.{GlossaryEnergy.TechnoPricesValue}:{techno}'] * techno_share_of_total_stream_prod

            self.outputs[f'{GlossaryEnergy.StreamPricesValue}:{self.name}_wotaxes'] = \
                self.outputs[f'{GlossaryEnergy.StreamPricesValue}:{self.name}_wotaxes']  + \
                self.inputs[f'{techno}.{GlossaryEnergy.TechnoPricesValue}:{techno}_wotaxes'] * techno_share_of_total_stream_prod

    def aggregate_land_use_required(self):
        '''
        Aggregate into an unique dataframe of information of sub technology about land use required
        '''

        for techno in self.inputs[GlossaryEnergy.techno_list]:
            for column in self.get_colnames_input_dataframe(df_name=f'{techno}.{GlossaryEnergy.LandUseRequiredValue}', expect_years=True):
                self.outputs[f'{GlossaryEnergy.LandUseRequiredValue}:{column}'] = \
                    self.inputs[f'{techno}.{GlossaryEnergy.LandUseRequiredValue}:{column}']

    def compute_consumptions(self):
        self.outputs[f"{GlossaryEnergy.StreamConsumptionValue}:{GlossaryEnergy.Years}"] = self.years

        for techno in self.inputs[GlossaryEnergy.techno_list]:
            techno_consumed_products = self.get_colnames_input_dataframe(df_name=f'{techno}.{GlossaryEnergy.TechnoConsumptionValue}', expect_years=True)
            for techno_consumed_product in techno_consumed_products:
                output_path = f"{GlossaryEnergy.StreamConsumptionValue}:{techno_consumed_product}"
                if output_path in self.outputs:
                    self.outputs[output_path] = \
                        self.outputs[output_path] + \
                        self.inputs[f'{techno}.{GlossaryEnergy.TechnoConsumptionValue}:{techno_consumed_product}']

                else:
                    self.outputs[output_path] = \
                        self.zeros_array + \
                        self.inputs[f'{techno}.{GlossaryEnergy.TechnoConsumptionValue}:{techno_consumed_product}']

    def compute_techno_mix(self):
        """Compute the contribution of each techno for the production of the main stream (in %) [0, 100]"""
        self.outputs[f'techno_mix:{GlossaryEnergy.Years}'] = self.years
        stream_total_prod = self.outputs[f'{GlossaryEnergy.StreamProductionValue}:{self.name} ({self.unit})']
        for techno in self.inputs[GlossaryEnergy.techno_list]:
            techno_share_of_total_stream_prod = self.inputs[f'{techno}.{GlossaryEnergy.TechnoProductionValue}:{self.name} ({self.unit})'] / stream_total_prod
            self.outputs[f'techno_mix:{techno}'] = techno_share_of_total_stream_prod * 100.

    def compute_consumptions_wo_ratios(self):
        self.outputs[f"{GlossaryEnergy.StreamConsumptionWithoutRatioValue}:{GlossaryEnergy.Years}"] = self.years

        for techno in self.inputs[GlossaryEnergy.techno_list]:
            techno_consumed_products = self.get_colnames_input_dataframe(
                df_name=f'{techno}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}', expect_years=True)
            for techno_consumed_product in techno_consumed_products:
                output_path = f"{GlossaryEnergy.StreamConsumptionWithoutRatioValue}:{techno_consumed_product}"
                if output_path in self.outputs:
                    self.outputs[output_path] = \
                        self.outputs[output_path] + \
                        self.inputs[f'{techno}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}:{techno_consumed_product}']

                else:
                    self.outputs[output_path] = \
                        self.zeros_array + \
                        self.inputs[f'{techno}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}:{techno_consumed_product}']

