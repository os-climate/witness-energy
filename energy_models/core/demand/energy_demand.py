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
from sos_trades_core.tools.base_functions.s_curve import s_curve


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
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.long_term_elec_machine_efficiency = 0.985
        self.initial_electricity_demand = 0.0
        self.energy_production_detailed = None
        self.demand_elec_constraint = None
        self.elec_demand = None
        self.eff_coeff = 0.4
        self.eff_x0 = 2015
        self.eff_y_min = 0.7

    def configure_parameters(self, inputs_dict):
        '''
        COnfigure paramters at the init execution (Does not change during the execution)
        '''
        self.year_start = inputs_dict['year_start']
        self.year_end = inputs_dict['year_end']
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.delta_years = self.year_end + 1 - self.year_start
        self.long_term_elec_machine_efficiency = inputs_dict['long_term_elec_machine_efficiency']
        self.initial_electricity_demand = inputs_dict['initial_electricity_demand']
        self.electricity_demand_constraint_ref = inputs_dict['electricity_demand_constraint_ref']
        self.demand_elec_constraint = pd.DataFrame(
            {'years': self.years})
        self.elec_demand = pd.DataFrame(
            {'years': self.years})

    def configure_parameters_update(self, inputs_dict):
        '''
        Update parameters at each execution
        '''
        self.energy_production_detailed = inputs_dict['energy_production_detailed']
        self.population_df = inputs_dict['population_df']

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
        The demand is decreasing due to increase of techno efficiency (division)
        and increasing due to increase of population (multiply)
        '''
        init_pop = self.population_df['population'].values[0]
        self.improved_efficiency_factor = self.compute_improved_efficiency_factor()
        pop_factor = self.population_df['population'].values / init_pop

        electricity_demand = self.initial_electricity_demand * \
            pop_factor / self.improved_efficiency_factor

        return electricity_demand

    def compute_improved_efficiency_factor(self):
        '''
        Compute the effect of efficiency improvement based on a S-curve 
        Electrical machine efficiency started at y_min =0.7
        and long term efficiency is planned to be 0.985
        coeff and x0 have been tuned to fit y[2020]=0.95 and y[2025]=0.98 
        '''

        elec_machine_efficiency = self.electrical_machine_efficiency(
            self.years)

        return elec_machine_efficiency / elec_machine_efficiency[0]

    def electrical_machine_efficiency(self, years):

        return s_curve(
            years, coeff=self.eff_coeff, x0=self.eff_x0, y_min=self.eff_y_min, y_max=self.long_term_elec_machine_efficiency)

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

    def compute_delec_demand_constraint_dpop(self):
        '''
        Compute the gradient of elec_demand_contraint vs population
        delec_demand_constraint/dpop = -delecdemand/dpop/ref/dt

        delec_demand/dpop = initial_demand/improved_eff_factor * grad

        grad[0,0] = 0
        grad[i,0] = -pop[i]/pop[0]**2

        elsewhere grad = 1/pop[0]
        '''
        pop0 = self.population_df['population'].values[0]
        grad = np.identity(self.delta_years) / pop0

        grad[:, 0] = -self.population_df['population'].values / pop0**2
        grad[0, 0] = 0.0

        return -grad * self.initial_electricity_demand / self.improved_efficiency_factor.reshape(self.delta_years, 1) / self.electricity_demand_constraint_ref / self.delta_years
