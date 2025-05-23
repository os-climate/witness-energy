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
from copy import deepcopy

# DESC_IN = Invest + energy source inputs
# DESC_OUT = energy techno output (J or Wh) + price + cost breakdown
import pandas as pd

from energy_models.glossaryenergy import GlossaryEnergy


class BaseInvest:
    # -- $ for now, to be able to change to euros if necessary
    POS_UNIT = ['$', 'k$', 'M$', 'G$', 'T$']
    name = 'base_invest'

    def __init__(self, name):
        self.name = name
        self.invest_df = None
        self.invest_unit = '$'
        self.mix_df = None
        self.energy_list = None
        self.column_name = None
        self.distribution_list = None

    # -- Setters

    def set_invest_unit(self, unit):
        self.check_unit(unit)
        self.invest_unit = unit

    def set_invest_level(self, invest_df, unit='$', column_name=GlossaryEnergy.InvestValue):
        self.column_name = column_name
        self.set_invest_unit(unit)
        if isinstance(invest_df, pd.DataFrame):
            self.invest_df = invest_df
        else:
            raise TypeError('invest_level must be a dataframe')

    def set_invest_mix(self, mix_df):
        if isinstance(mix_df, pd.DataFrame):
            self.mix_df = mix_df
        else:
            raise TypeError('invest_mix must be a dataframe')

    # -- Methods
    def check_unit(self, unit):
        if unit not in self.POS_UNIT:
            raise Exception(ValueError(
                'unit [' + unit + '] should be one of ' + str(self.POS_UNIT)))

    def get_invest_level(self, unit='$'):
        out_df = deepcopy(self.invest_df)
        self.check_unit(unit)
        ind_in = self.POS_UNIT.index(unit)
        ind_obj = self.POS_UNIT.index(self.invest_unit)
        delta = ind_in - ind_obj
        fact = 1.e3 ** (-delta)
        out_df[self.column_name] = self.invest_df[self.column_name] * fact
        return out_df

    def get_distributed_invest(self, base_list, output_unit):
        norm_mix = compute_norm_mix(self.mix_df, base_list)

        converted_invest_df = self.get_invest_level(output_unit)
        converted_invest_df[GlossaryEnergy.Years] = converted_invest_df[GlossaryEnergy.Years].values.real.astype(
            int)
        self.mix_df[GlossaryEnergy.Years] = self.mix_df[GlossaryEnergy.Years].values.real.astype(
            int)
        invest_distrib = pd.merge(self.mix_df, converted_invest_df, on=GlossaryEnergy.Years)

        for energy in base_list:
            invest_distrib[energy] *= invest_distrib[self.column_name].values / \
                                      norm_mix.values

        return invest_distrib[self.energy_list + [GlossaryEnergy.Years]], output_unit

    def compute_distribution_list(self, input_dict):
        self.distribution_list = []
        for energy in input_dict[GlossaryEnergy.energy_list]:
            if energy == GlossaryEnergy.biomass_dry:
                pass
            else:
                for techno in input_dict[f'{energy}.{GlossaryEnergy.techno_list}']:
                    self.distribution_list.append(f'{energy}.{techno}')
        for ccs in input_dict[GlossaryEnergy.ccs_list]:
            for techno in input_dict[f'{ccs}.{GlossaryEnergy.techno_list}']:
                self.distribution_list.append(f'{ccs}.{techno}')


def compute_norm_mix(mix_df, base_list):
    norm_mix = mix_df[base_list].sum(axis=1)

    return norm_mix
