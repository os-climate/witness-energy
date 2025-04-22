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
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{self.COAL_RESOURCE_NAME}_needs'] = self.np.ones(len(
            self.years)) / (SolidFuel.data_energy_dict['calorific_value'] * 1000.0)  # kg/kWh

    def compute_energies_needs(self):
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.electricity}_needs'] = self.get_electricity_needs() / self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

    def compute_co2_from_flue_gas_intensity_scope_1(self) -> float:
        return self.inputs['techno_infos_dict']['CO2_flue_gas_intensity_by_prod_unit'] / self.inputs['data_fuel_dict']['high_calorific_value']

    def compute(self):
        super(CoalExtraction, self).compute()
        self.specific_compute()
    def specific_compute(self):
        """Adding emissions from abandoned mines to CH4 emissions"""
        self.outputs[f'{GlossaryEnergy.TechnoScope1GHGEmissionsValue}:{GlossaryEnergy.CH4}'] = \
            self.outputs[f'{GlossaryEnergy.TechnoScope1GHGEmissionsValue}:{GlossaryEnergy.CH4}'] + self.inputs['techno_infos_dict']['ch4_from_abandoned_mines']
