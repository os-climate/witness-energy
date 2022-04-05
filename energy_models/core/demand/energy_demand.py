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

from energy_models.core.energy_mix.energy_mix import EnergyMix


class EnergyDemand(object):
    '''
    Compute a constraint to respect energy demand for consumption/transport ....
    In the V0, only elec demand constraint is implemented
    '''
    name = 'Energy_demand'
    elec_prod_column = f"production electricity ({EnergyMix.stream_class_dict['electricity'].unit})"

    def __init__(self, name):
        '''
        Constructor
        '''
        #-- Inputs attributes set from configure method
        self.name = name
        self.year_start = 2020  # year start
        self.year_end = 2100  # year end
        self.demand_efficiency = 0.0
        self.initial_electricity_demand = 0.0
        self.energy_production_detailed = None
        self.demand_elec_constraint = None
        self.elec_demand = None

    def configure_parameters(self, inputs_dict):
        '''
        COnfigure paramters at the init execution (Does not change during the execution)
        '''
        self.year_start = inputs_dict['year_start']
        self.year_end = inputs_dict['year_end']
        self.delta_years = self.year_end + 1 - self.year_start
        self.demand_efficiency = inputs_dict['demand_efficiency']
        self.initial_electricity_demand = inputs_dict['initial_electricity_demand']
        self.electricity_demand_constraint_ref = inputs_dict['electricity_demand_constraint_ref']
        self.demand_elec_constraint = pd.DataFrame(
            {'years': np.arange(inputs_dict['year_start'], inputs_dict['year_end'] + 1)})
        self.elec_demand = pd.DataFrame(
            {'years': np.arange(inputs_dict['year_start'], inputs_dict['year_end'] + 1)})

    def configure_parameters_update(self, inputs_dict):
        '''
        Update parameters at each execution
        '''
        self.energy_production_detailed = inputs_dict['energy_production_detailed']

    def compute(self):
        '''
        Compute the energy demand per mix
        '''

        self.compute_elec_demand_constraint()

    def compute_elec_demand_constraint(self):
        '''
        The constraint is the difference between the prod of electricity computed by the energy mix and the actual demand computed in this model 
        '''
        self.elec_demand['elec_demand (TWh)'] = self.compute_elec_demand_with_efficiency(
        )
        self.demand_elec_constraint['elec_demand_constraint'] = (
            self.energy_production_detailed[self.elec_prod_column].values - self.elec_demand['elec_demand (TWh)'].values) / self.electricity_demand_constraint_ref / self.delta_years

    def compute_elec_demand_with_efficiency(self):
        '''
        The demand is decreasing with years due to techno efficiency 
        '''
        electricity_demand = np.array(
            [self.initial_electricity_demand * self.demand_efficiency**i for i in range(self.delta_years)])
        return electricity_demand

    def get_elec_demand_constraint(self):
        '''
        Getter for elec_demand_constraint
        '''
        return self.demand_elec_constraint

    def get_elec_demand(self):
        '''
        Getter for elec_demand_constraint
        '''
        return self.elec_demand

    def compute_delec_demand_constraint_delec_prod(self):
        '''
        Compute the gradient of elec_demand_contraint vs electricity net production
        '''

        return np.identity(self.delta_years) / self.electricity_demand_constraint_ref / self.delta_years
