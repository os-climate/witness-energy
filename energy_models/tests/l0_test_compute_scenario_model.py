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
from itertools import islice
import scipy.interpolate as sc
import csv
import matplotlib.pyplot as plt

from energy_models.core.scenario.disciplines.scenario_disc import ScenarioDiscipline
from energy_models.core.scenario.scenario import ScenarioModel
from sos_trades_core.execution_engine.execution_engine import ExecutionEngine

class ScenarioTestCase(unittest.TestCase):
    """
    Scenario test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''

        self.year_start = 2020
        self.year_end = 2050
        self.scenario_name = 'STEPS'

    def tearDown(self):
        pass

    def test_01_run_scenario_discipline(self):

        self.name = 'Test'
        self.model_name = 'scenario'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.scenario.disciplines.scenario_disc.ScenarioDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{self.model_name}.yeart_start': self.year_start,
                       f'{self.name}.{self.model_name}.yeart_end': self.year_end,
                       f'{self.name}.{self.model_name}.scenario_name': self.scenario_name,
                       f'{self.name}.{self.model_name}.CO2_taxes_all_scenario': ScenarioDiscipline.default_scenario_co2_taxe_all,
                       f'{self.name}.{self.model_name}.transport_price_all_scenario': ScenarioDiscipline.default_transport_price_all,
                       f'{self.name}.{self.model_name}.transport_margin_factor_all_scenario':  ScenarioDiscipline.default_transport_margin_all}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        scenario_name = self.ee.dm.get_value(
            f'{self.name}.{self.model_name}.scenario_name')

        CO2_taxes_scenario = self.ee.dm.get_value(
            f'{self.name}.{self.model_name}.CO2_taxes_scenario')

        transport_price_scenario = self.ee.dm.get_value(
            f'{self.name}.{self.model_name}.transport_price_scenario')

        transport_margin_factor_scenario = self.ee.dm.get_value(
            f'{self.name}.{self.model_name}.transport_margin_factor_scenario')
