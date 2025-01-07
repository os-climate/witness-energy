'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/26-2024/06/24 Copyright 2023 Capgemini

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

import numpy as np
import pandas as pd
from climateeconomics.core.core_resources.resource_mix.resource_mix import (
    ResourceMixModel,
)

from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.syngas import Syngas
from energy_models.core.stream_type.energy_models.syngas import (
    compute_calorific_value as compute_syngas_calorific_value,
)
from energy_models.core.stream_type.energy_models.syngas import (
    compute_molar_mass as compute_syngas_molar_mass,
)
from energy_models.core.stream_type.resources_models.water import Water
from energy_models.core.techno_type.base_techno_models.liquid_fuel_techno import (
    LiquidFuelTechno,
)
from energy_models.database_witness_energy import DatabaseWitnessEnergy
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.gaseous_hydrogen.water_gas_shift.water_gas_shift import WGS
from energy_models.models.gaseous_hydrogen.water_gas_shift.water_gas_shift_disc import (
    WaterGasShiftDiscipline,
)
from energy_models.models.syngas.reversed_water_gas_shift.reversed_water_gas_shift import (
    RWGS,
)
from energy_models.models.syngas.reversed_water_gas_shift.reversed_water_gas_shift_disc import (
    ReversedWaterGasShiftDiscipline,
)


