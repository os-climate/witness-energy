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

from copy import deepcopy

import numpy as np
import pandas as pd
from sostrades_core.tools.base_functions.exp_min import compute_func_with_exp_min
from sostrades_optimization_plugins.models.differentiable_model import DifferentiableModel
from sostrades_optimization_plugins.tools.cst_manager.func_manager_common import (
    smooth_maximum,
)

from energy_models.core.stream_type.carbon_models.carbon import Carbon
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.carbon_models.carbon_storage import CarbonStorage
from energy_models.core.stream_type.energy_models.biodiesel import BioDiesel
from energy_models.core.stream_type.energy_models.biogas import BioGas
from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
from energy_models.core.stream_type.energy_models.clean_energy import CleanEnergy
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.ethanol import Ethanol
from energy_models.core.stream_type.energy_models.fossil import Fossil
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import (
    GaseousHydrogen,
)
from energy_models.core.stream_type.energy_models.heat import (
    hightemperatureheat,
    lowtemperatureheat,
    mediumtemperatureheat,
)
from energy_models.core.stream_type.energy_models.hydrotreated_oil_fuel import (
    HydrotreatedOilFuel,
)
from energy_models.core.stream_type.energy_models.liquid_fuel import LiquidFuel
from energy_models.core.stream_type.energy_models.liquid_hydrogen import LiquidHydrogen
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.energy_models.solid_fuel import SolidFuel
from energy_models.core.stream_type.energy_models.syngas import Syngas
from energy_models.core.stream_type.resources_models.resource_glossary import (
    ResourceGlossary,
)
from energy_models.glossaryenergy import GlossaryEnergy


