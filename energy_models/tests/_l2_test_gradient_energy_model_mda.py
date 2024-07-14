'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2024/06/24 Copyright 2023 Capgemini

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
from collections import defaultdict
from os.path import dirname, join
from pathlib import Path
from shutil import rmtree
from time import sleep

import numpy as np
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.study_manager.base_study_manager import BaseStudyManager
from sostrades_core.tests.core.abstract_jacobian_unit_test import (
    AbstractJacobianUnittest,
)
from sostrades_core.tools.rw.load_dump_dm_data import DirectLoadDump

from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.sos_processes.energy.MDA.energy_process_v0.usecase import (
    Study as Study_open,
)
from energy_models.sos_processes.energy.MDA.energy_process_v0_mda.usecase import (
    Study as Study_MDA,
)


class TestMDAAnalyticGradient(AbstractJacobianUnittest):
    """
    SoSDiscipline test class
    """

    def analytic_grad_entry(self):
        return [
            self.test_01_check_gradient_of_price_vs_price_open_loop,
            self.test_02_check_gradient_price_vs_invests,
            self.test_03_check_gradient_of_price_vs_co2_emissions_open_loop,
            self.test_04_check_gradient_energymixoutputs_vs_energy_investment,
            self.test_05_check_gradient_open_loop_after_MDA_results,
            self.test_06_check_gradient_energymixoutputs_vs_energy_mixes

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

    def test_01_check_gradient_of_price_vs_price_open_loop(self):

        self.name = 'Test'
        self.ee = ExecutionEngine(self.name)
        repo = 'energy_models.sos_processes.energy.MDA'
        builder = self.ee.factory.get_builder_from_process(
            repo, 'energy_process_v0')

        self.ee.factory.set_builders_to_coupling_builder(builder)
        self.ee.configure()
        usecase = Study_open(execution_engine=self.ee)
        usecase.study_name = self.name
        values_dict = usecase.setup_usecase()

        values_dict[0][f'{usecase.study_name}.chain_linearize'] = 'True'
        self.ee.display_treeview_nodes()
        full_values_dict = {}
        for dict_v in values_dict:
            full_values_dict.update(dict_v)
        self.ee.load_study_from_input_dict(full_values_dict)

        disc_mda = self.ee.root_process
        output_columns = [GlossaryEnergy.methane, f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}',
                          GlossaryEnergy.biogas, GlossaryEnergy.electricity, GlossaryEnergy.solid_fuel,
                          GlossaryEnergy.liquid_fuel, GlossaryEnergy.biodiesel, GlossaryEnergy.syngas,
                          GlossaryEnergy.biomass_dry, GlossaryEnergy.carbon_capture,
                          GlossaryEnergy.carbon_storage]

        output_prices = [
            f'{self.name}.EnergyMix.{energy}.{GlossaryEnergy.StreamPricesValue}' for energy in output_columns]
        self.check_jacobian(location=dirname(__file__), filename='jacobian_open_loop_price_vs_price_test.pkl',
                            discipline=disc_mda, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc_mda.local_data,
                            inputs=[f'{self.name}.EnergyMix.syngas.SMR.invest_level'],
                            outputs=output_prices + [f'{self.name}.EnergyMix.energy_mean_price'], parallel=True)

    def test_02_check_gradient_price_vs_invests(self):

        self.name = 'Test'
        self.ee = ExecutionEngine(self.name)
        repo = 'energy_models.sos_processes.energy.MDA'
        builder = self.ee.factory.get_builder_from_process(
            repo, 'energy_process_v0_mda')

        self.ee.factory.set_builders_to_coupling_builder(builder)
        self.ee.configure()
        usecase = Study_MDA(execution_engine=self.ee)
        usecase.study_name = self.name
        values_dict = usecase.setup_usecase()

        values_dict[0][f'{usecase.study_name}.tolerance'] = 1.0e-8
        values_dict[0][f'{usecase.study_name}.chain_linearize'] = True
        values_dict[0][f'{usecase.study_name}.sub_mda_class'] = 'MDAGaussSeidel'
        values_dict[0][f'{usecase.study_name}.linearization_mode'] = 'adjoint'
        self.ee.display_treeview_nodes()
        full_values_dict = {}
        for dict_v in values_dict:
            full_values_dict.update(dict_v)
        self.ee.load_study_from_input_dict(full_values_dict)

        disc_mda = self.ee.root_process
        output_columns = [GlossaryEnergy.methane, f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}',
                          GlossaryEnergy.biogas, GlossaryEnergy.electricity, GlossaryEnergy.solid_fuel,
                          GlossaryEnergy.liquid_fuel, GlossaryEnergy.biodiesel, GlossaryEnergy.syngas,
                          GlossaryEnergy.biomass_dry, GlossaryEnergy.carbon_capture,
                          GlossaryEnergy.carbon_storage]

        output_prices = [
            f'{self.name}.EnergyMix.{energy}.{GlossaryEnergy.StreamPricesValue}' for energy in output_columns]

        self.check_jacobian(location=dirname(__file__), filename='jacobian_open_loop_price_vs_invest.pkl',
                            discipline=disc_mda, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc_mda.local_data,
                            inputs=[
                                f'{self.name}.EnergyMix.energy_investment'],
                            outputs=output_prices + [f'{self.name}.EnergyMix.{GlossaryEnergy.StreamPricesValue}'],
                            parallel=True)

    def test_03_check_gradient_of_price_vs_co2_emissions_open_loop(self):

        self.name = 'Test'
        self.ee = ExecutionEngine(self.name)
        repo = 'energy_models.sos_processes.energy.MDA'
        builder = self.ee.factory.get_builder_from_process(
            repo, 'energy_process_v0')

        self.ee.factory.set_builders_to_coupling_builder(builder)
        self.ee.configure()
        usecase = Study_open(execution_engine=self.ee)
        usecase.study_name = self.name
        values_dict = usecase.setup_usecase()

        # values_dict[0][f'{usecase.study_name}.chain_linearize'] = 'True'
        self.ee.display_treeview_nodes()
        full_values_dict = {}
        for dict_v in values_dict:
            full_values_dict.update(dict_v)

        full_values_dict[f'{usecase.study_name}.tolerance_linear_solver_MDO'] = 1.0e-14
        full_values_dict[f'{usecase.study_name}.tolerance_linear_solver_MDO'] = 1.0e-14
        full_values_dict[f'{usecase.study_name}.linearization_mode'] = 'adjoint'
        full_values_dict[f'{usecase.study_name}.tolerance'] = 1.0e-12
        full_values_dict[f'{usecase.study_name}.max_mda_iter'] = 200
        full_values_dict[f'{usecase.study_name}.sub_mda_class'] = 'MDAGaussSeidel'
        self.ee.load_study_from_input_dict(full_values_dict)

        disc_mda = self.ee.root_process
        output_columns = [GlossaryEnergy.methane, f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}',
                          GlossaryEnergy.biogas, GlossaryEnergy.electricity, GlossaryEnergy.solid_fuel,
                          GlossaryEnergy.liquid_fuel, GlossaryEnergy.biodiesel, GlossaryEnergy.syngas,
                          GlossaryEnergy.biomass_dry, GlossaryEnergy.carbon_capture,
                          GlossaryEnergy.carbon_storage]

        output_prices = [
            f'{self.name}.EnergyMix.{energy}.{GlossaryEnergy.StreamPricesValue}' for energy in output_columns]

        hydrogen_techno = ['Electrolysis.SOEC', 'Electrolysis.PEM', GlossaryEnergy.PlasmaCracking, GlossaryEnergy.WaterGasShift
                           ]
        output_hydrogen_prices = [
            f'{self.name}.EnergyMix.hydrogen.gaseous_hydrogen.{techno}.{GlossaryEnergy.TechnoPricesValue}' for techno in
            hydrogen_techno]
        liquid_fuel_techno = ['Refinery', 'FischerTropsch']
        output_lf_prices = [
            f'{self.name}.EnergyMix.liquid_fuel.{techno}.{GlossaryEnergy.TechnoPricesValue}' for techno in
            liquid_fuel_techno]
        output_co2_emissions = [
            f'{self.name}.EnergyMix.{energy}.{GlossaryEnergy.CO2EmissionsValue}' for energy in output_columns[:-2]]
        self.check_jacobian(location=dirname(__file__), filename='jacobian_open_loop_price_vs_CO2_emissions.pkl',
                            discipline=disc_mda, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc_mda.local_data,
                            inputs=[f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}'],
                            outputs=output_prices + output_co2_emissions + output_hydrogen_prices + output_lf_prices +
                                    [f'{self.name}.EnergyMix.{GlossaryEnergy.StreamPricesValue}',
                                     f'{self.name}.EnergyMix.{GlossaryEnergy.StreamsCO2EmissionsValue}'], parallel=True)

    def test_04_check_gradient_energymixoutputs_vs_energy_investment(self):

        self.name = 'Test'
        self.ee = ExecutionEngine(self.name)
        repo = 'energy_models.sos_processes.energy.MDA'
        builder = self.ee.factory.get_builder_from_process(
            repo, 'energy_process_v0_mda')

        self.ee.factory.set_builders_to_coupling_builder(builder)
        self.ee.configure()
        usecase = Study_MDA(execution_engine=self.ee)
        usecase.study_name = self.name
        values_dict = usecase.setup_usecase()

        self.ee.display_treeview_nodes()
        full_values_dict = {}
        for dict_v in values_dict:
            full_values_dict.update(dict_v)

        full_values_dict[f'{usecase.study_name}.tolerance_linear_solver_MDO'] = 1.0e-14
        full_values_dict[f'{usecase.study_name}.tolerance_linear_solver_MDO'] = 1.0e-14
        full_values_dict[f'{usecase.study_name}.linearization_mode'] = 'adjoint'
        full_values_dict[f'{usecase.study_name}.tolerance'] = 1.0e-12
        full_values_dict[f'{usecase.study_name}.max_mda_iter'] = 200
        full_values_dict[f'{usecase.study_name}.sub_mda_class'] = 'MDAGaussSeidel'
        self.ee.load_study_from_input_dict(full_values_dict)

        disc_mda = self.ee.root_process

        energy_mix_output = [f'{self.name}.EnergyMix.{GlossaryEnergy.EnergyProductionValue}',
                             f'{self.name}.EnergyMix.co2_emissions_Gt',
                             f'{self.name}.FunctionManagerDisc.energy_production_objective',
                             f'{self.name}.FunctionManagerDisc.co2_emissions_objective',
                             f'{self.name}.EnergyMix.energy_mean_price',
                             f'{self.name}.EnergyMix.land_demand_df',
                             f'{self.name}.FunctionManagerDisc.primary_energies_production',
                             f'{self.name}.EnergyMix.CCS_price']

        self.check_jacobian(location=dirname(__file__),
                            filename='jacobian_open_loop_energymixoutputs_vs_energy_investment.pkl',
                            discipline=disc_mda, step=1.0e-14, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc_mda.local_data,
                            inputs=[
                                f'{self.name}.EnergyMix.energy_investment'],
                            outputs=energy_mix_output, parallel=True)

    def test_05_check_gradient_open_loop_after_MDA_results(self):

        self.name = 'Test'
        self.ee = ExecutionEngine(self.name)
        repo = 'energy_models.sos_processes.energy.MDA'
        builder = self.ee.factory.get_builder_from_process(
            repo, 'energy_process_v0_mda')

        self.ee.factory.set_builders_to_coupling_builder(builder)
        self.ee.configure()
        usecase = Study_MDA(execution_engine=self.ee)
        usecase.study_name = self.name
        values_dict = usecase.setup_usecase()

        self.ee.display_treeview_nodes()
        full_values_dict = {}
        for dict_v in values_dict:
            full_values_dict.update(dict_v)

        full_values_dict[f'{usecase.study_name}.linear_solver_MDO_options'] = {'max_iter': 1000,
                                                                               'tol': 1.0e-14}
        full_values_dict[f'{usecase.study_name}.linear_solver_MDA_options'] = {'max_iter': 1000,
                                                                               'tol': 1.0e-14}
        full_values_dict[f'{usecase.study_name}.linearization_mode'] = 'adjoint'
        full_values_dict[f'{usecase.study_name}.tolerance'] = 1.0e-12
        full_values_dict[f'{usecase.study_name}.sub_mda_class'] = 'MDANewtonRaphson'

        self.ee.load_study_from_input_dict(full_values_dict)

        self.ee.execute()

        energy_prices = self.ee.dm.get_value(
            f'{usecase.study_name}.EnergyMix.{GlossaryEnergy.StreamPricesValue}')
        energy_emissions = self.ee.dm.get_value(
            f'{usecase.study_name}.EnergyMix.{GlossaryEnergy.StreamsCO2EmissionsValue}')

        dump_dir = join(dirname(__file__), self.name)

        BaseStudyManager.static_dump_data(
            dump_dir, self.ee, DirectLoadDump())

        exec_eng2 = ExecutionEngine(self.name)
        repo = 'energy_models.sos_processes.energy.MDA'
        builders = exec_eng2.factory.get_builder_from_process(
            repo, 'energy_process_v0')
        exec_eng2.factory.set_builders_to_coupling_builder(builders)

        exec_eng2.configure()

        BaseStudyManager.static_load_data(
            dump_dir, exec_eng2, DirectLoadDump())

        full_values_dict = {
            f'{usecase.study_name}.sub_mda_class': 'MDAGaussSeidel',
            f'{usecase.study_name}.{GlossaryEnergy.StreamPricesValue}': energy_prices,
            f'{usecase.study_name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': energy_emissions}

        exec_eng2.load_study_from_input_dict(full_values_dict)
        energy_list = [GlossaryEnergy.methane, GlossaryEnergy.solid_fuel, GlossaryEnergy.syngas,
                       GlossaryEnergy.electricity, GlossaryEnergy.liquid_fuel,
                       GlossaryEnergy.carbon_capture, GlossaryEnergy.carbon_storage, GlossaryEnergy.biogas,
                       GlossaryEnergy.biomass_dry, GlossaryEnergy.biodiesel,
                       f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}',
                       f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.liquid_hydrogen}']

        disc_mda = exec_eng2.root_process
        energy_price_outputs = []
        for energy in energy_list:
            energy_price_outputs.append(
                f'{usecase.study_name}.EnergyMix.{energy}.{GlossaryEnergy.StreamPricesValue}')
            techno_list = self.ee.dm.get_value(
                f'{usecase.study_name}.EnergyMix.{energy}.{GlossaryEnergy.techno_list}')
            for techno in techno_list:
                energy_price_outputs.append(
                    f'{usecase.study_name}.EnergyMix.{energy}.{techno}.{GlossaryEnergy.TechnoPricesValue}')
        self.check_jacobian(location=dirname(__file__), filename='jacobian_open_loop_after_MDA_results.pkl',
                            discipline=disc_mda, step=1.0e-14, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc_mda.local_data,
                            inputs=[
                                f'{self.name}.EnergyMix.energy_investment'],
                            outputs=energy_price_outputs + [f'{usecase.study_name}.EnergyMix.energy_mean_price'],
                            parallel=True)

    def test_06_check_gradient_energymixoutputs_vs_energy_mixes(self):

        self.name = 'Test'
        self.ee = ExecutionEngine(self.name)
        repo = 'energy_models.sos_processes.energy.MDA'
        builder = self.ee.factory.get_builder_from_process(
            repo, 'energy_process_v0_mda')
        designvariable_name = "DesignVariables"
        # design variables builder
        design_var_path = 'energy_models.core.design_variables_translation_bspline.design_var_disc.Design_Var_Discipline'
        design_var_builder = self.ee.factory.get_builder_from_module(
            f'{designvariable_name}', design_var_path)
        ns_dict = {GlossaryEnergy.NS_WITNESS: f'{self.ee.study_name}',
                   'ns_optim': f'{self.ee.study_name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)
        builder.append(design_var_builder)
        self.ee.factory.set_builders_to_coupling_builder(builder)
        self.ee.configure()
        usecase = Study_MDA(execution_engine=self.ee)
        usecase.study_name = self.name
        values_dict = usecase.setup_usecase()

        self.ee.display_treeview_nodes()
        full_values_dict = {}
        for dict_v in values_dict:
            full_values_dict.update(dict_v)

        full_values_dict[f'{usecase.study_name}.tolerance_linear_solver_MDO'] = 1.0e-14
        full_values_dict[f'{usecase.study_name}.tolerance_linear_solver_MDO'] = 1.0e-14
        full_values_dict[f'{usecase.study_name}.linearization_mode'] = 'adjoint'
        full_values_dict[f'{usecase.study_name}.tolerance'] = 1.0e-12
        full_values_dict[f'{usecase.study_name}.max_mda_iter'] = 200
        full_values_dict[f'{usecase.study_name}.sub_mda_class'] = 'MDAGaussSeidel'

        nb_poles = 5

        full_values_dict[f'{usecase.study_name}.CO2_taxes_array'] = np.linspace(
            70, 200, nb_poles)
        input_full_names = [f'{usecase.study_name}.CO2_taxes_array']
        for energy in full_values_dict[f'{self.name}.{GlossaryEnergy.energy_list}']:
            energy_wo_dot = energy.replace('.', '_')
            input_name = f'{self.name}.EnergyMix.{energy}.{energy_wo_dot}_array_mix'
            input_full_names.append(input_name)
            full_values_dict[input_name] = np.linspace(1, 2, nb_poles)

            for technology in full_values_dict[f'{self.name}.EnergyMix.{energy}.{GlossaryEnergy.techno_list}']:
                technology_wo_dot = technology.replace('.', '_')
                input_name = f'{self.name}.EnergyMix.{energy}.{technology}.{energy_wo_dot}_{technology_wo_dot}_array_mix'
                input_full_names.append(input_name)
                full_values_dict[input_name] = np.linspace(3, 4, nb_poles)
        dspace = usecase.dspace
        self.dspace_size = dspace.pop('dspace_size')

        dspace_dict = defaultdict(list)
        for key, elem in self.dspace.items():
            dspace_dict['variable'].append(key)
            for column, value in elem.items():
                dspace_dict[column].append(value)
        full_values_dict[f'{self.name}.design_space'] = self.dspace

        self.ee.load_study_from_input_dict(full_values_dict)

        disc_mda = self.ee.root_process

        energy_mix_output = [f'{self.name}.EnergyMix.{GlossaryEnergy.EnergyProductionValue}',
                             f'{self.name}.EnergyMix.co2_emissions_Gt',
                             f'{self.name}.FunctionManagerDisc.energy_production_objective',
                             f'{self.name}.FunctionManagerDisc.co2_emissions_objective',
                             f'{self.name}.EnergyMix.energy_mean_price',
                             f'{self.name}.EnergyMix.land_demand_df',
                             f'{self.name}.FunctionManagerDisc.primary_energies_production',
                             f'{self.name}.EnergyMix.CCS_price']

        self.check_jacobian(location=dirname(__file__),
                            filename='jacobian_gradient_energymixoutputs_vs_energy_mixes.pkl',
                            discipline=disc_mda, step=1.0e-14, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc_mda.local_data,
                            inputs=input_full_names,
                            outputs=energy_mix_output, parallel=True)


#
#     def test_06_check_gradient_energymixoutputs_vs_energy_mixes(self):
#
#         self.name = 'Test'
#         self.ee = ExecutionEngine(self.name)
#         repo = 'energy_models.sos_processes.energy.MDA'
#         builder = self.ee.factory.get_builder_from_process(
#             repo, 'energy_process_v0')
#         designvariable_name = "DesignVariables"
#         # design variables builder
#         design_var_path = 'energy_models.core.design_variables_translation_bspline.design_var_disc.Design_Var_Discipline'
#         design_var_builder = self.ee.factory.get_builder_from_module(
#             f'{designvariable_name}', design_var_path)
#         ns_dict = {GlossaryEnergy.NS_WITNESS: f'{self.ee.study_name}',
#                    'ns_optim': f'{self.ee.study_name}'}
#         self.ee.ns_manager.add_ns_def(ns_dict)
#         builder.append(design_var_builder)
#         self.ee.factory.set_builders_to_coupling_builder(builder)
#         self.ee.configure()
#         usecase = Study_open(main_study=False, execution_engine=self.ee)
#         usecase.study_name = self.name
#         values_dict = usecase.setup_usecase()
#
#         self.ee.display_treeview_nodes()
#         full_values_dict = {}
#         for dict_v in values_dict:
#             full_values_dict.update(dict_v)
#
#         full_values_dict[f'{usecase.study_name}.tolerance_linear_solver_MDO'] = 1.0e-14
#         full_values_dict[f'{usecase.study_name}.tolerance_linear_solver_MDA'] = 1.0e-14
#         full_values_dict[f'{usecase.study_name}.linearization_mode'] = 'adjoint'
#         full_values_dict[f'{usecase.study_name}.tolerance'] = 1.0e-12
#         full_values_dict[f'{usecase.study_name}.max_mda_iter'] = 200
#         full_values_dict[f'{usecase.study_name}.sub_mda_class'] = 'MDAGaussSeidel'
#
#         nb_poles = 5
#
#         full_values_dict[f'{usecase.study_name}.CO2_taxes_array'] = np.linspace(
#             70, 200, nb_poles)
#         input_full_names = [f'{usecase.study_name}.CO2_taxes_array']
#         for energy in full_values_dict[f'{self.name}.{GlossaryEnergy.energy_list}']:
#             energy_wo_dot = energy.replace('.', '_')
#             input_name = f'{self.name}.EnergyMix.{energy}.{energy_wo_dot}_array_mix'
#             input_full_names.append(input_name)
#             full_values_dict[input_name] = np.linspace(1, 2, nb_poles)
#
#             for technology in full_values_dict[f'{self.name}.EnergyMix.{energy}.{GlossaryEnergy.techno_list}']:
#                 technology_wo_dot = technology.replace('.', '_')
#                 input_name = f'{self.name}.EnergyMix.{energy}.{technology}.{energy_wo_dot}_{technology_wo_dot}_array_mix'
#                 input_full_names.append(input_name)
#                 full_values_dict[input_name] = np.linspace(3, 4, nb_poles)
#         dspace = usecase.dspace
#         self.dspace_size = dspace.pop('dspace_size')
#
#         dspace_df_columns = ['variable', 'value', 'lower_bnd',
#                              'upper_bnd', 'enable_variable']
#         dspace_df = pd.DataFrame(columns=dspace_df_columns)
#         for key, elem in dspace.items():
#             dict_var = {'variable': key}
#             dict_var.update(elem)
#             dspace_df = pd.concat([dspace_df,pd.DataFrame(dict_var)], ignore_index=True)
#
#         self.dspace = dspace_df
#         full_values_dict[f'{self.name}.design_space'] = self.dspace
#
#         self.ee.load_study_from_input_dict(full_values_dict)
#
#         disc_mda = self.ee.root_process
#
#         energy_mix_output = [f'{self.name}.EnergyMix.{GlossaryEnergy.EnergyProductionValue}', f'{self.name}.EnergyMix.co2_emissions_Gt',
#                              f'{self.name}.FunctionManagerDisc.energy_production_objective', f'{self.name}.FunctionManagerDisc.co2_emissions_objective', f'{self.name}.EnergyMix.energy_mean_price',
#                              f'{self.name}.EnergyMix.land_demand_df',
#                              f'{self.name}.FunctionManagerDisc.primary_energies_production', f'{self.name}.EnergyMix.CCS_price']#
#         # for energy in self.ee.dm.get_value('Test.energy_list'):
#         #    print(energy)
#         self.check_jacobian(location=dirname(__file__), filename='jacobian_gradient_energymixoutputs_vs_energy_mixes_test.pkl',
#                             discipline=disc_mda, step=1.0e-14, derr_approx='complex_step', threshold=1e-5,
#                             inputs=[
#             'Test.EnergyMix.syngas.CoalGasification.syngas_CoalGasification_array_mix'],
#             outputs=energy_mix_output)


if '__main__' == __name__:
    cls = TestMDAAnalyticGradient()
    cls.test_06_check_gradient_energymixoutputs_vs_energy_mixes()
