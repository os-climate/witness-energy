'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2023/11/09 Copyright 2023 Capgemini

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
from energy_models.glossaryenergy import GlossaryEnergy

from .base_invest import BaseInvest


class EnergyInvest(BaseInvest):
    def __init__(self, name='Energy'):
        BaseInvest.__init__(self, name)
        # -- default value, can be changed if necessary
        self.energy_list = None
        self.invest_mix = None
        self.rescaling_factor = 1e2

    def set_energy_list(self, energy_list):
        '''
        Set the energy_list of the energy mix 
        '''
        self.energy_list = energy_list

    def set_invest_mix(self, mix_df):
        '''
        Set the invest mix of the energy mix 
        '''
        if not isinstance(self.energy_list, list):
            raise TypeError('energy_list must be defined as a list')
        head_list = list(mix_df.columns)
        try:
            head_list.remove(GlossaryEnergy.Years)
        except:
            print('years not in dataframe')
        if sorted(head_list) == sorted(self.energy_list):
            BaseInvest.set_invest_mix(self, mix_df)
        else:
            raise ValueError(str(sorted(head_list)) +
                             ' should be equal to ' + str(sorted(self.energy_list)))

    def get_invest_distrib(self, invest_level, invest_mix, input_unit, output_unit,
                           column_name=GlossaryEnergy.InvestValue):
        self.set_invest_level(invest_level, input_unit, column_name)
        self.set_invest_mix(invest_mix)
        invest_distrib, unit = self.get_distributed_invest(
            self.energy_list, output_unit)
        return invest_distrib, unit

    def get_invest_dict(self, invest_level, invest_mix, input_unit, output_unit):
        invest_distrib, unit = self.get_invest_distrib(
            invest_level, invest_mix, input_unit, output_unit)
        invest_dict = invest_distrib.to_dict('list')
        return invest_dict, unit
