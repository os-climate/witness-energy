'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2023/11/16 Copyright 2023 Capgemini

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

from energy_models.core.stream_type.energy_models.clean_energy import CleanEnergy
from energy_models.core.techno_type.base_techno_models.carbon_capture_techno import (
    CCTechno,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.carbon_capture.flue_gas_capture.generic_flue_gas_techno_model import (
    GenericFlueGasTechnoModel,
)


class FlueGasTechno(GenericFlueGasTechnoModel):

    def get_electricity_needs(self):
        """
        Overloads techno type method to use electricity in coarse technologies for heat
        Get the electricity needs for 1 kwh of the energy producted by the technology
        """
        if self.inputs['techno_infos_dict']['elec_demand'] != 0.0:
            elec_need = self.check_energy_demand_unit(self.inputs['techno_infos_dict']['elec_demand_unit'],
                                                      self.inputs['techno_infos_dict']['elec_demand'])

        else:
            elec_need = 0.0

        if 'heat_demand' in self.inputs['techno_infos_dict']:
            heat_need = self.check_energy_demand_unit(self.inputs['techno_infos_dict']['heat_demand_unit'],
                                                      self.inputs['techno_infos_dict']['heat_demand'])

        else:
            heat_need = 0.0

        return elec_need + heat_need

    def compute_other_streams_needs(self):
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.clean_energy}_needs'] = self.get_electricity_needs() / self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency'] * self.compute_electricity_variation_from_fg_ratio(
            self.inputs[f'{GlossaryEnergy.FlueGasMean}:{GlossaryEnergy.FlueGasMean}'], self.inputs['fg_ratio_effect'])

    def compute_energies_demand(self):
        # Consumption
        self.outputs[f'{GlossaryEnergy.TechnoEnergyConsumptionValue}:{CleanEnergy.name} ({self.energy_unit})'] = self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.clean_energy}_needs'] * \
                                                                                                                 self.outputs[f'{GlossaryEnergy.TechnoDetailedProductionValue}:'
                                                                                  f'{CCTechno.stream_name} ({self.product_unit})'] / self.compute_electricity_variation_from_fg_ratio(
            self.inputs[f'{GlossaryEnergy.FlueGasMean}:{GlossaryEnergy.FlueGasMean}'], self.inputs['fg_ratio_effect'])
