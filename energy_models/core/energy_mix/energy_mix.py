'''
Copyright 2022 Airbus SAS
Modifications on 2023/05/31-2023/11/16 Copyright 2023 Capgemini

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

import numpy as np
from sostrades_optimization_plugins.models.differentiable_model import (
    DifferentiableModel,
)

from energy_models.core.stream_type.energy_models.clean_energy import CleanEnergy
from energy_models.core.stream_type.energy_models.fossil import Fossil
from energy_models.glossaryenergy import GlossaryEnergy


class EnergyMix(DifferentiableModel):
    """Class Energy mix"""
    name = 'EnergyMix'

    # For simplified energy mix , raw_to_net factor is used to compute net
    # production from raw production
    raw_to_net_dict = {CleanEnergy.name: CleanEnergy.raw_to_net_production,
                       Fossil.name: Fossil.raw_to_net_production}

    energy_list = list(GlossaryEnergy.unit_dicts.keys())
    resource_list = ['natural_gas_resource', 'uranium_resource', 'coal_resource', 'oil_resource', 'copper_resource']  # , 'platinum_resource',]

    # TODO shouldnt it just be carbon stored ? like energy technos take stored carbon and emit it into the atmosphere ?
    # TODO because carbon captured is just a temporary state of carbon, waiting to be stored
    def __init__(self, name, logger: logging.Logger):
        super().__init__(sosname=name)
        self.name = name
        self.logger = logger

    def compute(self):
        self.configure_parameters_update()

        # energy production
        self.compute_raw_energy_production()
        self.compute_energy_consumptions_by_energy_sector()
        self.compute_net_energy_production()

        # ratios production vs demand
        self.compute_all_energies_demands()
        self.compute_energy_sector_ccs_demand()
        self.compute_energy_sector_ccs_consumption()
        self.compute_energies_availability_ratios()

        self.compute_price_by_energy()
        self.compute_energy_mix()
        self.compute_mean_energy_price()

        self.compute_ghg_emissions_intensity_by_energy()
        self.compute_ghg_emissions()

        self.aggregate_land_use_required()
        self.compute_energy_sector_capital()

        self.compute_target_production_constraint()

    def configure_parameters_update(self):
        """Configure parameters with possible update (variables that does change during the run)"""
        self.year_start = self.inputs[GlossaryEnergy.YearStart]
        self.year_end = self.inputs[GlossaryEnergy.YearEnd]
        self.years = self.np.arange(self.year_start, self.year_end + 1)
        self.zeros_array = self.years * 0.

    def compute_energy_sector_capital(self):
        """Energy sector capital = sum of all energy streams capital"""

        conversion_factor = GlossaryEnergy.conversion_dict[GlossaryEnergy.EnergyTypeCapitalDf['unit']][GlossaryEnergy.EnergyMixCapitalDf['unit']]
        energy_type_capitals = []
        for energy in self.inputs[GlossaryEnergy.energy_list]:
            energy_type_capitals.append(
                self.inputs[f"{energy}.{GlossaryEnergy.EnergyTypeCapitalDfValue}:{GlossaryEnergy.Capital}"])

        energy_capital = np.sum(energy_type_capitals, axis=0) * conversion_factor

        energy_type_non_use_capitals = []
        for energy in self.inputs[GlossaryEnergy.energy_list]:
            energy_type_non_use_capitals.append(
                self.inputs[f"{energy}.{GlossaryEnergy.EnergyTypeCapitalDfValue}:{GlossaryEnergy.NonUseCapital}"])

        energy_non_use_capital = np.sum(energy_type_non_use_capitals, axis=0) * conversion_factor

        self.outputs[f"{GlossaryEnergy.EnergyMixCapitalDfValue}:{GlossaryEnergy.Years}"] = self.years
        self.outputs[f"{GlossaryEnergy.EnergyMixCapitalDfValue}:{GlossaryEnergy.Capital}"] = energy_capital
        self.outputs[f"{GlossaryEnergy.EnergyMixCapitalDfValue}:{GlossaryEnergy.NonUseCapital}"] = energy_non_use_capital

    def compute_raw_energy_production(self):
        """Sum all the energy production"""

        self.outputs[f'{GlossaryEnergy.EnergyMixRawProductionValue}:{GlossaryEnergy.Years}'] = self.years
        input_unit = GlossaryEnergy.StreamProductionDf['unit'].split(' or ')[0]
        conversion_factor = GlossaryEnergy.conversion_dict[input_unit][GlossaryEnergy.EnergyMixRawProduction['unit']]
        for energy in self.inputs[GlossaryEnergy.energy_list]:
            self.outputs[f'{GlossaryEnergy.EnergyMixRawProductionValue}:{energy}'] = \
                self.inputs[f'{energy}.{GlossaryEnergy.StreamProductionValue}:{energy}'] * conversion_factor

        # Total computation :
        self.outputs[f'{GlossaryEnergy.EnergyMixRawProductionValue}:Total'] = \
            self.sum_cols(self.get_cols_output_dataframe(df_name=GlossaryEnergy.EnergyMixRawProductionValue, expect_years=True))

    def compute_net_energy_production(self):
        """
        Net energy = Raw energy production - Energy consumed for energy production - energy consumed for CCUS - heat losses
        """

        self.outputs[f"{GlossaryEnergy.EnergyMixNetProductionsDfValue}:{GlossaryEnergy.Years}"] = self.years

        assert GlossaryEnergy.EnergyMixRawProduction['unit'] == GlossaryEnergy.EnergyMixEnergiesConsumptionDf['unit']
        for energy in self.inputs[GlossaryEnergy.energy_list]:
            # starting from raw energy production
            raw_production_energy = self.outputs[f"{GlossaryEnergy.EnergyMixRawProductionValue}:{energy}"]

            # coarse technos:
            if energy in self.raw_to_net_dict:
                net_energy_production_in_energy_sector = self.raw_to_net_dict[energy] * raw_production_energy
            else:
                energy_consumption_in_energy_sector = self.outputs[f"{GlossaryEnergy.EnergyMixEnergiesConsumptionDfValue}:{energy}"]
                net_energy_production_in_energy_sector = raw_production_energy - energy_consumption_in_energy_sector

            net_production_positive_part = self.np.maximum(net_energy_production_in_energy_sector, 1e-3)
            self.outputs[f"{GlossaryEnergy.EnergyMixNetProductionsDfValue}:{energy}"] = net_production_positive_part

        self.outputs[f"{GlossaryEnergy.EnergyMixNetProductionsDfValue}:heat_losses"] = \
            - self.outputs[f'{GlossaryEnergy.EnergyMixRawProductionValue}:Total'] * self.inputs['heat_losses_percentage'] / 100.0

        self.outputs[f"{GlossaryEnergy.EnergyMixNetProductionsDfValue}:Total"] = self.sum_cols(
            self.get_cols_output_dataframe(df_name=GlossaryEnergy.EnergyMixNetProductionsDfValue, expect_years=True)
        )

    def compute_net_prod_of_coarse_energies(self, energy):
        """Compute the energy production share to remove for coarse techno to go from raw to net"""
        return (1.0 - self.raw_to_net_dict[energy]) if energy in self.raw_to_net_dict else 0.

    def compute_price_by_energy(self):
        """
        Compute the price of each energy.
        Energy price (energy type, year) in $/MWh = Raw energy price (techno, year) + CO2 emitted(techno, year) * carbon tax ($/tEqCO2)
        after carbon tax with all technology prices and technology weights computed with energy production
        """
        # TODO : add tax
        output_unit = GlossaryEnergy.StreamPrices['unit']
        self.outputs[f"{GlossaryEnergy.StreamPricesValue}:{GlossaryEnergy.Years}"] = self.years

        for energy in self.inputs[GlossaryEnergy.energy_list]:
            self.outputs[f"{GlossaryEnergy.StreamPricesValue}:{energy}"] = self.inputs[f'{energy}.{GlossaryEnergy.StreamPricesValue}:{energy}']

    def compute_mean_energy_price(self):
        """Compute mean energy price"""

        self.outputs[f"{GlossaryEnergy.EnergyMeanPriceValue}:{GlossaryEnergy.Years}"] = self.years
        self.outputs[f"{GlossaryEnergy.EnergyMeanPriceValue}:{GlossaryEnergy.EnergyPriceValue}"] = self.zeros_array

        for energy in self.inputs[GlossaryEnergy.energy_list]:
            self.outputs[f"{GlossaryEnergy.EnergyMeanPriceValue}:{GlossaryEnergy.EnergyPriceValue}"] = \
                self.outputs[f"{GlossaryEnergy.EnergyMeanPriceValue}:{GlossaryEnergy.EnergyPriceValue}"] + \
                self.outputs[f"energy_mix:{energy}"] / 100.

    def compute_energy_mix(self):
        """Compute the contribution (in %) of each energy in the total net energy production"""
        self.outputs[f"energy_mix:{GlossaryEnergy.Years}"] = self.years

        total_net_energy_prod_wo_heat_losses = self.outputs[f"{GlossaryEnergy.EnergyMixNetProductionsDfValue}:Total"] - \
                                               self.outputs[f"{GlossaryEnergy.EnergyMixNetProductionsDfValue}:heat_losses"]

        for energy in self.inputs[GlossaryEnergy.energy_list]:
            self.outputs[f"energy_mix:{energy}"] = self.outputs[f"{GlossaryEnergy.EnergyMixNetProductionsDfValue}:{energy}"] / \
                                                   total_net_energy_prod_wo_heat_losses * 100.

    def compute_energies_availability_ratios(self):
        """
        For each stream, compute the limitation ratio for its usage

        Ratio of availability for stream A = minimum(1, production of stream A / demand for stream A)

        Then, inside technos using stream A for their production, the desired production is multiplied by
        Ratio stream A to compute the real production.
        """
        self.outputs[f"{GlossaryEnergy.AllStreamsDemandRatioValue}:{GlossaryEnergy.Years}"] = self.years
        assert GlossaryEnergy.EnergyMixRawProduction['unit'] == GlossaryEnergy.EnergyMixEnergiesDemandsDf['unit']

        for stream_consumption in self.get_colnames_output_dataframe(f"{GlossaryEnergy.EnergyMixEnergiesDemandsDfValue}", expect_years=True, full_path=False):
            if f'{GlossaryEnergy.EnergyMixRawProductionValue}:{stream_consumption}' in self.outputs:
                stream_raw_production = self.outputs[f'{GlossaryEnergy.EnergyMixRawProductionValue}:{stream_consumption}']
                demand_for_stream = self.outputs[f"{GlossaryEnergy.EnergyMixEnergiesDemandsDfValue}:{stream_consumption}"]

                # min(1, raw_prod / demand) :
                self.outputs[f'{GlossaryEnergy.AllStreamsDemandRatioValue}:{stream_consumption}'] = self.np.maximum(
                    self.np.minimum(stream_raw_production / (demand_for_stream + 1e-6), 1), 0) * 100.
            else:
                #self.logger.warning(f"{stream_consumption} is consumed but not produced in current study. No limiting ratio assumed.")
                self.outputs[f'{GlossaryEnergy.AllStreamsDemandRatioValue}:{stream_consumption}'] = self.zeros_array + 100.

    def compute_target_production_constraint(self):
        """should be negative when satisfied"""
        self.outputs[f"{GlossaryEnergy.TargetProductionConstraintValue}:{GlossaryEnergy.Years}"] = self.years

        actual_net_production = self.outputs[f"{GlossaryEnergy.EnergyMixNetProductionsDfValue}:Total"]
        target_prod = self.inputs[f"{GlossaryEnergy.TargetEnergyProductionValue}:{GlossaryEnergy.TargetEnergyProductionValue}"]
        constraint_normalized = (actual_net_production - target_prod) / (target_prod + 1e-3)
        self.outputs[f"{GlossaryEnergy.TargetProductionConstraintValue}:{GlossaryEnergy.TargetProductionConstraintValue}"] = constraint_normalized

    def aggregate_land_use_required(self):
        """Aggregate into an unique dataframe of information of sub technology about land use required"""

        for stream in self.inputs[GlossaryEnergy.energy_list]:
            df_name = f'{stream}.{GlossaryEnergy.LandUseRequiredValue}'
            stream_land_use_df_cols = self.get_colnames_input_dataframe(df_name=df_name, expect_years=True)
            for col in stream_land_use_df_cols:
                self.outputs[f"land_demand_df:{col}"] = self.inputs[f"{df_name}:{col}"]

    def compute_all_energies_demands(self):
        """Sums all demands of all stream for each available product"""
        self.outputs[f"{GlossaryEnergy.EnergyMixEnergiesDemandsDfValue}:{GlossaryEnergy.Years}"] = self.years
        conversion_factor = GlossaryEnergy.conversion_dict[GlossaryEnergy.StreamEnergyDemand['unit']][GlossaryEnergy.EnergyMixEnergiesDemandsDf['unit']]
        for energy in self.inputs[GlossaryEnergy.energy_list]:
            for other_energy_demand in self.get_colnames_input_dataframe(
                    df_name=f'{energy}.{GlossaryEnergy.StreamEnergyDemandValue}', expect_years=True, full_path=False):
                if f"{GlossaryEnergy.EnergyMixEnergiesDemandsDfValue}:{other_energy_demand}" not in self.outputs:
                    self.outputs[f"{GlossaryEnergy.EnergyMixEnergiesDemandsDfValue}:{other_energy_demand}"] = self.zeros_array
                self.outputs[f"{GlossaryEnergy.EnergyMixEnergiesDemandsDfValue}:{other_energy_demand}"] = \
                    self.outputs[f"{GlossaryEnergy.EnergyMixEnergiesDemandsDfValue}:{other_energy_demand}"] + \
                    self.inputs[f'{energy}.{GlossaryEnergy.StreamEnergyDemandValue}:{other_energy_demand}'] * conversion_factor

    def compute_energy_consumptions_by_energy_sector(self):
        """For each energy, sum what has been consumed by other energy"""

        self.outputs[f"{GlossaryEnergy.EnergyMixEnergiesConsumptionDfValue}:{GlossaryEnergy.Years}"] = self.years
        conversion_factor = GlossaryEnergy.conversion_dict[GlossaryEnergy.StreamEnergyConsumption['unit']][GlossaryEnergy.EnergyMixEnergiesConsumptionDf['unit']]
        for energy in self.inputs[GlossaryEnergy.energy_list]:
            consumed_energy_by_energy_list = []
            for other_energy in self.inputs[GlossaryEnergy.energy_list]:
                consumptions_of_other_energy = self.get_colnames_input_dataframe(df_name=f'{other_energy}.{GlossaryEnergy.StreamEnergyConsumptionValue}', expect_years=True, full_path=False)
                if energy in consumptions_of_other_energy:
                    consumed_energy_by_energy_list.append(
                        self.inputs[f'{other_energy}.{GlossaryEnergy.StreamEnergyConsumptionValue}:{energy}'])

            consumed_energy_by_other_energy_sum = self.sum_cols(consumed_energy_by_energy_list) * conversion_factor if consumed_energy_by_energy_list else self.zeros_array
            self.outputs[f"{GlossaryEnergy.EnergyMixEnergiesConsumptionDfValue}:{energy}"] = consumed_energy_by_other_energy_sum


        self.outputs[f"{GlossaryEnergy.EnergyMixEnergiesConsumptionDfValue}:Total"] = self.sum_cols(
            self.get_cols_output_dataframe(df_name=GlossaryEnergy.EnergyMixEnergiesConsumptionDfValue, expect_years=True)
        )

    def compute_ghg_emissions(self):
        """Sum the emissions for each GHG (CO2, CH4, N2O)"""
        conversion_factor = GlossaryEnergy.conversion_dict[GlossaryEnergy.StreamScope1GHGEmissions['unit']][GlossaryEnergy.GHGEnergyEmissionsDf['unit']]
        for ghg in GlossaryEnergy.GreenHouseGases:
            self._sum_column_from_all_energies(
                output_varname=GlossaryEnergy.GHGEnergyEmissionsDfValue,
                input_energies_varname=GlossaryEnergy.StreamScope1GHGEmissionsValue,
                column_name=ghg, conversion_factor=conversion_factor)

            self._aggregate_column_from_all_energies(
                output_varname=f"{ghg}_emissions_by_energy",
                input_energies_varname=GlossaryEnergy.StreamScope1GHGEmissionsValue,
                input_colname=ghg,
                conversion_factor=conversion_factor
            )

    def _sum_column_from_all_energies(
            self, output_varname: str, input_energies_varname: str, column_name: str, conversion_factor : float):
        self.outputs[f"{output_varname}:{GlossaryEnergy.Years}"] = self.years

        for energy in self.inputs[GlossaryEnergy.energy_list]:
            output_path = f"{output_varname}:{column_name}"
            if output_path not in self.outputs:
                self.outputs[output_path] = self.zeros_array
            self.outputs[output_path] = self.outputs[output_path] + self.inputs[f'{energy}.{input_energies_varname}:{column_name}'] * conversion_factor

    def _aggregate_column_from_all_energies(
            self, output_varname: str, input_energies_varname: str, input_colname: str, conversion_factor : float):
        self.outputs[f"{output_varname}:{GlossaryEnergy.Years}"] = self.years

        for energy in self.inputs[GlossaryEnergy.energy_list]:
            output_path = f"{output_varname}:{energy}"
            self.outputs[output_path] = self.inputs[f'{energy}.{input_energies_varname}:{input_colname}'] * conversion_factor

    def compute_energy_sector_ccs_demand(self):
        """Sums all demands of ccs streams of each energy"""
        self.outputs[f"{GlossaryEnergy.EnergyMixCCSDemandsDfValue}:{GlossaryEnergy.Years}"] = self.years
        conversion_factor = GlossaryEnergy.conversion_dict[GlossaryEnergy.StreamCCSDemand['unit']][GlossaryEnergy.EnergyMixCCSDemandsDf['unit']]

        for energy in self.inputs[GlossaryEnergy.energy_list]:
            for ccs_stream in self.get_colnames_input_dataframe(
                    df_name=f'{energy}.{GlossaryEnergy.StreamCCSDemandValue}', expect_years=True, full_path=False):

                if f"{GlossaryEnergy.EnergyMixCCSDemandsDfValue}:{ccs_stream}" not in self.outputs:
                    self.outputs[f"{GlossaryEnergy.EnergyMixCCSDemandsDfValue}:{ccs_stream}"] = self.zeros_array

                self.outputs[f"{GlossaryEnergy.EnergyMixCCSDemandsDfValue}:{ccs_stream}"] = \
                    self.outputs[f"{GlossaryEnergy.EnergyMixCCSDemandsDfValue}:{ccs_stream}"] + \
                    self.inputs[f'{energy}.{GlossaryEnergy.StreamCCSDemandValue}:{ccs_stream}'] * conversion_factor

        if f"{GlossaryEnergy.EnergyMixCCSDemandsDfValue}:{GlossaryEnergy.carbon_captured}" not in self.outputs:
            self.outputs[f"{GlossaryEnergy.EnergyMixCCSDemandsDfValue}:{GlossaryEnergy.carbon_captured}"] = self.zeros_array
        if f"{GlossaryEnergy.EnergyMixCCSDemandsDfValue}:{GlossaryEnergy.carbon_storage}" not in self.outputs:
            self.outputs[f"{GlossaryEnergy.EnergyMixCCSDemandsDfValue}:{GlossaryEnergy.carbon_storage}"] = self.zeros_array

    def compute_energy_sector_ccs_consumption(self):
        self.outputs[f"{GlossaryEnergy.EnergyMixCCSConsumptionDfValue}:{GlossaryEnergy.Years}"] = self.years
        conversion_factor = GlossaryEnergy.conversion_dict[GlossaryEnergy.StreamCCSConsumption['unit']][GlossaryEnergy.EnergyMixCCSConsumptionDf['unit']]

        for energy in self.inputs[GlossaryEnergy.energy_list]:
            for ccs_stream in self.get_colnames_input_dataframe(
                    df_name=f'{energy}.{GlossaryEnergy.StreamCCSConsumptionValue}', expect_years=True, full_path=False):

                if f"{GlossaryEnergy.EnergyMixCCSConsumptionDfValue}:{ccs_stream}" not in self.outputs:
                    self.outputs[f"{GlossaryEnergy.EnergyMixCCSConsumptionDfValue}:{ccs_stream}"] = self.zeros_array

                self.outputs[f"{GlossaryEnergy.EnergyMixCCSConsumptionDfValue}:{ccs_stream}"] = \
                    self.outputs[f"{GlossaryEnergy.EnergyMixCCSConsumptionDfValue}:{ccs_stream}"] + \
                    self.inputs[f'{energy}.{GlossaryEnergy.StreamCCSConsumptionValue}:{ccs_stream}'] * conversion_factor

        if f"{GlossaryEnergy.EnergyMixCCSConsumptionDfValue}:{GlossaryEnergy.carbon_captured}" not in self.outputs:
            self.outputs[f"{GlossaryEnergy.EnergyMixCCSConsumptionDfValue}:{GlossaryEnergy.carbon_captured}"] = self.zeros_array
        if f"{GlossaryEnergy.EnergyMixCCSConsumptionDfValue}:{GlossaryEnergy.carbon_storage}" not in self.outputs:
            self.outputs[f"{GlossaryEnergy.EnergyMixCCSConsumptionDfValue}:{GlossaryEnergy.carbon_storage}"] = self.zeros_array

    def compute_ghg_emissions_intensity_by_energy(self):
        """Gather all ghg intensities into one dataframe, for each ghg."""
        for ghg in GlossaryEnergy.GreenHouseGases:
            self.outputs[f"{ghg}_intensity_by_energy:{GlossaryEnergy.Years}"] = self.years

            for energy in self.inputs[GlossaryEnergy.energy_list]:
                self.outputs[f"{ghg}_intensity_by_energy:{energy}"] = \
                    self.inputs[f'{energy}.{GlossaryEnergy.StreamScope1GHGIntensityValue}:{ghg}']