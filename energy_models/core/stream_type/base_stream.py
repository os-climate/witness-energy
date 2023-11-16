'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/14-2023/11/09 Copyright 2023 Capgemini

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
from copy import deepcopy

from climateeconomics.glossarycore import GlossaryCore
from energy_models.glossaryenergy import GlossaryEnergy


class BaseStream:
    """
    Class for energy production technology type
    """
    name = ''
    unit = ''
    default_techno_list = []
    # If the prod_element is negligible do not take into account this element
    # It is negligible if min_prod = 10-3 TWh
    min_prod = 1.0e-3

    def __init__(self, name):
        '''
        Constructor
        '''
        self.name = name
        #-- Inputs attributes set from configure method
        self.year_start = 2020  # year start
        self.year_end = 2100  # year end
        self.min_prod = 1e-3
        self.subelements_list = []
        self.total_prices = None  # energy outputs dataframe

        self.sub_production_dict = {}
        self.sub_consumption_dict = {}
        self.sub_consumption_woratio_dict = {}
        self.sub_land_use_required_dict = {}

    def reload_df(self):
        '''
        Reload all dataframes with new year start and year end 
        '''
        self.years = np.arange(self.year_start, self.year_end + 1)
        base_df = pd.DataFrame({GlossaryCore.Years: self.years})
        self.sub_prices = base_df.copy(deep=True)
        self.sub_prices_wo_taxes = base_df.copy(deep=True)
        self.total_prices = base_df.copy(deep=True)
        self.total_carbon_emissions = base_df.copy(deep=True)
        self.sub_carbon_emissions = base_df.copy(deep=True)
        self.co2_emitted_by_energy = base_df.copy(deep=True)
        self.mix_weights = base_df.copy(deep=True)
        self.price_by_energy = base_df.copy(deep=True)
        self.production = base_df.copy(deep=True)
        self.production_raw = base_df.copy(deep=True)
        self.production_by_techno = base_df.copy(deep=True)
        self.consumption = base_df.copy(deep=True)
        self.land_use_required = base_df.copy(deep=True)

    def configure(self, inputs_dict):
        self.configure_parameters(inputs_dict)
        self.configure_parameters_update(inputs_dict)

    def configure_parameters(self, inputs_dict):
        '''
        Configure at init
        '''
        self.year_start = inputs_dict[GlossaryCore.YearStart]
        self.year_end = inputs_dict[GlossaryCore.YearEnd]

        self.reload_df()

    def configure_parameters_update(self, inputs_dict):
        '''
        Configure before each run
        '''
        for element in self.subelements_list:
            self.sub_prices[element] = inputs_dict[f'{element}.{GlossaryCore.TechnoPricesValue}'][element]
            self.sub_prices_wo_taxes[element] = inputs_dict[
                f'{element}.{GlossaryCore.TechnoPricesValue}'][f'{element}_wotaxes']
            # Unscale techno production and consumption
            self.sub_production_dict[element] = deepcopy(
                inputs_dict[f'{element}.{GlossaryCore.TechnoProductionValue}'])
            self.sub_consumption_dict[element] = deepcopy(
                inputs_dict[f'{element}.{GlossaryCore.TechnoConsumptionValue}'])
            self.sub_consumption_woratio_dict[element] = deepcopy(
                inputs_dict[f'{element}.{GlossaryCore.TechnoConsumptionWithoutRatioValue}'])
            for column in self.sub_production_dict[element].columns:
                if column == GlossaryCore.Years:
                    continue
                self.sub_production_dict[element][column] = self.sub_production_dict[element][column].values * \
                    inputs_dict['scaling_factor_techno_production']
            for column in self.sub_consumption_dict[element].columns:
                if column == GlossaryCore.Years:
                    continue
                self.sub_consumption_dict[element][column] = self.sub_consumption_dict[element][column].values * \
                    inputs_dict['scaling_factor_techno_consumption']
                self.sub_consumption_woratio_dict[element][column] = self.sub_consumption_woratio_dict[element][column].values * \
                    inputs_dict['scaling_factor_techno_consumption']
            self.sub_land_use_required_dict[element] = inputs_dict[f'{element}.{GlossaryCore.LandUseRequiredValue}']

    def compute(self, exp_min=True):
        '''
        Compute all energy variables with its own technologies 
        '''

        _, self.consumption_woratio, _ = self.compute_production(
            self.sub_production_dict, self.sub_consumption_woratio_dict)

        self.production, self.consumption, self.production_by_techno = self.compute_production(
            self.sub_production_dict, self.sub_consumption_dict)

        self.compute_price(exp_min=exp_min)

        self.aggregate_land_use_required()

        return self.total_prices, self.production, self.consumption, self.consumption_woratio, self.mix_weights

    def compute_production(self, sub_production_dict, sub_consumption_dict):
        '''
        Compute energy production by summing all energy productions
        And compute the techno_mix_weights each year
        '''

        # Initialize dataframe out
        base_df = pd.DataFrame({GlossaryCore.Years: self.years})
        production = base_df.copy(deep=True)
        consumption = base_df.copy(deep=True)
        production_by_techno = base_df.copy(deep=True)

        # Loop on technologies
        production[f'{self.name}'] = 0.
        for element in self.subelements_list:
            production_by_techno[f'{self.name} {element} ({self.unit})'] = sub_production_dict[
                element][f'{self.name} ({self.unit})'].values
            production[
                f'{self.name}'] += production_by_techno[f'{self.name} {element} ({self.unit})'].values

            production, consumption = self.compute_other_consumption_production(
                element, sub_production_dict, sub_consumption_dict, production, consumption)

        return production, consumption, production_by_techno

    def compute_other_consumption_production(self, element, sub_production_dict, sub_consumption_dict, production, consumption, factor=1.0):
        '''
        Compute other consumption and production
        '''

        for elem, prod in sub_production_dict[element].items():
            # DO not count major energy production in this function (already
            # computed)
            if elem != f'{self.name} ({self.unit})' and elem != GlossaryCore.Years:
                if elem in production:
                    production[elem] += prod.values * factor
                else:
                    production[elem] = prod.values * factor

        for elem, cons in sub_consumption_dict[element].items():
            if elem != GlossaryCore.Years:
                if elem in consumption:
                    consumption[elem] += cons.values * factor
                else:
                    consumption[elem] = cons.values * factor

        return production, consumption

    def compute_energy_type_capital(self, inputs):
        technos = inputs[GlossaryCore.techno_list]
        capitals = [
            inputs[f"{techno}.{GlossaryEnergy.TechnoCapitalDfValue}"][GlossaryEnergy.Capital].values for techno in technos
        ]
        sum_technos_capital = np.sum(capitals, axis=0)

        self.energy_type_capital = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.Capital: sum_technos_capital,
        })

    def compute_price(self, exp_min=True):
        '''
        Compute the price with all sub_prices and sub weights computed with total production 
        '''

        self.total_prices[self.name] = 0.
        self.total_prices[f'{self.name}_wotaxes'] = 0.

        element_list = self.subelements_list
        full_element_list = [
            f'{self.name} {element} ({self.unit})' for element in element_list]
        element_dict = dict(zip(element_list, full_element_list))
        if exp_min:
            prod_element, prod_total_for_mix_weight = self.compute_prod_with_exp_min(
                self.production_by_techno, element_dict, self.min_prod)
        else:
            prod_element, prod_total_for_mix_weight = self.compute_prod_wcutoff(
                self.production_by_techno, element_dict, self.min_prod)
        for element in self.subelements_list:
            # we compute then mix_weight with these prods minimized and use it
            # also for co2 emissions
            mix_weight = prod_element[element] / \
                prod_total_for_mix_weight
            # Still If the element is negligible do not take into account this element
            # It is negligible if tol = 0.1%
            tol = 1e-3
            mix_weight[mix_weight < tol] = 0.0
            self.mix_weights[element] = mix_weight * 100.

            self.total_prices[self.name] += self.sub_prices[element] * mix_weight
            self.total_prices[f'{self.name}_wotaxes'] += self.sub_prices_wo_taxes[element] * mix_weight
            self.mix_weights[element] = mix_weight * 100.
        # In case all the technologies are below the threshold
        # and the cutoff is applied, assign a placeholder price
        if not exp_min:
            for year in self.total_prices[GlossaryCore.Years].values:
                if np.real(self.total_prices.loc[self.total_prices[GlossaryCore.Years] == year][self.name].values) == 0.0:
                    # Get the min_price of the technos this year that are > 0.0
                    year_techno_prices = self.sub_prices[self.subelements_list].loc[self.sub_prices[GlossaryCore.Years] == year]
                    min_techno_price = min(
                        val for val in year_techno_prices.values[0] if val > 0.0)
                    min_techno_name = [
                        name for name in year_techno_prices.columns if year_techno_prices[name].values == min_techno_price][0]
                    for element in self.subelements_list:
                        self.mix_weights.loc[self.mix_weights[GlossaryCore.Years] == year,
                                             element] = 100. if element == min_techno_name else 0.0
                    min_techno_price_wo_taxes = self.sub_prices_wo_taxes[min_techno_name]
                    self.total_prices.loc[self.total_prices[GlossaryCore.Years] ==
                                          year, self.name] = min_techno_price
                    self.total_prices.loc[self.total_prices[GlossaryCore.Years] ==
                                          year, f'{self.name}_wotaxes'] = min_techno_price_wo_taxes

    def compute_prod_wcutoff(self, production_by_techno, elements_dict, min_prod):

        prod_total_for_mix_weight = np.zeros(len(self.years))
        prod_element_dict = {}
        for key, value in elements_dict.items():
            prod_element_dict[key] = deepcopy(production_by_techno[
                value].values)
            prod_element_dict[key][prod_element_dict[key]
                                   < min_prod] = 0.0
            prod_total_for_mix_weight = prod_total_for_mix_weight + \
                prod_element_dict[key]
        prod_total_for_mix_weight[prod_total_for_mix_weight == 0.0] = min_prod

        return prod_element_dict, prod_total_for_mix_weight

    def compute_dprod_wcutoff(self, production_by_techno, elements_dict, min_prod):

        prod_element_dict = {}
        dprod_element_dict = {}

        for key, value in elements_dict.items():
            prod_element_dict[key] = deepcopy(production_by_techno[
                value].values)
            dprod_element_dict[key] = np.ones(
                len(prod_element_dict[key]))
            dprod_element_dict[key][prod_element_dict[key]
                                    < min_prod] = 0.0

        return dprod_element_dict

    def compute_prod_with_exp_min(self, production_by_techno, elements_dict, min_prod):
        '''
        Compute the production of each element by minimizing them with and exponential function to reach min prod
        Objective is to decrease gradients when prod are very low 
        Be careful the objective is to increase the total production to
        decrease the gradient then we have to modify the sum also

        BIG WARNING : there is an issue in the handling of complex number in this function that may cause small errors 
        in gradient tests. So far, no solution has been found. This error can be reproduced by running the test on the 
        gradients of liquid_hydrogen stream in the case of a production of techno HydrogenLiquefaction below min_prod.

        elements_dict contains {Name of the prod techno or energy: full name of the column}
        '''

        prod_total_for_mix_weight = np.zeros(len(self.years))
        prod_element_dict = {}
        for key, value in elements_dict.items():
            prod_element_dict[key] = deepcopy(production_by_techno[
                value].values)

            if prod_element_dict[key].min() < min_prod:
                # if some values are below min_prod
                # We use the exp smoothing only on values below self.min_prod (np.minimum(prod_element, min_prod))
                # Then we take the maximum to take prod_element if it is higher
                # than min_prod
                # To avoid underflow : exp(-200) is considered to be the
                # minimum value for the exp
                prod_element_dict[key][prod_element_dict[key]
                                       < -200.0 * min_prod] = -200.0 * min_prod
                prod_element_dict[key] = np.maximum(
                    min_prod / 10.0 * (9.0 + np.exp(np.minimum(prod_element_dict[key], min_prod) / min_prod)
                                       * np.exp(-1)), prod_element_dict[key])

            prod_total_for_mix_weight = prod_total_for_mix_weight + \
                prod_element_dict[key]

        return prod_element_dict, prod_total_for_mix_weight

    def compute_dprod_with_exp_min(self, production_by_techno, elements_dict, min_prod):

        prod_element_dict = {}
        dprod_element_dict = {}

        for key, value in elements_dict.items():
            prod_element_dict[key] = deepcopy(production_by_techno[
                value].values)
            dprod_element_dict[key] = np.ones(
                len(prod_element_dict[key]))
            if prod_element_dict[key].min() < min_prod:
                # To avoid underflow : exp(-200) is considered to be the
                # minimum value for the exp
                prod_element_dict[key][prod_element_dict[key]
                                       < -200.0 * min_prod] = -200.0 * min_prod
                dprod_element_dict[key][prod_element_dict[key] < min_prod] = np.exp(
                    prod_element_dict[key][prod_element_dict[key] < min_prod] / min_prod) * np.exp(-1) / 10.0

        return dprod_element_dict

    def compute_grad_element_mix_vs_prod(self, production_by_techno, elements_dict, exp_min=True, min_prod=1e-3):
        if exp_min:
            prod_element_dict, prod_total_for_mix_weight = self.compute_prod_with_exp_min(
                production_by_techno, elements_dict, min_prod)
            dprod_element_dict = self.compute_dprod_with_exp_min(
                production_by_techno, elements_dict, min_prod)
        else:
            prod_element_dict, prod_total_for_mix_weight = self.compute_prod_wcutoff(
                production_by_techno, elements_dict, min_prod)
            dprod_element_dict = self.compute_dprod_wcutoff(
                production_by_techno, elements_dict, min_prod)
        grad_element_mix_vs_prod = {}

        for element in elements_dict.keys():
            grad_element_mix_vs_prod[f'{element}'] = dprod_element_dict[element] * (
                prod_total_for_mix_weight - prod_element_dict[element]) / prod_total_for_mix_weight**2
            for element_other in elements_dict.keys():
                if element_other != element:
                    grad_element_mix_vs_prod[f'{element} {element_other}'] = -dprod_element_dict[element] * \
                        prod_element_dict[element_other] / \
                        prod_total_for_mix_weight**2

        return grad_element_mix_vs_prod

    def aggregate_land_use_required(self):
        '''
        Aggregate into an unique dataframe of information of sub technology about land use required
        '''

        for element in self.sub_land_use_required_dict.values():

            element_columns = list(element)
            element_columns.remove(GlossaryCore.Years)

            for column_df in element_columns:
                self.land_use_required[column_df] = element[column_df]
