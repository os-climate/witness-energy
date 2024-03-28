'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/02-2023/11/17 Copyright 2023 Capgemini

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

from climateeconomics.core.core_resources.resource_mix.resource_mix import ResourceMixModel
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.glossaryenergy import GlossaryEnergy
from sostrades_core.tools.base_functions.exp_min import compute_dfunc_with_exp_min, compute_func_with_exp_min
from sostrades_core.tools.cst_manager.func_manager_common import cons_smooth_maximum_vect, \
    get_dcons_smooth_dvariable_vect
from sostrades_core.tools.cst_manager.func_manager_common import smooth_maximum_vect, get_dsmooth_dvariable_vect
from sostrades_core.tools.cst_manager.func_manager_common import soft_maximum_vect, get_dsoft_maximum_vect


class TechnoType:
    """
    Class for energy production technology type
    """

    energy_name = 'energy'
    min_value_invest = 1.e-12

    def __init__(self, name):
        self.cost_of_resources_usage = None
        self.years = None
        self.cost_details = None
        self.production_detailed = None
        self.consumption_detailed = None
        self.aging_distribution = None
        self.land_use = None
        self.year_start = None
        self.year_end = None
        self.margin = None
        self.maturity = None
        self.invest_before_ystart = None
        self.is_apply_resource_ratio = None
        self.ratio_available_resource = None
        self.CO2_taxes = None
        self.resources_prices = None
        self.invest_level = None
        self.production_detailed = None
        self.is_apply_resource_ratio = None
        self.ratio_available_resource = None
        self.transport_cost = None
        self.transport_margin = None
        self.production_detailed = None
        self.dprod_dinvest = None
        self.dprod_list_dcapex_list = None
        self.dpower_list_dinvest_list = None
        self.mean_age_df = None
        self.production = None
        self.consumption = None
        self.name = name
        self.resources_used_for_production = []

        self.invest_years = None  # Investment per year
        self.prices = None  # Input energy price
        self.energy_CO2_emissions = None
        # -- Outputs attributes computed by run method
        # -- Contains: energy produced, price, CO2 emissions, energy consumption (per energy type)
        self.techno_out_df = None  # Technology outputs dataframe

        self.techno_infos_dict = {}
        self.data_energy_dict = {}
        self.initial_production = None
        self.age_distrib_prod_df = None
        self.initial_age_distrib = None

        self.resources_price = None
        self.resources_CO2_emissions = None
        self.carbon_intensity = None
        self.product_energy_unit = 'TWh'
        self.mass_unit = 'Mt'
        self.capital_recovery_factor = None
        self.nb_years_amort_capex = 10
        self.scaling_factor_invest_level = None
        self.scaling_factor_techno_production = None
        self.scaling_factor_techno_consumption = None
        # self.product_energy_unit_billion = 'TWh'
        self.all_streams_demand_ratio = None
        self.is_stream_demand = False
        self.is_resource_ratio = False
        self.is_applied_resource_ratios = None
        self.smooth_type = None
        self.ratio_df = None
        self.non_use_capital = None
        self.techno_capital = None
        self.applied_ratio = None
        self.installed_power = None
        self.utilisation_ratio = None

        self.production_woratio = None
        self.consumption_woratio = None
        self.land_use_woratio = None
        self.construction_resource_list = ['copper_resource']

    def check_outputs_dict(self, biblio_data):
        '''
        Check if outputs are coherent
        Biblio & references at https://docs.google.com/presentation/d/1r4JVNxEEClfjBGt27wdnzil8jaRt_TwnCMCQ76ew8o4/edit#slide=id.gc29c52ae34_0_96
        '''
        # Init price check
        price = self.cost_details[self.name][0]
        max_price = float(biblio_data['max_price'])
        min_price = float(biblio_data['min_price'])
        price_unit = biblio_data['price_unit'].item()
        # Unit check
        if price_unit == '$/MWh':
            pass
        elif price_unit == '$/kWh':
            price /= 1000
        else:
            raise Exception(
                f'Price unit {price_unit} is not valid for {self.name}')

        if not min_price <= price <= max_price:
            raise Exception(
                f'Price {price} {price_unit} is outside the biblio price range {min_price} - {max_price} for {self.name}')
        # Init prod check
        product = biblio_data['sos_name'].item().split('.')[0]
        production = self.production_detailed[f'{product} (TWh)'][0]
        biblio_init_prod = float(biblio_data['init_prod'])
        tolerance = float(biblio_data['prod_tolerance'])
        prod_unit = biblio_data['prod_unit'].item()
        # Unit check
        if prod_unit == 'TWh':
            pass
        elif prod_unit == 'MWh':
            production /= 1000
        else:
            raise Exception(
                f'Production unit {prod_unit} is not valid for {self.name}')
        if tolerance > 1:
            tolerance /= 100

        border_inf = biblio_init_prod - biblio_init_prod * tolerance
        border_sup = biblio_init_prod + biblio_init_prod * tolerance
        if not border_inf < production < border_sup:
            raise Exception(
                f'Initial production {production} {prod_unit} is outside the biblio production {border_inf} - {border_sup} range for {self.name}')

    def init_dataframes(self):
        '''
        Init dataframes with years
        '''
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.cost_details = pd.DataFrame({GlossaryEnergy.Years: self.years})
        self.production_detailed = pd.DataFrame({GlossaryEnergy.Years: self.years})
        self.consumption_detailed = pd.DataFrame({GlossaryEnergy.Years: self.years})

        self.aging_distribution = pd.DataFrame({GlossaryEnergy.Years: self.years})

        self.carbon_intensity = pd.DataFrame({GlossaryEnergy.Years: self.years})

        self.land_use = pd.DataFrame({GlossaryEnergy.Years: self.years})

        self.all_streams_demand_ratio = pd.DataFrame({GlossaryEnergy.Years: self.years})

        self.non_use_capital = pd.DataFrame({GlossaryEnergy.Years: self.years})
        self.techno_capital = pd.DataFrame({GlossaryEnergy.Years: self.years})

        self.installed_power = pd.DataFrame({GlossaryEnergy.Years: self.years})

    def configure_parameters(self, inputs_dict):
        '''
        Configure with inputs_dict from the discipline
        '''

        self.year_start = inputs_dict[GlossaryEnergy.YearStart]  # year start
        self.year_end = inputs_dict[GlossaryEnergy.YearEnd]  # year end

        self.init_dataframes()
        self.techno_infos_dict = inputs_dict['techno_infos_dict']

        if inputs_dict[GlossaryEnergy.MarginValue] is not None:
            self.margin = inputs_dict[GlossaryEnergy.MarginValue].loc[
                inputs_dict[GlossaryEnergy.MarginValue][GlossaryEnergy.Years]
                <= self.year_end]

        if 'maturity' in self.techno_infos_dict:
            self.maturity = self.techno_infos_dict['maturity']

        self.initial_production = inputs_dict['initial_production']
        self.initial_age_distrib = inputs_dict['initial_age_distrib']
        if self.initial_age_distrib is not None and self.initial_age_distrib['distrib'].sum() > 100.001 or \
                self.initial_age_distrib[
                    'distrib'].sum() < 99.999:
            sum_distrib = self.initial_age_distrib['distrib'].sum()
            raise Exception(
                f'The distribution sum is not equal to 100 % : {sum_distrib}')

        # invest level from G$ to M$
        self.scaling_factor_invest_level = inputs_dict['scaling_factor_invest_level']
        self.invest_before_ystart = inputs_dict[GlossaryEnergy.InvestmentBeforeYearStartValue] * \
                                    self.scaling_factor_invest_level

        self.configure_energy_data(inputs_dict)

        self.configure_transport_data(
            inputs_dict[GlossaryEnergy.TransportCostValue], inputs_dict[GlossaryEnergy.TransportMarginValue])

        self.scaling_factor_techno_consumption = inputs_dict['scaling_factor_techno_consumption']
        self.scaling_factor_techno_production = inputs_dict['scaling_factor_techno_production']
        self.is_stream_demand = inputs_dict['is_stream_demand']
        self.is_apply_resource_ratio = inputs_dict['is_apply_resource_ratio']
        self.smooth_type = inputs_dict['smooth_type']
        if self.is_stream_demand:
            self.all_streams_demand_ratio = inputs_dict[GlossaryEnergy.AllStreamsDemandRatioValue]
        if self.is_apply_resource_ratio:
            self.ratio_available_resource = inputs_dict[ResourceMixModel.RATIO_USABLE_DEMAND]

        if inputs_dict[GlossaryEnergy.UtilisationRatioValue] is not None:
            self.utilisation_ratio = inputs_dict[GlossaryEnergy.UtilisationRatioValue][
                GlossaryEnergy.UtilisationRatioValue].values

        self.resources_used_for_production = inputs_dict[GlossaryEnergy.ResourcesUsedForProductionValue]

    def configure_parameters_update(self, inputs_dict):
        '''
        Configure with inputs_dict from the discipline
        '''
        self.CO2_taxes = inputs_dict[GlossaryEnergy.CO2TaxesValue]
        self.configure_energy_data(inputs_dict)
        self.resources_prices = inputs_dict[GlossaryEnergy.ResourcesPriceValue].loc[
            inputs_dict[GlossaryEnergy.ResourcesPriceValue][GlossaryEnergy.Years]
            <= self.year_end]
        self.prices = inputs_dict[GlossaryEnergy.EnergyPricesValue]

        self.invest_level = inputs_dict[GlossaryEnergy.InvestLevelValue].loc[
            inputs_dict[GlossaryEnergy.InvestLevelValue][GlossaryEnergy.Years]
            <= self.year_end]
        # invest level from G$ to M$
        self.scaling_factor_invest_level = inputs_dict['scaling_factor_invest_level']
        self.invest_level[GlossaryEnergy.InvestValue] = self.invest_level[GlossaryEnergy.InvestValue] * \
                                                        self.scaling_factor_invest_level

        self.scaling_factor_techno_consumption = inputs_dict['scaling_factor_techno_consumption']
        self.scaling_factor_techno_production = inputs_dict['scaling_factor_techno_production']
        self.resources_CO2_emissions = inputs_dict[GlossaryEnergy.RessourcesCO2EmissionsValue]
        self.energy_CO2_emissions = inputs_dict[GlossaryEnergy.EnergyCO2EmissionsValue]
        self.production_detailed = pd.DataFrame({GlossaryEnergy.Years: self.years})
        self.installed_power = pd.DataFrame({GlossaryEnergy.Years: self.years})
        self.ratio_df = pd.DataFrame({GlossaryEnergy.Years: self.years})
        self.is_stream_demand = inputs_dict['is_stream_demand']
        self.is_apply_resource_ratio = inputs_dict['is_apply_resource_ratio']
        self.smooth_type = inputs_dict['smooth_type']
        if self.is_stream_demand:
            self.all_streams_demand_ratio = inputs_dict[GlossaryEnergy.AllStreamsDemandRatioValue].loc[
                inputs_dict[GlossaryEnergy.AllStreamsDemandRatioValue][GlossaryEnergy.Years]
                <= self.year_end]
        if self.is_apply_resource_ratio:
            self.ratio_available_resource = inputs_dict[ResourceMixModel.RATIO_USABLE_DEMAND]

        self.utilisation_ratio = inputs_dict[GlossaryEnergy.UtilisationRatioValue][
            GlossaryEnergy.UtilisationRatioValue].values
        self.techno_infos_dict = inputs_dict['techno_infos_dict']

    def configure_energy_data(self, inputs_dict):
        '''
        Configure energy data by reading the data_energy_dict in the right Energy class
        Overloaded for each energy type
        '''
        self.data_energy_dict = inputs_dict['data_fuel_dict']

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ?
        """

    def compute_consumption_and_installed_power(self):
        """
        Compute the power installed (W) of the technology for a given investment
        """

    def select_resources_ratios(self):
        """! Select the ratios to be added to ratio_df and convert it from % to normal
             This function is to be overloaded in specific techno_models
        """
        ratio_df = pd.DataFrame()
        if self.is_stream_demand:
            ratio_df = pd.concat(
                [ratio_df, self.all_streams_demand_ratio], ignore_index=True)

        if self.is_apply_resource_ratio:
            for resource in EnergyMix.RESOURCE_LIST:
                ratio_df[resource] = self.ratio_available_resource[resource].values
        for col in ratio_df.columns:
            ratio_df[col] = ratio_df[col].values / 100.0
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
                if self.smooth_type == 'smooth_max':
                    ratio_values = - \
                        smooth_maximum_vect(-self.ratio_df[elements].values)
                elif self.smooth_type == 'soft_max':
                    ratio_values = - \
                        soft_maximum_vect(-self.ratio_df[elements].values)
                elif self.smooth_type == 'cons_smooth_max':
                    ratio_values = - \
                        cons_smooth_maximum_vect(-self.ratio_df[elements].values)
                else:
                    raise Exception('Unknown smooth_type')

                min_ratio_name = self.ratio_df[elements].columns[np.argmin(
                    self.ratio_df[elements].values, axis=1)].values

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
                self.production_detailed[col] = self.production_detailed[col].values * \
                                                ratio_values
        for col in self.consumption_detailed.columns:
            if col not in [GlossaryEnergy.Years] + [f'{resource} (Mt)' for resource in self.construction_resource_list]:
                self.consumption_detailed[col] = self.consumption_detailed[col].values * \
                                                 ratio_values
            elif col in [f'{resource} (Mt)' for resource in self.construction_resource_list]:
                ratio_construction_values = 1
                self.consumption_detailed[col] = self.consumption_detailed[col].values * \
                                                 ratio_construction_values
        for col in self.land_use.columns:
            if col != GlossaryEnergy.Years:
                self.land_use[col] = self.land_use[col].values * \
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
        self.techno_capital[GlossaryEnergy.Capital] = self.cost_details[f'Capex_{self.name}'].values \
                                                      * self.production_woratio[
                                                          f'{self.energy_name} ({self.product_energy_unit})'].values \
                                                      / self.scaling_factor_invest_level

        self.non_use_capital[self.name] = self.techno_capital[GlossaryEnergy.Capital].values * (
                1.0 - self.applied_ratio['applied_ratio'].values * self.utilisation_ratio / 100.)

    def compute_dnon_usecapital_dinvest(self, dcapex_dinvest, dprod_dinvest):
        '''
        Compute the gradient of non_use capital by invest_level

        dnon_usecapital_dinvest = dcapex_dinvest*prod(1-ratio) + dprod_dinvest*capex(1-ratio) - dratiodinvest*prod*capex
        dratiodinvest = 0.0
        '''

        dtechnocapital_dinvest = (dcapex_dinvest * self.scaling_factor_techno_production * self.production_woratio[
            f'{self.energy_name} ({self.product_energy_unit})'].values.reshape((len(self.years), 1)) +
                                  dprod_dinvest * self.cost_details[f'Capex_{self.name}'].values.reshape(
                    (len(self.years), 1)))

        dnon_usecapital_dinvest = dtechnocapital_dinvest * (
                1.0 - self.applied_ratio['applied_ratio'].values).reshape((len(self.years), 1))

        # we do not divide by / self.scaling_factor_invest_level because invest
        # and non_use_capital are in G$
        return dnon_usecapital_dinvest, dtechnocapital_dinvest

    def compute_dnon_usecapital_dratio(self, dapplied_ratio_dratio):
        '''
        Compute the non_use_capital gradient vs all_stream_demand_ratio 
        In input we already have the gradient of applied_ratio on stream_demand_ratio
        '''
        mult_vect = self.cost_details[f'Capex_{self.name}'].values * \
                    self.production_woratio[f'{self.energy_name} ({self.product_energy_unit})'].values
        dnon_use_capital_dratio = -dapplied_ratio_dratio * mult_vect
        return np.diag(dnon_use_capital_dratio / 100.)

    def compute_price(self):
        """
        Compute the detail price of the technology
        """

        invest_inputs = self.invest_level.loc[self.invest_level[GlossaryEnergy.Years]
                                              <= self.cost_details[GlossaryEnergy.Years].max()][
            GlossaryEnergy.InvestValue].values
        # Maximize with smooth exponential
        self.cost_details[GlossaryEnergy.InvestValue] = compute_func_with_exp_min(
            invest_inputs, self.min_value_invest)

        self.cost_details[f'Capex_{self.name}'] = self.compute_capex(
            self.cost_details[GlossaryEnergy.InvestValue].values, self.techno_infos_dict)

        self.capital_recovery_factor = self.compute_capital_recovery_factor(self.techno_infos_dict)

        self.compute_efficiency()

        self.prices = self.prices.loc[self.prices[GlossaryEnergy.Years]
                                      <= self.cost_details[GlossaryEnergy.Years].max()]
        self.cost_details['energy_costs'] = self.compute_other_primary_energy_costs()

        # Factory cost including CAPEX OPEX
        # self.cost_details['CAPEX_heat_tech'] = self.cost_details[f'Capex_{self.name}'] * self.crf
        # self.cost_details['OPEX_heat_tech'] = self.cost_details[f'Opex_{self.name}'] * self.crf
        # self.cost_details[GlossaryEnergy.CO2TaxesValue] = self.cost_details[f'Capex_{self.name}'] * self.crf

        self.cost_details[f'{self.name}_factory'] = self.cost_details[f'Capex_{self.name}'] * \
                                                    (self.capital_recovery_factor + self.techno_infos_dict['Opex_percentage'])

        if 'decommissioning_percentage' in self.techno_infos_dict:
            self.cost_details[f'{self.name}_factory_decommissioning'] = self.cost_details[f'Capex_{self.name}'] * \
                                                                        self.techno_infos_dict[
                                                                            'decommissioning_percentage']
            self.cost_details[f'{self.name}_factory'] += self.cost_details[f'{self.name}_factory_decommissioning']

        # Compute and add transport
        self.cost_details['transport'] = self.compute_transport()

        self.cost_details[self.name] = self.cost_details[f'{self.name}_factory'] + self.cost_details['transport'] + \
                                       self.cost_details['energy_costs']

        # Add margin in %
        # self.cost_details[GlossaryEnergy.MarginValue] = self.cost_details[self.name] * self.margin.loc[self.margin[GlossaryEnergy.Years]<= self.cost_details[GlossaryEnergy.Years].max()][GlossaryEnergy.MarginValue].values / 100.0
        # self.cost_details[self.name] += self.cost_details[GlossaryEnergy.MarginValue]

        price_with_margin = self.cost_details[self.name] * self.margin.loc[self.margin[GlossaryEnergy.Years]
                                                                           <= self.cost_details[
                                                                               GlossaryEnergy.Years].max()][
            GlossaryEnergy.MarginValue].values / 100.0
        self.cost_details[GlossaryEnergy.MarginValue] = price_with_margin - self.cost_details[self.name]
        self.cost_details[self.name] = price_with_margin

        # Compute and add CO2 taxes
        self.cost_details['CO2_taxes_factory'] = self.compute_co2_tax()

        if 'nb_years_amort_capex' in self.techno_infos_dict:
            self.nb_years_amort_capex = self.techno_infos_dict['nb_years_amort_capex']

            # pylint: disable=no-member
            len_y = max(self.cost_details[GlossaryEnergy.Years]) + \
                    1 - min(self.cost_details[GlossaryEnergy.Years])
            self.cost_details[f'{self.name}_factory_amort'] = (
                        np.tril(np.triu(np.ones((len_y, len_y)), k=0), k=self.nb_years_amort_capex - 1).transpose() *
                        np.array(self.cost_details[f'{self.name}_factory'].values / self.nb_years_amort_capex)).T.sum(
                axis=0)
            # pylint: enable=no-member
            self.cost_details[f'{self.name}_amort'] = self.cost_details[f'{self.name}_factory_amort'] + \
                                                      self.cost_details['transport'] + \
                                                      self.cost_details['energy_costs']
            self.cost_details[f'{self.name}_amort'] *= self.margin.loc[self.margin[GlossaryEnergy.Years]
                                                                       <= self.cost_details[
                                                                           GlossaryEnergy.Years].max()][
                                                           GlossaryEnergy.MarginValue].values / 100.0
            self.cost_details[f'{self.name}_amort'] += self.cost_details['CO2_taxes_factory']

        # Add transport and CO2 taxes
        self.cost_details[self.name] += self.cost_details['CO2_taxes_factory']

        if 'CO2_taxes_factory' in self.cost_details:
            self.cost_details[f'{self.name}_wotaxes'] = self.cost_details[self.name] - \
                                                        self.cost_details['CO2_taxes_factory']
        else:
            self.cost_details[f'{self.name}_wotaxes'] = self.cost_details[self.name]

        # CAPEX in ($/MWh)
        self.cost_details['CAPEX_Part'] = self.cost_details[f'Capex_{self.name}'] * self.capital_recovery_factor

        # Running OPEX in ($/MWh)
        self.cost_details['OPEX_Part'] = self.cost_details[f'Capex_{self.name}'] * \
                                         (self.techno_infos_dict['Opex_percentage']) + \
                                         self.cost_details['transport'] + self.cost_details['energy_costs']
        # CO2 Tax in ($/MWh)
        self.cost_details['CO2Tax_Part'] = self.cost_details[self.name] - \
                                           self.cost_details[f'{self.name}_wotaxes']

        return self.cost_details

    def add_percentage_to_total(self, part_of_total):
        '''
        Add a percentage to the total price
        (for plasma cracking case we take only a percentage because the techno also creates graphene)
        '''
        techno_prices = self.cost_details[[
            GlossaryEnergy.Years, self.name, f'{self.name}_wotaxes']].merge(part_of_total, how='left').fillna(0)
        techno_prices[self.name] *= techno_prices[self.energy_name] / 100.
        techno_prices[f'{self.name}_wotaxes'] *= techno_prices[self.energy_name] / 100.

        return techno_prices[[GlossaryEnergy.Years, self.name, f'{self.name}_wotaxes']]

    def compute_cost_of_resources_usage_generic_method(self):
        """To replace non generic method compute_cost_of_resources_usage in the future"""
        cost_of_resource_usage =  {
            GlossaryEnergy.Years: self.years,
        }
        for resource in self.resources_used_for_production:
            cost_of_resource_usage[resource] = self.cost_details[f"{resource}_needs"].values * self.resources_prices[resource].values

        self.cost_of_resources_usage = pd.DataFrame(cost_of_resource_usage)

    @abstractmethod
    def compute_other_primary_energy_costs(self):
        '''
        Compute other energy costs which will depend on the techno reaction (elec for electrolysis or methane for SMR by example)
        '''
        self.compute_resources_needs()
        self.compute_cost_of_resources_usage_generic_method()
        self.compute_other_energies_needs()
        self.compute_cost_of_other_energies_usage()
        self.compute_specifif_costs_of_technos()

        return 0.0

    def is_invest_before_year(self, year):
        '''
        Check if an investment has been made on this technology before the year given in argument
        '''
        is_invest_before_year = False
        if self.initial_production == 0.0:
            if self.invest_before_ystart[GlossaryEnergy.InvestValue].sum() == 0.0:
                if self.invest_level[GlossaryEnergy.InvestValue].loc[
                    self.invest_level[GlossaryEnergy.Years] <= year].sum() == 0.0:
                    is_invest_before_year = True
        return is_invest_before_year

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
            invest_sum = self.initial_production * capex_init
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

    def compute_dcapex_dinvest(self, invest_list, data_config):
        """
        Compute Capital expenditures (immobilisations)
        depending on the demand on the technology
        """
        progress_ratio = 1.0 - data_config['learning_rate']

        capacity_factor_list = None
        if 'capacity_factor_at_year_end' in data_config \
                and 'capacity_factor' in data_config:
            capacity_factor_list = np.linspace(data_config['capacity_factor'],
                                               data_config['capacity_factor_at_year_end'],
                                               len(invest_list))

        expo_factor = -np.log(progress_ratio) / np.log(2.0)

        capex_init = self.check_capex_unity(data_config)

        invest_sum = self.initial_production * capex_init
        dcapex_year_dinvest_list = []
        capex_year = capex_init

        if 'complex128' in [invest_list.dtype]:
            arr_type = 'complex128'
        else:
            arr_type = 'float64'
        dcapex_calc_list_dinvest_list = np.zeros(
            (len(invest_list), len(invest_list)), dtype=arr_type)

        invest_list_2 = compute_func_with_exp_min(
            invest_list, self.min_value_invest)
        dinvest_func = compute_dfunc_with_exp_min(
            invest_list, self.min_value_invest)

        for i, invest in enumerate(invest_list_2):

            # first capex calculation
            if invest_sum.real < 10.0 or i == 0.0:
                capex_year = capex_init
                dcapex_year_dinvest_list = np.zeros(i + 1)
            else:
                if capacity_factor_list is not None:
                    ratio_capa = (
                            capacity_factor_list[i] / data_config['capacity_factor'])
                    ratio_invest = ((invest_sum + invest) / invest_sum *
                                    ratio_capa) \
                                   ** (-expo_factor)
                else:

                    ratio_invest = ((invest_sum + invest) /
                                    invest_sum) ** (-expo_factor)

                #                     # capexi = capex_i-1 * ratio
                # dcapexi = dcapex_i-1*ratio + dratio*capex

                dratio_invest_i_dinvest_i = -expo_factor * \
                                            ratio_invest / (invest_sum + invest)
                # dratioinvesti wrt invest i minus one
                dratio_invest_i_dinvest_i_m1 = expo_factor * invest * \
                                               ratio_invest / \
                                               (invest_sum * (invest_sum + invest))

                if ratio_invest.real < 0.95:
                    dratio_invest_i_dinvest_i = 0.05 * \
                                                np.exp(ratio_invest - 0.9) * dratio_invest_i_dinvest_i

                    dratio_invest_i_dinvest_i_m1 = 0.05 * \
                                                   np.exp(ratio_invest - 0.9) * \
                                                   dratio_invest_i_dinvest_i_m1

                    ratio_invest = 0.9 + 0.05 * np.exp(ratio_invest - 0.9)

                capex_i_m1 = capex_year
                dcapex_i_dinvest_i = capex_i_m1 * dratio_invest_i_dinvest_i

                dcapex_i_dinvest_i_m1 = [dcapex_i_dinvest_i_old * ratio_invest +
                                         capex_i_m1 * dratio_invest_i_dinvest_i_m1 for dcapex_i_dinvest_i_old
                                         in dcapex_year_dinvest_list]

                dcapex_year_dinvest_list = np.append(
                    dcapex_i_dinvest_i_m1, [dcapex_i_dinvest_i])

                dcapex_calc_list_dinvest_list[i,
                :i + 1] = dcapex_year_dinvest_list

                capex_year = capex_year * ratio_invest
            #
            invest_sum += invest

        if 'maximum_learning_capex_ratio' in data_config:
            maximum_learning_capex_ratio = data_config['maximum_learning_capex_ratio']
        else:
            maximum_learning_capex_ratio = 0.9
        # Reshape the gradient to get a multiplication line by column and not
        # line by line
        return (1.0 - maximum_learning_capex_ratio) * dcapex_calc_list_dinvest_list * dinvest_func.reshape(
            len(invest_list))

    def grad_price_vs_energy_price(self):

        return {}

    def grad_price_vs_resources_price(self):

        return {resource: np.diag(self.cost_details[f'{resource}_needs'].values) for resource in self.resources_used_for_production}

    def compute_expo_factor(self, data_config):

        progress_ratio = 1.0 - data_config['learning_rate']
        expo_factor = -np.log(progress_ratio) / np.log(2.0)

        return expo_factor

    def compute_capital_recovery_factor(self, data_config):
        """
        Compute annuity factor with the Weighted averaged cost of capital
        and the lifetime of the selected solution
        """
        wacc = self.techno_infos_dict['WACC']
        lifetime = self.techno_infos_dict['lifetime']

        capital_recovery_factor = (wacc * (1.0 + wacc) ** lifetime) / ((1.0 + wacc) ** lifetime - 1.0)

        return capital_recovery_factor

    def check_capex_unity(self, data_tocheck):
        """
        Put all capex in $/MWh
        """

        if data_tocheck['Capex_init_unit'] == '$/kWelectrical':

            if data_tocheck['stack_lifetime_unit'] == 'hours':
                capex_init = data_tocheck['Capex_init'] / \
                             data_tocheck['stack_lifetime']

        elif data_tocheck['Capex_init_unit'] == 'euro':
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
                             self.data_energy_dict['density'] / \
                             self.data_energy_dict['calorific_value']

            elif data_tocheck['available_power_unit'] == 'm^3':
                capex_init = data_tocheck['Capex_init'] * \
                             data_tocheck['euro_dollar'] / \
                             data_tocheck['available_power'] / \
                             self.data_energy_dict['density'] / \
                             self.data_energy_dict['calorific_value']
            elif data_tocheck['available_power_unit'] == 'kg/h':

                capex_init = data_tocheck['Capex_init'] * \
                             data_tocheck['euro_dollar'] / \
                             data_tocheck['full_load_hours'] / \
                             data_tocheck['capacity_factor'] / \
                             data_tocheck['available_power'] / \
                             self.data_energy_dict['calorific_value']
            elif data_tocheck['available_power_unit'] == 'kg/year':

                capex_init = data_tocheck['Capex_init'] * \
                             data_tocheck['euro_dollar'] / \
                             data_tocheck['available_power'] / \
                             self.data_energy_dict['calorific_value']
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
                                 self.data_energy_dict['calorific_value']
                else:
                    capex_init = data_tocheck['Capex_init'] * \
                                 data_tocheck['pounds_dollar'] / \
                                 data_tocheck['full_load_hours'] / \
                                 data_tocheck['available_power'] / \
                                 self.data_energy_dict['calorific_value']
        elif data_tocheck['Capex_init_unit'] == 'euro/W':
            capex_init = data_tocheck['Capex_init'] * \
                         data_tocheck['euro_dollar'] / 1.0e3 / \
                         (data_tocheck['full_load_hours'] * data_tocheck['lifetime'])

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
                         self.data_energy_dict['calorific_value']
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
                             self.data_energy_dict['calorific_value']
            elif data_tocheck['density_per_ha_unit'] == 'kg/ha':
                capex_init = data_tocheck['Capex_init'] * \
                             data_tocheck['euro_dollar'] / \
                             density_per_ha / \
                             self.data_energy_dict['calorific_value']
        else:
            capex_unit = data_tocheck['Capex_init_unit']
            raise Exception(
                f'The CAPEX unity {capex_unit} is not handled yet in techno_type')

        # return capex in $/MWh
        return capex_init * 1.0e3

    def get_electricity_needs(self):
        """
        Get the electricity needs for 1 kwh of the energy producted by the technology
        """
        if self.techno_infos_dict['elec_demand'] != 0.0:
            elec_need = self.check_energy_demand_unit(self.techno_infos_dict['elec_demand_unit'],
                                                      self.techno_infos_dict['elec_demand'])

        else:
            elec_need = 0.0

        return elec_need

    def get_heat_needs(self):
        """
        Get the heat needs for 1 kwh of the energy producted by the technology
        """

        if 'heat_demand' in self.techno_infos_dict:
            heat_need = self.check_energy_demand_unit(self.techno_infos_dict['heat_demand_unit'],
                                                      self.techno_infos_dict['heat_demand'])

        else:
            heat_need = 0.0

        return heat_need

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
                            / self.data_energy_dict['density'] \
                            / self.data_energy_dict['calorific_value']
        elif energy_demand_unit == 'kWh/kg':
            energy_demand = energy_demand \
                            / self.data_energy_dict['calorific_value']
        else:
            raise Exception(
                f'The unity of the energy demand {energy_demand_unit} is not handled with conversions')

        return energy_demand

    def get_fuel_needs(self):
        """
        Get the fuel needs for 1 kwh of the energy producted by the technology
        """
        if self.techno_infos_dict['fuel_demand'] != 0.0:
            fuel_need = self.check_energy_demand_unit(self.techno_infos_dict['fuel_demand_unit'],
                                                      self.techno_infos_dict['fuel_demand'])

        else:
            fuel_need = 0.0

        return fuel_need

    def compute_efficiency(self):
        # Compute efficiency evolving in time or not
        if 'techno_evo_time' in self.techno_infos_dict and self.techno_infos_dict['techno_evo_eff'] == 'yes':
            middle_evolution_year = self.techno_infos_dict['techno_evo_time']
            efficiency_max = self.techno_infos_dict['efficiency_max']
            efficiency_ini = self.techno_infos_dict['efficiency']
            efficiency_slope = 1

            if 'efficiency evolution slope' in self.techno_infos_dict:
                efficiency_slope = self.techno_infos_dict['efficiency evolution slope']

            years = self.years - self.years[0]

            eff_list = [self.sigmoid_function(
                i, efficiency_max, efficiency_ini, middle_evolution_year, efficiency_slope) for i in years]
            efficiency = pd.Series(eff_list)

        else:
            efficiency = self.techno_infos_dict['efficiency'] * np.ones_like(self.years)

        self.cost_details['efficiency'] = efficiency
        return efficiency

    def sigmoid_function(self, x, eff_max, eff_ini, l, slope):
        x = x - l
        # Logistic function
        return m.exp(slope * x) / (m.exp(slope * x) + 1) * (eff_max - eff_ini) + eff_ini

    def configure_transport_data(self, transport_cost, transport_margin):

        self.transport_cost = transport_cost
        self.transport_margin = transport_margin

    def compute_transport(self):
        '''
        Need a more complex model for hydrogen transport
        Computed in $/kWh
        Transport cost is in $/kg
        Margin is in %
        Result must be in $/MWh
        '''

        # transport_cost = 5.43  # $/kg
        transport_cost = self.transport_cost['transport'] * \
                         self.transport_margin[GlossaryEnergy.MarginValue] / 100.0

        # Need to multiply by * 1.0e3 to put it in $/MWh$
        if 'calorific_value' in self.data_energy_dict.keys():
            return transport_cost / \
                   self.data_energy_dict['calorific_value']
        else:
            keys = list(self.data_energy_dict.keys())
            calorific_value = self.data_energy_dict[keys[
                0]]['calorific_value']
            return transport_cost / \
                   calorific_value

    def compute_carbon_emissions(self):
        '''
        Compute the carbon emissions from the technology taking into account 
        CO2 from production + CO2 from primary resources

        Definitions of the various levels of emissions:
        self.carbon_intensity['production'] = -scope 1- (direct emissions): direct CO2 emissions during the production phase of the techno
                ex: CO2 emitted or needed as part of the chemical reaction used to produce the techno (ex: Sabatier reaction
                requires CO2 to produce methane from H2) + company facilities emissions + company vehicles emissions
                + CO2 emissions of energy used for the production + ...
        co2_emissions_frominput_energies = -scope 2- (indirect emissions): CO2 emissions during the production of the energies
                used in scope 1, namely of the energies used during the production of the techno = emissions during
                production of purchased electricity, steam, heating & cooling for own use
                NB: in climateeconomics/sos_wrapping/sos_wrapping_witness/post_proc_witness_optim/post_processing_witness_full.py
                co2_emissions_frominput_energies is referred to as CO2_from_other_consumption
                In https://ghgprotocol.org/sites/default/files/standards/ghg-protocol-revised.pdf p.31, scope 2 definition only accounts for
                indirect CO2 emissions of purchased electricity

        self.carbon_intensity[self.name] = CO2_from_production + co2_emissions_frominput_energies =  scope 1 + scope 2 emissions

        NB: scope 3 CO2 emissions of the techno are not considered in this method. See for instance
                CO2_per_use in climateeconomics/sos_wrapping/sos_wrapping_witness/post_proc_witness_optim/post_processing_witness_full.py
        '''

        if 'CO2_from_production' not in self.techno_infos_dict:
            self.carbon_intensity['production'] = self.get_theoretical_co2_prod(
                unit='kg/kWh')
        elif self.techno_infos_dict['CO2_from_production'] == 0.0:
            self.carbon_intensity['production'] = 0.0
        else:
            if self.techno_infos_dict['CO2_from_production_unit'] == 'kg/kg':
                self.carbon_intensity['production'] = self.techno_infos_dict['CO2_from_production'] / \
                                                      self.data_energy_dict['high_calorific_value']
            elif self.techno_infos_dict['CO2_from_production_unit'] == 'kg/kWh':
                self.carbon_intensity['production'] = self.techno_infos_dict['CO2_from_production']

        # Add carbon emission from input energies (resources or other
        # energies)

        co2_emissions_frominput_energies = self.compute_CO2_emissions_from_input_resources(
        )

        # Add CO2 from production + C02 from input energies
        self.carbon_intensity[self.name] = self.carbon_intensity['production'] + \
                                           co2_emissions_frominput_energies

    def compute_CO2_emissions_from_input_resources(self):
        '''
        Need to be overload in some technologies where input energies need to be taken into account for CO2 emissions
        '''
        return 0.0


    def compute_resources_needs(self):
        """To be overloaded when techno relies on resources"""
        pass

    def compute_other_energies_needs(self):
        """To be overloaded when techno uses other technos productions to produce its energy"""
        pass

    def compute_cost_of_other_energies_usage(self):
        """To be overloaded when techno uses other technos productions to produce its energy"""
        pass

    def compute_specifif_costs_of_technos(self):
        """To be overloaded when techno relies on resources"""
        pass

    def compute_co2_tax(self):
        '''
        CO2 taxes are in $/tCO2
        Need to be computed in $/MWh H2
        Only CO2 emitted from the technology is here taken into account to compute CO2 taxes
        If carbon emissions are negative then no negative CO2 taxes (use a clip on the column)
        '''
        self.compute_carbon_emissions()
        CO2_taxes_kwh = self.CO2_taxes[GlossaryEnergy.CO2Tax].loc[self.CO2_taxes[GlossaryEnergy.Years]
                                                                  <= self.carbon_intensity[
                                                                      GlossaryEnergy.Years].max()].values * \
                        self.carbon_intensity[self.name].clip(0)
        return CO2_taxes_kwh

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
            {f'distrib_prod ({self.product_energy_unit})': 'sum'}
            )
        if f'{self.energy_name} ({self.product_energy_unit})' in self.production_detailed:
            del self.production_detailed[f'{self.energy_name} ({self.product_energy_unit})']

        self.production_detailed = pd.merge(self.production_detailed, age_distrib_prod_sum, how='left',
                                            on=GlossaryEnergy.Years).rename(
            columns={
                f'distrib_prod ({self.product_energy_unit})': f'{self.energy_name} ({self.product_energy_unit})'}).fillna(
            0.0)

        self.compute_land_use()

    def compute_primary_installed_power(self):

        if GlossaryEnergy.ConstructionDelay in self.techno_infos_dict:
            construction_delay = self.techno_infos_dict[GlossaryEnergy.ConstructionDelay]
        else:
            print(
                f'The construction_delay data is not set for {self.name} : default = 3 years  ')
            construction_delay = 3

        if 'full_load_hours' in self.techno_infos_dict:
            full_load_hours = self.techno_infos_dict['full_load_hours']
        else:
            # print(
            #     f'The full_load_hours data is not set for {self.name} : default = 8760.0 hours, full year hours  ')
            full_load_hours = 8760.0

        production_from_invest = self.compute_prod_from_invest(
            construction_delay=construction_delay)

        # Conversion from TWh to MW
        self.installed_power['new_power_production'] = production_from_invest.loc[production_from_invest[
                                                                                      GlossaryEnergy.Years] == self.years, 'prod_from_invest'].values / full_load_hours * 1000
        self.installed_power['total_installed_power'] = self.production_detailed[
                                                            f'{self.energy_name} ({self.product_energy_unit})'] / full_load_hours * 1000
        self.installed_power['removed_power_production'] = np.zeros(len(self.years))

        power_production_dict = self.installed_power.to_dict()

        for year in self.years[1:]:
            power_production_dict['removed_power_production'][year - power_production_dict[GlossaryEnergy.Years][0]] = \
                power_production_dict['total_installed_power'][
                    year - 1 - power_production_dict[GlossaryEnergy.Years][0]] \
                - power_production_dict['total_installed_power'][year - power_production_dict[GlossaryEnergy.Years][0]] \
                + power_production_dict['new_power_production'][year - power_production_dict[GlossaryEnergy.Years][0]]
        self.installed_power = pd.DataFrame.from_dict(power_production_dict)

    def compute_dprod_dinvest(self, capex_list, invest_list, invest_before_year_start, techno_dict,
                              dcapex_list_dinvest_list):
        '''
        Compute the partial derivative of prod vs invest  and the partial derivative of prod vs capex
        To compute after the total derivative of prod vs invest = dpprod_dpinvest + dpprod_dpcapex*dcapexdinvest
        with dcapexdinvest already computed for detailed prices
        '''
        nb_years = len(capex_list)

        if 'complex128' in [capex_list.dtype, invest_list.dtype, invest_before_year_start.dtype,
                            dcapex_list_dinvest_list.dtype]:
            arr_type = 'complex128'
        else:
            arr_type = 'float64'
        dprod_list_dinvest_list = np.zeros(
            (nb_years, nb_years), dtype=arr_type)
        # We fill this jacobian column by column because it is the same element
        # in the entire column
        for i in range(nb_years):
            dpprod_dpinvest = compute_dfunc_with_exp_min(np.array([invest_list[i]]), self.min_value_invest)[0][0] / \
                              capex_list[i]
            len_non_zeros = min(max(0, nb_years -
                                    techno_dict[GlossaryEnergy.ConstructionDelay] - i),
                                techno_dict['lifetime'])
            first_len_zeros = min(
                i + techno_dict[GlossaryEnergy.ConstructionDelay], nb_years)
            last_len_zeros = max(0, nb_years -
                                 len_non_zeros - first_len_zeros)
            # For prod in each column there is lifetime times the same value which is dpprod_dpinvest
            # This value is delayed in time (means delayed in lines for
            # jacobian by construction _delay)
            # Each column is then composed of [0,0,0... (dp/dx,dp/dx)*lifetime,
            # 0,0,0]
            is_invest_negative = max(
                np.sign(invest_list[i] + np.finfo(float).eps), 0.0)
            dprod_list_dinvest_list[:, i] = np.hstack((np.zeros(first_len_zeros),
                                                       np.ones(
                                                           len_non_zeros) * dpprod_dpinvest * is_invest_negative,
                                                       np.zeros(last_len_zeros)))

        dprod_list_dcapex_list = self.compute_dprod_dcapex(
            capex_list, invest_list, techno_dict, invest_before_year_start)

        dinvest_exp_min = compute_dfunc_with_exp_min(
            invest_list, self.min_value_invest)

        dcapex_list_dinvest_list_withexp = dcapex_list_dinvest_list * dinvest_exp_min
        dprod_dinvest = np.zeros(
            (nb_years, nb_years), dtype=arr_type)
        # dprod_dinvest= dpprod_dpinvest + dprod_dcapex*dcapex_dinvest
        for line in range(nb_years):
            for column in range(nb_years):
                dprod_dinvest[line, column] = dprod_list_dinvest_list[line, column] + \
                                              np.matmul(
                                                  dprod_list_dcapex_list[line, :],
                                                  dcapex_list_dinvest_list_withexp[:, column])

        self.dprod_dinvest = dprod_dinvest

        return dprod_dinvest

    def compute_dprod_dcapex(self, capex_list, invest_list, techno_dict, invest_before_year_start):
        '''
        Compute the derivative of production over capex 
        '''
        nb_years = len(capex_list)
        dprod_list_dcapex_list = np.zeros(
            (nb_years, nb_years))
        if 'complex128' in [capex_list.dtype, invest_list.dtype, invest_before_year_start.dtype]:
            dprod_list_dcapex_list = np.zeros(
                (nb_years, nb_years), dtype='complex128')
        for i in range(nb_years):
            len_non_zeros = min(max(0, nb_years -
                                    techno_dict[GlossaryEnergy.ConstructionDelay] - i),
                                techno_dict['lifetime'])
            first_len_zeros = min(
                i + techno_dict[GlossaryEnergy.ConstructionDelay], nb_years)
            last_len_zeros = max(0, nb_years -
                                 len_non_zeros - first_len_zeros)
            # Same for capex
            dpprod_dpcapex = - invest_list[i] / capex_list[i] ** 2

            dprod_list_dcapex_list[:, i] = np.hstack((np.zeros(first_len_zeros),
                                                      np.ones(
                                                          len_non_zeros) * dpprod_dpcapex,
                                                      np.zeros(last_len_zeros)))
        # but the capex[0] is used for invest before
        # year_start then we need to add it to the first column
        dpprod_dpcapex0_list = [- invest / capex_list[0]
                                ** 2 for invest in invest_before_year_start]

        for index, dpprod_dpcapex0 in enumerate(dpprod_dpcapex0_list):
            len_non_zeros = min(
                techno_dict['lifetime'], nb_years - index)
            dprod_list_dcapex_list[:, 0] += np.hstack((np.zeros(index),
                                                       np.ones(
                                                           len_non_zeros) * dpprod_dpcapex0,
                                                       np.zeros(nb_years - index - len_non_zeros)))

        self.dprod_list_dcapex_list = dprod_list_dcapex_list

        return dprod_list_dcapex_list

    def compute_dpower_dinvest(self, capex_list, invest_list, techno_dict, dcapex_dinvest,
                               scaling_factor_techno_consumption):
        nb_years = len(capex_list)
        dpower_list_dinvest_list = np.zeros(
            (nb_years, nb_years))

        delay = techno_dict[GlossaryEnergy.ConstructionDelay]
        # power = cste * invest / capex ie dpower_d_invest = cste * (Id/capex - invest * dcapex_dinvest / capex**2)
        for i in range(delay, nb_years):
            if capex_list[i - delay] != 0:
                if 'full_load_hours' not in self.techno_infos_dict:
                    full_load_hours = 8760
                else:
                    full_load_hours = self.techno_infos_dict['full_load_hours']
                # cste * Id / capex
                dpower_list_dinvest_list[i, i - delay] += 1000 / full_load_hours / capex_list[
                    i - delay] * scaling_factor_techno_consumption
                # cste * invest * dcapex_dinvest / capex ** 2
                dpower_list_dinvest_list[i, :] -= 1000 / full_load_hours * invest_list[i - delay] * \
                                                  dcapex_dinvest[i - delay, :] / capex_list[
                                                      i - delay] ** 2 * scaling_factor_techno_consumption
        self.dpower_list_dinvest_list = np.multiply(dpower_list_dinvest_list,
                                                    compute_dfunc_with_exp_min(np.array(invest_list),
                                                                               self.min_value_invest).T)

        return self.dpower_list_dinvest_list

    def compute_dprod_dratio(self, prod, ratio_name, dapplied_ratio_dratio):
        '''! Select the most constraining ratio and apply it to production and consumption.
        To avoid clipping effects, the applied ratio is not the minimum value between all the ratios, 
        but the smoothed minimum value between all the ratio (see func_manager documentation for more).
        @param prod: pandas Series, values of the production/consumption for which the gradient is calculated
        @param ratio_name: string, name of the ratio for which the gradient is calculated
        @param is_apply_ratio: boolean, used to activate(True)/deactivate(False) the application of limiting ratios. Defaults to True.

        @return dprod_dratio: numpy array, size=(len(years), len(years))
        :param dapplied_ratio_dratio:
        :type dapplied_ratio_dratio:
        '''
        dprod_dratio = np.zeros(
            (len(self.years), len(self.years)))

        if ratio_name:
            # Check that the ratio corresponds to something consumed
            for col in self.consumption_detailed.columns:
                if ratio_name in col and ratio_name != GlossaryEnergy.Years:
                    dprod_dratio = (np.identity(len(self.years)) * prod.values) * \
                                   dapplied_ratio_dratio[ratio_name]
        return dprod_dratio / 100.

    def compute_dapplied_ratio_dratios(self, is_apply_ratio=True):
        '''
        Compute the gradient of applied ratio vs all_stream_demand_ratios
        only if is_apply_ratio is True
        '''
        dsmooth_dvariable = {}
        elements = []
        for i, element in enumerate(self.ratio_df.columns):
            # Initialize each dict element with array of zeros
            dsmooth_dvariable[element] = np.zeros(
                (len(self.years), len(self.years)))
            # Same as for the main function, search for matches between
            # ratio_df and consumptions
            if is_apply_ratio:
                for col in self.consumption_detailed.columns:
                    if element in col and element != GlossaryEnergy.Years:
                        elements += [element, ]
        if is_apply_ratio:
            if len(elements) > 0:
                if self.smooth_type == 'smooth_max':
                    dsmooth_matrix = get_dsmooth_dvariable_vect(
                        -self.ratio_df[elements].values)
                elif self.smooth_type == 'soft_max':
                    dsmooth_matrix = get_dsoft_maximum_vect(
                        -self.ratio_df[elements].values)
                elif self.smooth_type == 'cons_smooth_max':
                    dsmooth_matrix = get_dcons_smooth_dvariable_vect(
                        -self.ratio_df[elements].values)
                else:
                    raise Exception('Unknown smooth_type')
                for i, element in enumerate(self.ratio_df[elements].columns):
                    dsmooth_dvariable[element] = dsmooth_matrix.T[i]

        return dsmooth_dvariable

    def compute_aging_distribution_production(self):
        '''
        Compute the aging distribution production of primary energy for years of study
        Start with the initial distribution and add a year on the age each year 
        Add also the yearly production regarding the investment
        All productions older than the lifetime are removed from the dataframe  
        '''
        # To break the object link with initial distrib
        aging_distrib_year_df = pd.DataFrame(
            {'age': self.initial_age_distrib['age'].values})
        aging_distrib_year_df[f'distrib_prod ({self.product_energy_unit})'] = self.initial_age_distrib['distrib'] * \
                                                                              self.initial_production / 100.0

        if GlossaryEnergy.ConstructionDelay in self.techno_infos_dict:
            construction_delay = self.techno_infos_dict[GlossaryEnergy.ConstructionDelay]
        else:
            print(
                f'The construction_delay data is not set for {self.name} : default = 3 years  ')
            construction_delay = 3

        production_from_invest = self.compute_prod_from_invest(
            construction_delay=construction_delay)

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
        prod_array = production_from_invest['prod_from_invest'].values.tolist(
        ) * len_years

        new_prod_aged = pd.DataFrame({GlossaryEnergy.Years: year_array, 'age': age_array,
                                      f'distrib_prod ({self.product_energy_unit})': prod_array})

        # get the whole dataframe for old production with one line for each
        # year at each age
        year_array = np.array([[year] * len(aging_distrib_year_df)
                               for year in self.years]).flatten()
        age_values = aging_distrib_year_df['age'].values
        age_array = np.concatenate(tuple(
            age_values + i for i in range(len_years)))
        prod_array = aging_distrib_year_df[f'distrib_prod ({self.product_energy_unit})'].values.tolist(
        ) * len_years

        old_prod_aged = pd.DataFrame({GlossaryEnergy.Years: year_array, 'age': age_array,
                                      f'distrib_prod ({self.product_energy_unit})': prod_array})

        # Concat the two created df
        self.age_distrib_prod_df = pd.concat(
            [new_prod_aged, old_prod_aged], ignore_index=True)

        self.age_distrib_prod_df = self.age_distrib_prod_df.loc[
            # Suppress all lines where age is higher than lifetime
            (self.age_distrib_prod_df['age'] <
             self.techno_infos_dict['lifetime'])
            # Suppress all lines where age is higher than lifetime
            & (self.age_distrib_prod_df[GlossaryEnergy.Years] < self.year_end + 1)
            # Fill Nan with zeros and suppress all zeros
            & (self.age_distrib_prod_df[f'distrib_prod ({self.product_energy_unit})'] != 0.0)
            ]
        # Fill Nan with zeros
        self.age_distrib_prod_df.fillna(0.0, inplace=True)

    def compute_dlanduse_dinvest(self):
        """
        compute grad d_land_use / d_invest
        """

        dlanduse_dinvest = np.identity(len(self.years)) * 0
        for key in self.land_use:
            if key.startswith(self.name):
                if not (self.land_use[key] == np.array([0] * len(self.years))).all():
                    density_per_ha = self.techno_infos_dict['density_per_ha']
                    if self.techno_infos_dict['density_per_ha_unit'] == 'm^3/ha':
                        density_per_ha = density_per_ha * \
                                         self.techno_infos_dict['density'] * \
                                         self.data_energy_dict['calorific_value']
                    elif self.techno_infos_dict['density_per_ha_unit'] == 'kg/ha':
                        density_per_ha = density_per_ha * \
                                         self.data_energy_dict['calorific_value']

                    dlanduse_dinvest = self.dprod_dinvest / density_per_ha
                    if 'percentage_for_production' in self.techno_infos_dict:
                        dlanduse_dinvest /= self.techno_infos_dict['percentage_for_production']
                    if 'years_between_harvest' in self.techno_infos_dict:
                        dlanduse_dinvest *= self.techno_infos_dict['years_between_harvest']
                    if 'recyle_part' in self.techno_infos_dict:
                        dlanduse_dinvest *= (1 -
                                             self.techno_infos_dict['recyle_part'])

        return dlanduse_dinvest

    def compute_prod_from_invest(self, construction_delay):
        '''
        Compute the energy production of a techno from investment in TWh
        Add a delay for factory construction
        '''

        prod_before_ystart = pd.DataFrame(
            {GlossaryEnergy.Years: np.arange(self.year_start - construction_delay, self.year_start),
             GlossaryEnergy.InvestValue: self.invest_before_ystart[GlossaryEnergy.InvestValue].values[::1],
             f'Capex_{self.name}': self.cost_details.loc[
                 self.cost_details[GlossaryEnergy.Years] == self.year_start, f'Capex_{self.name}'].values[0]})

        production_from_invest = pd.concat(
            [self.cost_details[[GlossaryEnergy.Years, GlossaryEnergy.InvestValue, f'Capex_{self.name}']],
             prod_before_ystart], ignore_index=True)
        production_from_invest.sort_values(by=[GlossaryEnergy.Years], inplace=True)
        # Need prod_from invest in TWh we have M$ and $/MWh  M$/($/MWh)= TWh
        # invest_minimized = production_from_invest[GlossaryEnergy.InvestValue].values

        production_from_invest['prod_from_invest'] = production_from_invest[GlossaryEnergy.InvestValue].values / \
                                                     production_from_invest[f'Capex_{self.name}'].values
        production_from_invest[GlossaryEnergy.Years] += construction_delay
        production_from_invest = production_from_invest[production_from_invest[GlossaryEnergy.Years]
                                                        <= self.year_end]

        return production_from_invest

    def get_mean_age_over_years(self):

        mean_age_df = pd.DataFrame({GlossaryEnergy.Years: self.years})

        self.age_distrib_prod_df['age_x_prod'] = self.age_distrib_prod_df['age'] * \
                                                 self.age_distrib_prod_df[f'distrib_prod ({self.product_energy_unit})']

        mean_age_df['mean age'] = self.age_distrib_prod_df.groupby(
            [GlossaryEnergy.Years], as_index=False).agg({'age_x_prod': 'sum'})['age_x_prod'] / self.production_woratio[
                                      f'{self.energy_name} ({self.product_energy_unit})']
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
        if f'{GHG_type}_emission_factor' not in self.techno_infos_dict:
            raise Exception(
                f'The variable {GHG_type}_emission_factor should be in the techno dict to compute {GHG_type} emissions for {self.name}')
        emission_factor = self.techno_infos_dict[f'{GHG_type}_emission_factor']

        if related_to == 'prod':
            self.production_detailed[f'{GHG_type} ({self.mass_unit})'] = emission_factor * \
                                                                         self.production_detailed[
                                                                             f'{self.energy_name} ({self.product_energy_unit})'].values
        else:
            self.production_detailed[f'{GHG_type} ({self.mass_unit})'] = emission_factor * \
                                                                         self.consumption_detailed[
                                                                             f'{related_to} ({self.product_energy_unit})'].values

    def compute(self, inputs_dict):
        self.configure_parameters_update(inputs_dict)
        # -- compute informations
        self.compute_price()
        self.compute_primary_energy_production()
        self.compute_consumption_and_production()
        self.compute_primary_installed_power()
        self.compute_consumption_and_installed_power()

        # ratios : utilisation & resources
        self.store_consumption_and_production_and_landuse_wo_ratios()
        self.apply_utilisation_ratio()
        self.select_resources_ratios()
        self.apply_resources_ratios(inputs_dict['is_apply_ratio'])

        self.compute_capital()
        self.get_mean_age_over_years()

        self.rescale_outputs()

    def rescale_outputs(self):
        self.production = copy(self.production_detailed)
        self.consumption = copy(self.consumption_detailed)

        for column in self.consumption_detailed.columns:
            if column == GlossaryEnergy.Years:
                continue
            self.consumption[column] = self.consumption[column].values / self.scaling_factor_techno_consumption
        for column in self.production_detailed.columns:
            if column == GlossaryEnergy.Years:
                continue
            self.production[column] = self.production[column].values / self.scaling_factor_techno_production

        for column in self.consumption_woratio.columns:
            if column == GlossaryEnergy.Years:
                continue
            self.consumption_woratio[column] = self.consumption_woratio[
                                                   column].values / self.scaling_factor_techno_consumption
        for column in self.production_woratio.columns:
            if column == GlossaryEnergy.Years:
                continue
            self.production_woratio[column] = self.production_woratio[
                                                  column].values / self.scaling_factor_techno_production

    def apply_utilisation_ratio(self):
        """
        Apply utilisation ratio percentage to
        - consumption
        - production
        """
        for column in self.consumption_detailed.columns:
            if column == GlossaryEnergy.Years:
                continue
            self.consumption_detailed[column] = self.consumption_detailed[column].values * self.utilisation_ratio / 100.

        for column in self.production_detailed.columns:
            if column == GlossaryEnergy.Years:
                continue
            self.production_detailed[column] = self.production_detailed[column].values * self.utilisation_ratio / 100.

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

    def d_non_use_capital_d_utilisation_ratio(self):
        techno_capital = self.techno_capital[GlossaryEnergy.Capital].values
        d_non_use_capital_d_utilisation_ratio = np.diag(
            - techno_capital * self.applied_ratio['applied_ratio'] / 100.
        )
        return d_non_use_capital_d_utilisation_ratio

    def grad_co2_emissions_vs_resources_co2_emissions(self):
        '''
        Compute the gradient of global CO2 emissions vs resources CO2 emissions
        '''
        return {
            resource: np.diag(self.cost_details[f"{resource}_needs"].values) for resource in self.resources_used_for_production
        }

