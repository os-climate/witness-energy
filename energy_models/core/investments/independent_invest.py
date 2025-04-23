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

        self.inputs = {}
        self.years = None
        self.outputs = {}

    def compute(self, inputs_dict):

        """compute"""
        self.inputs = inputs_dict
        self.years = np.arange(self.inputs[GlossaryEnergy.YearStart], self.inputs[GlossaryEnergy.YearEnd] + 1)

        self.compute_technos_invest()
        self.compute_total_energy_invests()
        self.compute_total_ccus_invests()
        self.compute_max_budget_constraint()


    def compute_technos_invest(self):
        conversion_factor_2 = GlossaryEnergy.conversion_dict[GlossaryEnergy.invest_mix_df['unit']][
            GlossaryEnergy.TechnoInvestDf['unit']]
        for energy in self.inputs[GlossaryEnergy.energy_list] + self.inputs[GlossaryEnergy.ccs_list]:
            for techno in self.inputs[f'{energy}.{GlossaryEnergy.techno_list}']:
                self.outputs[f'{energy}.{techno}.{GlossaryEnergy.InvestLevelValue}'] = pd.DataFrame({
                    GlossaryEnergy.Years: self.years,
                    GlossaryEnergy.InvestValue: self.inputs[GlossaryEnergy.invest_mix][
                                                    f'{energy}.{techno}'].values * conversion_factor_2
                })

    def compute_total_energy_invests(self):
        conversion_factor = GlossaryEnergy.conversion_dict[GlossaryEnergy.invest_mix_df['unit']][GlossaryEnergy.InvestmentDf['unit']]
        energy_technos = []
        for energy in self.inputs[GlossaryEnergy.energy_list]:
            energy_technos.extend(
                [f"{energy}.{techno}" for techno in self.inputs[f'{energy}.{GlossaryEnergy.techno_list}']])

        self.outputs[f"{GlossaryEnergy.EnergyMix}.{GlossaryEnergy.InvestmentsValue}"] = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.InvestmentsValue: self.inputs[GlossaryEnergy.invest_mix][energy_technos].sum(
                axis=1) * conversion_factor,
        })

    def compute_total_ccus_invests(self):
        ccs_technos = []
        for css_stream in self.inputs[GlossaryEnergy.ccs_list]:
            ccs_technos.extend(
                [f"{css_stream}.{techno}" for techno in self.inputs[f'{css_stream}.{GlossaryEnergy.techno_list}']])

        conversion_factor = GlossaryEnergy.conversion_dict[GlossaryEnergy.invest_mix_df['unit']][GlossaryEnergy.InvestmentDf['unit']]

        self.outputs[f"{GlossaryEnergy.CCUS}.{GlossaryEnergy.InvestmentsValue}"] = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.InvestmentsValue: self.inputs[GlossaryEnergy.invest_mix][ccs_technos].sum(
                axis=1) * conversion_factor,
        })

    def compute_max_budget_constraint(self):
        """Compute the constraint for maximal invests"""
        conversion_factor = GlossaryEnergy.conversion_dict[GlossaryEnergy.MaxBudgetConstraintRef['unit']][GlossaryEnergy.InvestmentDf['unit']]
        conversion_factor_2 = GlossaryEnergy.conversion_dict[GlossaryEnergy.MaxBudgetDf['unit']][GlossaryEnergy.InvestmentDf['unit']]


        max_budget_constraint_ref = self.inputs[GlossaryEnergy.MaxBudgetConstraintRefValue] * conversion_factor
        max_budget = self.inputs[GlossaryEnergy.MaxBudgetValue][GlossaryEnergy.MaxBudgetValue].values

        overspending = self.outputs[f"{GlossaryEnergy.EnergyMix}.{GlossaryEnergy.InvestmentsValue}"][GlossaryEnergy.InvestmentsValue] \
                       + self.outputs[f"{GlossaryEnergy.CCUS}.{GlossaryEnergy.InvestmentsValue}"][GlossaryEnergy.InvestmentsValue] \
                       - max_budget * conversion_factor_2

        self.outputs[GlossaryEnergy.MaxBudgetConstraintValue] = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.MaxBudgetConstraintValue: overspending / max_budget_constraint_ref
        })
