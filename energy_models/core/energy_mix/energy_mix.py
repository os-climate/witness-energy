'''
Copyright 2022 Airbus SAS
Modifications on 2023/05/31-2023/11/03 Copyright 2023 Capgemini

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
import re

import numpy as np
import pandas as pd

from climateeconomics.glossarycore import GlossaryCore
from climateeconomics.sos_wrapping.sos_wrapping_agriculture.agriculture.agriculture_mix_disc import \
    AgricultureMixDiscipline
from energy_models.core.stream_type.base_stream import BaseStream
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.core.stream_type.carbon_models.carbon_storage import CarbonStorage
from energy_models.core.stream_type.energy_models.biodiesel import BioDiesel
from energy_models.core.stream_type.energy_models.ethanol import Ethanol
from energy_models.core.stream_type.energy_models.biogas import BioGas
from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import GaseousHydrogen
from energy_models.core.stream_type.energy_models.liquid_fuel import LiquidFuel
from energy_models.core.stream_type.energy_models.hydrotreated_oil_fuel import HydrotreatedOilFuel
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.energy_models.solid_fuel import SolidFuel
from energy_models.core.stream_type.energy_models.liquid_hydrogen import LiquidHydrogen
from energy_models.core.stream_type.energy_models.syngas import Syngas, \
    compute_calorific_value
from energy_models.core.stream_type.carbon_models.carbon import Carbon
from energy_models.core.stream_type.energy_models.renewable import Renewable
from energy_models.core.stream_type.energy_models.fossil import Fossil
from energy_models.core.stream_type.energy_models.heat import lowtemperatureheat
from energy_models.core.stream_type.energy_models.heat import mediumtemperatureheat
from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from copy import deepcopy

from energy_models.glossaryenergy import GlossaryEnergy
from sostrades_core.tools.base_functions.exp_min import compute_func_with_exp_min
from sostrades_core.tools.cst_manager.func_manager_common import smooth_maximum
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary


class EnergyMix(BaseStream):
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
    CARBON_STORAGE_CONSTRAINT = 'carbon_storage_constraint'
    energy_class_dict = {GaseousHydrogen.name: GaseousHydrogen,
                         LiquidFuel.name: LiquidFuel,
                         HydrotreatedOilFuel.name: HydrotreatedOilFuel,
                         Electricity.name: Electricity,
                         Methane.name: Methane,
                         BioGas.name: BioGas,
                         BioDiesel.name: BioDiesel,
                         Ethanol.name: Ethanol,
                         SolidFuel.name: SolidFuel,
                         Syngas.name: Syngas,
                         BiomassDry.name: BiomassDry,
                         LiquidHydrogen.name: LiquidHydrogen,
                         Renewable.name: Renewable,
                         Fossil.name: Fossil,
                         lowtemperatureheat.name: lowtemperatureheat,
                         mediumtemperatureheat.name: mediumtemperatureheat,
                         hightemperatureheat.name: hightemperatureheat
                         }

    # For simplified energy mix , raw_to_net factor is used to compute net
    # production from raw production
    raw_tonet_dict = {Renewable.name: Renewable.raw_to_net_production,
                      Fossil.name: Fossil.raw_to_net_production}

    only_energy_list = list(energy_class_dict.keys())

    stream_class_dict = {CarbonCapture.name: CarbonCapture,
                         CarbonStorage.name: CarbonStorage, }
    ccs_list = list(stream_class_dict.keys())
    stream_class_dict.update(energy_class_dict)

    energy_list = list(stream_class_dict.keys())
    resource_list = RESOURCE_LIST
    CO2_list = [f'{CarbonCapture.name} (Mt)',
                f'{CarbonCapture.flue_gas_name} (Mt)',
                f'{CarbonStorage.name} (Mt)',
                f'{CO2.name} (Mt)',
                f'{Carbon.name} (Mt)']
    solidFuel_name = SolidFuel.name
    electricity_name = Electricity.name
    gaseousHydrogen_name = GaseousHydrogen.name
    liquidHydrogen_name = LiquidHydrogen.name
    biomass_name = BiomassDry.name
    syngas_name = Syngas.name
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
        super(EnergyMix, self).__init__(name)

        self.total_co2_emissions = None
        self.total_co2_emissions_Gt = None
        self.co2_for_food = None
        self.losses_percentage_dict = {}
        self.inputs = {}

    def configure(self, inputs_dict):
        '''
        Configure method 
        '''
        self.configure_parameters(inputs_dict)
        self.configure_parameters_update(inputs_dict)

    def configure_parameters(self, inputs_dict):
        '''
        COnfigure parameters (variables that does not change during the run
        '''
        self.subelements_list = inputs_dict[GlossaryCore.energy_list]
        BaseStream.configure_parameters(self, inputs_dict)

        # Specific configure for energy mix
        self.co2_emitted_by_energy = {}
        self.CCS_price = pd.DataFrame(
            {GlossaryCore.Years: np.arange(inputs_dict[GlossaryCore.YearStart], inputs_dict[GlossaryCore.YearEnd] + 1)})
        self.CO2_tax_minus_CCS_constraint = pd.DataFrame(
            {GlossaryCore.Years: np.arange(inputs_dict[GlossaryCore.YearStart], inputs_dict[GlossaryCore.YearEnd] + 1)})
        self.total_prod_minus_min_prod_constraint_df = pd.DataFrame(
            {GlossaryCore.Years: np.arange(inputs_dict[GlossaryCore.YearStart], inputs_dict[GlossaryCore.YearEnd] + 1)})
        self.minimum_energy_production = inputs_dict['minimum_energy_production']
        self.production_threshold = inputs_dict['production_threshold']
        self.scaling_factor_energy_production = inputs_dict['scaling_factor_energy_production']
        self.scaling_factor_energy_consumption = inputs_dict['scaling_factor_energy_consumption']
        self.solid_fuel_elec_percentage = inputs_dict['solid_fuel_elec_percentage']
        self.solid_fuel_elec_constraint_ref = inputs_dict['solid_fuel_elec_constraint_ref']
        self.liquid_hydrogen_percentage = inputs_dict['liquid_hydrogen_percentage']
        self.liquid_hydrogen_constraint_ref = inputs_dict['liquid_hydrogen_constraint_ref']
        self.syngas_prod_ref = inputs_dict['syngas_prod_ref']
        self.syngas_prod_limit = inputs_dict['syngas_prod_constraint_limit']
        self.co2_for_food = pd.DataFrame(
            {GlossaryCore.Years: np.arange(inputs_dict[GlossaryCore.YearStart], inputs_dict[GlossaryCore.YearEnd] + 1),
             f'{CO2.name} for food (Mt)': 0.0})
        self.ratio_norm_value = inputs_dict['ratio_ref']

        self.heat_losses_percentage = inputs_dict['heat_losses_percentage']

        if self.subelements_list is not None:
            for energy in self.subelements_list:
                if f'{energy}.losses_percentage' in inputs_dict:
                    self.losses_percentage_dict[energy] = inputs_dict[f'{energy}.losses_percentage']

    def configure_parameters_update(self, inputs_dict):
        '''
        Configure parameters with possible update (variables that does change during the run)
        '''
        self.inputs = inputs_dict
        self.scaling_factor_energy_production = inputs_dict['scaling_factor_energy_production']
        self.scaling_factor_energy_consumption = inputs_dict['scaling_factor_energy_consumption']
        self.carbon_tax = inputs_dict[GlossaryCore.CO2TaxesValue]
        self.subelements_list = inputs_dict[GlossaryCore.energy_list] + \
                                inputs_dict[GlossaryCore.ccs_list]
        self.energy_list = inputs_dict[GlossaryCore.energy_list]
        self.total_prod_minus_min_prod_constraint_ref = inputs_dict[
            'total_prod_minus_min_prod_constraint_ref']
        # Specific configure for energy mix
        self.co2_emitted_by_energy = {}

        for energy in self.subelements_list:
            self.sub_prices[energy] = inputs_dict[f'{energy}.{GlossaryCore.EnergyPricesValue}'][energy]
            self.sub_production_dict[energy] = inputs_dict[f'{energy}.{GlossaryCore.EnergyProductionValue}'] * \
                                               self.scaling_factor_energy_production
            self.sub_consumption_dict[energy] = inputs_dict[f'{energy}.{GlossaryCore.EnergyConsumptionValue}'] * \
                                                self.scaling_factor_energy_consumption
            self.sub_consumption_woratio_dict[energy] = inputs_dict[f'{energy}.{GlossaryCore.EnergyConsumptionWithoutRatioValue}'] * \
                                                        self.scaling_factor_energy_consumption
            self.sub_land_use_required_dict[energy] = inputs_dict[f'{energy}.{GlossaryCore.LandUseRequiredValue}']

            if energy in self.energy_class_dict:
                self.sub_carbon_emissions[energy] = inputs_dict[f'{energy}.{GlossaryCore.CO2EmissionsValue}'][energy]
                self.co2_emitted_by_energy[energy] = inputs_dict[f'{energy}.CO2_per_use']

        self.co2_emissions = self.sub_carbon_emissions.copy(deep=True)
        self.energy_prices = self.sub_prices.copy(deep=True)
        self.price_by_energy = pd.DataFrame(
            {GlossaryCore.Years: self.energy_prices[GlossaryCore.Years].values})

        # dataframe resource demand
        self.resources_demand = pd.DataFrame(
            {GlossaryCore.Years: self.energy_prices[GlossaryCore.Years].values})
        self.resources_demand_woratio = pd.DataFrame(
            {GlossaryCore.Years: self.energy_prices[GlossaryCore.Years].values})
        for elements in self.resource_list:
            if elements in self.resource_list:
                self.resources_demand[elements] = np.linspace(
                    0, 0, len(self.resources_demand.index)) * 100.
                self.resources_demand_woratio[elements] = np.linspace(
                    0, 0, len(self.resources_demand.index)) * 100.
        for energy in self.subelements_list:
            for resource in self.resource_list:
                if f'{resource} ({self.RESOURCE_CONSUMPTION_UNIT})' in self.sub_consumption_dict[energy].columns:
                    self.resources_demand[resource] = self.resources_demand[resource] + \
                                                      inputs_dict[f'{energy}.{GlossaryCore.EnergyConsumptionValue}'][
                                                          f'{resource} ({self.RESOURCE_CONSUMPTION_UNIT})'].values * \
                                                      self.scaling_factor_energy_consumption
                    self.resources_demand_woratio[resource] = self.resources_demand_woratio[resource] + \
                                                              inputs_dict[f'{energy}.{GlossaryCore.EnergyConsumptionWithoutRatioValue}'][
                                                                  f'{resource} ({self.RESOURCE_CONSUMPTION_UNIT})'].values * \
                                                              self.scaling_factor_energy_consumption

        # DataFrame stream demand
        self.all_streams_demand_ratio = pd.DataFrame(
            {GlossaryCore.Years: self.energy_prices[GlossaryCore.Years].values})
        for energy in self.subelements_list:
            self.all_streams_demand_ratio[energy] = np.ones(
                len(self.all_streams_demand_ratio[GlossaryCore.Years].values)) * 100.

    def set_energy_prices_in(self, energy_prices):
        '''
        Setter method
        '''
        self.energy_prices_in = energy_prices

    def set_co2_emissions_in(self, co2_emissions):
        '''
        Setter method
        '''
        self.co2_emissions_in = co2_emissions

    def compute_energy_capital(self):
        """sum of positive energy production --> raw total production"""

        energy_type_capitals = []
        for energy in self.energy_list:
            energy_ = energy
            if energy == BiomassDry.name:
                energy_ = AgricultureMixDiscipline.name
            energy_type_capitals.append(self.inputs[f"{energy_}.{GlossaryEnergy.EnergyTypeCapitalDfValue}"][GlossaryCore.Capital].values)

        for ccs in self.inputs[GlossaryCore.ccs_list]:
            energy_type_capitals.append(
                self.inputs[f"{ccs}.{GlossaryEnergy.EnergyTypeCapitalDfValue}"][GlossaryCore.Capital].values)

        energy_capital = np.sum(energy_type_capitals, axis=0) / 1e3

        self.energy_capital = pd.DataFrame({
            GlossaryCore.Years: self.years,
            GlossaryCore.Capital: energy_capital
        })

    def compute_raw_production(self):
        """sum of positive energy production --> raw total production"""

        for energy in self.subelements_list:
            column_name = f'{self.PRODUCTION} {energy} ({self.stream_class_dict[energy].unit})'
            self.production_raw[column_name] = pd.Series(
                self.sub_production_dict[energy][energy].values)

        columns_to_sum = [column for column in self.production_raw if column.endswith('(TWh)')]
        self.production_raw[GlossaryCore.TotalProductionValue] = self.production_raw[columns_to_sum].sum(axis=1)

    def compute_net_consumable_energy(self):
        """consumable energy = Raw energy production - Energy consumed for energy production"""

        # for energy in self.subelements_list:
        #     column_name = f'{self.PRODUCTION} {energy} ({self.stream_class_dict[energy].unit})'
        #     self.production[column_name] = pd.Series(
        #         self.sub_production_dict[energy][energy].values)
        #     self.production_raw[column_name] = pd.Series(
        #         self.sub_production_dict[energy][energy].values)
        #     for idx, consu in self.sub_consumption_dict.items():
        #         if f'{energy} ({self.stream_class_dict[energy].unit})' in consu.columns:
        #             self.production[column_name] -= consu[
        #                 f'{energy} ({self.stream_class_dict[energy].unit})'].values
        #         else:
        #             wrong_columns = [
        #                 column for column in consu.columns if energy in column]
        #             if len(wrong_columns) != 0:
        #                 logging.warning(
        #                     f'The columns {wrong_columns} in the energy_consumption out of {idx} cannot be taken into account for an error of unity')

        self.consumable_energy_df = pd.DataFrame({GlossaryCore.Years: self.years})
        self.consumed_energy_by_ccus_sum = {}
        for energy in self.energy_list:
            # starting from raw energy production
            column_name_energy = f'{self.PRODUCTION} {energy} ({self.stream_class_dict[energy].unit})'
            raw_production_energy = self.production_raw[column_name_energy]

            # removing consumed energy
            consumed_energy_by_energy_list = []
            consumed_energy_by_ccus_list = []
            column_name_consumption = f'{energy} ({self.stream_class_dict[energy].unit})'
            for energy_other, consu in self.sub_consumption_dict.items():
                if column_name_consumption in consu.columns:
                    if energy_other in self.energy_list:
                        consumed_energy_by_energy_list.append(consu[column_name_consumption].values)
                    else:
                        consumed_energy_by_ccus_list.append(consu[column_name_consumption].values)
            consumed_energy_by_energy_sum = np.sum(np.array(consumed_energy_by_energy_list), axis=0) if len(
                consumed_energy_by_energy_list) else 0.
            self.consumed_energy_by_ccus_sum[energy] = np.sum(np.array(consumed_energy_by_ccus_list), axis=0) if len(
                consumed_energy_by_ccus_list) else 0.
            # obtaining net energy production for the techno
            column_name = f'{self.PRODUCTION} {energy} ({self.stream_class_dict[energy].unit})'
            prod_raw_to_substract = self.compute_net_prod_of_coarse_energies(energy, column_name)
            self.consumable_energy_df[
                column_name_energy] = raw_production_energy - consumed_energy_by_energy_sum - prod_raw_to_substract

        columns_to_sum = [column for column in self.consumable_energy_df if column.endswith('(TWh)')]
        self.consumable_energy_df[GlossaryCore.TotalProductionValue] = self.consumable_energy_df[columns_to_sum].sum(
            axis=1)

        # substract a percentage of raw production into net production
        self.consumable_energy_df[GlossaryCore.TotalProductionValue] -= self.production_raw[
                                                                            GlossaryCore.TotalProductionValue] * \
                                                                        self.heat_losses_percentage / 100.0

    def compute_net_energy_production(self):
        """
        Net energy production = Raw energy production - Energy consumed for energy production - Energy used by CCUS
        """
        self.production = deepcopy(self.consumable_energy_df)
        # taking into account consumption of ccs technos
        for ccs in self.ccs_list:
            # production_column_name_ccs = f'{self.PRODUCTION} {ccs} (TWh)'
            # if ccs in self.sub_consumption_dict:
            #     consumption_ccs_df = self.sub_consumption_dict[ccs]
            #     ccs_consumptions_list = []
            #     for column in consumption_ccs_df.columns:
            #         if column.endswith('(TWh)'):
            #             ccs_consumptions_list.append(consumption_ccs_df[column].values)
            #     self.production[production_column_name_ccs] = - np.sum(np.array(ccs_consumptions_list), axis=0) if len(
            #         ccs_consumptions_list) else 0.

            production_column_name_ccs = f'{self.PRODUCTION} {ccs} (Mt)'
            if ccs in self.sub_consumption_dict:
                consumption_ccs_df = self.sub_consumption_dict[ccs]
                ccs_consumptions_list = []
                for column in consumption_ccs_df.columns:
                    if column.endswith('(Mt)'):
                        ccs_consumptions_list.append(consumption_ccs_df[column].values)
                self.production[production_column_name_ccs] = - np.sum(np.array(ccs_consumptions_list), axis=0) if len(
                    ccs_consumptions_list) else 0.
        # Delete energy used by ccs from energy production (and not only from total production)
        for energy in self.energy_list:
            production_column_name_energy = f'{self.PRODUCTION} {energy} (TWh)'
            self.production[production_column_name_energy] -= self.consumed_energy_by_ccus_sum[energy]

        # Net energy production = Raw energy production - Energy consumed for energy production - Energy used by CCUS
        columns_to_sum = [column for column in self.production if column.endswith('(TWh)')]
        self.production[GlossaryCore.TotalProductionValue] = self.production[columns_to_sum].sum(axis=1)

        self.production[GlossaryCore.TotalProductionValue] -= self.production_raw[
                                                                  GlossaryCore.TotalProductionValue] * \
                                                              self.heat_losses_percentage / 100.0

    def compute_energy_production_uncut(self):
        """maybe to delete"""
        self.production['Total production (uncut)'] = self.production[GlossaryCore.TotalProductionValue].values
        min_energy = self.minimum_energy_production
        for year in self.production.index:
            if self.production.at[year, GlossaryCore.TotalProductionValue] < min_energy:
                # To avoid underflow : exp(-200) is considered to be the
                # minimum value for the exp
                production_year = max(
                    self.production.at[year, GlossaryCore.TotalProductionValue], -200.0 * min_energy)
                self.production.loc[year, GlossaryCore.TotalProductionValue] = min_energy / 10. * \
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
            return self.production_raw[column_name].values * \
                (1.0 - self.raw_tonet_dict[energy])
        except KeyError:
            return 0.

    def compute_price_by_energy(self):
        '''
        Compute the price of each energy.
        Energy price (techno, year) = Raw energy price (techno, year) + CO2 emitted(techno, year) * carbon tax ($/tEqCO2)
        after carbon tax with all technology prices and technology weights computed with energy production
        '''

        for energy in self.subelements_list:
            if energy in self.energy_class_dict:
                self.price_by_energy[energy] = self.sub_prices[energy].values + \
                                               self.co2_emitted_by_energy[energy]['CO2_per_use'].values * \
                                               self.carbon_tax[GlossaryCore.CO2Tax].values

    def compute_CO2_emissions_ratio(self):
        '''
        Compute the CO2 emission_ratio in kgCO2/kWh for the MDA
        '''
        self.carbon_emissions_after_use = pd.DataFrame(
            {GlossaryCore.Years: self.total_carbon_emissions[GlossaryCore.Years].values})
        for energy in self.subelements_list:
            if energy in self.energy_class_dict:
                self.total_carbon_emissions[energy] = self.sub_carbon_emissions[energy]
                self.carbon_emissions_after_use[energy] = self.total_carbon_emissions[energy] + \
                                                          self.co2_emitted_by_energy[energy]['CO2_per_use']

    def compute_CO2_emissions(self):
        '''
        Compute CO2 total emissions
        '''
        # Initialize dataframes
        self.total_co2_emissions = pd.DataFrame(
            {GlossaryCore.Years: self.production[GlossaryCore.Years]})
        self.co2_production = pd.DataFrame({GlossaryCore.Years: self.production[GlossaryCore.Years]})
        self.co2_consumption = pd.DataFrame(
            {GlossaryCore.Years: self.production[GlossaryCore.Years]})
        self.emissions_by_energy = pd.DataFrame(
            {GlossaryCore.Years: self.production[GlossaryCore.Years]})
        # Do not loop over carbon capture and carbon storage which will be
        # handled differently

        for energy in self.subelements_list:
            self.emissions_by_energy[energy] = np.zeros_like(
                self.production[GlossaryCore.Years].values)
            if energy in self.only_energy_list:

                # gather all production columns with a CO2 name in it
                for col, production in self.sub_production_dict[energy].items():
                    if col in self.CO2_list:
                        self.co2_production[f'{energy} {col}'] = production.values
                        self.emissions_by_energy[
                            energy] += self.co2_production[f'{energy} {col}'].values
                # gather all consumption columns with a CO2 name in it
                for col, consumption in self.sub_consumption_dict[energy].items():
                    if col in self.CO2_list:
                        self.co2_consumption[f'{energy} {col}'] = consumption.values
                        self.emissions_by_energy[
                            energy] -= self.co2_consumption[f'{energy} {col}'].values
                # Compute the CO2 emitted during the use of the net energy
                # If net energy is negative, CO2 by use is equals to zero

                self.co2_production[f'{energy} CO2 by use (Mt)'] = self.co2_emitted_by_energy[energy][
                                                                       'CO2_per_use'] * np.maximum(
                    0.0, self.production[f'production {energy} ({self.energy_class_dict[energy].unit})'].values)
                self.emissions_by_energy[
                    energy] += self.co2_production[f'{energy} CO2 by use (Mt)'].values

        ''' CARBON CAPTURE needed by energy mix
        Total carbon capture needed by energy mix if a technology needs carbon_capture
         Ex :Sabatier process or RWGS in FischerTropsch technology 
        '''
        energy_needing_carbon_capture = self.co2_consumption[[
            col for col in self.co2_consumption if col.endswith(f'{CarbonCapture.name} (Mt)')]]
        energy_needing_carbon_capture_list = [key.replace(
            f' {CarbonCapture.name} (Mt)', '') for key in energy_needing_carbon_capture]
        if len(energy_needing_carbon_capture_list) != 0:
            self.total_co2_emissions[
                f'{CarbonCapture.name} needed by energy mix (Mt)'] = energy_needing_carbon_capture.sum(
                axis=1).values
        else:
            self.total_co2_emissions[
                f'{CarbonCapture.name} needed by energy mix (Mt)'] = 0.0

        # Put in Gt carbon capture needed by energy mix
        self.co2_emissions_needed_by_energy_mix = pd.DataFrame(
            {GlossaryCore.Years: self.production[GlossaryCore.Years],
             f'{CarbonCapture.name} needed by energy mix (Gt)': self.total_co2_emissions[
                                                                    f'{CarbonCapture.name} needed by energy mix (Mt)'].values / 1e3})

        ''' CARBON CAPTURE from energy mix
        Total carbon capture from energy mix if the technology offers carbon_capture
         Ex : upgrading biogas technology is the same as Amine Scrubbing but
         on a different gas (biogas for upgrading biogas and flue gas for
         Amien scrubbing)
        '''
        energy_producing_carbon_capture = self.co2_production[[
            col for col in self.co2_production if col.endswith(f'{CarbonCapture.name} (Mt)')]]
        energy_producing_carbon_capture_list = [key.replace(
            f' {CarbonCapture.name} (Mt)', '') for key in energy_producing_carbon_capture]
        if len(energy_producing_carbon_capture_list) != 0:
            self.total_co2_emissions[
                f'{CarbonCapture.name} from energy mix (Mt)'] = energy_producing_carbon_capture.sum(
                axis=1).values
        else:
            self.total_co2_emissions[
                f'{CarbonCapture.name} from energy mix (Mt)'] = 0.0

        # Put in Gt CO2 from energy mix nedded for ccus discipline
        self.carbon_capture_from_energy_mix = pd.DataFrame(
            {GlossaryCore.Years: self.production[GlossaryCore.Years],
             f'{CarbonCapture.name} from energy mix (Gt)': self.total_co2_emissions[
                                                               f'{CarbonCapture.name} from energy mix (Mt)'].values / 1e3})

    def compute_net_positive_consumable_energy_production(self) -> pd.DataFrame:
        """Takes the positive part of the net consumable energy production for each energy
        (without energy consumed by CCUS)"""
        net_positives_consumable_energy_productions = {}
        for energy in self.energy_list:
            column_name = f'production {energy} ({self.energy_class_dict[energy].unit})'
            net_positives_consumable_energy_productions[energy] = np.maximum(0.0,
                                                                             self.consumable_energy_df[column_name])

        total_net_positive_consumable_production = pd.DataFrame(net_positives_consumable_energy_productions).sum(axis=1)

        net_positive_consumable_energy_production = pd.DataFrame({GlossaryCore.Years: self.years,
                                                                  **net_positives_consumable_energy_productions,
                                                                  GlossaryCore.TotalProductionValue: total_net_positive_consumable_production})
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
            columns=[GlossaryCore.Years, GlossaryCore.EnergyPriceValue])
        energy_mean_price[GlossaryCore.Years] = self.production[GlossaryCore.Years]
        energy_mean_price[GlossaryCore.EnergyPriceValue] = 0.0

        element_dict = dict(zip(self.energy_list, self.energy_list))
        if exp_min:
            prod_element, prod_total_for_mix_weight = self.compute_prod_with_exp_min(
                self.net_positive_consumable_energy_production, element_dict, self.production_threshold)
        else:
            prod_element, prod_total_for_mix_weight = self.compute_prod_wcutoff(
                self.net_positive_consumable_energy_production, element_dict, self.production_threshold)

        for energy in self.energy_list:
            # compute mix weights for each energy
            mix_weight = prod_element[energy] / prod_total_for_mix_weight
            # If the element is negligible do not take into account this element
            # It is negligible if tol = 0.1%
            tol = 1e-3
            mix_weight[mix_weight < tol] = 0.0
            energy_mean_price[GlossaryCore.EnergyPriceValue] += self.price_by_energy[energy].values * \
                                                 mix_weight
            self.mix_weights[energy] = mix_weight

        # In case all the technologies are below the threshold assign a
        # placeholder price
        if not exp_min:
            for year in energy_mean_price[GlossaryCore.Years].values:
                if np.real(energy_mean_price.loc[energy_mean_price[GlossaryCore.Years] == year][
                               GlossaryCore.EnergyPriceValue].values) == 0.0:
                    year_energy_prices = self.price_by_energy[
                        self.energy_list].loc[energy_mean_price[GlossaryCore.Years] == year]
                    min_energy_price = min(
                        val for val in year_energy_prices.values[0] if val > 0.0)
                    min_energy_name = [
                        name for name in year_energy_prices.columns if
                        year_energy_prices[name].values == min_energy_price][0]
                    energy_mean_price.loc[energy_mean_price[GlossaryCore.Years] ==
                                          year, GlossaryCore.EnergyPriceValue] = min_energy_price
                    for energy in self.energy_list:
                        self.mix_weights.loc[self.mix_weights[GlossaryCore.Years] == year,
                        energy] = 1. if energy == min_energy_name else 0.0

        self.energy_mean_price = energy_mean_price
        return energy_mean_price

    def compute_total_prod_minus_min_prod_constraint(self):
        '''
        Compute constraint for total production. Calculated on production before exponential decrease towards the limit.
        Input: self.production['Total production (uncut)'], self.minimum_energy_production
        Output: total_prod_minus_min_prod_constraint_df
        '''

        self.total_prod_minus_min_prod_constraint_df[self.TOTAL_PROD_MINUS_MIN_PROD_CONSTRAINT] = (
                                                                                                          self.production[
                                                                                                              'Total production (uncut)'].values - self.minimum_energy_production) / self.total_prod_minus_min_prod_constraint_ref

    def compute_constraint_h2(self):
        self.constraint_liquid_hydrogen = pd.DataFrame(
            {GlossaryCore.Years: self.production[GlossaryCore.Years].values})
        self.constraint_liquid_hydrogen['constraint_liquid_hydrogen'] = 0.
        hydrogen_name_list = [
            self.gaseousHydrogen_name, self.liquidHydrogen_name]
        # compute total H2 production
        for energy in hydrogen_name_list:
            if f'{self.PRODUCTION} {energy} ({self.energy_class_dict[energy].unit})' in self.production.columns:
                self.constraint_liquid_hydrogen['constraint_liquid_hydrogen'] += self.production[
                    f'{self.PRODUCTION} {energy} ({self.energy_class_dict[energy].unit})'].values
        if f'{self.PRODUCTION} {self.liquidHydrogen_name} ({self.energy_class_dict[self.liquidHydrogen_name].unit})' in self.production.columns:
            self.constraint_liquid_hydrogen['constraint_liquid_hydrogen'] = - (
                    self.liquid_hydrogen_percentage * self.constraint_liquid_hydrogen[
                'constraint_liquid_hydrogen'].values -
                    self.production[
                        f'{self.PRODUCTION} {self.liquidHydrogen_name} ({self.energy_class_dict[self.liquidHydrogen_name].unit})'].values) / self.liquid_hydrogen_constraint_ref

    def compute_constraint_solid_fuel_elec(self):
        self.constraint_solid_fuel_elec = pd.DataFrame(
            {GlossaryCore.Years: self.production[GlossaryCore.Years].values})
        self.constraint_solid_fuel_elec['constraint_solid_fuel_elec'] = 0.

        for energy in self.energy_constraint_list:
            if f'{self.PRODUCTION} {energy} ({self.energy_class_dict[energy].unit})' in self.production.columns:
                self.constraint_solid_fuel_elec['constraint_solid_fuel_elec'] += self.production[
                    f'{self.PRODUCTION} {energy} ({self.energy_class_dict[energy].unit})'].values
        self.constraint_solid_fuel_elec['constraint_solid_fuel_elec'] = - (self.constraint_solid_fuel_elec[
                                                                               'constraint_solid_fuel_elec'].values - self.solid_fuel_elec_percentage *
                                                                           self.production[
                                                                               GlossaryCore.TotalProductionValue].values) / self.solid_fuel_elec_constraint_ref

    def compute_syngas_prod_objective(self):
        '''
        Compute Syngas production objective
        '''
        if f'{self.PRODUCTION} {self.syngas_name} ({self.energy_class_dict[self.syngas_name].unit})' in self.production:
            self.syngas_prod_objective = np.sign(self.production[
                                                     f'{self.PRODUCTION} {self.syngas_name} ({self.energy_class_dict[self.syngas_name].unit})'].values) * \
                                         self.production[
                                             f'{self.PRODUCTION} {self.syngas_name} ({self.energy_class_dict[self.syngas_name].unit})'].values / \
                                         self.syngas_prod_ref
        else:
            self.syngas_prod_objective = np.zeros(len(self.years))

    def compute_syngas_prod_constraint(self):
        '''
        Compute Syngas production objective
        '''
        if f'{self.PRODUCTION} {self.syngas_name} ({self.energy_class_dict[self.syngas_name].unit})' in self.production:
            self.syngas_prod_constraint = (self.syngas_prod_limit - self.production[
                f'{self.PRODUCTION} {self.syngas_name} ({self.energy_class_dict[self.syngas_name].unit})'].values) / \
                                          self.syngas_prod_ref
        else:
            self.syngas_prod_constraint = np.zeros(len(self.years))

    def compute_all_streams_demand_ratio(self):
        '''! Computes the demand_ratio dataframe. 
        The ratio is calculated using the production and consumption WITHOUT the ratio applied
        The value of the ratio is capped to 100.0
        '''
        demand_ratio_df = pd.DataFrame(
            {GlossaryCore.Years: self.years})

        for energy in self.subelements_list:

            # Prod with ratio
            energy_production = deepcopy(
                self.sub_production_dict[f'{energy}'][f'{energy}'].values)
            # consumption without ratio
            sub_cons = self.sub_consumption_woratio_dict

            energy_consumption = np.zeros(len(self.years))
            for idx, consu in sub_cons.items():
                if f'{energy} ({self.stream_class_dict[energy].unit})' in consu.columns:
                    energy_consumption = np.sum([energy_consumption, consu[
                        f'{energy} ({self.stream_class_dict[energy].unit})'].values], axis=0)
            # if energy is in raw_tonet_dict, add the consumption due to raw_to_net ratio to energy_consumption
            if energy in self.raw_tonet_dict.keys():
                column_name = f'{self.PRODUCTION} {energy} ({self.stream_class_dict[energy].unit})'
                prod_raw_to_substract = self.compute_net_prod_of_coarse_energies(energy, column_name)
                energy_production -= prod_raw_to_substract

            energy_prod_limited = compute_func_with_exp_min(
                energy_production, 1.0e-10)
            energy_cons_limited = compute_func_with_exp_min(
                energy_consumption, 1.0e-10)

            demand_ratio_df[f'{energy}'] = np.minimum(
                np.maximum(energy_prod_limited / energy_cons_limited, 1E-15), 1.0) * 100.0
        self.all_streams_demand_ratio = demand_ratio_df

        # COmpute ratio_objective
        self.compute_ratio_objective()

    def compute_ratio_objective(self):

        ratio_arrays = self.all_streams_demand_ratio[self.subelements_list].values
        # Objective is to minimize the difference between 100 and all ratios
        # We give as objective the highest difference to start with the max of
        # the difference

        smooth_max = smooth_maximum(100.0 - ratio_arrays.flatten(), 3)
        self.ratio_objective = np.asarray(
            [smooth_max / self.ratio_norm_value])

    def compute_grad_CO2_emissions(self):
        '''
        Compute CO2 total emissions
        '''
        # Initialize dataframes
        len_years = len(self.production[GlossaryCore.Years])

        co2_production = pd.DataFrame({GlossaryCore.Years: self.production[GlossaryCore.Years]})
        co2_consumption = pd.DataFrame(
            {GlossaryCore.Years: self.production[GlossaryCore.Years]})

        dtot_CO2_emissions = {}
        # Do not loop over carbon capture and carbon storage which will be
        # handled differently
        for energy in self.subelements_list:
            if energy in self.only_energy_list:

                # gather all production columns with a CO2 name in it
                for col, production in self.sub_production_dict[energy].items():
                    if col in self.CO2_list:
                        co2_production[f'{energy} {col}'] = production.values
                # gather all consumption columns with a CO2 name in it
                for col, consumption in self.sub_consumption_dict[energy].items():
                    if col in self.CO2_list:
                        co2_consumption[f'{energy} {col}'] = consumption.values

        #                 # Compute the CO2 emitted during the use of the net energy
        #                 # If net energy is negative, CO2 by use is equals to zero
        #                 net_prod = net_production[
        #                     f'production {energy} ({self.energy_class_dict[energy].unit})'].values
        #
        #                 dtot_CO2_emissions[f'Total CO2 by use (Mt) vs {energy}#co2_per_use'] = np.maximum(
        #                     0, net_prod)
        #
        #                 # Specific case when net prod is equal to zero
        #                 # if we increase the prod of an energy the net prod will react
        #                 # however if we decrease the cons it does nothing
        #                 net_prod_sign = net_prod.copy()
        #                 net_prod_sign[net_prod_sign == 0] = 1
        #                 dtot_CO2_emissions[f'Total CO2 by use (Mt) vs {energy}#prod'] = self.co2_per_use[energy]['CO2_per_use'].values * \
        #                     np.maximum(0, np.sign(net_prod_sign))
        #                 dtot_CO2_emissions[f'Total CO2 by use (Mt) vs {energy}#cons'] = - self.co2_per_use[energy]['CO2_per_use'].values * \
        #                     np.maximum(0, np.sign(net_prod))
        # #                         co2_production[f'{energy} CO2 by use (Mt)'] = self.stream_class_dict[energy].data_energy_dict['CO2_per_use'] / \
        # #                             high_calorific_value * np.maximum(
        # 0.0, self.production[f'production {energy}
        # ({self.energy_class_dict[energy].unit})'].values)

        ''' CARBON STORAGE 
         Total carbon storage is production of carbon storage
         Solid carbon is gaseous equivalent in the production for
         solidcarbonstorage technology
        '''
        if CarbonStorage.name in self.sub_production_dict:
            dtot_CO2_emissions[
                f'{CarbonStorage.name} (Mt) vs {CarbonStorage.name}#{CarbonStorage.name}#prod'] = np.ones(
                len_years)
        #             self.total_co2_emissions[f'{CarbonStorage.name} (Mt)'] = self.sub_production_dict[
        #                 CarbonStorage.name][CarbonStorage.name].values
        #         else:
        #             self.total_co2_emissions[f'{CarbonStorage.name} (Mt)'] = 0.0

        ''' CARBON CAPTURE from CC technos       
         Total carbon capture = carbon captured from carboncapture stream +
         carbon captured from energies (can be negative if FischerTropsch needs carbon
         captured)
        '''
        if CarbonCapture.name in self.sub_production_dict:
            dtot_CO2_emissions[
                f'{CarbonCapture.name} (Mt) from CC technos vs {CarbonCapture.name}#{CarbonCapture.name}#prod'] = np.ones(
                len_years)
        #             self.total_co2_emissions[f'{CarbonCapture.name} (Mt) from CC technos'] = self.sub_production_dict[
        #                 CarbonCapture.name][CarbonCapture.name].values
        #         else:
        #             self.total_co2_emissions[f'{CarbonCapture.name} (Mt) from CC technos'] = 0.0

        ''' CARBON CAPTURE from energy mix
        Total carbon capture from energy mix if the technology offers carbon_capture
         Ex : upgrading biogas technology is the same as Amine Scrubbing but
         on a different gas (biogas for upgrading biogas and flue gas for
         Amien scrubbing)
        '''
        energy_producing_carbon_capture = co2_production[[
            col for col in co2_production if col.endswith(f'{CarbonCapture.name} (Mt)')]]
        energy_producing_carbon_capture_list = [key.replace(
            f' {CarbonCapture.name} (Mt)', '') for key in energy_producing_carbon_capture]
        if len(energy_producing_carbon_capture_list) != 0:
            for energy1 in energy_producing_carbon_capture_list:
                dtot_CO2_emissions[
                    f'{CarbonCapture.name} from energy mix (Gt) vs {energy1}#{CarbonCapture.name} (Mt)#prod'] = np.ones(
                    len_years)
        #             self.total_co2_emissions[f'{CarbonCapture.name} from energy mix (Mt)'] = energy_producing_carbon_capture.sum(
        #                 axis=1).values
        #         else:
        #             self.total_co2_emissions[
        #                 f'{CarbonCapture.name} from energy mix (Mt)'] = 0.0

        ''' CARBON CAPTURE needed by energy mix
        Total carbon capture needed by energy mix if a technology needs carbon_capture
         Ex :Sabatier process or RWGS in FischerTropsch technology 
        '''
        energy_needing_carbon_capture = co2_consumption[[
            col for col in co2_consumption if col.endswith(f'{CarbonCapture.name} (Mt)')]]
        energy_needing_carbon_capture_list = [key.replace(
            f' {CarbonCapture.name} (Mt)', '') for key in energy_needing_carbon_capture]
        if len(energy_needing_carbon_capture_list) != 0:
            for energy1 in energy_needing_carbon_capture_list:
                dtot_CO2_emissions[
                    f'{CarbonCapture.name} needed by energy mix (Gt) vs {energy1}#{CarbonCapture.name} (Mt)#cons'] = np.ones(
                    len_years)
        #             self.total_co2_emissions[f'{CarbonCapture.name} needed by energy mix (Mt)'] = energy_needing_carbon_capture.sum(
        #                 axis=1).values
        #         else:
        #             self.total_co2_emissions[
        #                 f'{CarbonCapture.name} needed by energy mix (Mt)'] = 0.0

        ''' CO2 from energy mix       
         CO2 expelled by energy mix technologies during the process 
         i.e. for machinery or tractors 
        '''
        energy_producing_co2 = co2_production[[
            col for col in co2_production if col.endswith(f'{CO2.name} (Mt)')]]
        energy_producing_co2_list = [key.replace(
            f' {CO2.name} (Mt)', '') for key in energy_producing_co2]
        if len(energy_producing_co2_list) != 0:
            for energy1 in energy_producing_co2_list:
                dtot_CO2_emissions[
                    f'{CO2.name} from energy mix (Mt) vs {energy1}#{CO2.name} (Mt)#prod'] = np.ones(len_years)

        #             self.total_co2_emissions[f'{CO2.name} from energy mix (Mt)'] = energy_producing_co2.sum(
        #                 axis=1).values
        #         else:
        #             self.total_co2_emissions[
        #                 f'{CO2.name} from energy mix (Mt)'] = 0.0

        ''' CO2 removed by energy mix       
         CO2 removed by energy mix technologies during the process 
         i.e. biomass processes as managed wood or crop energy
        '''
        energy_removing_co2 = co2_consumption[[
            col for col in co2_consumption if col.endswith(f'{CO2.name} (Mt)')]]
        energy_removing_co2_list = [key.replace(
            f' {CO2.name} (Mt)', '') for key in energy_removing_co2]
        if len(energy_removing_co2_list) != 0:
            for energy1 in energy_removing_co2_list:
                dtot_CO2_emissions[
                    f'{CO2.name} removed by energy mix (Mt) vs {energy1}#{CO2.name} (Mt)#cons'] = np.ones(len_years)
        #             self.total_co2_emissions[f'{CO2.name} removed by energy mix (Mt)'] = energy_removing_co2.sum(
        #                 axis=1).values
        #         else:
        #             self.total_co2_emissions[
        #                 f'{CO2.name} removed energy mix (Mt)'] = 0.0

        ''' Total C02 from Flue gas
            sum of all production of flue gas 
            it could be equal to carbon capture from CC technos if enough investment but not sure
        '''
        #         self.total_co2_emissions[f'Total {CarbonCapture.flue_gas_name} (Mt)'] = self.co2_production[[
        # col for col in self.co2_production if
        # col.endswith(f'{CarbonCapture.flue_gas_name} (Mt)')]].sum(axis=1)
        for col in co2_production:
            if col.endswith(f'{CarbonCapture.flue_gas_name} (Mt)'):
                energy1 = col.replace(
                    f' {CarbonCapture.flue_gas_name} (Mt)', '')
                dtot_CO2_emissions[
                    f'Total {CarbonCapture.flue_gas_name} (Mt) vs {energy1}#{CarbonCapture.flue_gas_name} (Mt)#prod'] = np.ones(
                    len_years)
        ''' Carbon captured that needs to be stored
            sum of the one from CC technos and the one directly captured 
            we delete the one needed by energy mix and potentially later the CO2 for food
        '''

        #         self.total_co2_emissions[f'{CarbonCapture.name} to be stored (Mt)'] = self.total_co2_emissions[f'{CarbonCapture.name} (Mt) from CC technos'] + \
        #             self.total_co2_emissions[f'{CarbonCapture.name} from energy mix (Mt)'] - \
        #             self.total_co2_emissions[f'{CarbonCapture.name} needed by energy mix (Mt)'] -\
        #             self.total_co2_emissions[f'{CO2.name} for food (Mt)'

        new_key = f'{CarbonCapture.name} to be stored (Mt)'
        key_dep_tuple_list = [(f'{CarbonCapture.name} (Mt) from CC technos', 1.0),
                              (f'{CarbonCapture.name} from energy mix (Mt)', 1.0),
                              (f'{CarbonCapture.name} needed by energy mix (Mt)', -1.0)]
        dtot_CO2_emissions = update_new_gradient(
            dtot_CO2_emissions, key_dep_tuple_list, new_key)

        return dtot_CO2_emissions

    def compute(self, inputs: dict, exp_min=True):
        self.configure_parameters_update(inputs)

        self.compute_raw_production()
        self.compute_net_consumable_energy()
        self.compute_net_energy_production()
        self.compute_energy_production_uncut()
        self.compute_price_by_energy()
        self.compute_CO2_emissions()
        self.compute_CO2_emissions_ratio()
        self.aggregate_land_use_required()
        self.compute_energy_capital()
        self.compute_total_prod_minus_min_prod_constraint()
        self.compute_constraint_solid_fuel_elec()
        self.compute_constraint_h2()
        self.compute_syngas_prod_objective()
        self.compute_syngas_prod_constraint()

        self.compute_all_streams_demand_ratio()
        self.compute_net_positive_consumable_energy_production()
        self.compute_mean_price(exp_min=inputs['exp_min'])
        self.compute_constraint_h2()


def update_new_gradient(grad_dict, key_dep_tuple_list, new_key):
    '''
        Update new gradient which are dependent of old ones by simple sum or difference
    '''
    new_grad_dict = grad_dict.copy()
    for key in grad_dict:
        for old_key, factor in key_dep_tuple_list:
            if key.startswith(old_key):
                # the grad of old key is equivalent to the new key because its
                # a sum
                new_grad_key = key.replace(old_key, new_key)
                if new_grad_key in new_grad_dict:
                    new_grad_dict[new_grad_key] = new_grad_dict[new_grad_key] + \
                                                  grad_dict[key] * factor
                else:
                    new_grad_dict[new_grad_key] = grad_dict[key] * factor

    return new_grad_dict
