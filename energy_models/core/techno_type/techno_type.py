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

import autograd.numpy as np

from sostrades_optimization_plugins.models.differentiable_model import DifferentiableModel
from sostrades_optimization_plugins.tools.cst_manager.func_manager_common import (
    smooth_maximum_vect,
    soft_maximum_vect,
)

from energy_models.glossaryenergy import GlossaryEnergy


class TechnoType(DifferentiableModel):
    """Class for energy production technology type"""

    energy_name = 'energy'

    def __init__(self, name):
        super().__init__()
        self.years = None
        self.ratios_name_list = []
        self.name = name
        self.product_unit = 'TWh'


    def configure_parameters_update(self):
        '''
        Configure with inputs_dict from the discipline
        '''
        self.year_start = self.inputs[GlossaryEnergy.YearStart]  # year start
        self.year_end = self.inputs[GlossaryEnergy.YearEnd]  # year end
        self.years = np.arange(self.year_start, self.year_end + 1)

        self.configure_energy_data()


    @property
    def zeros_array(self):
        return self.years * 0.

    def configure_energy_data(self):
        '''
        Configure energy data by reading the data_energy_dict in the right Energy class
        Overloaded for each energy type
        '''
        pass

    def compute_resource_consumption(self):
        for resource in self.inputs[GlossaryEnergy.ResourcesUsedForProductionValue]:
            self.outputs[f'{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}:{resource} ({GlossaryEnergy.mass_unit})'] =\
                self.outputs[f"{GlossaryEnergy.TechnoDetailedPricesValue}:{resource}_needs"] * \
                self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:{self.energy_name} ({self.product_unit})']

    def compute_streams_consumption(self):
        for stream in self.inputs[GlossaryEnergy.StreamsUsedForProductionValue]:
            stream_unit = GlossaryEnergy.unit_dicts[stream]
            self.outputs[f'{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}:{stream} ({stream_unit})'] = \
                self.outputs[f"{GlossaryEnergy.TechnoDetailedPricesValue}:{stream}_needs"] * \
                self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:{self.energy_name} ({self.product_unit})']

    def compute_byproducts_production(self):
        """
        Compute the production of byproduct of the technology
        """
        pass

    def select_concerning_ratios(self):
        """
        Select the ratios that are meaningfull to consider to modulate the techno production.
        Finally, it converts ratios in % to [0, 1].
        """
        self.ratios_name_list = []
        if self.inputs[GlossaryEnergy.BoolApplyRatio] and self.inputs[GlossaryEnergy.BoolApplyStreamRatio]:
            self.ratios_name_list.extend([f'{GlossaryEnergy.AllStreamsDemandRatioValue}:{stream}' for stream in self.inputs[GlossaryEnergy.StreamsUsedForProductionValue]])

        if self.inputs[GlossaryEnergy.BoolApplyRatio] and self.inputs[GlossaryEnergy.BoolApplyResourceRatio]:
            self.ratios_name_list.extend([f'all_resource_ratio_usable_demand:{resource}' for resource in self.inputs[GlossaryEnergy.ResourcesUsedForProductionValue]])
            self.ratios_name_list.extend([f'all_resource_ratio_usable_demand:{resource}' for resource in self.inputs[GlossaryEnergy.ResourcesUsedForBuildingValue]])


    def apply_limiting_ratio(self):
        """! Select the most constraining ratio and apply it to production and consumption.
        To avoid clipping effects, the applied ratio is not the minimum value between all the ratios, 
        but the smoothed minimum value between all the ratio (see func_manager documentation for more).
        A model variables is set in this method:
            -self.applied_ratio: the effective ratio applied for each year
        The method "select_ratios" must have been called beforehand to have the self.ratio_df variable
        """
        ratio_values = np.ones(len(self.years))
        limiting_input = np.array([''] * len(self.years))
        if len(self.ratios_name_list) > 0:
            ratios_array = np.vstack([self.inputs[col] for col in self.ratios_name_list]).T / 100.
            if self.inputs['smooth_type'] == 'smooth_max':
                ratio_values = - smooth_maximum_vect(-ratios_array)
            elif self.inputs['smooth_type'] == 'soft_max':
                ratio_values = - soft_maximum_vect(-ratios_array)
            elif self.inputs['smooth_type'] == 'cons_smooth_max':
                ratio_values = - cons_smooth_maximum_vect(-ratios_array)
            limiting_input = np.array([self.ratios_name_list[index].split(':')[1] for index in np.argmin(ratios_array, axis=1)])


        # Apply the smoothed ratio value
        # ----------
        # WARNING!!!
        # ----------
        # All these application of the ratio_values were made under the
        # assumption that a linear correlation is at work (ratio on prod == ratio on col)
        # there may be special cases that need to be handled differently
        # (quadratic correlation or other)

        for col in self.get_colnames_output_dataframe(GlossaryEnergy.TechnoProductionValue, expect_years=True):
            self.outputs[f'{GlossaryEnergy.TechnoProductionValue}:{col}'] *= ratio_values

        for col in self.get_colnames_output_dataframe(GlossaryEnergy.TechnoConsumptionValue, expect_years=True):
            self.outputs[f'{GlossaryEnergy.TechnoConsumptionValue}:{col}'] *= ratio_values

        self.outputs[f'{GlossaryEnergy.LandUseRequiredValue}:{GlossaryEnergy.Years}'] = self.years
        for col in self.get_colnames_output_dataframe(GlossaryEnergy.LandUseRequiredValue, expect_years=True):
            self.outputs[f'{GlossaryEnergy.LandUseRequiredValue}:{col}'] *= ratio_values

        self.outputs[f'applied_ratio:{GlossaryEnergy.Years}'] = self.years
        self.outputs[f'applied_ratio:limiting_input'] = limiting_input
        self.outputs[f'applied_ratio:applied_ratio'] = ratio_values

    def compute_capital(self):
        '''
        Compute Capital & loss of capital because of the unusability of the technology.
        When the applied ratio is below 1, the technology does not produce all the energy possible.
        Investments on this technology is consequently non_use. 
        This method computes the non_use of capital 

        Capex is in $/MWh
        Prod in TWh
        then capex * prod_wo_ratio is in $ / MWh*(1e6MWh)= M$

        We divide by 1e3 to put non_use_capital in G$
        '''
        self.outputs[f'{GlossaryEnergy.TechnoCapitalValue}:{GlossaryEnergy.Years}'] = self.years
        self.outputs[f'{GlossaryEnergy.TechnoCapitalValue}:{GlossaryEnergy.Capital}'] = \
            self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:Capex_{self.name}'] *\
            self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:{self.energy_name} ({self.product_unit})'] / 1e3

        self.outputs[f'{GlossaryEnergy.TechnoCapitalValue}:{GlossaryEnergy.NonUseCapital}'] = self.outputs[f'{GlossaryEnergy.TechnoCapitalValue}:{GlossaryEnergy.Capital}'] * (
                1.0 - self.outputs['applied_ratio:applied_ratio'] * self.inputs[f'{GlossaryEnergy.UtilisationRatioValue}:{GlossaryEnergy.UtilisationRatioValue}'] / 100.)

    def compute_price(self):
        """
        Compute the detail price of the technology
        """
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.Years}'] = self.years

        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:Capex_{self.name}'] = self.compute_capex() # $ / MWh

        capital_recovery_factor = self.compute_capital_recovery_factor()
        self.compute_efficiency()
        self.compute_other_primary_energy_costs()

        # Factory cost including CAPEX OPEX
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.name}_factory'] = self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:Capex_{self.name}'] * \
                                                    (capital_recovery_factor + self.inputs['techno_infos_dict']['Opex_percentage'])

        if 'decommissioning_percentage' in self.inputs['techno_infos_dict']:
            self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.name}_factory_decommissioning'] = \
                self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:Capex_{self.name}'] * self.inputs['techno_infos_dict']['decommissioning_percentage']
            self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.name}_factory'] += self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.name}_factory_decommissioning']

        # Compute and add transport
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:transport'] = self.compute_transport()

        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.name}'] = self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.name}_factory'] + self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:transport'] + \
                                       self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:energy_and_resources_costs']


        price_with_margin = self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.name}'] * self.inputs[f'{GlossaryEnergy.MarginValue}:{GlossaryEnergy.MarginValue}'] / 100.0
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.MarginValue}'] = price_with_margin - self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.name}']
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.name}'] = price_with_margin

        self.compute_carbon_emissions()
        self.compute_co2_tax()

        if 'nb_years_amort_capex' in self.inputs['techno_infos_dict']:
            nb_years_amort_capex = self.inputs['techno_infos_dict']['nb_years_amort_capex']

            # pylint: disable=no-member
            len_y = max(self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.Years}']) + \
                    1 - min(self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.Years}'])
            self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.name}_factory_amort'] = (
                    np.tril(np.triu(np.ones((len_y, len_y)), k=0), k=nb_years_amort_capex - 1).transpose() *
                    np.array(self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.name}_factory'] / nb_years_amort_capex)).T.sum(
                axis=0)
            # pylint: enable=no-member
            self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.name}_amort'] = self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.name}_factory_amort'] + \
                                                      self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:transport'] + \
                                                      self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:energy_and_resources_costs']
            self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.name}_amort'] *= self.inputs[f'{GlossaryEnergy.MarginValue}:{GlossaryEnergy.MarginValue}'] / 100.0
            self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.name}_amort'] += self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:CO2_taxes_factory']

        # Add transport and CO2 taxes
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.name}'] += self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:CO2_taxes_factory']

        if 'CO2_taxes_factory' in self.get_colnames_output_dataframe(GlossaryEnergy.TechnoDetailedPricesValue):
            self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.name}_wotaxes'] = self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.name}'] - \
                                                        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:CO2_taxes_factory']
        else:
            self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.name}_wotaxes'] = self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.name}']

        # CAPEX in ($/MWh)
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:CAPEX_Part'] = self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:Capex_{self.name}'] * capital_recovery_factor

        # Running OPEX in ($/MWh)
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:OPEX_Part'] = self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:Capex_{self.name}'] * \
                                         (self.inputs['techno_infos_dict']['Opex_percentage']) + \
                                         self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:transport'] + self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:energy_and_resources_costs']
        # CO2 Tax in ($/MWh)
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:CO2Tax_Part'] = self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.name}'] - \
                                           self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.name}_wotaxes']

        # only coupling columns :
        self.outputs[f'{GlossaryEnergy.TechnoPricesValue}:{GlossaryEnergy.Years}'] = self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.Years}']
        self.outputs[f'{GlossaryEnergy.TechnoPricesValue}:{self.name}'] = self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.name}']
        self.outputs[f'{GlossaryEnergy.TechnoPricesValue}:{self.name}_wotaxes'] = self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.name}_wotaxes']


    def compute_cost_of_resources_usage(self):
        """
        Cost of resource R = need of resource R x price of resource R
        """
        self.outputs[f"{GlossaryEnergy.CostOfResourceUsageValue}:{GlossaryEnergy.Years}"] = self.years
        self.outputs[f"{GlossaryEnergy.CostOfResourceUsageValue}:Total"] = self.zeros_array
        for resource in self.inputs[GlossaryEnergy.ResourcesUsedForProductionValue]:
            self.outputs[f"{GlossaryEnergy.CostOfResourceUsageValue}:{resource}"] = \
                self.outputs[f"{GlossaryEnergy.TechnoDetailedPricesValue}:{resource}_needs"] * self.inputs[f"{GlossaryEnergy.ResourcesPriceValue}:{resource}"]
            self.outputs[f"{GlossaryEnergy.CostOfResourceUsageValue}:Total"] += self.outputs[f"{GlossaryEnergy.CostOfResourceUsageValue}:{resource}"]


    def compute_cost_of_other_streams_usage(self):
        """Cost of usage of stream S per unit of current stream produced =
        Need of stream S by unit of production of current stream * Price per unit of production of stream S"""
        self.outputs[f"{GlossaryEnergy.CostOfStreamsUsageValue}:{GlossaryEnergy.Years}"] = self.years
        self.outputs[f"{GlossaryEnergy.CostOfStreamsUsageValue}:Total"] = self.zeros_array
        for stream in self.inputs[GlossaryEnergy.StreamsUsedForProductionValue]:
            self.outputs[f"{GlossaryEnergy.CostOfStreamsUsageValue}:{stream}"] = \
                self.outputs[f"{GlossaryEnergy.TechnoDetailedPricesValue}:{stream}_needs"] * self.inputs[f"{GlossaryEnergy.StreamPricesValue}:{stream}"]
            self.outputs[f"{GlossaryEnergy.CostOfStreamsUsageValue}:Total"] += self.outputs[f"{GlossaryEnergy.CostOfStreamsUsageValue}:{stream}"]


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

    def compute_capex(self):
        """
        Compute Capital expenditures (immobilisations)
        depending on the demand on the technology

        unit : $ / MWh
        """
        invests = self.inputs[f'{GlossaryEnergy.InvestLevelValue}:{GlossaryEnergy.InvestValue}'] * 1e3  # G$ to M$
        self.inputs['techno_infos_dict'] = self.inputs['techno_infos_dict']
        expo_factor = self.compute_expo_factor()
        initial_capex = self.capex_unity_harmonizer()
        if expo_factor != 0.0:
            capacity_factor = None
            if 'capacity_factor_at_year_end' in self.inputs['techno_infos_dict'] and 'capacity_factor' in self.inputs['techno_infos_dict']:
                capacity_factor = np.linspace(self.inputs['techno_infos_dict']['capacity_factor'],
                                                   self.inputs['techno_infos_dict']['capacity_factor_at_year_end'],
                                                   len(self.years))

            capex_calc_list = []
            invest_sum = self.inputs['initial_production'] * initial_capex
            capex_year = initial_capex

            for i, invest in enumerate(invests):

                # below 1M$ investments has no influence on learning rate for capex
                # decrease
                if invest_sum < 10.0 or i == 0:
                    # first capex calculation
                    capex_year = initial_capex
                else:
                    if capacity_factor is not None:
                        ratio_invest = ((invest_sum + invest) / invest_sum *
                                        (capacity_factor[i] / self.inputs['techno_infos_dict']['capacity_factor'])) \
                                       ** (-expo_factor)

                    else:
                        ratio_invest = ((invest_sum + invest) / invest_sum) ** (-expo_factor)

                    # Check that the ratio is always above 0.95 but no strict threshold for
                    # optim is equal to 0.92 when tends to zero:
                    if ratio_invest < 0.95:
                        ratio_invest = 0.9 + 0.05 * np.exp(ratio_invest - 0.9)
                    capex_year = capex_year * ratio_invest

                capex_calc_list.append(capex_year)
                invest_sum += invest

            if 'maximum_learning_capex_ratio' in self.inputs['techno_infos_dict']:
                maximum_learning_capex_ratio = self.inputs['techno_infos_dict']['maximum_learning_capex_ratio']
            else:
                # if maximum learning_capex_ratio is not specified, the learning
                # rate on capex ratio cannot decrease the initial capex mor ethan
                # 10%
                maximum_learning_capex_ratio = 0.9

            capex_calc_list = initial_capex * (maximum_learning_capex_ratio + (1.0 - maximum_learning_capex_ratio) * np.array(capex_calc_list) / initial_capex)
        else:
            capex_calc_list = initial_capex * np.ones(len(invests))

        return np.array(capex_calc_list)

    def compute_expo_factor(self):

        progress_ratio = 1.0 - self.inputs['techno_infos_dict']['learning_rate']
        expo_factor = -np.log(progress_ratio) / np.log(2.0)

        return expo_factor

    def compute_capital_recovery_factor(self):
        """
        Compute annuity factor with the Weighted averaged cost of capital
        and the lifetime of the selected solution
        """
        wacc = self.inputs['techno_infos_dict']['WACC']

        capital_recovery_factor = (wacc * (1.0 + wacc) ** self.inputs[GlossaryEnergy.LifetimeName]) / ((1.0 + wacc) ** self.inputs[GlossaryEnergy.LifetimeName] - 1.0)

        return capital_recovery_factor

    def capex_unity_harmonizer(self):
        """
        Put all capex in $/MWh
        """
        capex_init = None # intialize capex init variable
        data_tocheck = self.inputs['techno_infos_dict']
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
            efficiency = np.array([self.sigmoid_function(i, efficiency_max, efficiency_ini, middle_evolution_year, efficiency_slope) for i in years])

        else:
            efficiency = self.inputs['techno_infos_dict']['efficiency'] * np.ones_like(self.years)

        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency'] = efficiency
    
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

        self.outputs[f'CO2_emissions_detailed:{GlossaryEnergy.Years}'] = self.years
        self.compute_scope_1_emissions()
        self.compute_scope_2_emissions()

        self.outputs[f'CO2_emissions_detailed:{self.name}'] = self.outputs['CO2_emissions_detailed:production'] + self.outputs['CO2_emissions_detailed:Scope 2']

        self.outputs[f'{GlossaryEnergy.CO2EmissionsValue}:{GlossaryEnergy.Years}'] = self.years
        self.outputs[f'{GlossaryEnergy.CO2EmissionsValue}:{self.name}'] = self.outputs[f'CO2_emissions_detailed:{self.name}']


    def compute_scope_1_emissions(self):
        """Compute scope 1 emissions : emissions due to production"""
        if 'CO2_from_production' not in self.inputs['techno_infos_dict']:
            self.outputs['CO2_emissions_detailed:production'] = self.get_theoretical_co2_prod(unit='kg/kWh') + self.zeros_array
        elif self.inputs['techno_infos_dict']['CO2_from_production'] == 0.0:
            self.outputs['CO2_emissions_detailed:production'] = self.zeros_array
        else:
            if self.inputs['techno_infos_dict']['CO2_from_production_unit'] == 'kg/kg':
                self.outputs['CO2_emissions_detailed:production'] = self.inputs['techno_infos_dict']['CO2_from_production'] / \
                                                      self.inputs['data_fuel_dict']['high_calorific_value'] + self.zeros_array
            elif self.inputs['techno_infos_dict']['CO2_from_production_unit'] == 'kg/kWh':
                self.outputs['CO2_emissions_detailed:production'] = self.inputs['techno_infos_dict']['CO2_from_production'] + self.zeros_array

    def compute_scope_2_emissions(self):
        """Computes the Scope 2 CO2 emissions : due to resources and energies usage"""
        self.outputs['CO2_emissions_detailed:Scope 2'] = self.zeros_array
        self.compute_co2_emissions_from_ressources_usage()
        self.compute_co2_emissions_from_streams_usage()

    def compute_resources_needs(self):
        """To be overloaded when techno relies on resources"""
        pass

    def compute_other_streams_needs(self):
        """To be overloaded when techno uses other technos productions to produce its energy"""
        pass

    def compute_specifif_costs_of_technos(self):
        """To be overloaded when techno relies on resources"""
        self.outputs[f"{GlossaryEnergy.SpecificCostsForProductionValue}:{GlossaryEnergy.Years}"] = self.years
        self.outputs[f"{GlossaryEnergy.SpecificCostsForProductionValue}:Total"] = 0.

    def compute_co2_tax(self):
        '''
        CO2 taxes are in $/tCO2
        Need to be computed in $/MWh H2
        Only CO2 emitted from the technology is here taken into account to compute CO2 taxes
        If carbon emissions are negative then no negative CO2 taxes (use a clip on the column)
        '''
        CO2_taxes_kwh = self.inputs[f'{GlossaryEnergy.CO2TaxesValue}:{GlossaryEnergy.CO2Tax}'] * np.maximum(self.outputs[f'CO2_emissions_detailed:{self.name}'], 0)
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:CO2_taxes_factory'] = CO2_taxes_kwh

    @abstractmethod
    def get_theoretical_co2_prod(self, unit='kg/kWh') -> float:
        ''' 
        Get the theoretical CO2 production for a given technology,
        Need to be overloaded in each technology model (example in SMR)
        '''
        return 0.0

    def compute_primary_production(self):
        '''
        Compute the aging distribution production of primary energy for years of study
        Start with the initial distribution and add a year on the age each year
        Add also the yearly production regarding the investment
        All productions older than the lifetime are removed from the dataframe
        '''

        # production from historical plants
        lifetime = self.inputs[GlossaryEnergy.LifetimeName]
        historical_plants_production = self.zeros_array
        initial_age_distrib = self.outputs['initial_age_distrib:distrib']
        fraction_of_historical_plants_still_active = np.flip(np.tril(initial_age_distrib)).sum(axis=1) / 100
        n_years = len(self.years)
        historical_plants_production[:min(lifetime, n_years)] += self.inputs['initial_production'] * fraction_of_historical_plants_still_active[:min(lifetime, n_years)]

        # production from newly builted plants (construction delay already taken into account into prod from invests)
        new_installations_production_capacity = self.outputs[f'{GlossaryEnergy.TechnoDetailedProductionValue}:new_installations_production_capacity']
        mask_prod = np.zeros((n_years, n_years)).astype(int)
        for i in range(n_years):
            mask_prod[i, i: min(n_years, i + lifetime)] = 1

        production_newly_builted_plants = np.maximum(mask_prod.T @ new_installations_production_capacity, 1e-3)
        total_production = historical_plants_production + production_newly_builted_plants

        self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:{GlossaryEnergy.Years}'] = self.years
        self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:{self.energy_name} ({self.product_unit})'] = total_production

        self.outputs[f'{GlossaryEnergy.TechnoDetailedProductionValue}:{GlossaryEnergy.Years}'] = self.years
        self.outputs[f'{GlossaryEnergy.TechnoDetailedProductionValue}:{self.energy_name} ({self.product_unit})'] = total_production
        self.outputs[f'{GlossaryEnergy.TechnoDetailedProductionValue}:production_historical_plants'] = historical_plants_production
        self.outputs[f'{GlossaryEnergy.TechnoDetailedProductionValue}:production_newly_builted_plants'] = production_newly_builted_plants

    def compute_mean_age_of_production(self):
        """Computes the average age of the producing plants"""
        lifetime = self.inputs[GlossaryEnergy.LifetimeName]
        historical_plants_production = self.outputs[f'{GlossaryEnergy.TechnoDetailedProductionValue}:production_historical_plants']
        initial_age_distrib = self.outputs['initial_age_distrib:distrib']
        bb = np.flip(np.tril(initial_age_distrib))
        bb = (bb.T / bb.sum(axis=1)).T
        mean_age_historical_prod = bb @ np.arange(0, lifetime)
        mean_age_historical_prod_complete = self.zeros_array
        n_years = len(self.years)
        mean_age_historical_prod_complete[:min(n_years, lifetime)] = mean_age_historical_prod[:min(n_years, lifetime)]

        # production from newly builted plants (construction delay already taken into account into prod from invests)
        mask_age = np.zeros((n_years, n_years)).astype(int)
        ages = np.concatenate([np.arange(0, lifetime), np.array([0] * (n_years - lifetime))])
        for i in range(n_years):
            mask_age[i, i:] = ages[:n_years - i]

        new_installations_production_capacity = self.outputs[f'{GlossaryEnergy.TechnoDetailedProductionValue}:new_installations_production_capacity']
        mean_age_of_new_producing_plants = (mask_age.T @ new_installations_production_capacity) / self.outputs[f'{GlossaryEnergy.TechnoDetailedProductionValue}:production_newly_builted_plants']
        total_production = self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:{self.energy_name} ({self.product_unit})']
        production_newly_builted_plants = self.outputs[f'{GlossaryEnergy.TechnoDetailedProductionValue}:production_newly_builted_plants']

        mean_age_of_production = (mean_age_historical_prod_complete * historical_plants_production + mean_age_of_new_producing_plants * production_newly_builted_plants) / total_production
        self.outputs[f'mean_age_production:{GlossaryEnergy.Years}'] = self.years
        self.outputs['mean_age_production:mean age'] = mean_age_of_production

    def compute_primary_installed_capacity(self):

        if 'full_load_hours' in self.inputs['techno_infos_dict']:
            full_load_hours = self.inputs['techno_infos_dict']['full_load_hours']
        else:
            full_load_hours = 8760.0

        # Conversion from TWh to MW : divide by hours and multiply by 1000
        newly_installed_capacity = self.outputs[f'{GlossaryEnergy.TechnoDetailedProductionValue}:new_installations_production_capacity'] / full_load_hours * 1e3
        total_installed_capacity =  self.outputs[f'{GlossaryEnergy.TechnoDetailedProductionValue}:{self.energy_name} ({self.product_unit})'] / full_load_hours * 1e3
        
        self.outputs[f'{GlossaryEnergy.InstalledCapacity}:{GlossaryEnergy.Years}'] = self.years
        self.outputs[f'{GlossaryEnergy.InstalledCapacity}:newly_installed_capacity'] = newly_installed_capacity
        self.outputs[f'{GlossaryEnergy.InstalledCapacity}:total_installed_capacity'] = total_installed_capacity

        removed_installed_capacity = total_installed_capacity[:-1] - total_installed_capacity[1:] + newly_installed_capacity[1:]
        removed_installed_capacity = np.concatenate([[0.], removed_installed_capacity])
        self.outputs[f'{GlossaryEnergy.InstalledCapacity}:removed_installed_capacity'] = removed_installed_capacity

    def compute_new_installations_production_capacity(self):
        '''
        Compute the newly installed (from investments) power production in TWh
        Add a delay for factory construction
        '''

        years_before_year_start = np.arange(self.year_start - self.inputs[GlossaryEnergy.ConstructionDelay], self.year_start)
        invest_before_year_start = self.inputs[f'{GlossaryEnergy.InvestmentBeforeYearStartValue}:{GlossaryEnergy.InvestValue}'] # G$
        capex_after_year_start = self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:Capex_{self.name}'] # $ / MWh
        capex_year_start = capex_after_year_start[0]
        capexes_before_year_start = np.array([capex_year_start] * len(years_before_year_start))

        invest_after_year_start = self.inputs[f'{GlossaryEnergy.InvestLevelValue}:{GlossaryEnergy.InvestValue}'] # in G$
        invests_period_of_interest = np.concatenate([invest_before_year_start, invest_after_year_start])
        capex_period_of_interest = np.concatenate([capexes_before_year_start, capex_after_year_start])
        new_installations_production_capacity = invests_period_of_interest / capex_period_of_interest * 1e3 # G$ / ($/ MWh) = (G * MWh) = 10^9 * 10^6 Wh = 10^15 Wh = k TWh so multiply by 1e3 to get TWh

        # keep only prod for years >= year_start and <= year_end
        new_installations_production_capacity = new_installations_production_capacity[:len(self.years)]

        self.outputs[f'{GlossaryEnergy.TechnoDetailedProductionValue}:new_installations_production_capacity'] = new_installations_production_capacity


    def compute_land_use(self):
        ''' Set the compute land use dataframe

            to be overloaded in sub class
        '''

        self.outputs[f'{GlossaryEnergy.LandUseRequiredValue}:{GlossaryEnergy.Years}'] = self.years
        self.outputs[f'{GlossaryEnergy.LandUseRequiredValue}:{self.name} (Gha)'] = 0.0

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
            self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:{GHG_type} ({GlossaryEnergy.mass_unit})'] = emission_factor * \
                                                                         self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:{self.energy_name} ({self.product_unit})']
        else:
            self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:{GHG_type} ({GlossaryEnergy.mass_unit})'] = emission_factor * \
                                                                         self.outputs[f'{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}:{related_to} ({self.product_unit})']

    def apply_utilisation_ratio(self):
        """
        Apply utilisation ratio percentage to
        - consumption
        - production
        """
        self.outputs[f'{GlossaryEnergy.TechnoConsumptionValue}:{GlossaryEnergy.Years}'] = self.years
        utilisation_ratio = self.inputs[f'{GlossaryEnergy.UtilisationRatioValue}:{GlossaryEnergy.UtilisationRatioValue}'] / 100.
        for column in self.get_colnames_output_dataframe(GlossaryEnergy.TechnoConsumptionWithoutRatioValue, expect_years=True):
            self.outputs[f'{GlossaryEnergy.TechnoConsumptionValue}:{column}'] = self.outputs[f'{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}:{column}'] * utilisation_ratio

        self.outputs[f'{GlossaryEnergy.TechnoProductionValue}:{GlossaryEnergy.Years}'] = self.years
        for column in self.get_colnames_output_dataframe(GlossaryEnergy.TechnoProductionWithoutRatioValue, expect_years=True):
            self.outputs[f'{GlossaryEnergy.TechnoProductionValue}:{column}'] = self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:{column}'] * utilisation_ratio

    def compute_streams_and_resources_costs(self):
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:energy_and_resources_costs'] = \
            self.outputs[f"{GlossaryEnergy.CostOfResourceUsageValue}:Total"] +\
            self.outputs[f"{GlossaryEnergy.CostOfStreamsUsageValue}:Total"] +\
            self.outputs[f"{GlossaryEnergy.SpecificCostsForProductionValue}:Total"]

    def compute_co2_emissions_from_ressources_usage(self):
        """Computes the co2 emissions due to resources usage"""
        for resource in self.inputs[GlossaryEnergy.ResourcesUsedForProductionValue]:
            self.outputs[f'CO2_emissions_detailed:{resource}'] = self.outputs[f"{GlossaryEnergy.TechnoDetailedPricesValue}:{resource}_needs"] * self.inputs[f'{GlossaryEnergy.RessourcesCO2EmissionsValue}:{resource}']
            self.outputs['CO2_emissions_detailed:Scope 2'] += self.outputs[f'CO2_emissions_detailed:{resource}']

    def compute_co2_emissions_from_streams_usage(self):
        """Computes the co2 emissions due to streams usage"""
        for stream in self.inputs[GlossaryEnergy.StreamsUsedForProductionValue]:
            self.outputs[f'CO2_emissions_detailed:{stream}'] = self.outputs[f"{GlossaryEnergy.TechnoDetailedPricesValue}:{stream}_needs"] * self.inputs[f'{GlossaryEnergy.StreamsCO2EmissionsValue}:{stream}']
            self.outputs['CO2_emissions_detailed:Scope 2'] += self.outputs[f'CO2_emissions_detailed:{stream}']

    def compute_newly_installed_capacity_resource_consumption(self):
        """
        Here is computed the resource consumption by the building of new plants.
        Independant from utilisation ratio value.
        Resource R consumption (year) = Newly installed Power Production in MW (year) * Resource R needs (in Mt) for building 1 MW of installed power.
        """
        for resource in self.inputs[GlossaryEnergy.ResourcesUsedForBuildingValue]:
            self.outputs[f"{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}:{resource} ({GlossaryEnergy.mass_unit})"] =\
                self.inputs['techno_infos_dict'][f"{resource}_needs"] * self.outputs[f"{GlossaryEnergy.InstalledCapacity}:newly_installed_capacity"]

            self.outputs[
                f"{GlossaryEnergy.TechnoConsumptionValue}:{resource} ({GlossaryEnergy.mass_unit})"] = \
                self.inputs['techno_infos_dict'][f"{resource}_needs"] * self.outputs[
                    f"{GlossaryEnergy.InstalledCapacity}:newly_installed_capacity"]

    def compute(self):
        self.configure_parameters_update()
        # -- compute informations
        self.compute_initial_age_distribution()
        self.compute_price()
        self.compute_initial_plants_historical_prod()
        self.compute_new_installations_production_capacity()
        self.compute_primary_production()
        self.compute_mean_age_of_production()
        self.compute_land_use()
        self.compute_consumption_wo_ratio()

        self.compute_byproducts_production()
        self.compute_primary_installed_capacity()

        # ratios : utilisation & resources
        self.apply_utilisation_ratio()
        self.compute_newly_installed_capacity_resource_consumption()
        self.select_concerning_ratios()
        self.apply_limiting_ratio()

        self.compute_capital()

    def compute_initial_age_distribution(self):
        initial_value = 1
        decay_rate = self.inputs[GlossaryEnergy.InitialPlantsAgeDistribFactor]
        n_year = self.inputs[GlossaryEnergy.LifetimeName]

        total_sum = sum(initial_value * (decay_rate ** i) for i in range(n_year))
        distribution = [(initial_value * (decay_rate ** i) / total_sum) * 100 for i in range(n_year)]
        distrib = np.flip(distribution)
        self.outputs["initial_age_distrib:age"] = np.arange(self.inputs[GlossaryEnergy.LifetimeName])
        self.outputs["initial_age_distrib:distrib"] = distrib

    def compute_initial_plants_historical_prod(self):
        energy = self.outputs['initial_age_distrib:distrib'] / 100.0 * self.inputs['initial_production']

        self.outputs[f'{GlossaryEnergy.InitialPlantsTechnoProductionValue}:{GlossaryEnergy.Years}'] = np.flip(self.year_start - 1 - self.outputs['initial_age_distrib:age'])
        self.outputs[f'{GlossaryEnergy.InitialPlantsTechnoProductionValue}:energy ({self.product_unit})'] = np.flip(energy)
        self.outputs[f'{GlossaryEnergy.InitialPlantsTechnoProductionValue}:cum energy ({self.product_unit})'] = np.cumsum(self.outputs[f'{GlossaryEnergy.InitialPlantsTechnoProductionValue}:energy ({self.product_unit})'])

    def compute_consumption_wo_ratio(self):
        self.outputs[f'{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}:{GlossaryEnergy.Years}'] = self.years
        self.compute_resource_consumption()
        self.compute_streams_consumption()



def cons_smooth_maximum_vect(cst, alpha=1E16):
    """
    Conservative smooth maximum function.
    This modified version of the smooth_max adds an epsilon value to the smoothed value
    in order to have a conservative value (always smooth_value > max(values))
    """
    cst_array = np.array(cst)
    max_exp = 650  # max value for exponent input, higher value gives infinity
    min_exp = -300
    max_alphax = np.amax(alpha * cst_array, axis=1)

    k = max_alphax - max_exp
    # Deal with underflow . max with exp(-300)
    exp_func = np.maximum(min_exp, alpha * cst_array -
                          np.repeat(k, cst_array.shape[1]).reshape(cst_array.shape))
    den = np.sum(np.exp(exp_func), axis=1)
    num = np.sum(cst_array * np.exp(exp_func), axis=1)
    result = np.where(den != 0, num / den + 0.3 / alpha, np.amax(cst_array, axis=1))
    if (den == 0).any():
        print('Warning in smooth_maximum! den equals 0, hard max is used')

    return result
