'''
Copyright 2025 Capgemini

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
import logging

from sostrades_optimization_plugins.models.differentiable_model import (
    DifferentiableModel,
)

from energy_models.glossaryenergy import GlossaryEnergy


class EnergyMarket(DifferentiableModel):
    """Class Energy market"""

    def __init__(self, name, logger: logging.Logger):
        super().__init__()
        self.name = name
        self.logger = logger

    def compute(self):
        self.configure_parameters_update()

        self.compute_total_energy_demand()
        self.compute_availability_ratios()

        self.compute_prod_vs_demand_objective()


    def configure_parameters_update(self):
        """Configure parameters with possible update (variables that does change during the run)"""
        self.year_start = self.inputs[GlossaryEnergy.YearStart]
        self.year_end = self.inputs[GlossaryEnergy.YearEnd]
        self.years = self.np.arange(self.year_start, self.year_end + 1)
        self.zeros_array = self.years * 0.


    def compute_availability_ratios(self):
        """
        For each consumer sector, compute the limitation ratio for its usage
        """
        self.outputs[f"{GlossaryEnergy.EnergyMarketRatioAvailabilitiesValue}:{GlossaryEnergy.Years}"] = self.years
        commun_unit = "PWh"
        conversion_factor_demand = GlossaryEnergy.conversion_dict[GlossaryEnergy.EnergyDemandDf['unit']][commun_unit]
        conversion_factor_prod = GlossaryEnergy.conversion_dict[GlossaryEnergy.EnergyMixNetProductionsDf['unit']][commun_unit]
        if self.inputs[GlossaryEnergy.SimplifiedMarketEnergyDemandValue]:
            demand = self.outputs[f"{GlossaryEnergy.EnergyMarketDemandsDfValue}:Total"] * conversion_factor_demand
            production = self.inputs[f"{GlossaryEnergy.EnergyMixNetProductionsDfValue}:Total"] * conversion_factor_prod
            ratio = self.np.maximum(self.np.minimum(production / (demand + 1e-6), 1), 0) * 100.

            for column in self.get_colnames_output_dataframe(df_name=GlossaryEnergy.EnergyMarketDemandsDfValue, expect_years=True):
                self.outputs[f"{GlossaryEnergy.EnergyMarketRatioAvailabilitiesValue}:{column}"] = ratio
            self.outputs[f"{GlossaryEnergy.EnergyMarketRatioAvailabilitiesValue}:Total"] = ratio
        else:
            for column in self.get_colnames_output_dataframe(df_name=GlossaryEnergy.EnergyMarketDemandsDfValue, expect_years=True):
                demand = self.outputs[f"{GlossaryEnergy.EnergyMarketDemandsDfValue}:{column}"] * conversion_factor_demand
                production = self.inputs[f"{GlossaryEnergy.EnergyMixNetProductionsDfValue}:{column}"] * conversion_factor_prod
                self.outputs[f"{GlossaryEnergy.EnergyMarketRatioAvailabilitiesValue}:{column}"] = \
                    self.np.maximum(self.np.minimum(production / (demand + 1e-6), 1), 0) * 100.

    def compute_total_energy_demand(self):
        self.outputs[f"{GlossaryEnergy.EnergyMarketDemandsDfValue}:{GlossaryEnergy.Years}"] = self.years
        self.outputs[f"sectors_demand_breakdown:{GlossaryEnergy.Years}"] = self.years
        conversion_factor = GlossaryEnergy.conversion_dict[GlossaryEnergy.EnergyDemandDf['unit']][GlossaryEnergy.EnergyMarketDemandsDf['unit']]
        for consumer_actor in self.inputs['consumers_actors']:

            self.outputs[f"sectors_demand_breakdown:{consumer_actor}"] = self.sum_cols(
                self.get_cols_input_dataframe(df_name=f'{consumer_actor}_{GlossaryEnergy.EnergyDemandValue}', expect_years=True) * conversion_factor,
                index=self.years
            )

            for actor_energy_demand in self.get_colnames_input_dataframe(
                    df_name=f'{consumer_actor}_{GlossaryEnergy.EnergyDemandValue}', expect_years=True, full_path=False):
                if f"{GlossaryEnergy.EnergyMarketDemandsDfValue}:{actor_energy_demand}" not in self.outputs:
                    self.outputs[f"{GlossaryEnergy.EnergyMarketDemandsDfValue}:{actor_energy_demand}"] = self.zeros_array

                self.outputs[f"{GlossaryEnergy.EnergyMarketDemandsDfValue}:{actor_energy_demand}"] = \
                    self.outputs[f"{GlossaryEnergy.EnergyMarketDemandsDfValue}:{actor_energy_demand}"] + \
                    self.inputs[f'{consumer_actor}_{GlossaryEnergy.EnergyDemandValue}:{actor_energy_demand}'] * conversion_factor

        self.outputs[f"{GlossaryEnergy.EnergyMarketDemandsDfValue}:Total"] = self.sum_cols(
            self.get_cols_output_dataframe(df_name=GlossaryEnergy.EnergyMarketDemandsDfValue, expect_years=True), index=self.years
        )

    def compute_prod_vs_demand_objective(self):
        self.outputs[f"{GlossaryEnergy.EnergyMarketRatioAvailabilitiesValue}:{GlossaryEnergy.Years}"] = self.years
        commun_unit = "PWh"
        conversion_factor_demand = GlossaryEnergy.conversion_dict[GlossaryEnergy.EnergyDemandDf['unit']][commun_unit]
        conversion_factor_prod = GlossaryEnergy.conversion_dict[GlossaryEnergy.EnergyMixNetProductionsDf['unit']][
            commun_unit]
        if self.inputs[GlossaryEnergy.SimplifiedMarketEnergyDemandValue]:
            demand = self.outputs[f"{GlossaryEnergy.EnergyMarketDemandsDfValue}:Total"] * conversion_factor_demand
            production = self.inputs[f"{GlossaryEnergy.EnergyMixNetProductionsDfValue}:Total"] * conversion_factor_prod

            self.outputs[GlossaryEnergy.EnergyProdVsDemandObjective]= self.np.mean(self.np.array((demand - production) / (demand + 1e-6)))
        else:
            ratios_per_energy = []
            for column in self.get_colnames_output_dataframe(df_name=GlossaryEnergy.EnergyMarketDemandsDfValue,
                                                             expect_years=True):
                demand = self.outputs[f"{GlossaryEnergy.EnergyMarketDemandsDfValue}:{column}"] * conversion_factor_demand
                production = self.inputs[
                                 f"{GlossaryEnergy.EnergyMixNetProductionsDfValue}:{column}"] * conversion_factor_prod
                # differentiable en 0 :
                energy_obj = self.np.sqrt(self.np.mean(self.np.array((demand - production) / (demand + 1e-6))) ** 2 + 1e-4)
                ratios_per_energy.append(energy_obj)
            self.outputs[GlossaryEnergy.EnergyProdVsDemandObjective]= self.np.mean(self.np.array(ratios_per_energy))






