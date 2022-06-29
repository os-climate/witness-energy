'''
Copyright 2022 Airbus SAS

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

from energy_models.core.techno_type.base_techno_models.electricity_techno import ElectricityTechno
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary


class SolarPv(ElectricityTechno):

    COPPER_RESOURCE_NAME = ResourceGlossary.Copper['name']

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs which depends on the technology 
        """
        return 0

    def compute_land_use(self):
        '''
        Compute required land for solar_pv
        '''
        density_per_ha = self.techno_infos_dict['density_per_ha']

        self.techno_land_use[f'{self.name} (Gha)'] = \
            self.production[f'{self.energy_name} ({self.product_energy_unit})'] / \
            density_per_ha
    
    
    def compute_consumption_and_power_production(self):
        """
        Compute the resource consumption and the power installed (MW) of the technology for a given investment
        """
        self.compute_primary_power_production()

        # FOR ALL_RESOURCES DISCIPLINE

        copper_needs = self.get_theoretical_copper_needs(self)
        self.consumption[f'{self.COPPER_RESOURCE_NAME} ({self.mass_unit})'] = copper_needs * self.power_production['new_power_production'] # in Mt

    @staticmethod
    def get_theoretical_copper_needs(self):
        """
        According to the IEA, Solar PV panels need 2822 kg of copper for each MW implemented
        Computing the need in Mt/MW
        """
        copper_need = self.techno_infos_dict['copper_needs'] / 1000 / 1000 / 1000

        return copper_need
