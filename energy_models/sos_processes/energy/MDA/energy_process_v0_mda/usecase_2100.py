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

from sos_trades_core.study_manager.study_manager import StudyManager

from energy_models.sos_processes.energy.MDA.energy_process_v0.usecase_2100 import Study as Study_v0
from energy_models.core.energy_study_manager import DEFAULT_TECHNO_DICT
from energy_models.core.energy_process_builder import INVEST_DISCIPLINE_DEFAULT


class Study(StudyManager):

    def __init__(self, year_start=2020, year_end=2050, time_step=1, lower_bound_techno=1.0e-6, upper_bound_techno=100., techno_dict=DEFAULT_TECHNO_DICT, bspline=True, invest_discipline=INVEST_DISCIPLINE_DEFAULT, execution_engine=None):

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

        #-- Call class constructor after attributes have been set for setup_process usage
        super().__init__(__file__, execution_engine=execution_engine)

        self.study_v0 = Study_v0(
            self.year_start, self.year_end, self.time_step, main_study=False, bspline=self.bspline, execution_engine=execution_engine,
            invest_discipline=self.invest_discipline, techno_dict=techno_dict)
        self.sub_study_path_dict = self.study_v0.sub_study_path_dict

    def setup_usecase(self):

        values_dict_list = []

        study_v0 = Study_v0(
            self.year_start, self.year_end, self.time_step, bspline=self.bspline, execution_engine=self.execution_engine)
        study_v0.study_name = self.study_name
        invest_list = study_v0.setup_usecase()
        values_dict_list.extend(invest_list)
        self.energy_list = study_v0.energy_list
        self.dspace = study_v0.dspace
        self.dict_technos = study_v0.dict_technos
        numerical_values_dict = {
            f'{self.study_name}.epsilon0': 1.0,
            f'{self.study_name}.max_mda_iter': 50,
            f'{self.study_name}.tolerance': 1.0e-7,
            f'{self.study_name}.n_processes': 1,
            f'{self.study_name}.linearization_mode': 'adjoint',
            f'{self.study_name}.sub_mda_class': 'MDANewtonRaphson'}
        values_dict_list.append(numerical_values_dict)

        return values_dict_list


if '__main__' == __name__:
    uc_cls = Study()
    uc_cls.load_data()
    uc_cls.run()
