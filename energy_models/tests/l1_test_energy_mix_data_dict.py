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
import numpy as np
import pandas as pd
from os.path import join, dirname
from sos_trades_core.execution_engine.execution_engine import ExecutionEngine

from energy_models.sos_processes.energy.MDO_subprocesses.energy_optim_sub_process.usecase import Study
from energy_models.sos_processes.energy.MDA.energy_process_v0.usecase import Study as Study_open
from sos_trades_core.tests.core.abstract_jacobian_unit_test import AbstractJacobianUnittest
from sos_trades_core.tools.post_processing.post_processing_factory import PostProcessingFactory
from energy_models.core.energy_mix.energy_mix import EnergyMix


class EnergyMixDataDictTestCase(unittest.TestCase):
    """
    Energy mix test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''

    def test_01_energy_mix_discipline_zero_co2_per_use(self):

        self.name = 'Test'
        self.ee = ExecutionEngine(self.name)
        name = 'Test'
        model_name = 'EnergyMix'
        func_manager_name = 'FunctionManagerDisc'

        repo = 'energy_models.sos_processes.energy.MDA'
        builder = self.ee.factory.get_builder_from_process(
            repo, 'energy_process_v0')

        self.ee.factory.set_builders_to_coupling_builder(builder)
        self.ee.configure()
        usecase = Study_open(execution_engine=self.ee)
        usecase.study_name = self.name
        values_dict = usecase.setup_usecase()

        self.ee.display_treeview_nodes()
        full_values_dict = {}

        energy_class_dict = EnergyMix.energy_class_dict
        data_dicts = {}
        for energy_name, energy_class in energy_class_dict.items():
            data_dicts[energy_name] = energy_class.data_energy_dict
            if 'CO2_per_use' in data_dicts[energy_name].keys():
                data_dicts[energy_name]['CO2_per_use'] = .0

        for dict_v in values_dict:
            full_values_dict.update(dict_v)

        energy_list = full_values_dict['Test.energy_list']
        for energy in energy_list:
            full_values_dict[f'{name}.{model_name}.{energy}.data_fuel_dict'] = data_dicts[energy]

        full_values_dict[f'{name}.epsilon0'] = 1.0
        full_values_dict[f'{name}.tolerance'] = 1.0e-8
        full_values_dict[f'{name}.max_mda_iter'] = 50
        self.ee.load_study_from_input_dict(full_values_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.EnergyMix')[0]

        # check if total Co2 emissions by use are effectively 0
        assert disc.get_sosdisc_outputs('co2_emissions')[
            'Total CO2 by use (Mt)'].sum() == 0.0

        ppf = PostProcessingFactory()
        filters = ppf.get_post_processing_filters_by_discipline(disc)
        graph_list = ppf.get_post_processing_by_discipline(
            disc, filters, as_json=False)
        # for graph in graph_list:
        #     graph.to_plotly().show()


if '__main__' == __name__:
    cls = EnergyMixDataDictTestCase()
    cls.setUp()
    cls.test_01_energy_mix_discipline_zero_co2_per_use()
