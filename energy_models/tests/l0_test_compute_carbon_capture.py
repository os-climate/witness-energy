'''
Copyright 2022 Airbus SAS
Modifications on 2023/10/02-2023/11/16 Copyright 2023 Capgemini

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
from energy_models.sos_processes.energy.techno_mix.carbon_capture_mix.usecase import Study
from sostrades_core.execution_engine.execution_engine import ExecutionEngine


class CarbonCaptureTestCase(unittest.TestCase):
    """
    Carbon Capture prices test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
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
        carbon_capture_name = GlossaryEnergy.carbon_capture
        energy_mix = 'EnergyMix'
        flue_gas_name = 'flue_gas_capture'
        direct_air_name = 'direct_air_capture'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_carbon_capture': f'{ns_study}.{energy_mix}.{carbon_capture_name}',
                   'ns_energy': f'{ns_study}.{energy_mix}',
                   'ns_energy_study': f'{ns_study}',
                   'ns_flue_gas': f'{ns_study}.{energy_mix}.{carbon_capture_name}.{flue_gas_name}',
                   'ns_direct_air': f'{ns_study}.{energy_mix}.{carbon_capture_name}.{direct_air_name}',
                   'ns_public': f'{ns_study}',
                   GlossaryEnergy.NS_CCS: f'{ns_study}',
                   GlossaryEnergy.NS_ENERGY_MIX: f'{ns_study}.{energy_mix}',
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

    def test_02_carbon_capture_discipline_limited(self):
        self.name = 'Test'
        ns_study = self.name
        carbon_capture_name = GlossaryEnergy.carbon_capture
        energy_mix = 'EnergyMix'
        flue_gas_name = 'flue_gas_capture'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_carbon_capture': f'{ns_study}.{energy_mix}.{carbon_capture_name}',
                   'ns_energy': f'{ns_study}.{energy_mix}',
                   'ns_energy_study': f'{ns_study}',
                   'ns_flue_gas': f'{ns_study}.{energy_mix}.{carbon_capture_name}.{flue_gas_name}',
                   'ns_public': f'{ns_study}',
                   GlossaryEnergy.NS_ENERGY_MIX: f'{ns_study}.{energy_mix}',
                   'ns_resource': f'{ns_study}.{energy_mix}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.stream_type.carbon_disciplines.carbon_capture_disc.CarbonCaptureDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            f'{energy_mix}.{carbon_capture_name}', mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = deepcopy(self.dm_dict)

        inputs_dict[
            f'Test.EnergyMix.carbon_capture.flue_gas_capture.CalciumLooping.{GlossaryEnergy.TechnoProductionValue}'][
            f'{GlossaryEnergy.carbon_capture} (Mt)'] *= 5.0
        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{energy_mix}.{carbon_capture_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)

        # for graph in graph_list:
        #     graph.to_plotly().show()



if '__main__' == __name__:
    cls = CarbonCaptureTestCase()
    cls.setUp()
    cls.test_01_carbon_capture_discipline()
