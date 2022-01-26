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

from energy_models.sos_processes.energy.MDO_subprocesses.energy_optim_sub_process_mda.usecase import Study as Study_subprocess
from sos_trades_core.execution_engine.func_manager.func_manager_disc import FunctionManagerDisc
from energy_models.core.design_variables_translation.design_var_disc import Design_Var_Discipline
from energy_models.core.energy_mix.energy_mix import EnergyMix

from os.path import dirname
import numpy as np
import pandas as pd
from energy_models.core.energy_process_builder import INVEST_DISCIPLINE_DEFAULT,\
    INVEST_DISCIPLINE_OPTIONS

OBJECTIVE = FunctionManagerDisc.OBJECTIVE
INEQ_CONSTRAINT = FunctionManagerDisc.INEQ_CONSTRAINT
EQ_CONSTRAINT = FunctionManagerDisc.EQ_CONSTRAINT
OBJECTIVE_LAGR = FunctionManagerDisc.OBJECTIVE_LAGR
FUNC_DF = FunctionManagerDisc.FUNC_DF
DEMAND_VIOLATION = EnergyMix.DEMAND_VIOLATION
EXPORT_CSV = FunctionManagerDisc.EXPORT_CSV
EXPORT_XVECT = Design_Var_Discipline.EXPORT_XVECT


class Study(StudyManager):

    def __init__(self, year_start=2020, year_end=2050, time_step=1, run_usecase=False, execution_engine=None, invest_discipline=INVEST_DISCIPLINE_OPTIONS[0]):
        super().__init__(__file__, run_usecase=run_usecase, execution_engine=execution_engine)
        self.year_start = year_start
        self.year_end = year_end
        self.time_step = time_step

        self.optim_name = "EnergyOptimization"
        self.coupling_name = "EnergyModelEval"
        self.energy_mix_name = 'EnergyMix'  # should be importer from energy usecase
        self.designvariable_name = "DesignVariableDisc"
        self.invest_discipline = invest_discipline

    def setup_usecase(self):

        #-- retrieve study_subproc data
        study_subproc = Study_subprocess(
            self.year_start, self.year_end, self.time_step, execution_engine=self.execution_engine, invest_discipline=self.invest_discipline)
        study_subproc.study_name = f'{self.study_name}.{self.optim_name}'
        study_subproc_data_list = study_subproc.setup_usecase()

        self.dspace = study_subproc.dspace

        dspace_size = study_subproc.dspace_size
        dspace_df = pd.DataFrame(self.dspace)

        #-- energy optimization inputs
        optim_values_dict = {f'{self.study_name}.{self.optim_name}.design_space': dspace_df,
                             # optimization functions:
                             f'{self.study_name}.{self.optim_name}.objective_name': FunctionManagerDisc.OBJECTIVE_LAGR,
                             f'{self.study_name}.{self.optim_name}.eq_constraints': [],
                             f'{self.study_name}.{self.optim_name}.ineq_constraints': [],
                             # optimization parameters:
                             f'{self.study_name}.{self.optim_name}.max_iter': 500,
                             # SLSQP, NLOPT_SLSQP
                             f'{self.study_name}.{self.optim_name}.algo': "L-BFGS-B",
                             f'{self.study_name}.{self.optim_name}.formulation': 'DisciplinaryOpt',
                             f'{self.study_name}.{self.optim_name}.algo_options': {"ftol_rel": 1e-10,
                                                                                   "ineq_tolerance": 2e-3,
                                                                                   "normalize_design_space": True,
                                                                                   "maxls": 2 * dspace_size,
                                                                                   "maxcor": dspace_size,
                                                                                   "factr": 1.,
                                                                                   "pg_tol": 1.e-9,
                                                                                   "max_iter": 500,
                                                                                   #  'linesearch': 'lnsrlb',
                                                                                   #  'lnsrlb_xtol': 0.1
                                                                                   },
                             f'{self.study_name}.{self.optim_name}.{self.coupling_name}.warm_start': True,
                             f'{self.study_name}.{self.optim_name}.{self.coupling_name}.alpha': 0.5,
                             f'{self.study_name}.{self.optim_name}.differentiation_method': 'user',
                             f'{self.study_name}.{self.optim_name}.{self.coupling_name}.linear_solver_MDO_options': {'tol': 1.0e-6,
                                                                                                                     'max_iter': 5000},
                             f'{self.study_name}.{self.optim_name}.{self.coupling_name}.linear_solver_MDA_options': {'tol': 1.0e-7,
                                                                                                                     'max_iter': 5001},

                             #'usecase.EnergyOptimization.{self.coupling_name}.FunctionManagerDisc.linearization_mode':'finite_differences'
                             f'{self.study_name}.{self.optim_name}.{self.coupling_name}.sub_mda_class': 'MDANewtonRaphson',

                             # Boolean to print csv of optim
                             f'{self.study_name}.{self.optim_name}.{self.coupling_name}.FunctionManagerDisc.{EXPORT_CSV}': False,
                             f'{self.study_name}.{self.optim_name}.{self.coupling_name}.DesignVariableDisc.{EXPORT_XVECT}': False}

        return study_subproc_data_list + [optim_values_dict]


if '__main__' == __name__:
    uc_cls = Study(run_usecase=True)
    uc_cls.load_data()
    uc_cls.execution_engine.display_treeview_nodes()
#    uc_cls.dump_directory = dirname(__file__)
#     uc_cls.run(dump_study=True)
    uc_cls.run()
    '''
    ppf = PostProcessingFactory()
    disc = uc_cls.execution_engine.dm.get_disciplines_with_name(
        f'{uc_cls.study_name}.{uc_cls.optim_name}.{uc_cls.coupling_name}.FunctionManagerDisc')

    graph_list = ppf.get_post_processing_by_discipline(
        disc[0], None, as_json=False)

    for graph in graph_list:
        graph.to_plotly().show()

    disc = uc_cls.execution_engine.dm.get_disciplines_with_name(
        f'{uc_cls.study_name}.{uc_cls.optim_name}.{uc_cls.coupling_name}')

    graph_list = ppf.get_post_processing_by_discipline(
        disc[0], None, as_json=False)

    for graph in graph_list:
        graph.to_plotly().show()
    # for disc in uc_cls.execution_engine.root_process.sos_disciplines:
        # if disc.sos_name == 'EnergyMix.syngas.BiomassGasification':
        # filters = ppf.get_post_processing_filters_by_discipline(
        # disc)
        # graph_list = ppf.get_post_processing_by_discipline(
        # disc, filters, as_json=False)
        #
        # for graph in graph_list:
        # graph.to_plotly().show()

    # graph process (requires graphviz)
#     uc_cls.execution_engine.root_process.coupling_structure.graph.export_initial_graph(
#              "initial.pdf")
#     uc_cls.execution_engine.root_process.coupling_structure.graph.export_reduced_graph(
#     "reduced.pdf")
    '''
