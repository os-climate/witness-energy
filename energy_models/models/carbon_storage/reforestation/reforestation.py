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
import numpy as np

from energy_models.core.techno_type.base_techno_models.carbon_storage_techno import (
    CSTechno,
)


class Reforestation(CSTechno):

    def compute_land_use(self):
        ''' Set the compute land use dataframe

            to be overloaded in sub class
        '''

        self.land_use[f'{self.name} (Gha)'] = self.production_detailed[
                                                  f'{CSTechno.energy_name} ({self.product_unit})'] / \
                                              0.0067621 / 1.0e9

    def compute_dlanduse_dinvest(self):
        """
        compute grad d_land_use / d_invest
        """

        dlanduse_dinvest = np.identity(len(self.years)) * 0
        for key in self.land_use:
            if key.startswith(self.name):
                if not (self.land_use[key] == np.array([0] * len(self.years))).all():
                    dlanduse_dinvest = self.dprod_dinvest / self.data_energy_dict['calorific_value'] / \
                                       0.0067621 / 1.0e9

        return dlanduse_dinvest
