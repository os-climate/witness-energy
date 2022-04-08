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
from os.path import join, dirname
import pandas as pd
import numpy as np

from sos_trades_core.execution_engine.execution_engine import ExecutionEngine
from sos_trades_core.tests.core.abstract_jacobian_unit_test import AbstractJacobianUnittest
from energy_models.sos_processes.energy.MDO.energy_optim_process.usecase import Study


class EnergyMDAGetGradientTest(AbstractJacobianUnittest):

    #AbstractJacobianUnittest.DUMP_JACOBIAN = True

    def setUp(self):

        self.name = 'Test'
        self.ee = ExecutionEngine(self.name)

    def analytic_grad_entry(self):
        return []

    def test_01_check_gradients_values_at_mda_ite(self):
        '''
        Test that checks the gradients values of the energy optim process at each MDA iteration step
        '''
        self.name = 'Test'
        self.ee = ExecutionEngine(self.name)
        self.model_name = 'gradient_after_MDA'

        # retrieve energy process
        repo = 'energy_models.sos_processes.energy.MDO'
        builder = self.ee.factory.get_builder_from_process(
            repo, 'energy_optim_process')

        ns_dict = {'ns_functions': f'{self.ee.study_name}',
                   'ns_optim': f'{self.ee.study_name}',
                   'ns_public': f'{self.ee.study_name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        self.ee.factory.set_builders_to_coupling_builder(
            builder)

        self.ee.configure()
        data_dir = join(dirname(__file__), 'data')
        usecase = Study(execution_engine=self.ee)
        usecase.study_name = self.name
        values_dict = {}
        for dict_item in usecase.setup_usecase():
            values_dict.update(dict_item)
        values_dict[f'{self.name}.sub_mda_class'] = 'MDAGaussSeidel'
        values_dict[f'{self.name}.{usecase.optim_name}.max_iter'] = 1
        values_dict[f'{self.name}.max_mda_iter'] = 1
        values_dict[f'{self.name}.{usecase.optim_name}.{usecase.coupling_name}.sub_mda_class'] = 'MDAGaussSeidel'
        values_dict[f'{self.name}.{usecase.optim_name}.{usecase.coupling_name}.max_mda_iter'] = 1

        n_ite_mda = 5
        for ite_mda in range(n_ite_mda):
            self.ee_1 = ExecutionEngine(self.name)
            # retrieve energy process
            repo = 'energy_models.sos_processes.energy.MDO'
            builder = self.ee_1.factory.get_builder_from_process(
                repo, 'energy_optim_process')

            ns_dict = {'ns_functions': f'{self.ee_1.study_name}',
                       'ns_optim': f'{self.ee_1.study_name}',
                       'ns_public': f'{self.ee_1.study_name}'}

            self.ee_1.ns_manager.add_ns_def(ns_dict)

            self.ee_1.factory.set_builders_to_coupling_builder(
                builder)

            self.ee_1.configure()
            usecase_1 = Study(execution_engine=self.ee_1)
            usecase_1.study_name = self.name
            values_dict[f'{self.name}.{usecase.optim_name}.{usecase.coupling_name}.max_mda_iter'] = ite_mda + 1
            self.ee_1.load_study_from_input_dict(values_dict)
            self.ee_1.execute()
            df_disc_dict = {}

            for disc_name in self.ee_1.dm.disciplines_id_map.keys():
                disc = self.ee_1.dm.get_disciplines_with_name(disc_name)[0]
                outputs = disc.get_output_data_names()
                outputs = [output for output in outputs if self.ee_1.dm.get_data(output, 'coupling')
                           and not output.endswith('all_streams_demand_ratio')]

                if disc.name == 'FunctionsManager':
                    outputs.append(self.ee_1.dm.get_all_namespaces_from_var_name(
                        'objective_lagrangian')[0])
                inputs = disc.get_input_data_names()
                inputs = [input for input in inputs if self.ee_1.dm.get_data(input, 'coupling')
                          and not input.endswith('resources_price')
                          and not input.endswith('resources_CO2_emissions')
                          and not input.endswith('land_use_required')
                          and not input.endswith('all_streams_demand_ratio')]
                b = disc.get_infos_gradient(outputs, inputs)
                # columns = []
                # values = []
                # for k, v in b.items():
                # for k_k, v_v in v.items():
                # columns += [(k_k.split('.')[-1], 'abs_min'), ]
                # min_value = min(np.abs([min for min in [v_v['min']] if min not in [0.0]]),
                # np.abs([max for max in [v_v['max']] if max not in [0.0]]))
                # if len(min_value) == 0:
                # min_value = np.zeros(1)
                # values += [min_value[0], ]
                # columns += [(k_k.split('.')[-1], 'abs_max'), ]
                # values += [max(np.abs(v_v['min']),
                # np.abs(v_v['max'])), ]
                # miindex = pd.Index([ite_mda + 1])
                # micolumns = pd.MultiIndex.from_tuples(
                # columns, names=['lvl1', 'lvl2'])
                # df = pd.DataFrame(np.asarray(values).reshape(
                # (len(miindex), len(micolumns))), index=miindex, columns=micolumns)
                # df_disc_dict[disc_name] = df
                # df_disc_dict_list += [df_disc_dict, ]
                # for disc_name in df_disc_dict_list[0].keys():
                # df_list = [df_disc_dict[disc_name]
                # for df_disc_dict in df_disc_dict_list]
                # concat_df = pd.concat(df_list)
                # concat_df.to_csv(f'gradients_drdw_disc_{disc_name}.csv')

    def test_02_check_gradients_values_at_mdo_ite(self):
        '''
        Test that outputs the gradients values of the energy optim process at each MDO iteration step
        '''
        self.name = 'Test'
        self.ee = ExecutionEngine(self.name)
        self.model_name = 'gradient_after_MDA'

        # retrieve energy process
        repo = 'energy_models.sos_processes.energy.MDO'
        builder = self.ee.factory.get_builder_from_process(
            repo, 'energy_optim_process')

        ns_dict = {'ns_functions': f'{self.ee.study_name}',
                   'ns_optim': f'{self.ee.study_name}',
                   'ns_public': f'{self.ee.study_name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        self.ee.factory.set_builders_to_coupling_builder(
            builder)

        self.ee.configure()
        data_dir = join(dirname(__file__), 'data')
        usecase = Study(execution_engine=self.ee)
        usecase.study_name = self.name
        values_dict = {}
        for dict_item in usecase.setup_usecase():
            values_dict.update(dict_item)
        values_dict[f'{self.name}.sub_mda_class'] = 'MDANewtonRaphson'
        values_dict[f'{self.name}.{usecase.optim_name}.max_iter'] = 1
        values_dict[f'{self.name}.max_mda_iter'] = 1
        values_dict[f'{self.name}.{usecase.optim_name}.{usecase.coupling_name}.sub_mda_class'] = 'MDANewtonRaphson'
        values_dict[f'{self.name}.{usecase.optim_name}.{usecase.coupling_name}.max_mda_iter'] = 1

        n_ite_mdo = 5
        df_list = []
        for ite_mdo in range(n_ite_mdo):
            self.ee_1 = ExecutionEngine(self.name)
            # retrieve energy process
            repo = 'energy_models.sos_processes.energy.MDO'
            builder = self.ee_1.factory.get_builder_from_process(
                repo, 'energy_optim_process')

            ns_dict = {'ns_functions': f'{self.ee_1.study_name}',
                       'ns_optim': f'{self.ee_1.study_name}',
                       'ns_public': f'{self.ee_1.study_name}'}

            self.ee_1.ns_manager.add_ns_def(ns_dict)

            self.ee_1.factory.set_builders_to_coupling_builder(
                builder)

            self.ee_1.configure()
            usecase_1 = Study(execution_engine=self.ee_1)
            usecase_1.study_name = self.name
            values_dict[f'{self.name}.{usecase.optim_name}.max_iter'] = ite_mdo + 1
            self.ee_1.load_study_from_input_dict(values_dict)
            self.ee_1.execute()

            input_full_names = []
            for energy in values_dict[f'{self.name}.{usecase.optim_name}.{usecase.coupling_name}.energy_list']:
                energy_wo_dot = energy.replace('.', '_')
                input_full_names.append(
                    f'{self.name}.{usecase.optim_name}.{usecase.coupling_name}.EnergyMix.{energy}.{energy_wo_dot}_array_mix')

                for technology in values_dict[f'{self.name}.{usecase.optim_name}.{usecase.coupling_name}.EnergyMix.{energy}.technologies_list']:
                    technology_wo_dot = technology.replace('.', '_')
                    input_full_names.append(
                        f'{self.name}.{usecase.optim_name}.{usecase.coupling_name}.EnergyMix.{energy}.{technology}.{energy_wo_dot}_{technology_wo_dot}_array_mix')
            b = self.ee_1.dm.get_disciplines_with_name(f'{self.name}.{usecase.optim_name}.{usecase.coupling_name}')[0].get_infos_gradient(
                [f'{self.name}.{usecase.optim_name}.objective_lagrangian'], input_full_names)
            columns = []
            values = []
            for k, v in b.items():
                for k_k, v_v in v.items():
                    columns += [(k_k.split('.')[-1], 'abs_min'), ]
                    min_value = min(np.abs([min for min in [v_v['min']] if min not in [0.0]]),
                                    np.abs([max for max in [v_v['max']] if max not in [0.0]]))
                    if len(min_value) == 0:
                        min_value = np.zeros(1)
                    values += [min_value[0], ]
                    columns += [(k_k.split('.')[-1], 'abs_max'), ]
                    values += [max(np.abs(v_v['min']),
                                   np.abs(v_v['max'])), ]
            miindex = pd.Index([ite_mdo + 1])
            micolumns = pd.MultiIndex.from_tuples(
                columns, names=['lvl1', 'lvl2'])
            df = pd.DataFrame(np.asarray(values).reshape(
                (len(miindex), len(micolumns))), index=miindex, columns=micolumns)
            df_list += [df, ]

        concat_df = pd.concat(df_list)
        concat_df.to_csv(f'gradients_lagrangian_wrt_dv_{self.model_name}.csv')


if '__main__' == __name__:
    cls = EnergyMDAGetGradientTest()
    cls.test_01_check_gradients_values_at_mda_ite()
