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

import numpy as np
import pandas as pd


class DemandMix(object):
    '''
    Outputs the energy demand for each energy according to weights over overall energy demand
    V0 : energy_demand is a static input
    '''
    name = 'EnergyDemandMix'

    def __init__(self, name):
        '''
        Constructor
        '''
        #-- Inputs attributes set from configure method
        self.name = name
        self.year_start = 2020  # year start
        self.year_end = 2050  # year end
        self.energy_list = None
        # energy demand per energy per year (output)
        self.energy_demand_per_energy = {}

    def reload_df(self):
        '''
        Reload all dataframes with new year start and year end 
        '''
        self.years = np.arange(self.year_start, self.year_end + 1)
        base_df = pd.DataFrame({'years': self.years})
        # self.energy_consumption = base_df.copy() # consumption per energy per year
        # self.energy_production = base_df.copy() # production per energy per year
        # energy demand coefs per energy per year
        self.energy_demand_mix = base_df.copy(deep=True)
        self.total_energy_demand = base_df.copy(
            deep=True)  # overall energy demand per year
        for energy in self.energy_list:
            self.energy_demand_per_energy[energy] = base_df.copy(deep=True)

    def configure_parameters(self, inputs_dict):

        self.year_start = inputs_dict['year_start']
        self.year_end = inputs_dict['year_end']
        self.energy_list = inputs_dict['energy_list'] + inputs_dict['ccs_list']
        self.reload_df()

    def configure_parameters_update(self, inputs_dict):

        self.total_energy_demand['demand'] = inputs_dict['total_energy_demand']['demand']
        for energy in self.energy_list:
            #             self.energy_production[energy] = inputs_dict[f'{energy}.energy_production']
            #             self.energy_consumption[energy] = inputs_dict[f'{energy}.energy_consumption']
            self.energy_demand_mix[energy] = inputs_dict[f'{energy}.energy_demand_mix']['mix']

    def compute(self):
        '''
        Compute the energy demand per mix
        '''
        for energy in self.energy_list:
            demand = (
                self.energy_demand_mix[energy] / 100.) * self.total_energy_demand['demand']
            self.energy_demand_per_energy[energy]['demand'] = demand
