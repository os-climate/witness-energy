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
from sos_trades_core.tools.post_processing.post_processing_factory import PostProcessingFactory

from energy_models.sos_processes.energy.MDA.energy_process_v0.usecase import Study as energy_usecase
from sos_trades_core.execution_engine.func_manager.func_manager_disc import FunctionManagerDisc
from energy_models.core.energy_mix.energy_mix import EnergyMix

import numpy as np
import pandas as pd
from energy_models.core.energy_process_builder import INVEST_DISCIPLINE_OPTIONS,\
    INVEST_DISCIPLINE_DEFAULT
from energy_models.core.energy_study_manager import EnergyStudyManager

OBJECTIVE = FunctionManagerDisc.OBJECTIVE
INEQ_CONSTRAINT = FunctionManagerDisc.INEQ_CONSTRAINT
EQ_CONSTRAINT = FunctionManagerDisc.EQ_CONSTRAINT
OBJECTIVE_LAGR = FunctionManagerDisc.OBJECTIVE_LAGR
FUNC_DF = FunctionManagerDisc.FUNC_DF


def update_dspace_with(dspace_dict, name, value, lower, upper):
    ''' type(value) has to be ndarray
    '''
    if not isinstance(lower, (list, np.ndarray)):
        lower = [lower] * len(value)
    if not isinstance(upper, (list, np.ndarray)):
        upper = [upper] * len(value)
    dspace_dict['variable'].append(name)
    dspace_dict['value'].append(str(value.tolist()))
    dspace_dict['lower_bnd'].append(str(lower))
    dspace_dict['upper_bnd'].append(str(upper))
    dspace_dict['dspace_size'] += len(value)


