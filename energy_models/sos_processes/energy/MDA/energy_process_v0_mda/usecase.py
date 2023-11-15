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

from sostrades_core.study_manager.study_manager import StudyManager
from energy_models.core.energy_study_manager import DEFAULT_TECHNO_DICT

from energy_models.sos_processes.energy.MDA.energy_process_v0.usecase import Study as Study_v0

from sostrades_core.execution_engine.func_manager.func_manager_disc import FunctionManagerDisc
from energy_models.core.energy_mix.energy_mix import EnergyMix
from sostrades_core.tools.post_processing.post_processing_factory import PostProcessingFactory
from sostrades_core.tools.base_functions.specific_check import specific_check_years
from energy_models.core.energy_process_builder import INVEST_DISCIPLINE_DEFAULT

import cProfile
from io import StringIO
import pstats

OBJECTIVE = FunctionManagerDisc.OBJECTIVE
INEQ_CONSTRAINT = FunctionManagerDisc.INEQ_CONSTRAINT
EQ_CONSTRAINT = FunctionManagerDisc.EQ_CONSTRAINT
OBJECTIVE_LAGR = FunctionManagerDisc.OBJECTIVE_LAGR
FUNC_DF = FunctionManagerDisc.FUNC_DF


class Study(StudyManager):

    def __init__(self, year_start=2020, year_end=2050, time_step=1, lower_bound_techno=1.0e-6, upper_bound_techno=100.,
                 techno_dict=DEFAULT_TECHNO_DICT, bspline=True, invest_discipline=INVEST_DISCIPLINE_DEFAULT,
                 execution_engine=None):
        self.year_start = year_start
        self.year_end = year_end
        self.time_step = time_step
        self.energy_list = None
        self.ccs_list = None
        self.dict_technos = None
        self.bspline = bspline
        self.invest_discipline = invest_discipline
        self.lower_bound_techno = lower_bound_techno
        self.upper_bound_techno = upper_bound_techno

        # -- Call class constructor after attributes have been set for setup_process usage
        super().__init__(__file__, execution_engine=execution_engine)

        self.study_v0 = Study_v0(
            self.year_start, self.year_end, self.time_step, main_study=False, bspline=self.bspline,
            execution_engine=execution_engine,
            invest_discipline=self.invest_discipline, techno_dict=techno_dict)
        self.sub_study_path_dict = self.study_v0.sub_study_path_dict

    def setup_objectives(self):
        func_df = Study_v0.setup_objectives(self)
        return func_df

    def setup_constraints(self):
        func_df = Study_v0.setup_constraints(self)
        return func_df

    def setup_usecase(self):
        values_dict_list = []

        self.study_v0.study_name = self.study_name
        self.energy_usecase = self.study_v0
        invest_list = self.study_v0.setup_usecase()
        values_dict_list.extend(invest_list)
        self.energy_list = self.study_v0.energy_list
        self.ccs_list = self.study_v0.ccs_list
        self.dspace = self.study_v0.dspace
        self.dict_technos = self.study_v0.dict_technos
        numerical_values_dict = {
            f'{self.study_name}.epsilon0': 1.0,
            f'{self.study_name}.max_mda_iter': 50,
            f'{self.study_name}.tolerance': 1.0e-7,
            f'{self.study_name}.n_processes': 1,
            f'{self.study_name}.linearization_mode': 'adjoint',
            f'{self.study_name}.sub_mda_class': 'MDAGaussSeidel'}
        values_dict_list.append(numerical_values_dict)

        return values_dict_list

    def specific_check(self):
        """
        Specific check of years column
        """
        specific_check_years(self.execution_engine.dm)


if '__main__' == __name__:
    uc_cls = Study()
    uc_cls.load_data()
    #     uc_cls.execution_engine.root_process.coupling_structure.graph.export_reduced_graph(
    #         "reduced.pdf")
    profil = cProfile.Profile()
    profil.enable()
    uc_cls.run()
    profil.disable()
    result = StringIO()

    ps = pstats.Stats(profil, stream=result)
    ps.sort_stats('cumulative')
    ps.print_stats(200)
    result = result.getvalue()
    print(result)
    # Always check if post procs are OK
    ppf = PostProcessingFactory()

    # for disc in uc_cls.execution_engine.root_process.proxy_disciplines:

    #     filters = ppf.get_post_processing_filters_by_discipline(

    #         disc)

    graph_list = ppf.get_all_post_processings(uc_cls.ee, filters_only=False)
    for graph in graph_list:
        graph.to_plotly().show()
