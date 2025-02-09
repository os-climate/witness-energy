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
    CO2_list = [f'{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit})',
                f'{GlossaryEnergy.CO2FromFlueGas} ({GlossaryEnergy.mass_unit})',
                f'{GlossaryEnergy.carbon_storage} ({GlossaryEnergy.mass_unit})',
                f'{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit})',
                f'{GlossaryEnergy.CarbonResource} ({GlossaryEnergy.mass_unit})']
    def __init__(self, name, logger: logging.Logger):
        super().__init__()
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
        self.compute_all_streams_demand_ratio()

        self.compute_price_by_energy()
        self.compute_energy_mix()
        self.compute_mean_energy_price()

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

        energy_type_capitals = []
        for energy in self.inputs[GlossaryEnergy.energy_list]:
            energy_type_capitals.append(
                self.inputs[f"{energy}.{GlossaryEnergy.EnergyTypeCapitalDfValue}:{GlossaryEnergy.Capital}"])

        energy_capital = np.sum(energy_type_capitals, axis=0) / 1e3

        energy_type_non_use_capitals = []
        for energy in self.inputs[GlossaryEnergy.energy_list]:
            energy_type_non_use_capitals.append(
                self.inputs[f"{energy}.{GlossaryEnergy.EnergyTypeCapitalDfValue}:{GlossaryEnergy.NonUseCapital}"])

        energy_non_use_capital = np.sum(energy_type_non_use_capitals, axis=0) / 1e3

        self.outputs[f"{GlossaryEnergy.EnergyCapitalDfValue}:{GlossaryEnergy.Years}"] = self.years
        self.outputs[f"{GlossaryEnergy.EnergyCapitalDfValue}:{GlossaryEnergy.Capital}"] = energy_capital
        self.outputs[f"{GlossaryEnergy.EnergyCapitalDfValue}:{GlossaryEnergy.NonUseCapital}"] = energy_non_use_capital

    def compute_raw_energy_production(self):
        """Sum all the energy production"""

        self.outputs[f'energy_production_brut_detailed:{GlossaryEnergy.Years}'] = self.years
        for energy in self.inputs[GlossaryEnergy.energy_list]:
            column_name = f'{energy} ({GlossaryEnergy.unit_dicts[energy]})'
            self.outputs[f'energy_production_brut_detailed:{column_name}'] = \
                self.inputs[f'{energy}.{GlossaryEnergy.StreamProductionValue}:{energy}'] * 1e3

        # Total computation :
        energy_cols = list(filter(lambda x: x.endswith(f"({GlossaryEnergy.energy_unit})"),
                                  self.get_colnames_output_dataframe(df_name='energy_production_brut_detailed', expect_years=True)))
        energy_columns = [self.outputs[f"energy_production_brut_detailed:{col}"] for col in energy_cols]

        self.outputs[f'energy_production_brut:{GlossaryEnergy.Years}'] = self.years
        self.outputs['energy_production_brut:Total'] = self.sum_cols(energy_columns)

    def compute_net_energy_production(self):
        """
        Net energy = Raw energy production - Energy consumed for energy production - energy consumed for CCUS - heat losses
        """

        self.outputs[f"net_energy_production_details:{GlossaryEnergy.Years}"] = self.years
        for energy in self.inputs[GlossaryEnergy.energy_list]:
            # starting from raw energy production
            column_name_energy = f'{energy} (TWh)'
            raw_production_energy = self.outputs[f"energy_production_brut_detailed:{column_name_energy}"]

            # coarse technos:
            if energy in self.raw_to_net_dict:
                net_energy_production_in_energy_sector = self.raw_to_net_dict[energy] * raw_production_energy
            else:
                energy_consumption_in_energy_sector = self.outputs[f"energy_consumption:{energy}"]
                net_energy_production_in_energy_sector = raw_production_energy - energy_consumption_in_energy_sector

            net_production_positive_part = self.pseudo_max(net_energy_production_in_energy_sector, 1e-3)
            self.outputs[f"net_energy_production_details:{energy}"] = net_production_positive_part

        self.outputs["net_energy_production_details:heat_losses"] = \
            - self.outputs['energy_production_brut:Total'] * self.inputs['heat_losses_percentage'] / 100.0

        self.outputs["net_energy_production_details:Total"] = self.sum_cols(
            self.get_cols_output_dataframe(df_name="net_energy_production_details", expect_years=True)
        )

        self.outputs[f"net_energy_production:{GlossaryEnergy.Years}"] = self.outputs[f"net_energy_production_details:{GlossaryEnergy.Years}"]
        self.outputs["net_energy_production:Total"] = self.outputs["net_energy_production_details:Total"]

    def compute_net_prod_of_coarse_energies(self, energy):
        """Compute the energy production share to remove for coarse techno to go from raw to net"""
        return (1.0 - self.raw_to_net_dict[energy]) if energy in self.raw_to_net_dict else 0.

    def compute_price_by_energy(self):
        '''
        Compute the price of each energy.
        Energy price (techno, year) = Raw energy price (techno, year) + CO2 emitted(techno, year) * carbon tax ($/tEqCO2)
        after carbon tax with all technology prices and technology weights computed with energy production
        '''

        self.outputs[f"{GlossaryEnergy.EnergyPricesValue}:{GlossaryEnergy.Years}"] = self.years

        for energy in self.inputs[GlossaryEnergy.energy_list]:
            self.outputs[f"{GlossaryEnergy.EnergyPricesValue}:{energy}"] = \
                self.inputs[f'{energy}.{GlossaryEnergy.EnergyPricesValue}:{energy}'] + \
                self.inputs[f'{energy}.{GlossaryEnergy.CO2PerUse}:{GlossaryEnergy.CO2PerUse}'] * \
                self.inputs[f"{GlossaryEnergy.CO2TaxesValue}:{GlossaryEnergy.CO2Tax}"]

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

        total_net_energy_prod_wo_heat_losses = self.outputs["net_energy_production_details:Total"] - \
                                               self.outputs["net_energy_production_details:heat_losses"]

        for energy in self.inputs[GlossaryEnergy.energy_list]:
            self.outputs[f"energy_mix:{energy}"] = self.outputs[f"net_energy_production_details:{energy}"] / \
                                                   total_net_energy_prod_wo_heat_losses * 100.

    def compute_all_streams_demand_ratio(self):
        """
        For each stream, compute the limitation ratio for its usage

        Ratio stream A = minimum(1, production of stream A / demand for stream A)

        Then, inside technos using stream A for their production, the desired production is multiplied by
        Ratio stream A to compute the real production.
        """
        self.outputs[f"{GlossaryEnergy.AllStreamsDemandRatioValue}:{GlossaryEnergy.Years}"] = self.years

        for stream_consumption in self.get_colnames_output_dataframe("demands_df", expect_years=True, full_path=False):
            if f'energy_production_brut_detailed:{stream_consumption}' in self.outputs:
                stream_raw_production = self.outputs[f'energy_production_brut_detailed:{stream_consumption}']
                demand_for_stream = self.outputs[f"demands_df:{stream_consumption}"]

                # pseudo min(1, raw_prod / demand) :
                array_for_min = self.np.array([
                    self.np.ones_like(self.years),
                    stream_raw_production / demand_for_stream,
                ]).T
                self.outputs[f'{GlossaryEnergy.AllStreamsDemandRatioValue}:{stream_consumption}'] = \
                    self.cons_smooth_minimum_vect(array_for_min)
            else:
                self.logger.warning(f"{stream_consumption} is consumed but not produced in current study. No limiting ratio assumed.")
                self.outputs[f'{GlossaryEnergy.AllStreamsDemandRatioValue}:{stream_consumption}'] = self.zeros_array + 1.

    def compute_target_production_constraint(self):
        """should be negative when satisfied"""
        self.outputs[f"{GlossaryEnergy.TargetProductionConstraintValue}:{GlossaryEnergy.Years}"] = self.years

        actual_net_production = self.outputs["net_energy_production:Total"]
        target_prod = self.inputs[f"{GlossaryEnergy.TargetEnergyProductionValue}:{GlossaryEnergy.TargetEnergyProductionValue}"]
        constraint_normalized = (actual_net_production - target_prod) / target_prod
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
        self.outputs[f"demands_df:{GlossaryEnergy.Years}"] = self.years

        for energy in self.inputs[GlossaryEnergy.energy_list]:
            for other_energy_demand in self.get_colnames_input_dataframe(
                    df_name=f'{energy}.{GlossaryEnergy.StreamEnergyDemandValue}', expect_years=True, full_path=False):
                if f"demands_df:{other_energy_demand}" not in self.outputs:
                    self.outputs[f"demands_df:{other_energy_demand}"] = self.zeros_array
                self.outputs[f"demands_df:{other_energy_demand}"] = \
                    self.outputs[f"demands_df:{other_energy_demand}"] + \
                    self.inputs[f'{energy}.{GlossaryEnergy.StreamEnergyDemandValue}:{other_energy_demand}'] * 1e3

    def compute_energy_consumptions_by_energy_sector(self):
        """For each energy, sum what has been consumed by other energy"""

        self.outputs[f"energy_consumption:{GlossaryEnergy.Years}"] = self.years
        for energy in self.inputs[GlossaryEnergy.energy_list]:
            # starting from raw energy production
            column_name_energy = f'{energy} (TWh)'

            # removing consumed energy
            consumed_energy_by_energy_list = []
            for other_energy in self.inputs[GlossaryEnergy.energy_list]:
                consumptions_of_other_energy = self.get_colnames_input_dataframe(df_name=f'{other_energy}.{GlossaryEnergy.StreamEnergyConsumptionValue}', expect_years=True, full_path=False)
                if column_name_energy in consumptions_of_other_energy:
                    consumed_energy_by_energy_list.append(
                        self.inputs[f'{other_energy}.{GlossaryEnergy.StreamEnergyConsumptionValue}:{column_name_energy}'])

            consumed_energy_by_other_energy_sum = self.sum_cols(consumed_energy_by_energy_list) * 1e3 if consumed_energy_by_energy_list else self.zeros_array
            self.outputs[f"energy_consumption:{energy}"] = consumed_energy_by_other_energy_sum


        self.outputs["energy_consumption:Total"] = self.sum_cols(
            self.get_cols_output_dataframe(df_name="energy_consumption", expect_years=True)
        )

    def compute_ghg_emissions(self):
        """Sum the emissions for each GHG (CO2, CH4, N2O)"""
        for ghg in GlossaryEnergy.GreenHouseGases:
            self._aggregate_column_from_all_streams(output_varname="ghg_emission", input_stream_varname=GlossaryEnergy.StreamScope1GHGEmissionsValue, column_name=ghg)

    def _aggregate_column_from_all_streams(self, output_varname: str, input_stream_varname: str, column_name: str):
        self.outputs[f"{output_varname}:{GlossaryEnergy.Years}"] = self.years

        for techno in self.inputs[GlossaryEnergy.techno_list]:
            output_path = f"{output_varname}:{column_name}"
            if output_path in self.outputs:
                self.outputs[output_path] = \
                    self.outputs[output_path] + \
                    self.inputs[f'{techno}.{input_stream_varname}:{column_name}']
