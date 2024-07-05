'''
Copyright 2024 Capgemini

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

from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.techno_type.base_techno_models.carbon_capture_techno import (
    CCTechno,
)
from energy_models.glossaryenergy import GlossaryEnergy


class GenericFlueGasTechnoModel(CCTechno):
    def __init__(self, name):
        super().__init__(name)
        self.flue_gas_ratio = None
        self.fg_ratio_effect = None

    def configure_parameters_update(self, inputs_dict):

        CCTechno.configure_parameters_update(self, inputs_dict)
        self.flue_gas_ratio = inputs_dict[GlossaryEnergy.FlueGasMean].loc[
            inputs_dict[GlossaryEnergy.FlueGasMean][GlossaryEnergy.Years]
            <= self.year_end]
        # To deal quickly with l0 test
        if 'fg_ratio_effect' in inputs_dict:
            self.fg_ratio_effect = inputs_dict['fg_ratio_effect']
        else:
            self.fg_ratio_effect = True

    def compute_other_energies_needs(self):
        self.cost_details[f'{GlossaryEnergy.electricity}_needs'] = self.get_electricity_needs() / self.cost_details['efficiency'] * self.compute_electricity_variation_from_fg_ratio(self.flue_gas_ratio[GlossaryEnergy.FlueGasMean].values, self.fg_ratio_effect)

    def compute_capex(self, invest_list, data_config):
        capex_calc_list = super().compute_capex(invest_list, data_config)
        capex_calc_list *= self.compute_capex_variation_from_fg_ratio(
            self.flue_gas_ratio[GlossaryEnergy.FlueGasMean].values, self.fg_ratio_effect)

        return capex_calc_list

    def compute_energies_consumption(self):
        # Consumption
        self.consumption_detailed[f'{Electricity.name} ({self.energy_unit})'] = self.cost_details[f'{GlossaryEnergy.electricity}_needs'] * \
                                                                                self.production_detailed[f'{CCTechno.energy_name} ({self.product_unit})'] / self.compute_electricity_variation_from_fg_ratio(
            self.flue_gas_ratio[GlossaryEnergy.FlueGasMean].values, self.fg_ratio_effect)

