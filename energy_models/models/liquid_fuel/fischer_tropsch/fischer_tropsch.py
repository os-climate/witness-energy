'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/26-2023/11/03 Copyright 2023 Capgemini

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
from functools import reduce
from operator import mul

import pandas as pd
import numpy as np

from climateeconomics.glossarycore import GlossaryCore
from energy_models.core.techno_type.base_techno_models.liquid_fuel_techno import LiquidFuelTechno
from energy_models.core.stream_type.resources_models.water import Water
from climateeconomics.core.core_resources.resource_mix.resource_mix import ResourceMixModel
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.syngas import Syngas
from energy_models.core.stream_type.energy_models.syngas import compute_molar_mass as compute_syngas_molar_mass
from energy_models.core.stream_type.energy_models.syngas import compute_calorific_value as compute_syngas_calorific_value
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
from energy_models.core.stream_type.resources_models.water import Water
from energy_models.core.techno_type.base_techno_models.liquid_fuel_techno import LiquidFuelTechno
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.gaseous_hydrogen.water_gas_shift.water_gas_shift import WGS
from energy_models.models.gaseous_hydrogen.water_gas_shift.water_gas_shift_disc import WaterGasShiftDiscipline
from energy_models.models.syngas.reversed_water_gas_shift.reversed_water_gas_shift import RWGS
from energy_models.models.gaseous_hydrogen.water_gas_shift.water_gas_shift import WGS
from energy_models.models.syngas.reversed_water_gas_shift.reversed_water_gas_shift_disc import RWGSDiscipline
from energy_models.models.gaseous_hydrogen.water_gas_shift.water_gas_shift_disc import WaterGasShiftDiscipline
from climateeconomics.core.core_resources.resource_mix.resource_mix import ResourceMixModel
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
from energy_models.core.techno_type.base_techno_models.medium_heat_techno import mediumheattechno

