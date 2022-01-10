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

from energy_models.core.design_variables_translation.design_var import Design_Var
from sos_trades_core.execution_engine.sos_discipline import SoSDiscipline
import csv
import time
from pandas import DataFrame


class Design_Var_Discipline(SoSDiscipline):

    EXPORT_XVECT = 'export_xvect'

    DESC_IN = {  # 'energy_list': {'type': 'string_list', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'possible_values': EnergyMix.energy_list, 'namespace': 'ns_public'},
        'energy_list': {'type': 'string_list', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_study', 'editable': False, 'structuring': True},
        'year_start': {'type': 'int', 'default': 2020, 'unit': '[-]', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'year_end': {'type': 'int', 'default': 2050, 'unit': '[-]', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'CO2_taxes_array': {'type': 'array', 'unit': '$/t', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_study'},
        EXPORT_XVECT: {'type': 'bool', 'default': False, 'structuring': True}
    }

    energy_name = Design_Var.name

    DESC_OUT = {'invest_energy_mix': {'type': 'dataframe',
                                      'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_mix'},
                'CO2_taxes': {'type': 'dataframe', 'unit': '$/t', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_study'}
                }

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.energy_model = Design_Var(self.energy_name)
        self.energy_model.configure_parameters(inputs_dict)

    def setup_sos_disciplines(self):

        dynamic_inputs = {}
        dynamic_outputs = {}

        if 'energy_list' in self._data_in:
            energy_list = self.get_sosdisc_inputs('energy_list')
            if energy_list is not None:
                for energy in energy_list:
                    energy_wo_dot = energy.replace('.', '_')
                    dynamic_inputs[f'{energy}.{energy_wo_dot}_array_mix'] = {
                        'type': 'array', 'unit': '%', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_mix'}
                    dynamic_inputs[f'{energy}.technologies_list'] = {'type': 'string_list',
                                                                     'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_mix', 'structuring': True}
                    dynamic_outputs[f'{energy}.invest_techno_mix'] = {
                        'type': 'dataframe', 'unit': '$', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_mix'}
                    if f'{energy}.technologies_list' in self._data_in:
                        technology_list = self.get_sosdisc_inputs(
                            f'{energy}.technologies_list')

                        if technology_list is not None:
                            for techno in technology_list:
                                techno_wo_dot = techno.replace('.', '_')
                                dynamic_inputs[f'{energy}.{techno}.{energy_wo_dot}_{techno_wo_dot}_array_mix'] = {
                                    'type': 'array', 'unit': '%', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_mix'}

        if self.EXPORT_XVECT in self._data_in:
            if self.get_sosdisc_inputs(self.EXPORT_XVECT):
                dynamic_outputs['last_3_xvect'] = {'type': 'dataframe'}

        self.add_inputs(dynamic_inputs)
        self.add_outputs(dynamic_outputs)
        self.iter = 0

    def run(self):
        #-- get inputs
        inputs_dict = self.get_sosdisc_inputs()

        #-- configure class with inputs
        self.energy_model.configure_parameters_update(inputs_dict)
        self.store_sos_outputs_values(self.energy_model.output_dict)
        #-- compute informations
        outputs_dict = {
            'invest_energy_mix': self.energy_model.invest_energy_mix}

        if self.get_sosdisc_inputs(self.EXPORT_XVECT):
            header = [key for key in inputs_dict.keys() if '_array_mix' in key]
            x_vect = [self.iter, ]
            for key in header:
                x_vect += [inputs_dict[key], ]
            dict_xvect = dict(zip(['n_ite'] + header, x_vect))
            dict_xvect = {k: [v] for k, v in dict_xvect.items()}
            if self.iter == 0:
                df_xvect = DataFrame(
                    dict_xvect)
            else:
                df_xvect = self.get_sosdisc_outputs('last_3_xvect')
                df_xvect = df_xvect.append(
                    DataFrame(dict_xvect), ignore_index=True)
                if len(df_xvect.index) > 3:
                    df_xvect = df_xvect.drop([0])
            outputs_dict = {'last_3_xvect': df_xvect}

        #-- store outputs
        self.store_sos_outputs_values(outputs_dict)
        self.iter += 1

    def compute_sos_jacobian(self):

        inputs_dict = self.get_sosdisc_inputs()

        years = np.arange(inputs_dict['year_start'],
                          inputs_dict['year_end'] + 1)

        for energy in inputs_dict['energy_list']:
            energy_wo_dot = energy.replace('.', '_')
            self.set_partial_derivative_for_other_types(
                (f'invest_energy_mix', energy), (f'{energy}.{energy_wo_dot}_array_mix',),  np.identity(len(years)))
            for techno in inputs_dict[f'{energy}.technologies_list']:
                techno_wo_dot = techno.replace('.', '_')
                self.set_partial_derivative_for_other_types(
                    (f'{energy}.invest_techno_mix', techno), (f'{energy}.{techno}.{energy_wo_dot}_{techno_wo_dot}_array_mix',),  np.identity(len(years)))

        self.set_partial_derivative_for_other_types(
            ('CO2_taxes', 'CO2_tax'), ('CO2_taxes_array',),  np.identity(len(years)))
