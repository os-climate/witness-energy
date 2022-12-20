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
from os.path import join, dirname
from sostrades_core.execution_engine.execution_engine import ExecutionEngine

from energy_models.sos_processes.energy.MDO_subprocesses.energy_optim_sub_process.usecase import Study
from sostrades_core.tests.core.abstract_jacobian_unit_test import AbstractJacobianUnittest


class EnergyMixTestCase(AbstractJacobianUnittest):
    """
    Design variables test class
    """
    #AbstractJacobianUnittest.DUMP_JACOBIAN = True

    def analytic_grad_entry(self):
        return [
            self.test_01_check_gradient_design_var_with_open_loop,
            self.test_02_check_gradient_with_open_loop_lagrangian_objective_vs_all_design_vars,
            self.test_03_check_open_loop_gradient_until_2100,
        ]

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.year_start = 2020
        self.year_end = 2050
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.name = 'Test'
        self.ee = ExecutionEngine(self.name)
        repo = 'energy_models.sos_processes.energy.MDO_subprocesses'
        builder = self.ee.factory.get_builder_from_process(
            repo, 'energy_optim_sub_process')

        self.ee.factory.set_builders_to_coupling_builder(builder)
        self.ee.configure()
        usecase = Study(execution_engine=self.ee)
        usecase.study_name = self.name
        values_dict = usecase.setup_usecase()
        values_dict[0][f'{self.name}.EnergyModelEval.chain_linearize'] = True

        self.ee.display_treeview_nodes()
        full_values_dict = {}
        for dict_v in values_dict:
            full_values_dict.update(dict_v)
        self.ee.load_study_from_input_dict(full_values_dict)
        self.usecase = usecase

    def test_01_check_gradient_design_var_with_open_loop(self):

        self.model_name = 'design_var_open_loop'
        disc_design_var = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.EnergyModelEval.DesignVariableDisc')[0]
        input_names = ['CO2_taxes_array']
        for energy in self.usecase.energy_list:
            energy_wo_dot = energy.replace('.', '_')
            input_names += [f'{energy}.{energy_wo_dot}_array_mix']
            for techno in self.usecase.dict_technos[energy]:
                techno_wo_dot = techno.replace('.', '_')
                input_names += [f'{energy}.{techno}.{energy_wo_dot}_{techno_wo_dot}_array_mix']
        input_full_names = [disc_design_var.get_var_full_name(
            inp, disc_design_var._data_in) for inp in input_names]
        output_names = list(disc_design_var.get_sosdisc_outputs().keys())

        output_full_names = [disc_design_var.get_var_full_name(
            out, disc_design_var._data_out) for out in output_names]

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.model_name}.pkl',
                            discipline=disc_design_var, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            inputs=input_full_names,
                            outputs=output_full_names, parallel=True)

    def test_02_check_gradient_with_open_loop_lagrangian_objective_vs_all_design_vars(self):

        self.model_name = 'lagrangian_obj_vs_design_var_open_loop'
        disc_open_loop = self.ee.root_process.proxy_disciplines[0]

        input_names = ['CO2_taxes_array']
        for energy in self.usecase.energy_list:
            energy_wo_dot = energy.replace('.', '_')
            input_names += [f'{energy}.{energy_wo_dot}_array_mix']
            for techno in self.usecase.dict_technos[energy]:
                techno_wo_dot = techno.replace('.', '_')
                input_names += [f'{energy}.{techno}.{energy_wo_dot}_{techno_wo_dot}_array_mix']
        input_full_names = [disc_open_loop.get_var_full_name(
            inp, disc_open_loop._data_in) for inp in input_names]

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.model_name}.pkl',
                            discipline=disc_open_loop, step=1.0e-16, derr_approx='complex_step', threshold=1e-12,
                            inputs=input_full_names,
                            outputs=[f'{self.name}.objective_lagrangian'], parallel=True)

    def test_03_check_open_loop_gradient_until_2100(self):

        self.model_name = 'lagrangian_obj_vs_design_var_open_loop_2100'

        self.ee = ExecutionEngine(self.name)
        repo = 'energy_models.sos_processes.energy.MDO_subprocesses'
        builder = self.ee.factory.get_builder_from_process(
            repo, 'energy_optim_sub_process')

        self.ee.factory.set_builders_to_coupling_builder(builder)
        self.ee.configure()
        usecase = Study(year_end=2100, execution_engine=self.ee)
        usecase.study_name = self.name
        values_dict = usecase.setup_usecase()
        values_dict[0][f'{self.name}.EnergyModelEval.chain_linearize'] = True

        self.ee.display_treeview_nodes()
        full_values_dict = {}
        for dict_v in values_dict:
            full_values_dict.update(dict_v)
        self.ee.load_study_from_input_dict(full_values_dict)

        disc_open_loop = self.ee.root_process.proxy_disciplines[0]

        input_names = ['CO2_taxes_array']
        for energy in self.usecase.energy_list:
            energy_wo_dot = energy.replace('.', '_')
            input_names += [f'{energy}.{energy_wo_dot}_array_mix']
            for techno in self.usecase.dict_technos[energy]:
                techno_wo_dot = techno.replace('.', '_')
                input_names += [f'{energy}.{techno}.{energy_wo_dot}_{techno_wo_dot}_array_mix']
        input_full_names = [disc_open_loop.get_var_full_name(
            inp, disc_open_loop._data_in) for inp in input_names]

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.model_name}.pkl',
                            discipline=disc_open_loop, step=1.0e-16, derr_approx='complex_step', threshold=1e-12,
                            inputs=input_full_names, outputs=[f'{self.name}.objective_lagrangian'], parallel=True)

    # def test_04_check_open_loop_gradient_until_2100(self):
    #
        # designvariable_name = "DesignVariableDisc"
        # func_manager_name = "FunctionManagerDisc"
        # self.name = 'Test'
        # self.ee = ExecutionEngine(self.name)
        # # retrieve energy process
        # chain_builders = self.ee.factory.get_builder_from_process(
        # 'energy_models.sos_processes.energy.MDA', 'energy_process_v0')
        #
        # # design variables builder
        # design_var_path = 'energy_models.core.design_variables_translation.design_var_disc.Design_Var_Discipline'
        # design_var_builder = self.ee.factory.get_builder_from_module(
        # f'{designvariable_name}', design_var_path)
        # chain_builders.append(design_var_builder)
        #
