'''
Copyright 2022 Airbus SAS
Modifications on 2023/10/10-2023/11/16 Copyright 2023 Capgemini

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
from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
from energy_models.core.techno_type.base_techno_models.solid_fuel_techno import (
    SolidFuelTechno,
)
from energy_models.glossaryenergy import GlossaryEnergy


class Pelletizing(SolidFuelTechno):
    def compute_other_energies_needs(self):
        # in kg of fuel by kg of pellets depends on moisture level
        self.cost_details[f'{BiomassDry.name}_needs'] = (1 + self.data_energy_dict['biomass_dry_moisture']) / \
                                                 (1 + self.data_energy_dict['pellets_moisture'])

        # electricity needed for conditioning, storage + production of 1kg of pellets
        # plus electricity needed for chipping dry biomass
        self.cost_details[f'{GlossaryEnergy.electricity}_needs'] = self.get_electricity_needs()
        # Cost of electricity for 1 kWh of pellet

    def compute_production(self):
        self.production_detailed[f'{CarbonCapture.flue_gas_name} ({GlossaryEnergy.mass_unit})'] = self.techno_infos_dict[
                                                                                            'CO2_from_production'] * \
                                                                                        self.production_detailed[
                                                                                            f'{SolidFuelTechno.energy_name} ({self.product_unit})'] / \
                                                                                        self.data_energy_dict[
                                                                                            'calorific_value']