class FischerTropsch(LiquidFuelTechno):

    def configure_parameters_update(self, inputs_dict):
        LiquidFuelTechno.configure_parameters_update(self, inputs_dict)
        self.cost_details = pd.DataFrame({GlossaryEnergy.Years: self.years})
        self.syngas_ratio = np.array(inputs_dict['syngas_ratio']) / 100.0

        self.needed_syngas_ratio = self.techno_infos_dict['carbon_number'] / (
            2 * self.techno_infos_dict['carbon_number'] + 1)


    def configure_energy_data(self, inputs_dict):
        '''
        Configure energy data by reading the data_energy_dict in the right Energy class
        Overloaded for each energy type
        '''
        self.data_energy_dict = inputs_dict['data_fuel_dict']
        self.syngas_energy_dict = inputs_dict['syngas.data_fuel_dict']
        self.gaseous_hydrogen_energy_dict = inputs_dict['hydrogen.gaseous_hydrogen.data_fuel_dict']

    def select_ratios(self):
        """! Select the ratios to be added to ratio_df
        """
        ratio_df = LiquidFuelTechno.select_ratios(self)
        if 'carbon_capture' in ratio_df.columns and self.is_stream_demand:
            ratio_df['carbon_capture'] =  ratio_df['carbon_capture'].values
        else:
            ratio_df['carbon_capture'] = np.ones(len(self.years))
        self.ratio_df = ratio_df
        return ratio_df

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs which depends on the technology 
        """

        self.cost_details['elec_needs'] = self.get_electricity_needs()
        nb_years = self.year_end - self.year_start + 1
        sg_needs_efficiency = [self.get_theoretical_syngas_needs_for_FT(
        ) / self.cost_details['efficiency']] * nb_years

        # in kwh of fuel by kwh of liquid_fuel

        # Cost of electricity for 1 kWH of liquid_fuel
        self.cost_details[Electricity.name] = list(
            self.prices[Electricity.name] * self.cost_details['elec_needs'])
        if np.all(self.needed_syngas_ratio > self.syngas_ratio):
            self.sg_transformation_name = 'RWGS'
            self.price_details_sg_techno = self.compute_rwgs_contribution(
                self.syngas_ratio)
            # For RWGS dprice is composed of dsyngas, dCO2, delec
            dprice_RWGS_dsyngas_ratio = self.syngas_ratio_techno.compute_dprice_RWGS_wo_taxes_dsyngas_ratio()
            dco2_taxes_dsyngas_ratio = self.syngas_ratio_techno.dco2_taxes_dsyngas_ratio()

            self.dprice_FT_wotaxes_dsyngas_ratio = dprice_RWGS_dsyngas_ratio * self.margin[GlossaryEnergy.MarginValue].values / 100.0 * \
                (np.ones(len(self.years)) * sg_needs_efficiency)
            self.cost_details[self.sg_transformation_name] = self.price_details_sg_techno[
                f'{self.sg_transformation_name}_wotaxes']

            self.dprice_FT_dsyngas_ratio = self.dprice_FT_wotaxes_dsyngas_ratio + \
                dco2_taxes_dsyngas_ratio * \
                (np.identity(len(self.years)) * sg_needs_efficiency) * \
                np.sign(np.maximum(
                    0.0, self.syngas_ratio_techno.carbon_emissions[self.sg_transformation_name].values))

        elif np.all(self.needed_syngas_ratio <= self.syngas_ratio):
            self.sg_transformation_name = 'WGS'
            self.price_details_sg_techno = self.compute_wgs_contribution(
                self.syngas_ratio)
            # For WGS dprice is composed of dsyngas, dwater, dCO2_taxes
            dprice_WGS_dsyngas_ratio = self.syngas_ratio_techno.compute_dprice_WGS_wo_taxes_dsyngas_ratio() * \
                self.margin[GlossaryEnergy.MarginValue].values / 100.0
            dco2_taxes_dsyngas_ratio = self.syngas_ratio_techno.dco2_taxes_dsyngas_ratio()

            self.dprice_FT_wotaxes_dsyngas_ratio = dprice_WGS_dsyngas_ratio * \
                (np.ones(len(self.years)) * sg_needs_efficiency)
            self.dprice_FT_dsyngas_ratio = self.dprice_FT_wotaxes_dsyngas_ratio + \
                dco2_taxes_dsyngas_ratio * \
                (np.identity(len(self.years)) * sg_needs_efficiency) * \
                np.sign(np.maximum(
                    0.0, self.syngas_ratio_techno.carbon_emissions[self.sg_transformation_name].values))
            self.cost_details[self.sg_transformation_name] = self.price_details_sg_techno[
                f'{self.sg_transformation_name}_wotaxes']
        else:
            self.sg_transformation_name = 'WGS or RWGS'
            sg_ratio_wgs = np.maximum(
                self.syngas_ratio, self.needed_syngas_ratio)
            price_details_sg_techno_wgs = self.compute_wgs_contribution(
                sg_ratio_wgs)
            self.syn_needs_wgs = self.syngas_ratio_techno_wgs.get_theoretical_syngas_needs(sg_ratio_wgs
                                                                                           )
            price_details_sg_techno_wgs['sg_ratio'] = self.syngas_ratio
            price_details_sg_techno_wgs[self.sg_transformation_name] = price_details_sg_techno_wgs['WGS']
            # WGS matrix
            dprice_WGS_dsyngas_ratio = self.syngas_ratio_techno_wgs.compute_dprice_WGS_wo_taxes_dsyngas_ratio() * \
                self.margin[GlossaryEnergy.MarginValue].values / 100.0
            dco2_taxes_dsyngas_ratio_wgs = self.syngas_ratio_techno_wgs.dco2_taxes_dsyngas_ratio()

            dprice_FT_wotaxes_dsyngas_ratio_wgs = dprice_WGS_dsyngas_ratio * \
                (np.ones(len(self.years)) * sg_needs_efficiency)
            dprice_FT_dsyngas_ratio_wgs = dprice_FT_wotaxes_dsyngas_ratio_wgs + \
                dco2_taxes_dsyngas_ratio_wgs * \
                (np.identity(len(self.years)) * sg_needs_efficiency) * \
                np.sign(np.maximum(
                    0.0, self.syngas_ratio_techno.carbon_emissions['WGS'].values))

            sg_ratio_rwgs = np.minimum(
                self.syngas_ratio, self.needed_syngas_ratio)
            price_details_sg_techno_rwgs = self.compute_rwgs_contribution(
                sg_ratio_rwgs)
            self.syn_needs_rwgs = self.syngas_ratio_techno.get_theoretical_syngas_needs(sg_ratio_rwgs
                                                                                        )
            price_details_sg_techno_rwgs['sg_ratio'] = self.syngas_ratio
            price_details_sg_techno_rwgs[self.sg_transformation_name] = price_details_sg_techno_rwgs['RWGS']
            # RWGS matrix

            dprice_RWGS_dsyngas_ratio = self.syngas_ratio_techno_rwgs.compute_dprice_RWGS_wo_taxes_dsyngas_ratio() * \
                self.margin[GlossaryEnergy.MarginValue].values / 100.0
            dco2_taxes_dsyngas_ratio_rwgs = self.syngas_ratio_techno_rwgs.dco2_taxes_dsyngas_ratio()
            dprice_FT_wotaxes_dsyngas_ratio_RWGS = dprice_RWGS_dsyngas_ratio * \
                (np.ones(len(self.years)) * sg_needs_efficiency)
            dprice_FT_dsyngas_ratio_RWGS = dprice_FT_wotaxes_dsyngas_ratio_RWGS + \
                dco2_taxes_dsyngas_ratio_rwgs * \
                (np.identity(len(self.years)) * sg_needs_efficiency) * \
                np.sign(
                    self.syngas_ratio_techno.carbon_emissions['RWGS'].values) * \
                np.sign(np.maximum(
                    0.0, self.syngas_ratio_techno.carbon_emissions['RWGS'].values))

            self.price_details_sg_techno = pd.concat([price_details_sg_techno_wgs.loc[
                price_details_sg_techno_wgs['sg_ratio'] >= self.needed_syngas_ratio],
                price_details_sg_techno_rwgs.loc[
                price_details_sg_techno_rwgs['sg_ratio'] < self.needed_syngas_ratio]])
            self.price_details_sg_techno.sort_index(inplace=True)
            self.cost_details[self.sg_transformation_name] = self.price_details_sg_techno[
                f'WGS_wotaxes']

            if 'complex128' in [dprice_FT_dsyngas_ratio_RWGS.dtype, dprice_FT_wotaxes_dsyngas_ratio_RWGS.dtype]:
                arr_type = 'complex128'
            else:
                arr_type = 'float64'
            self.dprice_FT_dsyngas_ratio = np.zeros(
                (len(self.years), len(self.years)), dtype=arr_type)

            self.dprice_FT_wotaxes_dsyngas_ratio = np.zeros(
                (len(self.years), len(self.years)), dtype=arr_type)

            if(self.syngas_ratio[0] < self.needed_syngas_ratio):
                techno_first_year = 'RWGS'
            else:
                techno_first_year = 'WGS'
            first_value = None
            for i in range(self.year_end - self.year_start + 1):
                if(self.syngas_ratio[i] < self.needed_syngas_ratio):

                    self.dprice_FT_dsyngas_ratio[i,
                                                 :] = dprice_FT_dsyngas_ratio_RWGS[i, :]
                    self.dprice_FT_wotaxes_dsyngas_ratio[i,
                                                         :] = dprice_FT_wotaxes_dsyngas_ratio_RWGS[i, :]
                    if self.syngas_ratio[i] == 0.:
                        self.dprice_FT_dsyngas_ratio[i,
                                                     :] = dprice_FT_wotaxes_dsyngas_ratio_RWGS[i, :]

                    if techno_first_year == 'WGS':
                        self.dprice_FT_dsyngas_ratio[i, 0] = 0.0
                        self.dprice_FT_wotaxes_dsyngas_ratio[i, 0] = 0.0

                    self.cost_details.loc[i, self.sg_transformation_name] = self.price_details_sg_techno[
                        f'RWGS_wotaxes'].values[i]

                else:

                    self.dprice_FT_dsyngas_ratio[i,
                                                 :] = dprice_FT_dsyngas_ratio_wgs[i, :]
                    self.dprice_FT_wotaxes_dsyngas_ratio[i,
                                                         :] = dprice_FT_wotaxes_dsyngas_ratio_wgs[i, :]

                    if self.syngas_ratio[i] == 0.:
                        self.dprice_FT_dsyngas_ratio[i,
                                                     :] = dprice_FT_wotaxes_dsyngas_ratio_wgs[i, :]

                    if techno_first_year == 'RWGS':
                        self.dprice_FT_dsyngas_ratio[i, 0] = 0.0
                        self.dprice_FT_wotaxes_dsyngas_ratio[i, 0] = 0.0

            # We need WGS then RWGS depending on the years

        self.cost_details['syngas_needs_for_FT'] = self.get_theoretical_syngas_needs_for_FT(
        )

        self.cost_details[Syngas.name] = self.cost_details[self.sg_transformation_name] * \
            self.cost_details['syngas_needs_for_FT'] / \
            self.cost_details['efficiency']

        self.cost_details['syngas before transformation'] = self.prices[Syngas.name] * \
            self.cost_details['syngas_needs_for_FT'] / \
            self.cost_details['efficiency']

        return self.cost_details[Electricity.name] + self.cost_details[Syngas.name]

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices 
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        #elec_needs = self.get_electricity_needs()
        elec_needs = self.price_details_sg_techno['elec_needs'] * \
            self.cost_details['syngas_needs_for_FT'] / \
            self.techno_infos_dict['efficiency']

        if self.sg_transformation_name in ['WGS', 'RWGS']:

            syn_needs = self.syngas_ratio_techno.get_theoretical_syngas_needs(self.syngas_ratio_techno.syngas_ratio
                                                                              )

            return {Electricity.name: np.identity(len(self.years)) * elec_needs.to_numpy(),
                    Syngas.name: np.identity(len(self.years)) * (self.cost_details['syngas_needs_for_FT'].values * syn_needs /
                                                                 self.price_details_sg_techno['efficiency'].values) /
                    self.cost_details['efficiency'].values}

        else:

            if 'complex128' in [self.price_details_rwgs['elec_needs'].values.dtype, self.cost_details['syngas_needs_for_FT'].values.dtype]:
                arr_type = 'complex128'
            else:
                arr_type = 'float64'

            dsyngas_dprice = np.zeros(len(self.years), dtype=arr_type)
            delec_dprice = np.zeros(
                (len(self.years), len(self.years)), dtype=arr_type)
            for i in range(self.year_end - self.year_start + 1):
                if(self.syngas_ratio[i] < self.needed_syngas_ratio):
                    # RWGS

                    dsyngas_dprice[i] = (self.cost_details['syngas_needs_for_FT'][i] * self.syn_needs_rwgs[i] /
                                         self.price_details_rwgs['efficiency'][i])
                    elec_needs = self.price_details_rwgs['elec_needs'] * \
                        self.cost_details['syngas_needs_for_FT'] / \
                        self.techno_infos_dict['efficiency']
                    delec_dprice[i, :] = (np.identity(
                        len(self.years)) * elec_needs.values[:, np.newaxis])[i, :]
                else:
                    dsyngas_dprice[i] = (self.cost_details['syngas_needs_for_FT'][i] * self.syn_needs_wgs[i] /
                                         self.price_details_wgs['efficiency'][i])
                    elec_needs = self.price_details_wgs['elec_needs'] * \
                        self.cost_details['syngas_needs_for_FT'] / \
                        self.techno_infos_dict['efficiency']
                    delec_dprice[i, :] = (np.identity(
                        len(self.years)) * elec_needs.values[:, np.newaxis])[i, :]
            return {Electricity.name: delec_dprice,
                    Syngas.name: np.identity(len(self.years)) * dsyngas_dprice /
                    self.cost_details['efficiency'].values
                    }

    def grad_price_vs_resources_price(self):
        '''
        Compute the gradient of global price vs resources prices
        Work also for total CO2_emissions vs resources CO2 emissions
        '''
        water_needs = np.zeros(len(self.years))
        co2_needs = np.zeros(len(self.years))

        if self.sg_transformation_name in ['WGS', 'WGS or RWGS']:

            water_needs += (self.price_details_sg_techno['water_needs'].fillna(0.0) /
                           self.price_details_sg_techno['efficiency'] *
                           self.cost_details['syngas_needs_for_FT'] /
                           self.cost_details['efficiency']).values

        if self.sg_transformation_name in ['RWGS', 'WGS or RWGS']:

            co2_needs += (self.price_details_sg_techno['CO2_needs'].fillna(0.0) /
                         self.price_details_sg_techno['efficiency'] *
                         self.cost_details['syngas_needs_for_FT'] /
                         self.cost_details['efficiency']).values

        return {Water.name: np.identity(len(self.years)) * water_needs,
                CO2.name: np.identity(len(self.years)) * co2_needs,
                }

    def grad_co2_emission_vs_resources_co2_emissions(self):
        '''
        Compute the gradient of global price vs resources prices
        Work also for total CO2_emissions vs resources CO2 emissions
        '''

        water_needs = np.zeros(len(self.years))
        co2_needs = np.zeros(len(self.years))

        if self.sg_transformation_name in ['WGS', 'WGS or RWGS']:

            water_needs += (self.price_details_sg_techno['water_needs'].fillna(0.0) /
                           self.price_details_sg_techno['efficiency'] *
                           self.cost_details['syngas_needs_for_FT'] /
                           self.cost_details['efficiency']).values

            co2_needs += (-self.CO2_prod_wgs *
                         self.cost_details['syngas_needs_for_FT'] /
                         self.cost_details['efficiency']).values

        if self.sg_transformation_name in ['RWGS', 'WGS or RWGS']:

            co2_needs += (self.price_details_sg_techno['CO2_needs'].fillna(0.0) /
                         self.price_details_sg_techno['efficiency'] *
                         self.cost_details['syngas_needs_for_FT'] /
                         self.cost_details['efficiency']).values

        return {Water.name: np.identity(len(self.years)) * water_needs,
                CO2.name: np.identity(len(self.years)) * co2_needs,
                }

    def compute_rwgs_contribution(self, sg_ratio):
        years = np.arange(self.year_start, self.year_end + 1)
        utlisation_ratio = pd.DataFrame({GlossaryEnergy.Years: years,
                                        GlossaryEnergy.UtilisationRatioValue: self.utilisation_ratio})
        inputs_dict = {GlossaryEnergy.YearStart: self.year_start,
                       GlossaryEnergy.YearEnd: self.year_end,
                       GlossaryEnergy.UtilisationRatioValue: utlisation_ratio,
                       'techno_infos_dict': RWGSDiscipline.techno_infos_dict_default,
                       GlossaryEnergy.EnergyPricesValue: self.prices,
                       GlossaryEnergy.EnergyCO2EmissionsValue: self.energy_CO2_emissions,
                       # We suppose invest are not influencing the price of WGS or RWGS because the gradient is a mess to compute
                       # AND Is it obvious the fact that investing in Fischer
                       # Tropsch will decrease the price of WGS ?
                       GlossaryEnergy.InvestLevelValue: pd.DataFrame({GlossaryEnergy.Years: years, GlossaryEnergy.InvestValue: 1.0}),
                       GlossaryEnergy.InvestmentBeforeYearStartValue: RWGSDiscipline.invest_before_year_start,
                       GlossaryEnergy.CO2TaxesValue: self.CO2_taxes,
                       GlossaryEnergy.MarginValue: pd.DataFrame({GlossaryEnergy.Years: years, GlossaryEnergy.MarginValue: 100.0}),
                       GlossaryEnergy.TransportCostValue: pd.DataFrame({GlossaryEnergy.Years: years, 'transport': 0.0}),
                       GlossaryEnergy.TransportMarginValue: pd.DataFrame({GlossaryEnergy.Years: years, GlossaryEnergy.MarginValue: 100.0}),
                       'initial_production': RWGSDiscipline.initial_production,
                       'initial_age_distrib': RWGSDiscipline.initial_age_distribution,
                       GlossaryEnergy.RessourcesCO2EmissionsValue: self.resources_CO2_emissions,
                       GlossaryEnergy.ResourcesPriceValue: self.resources_prices,
                       'syngas_ratio': sg_ratio * 100.0,
                       'needed_syngas_ratio': self.needed_syngas_ratio * 100.0,
                       'scaling_factor_invest_level': self.scaling_factor_invest_level,
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production,
                       'smooth_type': self.smooth_type,
                       'is_stream_demand': self.is_stream_demand,
                       'is_apply_resource_ratio': self.is_apply_resource_ratio,
                       'data_fuel_dict': self.syngas_energy_dict
                       }
        if self.is_stream_demand:
            inputs_dict[GlossaryEnergy.AllStreamsDemandRatioValue] = self.all_streams_demand_ratio
        if self.is_apply_resource_ratio:
            inputs_dict[ResourceMixModel.RATIO_USABLE_DEMAND] = self.ratio_available_resource

        self.syngas_ratio_techno = RWGS('RWGS')
        self.syngas_ratio_techno.syngas_COH2_ratio = sg_ratio * 100.0
        self.syngas_ratio_techno.configure_parameters(inputs_dict)
        self.syngas_ratio_techno.configure_parameters_update(inputs_dict)
        price_details = self.syngas_ratio_techno.compute_price()
        self.syngas_ratio_techno_rwgs = self.syngas_ratio_techno
        self.price_details_rwgs = price_details
        self.water_prod_RWGS = self.syngas_ratio_techno.get_theoretical_water_prod()
        return price_details

    def compute_wgs_contribution(self, sg_ratio):
        years = np.arange(self.year_start, self.year_end + 1)
        utlisation_ratio = pd.DataFrame({
            GlossaryEnergy.Years: years,
            GlossaryEnergy.UtilisationRatioValue: self.utilisation_ratio
        })
        inputs_dict = {GlossaryEnergy.YearStart: self.year_start,
                       GlossaryEnergy.YearEnd: self.year_end,
                       GlossaryEnergy.UtilisationRatioValue: utlisation_ratio,
                       'techno_infos_dict': WaterGasShiftDiscipline.techno_infos_dict_default,
                       GlossaryEnergy.EnergyPricesValue: self.prices,
                       GlossaryEnergy.EnergyCO2EmissionsValue: self.energy_CO2_emissions,
                       # We suppose invest are not influencing the price of WGS or RWGS because the gradient is a mess to compute
                       # AND Is it obvious the fact that investing in Fischer
                       # Tropsch will decrease the price of WGS ? Not sure so
                       # the hypothesis looks fine
                       GlossaryEnergy.InvestLevelValue: pd.DataFrame({GlossaryEnergy.Years: years, GlossaryEnergy.InvestValue: 1.0}),
                       GlossaryEnergy.InvestmentBeforeYearStartValue: WaterGasShiftDiscipline.invest_before_year_start,
                       GlossaryEnergy.CO2TaxesValue: self.CO2_taxes,
                       GlossaryEnergy.MarginValue:  pd.DataFrame({GlossaryEnergy.Years: years, GlossaryEnergy.MarginValue: 100.0}),
                       GlossaryEnergy.TransportCostValue: pd.DataFrame({GlossaryEnergy.Years: years, 'transport': 0.0}),
                       GlossaryEnergy.TransportMarginValue: pd.DataFrame({GlossaryEnergy.Years: years, GlossaryEnergy.MarginValue: 100.0}),
                       'initial_production': WaterGasShiftDiscipline.initial_production,
                       'initial_age_distrib': WaterGasShiftDiscipline.initial_age_distribution,
                       GlossaryEnergy.RessourcesCO2EmissionsValue: self.resources_CO2_emissions,
                       GlossaryEnergy.ResourcesPriceValue: self.resources_prices,
                       'syngas_ratio': sg_ratio * 100.0,
                       'needed_syngas_ratio': self.needed_syngas_ratio * 100.0,
                       'scaling_factor_invest_level': self.scaling_factor_invest_level,
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production,
                       'smooth_type': self.smooth_type,
                       'is_stream_demand': self.is_stream_demand,
                       'is_apply_resource_ratio': self.is_apply_resource_ratio,
                       'data_fuel_dict': self.gaseous_hydrogen_energy_dict
                       }
        if self.is_stream_demand:
            inputs_dict[GlossaryEnergy.AllStreamsDemandRatioValue] = self.all_streams_demand_ratio
        if self.is_apply_resource_ratio:
            inputs_dict[ResourceMixModel.RATIO_USABLE_DEMAND] = self.ratio_available_resource

        self.syngas_ratio_techno = WGS('WGS')
        self.syngas_ratio_techno.syngas_COH2_ratio = sg_ratio * 100.0
        self.syngas_ratio_techno.configure_parameters(inputs_dict)
        self.syngas_ratio_techno.configure_parameters_update(inputs_dict)
        price_details = self.syngas_ratio_techno.compute_price()
        self.syngas_ratio_techno_wgs = self.syngas_ratio_techno
        self.price_details_wgs = price_details
        self.CO2_prod_wgs = self.syngas_ratio_techno.get_theoretical_co2_prod()

        return price_details

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """

        self.compute_primary_energy_production()

        # Compute elec demand from WGS
        elec_needs_wgs = self.price_details_sg_techno['elec_needs'] * \
            self.cost_details['syngas_needs_for_FT'] / \
            self.cost_details['efficiency']

        # Consumption of WGS and FT
        self.consumption[f'{Electricity.name} ({self.product_energy_unit})'] = (self.cost_details['elec_needs'] + elec_needs_wgs) * \
            self.production[f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})']  # in kWH

        # needs of syngas in kWh syngasin/kWhsyngas_out
        syngas_needs_wgs = self.price_details_sg_techno['syngas_needs'] / \
            self.price_details_sg_techno['efficiency']

        # in kWhsyngas_in/kwhliquid_fuel and syngas_needs_for_FT is in
        # kWhsyngas_out/kWhliquid_fuel
        syngas_needs = syngas_needs_wgs * \
            self.cost_details['syngas_needs_for_FT'] / \
            self.cost_details['efficiency']

        # Compute of initial syngas vs output liquid_fuel
        self.consumption[f'{Syngas.name} ({self.product_energy_unit})'] = syngas_needs * \
            self.production[f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})']  # in kWH

        # If WGS in the loop then we need water in the process
        if self.sg_transformation_name in ['WGS', 'WGS or RWGS']:
            water_needs = self.price_details_sg_techno['water_needs'].fillna(0.0) / \
                self.price_details_sg_techno['efficiency'] * \
                self.cost_details['syngas_needs_for_FT'] / \
                self.cost_details['efficiency']

            self.consumption[f'{Water.name} ({self.mass_unit})'] = water_needs * \
                self.production[f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})']

            co2_prod = self.CO2_prod_wgs * \
                self.cost_details['syngas_needs_for_FT'] / \
                self.cost_details['efficiency']

            self.production[f'{CarbonCapture.flue_gas_name} ({self.mass_unit})'] = co2_prod * \
                self.production[f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})']
            water_prod = 0.0
        elif self.sg_transformation_name == 'RWGS':
            self.consumption[f'{Water.name} ({self.mass_unit})'] = 0.0
            self.production[f'{CarbonCapture.flue_gas_name} ({self.mass_unit})'] = 0.0

        if self.sg_transformation_name == 'WGS':
            self.consumption[f'{CarbonCapture.name} ({self.mass_unit})'] = 0.0

        elif self.sg_transformation_name in ['RWGS', 'WGS or RWGS']:

            water_prod = self.water_prod_RWGS * \
                self.cost_details['syngas_needs_for_FT'] / \
                self.cost_details['efficiency']

            co2_needs = self.price_details_sg_techno['CO2_needs'].fillna(0.0) / \
                self.price_details_sg_techno['efficiency'] * \
                self.cost_details['syngas_needs_for_FT'] / \
                self.cost_details['efficiency']

            self.consumption[f'{CarbonCapture.name} ({self.mass_unit})'] = co2_needs * \
                self.production[f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})']

        water_prod += self.get_theoretical_water_prod_from_FT() / \
            self.cost_details['efficiency']

        self.production[f'{Water.name} ({self.mass_unit})'] = water_prod * \
            self.production[f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})']

        self.production[f'{mediumheattechno.energy_name} ({self.product_energy_unit})'] = \
            self.techno_infos_dict['medium_heat_production'] * self.techno_infos_dict['useful_heat_recovery_factor'] * \
            self.production[f'{CarbonCapture.flue_gas_name} ({self.mass_unit})'] * 1000000000

        self.consumption = self.consumption.fillna(0.0)
        self.production = self.production.fillna(0.0)

    def compute_delec_consumption_dsyngas_ratio(self, dprod_energy_dsyngas_ratio):
        elec_needs_wgs = self.price_details_sg_techno['elec_needs'] * \
            self.cost_details['syngas_needs_for_FT'] / \
            self.cost_details['efficiency']

        elec_needs = (self.cost_details['elec_needs'] + elec_needs_wgs)

        delec_consumption = dprod_energy_dsyngas_ratio * elec_needs.to_numpy()

        return delec_consumption

    def compute_CO2_emissions_from_input_resources(self):
        ''' 
        Need to take into account negative CO2 from biomass_dry and CO2 from electricity (can be 0.0 or positive)
        '''

        # Compute elec demand from WGS
        elec_needs_wgs = self.price_details_sg_techno['elec_needs'] * \
            self.cost_details['syngas_needs_for_FT'] / \
            self.cost_details['efficiency']

        self.carbon_emissions[f'{Electricity.name}'] = self.energy_CO2_emissions[f'{Electricity.name}'] * \
            (self.cost_details['elec_needs'] + elec_needs_wgs)

        # needs of syngas in kWh syngasin/kWhsyngas_out
        syngas_needs_wgs = self.price_details_sg_techno['syngas_needs'] / \
            self.price_details_sg_techno['efficiency']

        # in kWhsyngas_in/kwhliquid_fuel and syngas_needs_for_FT is in
        # kWhsyngas_out/kWhliquid_fuel
        syngas_needs = syngas_needs_wgs * \
            self.cost_details['syngas_needs_for_FT'] / \
            self.cost_details['efficiency']

        self.carbon_emissions[Syngas.name] = self.energy_CO2_emissions[
            f'{Syngas.name}'] * syngas_needs

        co2_needs = 0.0
        water_needs = 0.0
        if self.sg_transformation_name in ['WGS', 'WGS or RWGS']:

            water_needs += self.price_details_sg_techno['water_needs'].fillna(0.0) / \
                           self.price_details_sg_techno['efficiency'] * \
                           self.cost_details['syngas_needs_for_FT'] / \
                           self.cost_details['efficiency']

            co2_needs += -self.CO2_prod_wgs * \
                         self.cost_details['syngas_needs_for_FT'] / \
                         self.cost_details['efficiency']

        if self.sg_transformation_name in ['RWGS', 'WGS or RWGS']:

            co2_needs += self.price_details_sg_techno['CO2_needs'].fillna(0.0) / \
                self.price_details_sg_techno['efficiency'] * \
                self.cost_details['syngas_needs_for_FT'] / \
                self.cost_details['efficiency']

        self.carbon_emissions[CO2.name] = self.resources_CO2_emissions[
            ResourceGlossary.CO2['name']] * co2_needs

        self.carbon_emissions[Water.name] = self.resources_CO2_emissions[
            ResourceGlossary.Water['name']] * water_needs

        return self.carbon_emissions[f'{Electricity.name}'] + self.carbon_emissions[Syngas.name] + \
               self.carbon_emissions[CO2.name] + self.carbon_emissions[Water.name]

    def compute_dco2_emissions_dsyngas_ratio(self):

        if self.sg_transformation_name in ['WGS']:

            #             mol_H2 = (1.0 + self.syngas_ratio) / \
            #                 (1.0 + self.needed_syngas_ratio)
            #             mol_CO2 = self.syngas_ratio - self.needed_syngas_ratio * mol_H2
            #             co2_molar_mass = CO2.data_energy_dict['molar_mass']
            #
            #             needed_syngas_molar_mass = compute_syngas_molar_mass(
            #                 self.needed_syngas_ratio)
            #             needed_calorific_value = compute_syngas_calorific_value(
            #                 self.needed_syngas_ratio)
            #
            #             #mol_H2up = (1.0 + self.syngas_ratio)
            #             dmol_H2up = 1.0
            #             mol_H2down = (1.0 + self.needed_syngas_ratio)
            #             #dmol_H2down = 0.0
            #
            #             dmol_H2_dsyngas_ratio = (dmol_H2up * mol_H2down) / mol_H2down ** 2
            #             dmol_CO2_dsyngas_ratio = 1 - \
            #                 self.needed_syngas_ratio * dmol_H2_dsyngas_ratio

            #             dco2_dsyngas_ratio = self.syngas_ratio_techno.compute_dco2_prod_dsyngas_ratio(mol_CO2, mol_H2, co2_molar_mass, needed_syngas_molar_mass,
            # needed_calorific_value, dmol_CO2_dsyngas_ratio,
            # dmol_H2_dsyngas_ratio)

            dsyngasco2_dsyngasratio = self.syngas_ratio_techno.dtotal_co2_emissions_dsyngas_ratio()

            dsyngas_co2_emissions_dsyngas_ratio_wgs = np.identity(len(
                self.years)) * (dsyngasco2_dsyngasratio * self.cost_details['syngas_needs_for_FT'].values / self.cost_details['efficiency'].values)

            return dsyngas_co2_emissions_dsyngas_ratio_wgs