# #         # function manager builder
        # fmanager_path = 'sos_trades_core.execution_engine.func_manager.func_manager_disc.FunctionManagerDisc'
        # fmanager_builder = self.ee.factory.get_builder_from_module(
        # f'{func_manager_name}', fmanager_path)
        # chain_builders.append(fmanager_builder)
        #
        # # modify namespaces defined in the child process
        #
        # ns_dict = {'ns_energy_mix': f'{self.ee.study_name}.EnergyMix',
        # 'ns_functions': f'{self.ee.study_name}.EnergyMix',
        # 'ns_optim': f'{self.ee.study_name}'}
        # self.ee.ns_manager.add_ns_def(ns_dict)
        #
        # self.ee.factory.set_builders_to_coupling_builder(
        # chain_builders)
        #
        # self.ee.configure()
        # usecase = Study_2100()
        # usecase.study_name = self.name
        # values_dict = usecase.setup_usecase()
        # values_dict[0][f'{self.name}.chain_linearize'] = True
        # self.ee.display_treeview_nodes()
        #
        # years = np.arange(2020, 2101)
        # self.energy_mix_invest_df, self.technology_mix_invest_df = usecase.get_investments_mix(
        # years)
        #
        # self.energy_list = values_dict[0][f'{self.name}.energy_list']
        # invest_arrays_dict = {}
        # for energy in self.energy_list:
        # invest_arrays_dict[f'{self.name}.DesignVariableDisc.{energy}.{energy}_array_mix'] = self.energy_mix_invest_df[energy].values
        # for technology in values_dict[0][f'{self.name}.EnergyMix.{energy}.technologies_list']:
        # invest_arrays_dict[f'{self.name}.DesignVariableDisc.{energy}.{technology}.{energy}_{technology}_array_mix'] = self.technology_mix_invest_df[energy][technology].values
        #
        # usecase_MDA = StudyMDA(execution_engine=self.ee)
        # usecase_MDA.study_name = self.name
        # values_dict_MDA = usecase_MDA.setup_usecase()
        # values_dict[0][f'{self.name}.{func_manager_name}.function_df'] = values_dict_MDA[
        # -2][f'{self.name}.EnergyModelEval.{func_manager_name}.function_df']
        # for dict_v in values_dict:
        # dict_v = {key.replace('Test.EnergyModelEval', 'Test')                      : value for key, value in dict_v.items()}
        # #dict_v['Test.linearization_mode'] = 'adjoint'
        # dict_v.update(invest_arrays_dict)
        # self.ee.load_study_from_input_dict(dict_v)
        #
        # # self.ee.execute()
        #
        # disc_design_var = self.ee.dm.get_disciplines_with_name(
        # f'{self.name}.DesignVariableDisc')[0]
        # unwanted_inputs = ['export_xvect', 'energy_list', 'year_start', 'year_end',
        # 'linearization_mode', 'cache_type', 'cache_file_path']
        # unwanted_inputs.extend(list(disc_design_var.NUM_DESC_IN.keys()))
        # input_names = list(disc_design_var.get_sosdisc_inputs().keys())
        # input_names = [
        # inp for inp in input_names if inp not in unwanted_inputs]
        # input_names = [
        # inp for inp in input_names if not inp.endswith('technologies_list')]
        # input_full_names = [disc_design_var.get_var_full_name(
        # inp, disc_design_var._data_in) for inp in input_names]
        #
        # disc_open_loop = self.ee.root_process
        #
        # techno_elec_list = ['WindOffshore', 'WindOnshore', 'Hydropower', 'SolarPv', 'SolarThermal',
        # 'Nuclear', 'CombinedCycleGasTurbine', 'GasTurbine', 'Geothermal', 'CoalGen']
        # output_prices = [
        # f'Test.EnergyMix.electricity.{techno}.techno_prices' for techno in techno_elec_list]
        # output_prod = [
        # f'Test.EnergyMix.electricity.{techno}.techno_production' for techno in techno_elec_list]
        # output_cons = [
        # f'Test.EnergyMix.electricity.{techno}.techno_consumption' for techno in techno_elec_list]
        # output_emission = [
        # f'Test.EnergyMix.electricity.{techno}.CO2_emissions' for techno in techno_elec_list]
        #
        # output_energy = ['Test.EnergyMix.electricity.energy_prices', 'Test.EnergyMix.electricity.energy_consumption',
        # 'Test.EnergyMix.electricity.energy_production', 'Test.EnergyMix.electricity.CO2_emissions']
        # output_list = output_prices + output_prod + \
        # output_emission + output_cons + output_energy
        #
# #['years', 'methane', 'hydrogen.gaseous_hydrogen', 'biogas', 'electricity', 'solid_fuel','liquid_fuel', 'BioDiesel', 'syngas', 'biomass_dry', 'carbon_capture','carbon_storage']
        # self.check_jacobian(location=dirname(__file__), filename='jacobian_energymix_output_vs_design_vars_2100.pkl',
        # discipline=disc_open_loop, step=1.0e-16, derr_approx='complex_step', threshold=1e-12,
        # inputs=input_full_names, outputs=['Test.objective_lagrangian'],)


if '__main__' == __name__:
    cls = EnergyMixTestCase()
    cls.test_01_check_gradient_design_var_with_open_loop()
