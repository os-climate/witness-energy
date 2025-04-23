'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2024/06/24 Copyright 2023 Capgemini

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


class OneInvest(BaseInvest):
    '''
        Model to split global investment into investment for each technology
    '''

    def __init__(self, name='Invest'):
        '''
        Constructor
        '''
        BaseInvest.__init__(self, name)
        # -- default value, can be changed if necessary
        self.distribution_list = None
        self.invest_mix = None
        self.years = None
        self.outputs = {}

    def compute(self, inputs_dict):
        """Compute the investements in enrgy and ccs technos"""
        self.outputs = {}
        self.years = np.arange(inputs_dict[GlossaryEnergy.YearStart], inputs_dict[GlossaryEnergy.YearEnd] + 1,)
        sector_streams  = {
            GlossaryEnergy.EnergyMix: inputs_dict['energy_list'],
            GlossaryEnergy.CCUS: inputs_dict['ccs_list'],
        }
        conversion_factor = GlossaryEnergy.conversion_dict[GlossaryEnergy.InvestmentDf['unit']][GlossaryEnergy.TechnoInvestDf['unit']]
        for sector in [GlossaryEnergy.CCUS, GlossaryEnergy.EnergyMix]:
            sector_cols = []
            for stream in sector_streams[sector]:
                sector_cols.extend([f"{stream}.{techno}" for techno in inputs_dict[f'{stream}.{GlossaryEnergy.techno_list}']])

            df_sector = inputs_dict[GlossaryEnergy.invest_mix][sector_cols]
            df_normalized = df_sector.div(df_sector.sum(axis=1), axis=0)

            invest_sector = inputs_dict[f"{sector}.{GlossaryEnergy.InvestmentsValue}"][GlossaryEnergy.InvestmentsValue].values
            for stream in sector_streams[sector]:
                for techno in inputs_dict[f'{stream}.{GlossaryEnergy.techno_list}']:
                    self.outputs[f"{stream}.{techno}.{GlossaryEnergy.InvestLevelValue}"] = pd.DataFrame({
                        GlossaryEnergy.Years: self.years,
                        GlossaryEnergy.InvestValue: df_normalized[f'{stream}.{techno}'] * invest_sector * conversion_factor,
                    })

        all_invests_df = pd.DataFrame({GlossaryEnergy.Years: self.years})
        for key, value in self.outputs.items():
            key1 = key.replace(f'.{GlossaryEnergy.InvestLevelValue}', '')
            all_invests_df[key1] = value[GlossaryEnergy.InvestValue].values
        self.outputs["all_invest_df"] = all_invests_df
