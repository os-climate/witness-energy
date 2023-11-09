'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07 Copyright 2023 Capgemini

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
from climateeconomics.glossarycore import GlossaryCore
from .base_invest import BaseInvest
import pandas as pd


class OneInvest(BaseInvest):
    '''
        Model to split global investment into investment for each technology 
    '''

    def __init__(self, name='Invest'):
        '''
        Constructor
        '''
        BaseInvest.__init__(self, name)
        #-- default value, can be changed if necessary
        self.distribution_list = None
        self.invest_mix = None
        self.rescaling_factor = 1e2

    def compute(self, inputs_dict):
        '''
        Compute all invests with invest_mix coefficients
        '''
        energy_investment = inputs_dict[GlossaryCore.EnergyInvestmentsValue]
        self.rescaling_factor = inputs_dict['scaling_factor_energy_investment']
        energy_invest_df = pd.DataFrame({GlossaryCore.Years: energy_investment[GlossaryCore.Years].values,
                                         GlossaryCore.EnergyInvestmentsValue: energy_investment[GlossaryCore.EnergyInvestmentsValue].values * self.rescaling_factor})

        self.compute_distribution_list(inputs_dict)

        all_invest_df, unit = self.get_invest_distrib(
            energy_invest_df,
            inputs_dict[GlossaryCore.invest_mix],
            input_unit='G$',
            output_unit='G$',
            column_name=GlossaryCore.EnergyInvestmentsValue
        )

        return all_invest_df

    def set_invest_mix(self, mix_df):
        '''
        Set the invest mix of the energy mix 
        '''
        if not isinstance(self.distribution_list, list):
            raise TypeError('energy_list must be defined as a list')
        head_list = list(mix_df.columns)
        try:
            head_list.remove(GlossaryCore.Years)
        except:
            print('years not in dataframe')
        if sorted(head_list) == sorted(self.distribution_list):
            BaseInvest.set_invest_mix(self, mix_df)
        else:
            raise ValueError(str(sorted(head_list)) +
                             ' should be equal to ' + str(sorted(self.distribution_list)))

    def get_invest_distrib(self, invest_level, invest_mix, input_unit, output_unit, column_name=GlossaryCore.InvestValue):
        self.set_invest_level(invest_level, input_unit, column_name)
        self.set_invest_mix(invest_mix)
        self.energy_list = self.distribution_list
        invest_distrib, unit = self.get_distributed_invest(
            self.distribution_list, output_unit)
        return invest_distrib, unit

    def get_invest_dict(self, invest_level, invest_mix, input_unit, output_unit):
        invest_distrib, unit = self.get_invest_distrib(
            invest_level, invest_mix, input_unit, output_unit)
        invest_dict = invest_distrib.to_dict('list')
        return invest_dict, unit
