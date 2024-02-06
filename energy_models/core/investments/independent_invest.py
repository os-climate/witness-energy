'''
Copyright 2022 Airbus SAS
Modifications on 2023/04/21-2023/11/16 Copyright 2023 Capgemini

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

from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
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
        return energy_investment_wo_tax, energy_invest_objective

    def compute_energy_invest_objective(self, energy_investment_wo_tax):
        energy_invest_objective = energy_investment_wo_tax[GlossaryEnergy.EnergyInvestmentsWoTaxValue].values.sum()
        return np.array([energy_invest_objective])

    def compute_energy_investment_wo_tax(self, inputs_dict: dict):
        """computes investments in the energy sector (without tax)"""
        self.compute_distribution_list(inputs_dict)

        techno_invests = inputs_dict[GlossaryEnergy.invest_mix][self.distribution_list]
        techno_invest_sum = techno_invests.sum(axis=1).values

        techno_invest_sum += inputs_dict[GlossaryEnergy.ForestInvestmentValue][
            GlossaryEnergy.ForestInvestmentValue].values
        energy_list = inputs_dict[GlossaryEnergy.energy_list]

        if BiomassDry.name in energy_list:
            for techno in ['managed_wood_investment', 'deforestation_investment', 'crop_investment']:
                techno_invest_sum += inputs_dict[techno][GlossaryEnergy.InvestmentsValue].values
        energy_investment_wo_tax = pd.DataFrame(
            {GlossaryEnergy.Years: inputs_dict[GlossaryEnergy.invest_mix][GlossaryEnergy.Years],
             GlossaryEnergy.EnergyInvestmentsWoTaxValue: techno_invest_sum / 1e3})  # T$

        return energy_investment_wo_tax
