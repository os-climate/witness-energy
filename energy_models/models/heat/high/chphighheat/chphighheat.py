'''
Copyright 2023 Capgemini

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


from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.techno_type.base_techno_models.electricity_techno import (
    ElectricityTechno,
)
from energy_models.core.techno_type.base_techno_models.heat_techno import heattechno
from energy_models.core.techno_type.base_techno_models.high_heat_techno import (
    highheattechno,
)
from energy_models.glossaryenergy import GlossaryEnergy


class CHPHighHeat(highheattechno):
    def compute(self):
        super(heattechno, self).compute()
    def compute_energies_needs(self):
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{Methane.name}_needs'] = self.get_theoretical_methane_needs()

    def compute_byproducts_production(self):
        # CO2 production
        # TODO
        self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:{GlossaryEnergy.CO2FromFlueGas} ({GlossaryEnergy.mass_unit})'] = \
            Methane.data_energy_dict[GlossaryEnergy.CO2PerUse] / \
            Methane.data_energy_dict['calorific_value'] * \
            self.outputs[f'{GlossaryEnergy.TechnoEnergyDemandsValue}:{Methane.name} ({GlossaryEnergy.energy_unit})']

        self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:{ElectricityTechno.stream_name} ({GlossaryEnergy.energy_unit})'] = \
            (self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:{self.stream_name}'] /
             (1 - self.inputs['techno_infos_dict']['efficiency'])) - self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:{self.stream_name}']

    def get_theoretical_methane_needs(self):
        # we need as output kwh/kwh
        methane_demand = self.inputs['techno_infos_dict']['methane_demand']

        methane_needs = methane_demand

        return methane_needs

    def get_theoretical_electricity_needs(self):
        # we need as output kwh/kwh
        elec_demand = self.inputs['techno_infos_dict']['elec_demand']

        return elec_demand

    def compute_co2_from_flue_gas_intensity_scope_1(self, unit='kg/kWh'):
        co2_captured__production = self.inputs['techno_infos_dict']['co2_captured__production']
        heat_density = Methane.data_energy_dict['density']  # kg/m^3
        heat_calorific_value = Methane.data_energy_dict['calorific_value']  # kWh/kg

        co2_prod = co2_captured__production / (heat_density * heat_calorific_value)

        return co2_prod
