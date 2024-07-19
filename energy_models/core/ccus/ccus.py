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

import numpy as np
import pandas as pd

from energy_models.core.stream_type.base_stream import BaseStream
from energy_models.core.stream_type.carbon_models.carbon import Carbon
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.glossaryenergy import GlossaryEnergy


class CCUS(BaseStream):
    """
    Class CCUS
    """
    name = GlossaryEnergy.ccus_type
    PRODUCTION = 'production'
    DELTA_ENERGY_PRICES = 'delta_energy_prices'
    DELTA_CO2_EMISSIONS = 'delta_co2_emissions'
    TOTAL_PRODUCTION = 'Total production'
    RESOURCE_LIST = ['natural_gas_resource',
                     'uranium_resource', 'coal_resource', 'oil_resource']
    CARBON_STORAGE_CONSTRAINT = 'carbon_storage_constraint'

    resource_list = RESOURCE_LIST
    CO2_list = [f'{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit})',
                f'{CarbonCapture.flue_gas_name} ({GlossaryEnergy.mass_unit})',
                f'{GlossaryEnergy.carbon_storage} ({GlossaryEnergy.mass_unit})',
                f'{Carbon.name} ({GlossaryEnergy.mass_unit})']
    ccs_list = [GlossaryEnergy.carbon_capture, GlossaryEnergy.carbon_storage]

    def __init__(self, name):
        '''
        Constructor 
        '''
        super(CCUS, self).__init__(name)

        self.CCS_price = None
        self.carbonstorage_limit = None
        self.carbonstorage_constraint_ref = None
        self.stream_prices = None
        self.all_resource_demand = None
        self.co2_production = None
        self.co2_consumption = None
        self.emissions_by_energy = None
        self.carbon_storage_constraint = None
        self.total_co2_emissions = pd.DataFrame()
        self.total_co2_emissions_Gt = None
        self.co2_for_food = None
        self.scaling_factor_energy_production = None
        self.scaling_factor_energy_consumption = None
        self.co2_emissions_needed_by_energy_mix = None
        self.carbon_capture_from_energy_mix = None
        self.total_carbon_storage_by_invest = None

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
        self.subelements_list = inputs_dict[GlossaryEnergy.ccs_list]
        BaseStream.configure_parameters(self, inputs_dict)

        self.co2_for_food = pd.DataFrame(
            {GlossaryEnergy.Years: self.production[GlossaryEnergy.Years], f'{GlossaryEnergy.carbon_capture} for food (Mt)': 0.0})
        self.CCS_price = pd.DataFrame(
            {GlossaryEnergy.Years: np.arange(inputs_dict[GlossaryEnergy.YearStart],
                                             inputs_dict[GlossaryEnergy.YearEnd] + 1)})
        self.carbonstorage_limit = inputs_dict['carbonstorage_limit']
        self.carbonstorage_constraint_ref = inputs_dict['carbonstorage_constraint_ref']
        self.total_carbon_storage_by_invest = np.zeros(len(self.production[GlossaryEnergy.Years]))

    def configure_parameters_update(self, inputs_dict):
        '''
        COnfigure parameters with possible update (variables that does change during the run)
        '''
        self.subelements_list = inputs_dict[GlossaryEnergy.ccs_list]

        # Specific configure for energy mix
        self.scaling_factor_energy_production = inputs_dict['scaling_factor_energy_production']
        self.scaling_factor_energy_consumption = inputs_dict['scaling_factor_energy_consumption']
        for element in self.subelements_list:
            self.sub_prices[element] = inputs_dict[f'{element}.{GlossaryEnergy.StreamPricesValue}'][element]
            self.sub_production_dict[element] = inputs_dict[f'{element}.{GlossaryEnergy.EnergyProductionValue}'] * \
                                               self.scaling_factor_energy_production
            self.sub_consumption_dict[element] = inputs_dict[f'{element}.{GlossaryEnergy.EnergyConsumptionValue}'] * \
                                                self.scaling_factor_energy_consumption
            self.sub_consumption_woratio_dict[element] = inputs_dict[f'{element}.{GlossaryEnergy.EnergyConsumptionWithoutRatioValue}'] * \
                                                        self.scaling_factor_energy_consumption

        self.stream_prices = self.sub_prices.copy(deep=True)

        # dataframe resource demand
        self.all_resource_demand = pd.DataFrame(
            {GlossaryEnergy.Years: self.stream_prices[GlossaryEnergy.Years].values})
        for elements in self.resource_list:
            if elements in self.resource_list:
                self.all_resource_demand[elements] = np.linspace(
                    0, 0, len(self.all_resource_demand.index)) * 100.
        for element in self.subelements_list:
            for elements in self.sub_consumption_dict[element]:
                if elements in self.resource_list:
                    self.all_resource_demand[elements] = self.all_resource_demand[elements] + \
                                                         inputs_dict[
                                                             f'{element}.{GlossaryEnergy.EnergyConsumptionValue}'][
                                                             elements].values * \
                                                         self.scaling_factor_energy_consumption

        self.co2_emissions_needed_by_energy_mix = inputs_dict['co2_emissions_needed_by_energy_mix']
        self.carbon_capture_from_energy_mix = inputs_dict['carbon_capture_from_energy_mix']
        # self.co2_emissions = inputs_dict['co2_emissions']

    def compute_CO2_emissions(self):
        '''
        Compute CO2 total emissions
        '''
        # Initialize dataframes

        self.co2_production = pd.DataFrame({GlossaryEnergy.Years: self.production[GlossaryEnergy.Years]})
        self.total_co2_emissions[GlossaryEnergy.Years] = self.production[GlossaryEnergy.Years]
        self.co2_consumption = pd.DataFrame(
            {GlossaryEnergy.Years: self.production[GlossaryEnergy.Years]})
        self.emissions_by_energy = pd.DataFrame(
            {GlossaryEnergy.Years: self.production[GlossaryEnergy.Years]})
        # Do not loop over carbon capture and carbon storage which will be
        # handled differently

        ''' CARBON STORAGE 
         Total carbon storage is production of carbon storage
         Solid carbon is gaseous equivalent in the production for
         solidcarbonstorage technology
        '''
        if GlossaryEnergy.carbon_storage in self.sub_production_dict:

            self.total_co2_emissions[f'{GlossaryEnergy.carbon_storage} ({GlossaryEnergy.mass_unit})'] = self.sub_production_dict[
                GlossaryEnergy.carbon_storage][GlossaryEnergy.carbon_storage].values
            try:
                self.total_carbon_storage_by_invest = self.sub_production_dict[GlossaryEnergy.carbon_storage][
                                                          GlossaryEnergy.carbon_storage].values * \
                                                      self.sub_consumption_woratio_dict[GlossaryEnergy.carbon_storage][
                                                          f'{GlossaryEnergy.carbon_capture} ({CarbonCapture.unit})'].values / \
                                                      self.sub_consumption_dict[GlossaryEnergy.carbon_storage][
                                                          f'{GlossaryEnergy.carbon_capture} ({CarbonCapture.unit})'].values
            except:
                a = 1
        else:
            self.total_co2_emissions[f'{GlossaryEnergy.carbon_storage} ({GlossaryEnergy.mass_unit})'] = 0.0

        ''' CARBON CAPTURE from CC technos       
         Total carbon capture = carbon captured from carboncapture stream +
         carbon captured from energies (can be negative if FischerTropsch needs carbon
         captured)
        '''
        if GlossaryEnergy.carbon_capture in self.sub_production_dict:

            self.total_co2_emissions[f'{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit}) from CC technos'] = self.sub_production_dict[
                GlossaryEnergy.carbon_capture][GlossaryEnergy.carbon_capture].values
        else:
            self.total_co2_emissions[f'{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit}) from CC technos'] = 0.0

        ''' Carbon captured that needs to be stored
            sum of the one from CC technos and the one directly captured 
            we delete the one needed by energy mix and potentially later the CO2 for food
        '''

        self.total_co2_emissions[f'{GlossaryEnergy.carbon_capture} to be stored (Mt)'] = self.total_co2_emissions[
                                                                                  f'{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit}) from CC technos'] + \
                                                                              self.carbon_capture_from_energy_mix[
                                                                                  f'{GlossaryEnergy.carbon_capture} from energy mix (Gt)'] * 1e3 - \
                                                                              self.co2_emissions_needed_by_energy_mix[
                                                                                  f'{GlossaryEnergy.carbon_capture} needed by energy mix (Gt)'] * 1e3 - \
                                                                              self.co2_for_food[
                                                                                  f'{GlossaryEnergy.carbon_capture} for food (Mt)']

        '''
            Solid Carbon to be stored to limit the carbon solid storage
        '''
        energy_producing_solid_carbon = self.co2_production[[
            col for col in self.co2_production if col.endswith(f'{Carbon.name} ({GlossaryEnergy.mass_unit})')]]
        energy_producing_solid_carbon_list = [key.replace(
            f' {Carbon.name} ({GlossaryEnergy.mass_unit})', '') for key in energy_producing_solid_carbon]
        if len(energy_producing_solid_carbon_list) != 0:
            self.total_co2_emissions[f'{Carbon.name} to be stored (Mt)'] = energy_producing_solid_carbon.sum(
                axis=1).values
        else:
            self.total_co2_emissions[
                f'{Carbon.name} to be stored (Mt)'] = 0.0

        '''
            Solid Carbon storage 
        '''
        self.total_co2_emissions[f'Solid {Carbon.name} storage (Mt)'] = 0.0
        if GlossaryEnergy.carbon_storage in self.sub_consumption_dict:
            if f'{Carbon.name} ({GlossaryEnergy.mass_unit})' in self.sub_consumption_dict[GlossaryEnergy.carbon_storage]:
                self.total_co2_emissions[f'Solid {Carbon.name} storage (Mt)'] = self.sub_consumption_dict[
                    GlossaryEnergy.carbon_storage][f'{Carbon.name} ({GlossaryEnergy.mass_unit})'].values

        '''
            The carbon stored by invest is limited by the carbon previously captured to be stored
            for gaseous and solid carbon storage
            Solid carbon storage is taken into account into carbon storage 
            need to delete it before using the minimum
        '''

        self.total_co2_emissions[f'{GlossaryEnergy.carbon_storage} Limited by capture (Mt)'] = np.minimum(
            self.total_co2_emissions[f'{GlossaryEnergy.carbon_capture} to be stored (Mt)'].values,
            self.total_co2_emissions[f'{GlossaryEnergy.carbon_storage} ({GlossaryEnergy.mass_unit})'].values - self.total_co2_emissions[
                f'Solid {Carbon.name} storage (Mt)'].values * Carbon.data_energy_dict[GlossaryEnergy.CO2PerUse]) + \
                                                                                    np.minimum(
                                                                                        self.total_co2_emissions[
                                                                                            f'{Carbon.name} to be stored (Mt)'].values,
                                                                                        self.total_co2_emissions[
                                                                                            f'Solid {Carbon.name} storage (Mt)'].values) * \
                                                                                    Carbon.data_energy_dict[
                                                                                        GlossaryEnergy.CO2PerUse]

        self.total_co2_emissions_Gt = pd.DataFrame(
            {GlossaryEnergy.Years: self.production[GlossaryEnergy.Years],
             f'{GlossaryEnergy.carbon_storage} Limited by capture (Gt)': self.total_co2_emissions[
                                                                  f'{GlossaryEnergy.carbon_storage} Limited by capture (Mt)'].values / 1e3})

    def compute_CCS_price(self):
        '''
        Compute CCS_price 
        '''
        self.CCS_price['ccs_price_per_tCO2'] = 0.
        if GlossaryEnergy.carbon_capture in self.sub_prices:
            self.CCS_price['ccs_price_per_tCO2'] += self.stream_prices[GlossaryEnergy.carbon_capture]
        if GlossaryEnergy.carbon_storage in self.sub_prices:
            self.CCS_price['ccs_price_per_tCO2'] += self.sub_prices[GlossaryEnergy.carbon_storage]

    def compute_carbon_storage_constraint(self):
        '''
        Compute carbon storage constraint
        '''

        self.carbon_storage_constraint = np.array(
            [- (self.total_co2_emissions[f'{GlossaryEnergy.carbon_storage} Limited by capture (Mt)'].sum(
            ) - self.carbonstorage_limit) / self.carbonstorage_constraint_ref])

    def compute_grad_CO2_emissions(self, co2_emissions):
        '''
        Compute CO2 total emissions
        '''
        # Initialize dataframes
        len_years = len(self.production[GlossaryEnergy.Years])

        co2_production = pd.DataFrame({GlossaryEnergy.Years: self.production[GlossaryEnergy.Years]})
        co2_consumption = pd.DataFrame(
            {GlossaryEnergy.Years: self.production[GlossaryEnergy.Years]})

        dtot_CO2_emissions = {}
        # Do not loop over carbon capture and carbon storage which will be
        # handled differently

        ''' CARBON STORAGE 
         Total carbon storage is production of carbon storage
         Solid carbon is gaseous equivalent in the production for
         solidcarbonstorage technology
        '''
        if GlossaryEnergy.carbon_storage in self.sub_production_dict:
            dtot_CO2_emissions[
                f'{GlossaryEnergy.carbon_storage} ({GlossaryEnergy.mass_unit}) vs {GlossaryEnergy.carbon_storage}#{GlossaryEnergy.carbon_storage}#prod'] = np.ones(
                len_years)
        #             self.total_co2_emissions[f'{GlossaryEnergy.carbon_storage} ({GlossaryEnergy.mass_unit})'] = self.sub_production_dict[
        #                 GlossaryEnergy.carbon_storage][GlossaryEnergy.carbon_storage].values
        #         else:
        #             self.total_co2_emissions[f'{GlossaryEnergy.carbon_storage} ({GlossaryEnergy.mass_unit})'] = 0.0

        ''' CARBON CAPTURE from CC technos       
         Total carbon capture = carbon captured from carboncapture stream +
         carbon captured from energies (can be negative if FischerTropsch needs carbon
         captured)
        '''
        if GlossaryEnergy.carbon_capture in self.sub_production_dict:
            dtot_CO2_emissions[
                f'{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit}) from CC technos vs {GlossaryEnergy.carbon_capture}#{GlossaryEnergy.carbon_capture}#prod'] = np.ones(
                len_years)
        #             self.total_co2_emissions[f'{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit}) from CC technos'] = self.sub_production_dict[
        #                 GlossaryEnergy.carbon_capture][GlossaryEnergy.carbon_capture].values
        #         else:
        #             self.total_co2_emissions[f'{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit}) from CC technos'] = 0.0

        ''' CARBON CAPTURE from energy mix
        Total carbon capture from energy mix if the technology offers carbon_capture
         Ex : upgrading biogas technology is the same as Amine Scrubbing but
         on a different gas (biogas for upgrading biogas and flue gas for
         Amien scrubbing)
        '''
        energy_producing_carbon_capture = co2_production[[
            col for col in co2_production if col.endswith(f'{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit})')]]
        energy_producing_carbon_capture_list = [key.replace(
            f' {GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit})', '') for key in energy_producing_carbon_capture]
        if len(energy_producing_carbon_capture_list) != 0:
            for energy1 in energy_producing_carbon_capture_list:
                dtot_CO2_emissions[
                    f'{GlossaryEnergy.carbon_capture} from energy mix (Mt) vs {energy1}#{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit})#prod'] = np.ones(
                    len_years)
        #             self.total_co2_emissions[f'{GlossaryEnergy.carbon_capture} from energy mix (Mt)'] = energy_producing_carbon_capture.sum(
        #                 axis=1).values
        #         else:
        #             self.total_co2_emissions[
        #                 f'{GlossaryEnergy.carbon_capture} from energy mix (Mt)'] = 0.0

        ''' CARBON CAPTURE needed by energy mix
        Total carbon capture needed by energy mix if a technology needs carbon_capture
         Ex :Sabatier process or RWGS in FischerTropsch technology 
        '''
        energy_needing_carbon_capture = co2_consumption[[
            col for col in co2_consumption if col.endswith(f'{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit})')]]
        energy_needing_carbon_capture_list = [key.replace(
            f' {GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit})', '') for key in energy_needing_carbon_capture]
        if len(energy_needing_carbon_capture_list) != 0:
            for energy1 in energy_needing_carbon_capture_list:
                dtot_CO2_emissions[
                    f'{GlossaryEnergy.carbon_capture} needed by energy mix (Mt) vs {energy1}#{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit})#cons'] = np.ones(
                    len_years)
        #             self.total_co2_emissions[f'{GlossaryEnergy.carbon_capture} needed by energy mix (Mt)'] = energy_needing_carbon_capture.sum(
        #                 axis=1).values
        #         else:
        #             self.total_co2_emissions[
        #                 f'{GlossaryEnergy.carbon_capture} needed by energy mix (Mt)'] = 0.0

        ''' CO2 from energy mix       
         CO2 expelled by energy mix technologies during the process 
         i.e. for machinery or tractors 
        '''
        energy_producing_co2 = co2_production[[
            col for col in co2_production if col.endswith(f'{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit})')]]
        energy_producing_co2_list = [key.replace(
            f' {GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit})', '') for key in energy_producing_co2]
        if len(energy_producing_co2_list) != 0:
            for energy1 in energy_producing_co2_list:
                dtot_CO2_emissions[
                    f'{GlossaryEnergy.carbon_capture} from energy mix (Mt) vs {energy1}#{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit})#prod'] = np.ones(len_years)

        #             self.total_co2_emissions[f'{GlossaryEnergy.carbon_capture} from energy mix (Mt)'] = energy_producing_co2.sum(
        #                 axis=1).values
        #         else:
        #             self.total_co2_emissions[
        #                 f'{GlossaryEnergy.carbon_capture} from energy mix (Mt)'] = 0.0

        ''' CO2 removed by energy mix       
         CO2 removed by energy mix technologies during the process 
         i.e. biomass processes as managed wood or crop energy
        '''
        energy_removing_co2 = co2_consumption[[
            col for col in co2_consumption if col.endswith(f'{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit})')]]
        energy_removing_co2_list = [key.replace(
            f' {GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit})', '') for key in energy_removing_co2]
        if len(energy_removing_co2_list) != 0:
            for energy1 in energy_removing_co2_list:
                dtot_CO2_emissions[
                    f'{GlossaryEnergy.carbon_capture} removed by energy mix (Mt) vs {energy1}#{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit})#cons'] = np.ones(len_years)
        #             self.total_co2_emissions[f'{GlossaryEnergy.carbon_capture} removed by energy mix (Mt)'] = energy_removing_co2.sum(
        #                 axis=1).values
        #         else:
        #             self.total_co2_emissions[
        #                 f'{GlossaryEnergy.carbon_capture} removed energy mix (Mt)'] = 0.0

        ''' Total C02 from Flue gas
            sum of all production of flue gas 
            it could be equal to carbon capture from CC technos if enough investment but not sure
        '''
        #         self.total_co2_emissions[f'Total {CarbonCapture.flue_gas_name} ({GlossaryEnergy.mass_unit})'] = self.co2_production[[
        # col for col in self.co2_production if
        # col.endswith(f'{CarbonCapture.flue_gas_name} ({GlossaryEnergy.mass_unit})')]].sum(axis=1)
        for col in co2_production:
            if col.endswith(f'{CarbonCapture.flue_gas_name} ({GlossaryEnergy.mass_unit})'):
                energy1 = col.replace(
                    f' {CarbonCapture.flue_gas_name} ({GlossaryEnergy.mass_unit})', '')
                dtot_CO2_emissions[
                    f'Total {CarbonCapture.flue_gas_name} ({GlossaryEnergy.mass_unit}) vs {energy1}#{CarbonCapture.flue_gas_name} ({GlossaryEnergy.mass_unit})#prod'] = np.ones(
                    len_years)
        ''' Carbon captured that needs to be stored
            sum of the one from CC technos and the one directly captured 
            we delete the one needed by energy mix and potentially later the CO2 for food
        '''

        #         self.total_co2_emissions[f'{GlossaryEnergy.carbon_capture} to be stored (Mt)'] = self.total_co2_emissions[f'{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit}) from CC technos'] + \
        #             self.total_co2_emissions[f'{GlossaryEnergy.carbon_capture} from energy mix (Mt)'] - \
        #             self.total_co2_emissions[f'{GlossaryEnergy.carbon_capture} needed by energy mix (Mt)'] -\
        #             self.total_co2_emissions[f'{GlossaryEnergy.carbon_capture} for food (Mt)'

        new_key = f'{GlossaryEnergy.carbon_capture} to be stored (Mt)'
        dtot_CO2_emissions[f'{new_key} vs {GlossaryEnergy.carbon_capture} for food (Mt)#carbon_capture'] = - np.ones(
            len_years)
        dtot_CO2_emissions[f'{new_key} vs {GlossaryEnergy.carbon_capture} from energy mix (Mt)#carbon_capture'] = np.ones(
            len_years)
        dtot_CO2_emissions[f'{new_key} vs {GlossaryEnergy.carbon_capture} needed by energy mix (Mt)#carbon_capture'] = - np.ones(
            len_years)
        key_dep_tuple_list = [(f'{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit}) from CC technos', 1.0),
                              (f'{GlossaryEnergy.carbon_capture} from energy mix (Mt)', 1.0),
                              (f'{GlossaryEnergy.carbon_capture} needed by energy mix (Mt)', -1.0),
                              (f'{GlossaryEnergy.carbon_capture} for food (Mt)', -1.0)]
        dtot_CO2_emissions = update_new_gradient(
            dtot_CO2_emissions, key_dep_tuple_list, new_key)

        cc_to_be_stored = co2_emissions[f'{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit}) from CC technos'].values + \
                          self.carbon_capture_from_energy_mix[
                              f'{GlossaryEnergy.carbon_capture} from energy mix (Gt)'].values * 1e3 - \
                          self.co2_emissions_needed_by_energy_mix[
                              f'{GlossaryEnergy.carbon_capture} needed by energy mix (Gt)'].values * 1e3 - \
                          self.co2_for_food[f'{GlossaryEnergy.carbon_capture} for food (Mt)'].values
        # if the carbon to be stored is lower than zero that means that we need
        # more carbon capture for energy mix than the one created by CC technos
        # or upgrading biogas
        if cc_to_be_stored.min() < 0:
            cc_needed = self.co2_emissions_needed_by_energy_mix[
                            f'{GlossaryEnergy.carbon_capture} needed by energy mix (Gt)'].values * 1e3
            cc_provided = co2_emissions[f'{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit}) from CC technos'].values + \
                          self.carbon_capture_from_energy_mix[
                              f'{GlossaryEnergy.carbon_capture} from energy mix (Gt)'].values * 1e3
            dtot_CO2_emissions_old = dtot_CO2_emissions.copy()
            dratio_dkey = {}
            # The gradient is (u/v)' = (u'v -uv')/v**2 = u'/v -uv'/v**2
            # u is the cc needed f'{GlossaryEnergy.carbon_capture} needed by energy mix (Mt)'
            # v is the cc provided which is the sum of f'{GlossaryEnergy.carbon_capture}
            # (Mt) from CC technos' and f'{GlossaryEnergy.carbon_capture} from energy mix
            # (Mt)'

            for key, grad_cc in dtot_CO2_emissions_old.items():
                key_co2_emissions = key.split(' vs ')[0]
                grad_info_x = key.split(' vs ')[1]
                if key_co2_emissions == f'{GlossaryEnergy.carbon_capture} needed by energy mix (Mt)':

                    if grad_info_x in dratio_dkey:
                        dratio_dkey[grad_info_x] -= np.divide(cc_provided * grad_cc, cc_needed ** 2,
                                                              out=np.zeros_like(cc_needed), where=cc_needed > 1.0e-15)
                    else:
                        dratio_dkey[grad_info_x] = - np.divide(cc_provided * grad_cc, cc_needed ** 2,
                                                               out=np.zeros_like(cc_needed), where=cc_needed > 1.0e-15)

                elif key_co2_emissions in [f'{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit}) from CC technos',
                                           f'{GlossaryEnergy.carbon_capture} from energy mix (Mt)']:

                    if grad_info_x in dratio_dkey:
                        dratio_dkey[grad_info_x] += np.divide(grad_cc, cc_needed,
                                                              out=np.zeros_like(cc_needed), where=cc_needed > 1.0e-15)
                    else:
                        dratio_dkey[grad_info_x] = np.divide(grad_cc, cc_needed,
                                                             out=np.zeros_like(cc_needed), where=cc_needed > 1.0e-15)

        grad_max = np.maximum(0.0, np.sign(
            cc_to_be_stored))

        for key, value in dtot_CO2_emissions.items():
            if key.startswith(f'{GlossaryEnergy.carbon_capture} to be stored (Mt)'):
                value *= grad_max
        #         co2_emissions[f'{GlossaryEnergy.carbon_capture} to be stored (Mt)'] = np.maximum(
        # co2_emissions[f'{GlossaryEnergy.carbon_capture} to be stored (Mt)'],
        # 0.0)

        '''
            Solid Carbon to be stored to limit the carbon solid storage
        '''
        #         energy_producing_solid_carbon = self.co2_production[[
        #             col for col in self.co2_production if col.endswith(f'{Carbon.name} ({GlossaryEnergy.mass_unit})')]]
        #         energy_producing_solid_carbon_list = [key.replace(
        #             f' {Carbon.name} ({GlossaryEnergy.mass_unit})', '') for key in energy_producing_solid_carbon]
        #         if len(energy_producing_solid_carbon_list) != 0:
        #             co2_emissions[f'{Carbon.name} to be stored (Mt)'] = energy_producing_solid_carbon.sum(
        #                 axis=1).values
        #         else:
        #             co2_emissions[
        #                 f'{Carbon.name} to be stored (Mt)'] = 0.0

        for col in co2_production:
            if col.endswith(f'{Carbon.name} ({GlossaryEnergy.mass_unit})'):
                energy1 = col.replace(f' {Carbon.name} ({GlossaryEnergy.mass_unit})', '')
                dtot_CO2_emissions[f'{Carbon.name} to be stored (Mt) vs {energy1}#{Carbon.name} ({GlossaryEnergy.mass_unit})#prod'] = np.ones(
                    len_years)
        '''
            Solid Carbon storage 
        '''

        if GlossaryEnergy.carbon_storage in self.sub_consumption_dict:
            if f'{Carbon.name} ({GlossaryEnergy.mass_unit})' in self.sub_consumption_dict[GlossaryEnergy.carbon_storage]:
                dtot_CO2_emissions[
                    f'Solid {Carbon.name} storage (Mt) vs {GlossaryEnergy.carbon_storage}#{Carbon.name} ({GlossaryEnergy.mass_unit})#cons'] = np.ones(
                    len_years)
        #                 co2_emissions[f'Solid {Carbon.name} storage (Mt)'] = self.sub_consumption_dict[
        #                     GlossaryEnergy.carbon_storage][f'{Carbon.name} ({GlossaryEnergy.mass_unit})'].values

        '''
            The carbon stored by invest is limited by the carbon previously captured to be stored
            for gaseous and solid carbon storage
            Solid carbon storage is taken into account into carbon storage 
            need to delete it before using the minimum
        '''
        # if abs (min(a,b)-a) = 0.0 then the minimum is a else the minimum is b
        # and the sign of abs (min(a,b)-a) is one
        mini1 = np.minimum(
            co2_emissions[f'{GlossaryEnergy.carbon_capture} to be stored (Mt)'].values,
            co2_emissions[f'{GlossaryEnergy.carbon_storage} ({GlossaryEnergy.mass_unit})'].values - co2_emissions[
                f'Solid {Carbon.name} storage (Mt)'].values * Carbon.data_energy_dict[GlossaryEnergy.CO2PerUse])
        limit_is_storage = np.maximum(0.0, np.sign(np.abs(
            mini1 - co2_emissions[f'{GlossaryEnergy.carbon_capture} to be stored (Mt)'].values)))
        limit_is_to_be_stored = np.ones(len_years) - limit_is_storage

        # if abs (min(a,b)-a) = 0.0 then the minimum is a else the minimum is b
        # and the sign of abs (min(a,b)-a) is one
        mini2 = np.minimum(
            co2_emissions[f'{Carbon.name} to be stored (Mt)'].values,
            co2_emissions[f'Solid {Carbon.name} storage (Mt)'].values) * Carbon.data_energy_dict[GlossaryEnergy.CO2PerUse]

        limit_is_solid_storage = np.maximum(0.0, np.sign(np.abs(
            mini2 - co2_emissions[f'{Carbon.name} to be stored (Mt)'].values * Carbon.data_energy_dict[GlossaryEnergy.CO2PerUse])))
        limit_is_solid_to_be_stored = np.ones(
            len_years) - limit_is_solid_storage
        new_key = f'{GlossaryEnergy.carbon_storage} Limited by capture (Mt)'
        key_dep_tuple_list = [(f'{GlossaryEnergy.carbon_capture} to be stored (Mt)', limit_is_to_be_stored),
                              (f'{Carbon.name} to be stored (Mt)',
                               limit_is_solid_to_be_stored * Carbon.data_energy_dict[GlossaryEnergy.CO2PerUse]),
                              (f'{GlossaryEnergy.carbon_storage} ({GlossaryEnergy.mass_unit})', limit_is_storage),
                              (f'Solid {Carbon.name} storage (Mt)',
                               (-limit_is_storage + limit_is_solid_storage) * Carbon.data_energy_dict[GlossaryEnergy.CO2PerUse])]
        dtot_CO2_emissions = update_new_gradient(
            dtot_CO2_emissions, key_dep_tuple_list, new_key)

        dtot_final_CO2_emissions = dtot_CO2_emissions.copy()
        for key, gradient in dtot_CO2_emissions.items():

            if key.startswith(f'{GlossaryEnergy.carbon_storage} Limited by capture (Mt)'):
                new_key = key.replace(
                    f'{GlossaryEnergy.carbon_storage} Limited by capture (Mt)', 'Carbon storage constraint')
                dtot_final_CO2_emissions[new_key] = - \
                                                        gradient / self.carbonstorage_constraint_ref

        return dtot_final_CO2_emissions


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
