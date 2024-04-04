'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2023/11/09 Copyright 2023 Capgemini

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

from pathlib import Path
from shutil import rmtree
from time import sleep

from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.sos_processes.energy.MDA.energy_process_v0_mda.usecase import Study
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tests.core.abstract_jacobian_unit_test import AbstractJacobianUnittest


class TestMDAAnalyticGradient(AbstractJacobianUnittest):
    """
    Energy process MDA test class
    """

    def analytic_grad_entry(self):
        return [
            self.test_01_check_gradient_with_newtonraphson,
        ]

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.dirs_to_del = []
        self.namespace = 'MyCase'
        self.study_name = f'{self.namespace}'

    def tearDown(self):

        for dir_to_del in self.dirs_to_del:
            sleep(0.5)
            if Path(dir_to_del).is_dir():
                rmtree(dir_to_del)
        sleep(0.5)

    def test_01_check_gradient_with_newtonraphson(self):

        self.name = 'Test'
        self.ee = ExecutionEngine(self.name)
        repo = 'energy_models.sos_processes.energy.MDA'
        builder = self.ee.factory.get_builder_from_process(
            repo, 'energy_process_v0_mda')

        self.ee.factory.set_builders_to_coupling_builder(builder)
        self.ee.configure()
        usecase = Study(execution_engine=self.ee, year_end=GlossaryEnergy.YearEndDefaultValueGradientTest)
        usecase.study_name = self.name
        values_dict = usecase.setup_usecase()

        values_dict[0][f'{usecase.study_name}.sub_mda_class'] = 'MDANewtonRaphson'
        values_dict[0][f'{usecase.study_name}.linearization_mode'] = 'adjoint'

        full_values_dict = {}
        for dict_v in values_dict:
            full_values_dict.update(dict_v)
        self.ee.load_study_from_input_dict(full_values_dict)

        self.ee.display_treeview_nodes()
        self.ee.execute()

        energy_prices_nr = self.ee.dm.get_value(
            f'{usecase.study_name}.EnergyMix.{GlossaryEnergy.EnergyPricesValue}')

        ####################
        self.name = 'Test2'
        self.ee2 = ExecutionEngine(self.name)
        repo = 'energy_models.sos_processes.energy.MDA'
        builder2 = self.ee2.factory.get_builder_from_process(
            repo, 'energy_process_v0_mda')

        self.ee2.factory.set_builders_to_coupling_builder(builder2)
        self.ee2.configure()
        usecase = Study(execution_engine=self.ee2, year_end=GlossaryEnergy.YearEndDefaultValueGradientTest)
        usecase.study_name = self.name
        values_dict = usecase.setup_usecase()

        full_values_dict = {}
        for dict_v in values_dict:
            full_values_dict.update(dict_v)
        self.ee2.load_study_from_input_dict(full_values_dict)

        self.ee2.display_treeview_nodes()
        self.ee2.execute()
        energy_prices_jac = self.ee2.dm.get_value(
            f'{usecase.study_name}.EnergyMix.{GlossaryEnergy.EnergyPricesValue}')

        diff = energy_prices_jac - energy_prices_nr

        # diff.to_csv('diff_energy.csv')


if '__main__' == __name__:
    cls = TestMDAAnalyticGradient()
    cls.test_01_check_gradient_with_newtonraphson()
