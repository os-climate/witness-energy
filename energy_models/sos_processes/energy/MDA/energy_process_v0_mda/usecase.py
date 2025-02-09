'''
Copyright 2022 Airbus SAS
Modifications on 2023/04/21-2024/06/24 Copyright 2023 Capgemini

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
from sostrades_optimization_plugins.models.func_manager.func_manager_disc import (
    FunctionManagerDisc,
)

from energy_models.core.energy_process_builder import INVEST_DISCIPLINE_DEFAULT
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.sos_processes.energy.MDA.energy_process_v0.usecase import (
    Study as Study_v0,
)

OBJECTIVE = FunctionManagerDisc.OBJECTIVE
INEQ_CONSTRAINT = FunctionManagerDisc.INEQ_CONSTRAINT
EQ_CONSTRAINT = FunctionManagerDisc.EQ_CONSTRAINT
OBJECTIVE_LAGR = FunctionManagerDisc.OBJECTIVE_LAGR
FUNC_DF = FunctionManagerDisc.FUNC_DF


class Study(StudyManager):
    def __init__(
            self,
            year_start=GlossaryEnergy.YearStartDefault,
            year_end=GlossaryEnergy.YearEndDefault,
            lower_bound_techno=1.0e-6,
            upper_bound_techno=100.0,
            techno_dict=GlossaryEnergy.DEFAULT_TECHNO_DICT,
            bspline=True,
            invest_discipline=INVEST_DISCIPLINE_DEFAULT,
            energy_invest_input_in_abs_value=True,
            execution_engine=None,
            main_study: bool = True,
    ):
        self.main_study = main_study
        self.year_start = year_start
        self.year_end = year_end
        self.energy_list = None
        self.ccs_list = None
        self.dict_technos = None
        self.bspline = bspline
        self.invest_discipline = invest_discipline
        self.energy_invest_input_in_abs_value = energy_invest_input_in_abs_value
        self.lower_bound_techno = lower_bound_techno
        self.upper_bound_techno = upper_bound_techno
        self.energy_usecase = None

        # -- Call class constructor after attributes have been set for setup_process usage
        super().__init__(__file__, execution_engine=execution_engine)

        self.study_v0 = Study_v0(
            year_start=self.year_start,
            year_end=self.year_end,
            main_study=self.main_study,
            bspline=self.bspline,
            execution_engine=execution_engine,
            invest_discipline=self.invest_discipline,
            energy_invest_input_in_abs_value=self.energy_invest_input_in_abs_value,
            techno_dict=techno_dict,
        )
        self.sub_study_path_dict = self.study_v0.sub_study_path_dict
        self.test_post_procs = True

    def setup_objectives(self):
        func_df = Study_v0.setup_objectives(self)
        return func_df

    def setup_constraints(self):
        func_df = Study_v0.setup_constraints(self)
        return func_df

    def setup_usecase(self, study_folder_path=None):
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
            f'{self.study_name}.inner_mda_name': 'MDAGSNewton',
        }
        values_dict_list.append(numerical_values_dict)

        return values_dict_list


if '__main__' == __name__:
    uc_cls = Study()
    uc_cls.load_data()
    uc_cls.run()
