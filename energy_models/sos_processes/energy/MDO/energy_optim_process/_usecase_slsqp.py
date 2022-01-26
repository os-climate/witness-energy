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
from energy_models.core.energy_mix.energy_mix import EnergyMix

import numpy as np
import pandas as pd
from sos_trades_core.execution_engine.sos_optim_scenario import SoSOptimScenario

OBJECTIVE = FunctionManagerDisc.OBJECTIVE
INEQ_CONSTRAINT = FunctionManagerDisc.INEQ_CONSTRAINT
EQ_CONSTRAINT = FunctionManagerDisc.EQ_CONSTRAINT
OBJECTIVE_LAGR = FunctionManagerDisc.OBJECTIVE_LAGR
FUNC_DF = FunctionManagerDisc.FUNC_DF
DEMAND_VIOLATION = EnergyMix.DEMAND_VIOLATION
#DELTA_ENERGY_PRICES = EnergyMix.DELTA_ENERGY_PRICES


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

    def __init__(self, year_start=2020, year_end=2050, time_step=1, run_usecase=False, execution_engine=None):
        super().__init__(__file__, run_usecase=run_usecase, execution_engine=execution_engine)
        self.year_start = year_start
        self.year_end = year_end
        self.time_step = time_step

        self.optim_name = "EnergyOptimization"
        self.coupling_name = "EnergyModelEval"
        self.energy_mix_name = 'EnergyMix'  # should be importer from energy usecase

    def setup_usecase(self):
        #-- retrieve study_subproc data
        study_subproc = Study_subprocess(
            self.year_start, self.year_end, self.time_step, execution_engine=self.execution_engine)
        study_subproc.study_name = f'{self.study_name}.{self.optim_name}'
        study_subproc_data_list = study_subproc.setup_usecase()

        energy_list = study_subproc_data_list[0][f'{study_subproc.study_name}.{self.coupling_name}.energy_list']

        # setup constraints
        list_var = []
        for energy in energy_list:
            if energy in EnergyMix.energy_class_dict:
                out_name = f'{self.study_name}.{self.optim_name}.{self.coupling_name}.EnergyMix.{energy}.{DEMAND_VIOLATION}'
                sign = SoSOptimScenario.INEQ_POSITIVE
                list_var.append((out_name, sign))

        list_var.append(
            (f'{self.study_name}.{self.optim_name}.{self.coupling_name}.EnergyMix.primary_energies_production', sign))

        optim_values_dict = {f'{self.study_name}.{self.optim_name}.design_space': study_subproc.dspace,
                             # optimization functions:
                             f'{self.study_name}.{self.optim_name}.objective_name': FunctionManagerDisc.OBJECTIVE_LAGR,
                             f'{self.study_name}.{self.optim_name}.eq_constraints': [],

                             f'{self.study_name}.{self.optim_name}.ineq_constraints': list_var,

                             # optimization parameters:
                             f'{self.study_name}.{self.optim_name}.max_iter': 500,
                             # SLSQP, NLOPT_SLSQP
                             f'{self.study_name}.{self.optim_name}.algo': "NLOPT_SLSQP",
                             f'{self.study_name}.{self.optim_name}.formulation': 'DisciplinaryOpt',
                             f'{self.study_name}.{self.optim_name}.algo_options': {"ftol_rel": 1e-10,
                                                                                   "xtol_rel": 1e-8,
                                                                                   "ineq_tolerance": 1e-3,
                                                                                   "normalize_design_space": True,
                                                                                   },
                             f'{self.study_name}.{self.optim_name}.warm_start': True,
                             f'{self.study_name}.{self.optim_name}.differentiation_method': 'user',
                             #'usecase.EnergyOptimization.EnergyModelEval.FunctionManagerDisc.linearization_mode': 'finite_differences'
                             f'{self.study_name}.{self.optim_name}.EnergyModelEval.sub_mda_class': 'MDANewtonRaphson',
                             f'{self.study_name}.{self.optim_name}.EnergyModelEval.linear_solver_tolerance': 1.0e-8,
                             f'{self.study_name}.{self.optim_name}.EnergyModelEval.max_iter_GMRES': 7000,
                             f'{self.study_name}.{self.optim_name}.EnergyModelEval.linear_solver_MDO': 'GMRES'}

        return study_subproc_data_list + [optim_values_dict]


if '__main__' == __name__:
    uc_cls = Study(run_usecase=True)
    uc_cls.load_data()
#     uc_cls.execution_engine.root_process.sos_disciplines[0].sos_disciplines[0].coupling_structure.graph.export_reduced_graph(
#         "reduced.pdf")
#     uc_cls.execution_engine.root_process.sos_disciplines[0].sos_disciplines[0].coupling_structure.graph.export_initial_graph(
#         "initial.pdf")
   # uc_cls.execution_engine.display_treeview_nodes(display_variables=True)
    uc_cls.run()
    ppf = PostProcessingFactory()
    disc = uc_cls.execution_engine.dm.get_disciplines_with_name(
        'usecase.EnergyOptimization.EnergyModelEval.FunctionManagerDisc')
    # filters = ppf.get_post_processing_filters_by_discipline(
    #    disc)
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

#     # XDSMize vizu
#     uc_cls.execution_engine.root_process.sos_disciplines[0].xdsmize()
#     # to visualize in an internet browser :
#     # - download XDSMjs at https://github.com/OneraHub/XDSMjs and unzip
#     # - replace existing xdsm.json inside by yours
#     # - in the same folder, type in terminal 'python -m http.server 8080'
#     # - open in browser http://localhost:8080/xdsm.html