#             return {CO2.name: dco2_emissions_dsyngas_ratio_wgs,
#                     self.name: dsyngas_co2_emissions_dsyngas_ratio_wgs,
#                     'production': np.zeros(len(self.years),),
#                     'electricity': np.zeros(len(self.years),),
#                     'syngas': dsyngas_co2_emissions_dsyngas_ratio_wgs - dco2_emissions_dsyngas_ratio_wgs
#                     }

        elif self.sg_transformation_name in ['RWGS']:

            dsyngasco2_dsyngasratio = self.syngas_ratio_techno.dtotal_co2_emissions_dsyngas_ratio()

            dsyngas_co2_emissions_dsyngas_ratio_rwgs = np.identity(len(
                self.years)) * (dsyngasco2_dsyngasratio * self.cost_details['syngas_needs_for_FT'].values / self.cost_details['efficiency'].values)

            return dsyngas_co2_emissions_dsyngas_ratio_rwgs
#             return {CO2.name: dco2_emission_dsyngas_ratio_rwgs,
#                     self.name: dsyngas_co2_emissions_dsyngas_ratio_rwgs,
#                     'production': np.zeros(len(self.years),),
#                     'electricity': delectricity_emission_dsyngas_ratio_rwgs,
#                     'syngas': dsyngas_co2_emissions_dsyngas_ratio_rwgs - dco2_emission_dsyngas_ratio_rwgs - delectricity_emission_dsyngas_ratio_rwgs}

        else:

            # WGS
            dsyngasco2_dsyngasratio_wgs = self.syngas_ratio_techno_wgs.dtotal_co2_emissions_dsyngas_ratio()

            dsyngas_co2_emissions_dsyngas_ratio_wgs = np.identity(len(
                self.years)) * (dsyngasco2_dsyngasratio_wgs * self.cost_details['syngas_needs_for_FT'].values / self.cost_details['efficiency'].values)

            dsyngasco2_dsyngasratio_rwgs = self.syngas_ratio_techno_rwgs.dtotal_co2_emissions_dsyngas_ratio()

            dsyngas_co2_emissions_dsyngas_ratio_rwgs = np.identity(len(
                self.years)) * (dsyngasco2_dsyngasratio_rwgs * self.cost_details['syngas_needs_for_FT'].values / self.cost_details['efficiency'].values)

