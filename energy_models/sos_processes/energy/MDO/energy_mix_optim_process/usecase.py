'''
Copyright 2024 Capgemini
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
from sostrades_core.execution_engine.func_manager.func_manager_disc import (
    FunctionManagerDisc,
)
from sostrades_core.study_manager.study_manager import StudyManager

from energy_models.core.energy_study_manager import DEFAULT_TECHNO_DICT
from energy_models.sos_processes.energy.MDA.energy_mix_optim_sub_process.usecase import (
    Study as subStudy,
)

INVEST_DISC_NAME = 'InvestmentDistribution'


class Study(StudyManager):
    def __init__(
            self,
            file_path=__file__,
            execution_engine=None,
            run_usecase=False,
            use_utilisation_ratio: bool = False
    ):
        super().__init__(
            file_path=file_path,
            execution_engine=execution_engine,
            run_usecase=run_usecase
        )
        self.optim_name = 'MDO'
        self.techno_dict = DEFAULT_TECHNO_DICT
        self.use_utilisation_ratio = use_utilisation_ratio

    def setup_usecase(self, study_folder_path=None):
        data_usecase = subStudy(techno_dict=self.techno_dict, use_utilisation_ratio=self.use_utilisation_ratio)
        data_usecase.study_name = f'{self.study_name}.{self.optim_name}'
        data = data_usecase.setup_usecase()

        values_mdo = {
            f'{self.study_name}.{self.optim_name}.algo': 'L-BFGS-B',
            f'{self.study_name}.{self.optim_name}.formulation': 'DisciplinaryOpt',
            f'{self.study_name}.{self.optim_name}.objective_name': FunctionManagerDisc.OBJECTIVE_LAGR,
            f'{self.study_name}.{self.optim_name}.max_iter': 200,
            f'{self.study_name}.{self.optim_name}.differentiation_method': 'user',
            f"{self.study_name}.sub_mda_class": "GSPureNewtonMDA",
        }
        data.append(values_mdo)
        return data


if '__main__' == __name__:
    uc_cls = Study(run_usecase=True)
    uc_cls.test()
# uc_cls.run()
