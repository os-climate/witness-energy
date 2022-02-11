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

from .base_invest import BaseInvest
import pandas as pd
import numpy as np
from sos_trades_core.tools.base_functions.exp_min import compute_func_with_exp_min
from sos_trades_core.tools.cst_manager.func_manager_common import smooth_maximum


class IndependentInvest(BaseInvest):
    '''
        Model to Distribute Absolute invest from design space to technologies
        Need to compute a constraint on investment sum 
    '''

    def __init__(self, name='Invest'):
        '''
        Constructor
        '''
        BaseInvest.__init__(self, name)
        #-- default value, can be changed if necessary

        self.invest_mix = None
        self.scaling_factor_energy_investment = 1e2

    def compute_invest_objective(self, inputs_dict):
        '''
        The objective formulation is the minimization of the absolute relative difference of 
        available invest compared to the sum of techno invest.
        The objective is scaled by a reference value.
        '''

        energy_investment = inputs_dict['energy_investment']
        self.scaling_factor_energy_investment = inputs_dict['scaling_factor_energy_investment']
        invest_objective_ref = inputs_dict['invest_objective_ref']
        energy_invest_df = pd.DataFrame({'years': energy_investment['years'].values,
                                         'energy_investment': energy_investment['energy_investment'].values * self.scaling_factor_energy_investment})

        self.compute_distribution_list(inputs_dict)

        techno_invests = inputs_dict['invest_mix'][self.distribution_list]

        techno_invest_sum = techno_invests.sum(axis=1).values

        # Calculate relative diff
        delta = (energy_invest_df['energy_investment'].values -
                 techno_invest_sum) / energy_invest_df['energy_investment'].values

        # Get the L1 norm of the delta and apply a scaling to compute the
        # objective
        abs_delta = np.sqrt(compute_func_with_exp_min(delta**2, 1e-15))
        smooth_delta = np.asarray([smooth_maximum(abs_delta, alpha=10)])
        invest_objective = smooth_delta / invest_objective_ref
        return invest_objective
