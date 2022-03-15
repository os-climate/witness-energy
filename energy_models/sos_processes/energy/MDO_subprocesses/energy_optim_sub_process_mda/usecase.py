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
from sos_trades_core.study_manager.study_manager import StudyManager

from energy_models.sos_processes.energy.MDA.energy_process_v0_mda.usecase import Study as Study_MDA
from sos_trades_core.execution_engine.func_manager.func_manager_disc import FunctionManagerDisc
from energy_models.core.energy_mix.energy_mix import EnergyMix

import numpy as np
import pandas as pd
from energy_models.core.energy_process_builder import INVEST_DISCIPLINE_OPTIONS

OBJECTIVE = FunctionManagerDisc.OBJECTIVE
INEQ_CONSTRAINT = FunctionManagerDisc.INEQ_CONSTRAINT
EQ_CONSTRAINT = FunctionManagerDisc.EQ_CONSTRAINT
OBJECTIVE_LAGR = FunctionManagerDisc.OBJECTIVE_LAGR
FUNC_DF = FunctionManagerDisc.FUNC_DF
DEMAND_VIOLATION = EnergyMix.DEMAND_VIOLATION


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


class Study(StudyManager):

    def __init__(self, year_start=2020, year_end=2050, time_step=1, execution_engine=None, invest_discipline=INVEST_DISCIPLINE_OPTIONS[0]):
        super().__init__(__file__, execution_engine=execution_engine)
        self.year_start = year_start
        self.year_end = year_end
        self.time_step = time_step
        self.invest_discipline = invest_discipline
        self.coupling_name = "EnergyModelEval"
        self.designvariable_name = "DesignVariableDisc"
        self.func_manager_name = "FunctionManagerDisc"
        self.energy_mix_name = 'EnergyMix'  # should be importer from energy usecase
        self.ccs_mix_name = 'CCUS'
        self.energy_list = None
        self.ccs_list = None
        self.dict_technos = None

    def setup_usecase(self):

        #-- retrieve energy input data
        mda_usecase = Study_MDA(self.year_start, self.year_end,
                                self.time_step, execution_engine=self.execution_engine, invest_discipline=self.invest_discipline)
        mda_usecase.study_name = f'{self.study_name}.{self.coupling_name}'

        usecase_dict_list = mda_usecase.setup_usecase()

        dspace_df = mda_usecase.dspace

        self.energy_list = mda_usecase.energy_list
        self.ccs_list = mda_usecase.ccs_list
        self.dict_technos = mda_usecase.dict_technos

        dv_arrays_dict = {}
        design_var_descriptor = {}
        years = np.arange(self.year_start, self.year_end + 1, self.time_step)

        for energy in self.energy_list:
            energy_wo_dot = energy.replace('.', '_')
            if self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[0]:
                dv_arrays_dict[f'{mda_usecase.study_name}.{self.energy_mix_name}.{energy}.{energy_wo_dot}_array_mix'] = dspace_df[f'{energy}.{energy_wo_dot}_array_mix']['value']
                design_var_descriptor[f'{energy}.{energy_wo_dot}_array_mix'] = {'out_name': 'invest_mix',
                                                                            'out_type': 'dataframe',
                                                                            'key': f'{energy}',
                                                                            'index': years,
                                                                            'index_name': 'years',
                                                                            'namespace_in': 'ns_energy_mix',
                                                                            'namespace_out': 'ns_invest'}

            for technology in self.dict_technos[energy]:
                technology_wo_dot = technology.replace('.', '_')
                dv_arrays_dict[f'{mda_usecase.study_name}.{self.energy_mix_name}.{energy}.{technology}.{energy_wo_dot}_{technology_wo_dot}_array_mix'] = dspace_df[f'{energy}.{technology}.{energy_wo_dot}_{technology_wo_dot}_array_mix']['value']
                design_var_descriptor[f'{energy}.{technology}.{energy_wo_dot}_{technology_wo_dot}_array_mix'] = {'out_name': 'invest_mix',
                                                                                                             'out_type': 'dataframe',
                                                                                                             'key': f'{energy}.{technology}',
                                                                                                             'index': years,
                                                                                                             'index_name': 'years',
                                                                                                             'namespace_in': 'ns_energy_mix',
                                                                                                             'namespace_out': 'ns_invest'}

        for ccs in self.ccs_list:
            ccs_wo_dot = ccs.replace('.', '_')
            if self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[0]:
                dv_arrays_dict[f'{mda_usecase.study_name}.{self.ccs_mix_name}.{ccs}.{ccs_wo_dot}_array_mix'] = dspace_df[f'{ccs}.{ccs_wo_dot}_array_mix']['value']
                design_var_descriptor[f'{ccs}.{ccs_wo_dot}_array_mix'] = {'out_name': 'invest_mix',
                                                                      'out_type': 'dataframe',
                                                                      'key': f'{ccs}',
                                                                      'index': years,
                                                                      'index_name': 'years',
                                                                      'namespace_in': 'ns_ccs',
                                                                      'namespace_out': 'ns_invest'}

            for technology in self.dict_technos[ccs]:
                technology_wo_dot = technology.replace('.', '_')
                dv_arrays_dict[f'{mda_usecase.study_name}.{self.ccs_mix_name}.{ccs}.{technology}.{ccs_wo_dot}_{technology_wo_dot}_array_mix'] = dspace_df[f'{ccs}.{technology}.{ccs_wo_dot}_{technology_wo_dot}_array_mix']['value']
                design_var_descriptor[f'{ccs}.{technology}.{ccs_wo_dot}_{technology_wo_dot}_array_mix'] = {'out_name': 'invest_mix',
                                                                                                       'out_type': 'dataframe',
                                                                                                       'key': f'{ccs}.{technology}',
                                                                                                       'index': years,
                                                                                                       'index_name': 'years',
                                                                                                       'namespace_in': 'ns_ccs',
                                                                                                       'namespace_out': 'ns_invest'}

        if self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[0]:
            dv_arrays_dict[f'{mda_usecase.study_name}.ccs_percentage_array'] = dspace_df[f'ccs_percentage_array']['value']

        dv_arrays_dict[f'{mda_usecase.study_name}.{self.designvariable_name}.design_var_descriptor'] = design_var_descriptor

        # construct func_df
        func_df = pd.concat([mda_usecase.setup_objectives(),
                             mda_usecase.setup_constraints()])

        optim_values_dict = {f'{mda_usecase.study_name}.{self.func_manager_name}.{FUNC_DF}': func_df,
                             f'{mda_usecase.study_name}.epsilon0': 1.0,
                             f'{mda_usecase.study_name}.max_mda_iter': 50,
                             f'{mda_usecase.study_name}.tolerance': 1.0e-8,
                             f'{mda_usecase.study_name}.n_processes': 1,
                             f'{mda_usecase.study_name}.linearization_mode': 'adjoint',
                             f'{mda_usecase.study_name}.sub_mda_class': 'MDANewtonRaphson'}
        # design space

        dspace = mda_usecase.dspace
        self.dspace_size = dspace.pop('dspace_size')

        dspace_df_columns = ['variable', 'value', 'lower_bnd',
                             'upper_bnd', 'enable_variable']
        dspace_df = pd.DataFrame(columns=dspace_df_columns)
        for key, elem in dspace.items():
            dict_var = {'variable': key}
            dict_var.update(elem)
            dspace_df = dspace_df.append(dict_var, ignore_index=True)
        self.dspace = dspace_df
        optim_values_dict['usecase.design_space'] = self.dspace

        return usecase_dict_list + [optim_values_dict, dv_arrays_dict]


if '__main__' == __name__:
    uc_cls = Study()
    uc_cls.load_data()
    uc_cls.run()
    uc_cls.execution_engine.display_treeview_nodes(True)
    ppf = PostProcessingFactory()
#     for disc in uc_cls.execution_engine.root_process.sos_disciplines:
#         if disc.sos_name == 'EnergyMix.syngas.BiomassGasification':
#             filters = ppf.get_post_processing_filters_by_discipline(
#                 disc)
#             graph_list = ppf.get_post_processing_by_discipline(
#                 disc, filters, as_json=False)
#
#             for graph in graph_list:
#                 graph.to_plotly().show()

    # graph process (requires graphviz)
#     uc_cls.execution_engine.root_process.coupling_structure.graph.export_initial_graph(
#              "initial.pdf")
#     uc_cls.execution_engine.root_process.coupling_structure.graph.export_reduced_graph(
#     "reduced.pdf")
