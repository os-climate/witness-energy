'''
Copyright 2022 Airbus SAS
Modifications on 23/11/2023 Copyright 2023 Capgemini

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
import unittest
from copy import deepcopy

from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.sos_processes.energy.MDA.energy_process_v0.usecase import Study as StudyMDA
from gemseo.utils.compare_data_manager_tooling import compare_dict
from sostrades_core.execution_engine.execution_engine import ExecutionEngine


class DiscDoubleRunTestCase(unittest.TestCase):
    """
    Discipline double run test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.year_start = GlossaryEnergy.YeartStartDefault
        self.year_end = 2050

    def test_01_run_disc_twice_and_compare_dm(self):

        self.name = 'Test'
        self.model_name = 'design_var_open_loop'
        self.ee = ExecutionEngine(self.name)
        repo = 'energy_models.sos_processes.energy.MDA'
        builder = self.ee.factory.get_builder_from_process(
            repo, 'energy_process_v0')

        self.ee.factory.set_builders_to_coupling_builder(builder)
        self.ee.configure()
        usecase = StudyMDA(execution_engine=self.ee)
        usecase.study_name = self.name
        values_dict = usecase.setup_usecase()
        self.ee.display_treeview_nodes()
        dict_aggr = {}
        for dict_v in values_dict:
            dict_aggr.update(dict_v)
        numerical_values_dict = {
            f'{self.name}.epsilon0': 1.0,
            f'{self.name}.max_mda_iter': 1,
            f'{self.name}.tolerance': 1.0e-7,
            f'{self.name}.n_processes': 1,
            f'{self.name}.linearization_mode': 'adjoint',
            f'{self.name}.sub_mda_class': 'MDANewtonRaphson'}
        dict_aggr.update(numerical_values_dict)
        self.ee.load_study_from_input_dict(dict_aggr)
        proxy_factory = self.ee.execute()
        local_data = proxy_factory.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline.local_data
        # self.ee.root_process.pre_run_mda()
        output_error = ''
        test_passed = True
        for disc in self.ee.factory.proxy_disciplines:
            # print(disc.get_disc_full_name())
            if disc.get_disc_full_name() == 'Test.CCUS.carbon_capture':
                local_data = disc.mdo_discipline_wrapp.mdo_discipline.local_data
                # RUN 1
                local_data1 = deepcopy(disc.mdo_discipline_wrapp.mdo_discipline.execute(deepcopy(local_data)))
                # RUN 2
                local_data2 = deepcopy(disc.mdo_discipline_wrapp.mdo_discipline.execute(deepcopy(local_data)))
                # COMPARE DICT
                dict_error = {}
                compare_dict(local_data1, local_data2, '', dict_error)
                if dict_error != {}:
                    test_passed = False
                    for error in dict_error:
                        output_error += f'Error while runing twice { usecase }:\n'
                        output_error += f'Mismatch in {error} for disc {disc.get_disc_full_name()}: {dict_error.get(error)}'
                        output_error += '\n---------------------------------------------------------\n'
        if not test_passed:
            raise Exception(f'{output_error}')
