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

from energy_models.core.stream_type.energy_models.heat import mediumtemperatureheat
from energy_models.core.techno_type.base_techno_models.medium_heat_techno import (
    mediumheattechno,
)
from energy_models.glossaryenergy import GlossaryEnergy


class HeatPump(mediumheattechno):

    def __init__(self, name):
        super().__init__(name)
        self.land_rate = None
        self.heat_flux = None
        self.heat_flux_distribution = None

    def compute_other_streams_needs(self):
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.electricity}_needs'] = self.get_theoretical_electricity_needs() / self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

    def compute_byproducts_production(self):
        # Production
        self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:{mediumtemperatureheat.name} ({self.product_unit})'] = \
            self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:{mediumtemperatureheat.name} ({self.product_unit})'] / \
            self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

    def get_theoretical_electricity_needs(self):
        mean_temperature = self.inputs['techno_infos_dict']['mean_temperature']
        output_temperature = self.inputs['techno_infos_dict']['output_temperature']
        COP = output_temperature / (output_temperature - mean_temperature)
        electricity_needs = 1 / COP  # (heating_space*heat_required_per_meter_square) / COP

        return electricity_needs
