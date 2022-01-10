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


class Design_Var(object):
    """
    Class Design variable
    """
    name = 'design_var'

    def __init__(self, name):
        self.name = name
        self.CO2_tax = None
        self.CO2_tax_array = None

    def convert_arr_df(self, **kwargs):
        """
        Function that combines a set of numpy arrays into one global dataframe
        Parameters
        ----------
        *args : numpy arrays

        Returns
        -------
        None.

        """
        merged_df = pd.DataFrame(kwargs)
        merged_df['years'] = np.arange(self.year_start, self.year_end + 1)
        return(merged_df)

    def configure(self, inputs_dict):

        self.configure_parameters(inputs_dict)
        self.configure_parameters_update(inputs_dict)

    def configure_parameters(self, inputs_dict):
        '''
        Configure with inputs_dict from the discipline
        '''
        self.year_start = inputs_dict['year_start']
        self.year_end = inputs_dict['year_end']
        self.energy_list = inputs_dict['energy_list']
        self.energy_dict = dict()
        self.energy_mix_dict = dict()
        self.techno_mix_dict = dict()
        self.techno_mix = dict()
        self.output_dict = dict()
        self.invest_techno_mix = dict()

    def configure_parameters_update(self, inputs_dict):
        '''
        Configure with inputs_dict from the discipline
        '''
        for energy in self.energy_list:
            energy_wo_dot = energy.replace('.', '_')
            self.energy_mix_dict[energy] = inputs_dict[f'{energy}.{energy_wo_dot}_array_mix']
            self.techno_mix_dict[energy] = dict()
            technology_list = inputs_dict[f'{energy}.technologies_list']
            for techno in technology_list:
                techno_wo_dot = techno.replace('.', '_')
                self.techno_mix_dict[energy][techno] = inputs_dict[
                    f'{energy}.{techno}.{energy_wo_dot}_{techno_wo_dot}_array_mix']
        self.energy_mix = self.convert_arr_df(**self.energy_mix_dict)
        self.invest_energy_mix = self.convert_arr_df(**self.energy_mix_dict)

        for _key in self.techno_mix_dict.keys():
            self.techno_mix[_key] = self.convert_arr_df(
                **self.techno_mix_dict[_key])
            self.invest_techno_mix[_key] = self.convert_arr_df(
                **self.techno_mix_dict[_key])
            self.output_dict[f'{_key}.invest_techno_mix'] = self.invest_techno_mix[_key]

        self.CO2_tax_array = inputs_dict[
            'CO2_taxes_array']
        self.CO2_tax = pd.DataFrame({'years': np.arange(
            self.year_start, self.year_end + 1), 'CO2_tax': self.CO2_tax_array})
        self.output_dict['CO2_taxes'] = self.CO2_tax
