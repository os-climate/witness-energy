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
import pandas as pd
import numpy as np
from os.path import join, dirname
from sos_trades_core.execution_engine.execution_engine import ExecutionEngine
from energy_models.sos_processes.energy.techno_mix.carbon_capture_mix.usecase import Study
from copy import deepcopy


class CarbonCaptureTestCase(unittest.TestCase):
    """
    Carbon Capture prices test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        years = np.arange(2020, 2051)

        self.name = 'Test'
        ee_data = ExecutionEngine(self.name)
        repo = 'energy_models.sos_processes.energy.techno_mix'
        builder = ee_data.factory.get_builder_from_process(
            repo, 'carbon_capture_mix')

        ee_data.factory.set_builders_to_coupling_builder(builder)
        ee_data.configure()
        usecase = Study(execution_engine=ee_data)
        usecase.study_name = self.name
        values_dict = usecase.setup_usecase()
        full_values_dict = {}
        for dict_v in values_dict:
            full_values_dict.update(dict_v)
        ee_data.load_study_from_input_dict(full_values_dict)

        ee_data.display_treeview_nodes()
        ee_data.execute()
        self.dm_dict = ee_data.dm.get_data_dict_values()

    def tearDown(self):
        pass

    def test_01_carbon_capture_discipline(self):

        self.name = 'Test'
        ns_study = self.name
        carbon_capture_name = 'carbon_capture'
        energy_mix = 'EnergyMix'
        flue_gas_name = 'flue_gas_capture'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_carbon_capture': f'{ns_study}.{energy_mix}.{carbon_capture_name}',
                   'ns_energy': f'{ns_study}.{energy_mix}',
                   'ns_energy_study': f'{ns_study}',
                   'ns_flue_gas': f'{ns_study}.{energy_mix}.{carbon_capture_name}.{flue_gas_name}',
                   'ns_public': f'{ns_study}',
                   'ns_energy_mix': f'{ns_study}.{energy_mix}',
                   'ns_resource': f'{ns_study}.{energy_mix}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.stream_type.carbon_disciplines.carbon_capture_disc.CarbonCaptureDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            f'{energy_mix}.{carbon_capture_name}', mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = self.dm_dict
        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{energy_mix}.{carbon_capture_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)
#         for graph in graph_list:
#             graph.to_plotly().show()

    def test_02_carbon_capture_analytic_grad(self):

        self.name = 'Test'
        ns_study = self.name
        carbon_capture_name = 'carbon_capture'
        energy_mix = 'EnergyMix'
        flue_gas_name = 'flue_gas_capture'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_carbon_capture': f'{ns_study}.{energy_mix}.{carbon_capture_name}',
                   'ns_energy': f'{ns_study}.{energy_mix}',
                   'ns_energy_study': f'{ns_study}',
                   'ns_flue_gas': f'{ns_study}.{energy_mix}.{carbon_capture_name}.{flue_gas_name}',
                   'ns_public': f'{ns_study}',
                   'ns_energy_mix': f'{ns_study}.{energy_mix}',
                   'ns_resource': f'{ns_study}.{energy_mix}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.stream_type.carbon_disciplines.carbon_capture_disc.CarbonCaptureDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            f'{energy_mix}.{carbon_capture_name}', mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = self.dm_dict
        self.ee.load_study_from_input_dict(inputs_dict)

        disc_techno = self.ee.root_process.sos_disciplines[0]
        data_in = disc_techno._data_in
        input_keys = [disc_techno.get_var_full_name(key, data_in)
                      for key in disc_techno.get_sosdisc_inputs() if data_in[key]['type'] == 'dataframe']

        output_keys = [disc_techno.get_var_full_name(key, disc_techno._data_out)
                       for key in disc_techno.get_sosdisc_outputs() if 'detailed' not in key]
        succeed = disc_techno.check_jacobian(derr_approx='complex_step', inputs=input_keys,
                                             outputs=output_keys,
                                             dump_jac_path=join(dirname(__file__), 'jacobian_pkls',
                                                                f'jacobian_carbon_capture_discipline.pkl'))

        self.assertTrue(
            succeed, msg=f"Wrong gradient in {disc_techno.get_disc_full_name()}")

    def test_03_carbon_capture_discipline_limited(self):

        self.name = 'Test'
        ns_study = self.name
        carbon_capture_name = 'carbon_capture'
        energy_mix = 'EnergyMix'
        flue_gas_name = 'flue_gas_capture'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_carbon_capture': f'{ns_study}.{energy_mix}.{carbon_capture_name}',
                   'ns_energy': f'{ns_study}.{energy_mix}',
                   'ns_energy_study': f'{ns_study}',
                   'ns_flue_gas': f'{ns_study}.{energy_mix}.{carbon_capture_name}.{flue_gas_name}',
                   'ns_public': f'{ns_study}',
                   'ns_energy_mix': f'{ns_study}.{energy_mix}',
                   'ns_resource': f'{ns_study}.{energy_mix}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.stream_type.carbon_disciplines.carbon_capture_disc.CarbonCaptureDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            f'{energy_mix}.{carbon_capture_name}', mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = deepcopy(self.dm_dict)

        inputs_dict['Test.EnergyMix.carbon_capture.flue_gas_capture.CalciumLooping.techno_production'][
            'carbon_capture (Mt)'] *= 5.0
        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{energy_mix}.{carbon_capture_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)
#         for graph in graph_list:
#             graph.to_plotly().show()

    def test_04_carbon_capture_analytic_grad_limited(self):

        self.name = 'Test'
        ns_study = self.name
        carbon_capture_name = 'carbon_capture'
        energy_mix = 'EnergyMix'
        flue_gas_name = 'flue_gas_capture'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_carbon_capture': f'{ns_study}.{energy_mix}.{carbon_capture_name}',
                   'ns_energy': f'{ns_study}.{energy_mix}',
                   'ns_energy_study': f'{ns_study}',
                   'ns_flue_gas': f'{ns_study}.{energy_mix}.{carbon_capture_name}.{flue_gas_name}',
                   'ns_public': f'{ns_study}',
                   'ns_energy_mix': f'{ns_study}.{energy_mix}',
                   'ns_resource': f'{ns_study}.{energy_mix}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.stream_type.carbon_disciplines.carbon_capture_disc.CarbonCaptureDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            f'{energy_mix}.{carbon_capture_name}', mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = deepcopy(self.dm_dict)

        inputs_dict['Test.EnergyMix.carbon_capture.flue_gas_capture.CalciumLooping.techno_production'][
            'carbon_capture (Mt)'] *= 5.0
        self.ee.load_study_from_input_dict(inputs_dict)

        disc_techno = self.ee.root_process.sos_disciplines[0]
        data_in = disc_techno._data_in
        input_keys = [disc_techno.get_var_full_name(key, data_in)
                      for key in disc_techno.get_sosdisc_inputs() if data_in[key]['type'] == 'dataframe']

        output_keys = [disc_techno.get_var_full_name(key, disc_techno._data_out)
                       for key in disc_techno.get_sosdisc_outputs() if 'detailed' not in key]
        succeed = disc_techno.check_jacobian(derr_approx='complex_step', inputs=input_keys,
                                             outputs=output_keys,
                                             dump_jac_path=join(dirname(__file__), 'jacobian_pkls',
                                                                f'jacobian_carbon_capture_discipline_limited.pkl'))

        self.assertTrue(
            succeed, msg=f"Wrong gradient in {disc_techno.get_disc_full_name()}")


if '__main__' == __name__:
    cls = CarbonCaptureTestCase()
    cls.setUp()
    cls.test_01_carbon_capture_discipline()
