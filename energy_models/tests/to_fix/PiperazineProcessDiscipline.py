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
import pickle
from os.path import dirname

from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tests.core.abstract_jacobian_unit_test import (
    AbstractJacobianUnittest,
)


class MyGeneratedTest(AbstractJacobianUnittest):

    def analytic_grad_entry(self):
        return []

    def test_execute(self):
        with open('data\energy_models_models_carbon_capture_flue_gas_capture_piperazine_process_piperazine_process_disc_PiperazineProcessDiscipline.pkl', 'rb') as f:
            file_dict = pickle.load(f)
            ns_dict = file_dict['ns_dict']
            mod_path = file_dict['mod_path']
            model_name = file_dict['model_name']
            values_dict = file_dict['values_dict']
            coupling_inputs = file_dict['coupling_inputs']
            coupling_ouputs = file_dict['coupling_outputs']

        self.name = 'jacobianIsolatedDiscTest.MDO.MDA.CCUS.carbon_capture.flue_gas_capture'
        self.ee = ExecutionEngine(self.name)

        self.ee.ns_manager.add_ns_def(ns_dict)

        builder = self.ee.factory.get_builder_from_module(
            model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        self.ee.load_study_from_input_dict(values_dict)

        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].discipline_wrapp.discipline

        self.check_jacobian(location=dirname(__file__), filename='jacobianIsolatedDiscTest_MDO_MDA_CCUS_carbon_capture_flue_gas_capture_PiperazineProcess.pkl',
                            discipline=disc_techno, step=1e-15, derr_approx='complex_step', local_data = disc_techno.local_data,
                            inputs=coupling_inputs,
                            outputs=coupling_ouputs)
    