#             dco2_emission_dsyngas_ratio = np.zeros(
#                 (len(self.years), len(self.years)))
#             dsyngas_emission_dsyngas_ratio = np.zeros(
#                 (len(self.years), len(self.years)))
#             delec_emission_dsyngas_ratio = np.zeros(
#                 (len(self.years), len(self.years)))
            if 'complex128' in [dsyngas_co2_emissions_dsyngas_ratio_rwgs.dtype, dsyngas_co2_emissions_dsyngas_ratio_wgs.dtype]:
                arr_type = 'complex128'
            else:
                arr_type = 'float64'

            dtotal_emission_dsyngas_ratio = np.zeros(
                (len(self.years), len(self.years)), dtype=arr_type)
            for i in range(self.year_end - self.year_start + 1):
                if(self.syngas_ratio[i] < self.needed_syngas_ratio):
                    # RWGS
                    #                     dco2_emission_dsyngas_ratio[i,
                    #                                                 :] = dco2_emission_dsyngas_ratio_rwgs[i, :]
                    #                     dsyngas_emission_dsyngas_ratio[i,
                    #                                                    :] = dsyngas_co2_emissions_dsyngas_ratio_rwgs[i, :] - dco2_emission_dsyngas_ratio_rwgs[i, :] - delectricity_emission_dsyngas_ratio_rwgs[i, :]
                    #                     delec_emission_dsyngas_ratio[i,
                    #                                                  :] = delectricity_emission_dsyngas_ratio_rwgs[i, :]
                    dtotal_emission_dsyngas_ratio[i,
                                                  :] = dsyngas_co2_emissions_dsyngas_ratio_rwgs[i, :]
                else:
                    #                     dco2_emission_dsyngas_ratio[i,
                    #                                                 :] = dco2_emissions_dsyngas_ratio_wgs[i, :]
                    #                     dsyngas_emission_dsyngas_ratio[i,
                    #                                                    :] = dsyngas_co2_emissions_dsyngas_ratio_wgs[i, :] - dco2_emissions_dsyngas_ratio_wgs[i, :]
                    #                     delec_emission_dsyngas_ratio[i, :] = np.zeros(
                    #                         len(self.years),)
                    dtotal_emission_dsyngas_ratio[i,
                                                  :] = dsyngas_co2_emissions_dsyngas_ratio_wgs[i, :]
            return dtotal_emission_dsyngas_ratio
