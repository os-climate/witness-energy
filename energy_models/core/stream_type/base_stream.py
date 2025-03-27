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
        self.years = self.np.arange(self.year_start, self.year_end + 1)

    def compute(self):
        self.configure_parameters()
        self.compute_productions()

        self.compute_energy_consumptions()
        self.compute_ccs_consumptions()
        self.compute_resources_consumptions()

        self.compute_energy_demand()
        self.compute_ccs_demand()
        self.compute_resource_demand()

        self.compute_techno_mix()
        self.compute_price()
        self.compute_land_use()
        self.compute_energy_type_capital()

        self.compute_scope_1_emissions()
        self.compute_scope_1_ghg_intensity()

    def _aggregate_column_from_all_technos(self, output_varname: str, input_techno_varname: str, column_name: str):
        self.outputs[f"{output_varname}:{GlossaryEnergy.Years}"] = self.years

        for techno in self.inputs[GlossaryEnergy.techno_list]:
            output_path = f"{output_varname}:{column_name}"
            if output_path in self.outputs:
                self.outputs[output_path] = \
                    self.outputs[output_path] + \
                    self.inputs[f'{techno}.{input_techno_varname}:{column_name}']
            else:
                self.outputs[output_path] = self.zeros_array + self.inputs[f'{techno}.{input_techno_varname}:{column_name}']

    def _aggregate_from_all_technos(self, output_varname: str, input_techno_varname: str, conversion_factor: float):
        self.outputs[f"{output_varname}:{GlossaryEnergy.Years}"] = self.years

        for techno in self.inputs[GlossaryEnergy.techno_list]:
            techno_columns = self.get_colnames_input_dataframe(df_name=f'{techno}.{input_techno_varname}', expect_years=True)
            for col in techno_columns:
                output_path = f"{output_varname}:{col}"
                if output_path in self.outputs:
                    self.outputs[output_path] = \
                        self.outputs[output_path] + \
                        self.inputs[f'{techno}.{input_techno_varname}:{col}'] * conversion_factor

                else:
                    self.outputs[output_path] = \
                        self.zeros_array + \
                        self.inputs[f'{techno}.{input_techno_varname}:{col}'] * conversion_factor

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
        sum_technos_capital = self.np.sum(capitals, axis=0)

        non_use_capitals = [
            self.inputs[f"{techno}.{GlossaryEnergy.TechnoCapitalValue}:{GlossaryEnergy.NonUseCapital}"] for techno in technos
        ]
        sum_technos_non_use_capital = self.np.sum(non_use_capitals, axis=0)

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
                self.outputs[f'{GlossaryEnergy.StreamPricesValue}:{self.name}'] + \
                self.inputs[f'{techno}.{GlossaryEnergy.TechnoPricesValue}:{techno}'] * techno_share_of_total_stream_prod

            self.outputs[f'{GlossaryEnergy.StreamPricesValue}:{self.name}_wotaxes'] = \
                self.outputs[f'{GlossaryEnergy.StreamPricesValue}:{self.name}_wotaxes'] + \
                self.inputs[f'{techno}.{GlossaryEnergy.TechnoPricesValue}:{techno}_wotaxes'] * techno_share_of_total_stream_prod

    def compute_land_use(self):
        """Sum the land uses of the technos to obtain land use of the stream"""
        self.outputs[f'{GlossaryEnergy.LandUseRequiredValue}:{GlossaryEnergy.Years}'] = self.years
        self.outputs[f'{GlossaryEnergy.LandUseRequiredValue}:Land use'] = self.zeros_array
        conversion_factor = GlossaryEnergy.conversion_dict[GlossaryEnergy.TechnoLandUseDf['unit']][GlossaryEnergy.StreamLandUseDf['unit']]
        for techno in self.inputs[GlossaryEnergy.techno_list]:
                self.outputs[f'{GlossaryEnergy.LandUseRequiredValue}:Land use'] = \
                    self.outputs[f'{GlossaryEnergy.LandUseRequiredValue}:Land use'] + \
                    self.inputs[f'{techno}.{GlossaryEnergy.LandUseRequiredValue}:Land use'] \
                    * conversion_factor


    def compute_techno_mix(self):
        """Compute the contribution of each techno for the production of the main stream (in %) [0, 100]"""
        self.outputs[f'techno_mix:{GlossaryEnergy.Years}'] = self.years
        stream_total_prod = self.outputs[f'{GlossaryEnergy.StreamProductionValue}:{self.name} ({self.unit})']
        for techno in self.inputs[GlossaryEnergy.techno_list]:
            techno_share_of_total_stream_prod = self.inputs[
                                                    f'{techno}.{GlossaryEnergy.TechnoProductionValue}:{self.name} ({self.unit})'] / (stream_total_prod + 1e-9)
            self.outputs[f'techno_mix:{techno}'] = techno_share_of_total_stream_prod * 100.

    def compute_energy_consumptions(self):
        """Compute all energy consumptions in stream"""
        conversion_factor = GlossaryEnergy.conversion_dict[
            GlossaryEnergy.TechnoEnergyConsumption['unit']][GlossaryEnergy.StreamEnergyConsumption['unit']]
        self._aggregate_from_all_technos(
            output_varname=GlossaryEnergy.StreamEnergyConsumptionValue,
            input_techno_varname=GlossaryEnergy.TechnoEnergyConsumptionValue,
            conversion_factor=conversion_factor)

    def compute_resources_consumptions(self):
        """Compute all resources consumptions in stream"""
        conversion_factor = GlossaryEnergy.conversion_dict[
            GlossaryEnergy.TechnoResourceDemands['unit']][GlossaryEnergy.StreamResourceConsumption['unit']]
        self._aggregate_from_all_technos(
            output_varname=GlossaryEnergy.StreamResourceConsumptionValue,
            input_techno_varname=GlossaryEnergy.TechnoResourceConsumptionValue,
            conversion_factor=conversion_factor)

    def compute_energy_demand(self):
        """Compute total energy demands for each stream in current stream"""
        conversion_factor = GlossaryEnergy.conversion_dict[
            GlossaryEnergy.TechnoEnergyDemands['unit']][GlossaryEnergy.StreamEnergyDemand['unit']]
        self._aggregate_from_all_technos(
            output_varname=GlossaryEnergy.StreamEnergyDemandValue,
            input_techno_varname=GlossaryEnergy.TechnoEnergyDemandsValue,
            conversion_factor=conversion_factor)

    def compute_resource_demand(self):
        """Compute total resource demands for each stream in current stream"""
        conversion_factor = GlossaryEnergy.conversion_dict[
            GlossaryEnergy.TechnoResourceDemands['unit']][GlossaryEnergy.StreamResourceDemand['unit']]
        self._aggregate_from_all_technos(
            output_varname=GlossaryEnergy.StreamResourceDemandValue,
            input_techno_varname=GlossaryEnergy.TechnoResourceDemandsValue,
            conversion_factor=conversion_factor)

    def compute_scope_1_emissions(self):
        """Compute the scope 1 emissions of the stream : emissions associated to production"""
        for ghg in GlossaryEnergy.GreenHouseGases:
            self._aggregate_column_from_all_technos(
                output_varname=GlossaryEnergy.StreamScope1GHGEmissionsValue,
                input_techno_varname=GlossaryEnergy.TechnoScope1GHGEmissionsValue,
                column_name=ghg)

    def compute_scope_1_ghg_intensity(self):
        """Compute weighted average of scope 1 ghg intensity for each GHG (CO2, CH4, N2O)"""
        self.outputs[f"{GlossaryEnergy.StreamScope1GHGIntensityValue}:{GlossaryEnergy.Years}"] = self.years
        for ghg in GlossaryEnergy.GreenHouseGases:
            self.outputs[f"{GlossaryEnergy.StreamScope1GHGIntensityValue}:{ghg}"] = self.zeros_array
            for techno in self.inputs[GlossaryEnergy.techno_list]:
                self.outputs[f"{GlossaryEnergy.StreamScope1GHGIntensityValue}:{ghg}"] = self.outputs[f"{GlossaryEnergy.StreamScope1GHGIntensityValue}:{ghg}"] + \
                                                               self.outputs[f'techno_mix:{techno}'] / 100. * \
                                                               self.inputs[f"{techno}.{GlossaryEnergy.TechnoScope1GHGEmissionsValue}:{ghg}"]

    def compute_ccs_demand(self):
        conversion_factor = GlossaryEnergy.conversion_dict[
            GlossaryEnergy.TechnoCCSDemands['unit']][GlossaryEnergy.StreamCCSDemand['unit']]
        self._aggregate_from_all_technos(
            output_varname=GlossaryEnergy.StreamCCSDemandValue,
            input_techno_varname=GlossaryEnergy.TechnoCCSDemandsValue,
            conversion_factor=conversion_factor)

    def compute_ccs_consumptions(self):
        conversion_factor = GlossaryEnergy.conversion_dict[
            GlossaryEnergy.TechnoCCSConsumption['unit']][GlossaryEnergy.StreamCCSConsumption['unit']]
        self._aggregate_from_all_technos(
            output_varname=GlossaryEnergy.StreamCCSConsumptionValue,
            input_techno_varname=GlossaryEnergy.TechnoCCSConsumptionValue,
            conversion_factor=conversion_factor)
