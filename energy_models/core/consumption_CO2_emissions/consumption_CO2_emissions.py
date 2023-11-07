'''
Copyright 2022 Airbus SAS

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

import pandas as pd
import numpy as np

from climateeconomics.glossarycore import GlossaryCore
from energy_models.core.stream_type.base_stream import BaseStream
from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.core.stream_type.carbon_models.carbon import Carbon
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.carbon_models.carbon_storage import CarbonStorage


class ConsumptionCO2Emissions(BaseStream):
    """
    Class ConsumptionCO2Emissions:
    Takes as inputs the total production and the CO2 emissions per energy out of EnergyMix
    and calculate the total CO2 emissions of the energy consumption
    """
    name = 'ConsumptionCO2Emissions'

    CO2_list = [f'{CarbonCapture.name} (Mt)',
                f'{CarbonCapture.flue_gas_name} (Mt)',
                f'{CarbonStorage.name} (Mt)',
                f'{CO2.name} (Mt)',
                f'{Carbon.name} (Mt)']

    def __init__(self, name):
        '''
        Constructor 
        '''
        super(ConsumptionCO2Emissions, self).__init__(name)

    def configure(self, inputs_dict):
        '''
        Configure method 
        '''
        self.configure_parameters(inputs_dict)
        self.configure_parameters_update(inputs_dict)

    def configure_parameters(self, inputs_dict):
        '''
        Configure parameters (variables that does not change during the run)
        '''
        self.energy_list = inputs_dict[GlossaryCore.energy_list]
        self.ccs_list = inputs_dict[GlossaryCore.ccs_list]

    def configure_parameters_update(self, inputs_dict):
        '''
        Configure parameters with possible update (variables that does change during the run)
        '''

        self.years = np.arange(
            inputs_dict[GlossaryCore.YearStart], inputs_dict[GlossaryCore.YearEnd] + 1)

        self.scaling_factor_energy_production = inputs_dict['scaling_factor_energy_production']
        self.scaling_factor_energy_consumption = inputs_dict['scaling_factor_energy_consumption']
        self.energy_list = inputs_dict[GlossaryCore.energy_list]
        self.ccs_list = inputs_dict[GlossaryCore.ccs_list]

        self.co2_per_use = pd.DataFrame(
            {GlossaryCore.Years: self.years})
        self.sub_production_dict = {}
        self.sub_consumption_dict = {}

        for energy in self.energy_list:

            self.co2_per_use[energy] = inputs_dict[f'{energy}.CO2_per_use']['CO2_per_use']
            self.sub_production_dict[energy] = inputs_dict[f'{energy}.{GlossaryCore.EnergyProductionValue}'] * \
                self.scaling_factor_energy_production
            self.sub_consumption_dict[energy] = inputs_dict[f'{energy}.{GlossaryCore.EnergyConsumptionValue}'] * \
                self.scaling_factor_energy_consumption

        for energy in self.ccs_list:
            self.sub_production_dict[energy] = inputs_dict[f'{energy}.{GlossaryCore.EnergyProductionValue}'] * \
                                               self.scaling_factor_energy_production

        self.energy_production_detailed = inputs_dict[GlossaryCore.EnergyProductionDetailedValue]

    def compute_CO2_emissions(self):
        '''
        Compute CO2 total emissions
        '''
        # Initialize dataframes
        self.CO2_sources = pd.DataFrame({GlossaryCore.Years: self.years})
        self.CO2_sinks = pd.DataFrame({GlossaryCore.Years: self.years})
        self.CO2_production = pd.DataFrame({GlossaryCore.Years: self.years})
        self.CO2_consumption = pd.DataFrame({GlossaryCore.Years: self.years})

        # Aggregate CO2 production and consumption columns from sub_production
        # and sub_consumption df
        for energy in self.energy_list  :
            # gather all production columns with a CO2 name in it
            for col, production in self.sub_production_dict[energy].items():
                if col in self.CO2_list:
                    self.CO2_production[f'{energy} {col}'] = production.values
            # gather all consumption columns with a CO2 name in it
            for col, consumption in self.sub_consumption_dict[energy].items():
                if col in self.CO2_list:
                    self.CO2_consumption[f'{energy} {col}'] = consumption.values
            # Compute the CO2 emitted during the use of the net energy
            # If net energy is negative, CO2 by use is equals to zero
            self.CO2_production[f'{energy} CO2 by use (Mt)'] = self.co2_per_use[energy] * np.maximum(
                0.0, self.energy_production_detailed[f'production {energy} (TWh)'].values)

        for energy in self.ccs_list:
            for col, production in self.sub_production_dict[energy].items():
                if col in self.CO2_list:
                    self.CO2_production[f'{energy} {col}'] = production.values
        ''' CO2 from energy mix    
         CO2 expelled by energy mix technologies during the process 
         i.e. for machinery or tractors 
        '''
        energy_producing_co2 = self.CO2_production[[
            col for col in self.CO2_production if col.endswith(f'{CO2.name} (Mt)')]]
        energy_producing_co2_list = [key.replace(
            f' {CO2.name} (Mt)', '') for key in energy_producing_co2]
        if len(energy_producing_co2_list) != 0:
            self.CO2_sources[f'{CO2.name} from energy mix (Mt)'] = energy_producing_co2.sum(
                axis=1).values
        else:
            self.CO2_sources[
                f'{CO2.name} from energy mix (Mt)'] = 0.0

        ''' CARBON CAPTURE from energy mix
        Total carbon capture from energy mix if the technology offers carbon_capture
         Ex : upgrading biogas technology is the same as Amine Scrubbing but
         on a different gas (biogas for upgrading biogas and flue gas for
         Amien scrubbing)
        '''
        energy_producing_carbon_capture = self.CO2_production[[
            col for col in self.CO2_production if col.endswith(f'{CarbonCapture.name} (Mt)')]]
        energy_producing_carbon_capture_list = [key.replace(
            f' {CarbonCapture.name} (Mt)', '') for key in energy_producing_carbon_capture]
        if len(energy_producing_carbon_capture_list) != 0:
            self.CO2_sources[f'{CarbonCapture.name} from energy mix (Mt)'] = energy_producing_carbon_capture.sum(
                axis=1).values
        else:
            self.CO2_sources[
                f'{CarbonCapture.name} from energy mix (Mt)'] = 0.0

        ''' CO2 removed by energy mix
         CO2 removed by energy mix technologies during the process 
         i.e. biomass processes as managed wood or crop energy
        '''
        energy_removing_co2 = self.CO2_consumption[[
            col for col in self.CO2_consumption if col.endswith(f'{CO2.name} (Mt)')]]
        energy_removing_co2_list = [key.replace(
            f' {CO2.name} (Mt)', '') for key in energy_removing_co2]
        if len(energy_removing_co2_list) != 0:
            self.CO2_sinks[f'{CO2.name} removed by energy mix (Mt)'] = energy_removing_co2.sum(
                axis=1).values
        else:
            self.CO2_sinks[
                f'{CO2.name} removed by energy mix (Mt)'] = 0.0

        '''Total CO2 by use 
        which is the sum of all CO2 emissions emitted by use of net energy production
        '''
        self.CO2_sources[f'Total CO2 by use (Mt)'] = self.CO2_production[[
            col for col in self.CO2_production if col.endswith(f'CO2 by use (Mt)')]].sum(axis=1)

        ''' Total C02 from Flue gas 
            sum of all production of flue gas
            it could be equal to carbon capture from CC technos if enough investment but not sure
        '''
        self.CO2_sources[f'Total {CarbonCapture.flue_gas_name} (Mt)'] = self.CO2_production[[
            col for col in self.CO2_production if col.endswith(f'{CarbonCapture.flue_gas_name} (Mt)')]].sum(axis=1)

        # update values to Gt
        self.CO2_sources_Gt = pd.DataFrame(
            {GlossaryCore.Years: self.CO2_sources[GlossaryCore.Years]})
        self.CO2_sinks_Gt = pd.DataFrame(
            {GlossaryCore.Years: self.CO2_sinks[GlossaryCore.Years]})

        for column_df in self.CO2_sources.columns:
            if column_df != GlossaryCore.Years:
                self.CO2_sources_Gt[column_df.replace(
                    '(Mt)', '(Gt)')] = self.CO2_sources[column_df] / 1e3

        for column_df in self.CO2_sinks.columns:
            if column_df != GlossaryCore.Years:
                self.CO2_sinks_Gt[column_df.replace(
                    'Mt', 'Gt')] = self.CO2_sinks[column_df] / 1e3

        return self.CO2_sources_Gt, self.CO2_sinks_Gt

    # , co2_emissions):
    def compute_grad_CO2_emissions_sources(self, net_production):
        '''
        Compute CO2 total emissions
        '''
        # Initialize dataframes
        len_years = len(self.years)

        co2_production = pd.DataFrame({GlossaryCore.Years: self.years})
        co2_consumption = pd.DataFrame({GlossaryCore.Years: self.years})

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
                f'production {energy} (TWh)'].values

            dtot_CO2_emissions[f'Total CO2 by use (Gt) vs {energy}#co2_per_use'] = np.maximum(
                0, net_prod)

            # Specific case when net prod is equal to zero
            # if we increase the prod of an energy the net prod will react
            # however if we decrease the cons it does nothing
            net_prod_sign = net_prod.copy()
            net_prod_sign[net_prod_sign == 0] = 1
            dtot_CO2_emissions[f'Total CO2 by use (Gt) vs {energy}#prod'] = self.co2_per_use[energy].values * \
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
            col for col in co2_production if col.endswith(f'{CarbonCapture.name} (Mt)')]]
        energy_producing_carbon_capture_list = [key.replace(
            f' {CarbonCapture.name} (Mt)', '') for key in energy_producing_carbon_capture]
        if len(energy_producing_carbon_capture_list) != 0:
            for energy1 in energy_producing_carbon_capture_list:
                dtot_CO2_emissions[
                    f'{CarbonCapture.name} from energy mix (Gt) vs {energy1}#{CarbonCapture.name} (Mt)#prod'] = np.ones(len_years)
#             self.total_co2_emissions[f'{CarbonCapture.name} from energy mix (Mt)'] = energy_producing_carbon_capture.sum(
#                 axis=1).values
#         else:
#             self.total_co2_emissions[
#                 f'{CarbonCapture.name} from energy mix (Mt)'] = 0.0

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
                    f'{CO2.name} from energy mix (Gt) vs {energy1}#{CO2.name} (Mt)#prod'] = np.ones(len_years)

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
                    f'{CO2.name} removed by energy mix (Gt) vs {energy1}#{CO2.name} (Mt)#cons'] = np.ones(len_years)
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
                dtot_CO2_emissions[f'Total {CarbonCapture.flue_gas_name} (Gt) vs {energy1}#{CarbonCapture.flue_gas_name} (Mt)#prod'] = np.ones(
                    len_years)

        return dtot_CO2_emissions

    # , co2_emissions):
    def compute_grad_CO2_emissions_sinks(self, net_production):
        '''
        Compute CO2 total emissions
        '''
        # Initialize dataframes
        len_years = len(self.years)

        co2_production = pd.DataFrame({GlossaryCore.Years: self.years})
        co2_consumption = pd.DataFrame({GlossaryCore.Years: self.years})

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
                f'production {energy} (TWh)'].values

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
                    f'{CO2.name} removed by energy mix (Gt) vs {energy1}#{CO2.name} (Mt)#cons'] = np.ones(len_years)
#             self.total_co2_emissions[f'{CO2.name} removed by energy mix (Mt)'] = energy_removing_co2.sum(
#                 axis=1).values
#         else:
#             self.total_co2_emissions[
#                 f'{CO2.name} removed energy mix (Mt)'] = 0.0

        return dtot_CO2_emissions
