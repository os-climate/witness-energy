'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/02-2024/06/24 Copyright 2023 Capgemini

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
import math as m
from abc import abstractmethod
from copy import copy

import numpy as np
import pandas as pd
from climateeconomics.core.tools.differentiable_model import DifferentiableModel

from sostrades_optimization_plugins.tools.cst_manager.func_manager_common import (
    cons_smooth_maximum_vect,
    smooth_maximum_vect,
    soft_maximum_vect,
)

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.glossaryenergy import GlossaryEnergy


class TechnoType(DifferentiableModel):
    """
    Class for energy production technology type
    """

    energy_name = 'energy'
    min_value_invest = 1.e-12

    def __init__(self, name):
        self.name = name
        self.inputs[GlossaryEnergy.ResourcesUsedForProductionValue] = []
        self.inputs[GlossaryEnergy.ResourcesUsedForBuildingValue] = []
        self.inputs[GlossaryEnergy.StreamsUsedForProductionValue] = []

        self.inputs['techno_infos_dict'] = {}
        self.inputs['data_fuel_dict'] = {}
        self.product_unit = 'TWh'
        self.nb_years_amort_capex = 10
        self.inputs[GlossaryEnergy.BoolApplyRatio] = False
        self.inputs[GlossaryEnergy.BoolApplyStreamRatio] = False
        self.is_resource_ratio = False
        self.construction_resource_list = ['copper_resource']

    def init_dataframes(self):
        """Init dataframes with years"""
        self.outputs[f'self:{GlossaryEnergy.Years}'] = self.years
        self.outputs[f'self:{GlossaryEnergy.Years}'] = self.years
        self.outputs[f'self:{GlossaryEnergy.Years}'] = self.years
        self.outputs[f'self:{GlossaryEnergy.Years}'] = self.years
        self.outputs[f'self:{GlossaryEnergy.Years}'] = self.years
        self.outputs[f'self:{GlossaryEnergy.Years}'] = self.years
        self.outputs[f'self:{GlossaryEnergy.Years}'] = self.years
        self.outputs[f'self:{GlossaryEnergy.Years}'] = self.years
        self.outputs[f'self:{GlossaryEnergy.Years}'] = self.years
        self.outputs[f'self:{GlossaryEnergy.Years}'] = self.years

    def configure_parameters(self, inputs_dict):
        """Configure with inputs_dict from the discipline"""

        self.year_start = self.inputs[GlossaryEnergy.YearStart]  # year start
        self.year_end = self.inputs[GlossaryEnergy.YearEnd]  # year end
        self.years = np.arange(self.year_start, self.year_end + 1)

        self.init_dataframes()

        # invest level from G$ to M$
        self.inputs[f'{GlossaryEnergy.InvestmentBeforeYearStartValue}:{GlossaryEnergy.InvestLevelValue}'] *= self.inputs['scaling_factor_invest_level']

        self.configure_energy_data(inputs_dict)

    def configure_parameters_update(self, inputs_dict):
        '''
        Configure with inputs_dict from the discipline
        '''
        self.configure_energy_data(inputs_dict)

        self.inputs[f'{GlossaryEnergy.InvestLevelValue}:{GlossaryEnergy.InvestLevelValue}'] *= self.inputs['scaling_factor_invest_level']

        self.outputs[f'self:{GlossaryEnergy.Years}'] = self.years
        self.outputs[f'self:{GlossaryEnergy.Years}'] = self.years
        self.outputs[f'self:{GlossaryEnergy.Years}'] = self.years


    def configure_energy_data(self, inputs_dict):
        '''
        Configure energy data by reading the data_energy_dict in the right Energy class
        Overloaded for each energy type
        '''
        pass

    def compute_resource_consumption(self):
        for resource in self.inputs[GlossaryEnergy.ResourcesUsedForProductionValue]:
            self.outputs[f'consumption_detailed:{resource} ({GlossaryEnergy.mass_unit})'] =\
                self.outputs[f"cost_details:{resource}_needs"] * \
                self.outputs[f'production_detailed:{self.energy_name} ({self.product_unit})']

    def compute_streams_consumption(self):
        for stream in self.inputs[GlossaryEnergy.StreamsUsedForProductionValue]:
            stream_unit = GlossaryEnergy.unit_dicts[stream]
            self.outputs[f'consumption_detailed:{stream} ({stream_unit})'] = \
                self.outputs[f"cost_details:{stream}_needs"] * \
                self.outputs[f'production_detailed:{self.energy_name} ({self.product_unit})']

    def compute_byproducts_production(self):
        """
        Compute the production of byproduct of the technology
        """
        pass

    def select_resources_ratios(self):
        """! Select the ratios to be added to ratio_df and convert it from % to normal
             This function is to be overloaded in specific techno_models
        """
        ratio_df = pd.DataFrame()
        if self.inputs[GlossaryEnergy.BoolApplyStreamRatio]:
            ratio_df = pd.concat(
                [ratio_df, self.all_streams_demand_ratio], ignore_index=True)

        if self.inputs[GlossaryEnergy.BoolApplyResourceRatio]:
            for resource in EnergyMix.RESOURCE_LIST:
                ratio_df[resource] = self.ratio_available_resource[resource]
        for col in ratio_df.columns:
            ratio_df[col] = ratio_df[col] / 100.0
        self.ratio_df = ratio_df

        return ratio_df

    def apply_resources_ratios(self, apply_ressources_ratio: bool = True):
        """! Select the most constraining ratio and apply it to production and consumption.
        To avoid clipping effects, the applied ratio is not the minimum value between all the ratios, 
        but the smoothed minimum value between all the ratio (see func_manager documentation for more).
        A model variables is set in this method:
            -self.applied_ratio: the effective ratio applied for each year
        The method "select_ratios" must have been called beforehand to have the self.ratio_df variable
        @param apply_resources_ratio: boolean, used to activate(True)/deactivate(False) the application of limiting ratios. Defaults to True.
        :param apply_ressources_ratio:
        :type apply_ressources_ratio:
        """
        ratio_values = np.ones(len(self.years))
        min_ratio_name = ['' for _ in ratio_values]
        if apply_ressources_ratio:
            elements = []
            for element in self.ratio_df.columns:
                for col in self.consumption_detailed.columns:
                    if element in col and element != GlossaryEnergy.Years:
                        # Check for a match between ratio_df and the
                        # consumptions by the techno
                        elements += [element, ]
            if len(elements) > 0:
                # If a match is found, calculate the
                # smooth_min(smooth_min(x)=-smooth_max(-x)) between all the
                # matches for each year
                if self.inputs['smooth_type'] == 'smooth_max':
                    ratio_values = - \
                        smooth_maximum_vect(-self.ratio_df[elements])
                elif self.inputs['smooth_type'] == 'soft_max':
                    ratio_values = - \
                        soft_maximum_vect(-self.ratio_df[elements])
                elif self.inputs['smooth_type'] == 'cons_smooth_max':
                    ratio_values = - \
                        cons_smooth_maximum_vect(-self.ratio_df[elements])
                else:
                    raise Exception('Unknown smooth_type')

                min_ratio_name = self.ratio_df[elements].columns[np.argmin(
                    self.ratio_df[elements], axis=1)]

        # Apply the smoothed ratio value
        # ----------
        # WARNING!!!
        # ----------
        # All these application of the ratio_values were made under the
        # assumption that a linear correlation is at work (ratio on prod == ratio on col)
        # there may be special cases that need to be handled differently
        # (quadratic correlation or other)
        for col in self.production_detailed.columns:
            if col != GlossaryEnergy.Years:
                self.production_detailed[col] = self.production_detailed[col] * \
                                                ratio_values
        for col in self.consumption_detailed.columns:
            if col not in [GlossaryEnergy.Years] + [f'{resource} ({GlossaryEnergy.mass_unit})' for resource in self.construction_resource_list]:
                self.consumption_detailed[col] = self.consumption_detailed[col] * \
                                                 ratio_values
            elif col in [f'{resource} ({GlossaryEnergy.mass_unit})' for resource in self.construction_resource_list]:
                ratio_construction_values = 1
                self.consumption_detailed[col] = self.consumption_detailed[col] * \
                                                 ratio_construction_values
        for col in self.land_use.columns:
            if col != GlossaryEnergy.Years:
                self.land_use[col] = self.land_use[col] * \
                                     ratio_values
        # Pass this dataframe as model variable
        self.applied_ratio = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                           'min_ratio_name': min_ratio_name,
                                           'applied_ratio': ratio_values})

    def compute_capital(self):
        '''
        Compute Capital & loss of capital because of the unusability of the technology.
        When the applied ratio is below 1, the technology does not produce all the energy possible.
        Investments on this technology is consequently non_use. 
        This method computes the non_use of capital 

        Capex is in $/MWh
        Prod in TWh 
        then capex*prod_wo_ratio is in $/MWh*(1e6MWh)= M$

        We divide by scaling_factor_invest_level to put non_use_capital in G$
        '''
        self.techno_capital[GlossaryEnergy.Capital] = self.outputs[f'cost_details:Capex_{self.name}'] \
                                                      * self.production_woratio[
                                                          f'{self.energy_name} ({self.product_unit})'] \
                                                      / self.inputs['scaling_factor_invest_level']

        self.techno_capital[GlossaryEnergy.NonUseCapital] = self.techno_capital[GlossaryEnergy.Capital] * (
                1.0 - self.applied_ratio['applied_ratio'] * self.inputs[f'{GlossaryEnergy.UtilisationRatioValue}:{GlossaryEnergy.UtilisationRatioValue}'] / 100.)

    def compute_price(self):
        """
        Compute the detail price of the technology
        """

        self.outputs[f'cost_details:{GlossaryEnergy.InvestValue}'] = self.inputs[f'{GlossaryEnergy.InvestLevelValue}:{GlossaryEnergy.InvestLevelValue}']

        self.outputs[f'cost_details:Capex_{self.name}'] = self.compute_capex(
            self.outputs[f'cost_details:{GlossaryEnergy.InvestValue}'], self.inputs['techno_infos_dict'])

        self.capital_recovery_factor = self.compute_capital_recovery_factor(self.inputs['techno_infos_dict'])
        self.compute_efficiency()

        self.compute_other_primary_energy_costs()

        # Factory cost including CAPEX OPEX
        # self.otuputs['cost_details:CAPEX_heat_tech'] = self.outputs[f'cost_details:Capex_{self.name}'] * self.crf
        # self.otuputs['cost_details:OPEX_heat_tech'] = self.outputs[f'cost_details:Opex_{self.name}'] * self.crf
        # self.outpucost_details[f'{}:{GlossaryEnergy.CO2TaxesValue}'] = self.outputs[f'cost_details:Capex_{self.name}'] * self.crf

        self.outputs[f'cost_details:{self.name}_factory'] = self.outputs[f'cost_details:Capex_{self.name}'] * \
                                                    (self.capital_recovery_factor + self.inputs['techno_infos_dict']['Opex_percentage'])

        if 'decommissioning_percentage' in self.inputs['techno_infos_dict']:
            self.outputs[f'cost_details:{self.name}_factory_decommissioning'] = self.outputs[f'cost_details:Capex_{self.name}'] * \
                                                                        self.inputs['techno_infos_dict'][
                                                                            'decommissioning_percentage']
            self.outputs[f'cost_details:{self.name}_factory'] += self.outputs[f'cost_details:{self.name}_factory_decommissioning']

        # Compute and add transport
        self.outputs['cost_details:transport'] = self.compute_transport()

        self.outputs[f'cost_details:{self.name}'] = self.outputs[f'cost_details:{self.name}_factory'] + self.outputs['cost_details:transport'] + \
                                       self.outputs['cost_details:energy_and_resources_costs']


        price_with_margin = self.outputs[f'cost_details:{self.name}'] * self.inputs[f'{GlossaryEnergy.MarginValue}:{GlossaryEnergy.MarginValue}'] / 100.0
        self.outputs[f'cost_details:{GlossaryEnergy.MarginValue}'] = price_with_margin - self.outputs[f'cost_details:{self.name}']
        self.outputs[f'cost_details:{self.name}'] = price_with_margin

        self.compute_carbon_emissions()
        self.compute_co2_tax()

        if 'nb_years_amort_capex' in self.inputs['techno_infos_dict']:
            self.nb_years_amort_capex = self.inputs['techno_infos_dict']['nb_years_amort_capex']

            # pylint: disable=no-member
            len_y = max(self.outputs[f'cost_details:{GlossaryEnergy.Years}']) + \
                    1 - min(self.outputs[f'cost_details:{GlossaryEnergy.Years}'])
            self.outputs[f'cost_details:{self.name}_factory_amort'] = (
                    np.tril(np.triu(np.ones((len_y, len_y)), k=0), k=self.nb_years_amort_capex - 1).transpose() *
                    np.array(self.outputs[f'cost_details:{self.name}_factory'] / self.nb_years_amort_capex)).T.sum(
                axis=0)
            # pylint: enable=no-member
            self.outputs[f'cost_details:{self.name}_amort'] = self.outputs[f'cost_details:{self.name}_factory_amort'] + \
                                                      self.outputs['cost_details:transport'] + \
                                                      self.outputs['cost_details:energy_and_resources_costs']
            self.outputs[f'cost_details:{self.name}_amort'] *= self.margin.loc[self.margin[GlossaryEnergy.Years]
                                                                       <= self.cost_details[
                                                                           GlossaryEnergy.Years].max()][
                                                           GlossaryEnergy.MarginValue] / 100.0
            self.outputs[f'cost_details:{self.name}_amort'] += self.outputs['cost_details:CO2_taxes_factory']

        # Add transport and CO2 taxes
        self.outputs[f'cost_details:{self.name}'] += self.outputs['cost_details:CO2_taxes_factory']

        if 'CO2_taxes_factory' in self.cost_details:
            self.outputs[f'cost_details:{self.name}_wotaxes'] = self.outputs[f'cost_details:{self.name}'] - \
                                                        self.outputs['cost_details:CO2_taxes_factory']
        else:
            self.outputs[f'cost_details:{self.name}_wotaxes'] = self.outputs[f'cost_details:{self.name}']

        # CAPEX in ($/MWh)
        self.outputs['cost_details:CAPEX_Part'] = self.outputs[f'cost_details:Capex_{self.name}'] * self.capital_recovery_factor

        # Running OPEX in ($/MWh)
        self.outputs['cost_details:OPEX_Part'] = self.outputs[f'cost_details:Capex_{self.name}'] * \
                                         (self.inputs['techno_infos_dict']['Opex_percentage']) + \
                                         self.outputs['cost_details:transport'] + self.outputs['cost_details:energy_and_resources_costs']
        # CO2 Tax in ($/MWh)
        self.outputs['cost_details:CO2Tax_Part'] = self.outputs[f'cost_details:{self.name}'] - \
                                           self.outputs[f'cost_details:{self.name}_wotaxes']

        return self.cost_details

    def compute_cost_of_resources_usage(self):
        """
        Cost of resource R = need of resource R x price of resource R
        """
        cost_of_resource_usage =  {
            GlossaryEnergy.Years: self.years,
        }
        for resource in self.inputs[GlossaryEnergy.ResourcesUsedForProductionValue]:
            cost_of_resource_usage[resource] = self.outputs[f"cost_details:{resource}_needs"] * self.inputs[f"{GlossaryEnergy.ResourcesPriceValue}:{resource}"]

        self.cost_of_resources_usage = pd.DataFrame(cost_of_resource_usage)

    def compute_cost_of_other_streams_usage(self):
        """Cost of usage of stream S per unit of current stream produced =
        Need of stream S by unit of production of current stream * Price per unit of production of stream S"""
        cost_of_streams_usage = {
            GlossaryEnergy.Years: self.years,
        }
        for stream in self.inputs[GlossaryEnergy.StreamsUsedForProductionValue]:
            cost_of_streams_usage[stream] = self.outputs[f"cost_details:{stream}_needs"] * self.inputs[f"{GlossaryEnergy.StreamPricesValue}:{stream}"]

        self.cost_of_streams_usage = pd.DataFrame(cost_of_streams_usage)

    @abstractmethod
    def compute_other_primary_energy_costs(self):
        '''
        Compute other energy costs which will depend on the techno reaction (elec for electrolysis or methane for SMR by example)
        '''
        self.compute_resources_needs()
        self.compute_cost_of_resources_usage()
        self.compute_other_streams_needs()
        self.compute_cost_of_other_streams_usage()
        self.compute_specifif_costs_of_technos()
        self.compute_streams_and_resources_costs()

    def compute_capex(self, invest_list, data_config):
        """
        Compute Capital expenditures (immobilisations)
        depending on the demand on the technology
        """
        expo_factor = self.compute_expo_factor(data_config)
        capex_init = self.check_capex_unity(data_config)
        if expo_factor != 0.0:
            capacity_factor_list = None
            if 'capacity_factor_at_year_end' in data_config \
                    and 'capacity_factor' in data_config:
                capacity_factor_list = np.linspace(data_config['capacity_factor'],
                                                   data_config['capacity_factor_at_year_end'],
                                                   len(invest_list))

            capex_calc_list = []
            invest_sum = self.inputs['initial_production'] * capex_init
            capex_year = capex_init

            for i, invest in enumerate(invest_list):

                # below 1M$ investments has no influence on learning rate for capex
                # decrease
                if invest_sum.real < 10.0 or i == 0.0:
                    capex_year = capex_init
                    # first capex calculation
                else:
                    np.seterr('raise')
                    if capacity_factor_list is not None:
                        try:
                            ratio_invest = ((invest_sum + invest) / invest_sum *
                                            (capacity_factor_list[i] / data_config['capacity_factor'])) \
                                           ** (-expo_factor)

                        except:
                            raise Exception(
                                f'invest is {invest} and invest sum {invest_sum} on techno {self.name}')

                    else:
                        np.seterr('raise')
                        try:
                            # try to calculate capex_year "normally"
                            ratio_invest = ((invest_sum + invest) /
                                            invest_sum) ** (-expo_factor)

                            pass

                        except FloatingPointError:
                            # set invest as a complex to calculate capex_year as a
                            # complex
                            ratio_invest = ((invest_sum + np.complex128(invest)) /
                                            invest_sum) ** (-expo_factor)

                            pass
                        np.seterr('warn')

                    # Check that the ratio is always above 0.95 but no strict threshold for
                    # optim is equal to 0.92 when tends to zero:
                    if ratio_invest.real < 0.95:
                        ratio_invest = 0.9 + \
                                       0.05 * np.exp(ratio_invest - 0.9)
                    capex_year = capex_year * ratio_invest

                capex_calc_list.append(capex_year)
                invest_sum += invest

            if 'maximum_learning_capex_ratio' in data_config:
                maximum_learning_capex_ratio = data_config['maximum_learning_capex_ratio']
            else:
                # if maximum learning_capex_ratio is not specified, the learning
                # rate on capex ratio cannot decrease the initial capex mor ethan
                # 10%
                maximum_learning_capex_ratio = 0.9

            capex_calc_list = capex_init * (maximum_learning_capex_ratio + (
                    1.0 - maximum_learning_capex_ratio) * np.array(capex_calc_list) / capex_init)
        else:
            capex_calc_list = capex_init * np.ones(len(invest_list))

        return capex_calc_list.tolist()

    def compute_expo_factor(self, data_config):

        progress_ratio = 1.0 - data_config['learning_rate']
        expo_factor = -np.log(progress_ratio) / np.log(2.0)

        return expo_factor

    def compute_capital_recovery_factor(self, data_config):
        """
        Compute annuity factor with the Weighted averaged cost of capital
        and the lifetime of the selected solution
        """
        wacc = self.inputs['techno_infos_dict']['WACC']

        capital_recovery_factor = (wacc * (1.0 + wacc) ** self.inputs['techno_infos_dict'][GlossaryEnergy.LifetimeName]) / ((1.0 + wacc) ** self.inputs['techno_infos_dict'][GlossaryEnergy.LifetimeName] - 1.0)

        return capital_recovery_factor

    def check_capex_unity(self, data_tocheck):
        """
        Put all capex in $/MWh
        """
        capex_init = None # intialize capex init variable
        if data_tocheck['Capex_init_unit'] == 'euro':
            # it is a total capital requirement TCR , need to be divided by
            # full_load_hours available power and capacity factor
            if data_tocheck['available_power_unit'] == 'kW':
                capex_init = data_tocheck['Capex_init'] * \
                             data_tocheck['euro_dollar'] / \
                             data_tocheck['full_load_hours'] / \
                             data_tocheck['capacity_factor'] / \
                             data_tocheck['available_power']
            elif data_tocheck['available_power_unit'] == 'm^3/h':
                capex_init = data_tocheck['Capex_init'] * \
                             data_tocheck['euro_dollar'] / \
                             data_tocheck['full_load_hours'] / \
                             data_tocheck['capacity_factor'] / \
                             data_tocheck['available_power'] / \
                             self.inputs['data_fuel_dict']['density'] / \
                             self.inputs['data_fuel_dict']['calorific_value']

            elif data_tocheck['available_power_unit'] == 'm^3':
                capex_init = data_tocheck['Capex_init'] * \
                             data_tocheck['euro_dollar'] / \
                             data_tocheck['available_power'] / \
                             self.inputs['data_fuel_dict']['density'] / \
                             self.inputs['data_fuel_dict']['calorific_value']
            elif data_tocheck['available_power_unit'] == 'kg/h':

                capex_init = data_tocheck['Capex_init'] * \
                             data_tocheck['euro_dollar'] / \
                             data_tocheck['full_load_hours'] / \
                             data_tocheck['capacity_factor'] / \
                             data_tocheck['available_power'] / \
                             self.inputs['data_fuel_dict']['calorific_value']
            elif data_tocheck['available_power_unit'] == 'kg/year':

                capex_init = data_tocheck['Capex_init'] * \
                             data_tocheck['euro_dollar'] / \
                             data_tocheck['available_power'] / \
                             self.inputs['data_fuel_dict']['calorific_value']
            else:
                available_power_unit = data_tocheck['available_power_unit']
                raise Exception(
                    f'The available power unity {available_power_unit} is not handled yet in techno_type')

        elif data_tocheck['Capex_init_unit'] == 'pounds':
            # it is a total capital requirement TCR , need to be divided by
            # full_load_hours available power and capacity factor

            if data_tocheck['available_power_unit'] == 'kg/h':
                if 'capacity_factor' in data_tocheck:
                    capex_init = data_tocheck['Capex_init'] * \
                                 data_tocheck['pounds_dollar'] / \
                                 data_tocheck['full_load_hours'] / \
                                 data_tocheck['capacity_factor'] / \
                                 data_tocheck['available_power'] / \
                                 self.inputs['data_fuel_dict']['calorific_value']
                else:
                    capex_init = data_tocheck['Capex_init'] * \
                                 data_tocheck['pounds_dollar'] / \
                                 data_tocheck['full_load_hours'] / \
                                 data_tocheck['available_power'] / \
                                 self.inputs['data_fuel_dict']['calorific_value']
        elif data_tocheck['Capex_init_unit'] == '$/kW':
            if 'capacity_factor' in data_tocheck:
                capex_init = data_tocheck['Capex_init'] / \
                             data_tocheck['full_load_hours'] / \
                             data_tocheck['capacity_factor']
            else:
                capex_init = data_tocheck['Capex_init'] / \
                             (data_tocheck['full_load_hours'])

        elif data_tocheck['Capex_init_unit'] == '$/kg':

            capex_init = data_tocheck['Capex_init'] / \
                         self.inputs['data_fuel_dict']['calorific_value']
        elif data_tocheck['Capex_init_unit'] == 'euro/kW':
            if 'capacity_factor' in data_tocheck:
                capex_init = data_tocheck['Capex_init'] * \
                             data_tocheck['euro_dollar'] / data_tocheck['full_load_hours'] / \
                             data_tocheck['capacity_factor']
            else:
                capex_init = data_tocheck['Capex_init'] * \
                             data_tocheck['euro_dollar'] / \
                             data_tocheck['full_load_hours']

        elif data_tocheck['Capex_init_unit'] == '$/kWh':
            capex_init = data_tocheck['Capex_init']
        elif data_tocheck['Capex_init_unit'] == '$/MWh':
            capex_init = data_tocheck['Capex_init'] / 1.0e3
        elif data_tocheck['Capex_init_unit'] == 'euro/ha':

            density_per_ha = data_tocheck['density_per_ha']

            if data_tocheck['density_per_ha_unit'] == 'm^3/ha':
                capex_init = data_tocheck['Capex_init'] * \
                             data_tocheck['euro_dollar'] / \
                             density_per_ha / \
                             data_tocheck['density'] / \
                             self.inputs['data_fuel_dict']['calorific_value']
            elif data_tocheck['density_per_ha_unit'] == 'kg/ha':
                capex_init = data_tocheck['Capex_init'] * \
                             data_tocheck['euro_dollar'] / \
                             density_per_ha / \
                             self.inputs['data_fuel_dict']['calorific_value']
        else:
            capex_unit = data_tocheck['Capex_init_unit']
            raise Exception(
                f'The CAPEX unity {capex_unit} is not handled yet in techno_type')
        if capex_init is None:
            raise Exception("Capex could not be computed, check used unity")
        # return capex in $/MWh
        return capex_init * 1.0e3

    def get_electricity_needs(self):
        """
        Get the electricity needs for 1 kwh of the energy producted by the technology
        """
        if self.inputs['techno_infos_dict']['elec_demand'] != 0.0:
            elec_need = self.check_energy_demand_unit(self.inputs['techno_infos_dict']['elec_demand_unit'],
                                                      self.inputs['techno_infos_dict']['elec_demand'])

        else:
            elec_need = 0.0

        return elec_need


    def check_energy_demand_unit(self, energy_demand_unit, energy_demand):
        """
        Compute energy demand in kWh/kWh or MWh/MWh (equivalent)
        """
        # Based on formula 1 of the Fasihi2016 PtL paper
        # self.data['demand']=self.scenario_demand['elec_demand']

        if energy_demand_unit == 'kWh/kWh':
            pass
        elif energy_demand_unit == 'kWh/m^3':
            energy_demand = energy_demand \
                            / self.inputs['data_fuel_dict']['density'] \
                            / self.inputs['data_fuel_dict']['calorific_value']
        elif energy_demand_unit == 'kWh/kg':
            energy_demand = energy_demand \
                            / self.inputs['data_fuel_dict']['calorific_value']
        else:
            raise Exception(
                f'The unity of the energy demand {energy_demand_unit} is not handled with conversions')

        return energy_demand

    def compute_efficiency(self):
        # Compute efficiency evolving in time or not
        if 'techno_evo_time' in self.inputs['techno_infos_dict'] and self.inputs['techno_infos_dict']['techno_evo_eff'] == 'yes':
            middle_evolution_year = self.inputs['techno_infos_dict']['techno_evo_time']
            efficiency_max = self.inputs['techno_infos_dict']['efficiency_max']
            efficiency_ini = self.inputs['techno_infos_dict']['efficiency']
            efficiency_slope = 1

            if 'efficiency evolution slope' in self.inputs['techno_infos_dict']:
                efficiency_slope = self.inputs['techno_infos_dict']['efficiency evolution slope']

            years = self.years - self.years[0]

            eff_list = [self.sigmoid_function(
                i, efficiency_max, efficiency_ini, middle_evolution_year, efficiency_slope) for i in years]
            efficiency = pd.Series(eff_list)

        else:
            efficiency = self.inputs['techno_infos_dict']['efficiency'] * np.ones_like(self.years)

        self.outputs['cost_details:efficiency'] = efficiency
        return efficiency
    
    def sigmoid_function(self, x, eff_max, eff_ini, x_shift, slope):
        x = x - x_shift
        # Logistic function
        return m.exp(slope * x) / (m.exp(slope * x) + 1) * (eff_max - eff_ini) + eff_ini

    def compute_transport(self):
        '''
        Need a more complex model for hydrogen transport
        Computed in $/kWh
        Transport cost is in $/kg
        Margin is in %
        Result must be in $/MWh
        '''

        # transport_cost = 5.43  # $/kg
        transport_cost = self.inputs[f'{GlossaryEnergy.TransportCostValue}:transport'] * \
                         self.inputs[f'{GlossaryEnergy.TransportMarginValue}:{GlossaryEnergy.MarginValue}'] / 100.0

        # Need to multiply by * 1.0e3 to put it in $/MWh$
        if 'calorific_value' in self.inputs['data_fuel_dict'].keys():
            return transport_cost / self.inputs['data_fuel_dict']['calorific_value']
        else:
            keys = list(self.inputs['data_fuel_dict'].keys())
            calorific_value = self.inputs['data_fuel_dict'][keys[
                0]]['calorific_value']
            return transport_cost / \
                   calorific_value

    def compute_carbon_emissions(self):
        '''
        carbon_intensity = CO2_from_production + co2_emissions_frominput_energies =  scope 1 + scope 2 emissions

        NB: scope 3 CO2 emissions of the techno are not considered in this method. See for instance
                CO2_per_use in climateeconomics/sos_wrapping/sos_wrapping_witness/post_proc_witness_optim/post_processing_witness_full.py
        '''
        self.compute_scope_1_emissions()
        self.compute_scope_2_emissions()

        self.carbon_intensity[self.name] = self.outputs['carbon_intensity:production'] + self.outputs['carbon_intensity:Scope 2']

    def compute_scope_1_emissions(self):
        if 'CO2_from_production' not in self.inputs['techno_infos_dict']:
            self.outputs['carbon_intensity:production'] = self.get_theoretical_co2_prod(
                unit='kg/kWh')
        elif self.inputs['techno_infos_dict']['CO2_from_production'] == 0.0:
            self.outputs['carbon_intensity:production'] = 0.0
        else:
            if self.inputs['techno_infos_dict']['CO2_from_production_unit'] == 'kg/kg':
                self.outputs['carbon_intensity:production'] = self.inputs['techno_infos_dict']['CO2_from_production'] / \
                                                      self.inputs['data_fuel_dict']['high_calorific_value']
            elif self.inputs['techno_infos_dict']['CO2_from_production_unit'] == 'kg/kWh':
                self.outputs['carbon_intensity:production'] = self.inputs['techno_infos_dict']['CO2_from_production']

    def compute_scope_2_emissions(self):
        """Computes the Scope 2 CO2 emissions : due to resources and energies usage"""
        self.compute_co2_emissions_from_ressources_usage()
        self.compute_co2_emissions_from_streams_usage()
        self.outputs['carbon_intensity:Scope 2'] = self.carbon_intensity_generic.drop(GlossaryEnergy.Years, axis=1).sum(axis=1)

    def compute_resources_needs(self):
        """To be overloaded when techno relies on resources"""
        pass

    def compute_other_streams_needs(self):
        """To be overloaded when techno uses other technos productions to produce its energy"""
        pass

    def compute_specifif_costs_of_technos(self):
        """To be overloaded when techno relies on resources"""
        self.specific_costs = pd.DataFrame({
            GlossaryEnergy.Years: self.years
        })

    def compute_co2_tax(self):
        '''
        CO2 taxes are in $/tCO2
        Need to be computed in $/MWh H2
        Only CO2 emitted from the technology is here taken into account to compute CO2 taxes
        If carbon emissions are negative then no negative CO2 taxes (use a clip on the column)
        '''
        CO2_taxes_kwh = self.inputs[f'{GlossaryEnergy.CO2TaxesValue}:{GlossaryEnergy.CO2Tax}'] * self.carbon_intensity[self.name].clip(0)
        self.outputs['cost_details:CO2_taxes_factory'] = CO2_taxes_kwh

    @abstractmethod
    def get_theoretical_co2_prod(self, unit='kg/kWh'):
        ''' 
        Get the theoretical CO2 production for a given technology,
        Need to be overloaded in each technology model (example in SMR)
        '''
        return 0.0

    def compute_primary_energy_production(self):
        '''
        Compute the primary energy production for each technology
        (primary energy is H2 for H2 techno , Kero for Kero techno ...etc) 
        '''
        # First compute the initial aging distribution with the initial
        # production found in the techno discipline
        # self.compute_initial_aging_distribution()

        # Compute the aging distribution over the years of study to determine the total production over the years
        # This function also erase old factories from the distribution
        self.compute_aging_distribution_production()

        # Finally compute the production by summing all aged production for
        # each year

        age_distrib_prod_sum = self.age_distrib_prod_df.groupby([GlossaryEnergy.Years], as_index=False).agg(
            {f'distrib_prod ({self.product_unit})': 'sum'}
        )
        if f'{self.energy_name} ({self.product_unit})' in self.production_detailed:
            del self.outputs[f'production_detailed:{self.energy_name} ({self.product_unit})']

        self.production_detailed = pd.merge(self.production_detailed, age_distrib_prod_sum, how='left',
                                            on=GlossaryEnergy.Years).rename(
            columns={
                f'distrib_prod ({self.product_unit})': f'{self.energy_name} ({self.product_unit})'}).fillna(
            0.0)

    def compute_primary_installed_power(self):


        if 'full_load_hours' in self.inputs['techno_infos_dict']:
            full_load_hours = self.inputs['techno_infos_dict']['full_load_hours']
        else:
            # print(
            #     f'The full_load_hours data is not set for {self.name} : default = 8760.0 hours, full year hours  ')
            full_load_hours = 8760.0

        production_from_invest = self.compute_prod_from_invest()

        # Conversion from TWh to MW
        self.installed_power['new_power_production'] = production_from_invest.loc[production_from_invest[
                                                                                      GlossaryEnergy.Years] == self.years, 'prod_from_invest'] / full_load_hours * 1000
        self.installed_power['total_installed_power'] = self.production_detailed[
                                                            f'{self.energy_name} ({self.product_unit})'] / full_load_hours * 1000
        self.installed_power['removed_power_production'] = np.zeros(len(self.years))

        power_production_dict = self.installed_power.to_dict()

        for year in self.years[1:]:
            power_production_dict['removed_power_production'][year - power_production_dict[GlossaryEnergy.Years][0]] = \
                power_production_dict['total_installed_power'][
                    year - 1 - power_production_dict[GlossaryEnergy.Years][0]] \
                - power_production_dict['total_installed_power'][year - power_production_dict[GlossaryEnergy.Years][0]] \
                + power_production_dict['new_power_production'][year - power_production_dict[GlossaryEnergy.Years][0]]
        self.installed_power = pd.DataFrame.from_dict(power_production_dict)

    def compute_aging_distribution_production(self):
        '''
        Compute the aging distribution production of primary energy for years of study
        Start with the initial distribution and add a year on the age each year 
        Add also the yearly production regarding the investment
        All productions older than the lifetime are removed from the dataframe  
        '''
        # To break the object link with initial distrib
        aging_distrib_year_df = pd.DataFrame(
            {'age': self.outputs['initial_age_distrib:age']})
        aging_distrib_year_df[f'distrib_prod ({self.product_unit})'] = self.outputs['initial_age_distrib:distrib'] * self.inputs['initial_production'] / 100.0

        production_from_invest = self.compute_prod_from_invest()

        # get the whole dataframe for new production with one line for each
        # year at each age
        # concatenate tuple to get correct df to mimic the old year loop
        len_years = len(self.years)
        range_years = np.arange(
            self.year_start, self.year_end + len_years)

        year_array = np.concatenate(
            tuple(range_years[i:i + len_years] for i in range(len_years)))
        age_array = np.concatenate(tuple(np.ones(
            len_years) * (len_years - i) for i in range(len_years, 0, -1)))
        prod_array = production_from_invest['prod_from_invest'].tolist(
        ) * len_years

        new_prod_aged = pd.DataFrame({GlossaryEnergy.Years: year_array, 'age': age_array,
                                      f'distrib_prod ({self.product_unit})': prod_array})

        # get the whole dataframe for old production with one line for each
        # year at each age
        year_array = np.array([[year] * len(aging_distrib_year_df)
                               for year in self.years]).flatten()
        age_values = aging_distrib_year_df['age']
        age_array = np.concatenate(tuple(
            age_values + i for i in range(len_years)))
        prod_array = aging_distrib_year_df[f'distrib_prod ({self.product_unit})'].tolist(
        ) * len_years

        old_prod_aged = pd.DataFrame({GlossaryEnergy.Years: year_array, 'age': age_array,
                                      f'distrib_prod ({self.product_unit})': prod_array})

        # Concat the two created df
        self.age_distrib_prod_df = pd.concat(
            [new_prod_aged, old_prod_aged], ignore_index=True)

        self.age_distrib_prod_df = self.age_distrib_prod_df.loc[
            # Suppress all lines where age is higher than lifetime
            (self.age_distrib_prod_df['age'] <
             self.inputs['techno_infos_dict'][GlossaryEnergy.LifetimeName])
            # Suppress all lines where age is higher than lifetime
            & (self.age_distrib_prod_df[GlossaryEnergy.Years] < self.year_end + 1)
            # Fill Nan with zeros and suppress all zeros
            & (self.age_distrib_prod_df[f'distrib_prod ({self.product_unit})'] != 0.0)
            ]
        # Fill Nan with zeros
        self.age_distrib_prod_df.fillna(0.0, inplace=True)

    def compute_prod_from_invest(self):
        '''
        Compute the energy production of a techno from investment in TWh
        Add a delay for factory construction
        '''

        years_before_year_start = np.arange(self.year_start - self.inputs['techno_infos_dict'][GlossaryEnergy.ConstructionDelay], self.year_start)
        invest_before_year_start = self.invest_before_ystart[GlossaryEnergy.InvestValue]
        capex_year_start = self.cost_details.loc[self.outputs[f'cost_details:{GlossaryEnergy.Years}'] == self.year_start, f'Capex_{self.name}'][0]
        invest_before_year_start_df = pd.DataFrame({
            GlossaryEnergy.Years: years_before_year_start,
            GlossaryEnergy.InvestValue: invest_before_year_start,
            f'Capex_{self.name}': capex_year_start
         })
        invests_after_year_start_df = self.cost_details[[GlossaryEnergy.Years, GlossaryEnergy.InvestValue, f'Capex_{self.name}']].copy()
        prod_from_invests_df = pd.concat([invest_before_year_start_df, invests_after_year_start_df], ignore_index=True) if len(invest_before_year_start) > 0 else invests_after_year_start_df
        # Need prod_from invest in TWh we have M$ and $/MWh  M$/($/MWh)= TWh

        production_from_invests = prod_from_invests_df[GlossaryEnergy.InvestValue] / \
                                                     prod_from_invests_df[f'Capex_{self.name}']
        prod_from_invests_df['prod_from_invest'] = production_from_invests
        prod_from_invests_df[GlossaryEnergy.Years] += self.inputs['techno_infos_dict'][GlossaryEnergy.ConstructionDelay]
        prod_from_invests_df = prod_from_invests_df[prod_from_invests_df[GlossaryEnergy.Years] <= self.year_end]

        return prod_from_invests_df

    def get_mean_age_over_years(self):

        self.outputs[f'mean_age_df:{GlossaryEnergy.Years}'] = self.years

        self.age_distrib_prod_df['age_x_prod'] = self.age_distrib_prod_df['age'] * \
                                                 self.age_distrib_prod_df[f'distrib_prod ({self.product_unit})']

        mean_age_df['mean age'] = self.age_distrib_prod_df.groupby(
            [GlossaryEnergy.Years], as_index=False).agg({'age_x_prod': 'sum'})['age_x_prod'] / self.production_woratio[
                                      f'{self.energy_name} ({self.product_unit})']
        mean_age_df.replace([np.inf, -np.inf], np.nan, inplace=True)
        mean_age_df.fillna(0.0, inplace=True)

        self.mean_age_df = mean_age_df
        return mean_age_df

    def compute_land_use(self):
        ''' Set the compute land use dataframe

            to be overloaded in sub class
        '''

        self.land_use[f'{self.name} (Gha)'] = 0.0

    def compute_ghg_emissions(self, GHG_type, related_to='prod'):
        '''
        Method to compute GHG emissions for any techno type and any GHG type
        The proposed V0 only depends on production.
        Equation is taken from the GAINS model
        https://previous.iiasa.ac.at/web/home/research/researchPrograms/air/IR54-GAINS-CH4.pdf

        emission_factor is in Mt/TWh

        If related_to = 'prod' that means that we use main production to compute GHG emissions
        if related_to = other that means that we use the other column in consumption to compute_ghg_emissions
        '''
        if f'{GHG_type}_emission_factor' not in self.inputs['techno_infos_dict']:
            raise Exception(
                f'The variable {GHG_type}_emission_factor should be in the techno dict to compute {GHG_type} emissions for {self.name}')
        emission_factor = self.inputs['techno_infos_dict'][f'{GHG_type}_emission_factor']

        if related_to == 'prod':
            self.outputs[f'production_detailed:{GHG_type} ({GlossaryEnergy.mass_unit})'] = emission_factor * \
                                                                         self.outputs[f'production_detailed:{self.energy_name} ({self.product_unit})']
        else:
            self.outputs[f'production_detailed:{GHG_type} ({GlossaryEnergy.mass_unit})'] = emission_factor * \
                                                                         self.outputs[f'consumption_detailed:{related_to} ({self.product_unit})']

    def rescale_outputs(self):
        self.production = copy(self.production_detailed)
        self.consumption = copy(self.consumption_detailed)

        for column in self.consumption_detailed.columns:
            if column == GlossaryEnergy.Years:
                continue
            self.consumption[column] = self.consumption[column] / self.inputs['scaling_factor_techno_consumption']
        for column in self.production_detailed.columns:
            if column == GlossaryEnergy.Years:
                continue
            self.production[column] = self.production[column] / self.inputs['scaling_factor_techno_production']

        for column in self.consumption_woratio.columns:
            if column == GlossaryEnergy.Years:
                continue
            self.consumption_woratio[column] = self.consumption_woratio[
                                                   column] / self.inputs['scaling_factor_techno_consumption']
        for column in self.production_woratio.columns:
            if column == GlossaryEnergy.Years:
                continue
            self.production_woratio[column] = self.production_woratio[
                                                  column] / self.inputs['scaling_factor_techno_production']

    def apply_utilisation_ratio(self):
        """
        Apply utilisation ratio percentage to
        - consumption
        - production
        """
        for column in self.consumption_detailed.columns:
            if column == GlossaryEnergy.Years:
                continue
            self.consumption_detailed[column] = self.consumption_detailed[column] * self.inputs[f'{GlossaryEnergy.UtilisationRatioValue}:{GlossaryEnergy.UtilisationRatioValue}'] / 100.

        for column in self.production_detailed.columns:
            if column == GlossaryEnergy.Years:
                continue
            self.production_detailed[column] = self.production_detailed[column] * self.inputs[f'{GlossaryEnergy.UtilisationRatioValue}:{GlossaryEnergy.UtilisationRatioValue}'] / 100.

    def store_consumption_and_production_and_landuse_wo_ratios(self):
        """
        Store following dataframe values before applying any ratios (utilisation ratio or resources ratios)
        - production
        - consumption
        - land use
        """
        self.production_woratio = copy(self.production_detailed)
        self.consumption_woratio = copy(self.consumption_detailed)
        self.land_use_woratio = copy(self.land_use)

    def compute_streams_and_resources_costs(self):
        all_costs = self.cost_of_resources_usage[self.inputs[GlossaryEnergy.ResourcesUsedForProductionValue]].sum(axis=1) + \
                    self.cost_of_streams_usage[self.inputs[GlossaryEnergy.StreamsUsedForProductionValue]].sum(axis=1) + \
                    self.specific_costs.drop(GlossaryEnergy.Years, axis=1).sum(axis=1)
        self.outputs['cost_details:energy_and_resources_costs'] = all_costs

    def compute_co2_emissions_from_ressources_usage(self):
        """Computes the co2 emissions due to resources usage"""
        for resource in self.inputs[GlossaryEnergy.ResourcesUsedForProductionValue]:
            self.outputs[f'carbon_intensity_generic:{resource}'] = self.outputs[f"cost_details:{resource}_needs"] * self.inputs[f'{GlossaryEnergy.RessourcesCO2EmissionsValue}:{resource}']

    def compute_co2_emissions_from_streams_usage(self):
        """Computes the co2 emissions due to streams usage"""
        for stream in self.inputs[GlossaryEnergy.StreamsUsedForProductionValue]:
            self.outputs[f'carbon_intensity_generic:{stream}'] = self.outputs[f"cost_details:{stream}_needs"] * self.inputs[f'{GlossaryEnergy.StreamsCO2EmissionsValue}:{stream}']

    def compute_new_power_production_resource_consumption(self):
        """
        Here is computed the resource consumption by the building of new plants.

        Resource R consumption (year) = Newly installed Power Production in MW (year) * Resource R needs (in Mt) for building 1 MW of installed power.
        """
        for resource in self.inputs[GlossaryEnergy.ResourcesUsedForBuildingValue]:
            self.outputs[f"consumption_detailed:{resource} ({GlossaryEnergy.mass_unit})"] =\
                self.inputs['techno_infos_dict'][f"{resource}_needs"] * self.installed_power["new_power_production"]

    def compute(self, inputs_dict):
        self.configure_parameters_update(inputs_dict)
        # -- compute informations
        self.compute_initial_age_distribution()
        self.compute_price()
        self.compute_initial_plants_historical_prod()
        self.compute_primary_energy_production()
        self.compute_land_use()
        self.compute_resource_consumption()
        self.compute_streams_consumption()
        self.compute_byproducts_production()
        self.compute_primary_installed_power()
        self.compute_new_power_production_resource_consumption()

        # ratios : utilisation & resources
        self.store_consumption_and_production_and_landuse_wo_ratios()
        self.apply_utilisation_ratio()
        self.select_resources_ratios()
        self.apply_resources_ratios(self.inputs[GlossaryEnergy.BoolApplyRatio])

        self.compute_capital()
        self.get_mean_age_over_years()

        self.rescale_outputs()

    def compute_initial_age_distribution(self):
        initial_value = 1
        decay_rate = self.inputs['techno_infos_dict'][GlossaryEnergy.InitialPlantsAgeDistribFactor]
        n_year = self.inputs['techno_infos_dict'][GlossaryEnergy.LifetimeName] - 1
        
        total_sum = sum(initial_value * (decay_rate ** i) for i in range(n_year))
        distribution = [(initial_value * (decay_rate ** i) / total_sum) * 100 for i in range(n_year)]
        distrib = np.flip(distribution)
        self.outputs["initial_age_distrib:age"] = np.arange(1, self.inputs['techno_infos_dict'][GlossaryEnergy.LifetimeName]),
        self.outputs["initial_age_distrib:distrib"] = distrib

    def compute_initial_plants_historical_prod(self):
        energy = self.outputs['initial_age_distrib:distrib'] / 100.0 * self.inputs['initial_production']

        self.initial_plants_historical_prod = pd.DataFrame({
            GlossaryEnergy.Years: self.year_start - self.outputs['initial_age_distrib:age'],
            f'energy ({self.product_unit})': energy,
        })

        self.initial_plants_historical_prod.sort_values(GlossaryEnergy.Years, inplace=True)
        self.initial_plants_historical_prod[f'cum energy ({self.product_unit})'] = self.initial_plants_historical_prod[f'energy ({self.product_unit})'].cumsum()