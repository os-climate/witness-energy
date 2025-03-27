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
"""

import pandas as pd
from climateeconomics.core.core_resources.resource_mix.resource_mix import (
    ResourceMixModel,
)

from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
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
        self.sg_transformation_name = None
        self.syn_needs_wgs = None
        self.syn_needs_rwgs = None
        self.syngas_ratio_techno = None
        self.syngas_ratio_techno_rwgs = None
        self.costs_details_rwgs = None
        self.water_prod_RWGS = None
        self.syngas_ratio_techno = None
        self.CO2_prod_wgs: float = 0.0
        self.consumption = None
        self.production = None
        self.slope_capex = None

    def compute_transformation_type(self):
        self.temp_variables['needed_syngas_ratio'] = self.inputs['techno_infos_dict']['carbon_number'] / (2 * self.inputs['techno_infos_dict']['carbon_number'] + 1)
        if self.np.all(self.temp_variables['needed_syngas_ratio'] > self.inputs['syngas_ratio']):
            self.sg_transformation_name = GlossaryEnergy.RWGS

        elif self.np.all(self.temp_variables['needed_syngas_ratio'] <= self.inputs['syngas_ratio']):
            self.sg_transformation_name = 'WGS'
        else:
            self.sg_transformation_name = 'WGS or RWGS'

    def compute(self):
        self.compute_transformation_type()
        super(FischerTropsch, self).compute()

    def compute_energies_needs(self):
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.electricity}_needs'] = self.get_electricity_needs()

    def compute_specifif_costs_of_technos(self):
        # Cost of electricity for 1 kWH of liquid_fuel
        self.outputs[f'{GlossaryEnergy.CostOfResourceUsageValue}:{GlossaryEnergy.electricity}'] = \
            self.inputs[f'{GlossaryEnergy.StreamPricesValue}:{GlossaryEnergy.electricity}'] * self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.electricity}_needs']

        if self.sg_transformation_name == GlossaryEnergy.RWGS:
            self.compute_rwgs_contribution(self.inputs['syngas_ratio'])
            self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.sg_transformation_name}'] = \
                self.syngas_ratio_techno_wgs.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.sg_transformation_name}_wotaxes']

        elif self.sg_transformation_name == 'WGS':
            self.compute_wgs_contribution(self.inputs['syngas_ratio'])
            self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.sg_transformation_name}'] = \
                self.syngas_ratio_techno_wgs.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.sg_transformation_name}_wotaxes']
        else:
            # WGS
            sg_ratio_wgs = self.np.maximum(self.inputs['syngas_ratio'], self.temp_variables['needed_syngas_ratio'])
            costs_details_sg_techno_wgs = self.compute_wgs_contribution(sg_ratio_wgs)
            self.syn_needs_wgs = self.syngas_ratio_techno_wgs.get_theoretical_syngas_needs(sg_ratio_wgs)
            costs_details_sg_techno_wgs['sg_ratio'] = self.inputs['syngas_ratio']
            costs_details_sg_techno_wgs[self.sg_transformation_name] = costs_details_sg_techno_wgs['WGS']

            # RWGS
            sg_ratio_rwgs = self.np.minimum(self.inputs['syngas_ratio'], self.temp_variables['needed_syngas_ratio'])
            price_details_sg_techno_rwgs = self.compute_rwgs_contribution(sg_ratio_rwgs)
            self.syn_needs_rwgs = self.syngas_ratio_techno.get_theoretical_syngas_needs(sg_ratio_rwgs)
            price_details_sg_techno_rwgs['sg_ratio'] = self.inputs['syngas_ratio']
            price_details_sg_techno_rwgs[self.sg_transformation_name] = price_details_sg_techno_rwgs[GlossaryEnergy.RWGS]

            # Mix of both
            self.costs_details_sg_techno = pd.concat([costs_details_sg_techno_wgs.loc[
                                                          costs_details_sg_techno_wgs[
                                                              'sg_ratio'] >= self.temp_variables['needed_syngas_ratio']],
                                                      price_details_sg_techno_rwgs.loc[
                                                          price_details_sg_techno_rwgs[
                                                              'sg_ratio'] < self.temp_variables['needed_syngas_ratio']]])

            cost = self.zeros_array
            indexes_wgs  = self.inputs['syngas_ratio'] >= self.temp_variables['needed_syngas_ratio']
            indexes_rwgs = self.inputs['syngas_ratio'] < self.temp_variables['needed_syngas_ratio']
            cost[indexes_wgs] = 1

            self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.sg_transformation_name}'] = self.costs_details_sg_techno['WGS_wotaxes']

            for i in range(self.year_end - self.year_start + 1):
                if self.inputs['syngas_ratio'][i] < self.temp_variables['needed_syngas_ratio']:
                    self.cost_details.loc[i, self.sg_transformation_name] = self.costs_details_sg_techno[f'{GlossaryEnergy.RWGS}_wotaxes'].values[i]


        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:syngas_needs_for_FT'] = self.get_theoretical_syngas_needs_for_FT()

        syngas_costs = self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.sg_transformation_name}'] * \
                                         self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:syngas_needs_for_FT'] / \
                                         self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.syngas} before transformation'] = self.inputs[f'{GlossaryEnergy.StreamPricesValue}:{GlossaryEnergy.syngas}'] * \
                                                                                                                    self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:syngas_needs_for_FT'] / \
                                                                                                                    self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

        self.outputs[f'{GlossaryEnergy.SpecificCostsForProductionValue}:{GlossaryEnergy.Years}'] = self.years
        self.outputs[f'{GlossaryEnergy.SpecificCostsForProductionValue}:{GlossaryEnergy.syngas}'] = syngas_costs
        self.outputs[f'{GlossaryEnergy.SpecificCostsForProductionValue}:Total'] = syngas_costs

    def compute_rwgs_contribution(self, sg_ratio):
        years = self.np.arange(self.year_start, self.year_end + 1)
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
                       'needed_syngas_ratio': self.temp_variables['needed_syngas_ratio'] * 100.0,
                       'scaling_factor_invest_level': self.scaling_factor_invest_level,
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production,
                       'smooth_type': self.smooth_type,
                       GlossaryEnergy.BoolApplyRatio: self.apply_ratio,
                       GlossaryEnergy.BoolApplyStreamRatio: self.apply_stream_ratio,
                       GlossaryEnergy.BoolApplyResourceRatio: self.apply_resource_ratio,
                       'data_fuel_dict': self.inputs[f'{GlossaryEnergy.syngas}.{GlossaryEnergy.data_fuel_dict}'],
                       GlossaryEnergy.ResourcesUsedForProductionValue: GlossaryEnergy.TechnoResourceUsedDict[GlossaryEnergy.RWGS],
                       GlossaryEnergy.ResourcesUsedForBuildingValue: GlossaryEnergy.TechnoBuildingResourceDict[GlossaryEnergy.RWGS] if GlossaryEnergy.RWGS in GlossaryEnergy.TechnoBuildingResourceDict else [],
                       GlossaryEnergy.EnergiesUsedForProductionValue: GlossaryEnergy.TechnoStreamsUsedDict[GlossaryEnergy.RWGS],
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
        self.syngas_ratio_techno.configure_parameters_update()
        cost_details = self.syngas_ratio_techno.compute_price()
        self.syngas_ratio_techno_rwgs = self.syngas_ratio_techno
        self.costs_details_rwgs = cost_details
        self.water_prod_RWGS = self.syngas_ratio_techno.get_theoretical_water_prod()
        return cost_details

    def compute_wgs_contribution(self, sg_ratio):
        keys_to_copy = [
            GlossaryEnergy.YearStart,
            GlossaryEnergy.YearEnd,
            'data_fuel_dict',
        ]
        inputs_wgs = {key: self.inputs[key] for key in keys_to_copy}
        others = [GlossaryEnergy.ResourcesPriceValue,
                  GlossaryEnergy.StreamPricesValue,
                  GlossaryEnergy.RessourcesCO2EmissionsValue,
                  GlossaryEnergy.StreamsCO2EmissionsValue,
                  GlossaryEnergy.CO2TaxesValue]
        for key in others:
            inputs_arrays = list(filter(lambda x: x.startswith(key + ':'), self.inputs.keys()))
            inputs_wgs.update({name: self.inputs[name] for name in inputs_arrays})
        inputs_wgs.update({
                       GlossaryEnergy.YearStart: self.year_start,
                       GlossaryEnergy.YearEnd: self.year_end,
                       'techno_infos_dict': WaterGasShiftDiscipline.techno_infos_dict_default,
                       'initial_production': WaterGasShiftDiscipline.initial_production,
                       'syngas_ratio': sg_ratio * 100.0,
                       'needed_syngas_ratio': self.temp_variables['needed_syngas_ratio'] * 100.0,
                       GlossaryEnergy.ResourcesUsedForProductionValue: GlossaryEnergy.TechnoResourceUsedDict[GlossaryEnergy.WaterGasShift],
                       GlossaryEnergy.ResourcesUsedForBuildingValue: GlossaryEnergy.TechnoBuildingResourceDict[GlossaryEnergy.WaterGasShift] if GlossaryEnergy.WaterGasShift in GlossaryEnergy.TechnoBuildingResourceDict else [],
                       GlossaryEnergy.EnergiesUsedForProductionValue: GlossaryEnergy.TechnoStreamsUsedDict[GlossaryEnergy.WaterGasShift],
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
                inputs_wgs.update({f"{key}:{column}": df[column].values})

        self.syngas_ratio_techno = WGS('WGS')
        self.syngas_ratio_techno.inputs = inputs_wgs
        self.syngas_ratio_techno.configure_parameters_update()
        self.syngas_ratio_techno.compute_price()
        self.syngas_ratio_techno_wgs = self.syngas_ratio_techno
        self.CO2_prod_wgs = self.syngas_ratio_techno_wgs.get_theoretical_co2_prod()

    def compute_byproducts_production(self):
        water_prod = 0.0
        if self.sg_transformation_name in ['WGS', 'WGS or RWGS']:
            co2_prod = self.CO2_prod_wgs * \
                       self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:syngas_needs_for_FT'] / \
                       self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

            self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:{GlossaryEnergy.CO2FromFlueGas} ({GlossaryEnergy.mass_unit})'] = co2_prod * \
                                                                                                                                       self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:'
                                                                                                f'{self.stream_name} ({self.product_unit})']

        elif self.sg_transformation_name == GlossaryEnergy.RWGS:
            self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:{GlossaryEnergy.CO2FromFlueGas} ({GlossaryEnergy.mass_unit})'] = 0.0

        if self.sg_transformation_name in [GlossaryEnergy.RWGS, 'WGS or RWGS']:

            water_prod = self.water_prod_RWGS * \
                         self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:syngas_needs_for_FT'] / \
                         self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

        water_prod += self.get_theoretical_water_prod_from_FT() / \
                      self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

        self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:{Water.name} ({GlossaryEnergy.mass_unit})'] = water_prod * \
                                                                                                                  self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:'
                                                                           f'{self.stream_name} ({self.product_unit})']



    def compute_energies_demand(self):
        # Compute elec demand from WGS
        elec_needs_wgs = self.syngas_ratio_techno.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.electricity}_needs'] * \
                         self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:syngas_needs_for_FT'] / \
                         self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

        # Consumption of WGS and FT
        self.outputs[f'{GlossaryEnergy.TechnoEnergyDemandsValue}:{GlossaryEnergy.electricity} ({self.product_unit})'] = \
            (self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.electricity}_needs'] + elec_needs_wgs) * \
            self.outputs[f'{GlossaryEnergy.TechnoTargetProduction}:{self.stream_name} ({self.product_unit})']  # in kWH

        # needs of syngas in kWh syngasin/kWhsyngas_out
        syngas_needs_wgs = self.syngas_ratio_techno.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:syngas_needs']

        # in kWhsyngas_in/kwhliquid_fuel and syngas_needs_for_FT is in
        # kWhsyngas_out/kWhliquid_fuel
        syngas_needs = syngas_needs_wgs * \
                       self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:syngas_needs_for_FT'] / \
                       self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

        # Compute of initial syngas vs output liquid_fuel
        self.outputs[f'{GlossaryEnergy.TechnoEnergyDemandsValue}:{GlossaryEnergy.syngas} ({self.product_unit})'] = syngas_needs * \
                                                                                                                       self.outputs[f'{GlossaryEnergy.TechnoTargetProduction}:'
                                                                                       f'{self.stream_name} ({self.product_unit})']  # in kWH

        # If WGS in the loop then we need water in the process
        if self.sg_transformation_name in ['WGS', 'WGS or RWGS']:
            water_needs = self.syngas_ratio_techno.outputs[f"{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.WaterResource}_needs"] * \
                          self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:syngas_needs_for_FT'] / \
                          self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

            self.outputs[f'{GlossaryEnergy.TechnoEnergyConsumptionValue}:{Water.name} ({GlossaryEnergy.mass_unit})'] = water_needs * \
                                                                                                                       self.outputs[f'{GlossaryEnergy.TechnoTargetProduction}:'
                                                                                f'{self.stream_name} ({self.product_unit})']

        elif self.sg_transformation_name == GlossaryEnergy.RWGS:
            self.outputs[f'{GlossaryEnergy.TechnoEnergyConsumptionValue}:{Water.name} ({GlossaryEnergy.mass_unit})'] = 0.0

        if self.sg_transformation_name == 'WGS':
            self.outputs[f'{GlossaryEnergy.TechnoEnergyConsumptionValue}:{GlossaryEnergy.carbon_captured} ({GlossaryEnergy.mass_unit})'] = 0.0

        elif self.sg_transformation_name in [GlossaryEnergy.RWGS, 'WGS or RWGS']:

            co2_needs = self.syngas_ratio_techno.outputs[f"{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.CO2Resource}_needs"] * \
                        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:syngas_needs_for_FT'] / \
                        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

            self.outputs[f'{GlossaryEnergy.TechnoEnergyConsumptionValue}:{GlossaryEnergy.carbon_captured} ({GlossaryEnergy.mass_unit})'] = co2_needs * \
                                                                                                                                           self.outputs[f'{GlossaryEnergy.TechnoTargetProduction}:'
                                                                                        f'{self.stream_name} ({self.product_unit})']


    def compute_scope_2_ghg_intensity(self):
        ''' 
        Need to take into account negative CO2 from biomass_dry and CO2 from electricity (can be 0.0 or positive)
        '''

        # Compute elec demand from WGS
        elec_needs_wgs = self.syngas_ratio_techno.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.electricity}_needs'] * \
                         self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:syngas_needs_for_FT'] / \
                         self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

        self.outputs[f'CO2_emissions_detailed:{GlossaryEnergy.electricity}'] = self.inputs[f'{GlossaryEnergy.StreamsCO2EmissionsValue}:{GlossaryEnergy.electricity}'] * \
                                                            (self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.electricity}_needs'] + elec_needs_wgs)

        # needs of syngas in kWh syngasin/kWhsyngas_out
        syngas_needs_wgs = self.syngas_ratio_techno.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:syngas_needs']

        # in kWhsyngas_in/kwhliquid_fuel and syngas_needs_for_FT is in
        # kWhsyngas_out/kWhliquid_fuel
        syngas_needs = syngas_needs_wgs * \
                       self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:syngas_needs_for_FT'] / \
                       self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

        self.outputs[f'CO2_emissions_detailed:{GlossaryEnergy.syngas}'] = self.inputs[f'{GlossaryEnergy.StreamsCO2EmissionsValue}:{GlossaryEnergy.syngas}'] * syngas_needs

        co2_needs = 0.0
        water_needs = 0.0
        if self.sg_transformation_name in ['WGS', 'WGS or RWGS']:
            water_needs += self.syngas_ratio_techno.outputs[f"{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.WaterResource}_needs"] * \
                           self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:syngas_needs_for_FT'] / \
                           self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

            co2_needs += -self.CO2_prod_wgs * \
                         self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:syngas_needs_for_FT'] / \
                         self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

        if self.sg_transformation_name in [GlossaryEnergy.RWGS, 'WGS or RWGS']:
            co2_needs += self.syngas_ratio_techno.outputs[f"{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.CO2Resource}_needs"] * \
                         self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:syngas_needs_for_FT'] / \
                         self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

        self.outputs[f'CO2_emissions_detailed:{CO2.name}'] = self.inputs[f'{GlossaryEnergy.RessourcesCO2EmissionsValue}:{GlossaryEnergy.CO2Resource}'] * co2_needs
        self.outputs[f'CO2_emissions_detailed:{Water.name}'] = self.inputs[f'{GlossaryEnergy.RessourcesCO2EmissionsValue}:{GlossaryEnergy.WaterResource}'] * water_needs

        self.outputs['CO2_emissions_detailed:Scope 2'] = self.outputs[f'CO2_emissions_detailed:{GlossaryEnergy.electricity}'] +\
                                                         self.outputs[f'CO2_emissions_detailed:{GlossaryEnergy.syngas}'] + \
                                                         self.outputs[f'CO2_emissions_detailed:{CO2.name}'] +\
                                                         self.outputs[f'CO2_emissions_detailed:{Water.name}']

    def get_theoretical_syngas_needs_for_FT(self):
        '''
        Get syngas needs in kWh syngas /kWh liquid_fuel
        H2 + n/(2n+1)CO --> 1/(2n+1) CnH_2n+1 + n/(2n+1)H20
        Warning : molar mass is in g/mol but we divide and multiply by one
        '''

        mol_syngas = 1.0
        mol_liquid_fuel = 1.0 / \
                          (2 * self.inputs['techno_infos_dict']['carbon_number'] + 1)
        syngas_molar_mass = compute_syngas_molar_mass(self.temp_variables['needed_syngas_ratio'])

        syngas_calorific_value = compute_syngas_calorific_value(
            self.temp_variables['needed_syngas_ratio'])
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
                     (mol_liquid_fuel * self.inputs['data_fuel_dict']['molar_mass'] *
                      self.inputs['data_fuel_dict']['calorific_value'])

        return water_prod
"""