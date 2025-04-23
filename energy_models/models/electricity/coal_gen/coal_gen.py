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

from energy_models.core.stream_type.energy_models.solid_fuel import SolidFuel
from energy_models.core.techno_type.base_techno_models.electricity_techno import (
    ElectricityTechno,
)
from energy_models.glossaryenergy import GlossaryEnergy


class CoalGen(ElectricityTechno):
    def compute_resources_needs(self):
        # need in kg/kWh
        self.outputs[f"{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.WaterResource}_needs"] = self.inputs['techno_infos_dict']['water_demand']

    def compute_energies_needs(self):
        # in kwh of fuel by kwh of electricity
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{SolidFuel.name}_needs'] = \
            self.inputs['techno_infos_dict']['fuel_demand'] / \
            self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

    def compute_co2_from_flue_gas_intensity_scope_1(self):
        return self.inputs['techno_infos_dict']['CO2_flue_gas_intensity_by_prod_unit']

    def compute_byproducts_production(self):
        elec_needs = self.get_electricity_needs()
        self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:{self.stream_name}'] = \
            self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:'
                f'{self.stream_name}'] * (1.0 - elec_needs)

        self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:{GlossaryEnergy.hightemperatureheat_energyname}'] = \
            self.outputs[f'{GlossaryEnergy.TechnoEnergyDemandsValue}:{SolidFuel.name}'] - \
            self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:{self.stream_name}']
