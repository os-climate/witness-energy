'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/09-2024/06/24 Copyright 2023 Capgemini

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
from sostrades_core.tools.base_functions.exp_min import compute_dfunc_with_exp_min

from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import (
    GaseousHydrogen,
)
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.techno_type.base_techno_models.liquid_fuel_techno import (
    LiquidFuelTechno,
)
from energy_models.glossaryenergy import GlossaryEnergy


class Refinery(LiquidFuelTechno):
    OIL_RESOURCE_NAME = GlossaryEnergy.OilResource
    # corresponds to crude oil price divided by efficiency TO BE MODIFIED
    oil_extraction_capex = 44.0 / 0.89

    def __init__(self, name):
        super().__init__(name)
        self.other_energy_dict = None
        self.dprod_dinvest = None
        self.dprod_list_dcapex_list = None

    def compute_cost_of_resources_usage(self):
        """
        Cost of resource R = need of resource R x price of resource R

        Does not take oil price into account
        """
        cost_of_resource_usage = {
            GlossaryEnergy.Years: self.years,
        }
        for resource in self.resources_used_for_production:
            if resource == GlossaryEnergy.OilResource:
                # Skip OilResource so not to count it twice
                cost_of_resource_usage[resource] = 0.0
            else:
                cost_of_resource_usage[resource] = self.cost_details[f"{resource}_needs"].values * self.resources_prices[resource].values

        self.cost_of_resources_usage = pd.DataFrame(cost_of_resource_usage)

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

    def configure_energy_data(self, inputs_dict):
        '''
        Configure energy data by reading the data_energy_dict in the right Energy class
        Overloaded for each energy type
        '''
        self.data_energy_dict = inputs_dict['data_fuel_dict']
        self.other_energy_dict = inputs_dict['other_fuel_dict']

    def compute_resources_needs(self):
        # needs in [kWh/kWh] divided by calorific value in [kWh/kg] to have
        # needs in [kg/kWh]
        self.cost_details[f'{self.OIL_RESOURCE_NAME}_needs'] = self.get_fuel_needs(
        ) / self.data_energy_dict['calorific_value'] / self.cost_details['efficiency']

    def compute_other_streams_needs(self):
        self.cost_details[f'{GlossaryEnergy.electricity}_needs'] = self.get_electricity_needs() / self.cost_details['efficiency']
        self.cost_details[f'{GaseousHydrogen.name}_needs'] = self.techno_infos_dict['hydrogen_demand'] / self.cost_details['efficiency']


    def compute_byproducts_production(self):
        for energy in self.other_energy_dict:
            # if it s a dict, so it is a data_energy_dict
            self.production_detailed[f'{energy} ({self.product_unit})'] = self.production_detailed[
                                                                                     f'{self.energy_name} ({self.product_unit})'] * \
                                                                                 self.techno_infos_dict[
                                                                                     'product_break_down'][
                                                                                     energy] / 11.66 * \
                                                                                 self.other_energy_dict[energy][
                                                                                     'calorific_value']

        self.production_detailed[f'{CarbonCapture.flue_gas_name} ({GlossaryEnergy.mass_unit})'] = self.techno_infos_dict[
                                                                                            'CO2_from_production'] / \
                                                                                        self.data_energy_dict[
                                                                                            'calorific_value'] * \
                                                                                        self.production_detailed[
                                                                                            f'{LiquidFuelTechno.energy_name} ({self.product_unit})']
        '''
        Method to compute CH4 emissions from gas production
        The proposed V0 only depends on production.
        Equation is taken from the GAINS model for crude oil
        https://previous.iiasa.ac.at/web/home/research/researchPrograms/air/IR54-GAINS-CH4.pdf
        CH4 emissions can be separated in three categories : flaring,venting and unintended leakage
        emission_factor is in Mt/TWh
        '''
        emission_factor = self.techno_infos_dict['CH4_flaring_emission_factor'] + \
                          self.techno_infos_dict['CH4_venting_emission_factor'] + \
                          self.techno_infos_dict['CH4_unintended_leakage_emission_factor']

        self.production_detailed[f'{Methane.emission_name} ({GlossaryEnergy.mass_unit})'] = emission_factor * \
                                                                                  self.production_detailed[
                                                                                      f'{LiquidFuelTechno.energy_name} ({self.product_unit})'].values

    def compute_prod_from_invest(self):
        '''
        Compute the energy production of a techno from investment in TWh
        Add a delay for factory construction
        '''

        # Reverse the array of invest before year start with [::-1]
        prod_before_ystart = pd.DataFrame(
            {GlossaryEnergy.Years: np.arange(self.year_start - self.construction_delay, self.year_start),
             GlossaryEnergy.InvestValue: self.invest_before_ystart[GlossaryEnergy.InvestValue].values[::1],
             f'Capex_{self.name}': self.cost_details.loc[
                 self.cost_details[GlossaryEnergy.Years] == self.year_start, f'Capex_{self.name}'].values[0]})

        production_from_invest = pd.concat(
            [self.cost_details[[GlossaryEnergy.Years, GlossaryEnergy.InvestValue, f'Capex_{self.name}']],
             prod_before_ystart], ignore_index=True)
        production_from_invest.sort_values(by=[GlossaryEnergy.Years], inplace=True)
        # invest from G$ to M$
        # Added a cost of 44.0$/TWh / 0.89 (efficiency) to account for the price of oil extraction
        # (until an extraction model is connected)
        production_from_invest['prod_from_invest'] = production_from_invest[GlossaryEnergy.InvestValue] / \
                                                     (production_from_invest[f'Capex_{self.name}'] +
                                                      self.oil_extraction_capex)
        production_from_invest[GlossaryEnergy.Years] += self.construction_delay
        production_from_invest = production_from_invest[production_from_invest[GlossaryEnergy.Years]
                                                        <= self.year_end]

        return production_from_invest

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
                              (capex_list[i] + self.oil_extraction_capex)
            len_non_zeros = min(max(0, nb_years -
                                    self.construction_delay - i),
                                self.lifetime)
            first_len_zeros = min(
                i + self.construction_delay, nb_years)
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
        Overwrite the dprod_dcapex derivative to take the added oil extraction capex into account
        '''
        nb_years = len(capex_list)
        dprod_list_dcapex_list = np.zeros(
            (nb_years, nb_years))
        if 'complex128' in [capex_list.dtype, invest_list.dtype, invest_before_year_start.dtype]:
            dprod_list_dcapex_list = np.zeros(
                (nb_years, nb_years), dtype='complex128')
        for i in range(nb_years):
            len_non_zeros = min(max(0, nb_years - self.construction_delay - i),
                                self.lifetime)
            first_len_zeros = min(
                i + self.construction_delay, nb_years)
            last_len_zeros = max(0, nb_years -
                                 len_non_zeros - first_len_zeros)
            # Same for capex
            dpprod_dpcapex = - \
                                 invest_list[i] / (capex_list[i] + self.oil_extraction_capex) ** 2

            dprod_list_dcapex_list[:, i] = np.hstack((np.zeros(first_len_zeros),
                                                      np.ones(
                                                          len_non_zeros) * dpprod_dpcapex,
                                                      np.zeros(last_len_zeros)))
        # but the capex[0] is used for invest before
        # year_start then we need to add it to the first column
        dpprod_dpcapex0_list = [- invest / (capex_list[0] + self.oil_extraction_capex)
                                ** 2 for invest in invest_before_year_start]

        for index, dpprod_dpcapex0 in enumerate(dpprod_dpcapex0_list):
            len_non_zeros = min(
                self.lifetime, nb_years - index)
            dprod_list_dcapex_list[:, 0] += np.hstack((np.zeros(index),
                                                       np.ones(
                                                           len_non_zeros) * dpprod_dpcapex0,
                                                       np.zeros(nb_years - index - len_non_zeros)))

        self.dprod_list_dcapex_list = dprod_list_dcapex_list

        return dprod_list_dcapex_list
