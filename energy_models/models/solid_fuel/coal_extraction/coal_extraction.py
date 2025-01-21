'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/09-2023/11/15 Copyright 2023 Capgemini

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

import autograd.numpy as np

from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.energy_models.solid_fuel import SolidFuel
from energy_models.core.techno_type.base_techno_models.solid_fuel_techno import (
    SolidFuelTechno,
)
from energy_models.glossaryenergy import GlossaryEnergy


class CoalExtraction(SolidFuelTechno):
    COAL_RESOURCE_NAME = GlossaryEnergy.CoalResource

    def __init__(self, name):
        super().__init__(name)
        self.emission_factor_mt_twh = None

    def compute_resources_needs(self):
        # calorific value in kWh/kg * 1000 to have needs in t/kWh
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.COAL_RESOURCE_NAME}_needs'] = np.ones(len(
            self.years)) / (SolidFuel.data_energy_dict['calorific_value'] * 1000.0)  # kg/kWh

    def compute_other_streams_needs(self):
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.electricity}_needs'] = self.get_electricity_needs() / self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

    def compute_byproducts_production(self):
        self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit})'] = self.inputs['techno_infos_dict']['CO2_from_production'] / \
                                                                     self.inputs['data_fuel_dict']['high_calorific_value'] * \
                                                                     self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:'
                                                                         f'{SolidFuelTechno.energy_name} ({self.product_unit})']
        '''
        Method to compute CH4 emissions from coal mines
        The proposed V0 only depends on production. The V1 could depend on mining depth (deeper and deeper along the years)
        Equation is taken from the GAINS model
        https://gem.wiki/Estimating_methane_emissions_from_coal_mines#Model_for_Calculating_Coal_Mine_Methane_.28MC2M.29,
        Nazar Kholod &al Global methane emissions from coal mining to continue growing even with declining coal production,
         Journal of Cleaner Production, Volume 256, February 2020.
        '''
        emission_factor_coeff = self.inputs['techno_infos_dict']['emission_factor_coefficient']

        # compute gas content with surface and underground_gas_content in m3/t
        underground_mining_gas_content = self.inputs['techno_infos_dict']['underground_mining_gas_content']
        surface_mining_gas_content = self.inputs['techno_infos_dict']['surface_mining_gas_content']
        gas_content = self.inputs['techno_infos_dict']['underground_mining_percentage'] / \
                      100.0 * underground_mining_gas_content + \
                      (1. - self.inputs['techno_infos_dict']['underground_mining_percentage'] /
                       100.0) * surface_mining_gas_content

        # gascontent must be passed in Mt/Twh
        self.emission_factor_mt_twh = gas_content * emission_factor_coeff * Methane.data_energy_dict['density'] / \
                                      self.inputs['data_fuel_dict']['calorific_value'] * 1e-3
        # need to multiply by 1e9 to be in m3 by density to be in kg and by 1e-9 to be in Mt
        # and add ch4 from abandoned mines
        self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:{Methane.emission_name} ({GlossaryEnergy.mass_unit})'] = self.emission_factor_mt_twh * \
                                                                                  self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:'
                                                                                      f'{SolidFuelTechno.energy_name} ({self.product_unit})'] + \
                                                                                  self.inputs['techno_infos_dict'][
                                                                                      'ch4_from_abandoned_mines']
