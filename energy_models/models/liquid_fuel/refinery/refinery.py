'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/09-2023/11/16 Copyright 2023 Capgemini

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

from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import GaseousHydrogen
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
from energy_models.core.techno_type.base_techno_models.liquid_fuel_techno import LiquidFuelTechno
from energy_models.glossaryenergy import GlossaryEnergy
from sostrades_core.tools.base_functions.exp_min import compute_func_with_exp_min, compute_dfunc_with_exp_min


class Refinery(LiquidFuelTechno):

    OIL_RESOURCE_NAME = ResourceGlossary.Oil['name']
    # corresponds to crude oil price divided by efficiency TO BE MODIFIED
    oil_extraction_capex = 44.0 / 0.89

    def configure_energy_data(self, inputs_dict):
        '''
        Configure energy data by reading the data_energy_dict in the right Energy class
        Overloaded for each energy type
        '''
        self.data_energy_dict = inputs_dict['data_fuel_dict']
        self.other_energy_dict = inputs_dict['other_fuel_dict']

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs which depends on the technology 
        """

        self.cost_details['elec_needs'] = self.get_electricity_needs()

        self.cost_details[Electricity.name] = list(
            self.prices[Electricity.name] * self.cost_details['elec_needs'] / self.cost_details['efficiency'])
        # needs in [kWh/kWh] divided by calorific value in [kWh/kg] to have
        # needs in [kg/kWh]
        self.cost_details[f'{self.OIL_RESOURCE_NAME}_needs'] = self.get_fuel_needs(
        ) / self.data_energy_dict['calorific_value']
        # resources price [$/t] since needs are in [kg/kWh] to have cost in
        # [$/t]*[kg/kWh]=[$/MWh]
        self.cost_details[self.OIL_RESOURCE_NAME] = list(
            self.resources_prices[self.OIL_RESOURCE_NAME] * self.cost_details[f'{self.OIL_RESOURCE_NAME}_needs'] / self.cost_details['efficiency'])

        # in kWh of hydrogen per kWh of fuel
        self.cost_details[GaseousHydrogen.name] = list(
            self.techno_infos_dict['hydrogen_demand'] * self.prices[GaseousHydrogen.name]) / self.cost_details['efficiency']

        return self.cost_details[Electricity.name] + self.cost_details[self.OIL_RESOURCE_NAME] + self.cost_details[GaseousHydrogen.name]

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices 
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        elec_needs = self.get_electricity_needs()

        return {Electricity.name: np.identity(len(self.years)) * elec_needs,
                GaseousHydrogen.name: np.identity(len(self.years)) * self.techno_infos_dict['hydrogen_demand'],
                }

    def grad_price_vs_resources_price(self):
        '''
        Compute the gradient of global price vs resources prices
        '''
        oil_needs = self.cost_details[f'{self.OIL_RESOURCE_NAME}_needs'].values
        return {
            self.OIL_RESOURCE_NAME: np.identity(
                len(self.years)) * oil_needs,
        }

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ?

        liquid_fuel is the total production
        the break down is made with self.production['kerosene'] ... ect 
        """

        

        for energy in self.other_energy_dict:
            # if it s a dict, so it is a data_energy_dict
            self.production_detailed[f'{energy} ({self.product_energy_unit})'] = self.production_detailed[
                f'{self.energy_name} ({self.product_energy_unit})'] * self.techno_infos_dict['product_break_down'][energy] / 11.66 * self.other_energy_dict[energy]['calorific_value']

        self.production_detailed[f'{CarbonCapture.flue_gas_name} ({self.mass_unit})'] = self.techno_infos_dict['CO2_from_production'] / \
                                                                                        self.data_energy_dict['calorific_value'] * \
                                                                                        self.production_detailed[f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})']
        self.compute_ch4_emissions()
        # Consumption
        self.consumption_detailed[f'{Electricity.name} ({self.product_energy_unit})'] = self.cost_details['elec_needs'] * \
                                                                                        self.production_detailed[f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})']  # in kWH

        # oil consumption: prod [TWh] * needs [kg/kWh] = [Mt]
        self.consumption_detailed[f'{self.OIL_RESOURCE_NAME} ({self.mass_unit})'] = self.cost_details[f'{self.OIL_RESOURCE_NAME}_needs'] * \
                                                                                    self.production_detailed[f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})']  # in Mt

        self.consumption_detailed[f'{GaseousHydrogen.name} ({self.product_energy_unit})'] = self.techno_infos_dict['hydrogen_demand'] * \
                                                                                            self.production_detailed[f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})']     # in kWh

        # self.consumption[f'{mediumheattechno.energy_name} ({self.product_energy_unit})'] = self.techno_infos_dict['medium_heat_production'] *  \
        #     self.production[f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})']     # in kWh

    def compute_ch4_emissions(self):
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

        self.production_detailed[f'{Methane.emission_name} ({self.mass_unit})'] = emission_factor * \
                                                                                  self.production_detailed[f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})'].values

    def compute_CO2_emissions_from_input_resources(self):
        '''
        Need to take into account  CO2 from electricity/fuel production
        '''

        self.carbon_intensity[Electricity.name] = self.energy_CO2_emissions[Electricity.name] * \
                                                       self.cost_details['elec_needs']

        self.carbon_intensity[GaseousHydrogen.name] = self.energy_CO2_emissions[GaseousHydrogen.name] * \
                                                           self.techno_infos_dict['hydrogen_demand']

        self.carbon_intensity[self.OIL_RESOURCE_NAME] = self.resources_CO2_emissions[self.OIL_RESOURCE_NAME] * \
                                                        self.cost_details[f'{self.OIL_RESOURCE_NAME}_needs']

        return self.carbon_intensity[Electricity.name] + \
               self.carbon_intensity[self.OIL_RESOURCE_NAME] + \
               self.carbon_intensity[GaseousHydrogen.name]

    def compute_prod_from_invest(self, construction_delay):
        '''
        Compute the energy production of a techno from investment in TWh
        Add a delay for factory construction
        '''

        # Reverse the array of invest before year start with [::-1]
        prod_before_ystart = pd.DataFrame({GlossaryEnergy.Years: np.arange(self.year_start - construction_delay, self.year_start),
                                           GlossaryEnergy.InvestValue: self.invest_before_ystart[GlossaryEnergy.InvestValue].values[::1],
                                           f'Capex_{self.name}': self.cost_details.loc[self.cost_details[GlossaryEnergy.Years] == self.year_start, f'Capex_{self.name}'].values[0]})

        production_from_invest = pd.concat(
            [self.cost_details[[GlossaryEnergy.Years, GlossaryEnergy.InvestValue, f'Capex_{self.name}']], prod_before_ystart], ignore_index=True)
        production_from_invest.sort_values(by=[GlossaryEnergy.Years], inplace=True)
        # invest from G$ to M$
        # Added a cost of 44.0$/TWh / 0.89 (efficiency) to account for the price of oil extraction
        # (until an extraction model is connected)
        production_from_invest['prod_from_invest'] = production_from_invest[GlossaryEnergy.InvestValue] / \
            (production_from_invest[f'Capex_{self.name}'] +
             self.oil_extraction_capex)
        production_from_invest[GlossaryEnergy.Years] += construction_delay
        production_from_invest = production_from_invest[production_from_invest[GlossaryEnergy.Years]
                                                        <= self.year_end]

        return production_from_invest

    def compute_dprod_dinvest(self, capex_list, invest_list, invest_before_year_start, techno_dict, dcapex_list_dinvest_list):
        '''
        Compute the partial derivative of prod vs invest  and the partial derivative of prod vs capex
        To compute after the total derivative of prod vs invest = dpprod_dpinvest + dpprod_dpcapex*dcapexdinvest
        with dcapexdinvest already computed for detailed prices
        '''
        nb_years = len(capex_list)

        if 'complex128' in [capex_list.dtype, invest_list.dtype, invest_before_year_start.dtype, dcapex_list_dinvest_list.dtype]:
            arr_type = 'complex128'
        else:
            arr_type = 'float64'
        dprod_list_dinvest_list = np.zeros(
            (nb_years, nb_years), dtype=arr_type)
        dprod_list_dcapex_list = np.zeros(
            (nb_years, nb_years), dtype=arr_type)
        # We fill this jacobian column by column because it is the same element
        # in the entire column
        for i in range(nb_years):

            dpprod_dpinvest = compute_dfunc_with_exp_min(np.array([invest_list[i]]), self.min_value_invest)[0][0] / \
                (capex_list[i] + self.oil_extraction_capex)
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
        #dprod_dinvest= dpprod_dpinvest + dprod_dcapex*dcapex_dinvest
        for line in range(nb_years):
            for column in range(nb_years):
                dprod_dinvest[line, column] = dprod_list_dinvest_list[line, column] + \
                    np.matmul(
                        dprod_list_dcapex_list[line, :], dcapex_list_dinvest_list_withexp[:, column])

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

            len_non_zeros = min(max(0, nb_years -
                                    techno_dict[GlossaryEnergy.ConstructionDelay] - i),
                                techno_dict['lifetime'])
            first_len_zeros = min(
                i + techno_dict[GlossaryEnergy.ConstructionDelay], nb_years)
            last_len_zeros = max(0, nb_years -
                                 len_non_zeros - first_len_zeros)
            # Same for capex
            dpprod_dpcapex = - \
                invest_list[i] / (capex_list[i] + self.oil_extraction_capex)**2

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
                techno_dict['lifetime'], nb_years - index)
            dprod_list_dcapex_list[:, 0] += np.hstack((np.zeros(index),
                                                       np.ones(
                len_non_zeros) * dpprod_dpcapex0,
                np.zeros(nb_years - index - len_non_zeros)))

        self.dprod_list_dcapex_list = dprod_list_dcapex_list

        return dprod_list_dcapex_list
