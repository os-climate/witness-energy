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
from os.path import dirname

import numpy as np
import pandas as pd
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tests.core.abstract_jacobian_unit_test import (
    AbstractJacobianUnittest,
)

from energy_models.glossaryenergy import GlossaryEnergy


class TestInvestmentProfileBuilderDisc(AbstractJacobianUnittest):
    """
    Resources prices test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.override_dump_jacobian = True  # let that to True
        self.name = 'Test'
        self.model_name = 'investments profile'
        self.columns_names = [GlossaryEnergy.clean_energy, GlossaryEnergy.fossil, GlossaryEnergy.carbon_capture]
        self.n_profiles = 4
        self.coeff_jacobian = [f'{self.name}.{self.model_name}.coeff_{i}' for i in range(self.n_profiles)]
        self.year_min = 2020
        self.year_max = 2025
        self.years = np.arange(self.year_min, self.year_max + 1)

        self.inputs_dict = {
            f'{self.name}.{self.model_name}.column_names': self.columns_names,
            f'{self.name}.{self.model_name}.n_profiles': self.n_profiles,
            f'{self.name}.{self.model_name}.{GlossaryEnergy.EXPORT_PROFILES_AT_POLES}': False,

        }

        def df_generator(years):
            df = pd.DataFrame({
                **{GlossaryEnergy.Years: years},
                **dict(zip(self.columns_names, np.random.rand(len(self.columns_names))))
            })
            return df

        self.inputs_dict.update({
            f"{self.name}.{self.model_name}.coeff_{i}": np.random.uniform(0, 15) for i in range(self.n_profiles)
        })

        self.inputs_dict.update({
            f"{self.name}.{self.model_name}.df_{i}": df_generator(self.years) for i in range(self.n_profiles)
        })
        pass

    def tearDown(self):
        pass

    def analytic_grad_entry(self):
        return [
            self.test_01_output_invest_mix,
            self.test_02_output_at_poles,
            ]

    def test_01_output_invest_mix(self):
        '''
        Test the gradient of the invest profile exported into invest_mix
        '''

        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_invest': f'{self.name}.{self.model_name}', }
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.investments.disciplines.investments_profile_builder_disc.InvestmentsProfileBuilderDisc'

        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        self.ee.load_study_from_input_dict(self.inputs_dict)

        self.ee.execute()

        disc = self.ee.root_process.proxy_disciplines[0].discipline_wrapp.discipline
        self.check_jacobian(derr_approx='complex_step',
                            inputs=self.coeff_jacobian,
                            outputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.invest_mix}'],
                            local_data=disc.local_data,
                            location=dirname(__file__),
                            discipline=disc,
                            filename='jacobian_investments_profile_builder_disc_all_years.pkl', threshold=1e-5, )

    def test_02_output_at_poles(self):
        '''
        Test the gradient of the invest profile exported into mix_array at the poles
        '''
        inputs_dict = self.inputs_dict.copy()
        nb_poles = 3
        inputs_dict.update({
            f'{self.name}.{self.model_name}.nb_poles': nb_poles,
            f'{self.name}.{self.model_name}.{GlossaryEnergy.EXPORT_PROFILES_AT_POLES}': True,

        })

        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_invest': f'{self.name}.{self.model_name}', }
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.investments.disciplines.investments_profile_builder_disc.InvestmentsProfileBuilderDisc'

        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        outputs = [f'{self.name}.{self.model_name}.{col}_array_mix' for col in self.columns_names]

        disc = self.ee.root_process.proxy_disciplines[0].discipline_wrapp.discipline
        self.check_jacobian(derr_approx='complex_step',
                            inputs=self.coeff_jacobian,
                            outputs=outputs,
                            local_data=disc.local_data,
                            location=dirname(__file__),
                            discipline=disc,
                            filename='jacobian_investments_profile_builder_disc_poles.pkl', threshold=1e-5, )
