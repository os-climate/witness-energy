'''
Copyright 2022 Airbus SAS
Modifications on 2023/04/21-2024/06/24 Copyright 2023 Capgemini

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

from energy_models.glossaryenergy import GlossaryEnergy

from .base_invest import BaseInvest


class IndependentInvest(BaseInvest):
    '''
        Model to Distribute Absolute invest from design space to technologies
    '''

    def __init__(self, name='Invest'):
        '''
        Constructor
        '''
        BaseInvest.__init__(self, name)
        # -- default value, can be changed if necessary

        self.invest_mix = None

    def compute(self, inputs_dict):
        """compute"""
        energy_investment_wo_tax = self.compute_energy_investment_wo_tax(inputs_dict)
        energy_invest_objective = self.compute_energy_invest_objective(energy_investment_wo_tax)
        max_budget_constraint = self.compute_max_budget_constraint(energy_investment_wo_tax, inputs_dict)
        return energy_investment_wo_tax, energy_invest_objective, max_budget_constraint

    def compute_energy_invest_objective(self, energy_investment_wo_tax):
        energy_invest_objective = energy_investment_wo_tax[GlossaryEnergy.EnergyInvestmentsWoTaxValue].values.sum()
        return np.array([energy_invest_objective])

    def compute_energy_investment_wo_tax(self, inputs_dict: dict):
        """computes investments in the energy sector (without tax)"""
        self.compute_distribution_list(inputs_dict)

        techno_invests = inputs_dict[GlossaryEnergy.invest_mix][self.distribution_list]
        techno_invest_sum = techno_invests.sum(axis=1).values

        energy_investment_wo_tax = pd.DataFrame(
            {GlossaryEnergy.Years: inputs_dict[GlossaryEnergy.invest_mix][GlossaryEnergy.Years],
             GlossaryEnergy.EnergyInvestmentsWoTaxValue: techno_invest_sum / 1e3})  # T$

        return energy_investment_wo_tax

    def compute_max_budget_constraint(self, energy_investment_wo_tax: np.ndarray, inputs_dict: dict):
        """should be negative"""
        max_budget_constraint_ref = inputs_dict[GlossaryEnergy.MaxBudgetConstraintRefValue]
        max_budget = inputs_dict[GlossaryEnergy.MaxBudgetValue][GlossaryEnergy.MaxBudgetValue].values
        overspending = energy_investment_wo_tax[GlossaryEnergy.EnergyInvestmentsWoTaxValue].values * 1000 - max_budget
        max_budget_constraint_df = pd.DataFrame({
            GlossaryEnergy.Years: inputs_dict[GlossaryEnergy.invest_mix][GlossaryEnergy.Years],
            GlossaryEnergy.MaxBudgetConstraintValue: overspending / max_budget_constraint_ref
        })
        return max_budget_constraint_df