#             return {CO2.name: dco2_emission_dsyngas_ratio,
#                     self.name: dtotal_emission_dsyngas_ratio,
#                     'electricity': delec_emission_dsyngas_ratio,
#                     'syngas': dsyngas_emission_dsyngas_ratio}

    def get_theoretical_syngas_needs_for_FT(self):
        ''' 
        Get syngas needs in kWh syngas /kWh liquid_fuel
        H2 + n/(2n+1)CO --> 1/(2n+1) CnH_2n+1 + n/(2n+1)H20
        Warning : molar mass is in g/mol but we divide and multiply by one
        '''

        mol_syngas = 1.0
        mol_liquid_fuel = 1.0 / \
            (2 * self.techno_infos_dict['carbon_number'] + 1)
        syngas_molar_mass = compute_syngas_molar_mass(self.needed_syngas_ratio)

        syngas_calorific_value = compute_syngas_calorific_value(
            self.needed_syngas_ratio)
        syngas_needs_for_FT = mol_syngas * syngas_molar_mass * syngas_calorific_value / \
            (mol_liquid_fuel * self.data_energy_dict['molar_mass'] *
             self.data_energy_dict['calorific_value'])

        return syngas_needs_for_FT

    def get_theoretical_water_prod_from_FT(self):
        ''' 
        Get water prod in kg H20 /kWh liquid_fuel
        H2 + n/(2n+1)CO --> 1/(2n+1) CnH_2n+1 + n/(2n+1)H20
        Warning : molar mass is in g/mol but we divide and multiply by one
        '''

        mol_H20 = self.techno_infos_dict['carbon_number']
        mol_liquid_fuel = 1.0
        water_data = Water.data_energy_dict
        water_prod = mol_H20 * water_data['molar_mass'] / \
            (mol_liquid_fuel * self.data_energy_dict['molar_mass'] *
             self.data_energy_dict['calorific_value'])

        return water_prod

    def compute_dcapex_dsyngas_ratio(self):

        invest_sum = 0.0
        dinvest_sum = 0.0
        q = 0.0
        dq = 0.0
        capex_year = 0.0
        capex_init = self.check_capex_unity(
            self.techno_infos_dict)

        expo_factor = self.compute_expo_factor(
            self.techno_infos_dict)

        if 'complex128' in [type(self.initial_production), type(capex_init), self.cost_details[GlossaryEnergy.InvestValue].values.dtype]:
            arr_type = 'complex128'
        else:
            arr_type = 'float64'

        capex_grad = np.zeros(
            (len(self.years), len(self.years)), dtype=arr_type)

        dqlist = []
        qlist = []
        self.slope_capex = 0.0

        if 'maximum_learning_capex_ratio' in self.techno_infos_dict:
            maximum_learning_capex_ratio = self.techno_infos_dict['maximum_learning_capex_ratio']
        else:
            maximum_learning_capex_ratio = 0.9

        invest_list = self.cost_details[GlossaryEnergy.InvestValue].values

        if min(invest_list.real) < 0:
            print(
                f'invest is negative {min(invest_list.real)} on techno {self.name}')
            invest_list = np.maximum(0.0, invest_list)

        for i, invest in enumerate(invest_list):

            if i == 0.0:
                capex_year = capex_init
                capex_grad[0][0] = 1000 * self.slope_capex
                invest_sum = self.initial_production * capex_init
            else:
                dinvest_sum = self.initial_production * self.slope_capex
                q = ((invest_sum + invest) / invest_sum) ** (-expo_factor)
                qlist.append(q)
                dq = -expo_factor * ((invest_sum + invest) / invest_sum) ** (-expo_factor -
                                                                             1.0) * (-dinvest_sum * invest / (invest_sum * invest_sum))
                dqlist.append(dq)

                q_product = reduce(mul, qlist)

                qlistmod = []
                for k in range(0, i):
                    qlistmod.extend([qlist[:k] + qlist[k + 1:]])

                if qlistmod == [[]]:
                    productlist = [0]
                else:
                    productlist = [reduce(mul, ql) for ql in qlistmod]
                prod_mul = sum([a * b for a, b in zip(productlist, dqlist)])
                capex_year = capex_year * q
                capex_grad[i][0] = capex_grad[0][0] * \
                    q_product + capex_init * prod_mul
            invest_sum += invest

        #dcapex = maximum_learning_capex_ratio*dcapex_init + (1.0 - maximum_learning_capex_ratio)*dcapex
        capex_grad = maximum_learning_capex_ratio * capex_grad[0][0] * np.insert(np.zeros((len(self.years), len(self.years) - 1)), 0, np.ones(len(self.years)), axis=1) + \
            (1.0 - maximum_learning_capex_ratio) * capex_grad
        return capex_grad

    def compute_dprod_dfluegas(self,  capex_list, invest_list, invest_before_year_start, techno_dict, dcapexdfluegas):

        #dpprod_dpfluegas = np.zeros(dcapexdfluegas.shape())

        dprod_dcapex = self.compute_dprod_dcapex(
            capex_list, invest_list, techno_dict, invest_before_year_start)

        if 'complex128' in [dprod_dcapex.dtype]:
            arr_type = 'complex128'
        else:
            arr_type = 'float64'

        #dprod_dfluegas = dpprod_dpfluegas + dprod_dcapex * dcapexdfluegas
        dprod_dfluegas = np.zeros(dprod_dcapex.shape, dtype=arr_type)
        for line in range(dprod_dcapex.shape[0]):
            for column in range(dprod_dcapex.shape[1]):
                dprod_dfluegas[line, column] = np.matmul(
                    dprod_dcapex[line, :], dcapexdfluegas[:, column])

        return dprod_dfluegas

    def grad_techno_producion_vs_syngas_ratio(self, capex, invest, invest_before_ystart, techno_infos_dict):
        '''
        Compute the gradient of techno production vs syngas ratio
        '''
        if np.all(self.needed_syngas_ratio <= self.syngas_ratio):

            if f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})' not in self.production:
                self.compute_price()
                self.compute_primary_energy_production()

            mol_H2 = (1.0 + self.syngas_ratio) / \
                (1.0 + self.needed_syngas_ratio)
            mol_CO2 = self.syngas_ratio - self.needed_syngas_ratio * mol_H2
            co2_molar_mass = CO2.data_energy_dict['molar_mass']

            needed_syngas_molar_mass = compute_syngas_molar_mass(
                self.needed_syngas_ratio)
            needed_calorific_value = compute_syngas_calorific_value(
                self.needed_syngas_ratio)

            mol_H2up = (1.0 + self.syngas_ratio)
            dmol_H2up = 1.0
            mol_H2down = (1.0 + self.needed_syngas_ratio)
            dmol_H2down = 0.0

            dmol_H2_dsyngas_ratio = (dmol_H2up * mol_H2down) / mol_H2down ** 2
            dmol_CO2_dsyngas_ratio = 1 - \
                self.needed_syngas_ratio * dmol_H2_dsyngas_ratio

            dco2_dsyngas_ratio = self.syngas_ratio_techno.compute_dco2_prod_dsyngas_ratio(mol_CO2, mol_H2, co2_molar_mass, needed_syngas_molar_mass,
                                                                                          needed_calorific_value, dmol_CO2_dsyngas_ratio, dmol_H2_dsyngas_ratio)

            capex_grad = self.compute_dcapex_dsyngas_ratio()
            dprodenergy_dsyngas_ratio = self.compute_dprod_dfluegas(
                capex, invest, invest_before_ystart, techno_infos_dict, capex_grad)

            return {f'{CarbonCapture.flue_gas_name} ({self.mass_unit})': np.identity(len(self.years)) * (
                self.production[f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})'].values *
                dco2_dsyngas_ratio / 100.0 * self.cost_details['syngas_needs_for_FT'].values / self.cost_details['efficiency'].values),
                f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})': dprodenergy_dsyngas_ratio / 100.0}  # now syngas is in % grad is divided by 100

        elif np.all(self.needed_syngas_ratio > self.syngas_ratio):

            dwater_prod_dsyngas_ratio = self.syngas_ratio_techno.compute_dwater_prod_dsynags_ratio()
            if f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})' not in self.production:
                self.compute_price()
                self.compute_primary_energy_production()

            capex_grad = self.compute_dcapex_dsyngas_ratio()
            dprodenergy_dsyngas_ratio = self.compute_dprod_dfluegas(
                capex, invest, invest_before_ystart, techno_infos_dict, capex_grad)

            return {f'{Water.name} ({self.mass_unit})': np.identity(len(self.years)) * (self.production[f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})'].values * dwater_prod_dsyngas_ratio / 100.0 * self.cost_details['syngas_needs_for_FT'].values / self.cost_details['efficiency'].values),
                    f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})': dprodenergy_dsyngas_ratio / 100.0}  # now syngas is in % grad is divided by 100

        else:

            if f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})' not in self.production:
                self.compute_price()
                self.compute_primary_energy_production()

            mol_H2 = (1.0 + self.syngas_ratio) / \
                (1.0 + self.needed_syngas_ratio)
            mol_CO2 = self.syngas_ratio - self.needed_syngas_ratio * mol_H2
            co2_molar_mass = CO2.data_energy_dict['molar_mass']

            needed_syngas_molar_mass = compute_syngas_molar_mass(
                self.needed_syngas_ratio)
            needed_calorific_value = compute_syngas_calorific_value(
                self.needed_syngas_ratio)

            mol_H2up = (1.0 + self.syngas_ratio)
            dmol_H2up = 1.0
            mol_H2down = (1.0 + self.needed_syngas_ratio)
            dmol_H2down = 0.0

            dmol_H2_dsyngas_ratio = (dmol_H2up * mol_H2down) / mol_H2down ** 2
            dmol_CO2_dsyngas_ratio = 1 - \
                self.needed_syngas_ratio * dmol_H2_dsyngas_ratio

            dco2_dsyngas_ratio = self.syngas_ratio_techno_wgs.compute_dco2_prod_dsyngas_ratio(mol_CO2, mol_H2, co2_molar_mass, needed_syngas_molar_mass,
                                                                                              needed_calorific_value, dmol_CO2_dsyngas_ratio, dmol_H2_dsyngas_ratio)

            capex_grad = self.compute_dcapex_dsyngas_ratio()
            dprodenergy_dsyngas_ratio = self.compute_dprod_dfluegas(
                capex, invest, invest_before_ystart, techno_infos_dict, capex_grad)

            dco2_flue_gas_prod_dsyngas_ratio = np.identity(len(self.years)) * (
                self.production[f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})'].values * dco2_dsyngas_ratio * self.cost_details['syngas_needs_for_FT'].values / self.cost_details['efficiency'].values)

            # RWGS

            dwater_prod_dsyngas_ratio = self.syngas_ratio_techno_rwgs.compute_dwater_prod_dsynags_ratio()
            if f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})' not in self.production:
                self.compute_price()
                self.compute_primary_energy_production()

            capex_grad = self.compute_dcapex_dsyngas_ratio()
            dprodenergy_dsyngas_ratio_rwgs = self.compute_dprod_dfluegas(
                capex, invest, invest_before_ystart, techno_infos_dict, capex_grad)

            dwater_dsyngas_ratio = np.identity(len(self.years)) * (self.production[f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})'].values
                                                                   * dwater_prod_dsyngas_ratio * self.cost_details['syngas_needs_for_FT'].values / self.cost_details['efficiency'].values)

            if 'complex128' in [dwater_dsyngas_ratio.dtype, dprodenergy_dsyngas_ratio.dtype]:
                arr_type = 'complex128'
            else:
                arr_type = 'float64'

            dfluegas_dsyngas_ratio = np.zeros(
                (len(self.years), len(self.years)), dtype=arr_type)
            dwaterprod_dsyngas_ratio = np.zeros((
                len(self.years), len(self.years)), dtype=arr_type)
            dliquid_fuelprod_dsyngas_ratio = np.zeros(
                (len(self.years), len(self.years)), dtype=arr_type)

            for i in range(self.year_end - self.year_start + 1):
                if(self.syngas_ratio[i] < self.needed_syngas_ratio):
                    # RWGS
                    dwaterprod_dsyngas_ratio[i, :] = dwater_dsyngas_ratio[i, :]
                    dliquid_fuelprod_dsyngas_ratio[:,
                                                   i] = dprodenergy_dsyngas_ratio_rwgs[i, :]

                else:
                    dfluegas_dsyngas_ratio[:,
                                           i] = dco2_flue_gas_prod_dsyngas_ratio[i, :]
                    dliquid_fuelprod_dsyngas_ratio[:,
                                                   i] = dprodenergy_dsyngas_ratio[i, :]

            return {
                # now syngas is in % grad is divided by 100
                f'{Water.name} ({self.mass_unit})': dwaterprod_dsyngas_ratio / 100.0,
                f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})': dliquid_fuelprod_dsyngas_ratio / 100.0,
                f'{CarbonCapture.flue_gas_name} ({self.mass_unit})': dfluegas_dsyngas_ratio / 100.0

            }

    def grad_techno_producion_vs_syngas_ratio_rwgs(self):
        mol_H2 = (1.0 + self.syngas_ratio) / \
            (1.0 + self.needed_syngas_ratio)
        mol_CO2 = self.syngas_ratio - self.needed_syngas_ratio * mol_H2
        co2_molar_mass = CO2.data_energy_dict['molar_mass']

        needed_syngas_molar_mass = compute_syngas_molar_mass(
            self.needed_syngas_ratio)
        needed_calorific_value = compute_syngas_calorific_value(
            self.needed_syngas_ratio)

        mol_H2up = (1.0 + self.syngas_ratio)
        dmol_H2up = 1.0
        mol_H2down = (1.0 + self.needed_syngas_ratio)
        dmol_H2down = 0.0

        dmol_H2_dsyngas_ratio = (dmol_H2up * mol_H2down) / mol_H2down ** 2
        dmol_CO2_dsyngas_ratio = 1 - \
            self.needed_syngas_ratio * dmol_H2_dsyngas_ratio

        dco2_dsyngas_ratio = self.syngas_ratio_techno.compute_dco2_prod_dsyngas_ratio(mol_CO2, mol_H2, co2_molar_mass, needed_syngas_molar_mass,
                                                                                      needed_calorific_value, dmol_CO2_dsyngas_ratio, dmol_H2_dsyngas_ratio)

        if f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})' not in self.production:
            self.compute_price()
            self.compute_primary_energy_production()

        return {f'{CarbonCapture.flue_gas_name} ({self.mass_unit})': np.identity(len(self.years)) * (self.production[f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})'] * dco2_dsyngas_ratio * self.cost_details['syngas_needs_for_FT'] / self.cost_details['efficiency'])[:, np.newaxis]}

    def grad_techno_consumption_vs_syngas_ratio(self, capex, invest, invest_before_ystart, techno_infos_dict):
        '''
        Compute the gradient of techno consumption vs syngas ratio
        '''
        # compute kerosen production
        if np.all(self.needed_syngas_ratio <= self.syngas_ratio):
            if f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})' not in self.production:
                self.compute_price()
                self.compute_primary_energy_production()

            # syngas component
            dsyngas_needs_dsyngas_ratio = self.syngas_ratio_techno.compute_dsyngas_needs_dsyngas_ratio()
            dsyngas_dsyngas_ratio = np.identity(len(self.years)) * (self.production[f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})'].values * dsyngas_needs_dsyngas_ratio *
                                                                    self.cost_details['syngas_needs_for_FT'].values / self.cost_details['efficiency'].values / self.syngas_ratio_techno.cost_details['efficiency'].values)

            # water component
            dwater_needs_dsyngas_ratio = self.syngas_ratio_techno.compute_dwater_needs_dsyngas_ratio()
            dwater_dsyngas_ratio = np.identity(len(self.years)) * (self.production[f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})'].values * dwater_needs_dsyngas_ratio *
                                                                   self.cost_details['syngas_needs_for_FT'].values / self.cost_details['efficiency'].values / self.syngas_ratio_techno.cost_details['efficiency'].values)

            capex_grad = self.compute_dcapex_dsyngas_ratio()
            dprodenergy_dsyngas_ratio = self.compute_dprod_dfluegas(
                capex, invest, invest_before_ystart, techno_infos_dict, capex_grad)

            delectricity_dsyngas_ratio = self.compute_delec_consumption_dsyngas_ratio(
                dprodenergy_dsyngas_ratio)
            # now syngas is in % grad is divided by 100
            return {f'{Syngas.name} ({self.product_energy_unit})': dsyngas_dsyngas_ratio / 100.0,
                    f'{Water.name} ({self.mass_unit})': dwater_dsyngas_ratio / 100.0,
                    f'{Electricity.name} ({self.product_energy_unit})': delectricity_dsyngas_ratio / 100.0
                    }

        elif np.all(self.needed_syngas_ratio > self.syngas_ratio):
            dco2_needs_dsyngas_ratio = self.syngas_ratio_techno.compute_dco2_needs_dsyngas_ratio()
            dco2_cons_dsyngas_ratio = np.identity(len(self.years)) * (dco2_needs_dsyngas_ratio * self.production[f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})'].values /
                                                                      self.price_details_sg_techno['efficiency'].values * self.cost_details['syngas_needs_for_FT'].values / self.cost_details['efficiency'].values)

            dsyngas_needs_dsyngas_ratio = self.syngas_ratio_techno.compute_dsyngas_needs_dsyngas_ratio()
            dsyngas_dsyngas_ratio = np.identity(len(self.years)) * (self.production[f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})'].values * dsyngas_needs_dsyngas_ratio *
                                                                    self.cost_details['syngas_needs_for_FT'].values / self.cost_details['efficiency'].values / self.syngas_ratio_techno.cost_details['efficiency'].values)

            capex_grad = self.compute_dcapex_dsyngas_ratio()
            dprodenergy_dsyngas_ratio = self.compute_dprod_dfluegas(
                capex, invest, invest_before_ystart, techno_infos_dict, capex_grad)

            delectricity_dsyngas_ratio = self.compute_delec_consumption_dsyngas_ratio(
                dprodenergy_dsyngas_ratio)
            delec_dsyngas_ratio = delectricity_dsyngas_ratio + np.identity(len(self.years)) * (-1.0 * self.syngas_ratio_techno.slope_elec_demand * self.cost_details[
                'syngas_needs_for_FT'] * self.production[f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})'] / self.cost_details['efficiency']).to_numpy()[:, np.newaxis]
            # now syngas is in % grad is divided by 100
            return {f'{CarbonCapture.name} ({self.mass_unit})': dco2_cons_dsyngas_ratio / 100.0,
                    f'{Syngas.name} ({self.product_energy_unit})': dsyngas_dsyngas_ratio / 100.0,
                    f'{Electricity.name} ({self.product_energy_unit})': delec_dsyngas_ratio / 100.0

                    }

        else:

            # case we have mixed syngas ratio

            # WGS

            if f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})' not in self.production:
                self.compute_price()
                self.compute_primary_energy_production()

            # syngas component
            dsyngas_needs_dsyngas_ratio = self.syngas_ratio_techno_wgs.compute_dsyngas_needs_dsyngas_ratio()
            dsyngas_dsyngas_ratio_wgs = np.identity(len(self.years)) * (self.production[f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})'].values * dsyngas_needs_dsyngas_ratio *
                                                                        self.cost_details['syngas_needs_for_FT'].values / self.cost_details['efficiency'].values / self.syngas_ratio_techno_wgs.cost_details['efficiency'].values)

            # water component
            dwater_needs_dsyngas_ratio = self.syngas_ratio_techno_wgs.compute_dwater_needs_dsyngas_ratio()
            dwater_dsyngas_ratio_wgs = np.identity(len(self.years)) * (self.production[f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})'].values * dwater_needs_dsyngas_ratio *
                                                                       self.cost_details['syngas_needs_for_FT'].values / self.cost_details['efficiency'].values / self.syngas_ratio_techno_wgs.cost_details['efficiency'].values)

            capex_grad = self.compute_dcapex_dsyngas_ratio()
            dprodenergy_dsyngas_ratio = self.compute_dprod_dfluegas(
                capex, invest, invest_before_ystart, techno_infos_dict, capex_grad)

            delectricity_dsyngas_ratio_wgs = self.compute_delec_consumption_dsyngas_ratio(
                dprodenergy_dsyngas_ratio)
            delec_dsyngas_ratio_wgs = delectricity_dsyngas_ratio_wgs + np.identity(len(self.years)) * (-1.0 * self.syngas_ratio_techno.slope_elec_demand * self.cost_details[
                'syngas_needs_for_FT'] * self.production[f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})'] / self.syngas_ratio_techno_wgs.cost_details['efficiency']).to_numpy()[:, np.newaxis]

            # RWGS

            dco2_needs_dsyngas_ratio = self.syngas_ratio_techno_rwgs.compute_dco2_needs_dsyngas_ratio()
            dco2_cons_dsyngas_ratio_rwgs = np.identity(len(self.years)) * (dco2_needs_dsyngas_ratio * self.production[f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})'].values /
                                                                           self.price_details_sg_techno['efficiency'].values * self.cost_details['syngas_needs_for_FT'].values / self.cost_details['efficiency'].values)

            dsyngas_needs_dsyngas_ratio = self.syngas_ratio_techno_rwgs.compute_dsyngas_needs_dsyngas_ratio()
            dsyngas_dsyngas_ratio_rwgs = np.identity(len(self.years)) * (self.production[f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})'].values * dsyngas_needs_dsyngas_ratio *
                                                                         self.cost_details['syngas_needs_for_FT'].values / self.cost_details['efficiency'].values / self.syngas_ratio_techno.cost_details['efficiency'].values)

            capex_grad = self.compute_dcapex_dsyngas_ratio()
            dprodenergy_dsyngas_ratio = self.compute_dprod_dfluegas(
                capex, invest, invest_before_ystart, techno_infos_dict, capex_grad)

            delectricity_dsyngas_ratio = self.compute_delec_consumption_dsyngas_ratio(
                dprodenergy_dsyngas_ratio)
            delec_dsyngas_ratio_rwgs = delectricity_dsyngas_ratio + np.identity(len(self.years)) * (-1.0 * self.syngas_ratio_techno.slope_elec_demand * self.cost_details[
                'syngas_needs_for_FT'] * self.production[f'{LiquidFuelTechno.energy_name} ({self.product_energy_unit})'] / self.cost_details['efficiency']).to_numpy()[:, np.newaxis]

            if 'complex128' in [dsyngas_dsyngas_ratio_rwgs.dtype, dsyngas_dsyngas_ratio_wgs.dtype, delec_dsyngas_ratio_rwgs.dtype]:
                arr_type = 'complex128'
            else:
                arr_type = 'float64'

            dsyngas_dsyngas_ratio = np.zeros(
                (len(self.years), len(self.years)), dtype=arr_type)
            dwater_dsyngas_ratio = np.zeros(
                (len(self.years), len(self.years)), dtype=arr_type)
            dco2_dsyngas_ratio = np.zeros(
                (len(self.years), len(self.years)), dtype=arr_type)
            delec_dsyngas_ratio = np.zeros(
                (len(self.years), len(self.years)), dtype=arr_type)

            for i in range(self.year_end - self.year_start + 1):
                if(self.syngas_ratio[i] < self.needed_syngas_ratio):
                    # RWGS
                    dsyngas_dsyngas_ratio[i,
                                          :] = dsyngas_dsyngas_ratio_rwgs[i, :]
                    dco2_dsyngas_ratio[i,
                                       :] = dco2_cons_dsyngas_ratio_rwgs[i, :]
                    delec_dsyngas_ratio[i, :] = delec_dsyngas_ratio_rwgs[i, :]

                else:
                    dsyngas_dsyngas_ratio[i,
                                          :] = dsyngas_dsyngas_ratio_wgs[i, :]
                    dwater_dsyngas_ratio[i, :] = dwater_dsyngas_ratio_wgs[i, :]
#                     delec_dsyngas_ratio[i,
#                                         :] = delec_dsyngas_ratio_wgs[i, :]
            # now syngas is in % grad is divided by 100
            return {f'{CarbonCapture.name} ({self.mass_unit})': dco2_dsyngas_ratio / 100.0,
                    f'{Syngas.name} ({self.product_energy_unit})': dsyngas_dsyngas_ratio / 100.0,
                    f'{Electricity.name} ({self.product_energy_unit})': delec_dsyngas_ratio / 100.0,
                    f'{Water.name} ({self.mass_unit})': dwater_dsyngas_ratio / 100.0,

                    }
