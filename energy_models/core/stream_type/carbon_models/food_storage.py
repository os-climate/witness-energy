'''
Copyright 2022 Airbus SAS
Modifications on 2023/10/23-2023/11/16 Copyright 2023 Capgemini

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
import pandas as pd

from energy_models.core.stream_type.base_stream import BaseStream
from energy_models.core.stream_type.carbon_models.carbon_utilization import CarbonUtilization
from energy_models.glossaryenergy import GlossaryEnergy


class FoodStorage(BaseStream):
    name = CarbonUtilization.food_storage_name
    node_name = 'food_storage_applications'
    unit = 'Mt'

    def __init__(self, name):
        BaseStream.__init__(self, name)
        self.food_storage_ratio_dict = {}
        self.food_storage_ratio_mean = pd.DataFrame()

    def configure_parameters(self, inputs_dict):
        BaseStream.configure_parameters(self, inputs_dict)
        self.subelements_list = inputs_dict[GlossaryEnergy.techno_list]

    def configure_parameters_update(self, inputs_dict):
        for techno in self.subelements_list:
            self.sub_production_dict[techno] = inputs_dict[f'{techno}.{GlossaryEnergy.TechnoProductionValue}'] * \
                inputs_dict['scaling_factor_techno_production']
            self.food_storage_ratio_dict[techno] = inputs_dict[f'{techno}.food_storage_co2_ratio'][0]

    def compute_production(self):
        '''
        Compute energy production by summing all energy productions
        And compute the techno_mix_weights each year
        '''

        # print('')
        # print(self.sub_production_dict)

        self.production[f'{self.name}'] = 0.
        for element in self.subelements_list:
            self.production[f'{self.name} {element} ({self.unit})'] = self.sub_production_dict[
                element][f'{self.name} ({self.unit})']
            self.production[
                f'{self.name}'] += self.production[f'{self.name} {element} ({self.unit})']

    def compute(self, inputs, exp_min=True):
        '''
        Compute function which compute food storage production and food storage mean ratio
        '''
        self.compute_production()
        self.compute_food_storage_ratio()

        return self.food_storage_ratio_mean

    def get_total_food_storage_production(self):
        '''
        Return a df with total food storage production and years
        '''
        return self.production[[GlossaryEnergy.Years, self.name]]

    def get_total_food_storage_prod_ratio(self):
        '''
        Return mix weights which is food storage production ratio
        '''
        return self.mix_weights

    def compute_food_storage_ratio(self):
        """
        Method to compute food storage ratio using production by
        """
        self.food_storage_ratio_mean = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.FoodStorageMean: 0.0})

        for techno in self.subelements_list:
            self.mix_weights[techno] = self.production[f'{self.name} {techno} (Mt)'] / \
                self.production[f'{self.name}']
            self.food_storage_ratio_mean[GlossaryEnergy.FoodStorageMean] += self.food_storage_ratio_dict[techno] *  \
                self.mix_weights[techno].values