class EnergyMix(DifferentiableModel):
    """
    Class Energy mix
    """
    name = 'EnergyMix'
    PRODUCTION = 'production'
    CO2_TAX_MINUS_CCS_CONSTRAINT_DF = 'CO2_tax_minus_CCS_constraint_df'
    TOTAL_PROD_MINUS_MIN_PROD_CONSTRAINT_DF = 'total_prod_minus_min_prod_constraint_df'
    TOTAL_PROD_MINUS_MIN_PROD_CONSTRAINT = 'total_prod_minus_min_prod_constraint'
    CONSTRAINT_PROD_H2_LIQUID = 'total_prod_h2_liquid'
    CONSTRAINT_PROD_SOLID_FUEL_ELEC = 'total_prod_solid_fuel_elec'
    CONSTRAINT_PROD_HYDROELECTRIC = 'total_prod_hydroelectric'
    CO2_TAX_OBJECTIVE = 'CO2_tax_objective'
    SYNGAS_PROD_OBJECTIVE = 'syngas_prod_objective'
    SYNGAS_PROD_CONSTRAINT = 'syngas_prod_constraint'
    RESOURCE_LIST = ['natural_gas_resource', 'uranium_resource',
                     'coal_resource', 'oil_resource', 'copper_resource']  # , 'platinum_resource',]
    RESOURCE_CONSUMPTION_UNIT = ResourceGlossary.UNITS['consumption']
    energy_class_dict = {GaseousHydrogen.name: GaseousHydrogen,
                         LiquidFuel.name: LiquidFuel,
                         HydrotreatedOilFuel.name: HydrotreatedOilFuel,
                         GlossaryEnergy.electricity: Electricity,
                         Methane.name: Methane,
                         BioGas.name: BioGas,
                         BioDiesel.name: BioDiesel,
                         Ethanol.name: Ethanol,
                         SolidFuel.name: SolidFuel,
                         GlossaryEnergy.syngas: Syngas,
                         BiomassDry.name: BiomassDry,
                         LiquidHydrogen.name: LiquidHydrogen,
                         CleanEnergy.name: CleanEnergy,
                         Fossil.name: Fossil,
                         lowtemperatureheat.name: lowtemperatureheat,
                         mediumtemperatureheat.name: mediumtemperatureheat,
                         hightemperatureheat.name: hightemperatureheat
                         }

    # For simplified energy mix , raw_to_net factor is used to compute net
    # production from raw production
    raw_tonet_dict = {CleanEnergy.name: CleanEnergy.raw_to_net_production,
                      Fossil.name: Fossil.raw_to_net_production}

    only_energy_list = list(energy_class_dict.keys())

    stream_class_dict = {GlossaryEnergy.carbon_capture: CarbonCapture,
                         GlossaryEnergy.carbon_storage: CarbonStorage, }
    ccs_list = list(stream_class_dict.keys())
    stream_class_dict.update(energy_class_dict)

    energy_list = list(stream_class_dict.keys())
    resource_list = RESOURCE_LIST
    CO2_list = [f'{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit})',
                f'{CarbonCapture.flue_gas_name} ({GlossaryEnergy.mass_unit})',
                f'{GlossaryEnergy.carbon_storage} ({GlossaryEnergy.mass_unit})',
                f'{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit})',
                f'{Carbon.name} ({GlossaryEnergy.mass_unit})']
    solidFuel_name = SolidFuel.name
    electricity_name = GlossaryEnergy.electricity
    gaseousHydrogen_name = GaseousHydrogen.name
    liquidHydrogen_name = LiquidHydrogen.name
    biomass_name = GlossaryEnergy.biomass_dry
    syngas_name = GlossaryEnergy.syngas
    lowtemperatureheat_name = lowtemperatureheat.name
    mediumtemperatureheat_name = mediumtemperatureheat.name
    hightemperatureheat_name = hightemperatureheat.name

    energy_constraint_list = [solidFuel_name,
                              electricity_name, biomass_name, lowtemperatureheat_name, mediumtemperatureheat_name,
                              hightemperatureheat_name]
    movable_fuel_list = [liquidHydrogen_name,
                         LiquidFuel.name, BioDiesel.name, Methane.name]

    def __init__(self, name):
        '''
        Constructor
        '''
        self.name = name
        super().__init__()

    def configure_parameters_update(self):
        """Configure parameters with possible update (variables that does change during the run)"""
        self.year_start = self.inputs[GlossaryEnergy.YearStart]
        self.year_end = self.inputs[GlossaryEnergy.YearEnd]
        self.years = self.np.arange(self.year_start, self.year_end + 1)


        self.inputs["stream_list"] = list(self.inputs[GlossaryEnergy.energy_list]) + list(self.inputs[GlossaryEnergy.ccs_list])

        self.sub_production_dict = {}
        self.sub_consumption_dict = {}
        self.sub_consumption_woratio_dict = {}

        """
        for stream in self.inputs["stream_list"]:
            self.sub_production_dict[stream] = self.inputs[f'{stream}.{GlossaryEnergy.StreamProductionValue}'] * 1e3
            self.sub_consumption_dict[stream] = self.inputs[f'{stream}.{GlossaryEnergy.StreamConsumptionValue}'] * 1e3
            self.sub_consumption_woratio_dict[stream] = self.inputs[f'{stream}.{GlossaryEnergy.StreamConsumptionWithoutRatioValue}'] * 1e3

            if stream in self.energy_class_dict:
                self.sub_carbon_emissions[stream] = self.inputs[f'{stream}.{GlossaryEnergy.CO2EmissionsValue}'][stream]
        """

        self.price_by_energy = pd.DataFrame(
            {GlossaryEnergy.Years: self.years})

        # dataframe resource demand
        self.resources_demand = pd.DataFrame(
            {GlossaryEnergy.Years: self.years})
        self.resources_demand_woratio = pd.DataFrame(
            {GlossaryEnergy.Years: self.years})
        for elements in self.resource_list:
            if elements in self.resource_list:
                self.resources_demand[elements] = np.linspace(
                    0, 0, len(self.resources_demand.index)) * 100.
                self.resources_demand_woratio[elements] = np.linspace(
                    0, 0, len(self.resources_demand.index)) * 100.

        """
        for stream in self.inputs["stream_list"]:
            for resource in self.resource_list:
                if f'{resource} ({self.RESOURCE_CONSUMPTION_UNIT})' in self.sub_consumption_dict[stream].columns:
                    self.resources_demand[resource] = self.resources_demand[resource] + \
                                                      self.inputs[f'{stream}.{GlossaryEnergy.StreamConsumptionValue}'][
                                                          f'{resource} ({self.RESOURCE_CONSUMPTION_UNIT})'] * \
                                                      1e3
                    self.resources_demand_woratio[resource] = self.resources_demand_woratio[resource] + \
                                                              self.inputs[
                                                                  f'{stream}.{GlossaryEnergy.StreamConsumptionWithoutRatioValue}'][
                                                                  f'{resource} ({self.RESOURCE_CONSUMPTION_UNIT})'] * \
                                                              1e3

        """

    def compute_energy_capital(self):
        """sum of positive energy production --> raw total production"""

        energy_type_capitals = []
        for energy in self.inputs[GlossaryEnergy.energy_list]:
            energy_ = energy
            energy_type_capitals.append(
                self.inputs[f"{energy_}.{GlossaryEnergy.EnergyTypeCapitalDfValue}"][GlossaryEnergy.Capital])

        for ccs in self.inputs[GlossaryEnergy.ccs_list]:
            energy_type_capitals.append(
                self.inputs[f"{ccs}.{GlossaryEnergy.EnergyTypeCapitalDfValue}"][GlossaryEnergy.Capital])

        energy_capital = np.sum(energy_type_capitals, axis=0) / 1e3

        energy_type_non_use_capitals = []
        for energy in self.inputs[GlossaryEnergy.energy_list]:
            energy_ = energy
            energy_type_non_use_capitals.append(
                self.inputs[f"{energy_}.{GlossaryEnergy.EnergyTypeCapitalDfValue}"][GlossaryEnergy.NonUseCapital])

        for ccs in self.inputs[GlossaryEnergy.ccs_list]:
            energy_type_non_use_capitals.append(
                self.inputs[f"{ccs}.{GlossaryEnergy.EnergyTypeCapitalDfValue}"][GlossaryEnergy.NonUseCapital])

        energy_non_use_capital = np.sum(energy_type_non_use_capitals, axis=0) / 1e3

        self.energy_capital = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.Capital: energy_capital,
            GlossaryEnergy.NonUseCapital: energy_non_use_capital,
        })

    def compute_non_use_capital_mean_by_stream(self):
        """to minimize"""

        streams = self.inputs[GlossaryEnergy.energy_list] + self.inputs[GlossaryEnergy.ccs_list]
        obj = 0.
        for stream in streams:
            stream_ = stream
            stream_capital = self.inputs[f"{stream_}.{GlossaryEnergy.EnergyTypeCapitalDfValue}"][GlossaryEnergy.Capital]
            stream_non_used_capital = self.inputs[f"{stream_}.{GlossaryEnergy.EnergyTypeCapitalDfValue}"][GlossaryEnergy.NonUseCapital]
            stream_capital[stream_capital == 0] = 1.
            stream_non_use_capital_ratio = (stream_non_used_capital / stream_capital).mean()
            obj += stream_non_use_capital_ratio

        self.non_use_capital_obj_by_stream = np.array([obj / len(streams)])

    def compute_raw_production(self):
        """sum of positive energy production --> raw total production"""

        self.outputs[f'energy_production_brut_detailed:{GlossaryEnergy.Years}'] = self.years
        for stream in self.inputs["stream_list"]:
            column_name = f'{self.PRODUCTION} {stream} ({self.stream_class_dict[stream].unit})'
            self.outputs[f'energy_production_brut_detailed:{column_name}'] = self.inputs[f'{stream}.{GlossaryEnergy.StreamProductionValue}:{stream}'] * 1e3


        # Total computation :
        energy_cols = list(filter(lambda x: x.endswith(f"({GlossaryEnergy.energy_unit})"),
                                  self.get_colnames_output_dataframe(df_name='energy_production_brut_detailed', expect_years=True)))
        energy_columns = [self.outputs[f"energy_production_brut_detailed:{col}"] for col in energy_cols]

        self.outputs[f'energy_production_brut:{GlossaryEnergy.Years}'] = self.years
        self.outputs[f'energy_production_brut:{GlossaryEnergy.TotalProductionValue}'] = self.sum_cols(energy_columns)

    def compute_net_consumable_energy(self):
        """consumable energy = Raw energy production - Energy consumed for energy production"""

        self.consumable_energy_df = pd.DataFrame({GlossaryEnergy.Years: self.years})
        self.consumed_energy_by_ccus_sum = {}
        for energy in self.inputs[GlossaryEnergy.energy_list]:
            # starting from raw energy production
            column_name_energy = f'{self.PRODUCTION} {energy} ({self.stream_class_dict[energy].unit})'
            raw_production_energy = self.outputs[f"energy_production_brut_detailed:{column_name_energy}"]

            # removing consumed energy
            consumed_energy_by_energy_list = []
            consumed_energy_by_ccus_list = []
            column_name_consumption = f'{energy} ({self.stream_class_dict[energy].unit})'
            for energy_other, consu in self.sub_consumption_dict.items():
                if column_name_consumption in consu.columns:
                    if energy_other in self.inputs[GlossaryEnergy.energy_list]:
                        consumed_energy_by_energy_list.append(consu[column_name_consumption])
                    else:
                        consumed_energy_by_ccus_list.append(consu[column_name_consumption])
            consumed_energy_by_energy_sum = np.sum(np.array(consumed_energy_by_energy_list), axis=0) if len(
                consumed_energy_by_energy_list) else 0.
            self.consumed_energy_by_ccus_sum[energy] = np.sum(np.array(consumed_energy_by_ccus_list), axis=0) if len(
                consumed_energy_by_ccus_list) else 0.
            # obtaining net energy production for the techno
            column_name = f'{self.PRODUCTION} {energy} ({self.stream_class_dict[energy].unit})'
            prod_raw_to_substract = self.compute_net_prod_of_coarse_energies(energy, column_name)
            self.consumable_energy_df[
                column_name_energy] = raw_production_energy - consumed_energy_by_energy_sum - prod_raw_to_substract

        columns_to_sum = [column for column in self.consumable_energy_df if column.endswith(f"({GlossaryEnergy.energy_unit})")]
        self.consumable_energy_df[GlossaryEnergy.TotalProductionValue] = self.consumable_energy_df[columns_to_sum].sum(
            axis=1)

        # substract a percentage of raw production into net production
        self.consumable_energy_df[GlossaryEnergy.TotalProductionValue] -= self.production_raw[
                                                                              GlossaryEnergy.TotalProductionValue] * \
                                                                          self.inputs['heat_losses_percentage'] / 100.0

    def compute_net_energy_production(self):
        """
        Net energy production = Raw energy production - Energy consumed for energy production - Energy used by CCUS
        """
        self.production = deepcopy(self.consumable_energy_df)
        # taking into account consumption of ccs technos
        for ccs in self.inputs[GlossaryEnergy.ccs_list]:
            # production_column_name_ccs = f'{self.PRODUCTION} {ccs} ({GlossaryEnergy.energy_unit})'
            # if ccs in self.sub_consumption_dict:
            #     consumption_ccs_df = self.sub_consumption_dict[ccs]
            #     ccs_consumptions_list = []
            #     for column in consumption_ccs_df.columns:
            #         if column.endswith(f"({GlossaryEnergy.energy_unit})"):
            #             ccs_consumptions_list.append(consumption_ccs_df[column])
            #     self.production[production_column_name_ccs] = - np.sum(np.array(ccs_consumptions_list), axis=0) if len(
            #         ccs_consumptions_list) else 0.

            production_column_name_ccs = f'{self.PRODUCTION} {ccs} ({GlossaryEnergy.mass_unit})'
            if ccs in self.sub_consumption_dict:
                consumption_ccs_df = self.sub_consumption_dict[ccs]
                ccs_consumptions_list = []
                for column in consumption_ccs_df.columns:
                    if column.endswith(f"({GlossaryEnergy.mass_unit})"):
                        ccs_consumptions_list.append(consumption_ccs_df[column])
                self.production[production_column_name_ccs] = - np.sum(np.array(ccs_consumptions_list), axis=0) if len(
                    ccs_consumptions_list) else 0.
        # Delete energy used by ccs from energy production (and not only from total production)
        for energy in self.inputs[GlossaryEnergy.energy_list]:
            production_column_name_energy = f'{self.PRODUCTION} {energy} ({GlossaryEnergy.energy_unit})'
            self.production[production_column_name_energy] -= self.consumed_energy_by_ccus_sum[energy]

        # Net energy production = Raw energy production - Energy consumed for energy production - Energy used by CCUS
        columns_to_sum = [column for column in self.production if column.endswith(f"({GlossaryEnergy.energy_unit})")]
        self.production[GlossaryEnergy.TotalProductionValue] = self.production[columns_to_sum].sum(axis=1)

        self.production[GlossaryEnergy.TotalProductionValue] -= self.production_raw[
                                                                    GlossaryEnergy.TotalProductionValue] * \
                                                                self.inputs['heat_losses_percentage'] / 100.0

    def compute_energy_production_uncut(self):
        """maybe to delete"""
        self.production['Total production (uncut)'] = self.production[GlossaryEnergy.TotalProductionValue]
        min_energy = self.inputs['minimum_energy_production']
        for year in self.production.index:
            if self.production.at[year, GlossaryEnergy.TotalProductionValue] < min_energy:
                # To avoid underflow : exp(-200) is considered to be the
                # minimum value for the exp
                production_year = max(
                    self.production.at[year, GlossaryEnergy.TotalProductionValue], -200.0 * min_energy)
                self.production.loc[year, GlossaryEnergy.TotalProductionValue] = min_energy / 10. * \
                                                                                 (9 + np.exp(
                                                                                     production_year / min_energy) * np.exp(
                                                                                     -1))

    def compute_net_prod_of_coarse_energies(self, energy, column_name):
        '''
        Compute the net production for coarse energies which does not have energy consumption
        We use a raw/net ratio to compute consumed energy production
        consu = raw-net = raw(1-1/ratio)
        '''
        try:
            return self.production_raw[column_name] * \
                   (1.0 - self.raw_tonet_dict[energy])
        except KeyError:
            return 0.

    def compute_price_by_energy(self):
        '''
        Compute the price of each energy.
        Energy price (techno, year) = Raw energy price (techno, year) + CO2 emitted(techno, year) * carbon tax ($/tEqCO2)
        after carbon tax with all technology prices and technology weights computed with energy production
        '''

        for energy in self.inputs["stream_list"]:
            if energy in self.energy_class_dict:
                self.price_by_energy[energy] = self.inputs[f'{energy}.{GlossaryEnergy.StreamPricesValue}:{energy}'] + \
                                               self.inputs[f'{energy}.{GlossaryEnergy.CO2PerUse}'][GlossaryEnergy.CO2PerUse] * \
                                               self.inputs[f"{GlossaryEnergy.CO2TaxesValue}:{GlossaryEnergy.CO2Tax}"]

    def compute_CO2_emissions_ratio(self):
        '''
        Compute the CO2 emission_ratio in kgCO2/kWh for the MDA
        '''
        self.carbon_emissions_after_use = pd.DataFrame(
            {GlossaryEnergy.Years: self.total_carbon_emissions[GlossaryEnergy.Years]})
        for stream in self.inputs["stream_list"]:
            if stream in self.energy_class_dict:
                self.total_carbon_emissions[stream] = self.inputs[f'{stream}.{GlossaryEnergy.CO2EmissionsValue}:{stream}']
                self.carbon_emissions_after_use[stream] = self.total_carbon_emissions[stream] + \
                                                          self.inputs[f'{stream}.{GlossaryEnergy.CO2PerUse}'][stream][GlossaryEnergy.CO2PerUse]
            else:
                self.total_carbon_emissions[stream] = 0.  # todo: fixme, Antoine: shouldnt we compute emissions for each stream, even ccs ones ?

    def compute_CO2_emissions(self):
        '''
        Compute CO2 total emissions
        '''
        # Initialize dataframes
        self.total_co2_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: self.production[GlossaryEnergy.Years]})
        self.co2_production = pd.DataFrame({GlossaryEnergy.Years: self.production[GlossaryEnergy.Years]})
        self.co2_consumption = pd.DataFrame(
            {GlossaryEnergy.Years: self.production[GlossaryEnergy.Years]})
        self.emissions_by_energy = pd.DataFrame(
            {GlossaryEnergy.Years: self.production[GlossaryEnergy.Years]})
        # Do not loop over carbon capture and carbon storage which will be
        # handled differently

        for energy in self.inputs["stream_list"]:
            self.emissions_by_energy[energy] = np.zeros_like(
                self.production[GlossaryEnergy.Years])
            if energy in self.only_energy_list:

                # gather all production columns with a CO2 name in it
                for col, production in self.sub_production_dict[energy].items():
                    if col in self.CO2_list:
                        self.co2_production[f'{energy} {col}'] = production
                        self.emissions_by_energy[
                            energy] += self.co2_production[f'{energy} {col}']
                # gather all consumption columns with a CO2 name in it
                for col, consumption in self.sub_consumption_dict[energy].items():
                    if col in self.CO2_list:
                        self.co2_consumption[f'{energy} {col}'] = consumption
                        self.emissions_by_energy[
                            energy] -= self.co2_consumption[f'{energy} {col}']
                # Compute the CO2 emitted during the use of the net energy
                # If net energy is negative, CO2 by use is equals to zero

                self.co2_production[f'{energy} CO2 by use (Mt)'] = self.inputs[f'{energy}.{GlossaryEnergy.CO2PerUse}:{GlossaryEnergy.CO2PerUse}'] * np.maximum(
                    0.0, self.production[f'production {energy} ({self.energy_class_dict[energy].unit})'])
                self.emissions_by_energy[
                    energy] += self.co2_production[f'{energy} CO2 by use (Mt)']

        ''' CARBON CAPTURE needed by energy mix
        Total carbon capture needed by energy mix if a technology needs carbon_capture
         Ex :Sabatier process or RWGS in FischerTropsch technology
        '''
        energy_needing_carbon_capture = self.co2_consumption[[
            col for col in self.co2_consumption if col.endswith(f'{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit})')]]
        energy_needing_carbon_capture_list = [key.replace(
            f' {GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit})', '') for key in energy_needing_carbon_capture]
        if len(energy_needing_carbon_capture_list) != 0:
            self.total_co2_emissions[
                f'{GlossaryEnergy.carbon_capture} needed by energy mix (Mt)'] = energy_needing_carbon_capture.sum(
                axis=1)
        else:
            self.total_co2_emissions[
                f'{GlossaryEnergy.carbon_capture} needed by energy mix (Mt)'] = 0.0

        # Put in Gt carbon capture needed by energy mix
        self.co2_emissions_needed_by_energy_mix = pd.DataFrame(
            {GlossaryEnergy.Years: self.production[GlossaryEnergy.Years],
             f'{GlossaryEnergy.carbon_capture} needed by energy mix (Gt)': self.total_co2_emissions[
                                                                    f'{GlossaryEnergy.carbon_capture} needed by energy mix (Mt)'] / 1e3})

        ''' CARBON CAPTURE from energy mix
        Total carbon capture from energy mix if the technology offers carbon_capture
         Ex : upgrading biogas technology is the same as Amine Scrubbing but
         on a different gas (biogas for upgrading biogas and flue gas for
         Amien scrubbing)
        '''
        energy_producing_carbon_capture = self.co2_production[[
            col for col in self.co2_production if col.endswith(f'{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit})')]]
        energy_producing_carbon_capture_list = [key.replace(
            f' {GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit})', '') for key in energy_producing_carbon_capture]
        if len(energy_producing_carbon_capture_list) != 0:
            self.total_co2_emissions[
                f'{GlossaryEnergy.carbon_capture} from energy mix (Mt)'] = energy_producing_carbon_capture.sum(
                axis=1)
        else:
            self.total_co2_emissions[
                f'{GlossaryEnergy.carbon_capture} from energy mix (Mt)'] = 0.0

        # Put in Gt CO2 from energy mix nedded for ccus discipline
        self.carbon_capture_from_energy_mix = pd.DataFrame(
            {GlossaryEnergy.Years: self.production[GlossaryEnergy.Years],
             f'{GlossaryEnergy.carbon_capture} from energy mix (Gt)': self.total_co2_emissions[
                                                               f'{GlossaryEnergy.carbon_capture} from energy mix (Mt)'] / 1e3})

    def compute_net_positive_consumable_energy_production(self) -> pd.DataFrame:
        """Takes the positive part of the net consumable energy production for each energy
        (without energy consumed by CCUS)"""
        net_positives_consumable_energy_productions = {}
        for energy in self.inputs[GlossaryEnergy.energy_list]:
            column_name = f'production {energy} ({self.energy_class_dict[energy].unit})'
            net_positives_consumable_energy_productions[energy] = np.maximum(0.0,
                                                                             self.consumable_energy_df[column_name])

        total_net_positive_consumable_production = pd.DataFrame(net_positives_consumable_energy_productions).sum(axis=1)

        net_positive_consumable_energy_production = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                                                  **net_positives_consumable_energy_productions,
                                                                  GlossaryEnergy.TotalProductionValue: total_net_positive_consumable_production})
        self.net_positive_consumable_energy_production = net_positive_consumable_energy_production
        return net_positive_consumable_energy_production

    def compute_mean_price(self, exp_min: bool = True):
        '''
        Compute energy mean price and price of each energy after carbon tax
        returns energy_mean price
                type:dataframe (years,energy_price)
                production_energy_pos (years,energies)
        '''
        energy_mean_price = pd.DataFrame(
            columns=[GlossaryEnergy.Years, GlossaryEnergy.EnergyPriceValue])
        energy_mean_price[GlossaryEnergy.Years] = self.production[GlossaryEnergy.Years]
        energy_mean_price[GlossaryEnergy.EnergyPriceValue] = 0.0

        element_dict = dict(zip(self.inputs[GlossaryEnergy.energy_list], self.inputs[GlossaryEnergy.energy_list]))
        if exp_min:
            prod_element, prod_total_for_mix_weight = self.compute_total_prod(
                self.net_positive_consumable_energy_production, element_dict, self.inputs['production_threshold'])
        else:
            prod_element, prod_total_for_mix_weight = self.compute_prod_wcutoff(
                self.net_positive_consumable_energy_production, element_dict, self.inputs['production_threshold'])

        for energy in self.inputs[GlossaryEnergy.energy_list]:
            # compute mix weights for each energy
            mix_weight = prod_element[energy] / prod_total_for_mix_weight
            # If the element is negligible do not take into account this element
            # It is negligible if tol = 0.1%
            tol = 1e-3
            mix_weight[mix_weight < tol] = 0.0
            energy_mean_price[GlossaryEnergy.EnergyPriceValue] += self.price_by_energy[energy] * \
                                                                  mix_weight
            self.mix_weights[energy] = mix_weight

        # In case all the technologies are below the threshold assign a
        # placeholder price
        if not exp_min:
            for year in energy_mean_price[GlossaryEnergy.Years]:
                if np.real(energy_mean_price.loc[energy_mean_price[GlossaryEnergy.Years] == year][
                               GlossaryEnergy.EnergyPriceValue]) == 0.0:
                    year_energy_prices = self.price_by_energy[
                        self.inputs[GlossaryEnergy.energy_list]].loc[energy_mean_price[GlossaryEnergy.Years] == year]
                    min_energy_price = min(
                        val for val in year_energy_prices[0] if val > 0.0)
                    min_energy_name = [
                        name for name in year_energy_prices.columns if
                        year_energy_prices[name] == min_energy_price][0]
                    energy_mean_price.loc[energy_mean_price[GlossaryEnergy.Years] ==
                                          year, GlossaryEnergy.EnergyPriceValue] = min_energy_price
                    for energy in self.inputs[GlossaryEnergy.energy_list]:
                        self.mix_weights.loc[self.mix_weights[GlossaryEnergy.Years] == year,
                                             energy] = 1. if energy == min_energy_name else 0.0

        self.energy_mean_price = energy_mean_price
        return energy_mean_price

    def compute_total_prod_minus_min_prod_constraint(self):
        '''
        Compute constraint for total production. Calculated on production before exponential decrease towards the limit.
        Input: self.production['Total production (uncut)'], self.inputs['minimum_energy_production']
        Output: total_prod_minus_min_prod_constraint_df
        '''

        self.outputs[f"{self.TOTAL_PROD_MINUS_MIN_PROD_CONSTRAINT_DF}:{GlossaryEnergy.Years}"] = self.years
        self.outputs[f"{self.TOTAL_PROD_MINUS_MIN_PROD_CONSTRAINT_DF}:{self.TOTAL_PROD_MINUS_MIN_PROD_CONSTRAINT}"] = \
            (self.production['Total production (uncut)'] - self.inputs['minimum_energy_production']) / self.inputs['total_prod_minus_min_prod_constraint_ref']

    def compute_constraint_h2(self):
        self.constraint_liquid_hydrogen = pd.DataFrame(
            {GlossaryEnergy.Years: self.production[GlossaryEnergy.Years]})
        self.constraint_liquid_hydrogen['constraint_liquid_hydrogen'] = 0.
        hydrogen_name_list = [
            self.gaseousHydrogen_name, self.liquidHydrogen_name]
        # compute total H2 production
        for energy in hydrogen_name_list:
            if f'{self.PRODUCTION} {energy} ({self.energy_class_dict[energy].unit})' in self.production.columns:
                self.constraint_liquid_hydrogen['constraint_liquid_hydrogen'] += self.production[
                    f'{self.PRODUCTION} {energy} ({self.energy_class_dict[energy].unit})']
        if f'{self.PRODUCTION} {self.liquidHydrogen_name} ({self.energy_class_dict[self.liquidHydrogen_name].unit})' in self.production.columns:
            self.constraint_liquid_hydrogen['constraint_liquid_hydrogen'] = - (
                    self.inputs['liquid_hydrogen_percentage'] * self.constraint_liquid_hydrogen[
                'constraint_liquid_hydrogen'] -
                    self.production[
                        f'{self.PRODUCTION} {self.liquidHydrogen_name} ({self.energy_class_dict[self.liquidHydrogen_name].unit})']) / self.inputs['liquid_hydrogen_constraint_ref']

    def compute_constraint_solid_fuel_elec(self):
        self.constraint_solid_fuel_elec = pd.DataFrame(
            {GlossaryEnergy.Years: self.production[GlossaryEnergy.Years]})
        self.constraint_solid_fuel_elec['constraint_solid_fuel_elec'] = 0.

        for energy in self.energy_constraint_list:
            if f'{self.PRODUCTION} {energy} ({self.energy_class_dict[energy].unit})' in self.production.columns:
                self.constraint_solid_fuel_elec['constraint_solid_fuel_elec'] += self.production[
                    f'{self.PRODUCTION} {energy} ({self.energy_class_dict[energy].unit})']
        self.constraint_solid_fuel_elec['constraint_solid_fuel_elec'] = - (self.constraint_solid_fuel_elec[
                                                                               'constraint_solid_fuel_elec'] - self.inputs['solid_fuel_elec_percentage'] *
                                                                           self.production[
                                                                               GlossaryEnergy.TotalProductionValue]) / self.inputs['solid_fuel_elec_constraint_ref']

    def compute_syngas_prod_objective(self):
        '''
        Compute Syngas production objective
        '''
        if f'{self.PRODUCTION} {self.syngas_name} ({self.energy_class_dict[self.syngas_name].unit})' in self.production:
            self.syngas_prod_objective = np.sign(self.production[
                                                     f'{self.PRODUCTION} {self.syngas_name} ({self.energy_class_dict[self.syngas_name].unit})']) * \
                                         self.production[
                                             f'{self.PRODUCTION} {self.syngas_name} ({self.energy_class_dict[self.syngas_name].unit})'] / \
                                         self.inputs['syngas_prod_ref']
        else:
            self.syngas_prod_objective = self.zeros_array

    def compute_syngas_prod_constraint(self):
        '''
        Compute Syngas production objective
        '''
        if f'{self.PRODUCTION} {self.syngas_name} ({self.energy_class_dict[self.syngas_name].unit})' in self.production:
            self.syngas_prod_constraint = (self.inputs['syngas_prod_constraint_limit'] - self.production[
                f'{self.PRODUCTION} {self.syngas_name} ({self.energy_class_dict[self.syngas_name].unit})']) / \
                                          self.inputs['syngas_prod_ref']
        else:
            self.syngas_prod_constraint = self.zeros_array

    def compute_all_streams_demand_ratio(self):
        '''! Computes the demand_ratio dataframe.
        The ratio is calculated using the production and consumption WITHOUT the ratio applied
        The value of the ratio is capped to 100.0
        '''
        demand_ratio_df = pd.DataFrame(
            {GlossaryEnergy.Years: self.years})

        for stream in self.inputs["stream_list"]:

            # Prod with ratio
            energy_production = deepcopy(
                self.sub_production_dict[f'{stream}'][f'{stream}'])
            # consumption without ratio
            sub_cons = self.sub_consumption_woratio_dict

            energy_consumption = self.zeros_array
            for idx, consu in sub_cons.items():
                if f'{stream} ({self.stream_class_dict[stream].unit})' in consu.columns:
                    energy_consumption = np.sum([energy_consumption, consu[
                        f'{stream} ({self.stream_class_dict[stream].unit})']], axis=0)
            # if energy is in raw_tonet_dict, add the consumption due to raw_to_net ratio to energy_consumption
            if stream in self.raw_tonet_dict.keys():
                column_name = f'{self.PRODUCTION} {stream} ({self.stream_class_dict[stream].unit})'
                prod_raw_to_substract = self.compute_net_prod_of_coarse_energies(stream, column_name)
                energy_production -= prod_raw_to_substract

            energy_prod_limited = compute_func_with_exp_min(
                energy_production, 1.0e-10)
            energy_cons_limited = compute_func_with_exp_min(
                energy_consumption, 1.0e-10)

            demand_ratio_df[f'{stream}'] = np.minimum(
                np.maximum(energy_prod_limited / energy_cons_limited, 1E-15), 1.0) * 100.0
        self.all_streams_demand_ratio = demand_ratio_df

        # COmpute ratio_objective
        self.compute_ratio_objective()

    def compute_ratio_objective(self):

        ratio_arrays = self.all_streams_demand_ratio[self.inputs["stream_list"]]
        # Objective is to minimize the difference between 100 and all ratios
        # We give as objective the highest difference to start with the max of
        # the difference

        smooth_max = smooth_maximum(100.0 - ratio_arrays.flatten(), 3)
        self.ratio_objective = np.asarray(
            [smooth_max / self.inputs['ratio_ref']])

    def compute_target_production_constraint(self):
        """should be negative"""
        target_production_constraint_ref = self.inputs[GlossaryEnergy.TargetProductionConstraintRefValue]
        target_energy_production = self.inputs[GlossaryEnergy.TargetEnergyProductionValue][GlossaryEnergy.TargetEnergyProductionValue]
        actual_production_twh = self.production[GlossaryEnergy.TotalProductionValue]
        missing_production = target_energy_production - actual_production_twh
        self.target_production_constraint = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.TargetProductionConstraintValue: missing_production / target_production_constraint_ref
        })

    def compute(self):
        self.configure_parameters_update()

        self.compute_raw_production()
        self.compute_energy_consumptions_by_energy_sector()
        self.compute_energy_consumptions_by_ccus_sector()
        self.compute_all_energy_consumptions()

        self.compute_net_consumable_energy()
        self.compute_net_energy_production()


        self.compute_energy_production_uncut()
        self.compute_price_by_energy()
        self.compute_CO2_emissions()
        self.compute_CO2_emissions_ratio()
        self.aggregate_land_use_required()
        self.compute_energy_capital()
        self.compute_non_use_capital_mean_by_stream()
        self.compute_non_use_energy_capital_constraint()
        self.compute_non_use_energy_capital_objective()
        self.compute_total_prod_minus_min_prod_constraint()
        self.compute_constraint_solid_fuel_elec()
        self.compute_constraint_h2()
        self.compute_syngas_prod_objective()
        self.compute_syngas_prod_constraint()

        self.compute_all_streams_demand_ratio()
        self.compute_net_positive_consumable_energy_production()
        self.compute_mean_price()
        self.compute_energy_mean_price_objective()

        self.compute_constraint_h2()

        self.compute_target_production_constraint()

    def compute_energy_mean_price_objective(self):
        self.energy_mean_price_objective = np.array([
            self.energy_mean_price[GlossaryEnergy.EnergyPriceValue].mean() / self.inputs[GlossaryEnergy.EnergyMeanPriceObjectiveRefValue]])

    def compute_non_use_energy_capital_constraint(self):
        """
        Non use capital <= 5%(tolerance) Capital <=> non use capital / capital - .05 <= 0.

        <=> (non use capital / capital - tol) / ref <= 0
        ref = 0.30 means after 35 % of capital not used the constraint will explode

        It is not a problem if in the early years, there is a loss of capital, it may be necessary to drift away from current energy mix system,
        so we increase constraint strenght with time, from 0 % at year start to 100% at year end, just like x^2 between 0 and 1
        We add also a period tolerance, so
        """
        ratio_non_use_capital = self.energy_capital[GlossaryEnergy.NonUseCapital] / self.energy_capital[GlossaryEnergy.Capital]
        period_tolerance = np.linspace(0, 1, len(self.years)) ** self.inputs['period_tol_power_non_use_capital_constraint']
        constraint = (ratio_non_use_capital - self.inputs['tol_constraint_non_use_capital_energy']) / self.inputs['ref_constraint_non_use_capital_energy'] * period_tolerance

        self.non_use_capital_constraint_df = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.ConstraintEnergyNonUseCapital: constraint
        })

    def compute_non_use_energy_capital_objective(self):
        """to minimize"""
        ratio_non_use_capital = self.energy_capital[GlossaryEnergy.NonUseCapital] / self.energy_capital[GlossaryEnergy.Capital]
        self.non_use_capital_obj = np.array([ratio_non_use_capital.mean()])

    def aggregate_land_use_required(self):
        """Aggregate into an unique dataframe of information of sub technology about land use required"""

        for stream in self.inputs["stream_list"]:
            df_name = f'{stream}.{GlossaryEnergy.LandUseRequiredValue}'
            stream_land_use_df_cols = self.get_colnames_input_dataframe(df_name=df_name, expect_years=True)
            for col in stream_land_use_df_cols:
                self.outputs[f"land_demand_df:{col}"] = self.inputs[f"{df_name}:{col}"]

    def compute_all_consumptions_wo_ratios(self):
        pass

    def compute_all_energy_consumptions(self):
        pass

    def compute_energy_consumptions_by_energy_sector(self):
        pass

    def compute_energy_consumptions_by_ccus_sector(self):
        pass
