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

from sos_trades_core.study_manager.study_manager import StudyManager
from sos_trades_core.tools.post_processing.post_processing_factory import PostProcessingFactory
from energy_models.sos_processes.energy.MDO.energy_optim_process.usecase import Study as energy_optim_usecase


class Study(StudyManager):

    def __init__(self, year_start=2020, year_end=2050, time_step=1, run_usecase=False, execution_engine=None):
        super().__init__(__file__, run_usecase=run_usecase, execution_engine=execution_engine)
        self.year_start = year_start
        self.year_end = year_end
        self.time_step = time_step

    def setup_usecase(self):

        optim_usecase = energy_optim_usecase(
            self.year_start, self.year_end, self.time_step, execution_engine=self.execution_engine)

        self.scatter_scenario = 'Multi-scenarios'
        # Set public values at a specific namespace
        optim_usecase.study_name = f'{self.study_name}.{self.scatter_scenario}'
        setup_data_list = optim_usecase.setup_usecase()
        values_dict = {}

        # set scenario_list and alpha for each scenario
        scenario_list = []
        alpha_list = np.linspace(5, 95, 10, endpoint=True) / 100.0
        for i, alpha_i in enumerate(alpha_list):
            scenario_i = 'scenario_\u03B1=%.2f' % alpha_i
            scenario_i = scenario_i.replace('.', ',')
            scenario_list.append(scenario_i)
            values_dict[f'{self.study_name}.{self.scatter_scenario}.{scenario_i}.{optim_usecase.optim_name}.{optim_usecase.coupling_name}.alpha'] = alpha_i
        values_dict[f'{self.study_name}.{self.scatter_scenario}.scenario_list'] = scenario_list

        # get inputs from energy_optim_process usecase
        for scenario in scenario_list:
            optim_usecase.study_name = f'{self.study_name}.{self.scatter_scenario}.{scenario}'
            setup_data_list.extend(optim_usecase.setup_usecase())

        # set optimization inputs
        values_dict[f'{self.study_name}.max_mda_iter'] = 2
        values_dict[f'{self.study_name}.sub_mda_class'] = 'MDANewtonRaphson'
        for scenario in scenario_list:
            values_dict[f'{self.study_name}.{self.scatter_scenario}.{scenario}.{optim_usecase.optim_name}.max_iter'] = 2
            values_dict[f'{self.study_name}.{self.scatter_scenario}.{scenario}.max_mda_iter'] = 2
            values_dict[f'{self.study_name}.{self.scatter_scenario}.{scenario}.{optim_usecase.optim_name}.{optim_usecase.coupling_name}.max_mda_iter'] = 2
            values_dict[f'{self.study_name}.{self.scatter_scenario}.{scenario}.sub_mda_class'] = 'MDANewtonRaphson'

        return setup_data_list + [values_dict]


if '__main__' == __name__:
    uc_cls = Study()
    uc_cls.load_data()
    uc_cls.run()

#     ppf = PostProcessingFactory()
#     for disc in uc_cls.execution_engine.root_process.sos_disciplines:
#         if disc.sos_name == 'Post-processing':
#             filters = ppf.get_post_processing_filters_by_discipline(
#                 disc)
#             graph_list = ppf.get_post_processing_by_discipline(
#                 disc, filters, as_json=False)
#
#             for graph in graph_list:
#                 graph.to_plotly().show()