class Study(EnergyStudyManager):

    def __init__(self, year_start=2020, year_end=2050, time_step=1, execution_engine=None, invest_discipline=INVEST_DISCIPLINE_OPTIONS[0]):
        super().__init__(__file__, execution_engine=execution_engine)
        self.year_start = year_start
        self.year_end = year_end
        self.time_step = time_step

        self.coupling_name = "EnergyModelEval"
        self.designvariable_name = "DesignVariableDisc"
        self.func_manager_name = "FunctionManagerDisc"
        self.energy_mix_name = 'EnergyMix'  # should be importer from energy usecase
        self.ccs_mix_name = 'CCUS'
        self.energy_list = None
        self.ccs_list = None
        self.dict_technos = None
        self.invest_discipline = invest_discipline

    def setup_usecase(self):

        #-- retrieve energy input data
        energy_uc = energy_usecase(
            self.year_start, self.year_end, self.time_step, main_study=False, execution_engine=self.execution_engine, invest_discipline=self.invest_discipline)
        energy_uc.study_name = f'{self.study_name}.{self.coupling_name}'

        usecase_dict_list = energy_uc.setup_usecase()

        dspace_df = energy_uc.dspace

        self.energy_list = energy_uc.energy_list

        self.ccs_list = energy_uc.ccs_list
        self.dict_technos = energy_uc.dict_technos

        dv_arrays_dict = {}
        design_var_descriptor = {}
        years = np.arange(self.year_start, self.year_end + 1, self.time_step)

        for energy in self.energy_list:
            energy_wo_dot = energy.replace('.', '_')
            if self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[0]:
                dv_arrays_dict[f'{energy_uc.study_name}.{self.energy_mix_name}.{energy}.{energy_wo_dot}_array_mix'] = dspace_df[f'{energy}.{energy_wo_dot}_array_mix']['value']
                design_var_descriptor[f'{energy}.{energy_wo_dot}_array_mix'] = {'out_name': 'invest_mix',
                                                                                'out_type': 'dataframe',
                                                                                'key': f'{energy}',
                                                                                'index': years,
                                                                                'index_name': 'years',
                                                                                'namespace_in': 'ns_energy_mix',
                                                                                'namespace_out': 'ns_invest'
                                                                                }
            for technology in self.dict_technos[energy]:
                technology_wo_dot = technology.replace('.', '_')
                dv_arrays_dict[f'{energy_uc.study_name}.{self.energy_mix_name}.{energy}.{technology}.{energy_wo_dot}_{technology_wo_dot}_array_mix'] = dspace_df[
                    f'{energy}.{technology}.{energy_wo_dot}_{technology_wo_dot}_array_mix']['value']
                design_var_descriptor[f'{energy}.{technology}.{energy_wo_dot}_{technology_wo_dot}_array_mix'] = {'out_name': 'invest_mix',
                                                                                                                 'out_type': 'dataframe',
                                                                                                                 'key': f'{energy}.{technology}',
                                                                                                                 'index': years,
                                                                                                                 'index_name': 'years',
                                                                                                                 'namespace_in': 'ns_energy_mix',
                                                                                                                 'namespace_out': 'ns_invest'
                                                                                                                 }

        for ccs in self.ccs_list:
            ccs_wo_dot = ccs.replace('.', '_')
            if self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[0]:
                dv_arrays_dict[f'{energy_uc.study_name}.{self.ccs_mix_name}.{ccs}.{ccs_wo_dot}_array_mix'] = dspace_df[f'{ccs}.{ccs_wo_dot}_array_mix']['value']
                design_var_descriptor[f'{ccs}.{ccs_wo_dot}_array_mix'] = {'out_name': 'invest_mix',
                                                                          'out_type': 'dataframe',
                                                                          'key': f'{ccs}',
                                                                          'index': years,
                                                                          'index_name': 'years',
                                                                          'namespace_in': 'ns_ccs',
                                                                          'namespace_out': 'ns_invest'
                                                                          }
            for technology in self.dict_technos[ccs]:
                technology_wo_dot = technology.replace('.', '_')
                dv_arrays_dict[f'{energy_uc.study_name}.{self.ccs_mix_name}.{ccs}.{technology}.{ccs_wo_dot}_{technology_wo_dot}_array_mix'] = dspace_df[
                    f'{ccs}.{technology}.{ccs_wo_dot}_{technology_wo_dot}_array_mix']['value']
                design_var_descriptor[f'{ccs}.{technology}.{ccs_wo_dot}_{technology_wo_dot}_array_mix'] = {'out_name': 'invest_mix',
                                                                                                           'out_type': 'dataframe',
                                                                                                           'key': f'{ccs}.{technology}',
                                                                                                           'index': years,
                                                                                                           'index_name': 'years',
                                                                                                           'namespace_in': 'ns_ccs',
                                                                                                           'namespace_out': 'ns_invest'}

        if self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[0]:
            dv_arrays_dict[f'{energy_uc.study_name}.ccs_percentage_array'] = dspace_df[f'ccs_percentage_array']['value']

        dv_arrays_dict[f'{energy_uc.study_name}.{self.designvariable_name}.design_var_descriptor'] = design_var_descriptor
        # construct func_df
        func_df = pd.concat([energy_uc.setup_objectives(),
                             energy_uc.setup_constraints()])

        optim_values_dict = {f'{energy_uc.study_name}.{self.func_manager_name}.{FUNC_DF}': func_df,
                             f'{energy_uc.study_name}.epsilon0': 1.0,
                             f'{energy_uc.study_name}.max_mda_iter': 50,
                             f'{energy_uc.study_name}.tolerance': 1.0e-8,
                             f'{energy_uc.study_name}.n_processes': 1,
                             f'{energy_uc.study_name}.linearization_mode': 'adjoint',
                             f'{energy_uc.study_name}.sub_mda_class': 'GSPureNewtonMDA'}
        # design space

        dspace = energy_uc.dspace
        self.dspace_size = dspace.pop('dspace_size')

        dspace_df_columns = ['variable', 'value', 'lower_bnd',
                             'upper_bnd', 'enable_variable']
        dspace_df = pd.DataFrame(columns=dspace_df_columns)
        for key, elem in dspace.items():
            dict_var = {'variable': key}
            dict_var.update(elem)
            dspace_df = dspace_df.append(dict_var, ignore_index=True)
        self.dspace = dspace_df
        optim_values_dict[f'{self.study_name}.design_space'] = self.dspace

        return usecase_dict_list + [optim_values_dict, dv_arrays_dict]


if '__main__' == __name__:
    uc_cls = Study()
    uc_cls.load_data()
    uc_cls.run()
    # uc_cls.execution_engine.display_treeview_nodes(display_variables=True)
    #ppf = PostProcessingFactory()
