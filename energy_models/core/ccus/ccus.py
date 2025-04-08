'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2023/11/09 Copyright 2023 Capgemini

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

from energy_models.glossaryenergy import GlossaryEnergy


class CCUS(DifferentiableModel):
    """CCUS model"""
    ccs_list = [GlossaryEnergy.carbon_captured, GlossaryEnergy.carbon_storage]


    def compute(self):
        self.configure()
        self.compute_ccus_production()
        self.compute_ccus_demands()
        self.compute_ccus_energy_demand()
        self.compute_ccus_energy_consumption()
        self.compute_land_use()
        self.compute_emissions()
        self.compute_ccus_streams_ratios()
        self.compute_ccus_price()

    def compute_ccus_production(self):
        """Carbon captured production and carbon storage capacity"""
        input_unit = GlossaryEnergy.StreamProductionDf['unit']
        conversion_factor = GlossaryEnergy.conversion_dict[input_unit][GlossaryEnergy.CCUSOutput['unit']]
        self.outputs[f"{GlossaryEnergy.CCUSOutputValue}:{GlossaryEnergy.Years}"] = self.years

        self.outputs[f"{GlossaryEnergy.CCUSOutputValue}:{GlossaryEnergy.carbon_storage}"] = \
            self.inputs[f"{GlossaryEnergy.carbon_storage}.{GlossaryEnergy.StreamProductionValue}:{GlossaryEnergy.carbon_storage}"]\
            * conversion_factor

        self.outputs[f"{GlossaryEnergy.CCUSOutputValue}:{GlossaryEnergy.carbon_captured}"] = \
            self.inputs[f"{GlossaryEnergy.carbon_captured}.{GlossaryEnergy.StreamProductionValue}:{GlossaryEnergy.carbon_captured}"]\
            * conversion_factor

        self.outputs[f"{GlossaryEnergy.CCUSOutputValue}:Carbon captured to store (after direct usages)"] = \
            self.outputs[f"{GlossaryEnergy.CCUSOutputValue}:{GlossaryEnergy.carbon_captured}"] - \
            self.inputs[f"{GlossaryEnergy.EnergyMixCCSConsumptionDfValue}:{GlossaryEnergy.carbon_captured}"]

        self.outputs[f"{GlossaryEnergy.CCUSOutputValue}:Carbon captured and stored"] = \
            self.np.minimum(
                self.outputs[f"{GlossaryEnergy.CCUSOutputValue}:Carbon captured to store (after direct usages)"],
                self.outputs[f"{GlossaryEnergy.CCUSOutputValue}:{GlossaryEnergy.carbon_storage}"]
            )

    def configure(self):
        self.years = self.np.arange(self.inputs[GlossaryEnergy.YearStart], self.inputs[GlossaryEnergy.YearEnd] + 1)
        self.zeros_array = self.years * 0.

    def compute_land_use(self):
        self.outputs[f"{GlossaryEnergy.CCUS}.{GlossaryEnergy.LandUseRequiredValue}:{GlossaryEnergy.Years}"] = self.years
        self.outputs[f"{GlossaryEnergy.CCUS}.{GlossaryEnergy.LandUseRequiredValue}:Land use"] = self.zeros_array
        for stream in self.ccs_list:
            conversion_factor = GlossaryEnergy.conversion_dict[GlossaryEnergy.StreamLandUseDf['unit']][GlossaryEnergy.StreamLandUseDf['unit']]
            self.outputs[f"{GlossaryEnergy.CCUS}.{GlossaryEnergy.LandUseRequiredValue}:Land use"] = \
                self.outputs[f"{GlossaryEnergy.CCUS}.{GlossaryEnergy.LandUseRequiredValue}:Land use"] + \
                self.inputs[f"{stream}.{GlossaryEnergy.LandUseRequiredValue}:Land use"] * conversion_factor

    def compute_emissions(self):
        input_unit = GlossaryEnergy.StreamProductionDf['unit']
        conversion_factor = GlossaryEnergy.conversion_dict[input_unit][GlossaryEnergy.CCUS_CO2EmissionsDf['unit']]
        self.outputs[f"{GlossaryEnergy.CCUS_CO2EmissionsDfValue}:{GlossaryEnergy.Years}"] = self.years
        self.outputs[f"{GlossaryEnergy.CCUS_CO2EmissionsDfValue}:{GlossaryEnergy.CO2}"] = \
            self.inputs[f"{GlossaryEnergy.carbon_captured}.{GlossaryEnergy.StreamProductionValue}:{GlossaryEnergy.carbon_captured}"] * conversion_factor

    def compute_ccus_streams_ratios(self):
        """Availibility = min(1 , prod/ demand)"""
        for stream in [GlossaryEnergy.carbon_captured, GlossaryEnergy.carbon_storage]:
            demand = self.outputs[f"demands_df:{stream}"]
            prod = self.outputs[f"{GlossaryEnergy.CCUSOutputValue}:{stream}"]
            self.outputs[f"{GlossaryEnergy.CCUSAvailabilityRatiosValue}:{stream}"] = \
                self.np.maximum(self.np.minimum(prod/ (demand + 1e-6), 1), 0) * 100. # avoid division by zero

    def compute_ccus_price(self):
        """Price in $/tCO2 captured and stored"""
        self.outputs[f'{GlossaryEnergy.CCUSPriceValue}:Captured and stored'] = \
            self.inputs[f"{GlossaryEnergy.carbon_captured}.{GlossaryEnergy.StreamPricesValue}:{GlossaryEnergy.carbon_captured}"] + \
            self.inputs[f"{GlossaryEnergy.carbon_storage}.{GlossaryEnergy.StreamPricesValue}:{GlossaryEnergy.carbon_storage}"]


    def compute_ccus_demands(self):
        """
        carbon storage demand is carbon capture production - energy mix demand for carbon capture
        """
        output_unit = "Gt"

        carbon_storage_demand_breakdown = {
            "Carbon captured by CCUS": self.inputs[f"{GlossaryEnergy.carbon_captured}.{GlossaryEnergy.StreamProductionValue}:{GlossaryEnergy.carbon_captured}"]
                                       * GlossaryEnergy.conversion_dict[GlossaryEnergy.StreamProductionDf['unit']][output_unit],
            "Carbon captured demand for Energy Mix": - self.inputs[f"{GlossaryEnergy.EnergyMixCCSDemandsDfValue}:{GlossaryEnergy.carbon_captured}"]
                                                     * GlossaryEnergy.conversion_dict[GlossaryEnergy.EnergyMixCCSDemandsDf['unit']][output_unit]
        }
        carbon_capture_demand_breakdown = {
            "Carbon captured demand for Energy Mix" : - carbon_storage_demand_breakdown["Carbon captured demand for Energy Mix"]
        }

        self.outputs[f"{GlossaryEnergy.carbon_captured}_demand_breakdown"] = carbon_capture_demand_breakdown
        self.outputs[f"{GlossaryEnergy.carbon_storage}_demand_breakdown"] = carbon_storage_demand_breakdown

        self.outputs[f"demands_df:{GlossaryEnergy.Years}"] = self.years
        self.outputs[f"demands_df:{GlossaryEnergy.carbon_storage}"] = self.np.sum(self.np.array(list(carbon_storage_demand_breakdown.values())), axis=0)
        self.outputs[f"demands_df:{GlossaryEnergy.carbon_captured}"] = carbon_capture_demand_breakdown["Carbon captured demand for Energy Mix"]

    def compute_ccus_energy_demand(self):
        """Compute energies demand (all forms) of CCUS sector"""
        self.outputs[f"{GlossaryEnergy.CCUS}_{GlossaryEnergy.EnergyDemandValue}:{GlossaryEnergy.Years}"] = self.years
        conversion_factor = GlossaryEnergy.conversion_dict[GlossaryEnergy.StreamEnergyDemand['unit']][GlossaryEnergy.EnergyDemandDf['unit']]

        for stream in self.ccs_list:
            for other_energy_demand in self.get_colnames_input_dataframe(
                    df_name=f'{stream}.{GlossaryEnergy.StreamEnergyDemandValue}', expect_years=True, full_path=False):
                if f"{GlossaryEnergy.CCUS}_{GlossaryEnergy.EnergyDemandValue}:{other_energy_demand}" not in self.outputs:
                    self.outputs[
                        f"{GlossaryEnergy.CCUS}_{GlossaryEnergy.EnergyDemandValue}:{other_energy_demand}"] = self.zeros_array
                self.outputs[f"{GlossaryEnergy.CCUS}_{GlossaryEnergy.EnergyDemandValue}:{other_energy_demand}"] = \
                    self.outputs[f"{GlossaryEnergy.CCUS}_{GlossaryEnergy.EnergyDemandValue}:{other_energy_demand}"] + \
                    self.inputs[
                        f'{stream}.{GlossaryEnergy.StreamEnergyDemandValue}:{other_energy_demand}'] * conversion_factor

    def compute_ccus_energy_consumption(self):
        """Compute CCUS sector energies consumption"""
        self.outputs[f"{GlossaryEnergy.CCUS}.{GlossaryEnergy.EnergyConsumptionValue}:{GlossaryEnergy.Years}"] = self.years
        conversion_factor = GlossaryEnergy.conversion_dict[GlossaryEnergy.StreamEnergyConsumption['unit']][GlossaryEnergy.EnergyConsumptionDf['unit']]

        for stream in self.ccs_list:
            for other_energy_consumption in self.get_colnames_input_dataframe(
                    df_name=f'{stream}.{GlossaryEnergy.StreamEnergyConsumptionValue}', expect_years=True, full_path=False):
                if f"{GlossaryEnergy.CCUS}.{GlossaryEnergy.EnergyConsumptionValue}:{other_energy_consumption}" not in self.outputs:
                    self.outputs[
                        f"{GlossaryEnergy.CCUS}.{GlossaryEnergy.EnergyConsumptionValue}:{other_energy_consumption}"] = self.zeros_array
                self.outputs[f"{GlossaryEnergy.CCUS}.{GlossaryEnergy.EnergyConsumptionValue}:{other_energy_consumption}"] = \
                    self.outputs[f"{GlossaryEnergy.CCUS}.{GlossaryEnergy.EnergyConsumptionValue}:{other_energy_consumption}"] + \
                    self.inputs[
                        f'{stream}.{GlossaryEnergy.StreamEnergyConsumptionValue}:{other_energy_consumption}'] * conversion_factor

