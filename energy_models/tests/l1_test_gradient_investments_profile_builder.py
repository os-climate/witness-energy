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
import unittest
import numpy as np
import pandas as pd
from os.path import dirname

from energy_models.glossaryenergy import GlossaryEnergy
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tests.core.abstract_jacobian_unit_test import AbstractJacobianUnittest


class TestInvestmentProfileBuilderDisc(AbstractJacobianUnittest):
    """
    Resources prices test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''

        pass

    def tearDown(self):
        pass

    def analytic_grad_entry(self):
        return [
            self.test_01_run,
            ]


    def test_01_run(self, energy_list=None):
        '''
        The objective is to test output energy price and energy co2 emissions when
        one techno has low prod compare to the other
        We want to kill the low influence to reduce gradients
        '''
        self.name = 'Test'
        self.model_name = 'investments profile'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.investments.disciplines.investments_profile_builder_disc.InvestmentsProfileBuilderDisc'

        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        columns_names = [GlossaryEnergy.renewable, GlossaryEnergy.fossil, GlossaryEnergy.carbon_capture]
        n_profiles = 4
        inputs_dict = {
            f'{self.name}.{self.model_name}.column_names': columns_names,
            f'{self.name}.{self.model_name}.n_profiles': n_profiles,
        }

        def df_generator():
            year_min = 2020
            year_max = 2025
            years = np.arange(year_min, year_max + 1)
            df = pd.DataFrame({
                **{GlossaryEnergy.Years: years},
                **dict(zip(columns_names, np.random.rand(len(columns_names))))
            })
            return df

        inputs_dict.update({
            f"{self.name}.{self.model_name}.coeff_{i}": np.random.uniform(0, 15) for i in range(n_profiles)
        })

        inputs_dict.update({
            f"{self.name}.{self.model_name}.df_{i}": df_generator() for i in range(n_profiles)
        })

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        coeff_jacobian = [f'{self.name}.{self.model_name}.coeff_{i}' for i in range(n_profiles)]

        disc = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline
        self.override_dump_jacobian = True
        self.check_jacobian(derr_approx='complex_step',
                            inputs=coeff_jacobian,
                            outputs=[f'{self.name}.{self.model_name}.invest_profile'],
                            local_data=disc.local_data,
                            location=dirname(__file__),
                            discipline=disc,
                            filename=f'jacobian_investments_profile_builder_disc.pkl', threshold=1e-5, )
