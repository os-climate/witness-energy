'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2024/06/24 Copyright 2023 Capgemini

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
import pandas as pd
from climateeconomics.core.core_emissions.ghg_emissions_model import GHGEmissions
from climateeconomics.glossarycore import GlossaryCore
from climateeconomics.sos_wrapping.sos_wrapping_agriculture.agriculture.agriculture_mix_disc import (
    AgricultureMixDiscipline,
)

from energy_models.core.stream_type.base_stream import BaseStream
from energy_models.core.stream_type.carbon_models.carbon import Carbon
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.glossaryenergy import GlossaryEnergy


class EnergyGHGEmissions(BaseStream):
    """
    Class EnergyGHGEmissions:
    Takes as inputs the total production and the GHG emissions per energy out of EnergyMix
    and calculate the total GHG emissions of the energy consumption
    """
    name = 'EnergyGHGEmissions'
    ghg_input_unit = '(Mt)'
    ghg_output_unit = '(Gt)'
    CO2_list = [f'{GlossaryEnergy.carbon_capture} {ghg_input_unit}',
                f'{CarbonCapture.flue_gas_name} {ghg_input_unit}',
                f'{GlossaryEnergy.carbon_storage} {ghg_input_unit}',
                f'{CO2.name} {ghg_input_unit}',
                f'{Carbon.name} {ghg_input_unit}']

    GHG_TYPE_LIST = GHGEmissions.GHG_TYPE_LIST

    def __init__(self, name):
        super().__init__(name)
        self.energy_list = None
        self.scaling_factor_energy_production = None
        self.scaling_factor_energy_consumption = None
        self.years = None
        self.gwp_20 = None
        self.gwp_100 = None
        self.energy_list = None
        self.ccs_list = None
        self.ghg_per_use_dict = None
        self.energy_production_detailed = None
        self.co2_emissions_needed_by_energy_mix = None
        self.co2_emissions_ccus_Gt = None
        self.CO2_sources = None
        self.CO2_sinks = None
        self.ghg_production_dict = None
        self.CO2_consumption = None
        self.ghg_sources = None
        self.ghg_total_emissions = None
        self.gwp_emissions = None
        self.CO2_sources_Gt = None
        self.CO2_sinks_Gt = None

    def configure_parameters(self, inputs_dict):
        '''
        Configure parameters (variables that does not change during the run)
        '''
        self.energy_list = inputs_dict[GlossaryEnergy.energy_list]
        self.scaling_factor_energy_production = inputs_dict['scaling_factor_energy_production']
        self.scaling_factor_energy_consumption = inputs_dict['scaling_factor_energy_consumption']
        self.years = np.arange(
            inputs_dict[GlossaryEnergy.YearStart], inputs_dict[GlossaryEnergy.YearEnd] + 1)
        self.gwp_20 = inputs_dict['GHG_global_warming_potential20']
        self.gwp_100 = inputs_dict['GHG_global_warming_potential100']

    def configure_parameters_update(self, inputs_dict):
        '''
        Configure parameters with possible update (variables that does change during the run)
        '''

        self.energy_list = inputs_dict[GlossaryEnergy.energy_list]
        self.ccs_list = inputs_dict[GlossaryEnergy.ccs_list]

        self.ghg_per_use_dict = {ghg: pd.DataFrame(
            {GlossaryEnergy.Years: self.years}) for ghg in self.GHG_TYPE_LIST}
        self.sub_production_dict = {}
        self.sub_consumption_dict = {}

        for energy in self.energy_list:
            if energy == GlossaryEnergy.biomass_dry:

                for ghg in self.GHG_TYPE_LIST:
                    self.ghg_per_use_dict[ghg][energy] = inputs_dict[
                        f'{AgricultureMixDiscipline.name}.{ghg}_per_use'][f'{ghg}_per_use'].values

                self.sub_production_dict[energy] = inputs_dict[
                                                       f'{AgricultureMixDiscipline.name}.{GlossaryEnergy.EnergyProductionValue}'] * \
                                                   self.scaling_factor_energy_production
                self.sub_consumption_dict[energy] = inputs_dict[
                                                        f'{AgricultureMixDiscipline.name}.{GlossaryEnergy.EnergyConsumptionValue}'] * \
                                                    self.scaling_factor_energy_consumption
            else:
                for ghg in self.GHG_TYPE_LIST:
                    self.ghg_per_use_dict[ghg][energy] = inputs_dict[
                        f'{energy}.{ghg}_per_use'][f'{ghg}_per_use'].values

                self.sub_production_dict[energy] = inputs_dict[f'{energy}.{GlossaryEnergy.EnergyProductionValue}'] * \
                                                   self.scaling_factor_energy_production
                self.sub_consumption_dict[energy] = inputs_dict[f'{energy}.{GlossaryEnergy.EnergyConsumptionValue}'] * \
                                                    self.scaling_factor_energy_consumption

        for energy in self.ccs_list:
            self.sub_production_dict[energy] = inputs_dict[f'{energy}.{GlossaryEnergy.EnergyProductionValue}'] * \
                                               self.scaling_factor_energy_production

        self.energy_production_detailed = inputs_dict[GlossaryEnergy.EnergyProductionDetailedValue]

        self.co2_emissions_needed_by_energy_mix = inputs_dict['co2_emissions_needed_by_energy_mix']

        self.co2_emissions_ccus_Gt = inputs_dict['co2_emissions_ccus_Gt']

        self.init_dataframe_dict()

    def init_dataframe_dict(self):
        # Initialize dataframes
        self.CO2_sources = pd.DataFrame({GlossaryEnergy.Years: self.years})
        self.CO2_sinks = pd.DataFrame({GlossaryEnergy.Years: self.years})
        self.ghg_production_dict = {ghg: pd.DataFrame(
            {GlossaryEnergy.Years: self.years}) for ghg in self.GHG_TYPE_LIST}
        self.CO2_consumption = pd.DataFrame({GlossaryEnergy.Years: self.years})
        self.ghg_sources = pd.DataFrame({GlossaryEnergy.Years: self.years})
        self.ghg_total_emissions = pd.DataFrame({GlossaryEnergy.Years: self.years})
        self.gwp_emissions = pd.DataFrame({GlossaryEnergy.Years: self.years})

    def compute_ghg_emissions(self):
        '''
        Compute GHG total emissions
        '''

        # Aggregate CO2 production and consumption columns from sub_production
        # and sub_consumption df
        for energy in self.energy_list:
            self.aggregate_all_ghg_emissions_in_energy(energy)
            self.compute_ghg_emissions_by_use(energy)

        for ccs_name in self.ccs_list:
            self.aggregate_all_ghg_emissions_in_energy(ccs_name)

        self.sum_ghg_emissions_by_use()
        self.compute_other_co2_emissions()
        self.update_emissions_in_gt()
        self.compute_total_ghg_emissions()
        self.compute_gwp()

    def sum_ghg_emissions_by_use(self):
        '''Total CO2 by use 
        which is the sum of all CO2 emissions emitted by use of net energy production
        '''
        for ghg in self.GHG_TYPE_LIST:
            self.ghg_sources[f'Total {ghg} by use {self.ghg_input_unit}'] = self.ghg_production_dict[ghg][[
                col for col in self.ghg_production_dict[ghg] if
                col.endswith(f'{ghg} by use {self.ghg_input_unit}')]].sum(axis=1)

    def compute_other_co2_emissions(self):
        ''' CO2 from energy mix    
         CO2 expelled by energy mix technologies during the process 
         i.e. for machinery or tractors 
        '''
        energy_producing_co2 = self.ghg_production_dict[GlossaryEnergy.CO2][[
            col for col in self.ghg_production_dict[GlossaryEnergy.CO2] if col.endswith(f'{CO2.name} {self.ghg_input_unit}')]]
        energy_producing_co2_list = [key.replace(
            f' {CO2.name} {self.ghg_input_unit}', '') for key in energy_producing_co2]
        if len(energy_producing_co2_list) != 0:
            self.CO2_sources[f'{CO2.name} from energy mix {self.ghg_input_unit}'] = energy_producing_co2.sum(
                axis=1).values
        else:
            self.CO2_sources[
                f'{CO2.name} from energy mix {self.ghg_input_unit}'] = 0.0

        ''' CARBON CAPTURE from energy mix
        Total carbon capture from energy mix if the technology offers carbon_capture
         Ex : upgrading biogas technology is the same as Amine Scrubbing but
         on a different gas (biogas for upgrading biogas and flue gas for
         Amien scrubbing)
        '''
        energy_producing_carbon_capture = self.ghg_production_dict[GlossaryEnergy.CO2][[
            col for col in self.ghg_production_dict[GlossaryEnergy.CO2] if
            col.endswith(f'{GlossaryEnergy.carbon_capture} {self.ghg_input_unit}')]]
        energy_producing_carbon_capture_list = [key.replace(
            f' {GlossaryEnergy.carbon_capture} {self.ghg_input_unit}', '') for key in energy_producing_carbon_capture]
        if len(energy_producing_carbon_capture_list) != 0:
            self.CO2_sources[
                f'{GlossaryEnergy.carbon_capture} from energy mix {self.ghg_input_unit}'] = energy_producing_carbon_capture.sum(
                axis=1).values
        else:
            self.CO2_sources[
                f'{GlossaryEnergy.carbon_capture} from energy mix {self.ghg_input_unit}'] = 0.0

        ''' CO2 removed by energy mix
         CO2 removed by energy mix technologies during the process 
         i.e. biomass processes as managed wood or crop energy
        '''
        energy_removing_co2 = self.CO2_consumption[[
            col for col in self.CO2_consumption if col.endswith(f'{CO2.name} {self.ghg_input_unit}')]]
        energy_removing_co2_list = [key.replace(
            f' {CO2.name} {self.ghg_input_unit}', '') for key in energy_removing_co2]
        if len(energy_removing_co2_list) != 0:
            self.CO2_sinks[f'{CO2.name} removed by energy mix {self.ghg_input_unit}'] = energy_removing_co2.sum(
                axis=1).values
        else:
            self.CO2_sinks[
                f'{CO2.name} removed by energy mix {self.ghg_input_unit}'] = 0.0

        ''' Total C02 from Flue gas 
            sum of all production of flue gas
            it could be equal to carbon capture from CC technos if enough investment but not sure
        '''
        self.CO2_sources[f'Total {CarbonCapture.flue_gas_name} {self.ghg_input_unit}'] = \
        self.ghg_production_dict[GlossaryEnergy.CO2][[
            col for col in self.ghg_production_dict[GlossaryEnergy.CO2] if
            col.endswith(f'{CarbonCapture.flue_gas_name} {self.ghg_input_unit}')]].sum(axis=1)

    def update_emissions_in_gt(self):
        # update values to Gt
        self.CO2_sources_Gt = pd.DataFrame(
            {GlossaryEnergy.Years: self.CO2_sources[GlossaryEnergy.Years]})
        self.CO2_sinks_Gt = pd.DataFrame(
            {GlossaryEnergy.Years: self.CO2_sinks[GlossaryEnergy.Years]})

        for column_df in self.CO2_sources.columns:
            if column_df != GlossaryEnergy.Years:
                self.CO2_sources_Gt[column_df.replace(
                    '{self.ghg_input_unit}', '{self.ghg_output_unit}')] = self.CO2_sources[column_df] / 1e3

        for column_df in self.CO2_sinks.columns:
            if column_df != GlossaryEnergy.Years:
                self.CO2_sinks_Gt[column_df.replace(
                    '{self.ghg_input_unit}', '{self.ghg_output_unit}')] = self.CO2_sinks[column_df] / 1e3

        return self.CO2_sources_Gt, self.CO2_sinks_Gt

    def aggregate_all_ghg_emissions_in_energy(self, energy):

        if energy in self.sub_production_dict:
            # gather all production columns with a CO2 name in it
            for col, production in self.sub_production_dict[energy].items():
                if col in self.CO2_list:
                    self.ghg_production_dict[GlossaryEnergy.CO2][f'{energy} {col}'] = production.values
                else:
                    for ghg in self.GHG_TYPE_LIST:
                        if col == f'{ghg} {self.ghg_input_unit}':
                            self.ghg_production_dict[ghg][f'{energy} {col}'] = production.values
        # gather all consumption columns with a CO2 name in it
        # other green house gases are not consumed in energy mix for now
        if energy in self.sub_consumption_dict:
            for col, consumption in self.sub_consumption_dict[energy].items():
                if col in self.CO2_list:
                    self.CO2_consumption[f'{energy} {col}'] = consumption.values

    # , co2_emissions):

    def compute_ghg_emissions_by_use(self, energy):
        # Compute the CO2 emitted during the use of the net energy
        # If net energy is negative, CO2 by use is equals to zero
        for ghg in self.GHG_TYPE_LIST:
            if energy in self.ghg_per_use_dict[ghg]:
                self.ghg_production_dict[ghg][f'{energy} {ghg} by use {self.ghg_input_unit}'] = \
                self.ghg_per_use_dict[ghg][energy] * np.maximum(
                    0.0, self.energy_production_detailed[f'production {energy} ({GlossaryEnergy.energy_unit})'].values)

    def compute_total_ghg_emissions(self):
        """
        Compute total GHG emissions
        """

        # drop years column in new dataframe
        co2_sources_wo_years = self.CO2_sources_Gt.drop(
            GlossaryEnergy.Years, axis=1)

        # sum all co2 sources using the wo years dataframe
        sum_sources = co2_sources_wo_years.sum(axis=1).values

        # get unique column in serie format
        limited_by_capture_wo_years = self.co2_emissions_ccus_Gt.drop(
            GlossaryEnergy.Years, axis=1).iloc[:, 0].values
        needed_by_energy_mix_wo_years = self.co2_emissions_needed_by_energy_mix.drop(
            GlossaryEnergy.Years, axis=1).iloc[:, 0].values
        sinks_df = self.CO2_sinks_Gt.drop(
            GlossaryEnergy.Years, axis=1).iloc[:, 0].values

        sum_sinks = limited_by_capture_wo_years + \
                    needed_by_energy_mix_wo_years + sinks_df

        total_CO2_emissions = sum_sources + \
                              self.ghg_sources[f'Total CO2 by use {self.ghg_input_unit}'].values / \
                              1e3 - sum_sinks

        total_n2O_emissions = self.ghg_production_dict['N2O'].drop(
            GlossaryEnergy.Years, axis=1).sum(axis=1).values

        total_ch4_emissions = self.ghg_production_dict['CH4'].drop(
            GlossaryEnergy.Years, axis=1).sum(axis=1).values

        self.ghg_total_emissions['Total CO2 emissions'] = total_CO2_emissions
        self.ghg_total_emissions['Total N2O emissions'] = total_n2O_emissions / 1e3
        self.ghg_total_emissions['Total CH4 emissions'] = total_ch4_emissions / 1e3

    def compute_gwp(self):

        for ghg in self.GHG_TYPE_LIST:
            self.gwp_emissions[f'{ghg}_20'] = self.ghg_total_emissions[GlossaryCore.insertGHGTotalEmissions.format(ghg)] * self.gwp_20[ghg]
            self.gwp_emissions[f'{ghg}_100'] = self.ghg_total_emissions[GlossaryCore.insertGHGTotalEmissions.format(ghg)] * self.gwp_100[ghg]

    def compute_grad_total_co2_emissions(self, net_production):

        dtot_CO2_emissions = {}
        for energy in self.energy_list:
            net_prod = net_production[
                f'production {energy} ({GlossaryEnergy.energy_unit})'].values

            # Specific case when net prod is equal to zero
            # if we increase the prod of an energy the net prod will react
            # however if we decrease the cons it does nothing
            net_prod_sign = net_prod.copy()
            net_prod_sign[net_prod_sign == 0] = 1
            for ghg in self.GHG_TYPE_LIST:
                dtot_CO2_emissions[f'Total {ghg} emissions vs prod{energy}'] = self.ghg_per_use_dict[ghg][
                                                                                   energy].values * \
                                                                               np.maximum(0, np.sign(net_prod_sign))
        return dtot_CO2_emissions

    def compute_grad_CO2_emissions_sources(self, net_production):
        '''
        Compute CO2 total emissions
        '''
        # Initialize dataframes
        len_years = len(self.years)

        co2_production = pd.DataFrame({GlossaryEnergy.Years: self.years})
        co2_consumption = pd.DataFrame({GlossaryEnergy.Years: self.years})

        dtot_CO2_emissions = {}
        # Do not loop over carbon capture and carbon storage which will be
        # handled differently
        for energy in self.energy_list:

            # gather all production columns with a CO2 name in it
            for col, production in self.sub_production_dict[energy].items():
                if col in self.CO2_list:
                    co2_production[f'{energy} {col}'] = production.values
            # gather all consumption columns with a CO2 name in it
            for col, consumption in self.sub_consumption_dict[energy].items():
                if col in self.CO2_list:
                    co2_consumption[f'{energy} {col}'] = consumption.values

            # Compute the CO2 emitted during the use of the net energy
            # If net energy is negative, CO2 by use is equals to zero
            net_prod = net_production[
                f'production {energy} ({GlossaryEnergy.energy_unit})'].values

            dtot_CO2_emissions[f'Total CO2 by use (Gt) vs {energy}#co2_per_use'] = np.maximum(
                0, net_prod)

            # Specific case when net prod is equal to zero
            # if we increase the prod of an energy the net prod will react
            # however if we decrease the cons it does nothing
            net_prod_sign = net_prod.copy()
            net_prod_sign[net_prod_sign == 0] = 1
            for ghg in self.GHG_TYPE_LIST:
                dtot_CO2_emissions[f'Total {ghg} by use (Gt) vs {energy}#prod'] = self.ghg_per_use_dict[ghg][
                                                                                      energy].values * \
                                                                                  np.maximum(0, np.sign(net_prod_sign))

        for energy in self.ccs_list:
            for col, production in self.sub_production_dict[energy].items():
                if col in self.CO2_list:
                    co2_production[f'{energy} {col}'] = production.values
        ''' CARBON CAPTURE from energy mix
        Total carbon capture from energy mix if the technology offers carbon_capture
         Ex : upgrading biogas technology is the same as Amine Scrubbing but
         on a different gas (biogas for upgrading biogas and flue gas for
         Amine scrubbing)
        '''
        energy_producing_carbon_capture = co2_production[[
            col for col in co2_production if col.endswith(f'{GlossaryEnergy.carbon_capture} {self.ghg_input_unit}')]]
        energy_producing_carbon_capture_list = [key.replace(
            f' {GlossaryEnergy.carbon_capture} {self.ghg_input_unit}', '') for key in energy_producing_carbon_capture]
        if len(energy_producing_carbon_capture_list) != 0:
            for energy1 in energy_producing_carbon_capture_list:
                dtot_CO2_emissions[
                    f'{GlossaryEnergy.carbon_capture} from energy mix (Mt) vs {energy1}#{GlossaryEnergy.carbon_capture} {self.ghg_input_unit}#prod'] = np.ones(
                    len_years)
        #             self.total_co2_emissions[f'{GlossaryEnergy.carbon_capture} from energy mix {self.ghg_input_unit}'] = energy_producing_carbon_capture.sum(
        #                 axis=1).values
        #         else:
        #             self.total_co2_emissions[
        # f'{GlossaryEnergy.carbon_capture} from energy mix {self.ghg_input_unit}'] = 0.0

        ''' CO2 from energy mix       
         CO2 expelled by energy mix technologies during the process 
         i.e. for machinery or tractors 
        '''
        energy_producing_co2 = co2_production[[
            col for col in co2_production if col.endswith(f'{CO2.name} {self.ghg_input_unit}')]]
        energy_producing_co2_list = [key.replace(
            f' {CO2.name} {self.ghg_input_unit}', '') for key in energy_producing_co2]
        if len(energy_producing_co2_list) != 0:
            for energy1 in energy_producing_co2_list:
                dtot_CO2_emissions[
                    f'{CO2.name} from energy mix (Mt) vs {energy1}#{CO2.name} {self.ghg_input_unit}#prod'] = np.ones(
                    len_years)

        #             self.total_co2_emissions[f'{CO2.name} from energy mix {self.ghg_input_unit}'] = energy_producing_co2.sum(
        #                 axis=1).values
        #         else:
        #             self.total_co2_emissions[
        #                 f'{CO2.name} from energy mix {self.ghg_input_unit}'] = 0.0

        ''' CO2 removed by energy mix       
         CO2 removed by energy mix technologies during the process 
         i.e. biomass processes as managed wood or crop energy
        '''
        energy_removing_co2 = co2_consumption[[
            col for col in co2_consumption if col.endswith(f'{CO2.name} {self.ghg_input_unit}')]]
        energy_removing_co2_list = [key.replace(
            f' {CO2.name} {self.ghg_input_unit}', '') for key in energy_removing_co2]
        if len(energy_removing_co2_list) != 0:
            for energy1 in energy_removing_co2_list:
                dtot_CO2_emissions[
                    f'{CO2.name} removed by energy mix (Mt) vs {energy1}#{CO2.name} {self.ghg_input_unit}#cons'] = np.ones(
                    len_years)
        #             self.total_co2_emissions[f'{CO2.name} removed by energy mix {self.ghg_input_unit}'] = energy_removing_co2.sum(
        #                 axis=1).values
        #         else:
        #             self.total_co2_emissions[
        #                 f'{CO2.name} removed energy mix {self.ghg_input_unit}'] = 0.0

        ''' Total C02 from Flue gas
            sum of all production of flue gas 
            it could be equal to carbon capture from CC technos if enough investment but not sure
        '''
        #         self.total_co2_emissions[f'Total {CarbonCapture.flue_gas_name} {self.ghg_input_unit}'] = self.co2_production[[
        # col for col in self.co2_production if
        # col.endswith(f'{CarbonCapture.flue_gas_name}
        # {self.ghg_input_unit}')]].sum(axis=1)
        for col in co2_production:
            if col.endswith(f'{CarbonCapture.flue_gas_name} {self.ghg_input_unit}'):
                energy1 = col.replace(
                    f' {CarbonCapture.flue_gas_name} {self.ghg_input_unit}', '')
                dtot_CO2_emissions[
                    f'Total {CarbonCapture.flue_gas_name} ({GlossaryEnergy.mass_unit}) vs {energy1}#{CarbonCapture.flue_gas_name} {self.ghg_input_unit}#prod'] = np.ones(
                    len_years)

        return dtot_CO2_emissions

    # , co2_emissions):
    def compute_grad_CO2_emissions_sinks(self):
        '''
        Compute CO2 total emissions
        '''
        # Initialize dataframes
        len_years = len(self.years)

        co2_production = pd.DataFrame({GlossaryEnergy.Years: self.years})
        co2_consumption = pd.DataFrame({GlossaryEnergy.Years: self.years})

        dtot_CO2_emissions = {}
        # Do not loop over carbon capture and carbon storage which will be
        # handled differently
        for energy in self.energy_list:

            # gather all production columns with a CO2 name in it
            for col, production in self.sub_production_dict[energy].items():
                if col in self.CO2_list:
                    co2_production[f'{energy} {col}'] = production.values
            # gather all consumption columns with a CO2 name in it
            for col, consumption in self.sub_consumption_dict[energy].items():
                if col in self.CO2_list:
                    co2_consumption[f'{energy} {col}'] = consumption.values

            # Compute the CO2 emitted during the use of the net energy
            # If net energy is negative, CO2 by use is equals to zero

        ''' CO2 removed by energy mix       
         CO2 removed by energy mix technologies during the process 
         i.e. biomass processes as managed wood or crop energy
        '''
        energy_removing_co2 = co2_consumption[[
            col for col in co2_consumption if col.endswith(f'{CO2.name} {self.ghg_input_unit}')]]
        energy_removing_co2_list = [key.replace(
            f' {CO2.name} {self.ghg_input_unit}', '') for key in energy_removing_co2]
        if len(energy_removing_co2_list) != 0:
            for energy1 in energy_removing_co2_list:
                dtot_CO2_emissions[
                    f'{CO2.name} removed by energy mix (Mt) vs {energy1}#{CO2.name} {self.ghg_input_unit}#cons'] = np.ones(
                    len_years)

        return dtot_CO2_emissions
