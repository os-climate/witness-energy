'''
Copyright 2022 Airbus SAS
Modifications on 2023/10/03-2023/11/14 Copyright 2023 Capgemini

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
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
from energy_models.core.techno_type.base_techno_models.electricity_techno import ElectricityTechno


class Geothermal(ElectricityTechno):

    COPPER_RESOURCE_NAME = ResourceGlossary.Copper['name']

    def compute_other_primary_energy_costs(self):
        return 0



    def compute_consumption_and_installed_power(self):
        """
        Compute the resource consumption and the power installed (MW) of the technology for a given investment
        """
        

        # FOR ALL_RESOURCES DISCIPLINE
        copper_needs = self.get_theoretical_copper_needs(self)
        self.consumption_detailed[f'{self.COPPER_RESOURCE_NAME} ({self.mass_unit})'] = copper_needs * self.installed_power['new_power_production'] # in Mt

    @staticmethod
    def get_theoretical_copper_needs(self):
        """
        No data found, therefore we make the assumption that it needs at least a generator which uses the same amount of copper as a gaz powered station
        It needs 1100 kg / MW
        Computing the need in Mt/MW
        """
        copper_need = self.techno_infos_dict['copper_needs'] / 1000 / 1000 / 1000

        return copper_need

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        """
        
        self.consumption_detailed[f'{mediumtemperatureheat.name}({self.product_energy_unit})'] = ((1 - self.techno_infos_dict['efficiency']) * \
                                                                                                  self.production_detailed[f'{ElectricityTechno.energy_name} ({self.product_energy_unit})']) / \
                                                                                                 self.techno_infos_dict['efficiency']