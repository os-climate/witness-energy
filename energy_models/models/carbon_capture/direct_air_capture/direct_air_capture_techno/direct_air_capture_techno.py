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


from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.energy_models.fossil import Fossil
from energy_models.core.techno_type.base_techno_models.carbon_capture_techno import (
    CCTechno,
)
from energy_models.glossaryenergy import GlossaryEnergy


class DirectAirCaptureTechno(CCTechno):

    def get_heat_needs(self):
        """
        Get the heat needs for 1 kwh of the energy producted by the technology
        """

        if 'heat_demand' in self.inputs['techno_infos_dict']:
            heat_need = self.check_energy_demand_unit(self.inputs['techno_infos_dict']['heat_demand_unit'],
                                                      self.inputs['techno_infos_dict']['heat_demand'])

        else:
            heat_need = 0.0

        return heat_need

    def compute_other_streams_needs(self):
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.clean_energy}_needs'] = self.get_electricity_needs()
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{Fossil.name}_needs'] = self.get_heat_needs()

    def compute_byproducts_production(self):

        self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:{CarbonCapture.flue_gas_name} ({GlossaryEnergy.mass_unit})'] = \
            self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{Fossil.name}_needs'] * self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:{CCTechno.energy_name} ({self.product_unit})'] * \
            Fossil.data_energy_dict[GlossaryEnergy.CO2PerUse] / Fossil.data_energy_dict[
                                                                                            'calorific_value']