class FischerTropsch(LiquidFuelTechno):

    def __init__(self, name):
        super().__init__(name)
        self.inputs['syngas_ratio'] = None
        self.inputs['needed_syngas_ratio'] = None
        self.syngas_energy_dict = None
        self.gaseous_hydrogen_energy_dict = None
        self.sg_transformation_name = None
        self.syn_needs_wgs = None
        self.syn_needs_rwgs = None
        self.costs_details_sg_techno = None
        self.syngas_ratio_techno = None
        self.syngas_ratio_techno_rwgs = None
        self.costs_details_rwgs = None
        self.water_prod_RWGS = None
        self.syngas_ratio_techno = None
        self.syngas_ratio_techno_wgs = None
        self.price_details_wgs = None
        self.CO2_prod_wgs: float = 0.0
        self.consumption = None
        self.production = None
        self.slope_capex = None

    def configure_energy_data(self):
        '''
        Configure energy data by reading the data_energy_dict in the right Energy class
        Overloaded for each energy type
        '''
        self.data_energy_dict = self.inputs['data_fuel_dict']
        self.syngas_energy_dict = self.inputs[f'{GlossaryEnergy.syngas}.{GlossaryEnergy.data_fuel_dict}']
        self.gaseous_hydrogen_energy_dict = self.inputs[f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.data_fuel_dict']
        self.inputs['needed_syngas_ratio'] = self.inputs['techno_infos_dict']['carbon_number'] / (2 * self.inputs['techno_infos_dict']['carbon_number'] + 1)

    def select_concerning_ratios(self):
        """! Select the ratios to be added to ratio_df
        """
        ratio_df = LiquidFuelTechno.select_concerning_ratios(self)
        if GlossaryEnergy.carbon_capture in ratio_df.columns and self.apply_stream_ratio:
            ratio_df[GlossaryEnergy.carbon_capture] = ratio_df[GlossaryEnergy.carbon_capture].values
        else:
            ratio_df[GlossaryEnergy.carbon_capture] = np.ones(len(self.years))
        self.ratio_df = ratio_df
        return ratio_df

    def compute_other_streams_needs(self):
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.electricity}_needs'] = self.get_electricity_needs()


    def compute_specifif_costs_of_technos(self):
        nb_years = self.year_end - self.year_start + 1
        sg_needs_efficiency = [self.get_theoretical_syngas_needs_for_FT(
        ) / self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']] * nb_years

        # in kwh of fuel by kwh of liquid_fuel

        # Cost of electricity for 1 kWH of liquid_fuel
        self.outputs[f'{GlossaryEnergy.CostOfResourceUsageValue}:{GlossaryEnergy.electricity}'] = self.inputs[f'{GlossaryEnergy.StreamPricesValue}:{GlossaryEnergy.electricity}'] * self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.electricity}_needs']
        if np.all(self.inputs['needed_syngas_ratio'] > self.inputs['syngas_ratio']):
            self.sg_transformation_name = GlossaryEnergy.RWGS
            self.costs_details_sg_techno = self.compute_rwgs_contribution(
                self.inputs['syngas_ratio'])
            # For RWGS dprice is composed of dsyngas, dCO2, delec
            dprice_RWGS_dsyngas_ratio = self.syngas_ratio_techno.compute_dprice_RWGS_wo_taxes_dsyngas_ratio()
            dco2_taxes_dsyngas_ratio = self.syngas_ratio_techno.dco2_taxes_dsyngas_ratio()

            self.dprice_FT_wotaxes_dsyngas_ratio = dprice_RWGS_dsyngas_ratio * self.margin[
                GlossaryEnergy.MarginValue].values / 100.0 * \
                                                   (np.ones(len(self.years)) * sg_needs_efficiency)
            self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.sg_transformation_name}'] = self.costs_details_sg_techno[
                f'{self.sg_transformation_name}_wotaxes']

            self.dprice_FT_dsyngas_ratio = self.dprice_FT_wotaxes_dsyngas_ratio + \
                                           dco2_taxes_dsyngas_ratio * \
                                           (np.identity(len(self.years)) * sg_needs_efficiency) * \
                                           np.sign(np.maximum(
                                               0.0, self.syngas_ratio_techno.carbon_intensity[
                                                   self.sg_transformation_name].values))

        elif np.all(self.inputs['needed_syngas_ratio'] <= self.inputs['syngas_ratio']):
            self.sg_transformation_name = 'WGS'
            self.costs_details_sg_techno = self.compute_wgs_contribution(
                self.inputs['syngas_ratio'])
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
                                               0.0, self.syngas_ratio_techno.carbon_intensity[
                                                   self.sg_transformation_name].values))
            self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.sg_transformation_name}'] = self.costs_details_sg_techno[
                f'{self.sg_transformation_name}_wotaxes']
        else:
            self.sg_transformation_name = 'WGS or RWGS'
            sg_ratio_wgs = np.maximum(
                self.inputs['syngas_ratio'], self.inputs['needed_syngas_ratio'])
            costs_details_sg_techno_wgs = self.compute_wgs_contribution(sg_ratio_wgs)
            self.syn_needs_wgs = self.syngas_ratio_techno_wgs.get_theoretical_syngas_needs(sg_ratio_wgs
                                                                                           )
            costs_details_sg_techno_wgs['sg_ratio'] = self.inputs['syngas_ratio']
            costs_details_sg_techno_wgs[self.sg_transformation_name] = costs_details_sg_techno_wgs['WGS']
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
                                              0.0, self.syngas_ratio_techno.carbon_intensity['WGS'].values))

            sg_ratio_rwgs = np.minimum(
                self.inputs['syngas_ratio'], self.inputs['needed_syngas_ratio'])
            price_details_sg_techno_rwgs = self.compute_rwgs_contribution(
                sg_ratio_rwgs)
            self.syn_needs_rwgs = self.syngas_ratio_techno.get_theoretical_syngas_needs(sg_ratio_rwgs)
            price_details_sg_techno_rwgs['sg_ratio'] = self.inputs['syngas_ratio']
            price_details_sg_techno_rwgs[self.sg_transformation_name] = price_details_sg_techno_rwgs[GlossaryEnergy.RWGS]
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
                                               self.syngas_ratio_techno.carbon_intensity[GlossaryEnergy.RWGS].values) * \
                                           np.sign(np.maximum(
                                               0.0, self.syngas_ratio_techno.carbon_intensity[GlossaryEnergy.RWGS].values))

            self.costs_details_sg_techno = pd.concat([costs_details_sg_techno_wgs.loc[
                                                          costs_details_sg_techno_wgs[
                                                              'sg_ratio'] >= self.inputs['needed_syngas_ratio']],
                                                      price_details_sg_techno_rwgs.loc[
                                                          price_details_sg_techno_rwgs[
                                                              'sg_ratio'] < self.inputs['needed_syngas_ratio']]])
            self.costs_details_sg_techno.sort_index(inplace=True)
            self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.sg_transformation_name}'] = self.costs_details_sg_techno[
                'WGS_wotaxes']

            if 'complex128' in [dprice_FT_dsyngas_ratio_RWGS.dtype, dprice_FT_wotaxes_dsyngas_ratio_RWGS.dtype]:
                arr_type = 'complex128'
            else:
                arr_type = 'float64'
            self.dprice_FT_dsyngas_ratio = np.zeros(
                (len(self.years), len(self.years)), dtype=arr_type)

            self.dprice_FT_wotaxes_dsyngas_ratio = np.zeros(
                (len(self.years), len(self.years)), dtype=arr_type)

            if self.inputs['syngas_ratio'][0] < self.inputs['needed_syngas_ratio']:
                techno_first_year = GlossaryEnergy.RWGS
            else:
                techno_first_year = 'WGS'
            for i in range(self.year_end - self.year_start + 1):
                if self.inputs['syngas_ratio'][i] < self.inputs['needed_syngas_ratio']:

                    self.dprice_FT_dsyngas_ratio[i,
                    :] = dprice_FT_dsyngas_ratio_RWGS[i, :]
                    self.dprice_FT_wotaxes_dsyngas_ratio[i,
                    :] = dprice_FT_wotaxes_dsyngas_ratio_RWGS[i, :]
                    if self.inputs['syngas_ratio'][i] == 0.:
                        self.dprice_FT_dsyngas_ratio[i,
                        :] = dprice_FT_wotaxes_dsyngas_ratio_RWGS[i, :]

                    if techno_first_year == 'WGS':
                        self.dprice_FT_dsyngas_ratio[i, 0] = 0.0
                        self.dprice_FT_wotaxes_dsyngas_ratio[i, 0] = 0.0

                    self.cost_details.loc[i, self.sg_transformation_name] = self.costs_details_sg_techno[
                        f'{GlossaryEnergy.RWGS}_wotaxes'].values[i]

                else:

                    self.dprice_FT_dsyngas_ratio[i,
                    :] = dprice_FT_dsyngas_ratio_wgs[i, :]
                    self.dprice_FT_wotaxes_dsyngas_ratio[i,
                    :] = dprice_FT_wotaxes_dsyngas_ratio_wgs[i, :]

                    if self.inputs['syngas_ratio'][i] == 0.:
                        self.dprice_FT_dsyngas_ratio[i,
                        :] = dprice_FT_wotaxes_dsyngas_ratio_wgs[i, :]

                    if techno_first_year == GlossaryEnergy.RWGS:
                        self.dprice_FT_dsyngas_ratio[i, 0] = 0.0
                        self.dprice_FT_wotaxes_dsyngas_ratio[i, 0] = 0.0

            # We need WGS then RWGS depending on the years

        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:syngas_needs_for_FT'] = self.get_theoretical_syngas_needs_for_FT(
        )

        syngas_costs = self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.sg_transformation_name}'] * \
                                         self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:syngas_needs_for_FT'] / \
                                         self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.syngas} before transformation'] = self.inputs[f'{GlossaryEnergy.StreamPricesValue}:{GlossaryEnergy.syngas}'] * \
                                                                              self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:syngas_needs_for_FT'] / \
                                                                              self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

        self.specific_costs = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.syngas: syngas_costs
        })

    def compute_rwgs_contribution(self, sg_ratio):
        years = np.arange(self.year_start, self.year_end + 1)
        utlisation_ratio = pd.DataFrame({GlossaryEnergy.Years: years,
                                         GlossaryEnergy.UtilisationRatioValue: self.utilisation_ratio})
        inputs_dict = {GlossaryEnergy.YearStart: self.year_start,
                       GlossaryEnergy.YearEnd: self.year_end,
                       GlossaryEnergy.UtilisationRatioValue: utlisation_ratio,
                       'techno_infos_dict': ReversedWaterGasShiftDiscipline.techno_infos_dict_default,
                       GlossaryEnergy.StreamPricesValue: self.stream_prices,
                       GlossaryEnergy.StreamsCO2EmissionsValue: self.streams_CO2_emissions,
                       # We suppose invest are not influencing the price of WGS or RWGS because the gradient is a mess to compute
                       # AND Is it obvious the fact that investing in Fischer
                       # Tropsch will decrease the price of WGS ?
                       GlossaryEnergy.InvestLevelValue: pd.DataFrame(
                           {GlossaryEnergy.Years: years, GlossaryEnergy.InvestValue: 1.0}),
                       GlossaryEnergy.InvestmentBeforeYearStartValue: DatabaseWitnessEnergy.get_techno_invest_before_year_start(
                           techno_name=ReversedWaterGasShiftDiscipline.techno_name, year_start=self.year_start, construction_delay=GlossaryEnergy.TechnoConstructionDelayDict[ReversedWaterGasShiftDiscipline.techno_name])[0],
                       GlossaryEnergy.CO2TaxesValue: self.CO2_taxes,
                       GlossaryEnergy.MarginValue: pd.DataFrame(
                           {GlossaryEnergy.Years: years, GlossaryEnergy.MarginValue: 100.0}),
                       GlossaryEnergy.TransportCostValue: pd.DataFrame({GlossaryEnergy.Years: years, 'transport': 0.0}),
                       GlossaryEnergy.TransportMarginValue: pd.DataFrame(
                           {GlossaryEnergy.Years: years, GlossaryEnergy.MarginValue: 100.0}),
                       'initial_production': ReversedWaterGasShiftDiscipline.initial_production,
                       GlossaryEnergy.RessourcesCO2EmissionsValue: self.resources_CO2_emissions,
                       GlossaryEnergy.ResourcesPriceValue: self.resources_prices,
                       'syngas_ratio': sg_ratio * 100.0,
                       'needed_syngas_ratio': self.inputs['needed_syngas_ratio'] * 100.0,
                       'scaling_factor_invest_level': self.scaling_factor_invest_level,
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production,
                       'smooth_type': self.smooth_type,
                       GlossaryEnergy.BoolApplyRatio: self.apply_ratio,
                       GlossaryEnergy.BoolApplyStreamRatio: self.apply_stream_ratio,
                       GlossaryEnergy.BoolApplyResourceRatio: self.apply_resource_ratio,
                       'data_fuel_dict': self.syngas_energy_dict,
                       GlossaryEnergy.ResourcesUsedForProductionValue: GlossaryEnergy.TechnoResourceUsedDict[GlossaryEnergy.RWGS],
                       GlossaryEnergy.ResourcesUsedForBuildingValue: GlossaryEnergy.TechnoBuildingResourceDict[GlossaryEnergy.RWGS] if GlossaryEnergy.RWGS in GlossaryEnergy.TechnoBuildingResourceDict else [],
                       GlossaryEnergy.StreamsUsedForProductionValue: GlossaryEnergy.TechnoStreamsUsedDict[GlossaryEnergy.RWGS],
                       GlossaryEnergy.ConstructionDelay: GlossaryEnergy.TechnoConstructionDelayDict[GlossaryEnergy.RWGS],
                       GlossaryEnergy.LifetimeName: GlossaryEnergy.TechnoLifetimeDict[GlossaryEnergy.RWGS],
                       GlossaryEnergy.InitialPlantsAgeDistribFactor: DatabaseWitnessEnergy.get_techno_age_distrib_factor(techno_name=ReversedWaterGasShiftDiscipline.techno_name, year=self.year_start)[0],
                       }
        if self.apply_stream_ratio:
            inputs_dict[GlossaryEnergy.AllStreamsDemandRatioValue] = self.all_streams_demand_ratio
        if self.apply_resource_ratio:
            inputs_dict[ResourceMixModel.RATIO_USABLE_DEMAND] = self.ratio_available_resource

        self.syngas_ratio_techno = RWGS(GlossaryEnergy.RWGS)
        self.syngas_ratio_techno.syngas_COH2_ratio = sg_ratio * 100.0
        self.syngas_ratio_techno.configure_parameters(inputs_dict)
        self.syngas_ratio_techno.configure_parameters_update(inputs_dict)
        cost_details = self.syngas_ratio_techno.compute_price()
        self.syngas_ratio_techno_rwgs = self.syngas_ratio_techno
        self.costs_details_rwgs = cost_details
        self.water_prod_RWGS = self.syngas_ratio_techno.get_theoretical_water_prod()
        return cost_details

    def compute_wgs_contribution(self, sg_ratio):
        inputs_wgs = self.inputs
        inputs_wgs.update({
                       'techno_infos_dict': WaterGasShiftDiscipline.techno_infos_dict_default,
                       'initial_production': WaterGasShiftDiscipline.initial_production,
                       'syngas_ratio': sg_ratio * 100.0,
                       'needed_syngas_ratio': self.inputs['needed_syngas_ratio'] * 100.0,
                       GlossaryEnergy.ResourcesUsedForProductionValue: GlossaryEnergy.TechnoResourceUsedDict[GlossaryEnergy.WaterGasShift],
                       GlossaryEnergy.ResourcesUsedForBuildingValue: GlossaryEnergy.TechnoBuildingResourceDict[GlossaryEnergy.WaterGasShift] if GlossaryEnergy.WaterGasShift in GlossaryEnergy.TechnoBuildingResourceDict else [],
                       GlossaryEnergy.StreamsUsedForProductionValue: GlossaryEnergy.TechnoStreamsUsedDict[GlossaryEnergy.WaterGasShift],
                       GlossaryEnergy.ConstructionDelay: GlossaryEnergy.TechnoConstructionDelayDict[GlossaryEnergy.WaterGasShift],
                       GlossaryEnergy.LifetimeName: GlossaryEnergy.TechnoLifetimeDict[GlossaryEnergy.WaterGasShift],
                       GlossaryEnergy.InitialPlantsAgeDistribFactor:DatabaseWitnessEnergy.get_techno_age_distrib_factor(techno_name=WaterGasShiftDiscipline.techno_name, year=self.year_start)[0],
        })
        dfs_to_converts = {
            GlossaryEnergy.InvestLevelValue: pd.DataFrame({GlossaryEnergy.Years: self.years, GlossaryEnergy.InvestValue: 1.0}),
            GlossaryEnergy.InvestmentBeforeYearStartValue:
                DatabaseWitnessEnergy.get_techno_invest_before_year_start(
                    techno_name=WaterGasShiftDiscipline.techno_name, year_start=self.year_start,
                    construction_delay=GlossaryEnergy.TechnoConstructionDelayDict[WaterGasShiftDiscipline.techno_name])[
                    0],
            GlossaryEnergy.MarginValue: pd.DataFrame({GlossaryEnergy.Years: self.years, GlossaryEnergy.MarginValue: 100.0}),
            GlossaryEnergy.TransportCostValue: pd.DataFrame({GlossaryEnergy.Years: self.years, 'transport': 0.0}),
            GlossaryEnergy.TransportMarginValue: pd.DataFrame({GlossaryEnergy.Years: self.years, GlossaryEnergy.MarginValue: 100.0}),
        }
        for key, df in dfs_to_converts.items():
            for column in df.columns:
                inputs_wgs.update({f"{key}:{column}": df.columns.values})

        self.syngas_ratio_techno = WGS('WGS')
        self.syngas_ratio_techno.inputs = inputs_wgs
        price_details = self.syngas_ratio_techno.compute_price()
        self.syngas_ratio_techno_wgs = self.syngas_ratio_techno
        self.price_details_wgs = price_details
        self.CO2_prod_wgs = self.syngas_ratio_techno.get_theoretical_co2_prod()

        return price_details

    def compute_byproducts_production(self):
        water_prod = 0.0
        if self.sg_transformation_name in ['WGS', 'WGS or RWGS']:
            co2_prod = self.CO2_prod_wgs * \
                       self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:syngas_needs_for_FT'] / \
                       self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

            self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:{CarbonCapture.flue_gas_name} ({GlossaryEnergy.mass_unit})'] = co2_prod * \
                                                                                            self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:'
                                                                                                f'{LiquidFuelTechno.energy_name} ({self.product_unit})']

        elif self.sg_transformation_name == GlossaryEnergy.RWGS:
            self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:{CarbonCapture.flue_gas_name} ({GlossaryEnergy.mass_unit})'] = 0.0


        if self.sg_transformation_name in [GlossaryEnergy.RWGS, 'WGS or RWGS']:

            water_prod = self.water_prod_RWGS * \
                         self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:syngas_needs_for_FT'] / \
                         self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']


        water_prod += self.get_theoretical_water_prod_from_FT() / \
                      self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

        self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:{Water.name} ({GlossaryEnergy.mass_unit})'] = water_prod * \
                                                                       self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:'
                                                                           f'{LiquidFuelTechno.energy_name} ({self.product_unit})']



    def compute_streams_consumption(self):

        # Compute elec demand from WGS
        elec_needs_wgs = self.costs_details_sg_techno[f'{GlossaryEnergy.electricity}_needs'] * \
                         self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:syngas_needs_for_FT'] / \
                         self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

        # Consumption of WGS and FT
        self.outputs[f'{GlossaryEnergy.TechnoConsumptionValue}:{GlossaryEnergy.electricity} ({self.product_unit})'] = (self.cost_details[
                                                                                             f'{GlossaryEnergy.electricity}_needs'] + elec_needs_wgs) * \
                                                                                        self.outputs[f'{GlossaryEnergy.TechnoDetailedProductionValue}:'
                                                                                            f'{LiquidFuelTechno.energy_name} ({self.product_unit})']  # in kWH

        # needs of syngas in kWh syngasin/kWhsyngas_out
        syngas_needs_wgs = self.costs_details_sg_techno['syngas_needs']

        # in kWhsyngas_in/kwhliquid_fuel and syngas_needs_for_FT is in
        # kWhsyngas_out/kWhliquid_fuel
        syngas_needs = syngas_needs_wgs * \
                       self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:syngas_needs_for_FT'] / \
                       self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

        # Compute of initial syngas vs output liquid_fuel
        self.outputs[f'{GlossaryEnergy.TechnoConsumptionValue}:{GlossaryEnergy.syngas} ({self.product_unit})'] = syngas_needs * \
                                                                                   self.outputs[f'{GlossaryEnergy.TechnoDetailedProductionValue}:'
                                                                                       f'{LiquidFuelTechno.energy_name} ({self.product_unit})']  # in kWH

        # If WGS in the loop then we need water in the process
        if self.sg_transformation_name in ['WGS', 'WGS or RWGS']:
            water_needs = self.costs_details_sg_techno[f"{GlossaryEnergy.WaterResource}_needs"].fillna(0.0) * \
                          self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:syngas_needs_for_FT'] / \
                          self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

            self.outputs[f'{GlossaryEnergy.TechnoConsumptionValue}:{Water.name} ({GlossaryEnergy.mass_unit})'] = water_needs * \
                                                                            self.outputs[f'{GlossaryEnergy.TechnoDetailedProductionValue}:'
                                                                                f'{LiquidFuelTechno.energy_name} ({self.product_unit})']

        elif self.sg_transformation_name == GlossaryEnergy.RWGS:
            self.outputs[f'{GlossaryEnergy.TechnoConsumptionValue}:{Water.name} ({GlossaryEnergy.mass_unit})'] = 0.0

        if self.sg_transformation_name == 'WGS':
            self.outputs[f'{GlossaryEnergy.TechnoConsumptionValue}:{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit})'] = 0.0

        elif self.sg_transformation_name in [GlossaryEnergy.RWGS, 'WGS or RWGS']:

            co2_needs = self.costs_details_sg_techno[f"{GlossaryEnergy.CO2Resource}_needs"].fillna(0.0) * \
                        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:syngas_needs_for_FT'] / \
                        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

            self.outputs[f'{GlossaryEnergy.TechnoConsumptionValue}:{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit})'] = co2_needs * \
                                                                                    self.outputs[f'{GlossaryEnergy.TechnoDetailedProductionValue}:'
                                                                                        f'{LiquidFuelTechno.energy_name} ({self.product_unit})']

        self.consumption = self.consumption_detailed.fillna(0.0)

    def compute_scope_2_emissions(self):
        ''' 
        Need to take into account negative CO2 from biomass_dry and CO2 from electricity (can be 0.0 or positive)
        '''

        # Compute elec demand from WGS
        elec_needs_wgs = self.costs_details_sg_techno[f'{GlossaryEnergy.electricity}_needs'] * \
                         self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:syngas_needs_for_FT'] / \
                         self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

        self.outputs[f'CO2_emissions_detailed:{GlossaryEnergy.electricity}'] = self.inputs[f'{GlossaryEnergy.StreamsCO2EmissionsValue}:{GlossaryEnergy.electricity}'] * \
                                                            (self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.electricity}_needs'] + elec_needs_wgs)

        # needs of syngas in kWh syngasin/kWhsyngas_out
        syngas_needs_wgs = self.costs_details_sg_techno['syngas_needs']

        # in kWhsyngas_in/kwhliquid_fuel and syngas_needs_for_FT is in
        # kWhsyngas_out/kWhliquid_fuel
        syngas_needs = syngas_needs_wgs * \
                       self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:syngas_needs_for_FT'] / \
                       self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

        self.outputs[f'CO2_emissions_detailed:{GlossaryEnergy.syngas}'] = self.streams_CO2_emissions[
                                                 GlossaryEnergy.syngas] * syngas_needs

        co2_needs = 0.0
        water_needs = 0.0
        if self.sg_transformation_name in ['WGS', 'WGS or RWGS']:
            water_needs += self.costs_details_sg_techno[f"{GlossaryEnergy.WaterResource}_needs"].fillna(0.0) * \
                           self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:syngas_needs_for_FT'] / \
                           self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

            co2_needs += -self.CO2_prod_wgs * \
                         self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:syngas_needs_for_FT'] / \
                         self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

        if self.sg_transformation_name in [GlossaryEnergy.RWGS, 'WGS or RWGS']:
            co2_needs += self.costs_details_sg_techno[f"{GlossaryEnergy.CO2Resource}_needs"].fillna(0.0) * \
                         self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:syngas_needs_for_FT'] / \
                         self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

        self.outputs[f'CO2_emissions_detailed:{CO2.name}'] = self.inputs[f'{GlossaryEnergy.RessourcesCO2EmissionsValue}:{GlossaryEnergy.CO2Resource}'] * co2_needs
        self.outputs[f'CO2_emissions_detailed:{Water.name}'] = self.inputs[f'{GlossaryEnergy.RessourcesCO2EmissionsValue}:{GlossaryEnergy.WaterResource}'] * water_needs

        self.outputs['CO2_emissions_detailed:Scope 2'] = self.outputs[f'CO2_emissions_detailed:{GlossaryEnergy.electricity}'] + self.outputs[f'CO2_emissions_detailed:{GlossaryEnergy.syngas}'] + \
                                           self.outputs[f'CO2_emissions_detailed:{CO2.name}'] + self.outputs[f'CO2_emissions_detailed:{Water.name}']

    def get_theoretical_syngas_needs_for_FT(self):
        ''' 
        Get syngas needs in kWh syngas /kWh liquid_fuel
        H2 + n/(2n+1)CO --> 1/(2n+1) CnH_2n+1 + n/(2n+1)H20
        Warning : molar mass is in g/mol but we divide and multiply by one
        '''

        mol_syngas = 1.0
        mol_liquid_fuel = 1.0 / \
                          (2 * self.inputs['techno_infos_dict']['carbon_number'] + 1)
        syngas_molar_mass = compute_syngas_molar_mass(self.inputs['needed_syngas_ratio'])

        syngas_calorific_value = compute_syngas_calorific_value(
            self.inputs['needed_syngas_ratio'])
        syngas_needs_for_FT = mol_syngas * syngas_molar_mass * syngas_calorific_value / \
                              (mol_liquid_fuel * self.inputs['data_fuel_dict']['molar_mass'] *
                               self.inputs['data_fuel_dict']['calorific_value'])

        return syngas_needs_for_FT

    def get_theoretical_water_prod_from_FT(self):
        ''' 
        Get water prod in kg H20 /kWh liquid_fuel
        H2 + n/(2n+1)CO --> 1/(2n+1) CnH_2n+1 + n/(2n+1)H20
        Warning : molar mass is in g/mol but we divide and multiply by one
        '''

        mol_H20 = self.inputs['techno_infos_dict']['carbon_number']
        mol_liquid_fuel = 1.0
        water_data = Water.data_energy_dict
        water_prod = mol_H20 * water_data['molar_mass'] / \
                     (mol_liquid_fuel * self.inputs['data_energy_dict']['molar_mass'] *
                      self.inputs['data_energy_dict']['calorific_value'])

        return water_prod
