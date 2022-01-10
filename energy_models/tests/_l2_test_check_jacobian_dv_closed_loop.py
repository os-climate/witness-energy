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
import unittest
from sos_trades_core.execution_engine.execution_engine import ExecutionEngine
from energy_models.sos_processes.energy.MDO_subprocesses.energy_optim_sub_process_mda.usecase import Study
from os.path import join, dirname
from sos_trades_core.tests.core.abstract_jacobian_unit_test import AbstractJacobianUnittest


class TestCheckJacobian(AbstractJacobianUnittest):

    def analytic_grad_entry(self):
        return [
            self.test_01_gradient_objective_wrt_design_var_on_energy_sub_process_mda_closed_loop,
        ]

    def test_01_gradient_objective_wrt_design_var_on_energy_sub_process_mda_closed_loop(self):

        self.name = 'Test'
        self.check_jack = 'Check_jacobian'
        self.ee = ExecutionEngine(self.name)

        mod_path = 'sos_trades_core.sos_disciplines.check_jacobian_discipline.CheckJacobianDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.check_jack, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)
        self.ee.configure()

        usecase = Study(execution_engine=self.ee)
        usecase.study_name = f'{self.name}.{self.check_jack}'
        values_dict = usecase.setup_usecase()

        design_var_path = f'{self.name}.{self.check_jack}.{usecase.coupling_name}.DesignVariableDisc'
        design_var = [design_var_path + var for var in ['.methane.methane_array_mix',
                                                        '.hydrogen.gaseous_hydrogen.hydrogen_gaseous_hydrogen_array_mix',
                                                        '.biogas.biogas_array_mix',
                                                        '.electricity.electricity_array_mix',
                                                        '.solid_fuel.solid_fuel_array_mix',
                                                        '.liquid_fuel.liquid_fuel_array_mix',
                                                        '.BioDiesel.BioDiesel_array_mix',
                                                        '.syngas.syngas_array_mix',
                                                        '.biomass_dry.biomass_dry_array_mix',
                                                        '.carbon_capture.carbon_capture_array_mix',
                                                        '.carbon_storage.carbon_storage_array_mix',
                                                        ]]

        inputs_dict = {f'{self.name}.{self.check_jack}.repo_name': 'energy_models.sos_processes.energy.MDO_subprocesses',
                       f'{self.name}.{self.check_jack}.process_name': 'energy_optim_sub_process_mda',
                       f'{self.name}.{self.check_jack}.load_jac_path': join(dirname(__file__), 'jacobian_pkls', f'jacobian_obj_dv_closed_loop.pkl'),
                       f'{self.name}.{self.check_jack}.inputs': design_var,
                       f'{self.name}.{self.check_jack}.outputs': [f'{self.name}.{self.check_jack}.objective_lagrangian'],
                       f'{self.name}.{self.check_jack}.derr_approx': 'complex_step',
                       f'{self.name}.{self.check_jack}.step': 1e-15}
        values_dict[0].update(inputs_dict)

        full_values_dict = {}
        for dict_v in values_dict:
            full_values_dict.update(dict_v)
        self.ee.load_study_from_input_dict(full_values_dict)

        check_jac_disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.check_jack}')[0]
        optim_disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.check_jack}.{usecase.coupling_name}')[0]
        mode_jac_keys = list(check_jac_disc.DESC_IN.keys())
        jac_inputs = check_jac_disc.get_sosdisc_inputs(
            mode_jac_keys, in_dict=True)

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_obj_dv_closed_loop.pkl',
                            discipline=optim_disc, step=1.0e-16, derr_approx='complex_step', threshold=1e-12,
                            inputs=jac_inputs['inputs'],
                            outputs=jac_inputs['outputs'],)

        # self.ee.execute()
