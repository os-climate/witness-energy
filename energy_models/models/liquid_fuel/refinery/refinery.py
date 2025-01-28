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
        self.outputs[f"{GlossaryEnergy.CostOfResourceUsageValue}:{GlossaryEnergy.Years}"] = self.years
        self.outputs[f"{GlossaryEnergy.CostOfResourceUsageValue}:Total"] = self.zeros_array
        for resource in self.inputs[GlossaryEnergy.ResourcesUsedForProductionValue]:
            if resource == GlossaryEnergy.OilResource:
                # Skip OilResource so not to count it twice
                self.outputs[f"{GlossaryEnergy.CostOfResourceUsageValue}:{resource}"] = 0.0
            else:
                self.outputs[f"{GlossaryEnergy.CostOfResourceUsageValue}:{resource}"] = self.outputs[f"{GlossaryEnergy.TechnoDetailedPricesValue}:{resource}_needs"].values * self.inputs[f"{GlossaryEnergy.ResourcesPriceValue}:{resource}"]
            self.outputs[f"{GlossaryEnergy.CostOfResourceUsageValue}:Total"] += self.outputs[f"{GlossaryEnergy.CostOfResourceUsageValue}:{resource}"]


    def get_fuel_needs(self):
        """
        Get the fuel needs for 1 kwh of the energy producted by the technology
        """
        if self.inputs['techno_infos_dict']['fuel_demand'] != 0.0:
            fuel_need = self.check_energy_demand_unit(self.inputs['techno_infos_dict']['fuel_demand_unit'],
                                                      self.inputs['techno_infos_dict']['fuel_demand'])

        else:
            fuel_need = 0.0

        return fuel_need

    def configure_energy_data(self):
        '''
        Configure energy data by reading the data_energy_dict in the right Energy class
        Overloaded for each energy type
        '''
        self.inputs['data_fuel_dict'] = self.inputs['data_fuel_dict']
        self.other_energy_dict = self.inputs['other_fuel_dict']

    def compute_resources_needs(self):
        # needs in [kWh/kWh] divided by calorific value in [kWh/kg] to have
        # needs in [kg/kWh]
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.OIL_RESOURCE_NAME}_needs'] = self.get_fuel_needs(
        ) / self.inputs['data_fuel_dict']['calorific_value'] / self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

    def compute_other_streams_needs(self):
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.electricity}_needs'] = self.get_electricity_needs() / self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GaseousHydrogen.name}_needs'] = self.inputs['techno_infos_dict']['hydrogen_demand'] / self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

    def compute_byproducts_production(self):
        for energy in self.other_energy_dict:
            # if it s a dict, so it is a data_energy_dict
            self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:{energy} ({self.product_unit})'] = self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:'
                                                                                     f'{self.stream_name} ({self.product_unit})'] * \
                                                                                 self.inputs['techno_infos_dict'][
                                                                                     'product_break_down'][
                                                                                     energy] / 11.66 * \
                                                                                 self.other_energy_dict[energy][
                                                                                     'calorific_value']

        self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:{CarbonCapture.flue_gas_name} ({GlossaryEnergy.mass_unit})'] = self.inputs['techno_infos_dict'][
                                                                                            'CO2_from_production'] / \
                                                                                        self.inputs['data_fuel_dict'][
                                                                                            'calorific_value'] * \
                                                                                        self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:'
                                                                                            f'{LiquidFuelTechno.stream_name} ({self.product_unit})']
        '''
        Method to compute CH4 emissions from gas production
        The proposed V0 only depends on production.
        Equation is taken from the GAINS model for crude oil
        https://previous.iiasa.ac.at/web/home/research/researchPrograms/air/IR54-GAINS-CH4.pdf
        CH4 emissions can be separated in three categories : flaring,venting and unintended leakage
        emission_factor is in Mt/TWh
        '''
        emission_factor = self.inputs['techno_infos_dict']['CH4_flaring_emission_factor'] + \
                          self.inputs['techno_infos_dict']['CH4_venting_emission_factor'] + \
                          self.inputs['techno_infos_dict']['CH4_unintended_leakage_emission_factor']

        self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:{Methane.emission_name} ({GlossaryEnergy.mass_unit})'] = emission_factor * \
                                                                                  self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:'
                                                                                      f'{LiquidFuelTechno.stream_name} ({self.product_unit})']

    def compute_new_installations_production_capacity(self):
        '''
        Compute the energy production of a techno from investment in TWh
        Add a delay for factory construction
        '''

        years_before_year_start = self.np.arange(self.year_start - self.inputs[GlossaryEnergy.ConstructionDelay], self.year_start)
        invest_before_year_start = self.inputs[f'{GlossaryEnergy.InvestmentBeforeYearStartValue}:{GlossaryEnergy.InvestValue}']
        capex_after_year_start = self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:Capex_{self.name}']
        capex_year_start = capex_after_year_start[0]
        capexes_before_year_start = self.np.array([capex_year_start] * len(years_before_year_start))

        invest_after_year_start = self.inputs[f'{GlossaryEnergy.InvestLevelValue}:{GlossaryEnergy.InvestValue}']
        invests_period_of_interest = self.np.concatenate([invest_before_year_start, invest_after_year_start])
        capex_period_of_interest = self.np.concatenate([capexes_before_year_start, capex_after_year_start])
        new_installations_production_capacity = invests_period_of_interest / (capex_period_of_interest + self.oil_extraction_capex)

        # keep only prod for years >= year_start and <= year_end
        new_installations_production_capacity = new_installations_production_capacity[:len(self.years)]

        self.outputs[f'{GlossaryEnergy.TechnoDetailedProductionValue}:new_installations_production_capacity'] = new_installations_production_capacity
