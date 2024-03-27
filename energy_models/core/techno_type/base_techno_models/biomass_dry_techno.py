'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/09-2023/11/14 Copyright 2023 Capgemini

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
from abc import abstractmethod

from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
from energy_models.core.techno_type.techno_type import TechnoType


class BiomassDryTechno(TechnoType):
    energy_name = BiomassDry.name

    def __init__(self, name):
        TechnoType.__init__(self, name)

    def compute_land_use(self):
        density_per_ha = self.techno_infos_dict['density_per_ha']
        if self.techno_infos_dict['density_per_ha_unit'] == 'm^3/ha':
            density_per_ha = density_per_ha * self.techno_infos_dict['density']

        self.land_use[f'{self.name} (Gha)'] = \
            self.production_detailed[f'{self.energy_name} ({self.product_energy_unit})'] / \
            self.data_energy_dict['calorific_value'] / \
            density_per_ha

        # if the techno has a percentage for production
        if 'years_between_harvest' in self.techno_infos_dict:
            self.land_use[f'{self.name} (Gha)'] *= self.techno_infos_dict['years_between_harvest']

        if 'recyle_part' in self.techno_infos_dict:
            self.land_use[f'{self.name} (Gha)'] *= (
                    1 - self.techno_infos_dict['recyle_part'])

    @abstractmethod
    def get_theoretical_co2_prod(self, unit='kg/kWh'):
        ''' 
        Get the theoretical CO2 production for a given technology,
        Need to be overloaded in each technology model (example in SMR)
        '''
        return 0.0
