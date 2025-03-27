'''
Copyright 2022 Airbus SAS
Modifications on 2023/09/25-2023/11/16 Copyright 2023 Capgemini

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
from energy_models.core.stream_type.carbon_models.nitrous_oxide import N2O
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.techno_type.base_techno_models.electricity_techno import (
    ElectricityTechno,
)
from energy_models.glossaryenergy import GlossaryEnergy


class CCGasT(ElectricityTechno):
    COPPER_RESOURCE_NAME = GlossaryEnergy.CopperResource
    def compute_energies_needs(self):
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{Methane.name}_needs'] = self.inputs['techno_infos_dict'][f'{Methane.name}_needs']

    def compute_co2_from_flue_gas_intensity_scope_1(self) -> float:
        '''
        Get co2 producted in kg co2 /kWh
        '''
        methane_data = Methane.data_energy_dict
        # kg of C02 per kg of methane burnt
        methane_co2 = methane_data[GlossaryEnergy.CO2PerUse]
        # Amount of methane in kwh for 1 kwh of elec
        methane_need = self.inputs['techno_infos_dict'][f'{Methane.name}_needs']
        calorific_value = methane_data['calorific_value']  # kWh/kg

        co2_prod = methane_co2 / calorific_value * methane_need
        return co2_prod

    def compute_byproducts_production(self):
        self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:{GlossaryEnergy.hightemperatureheat_energyname} ({self.product_unit})'] = \
            self.outputs[f'{GlossaryEnergy.TechnoEnergyDemandsValue}:{Methane.name} ({self.product_unit})'] - \
            self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:{self.stream_name} ({self.product_unit})']

        # TODO
        self.compute_ghg_emissions(N2O.name, related_to=Methane.name)
