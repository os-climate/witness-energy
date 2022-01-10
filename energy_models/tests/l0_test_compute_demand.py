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
from pandas.testing import assert_frame_equal

from sos_trades_core.execution_engine.execution_engine import ExecutionEngine


class DemandTestCase(unittest.TestCase):
    """
    Demand computation tests
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.year_start = 2020
        self.year_end = 2051
        self.years = np.arange(self.year_start, self.year_end)

        self.total_energy_demand = pd.DataFrame(
            {'years': self.years, 'demand': np.arange(10, 41)})
        self.energy_list = ['hydrogen.gaseous_hydrogen', 'methane']

        self.energy_demand_mix = {}
        self.energy_demand_mix['hydrogen.gaseous_hydrogen.energy_demand_mix'] = pd.DataFrame({'years': self.years,
                                                                                              'mix': np.arange(50, 81)})
        self.energy_demand_mix['methane.energy_demand_mix'] = pd.DataFrame({'years': self.years,
                                                                            'mix': np.arange(20, 51)})
        self.energy_demand_mix['carbon_storage.energy_demand_mix'] = pd.DataFrame({'years': self.years,
                                                                                   'mix': np.arange(50, 81)})
        self.energy_demand_mix['carbon_capture.energy_demand_mix'] = pd.DataFrame({'years': self.years,
                                                                                   'mix': np.arange(50, 81)})
        self.scaling_factor_techno_consumption = 1e3
        self.scaling_factor_techno_production = 1e3

    def tearDown(self):
        pass

    def test_01_demand_discipline(self):

        self.name = 'Test'
        self.model_name = 'Demand'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_demand': f'{self.name}.{self.model_name}',
                   'ns_energy_mix': f'{self.name}.{self.model_name}',
                   'ns_ccs': f'{self.name}.{self.model_name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.demand.demand_mix_disc.DemandMixDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{self.model_name}.year_start': 2020,
                       f'{self.name}.{self.model_name}.year_end': 2050,
                       f'{self.name}.energy_list': self.energy_list,
                       f'{self.name}.{self.model_name}.hydrogen.gaseous_hydrogen.energy_demand_mix': self.energy_demand_mix['hydrogen.gaseous_hydrogen.energy_demand_mix'],
                       f'{self.name}.{self.model_name}.methane.energy_demand_mix': self.energy_demand_mix['methane.energy_demand_mix'],
                       f'{self.name}.{self.model_name}.carbon_storage.energy_demand_mix': self.energy_demand_mix['carbon_storage.energy_demand_mix'],
                       f'{self.name}.{self.model_name}.carbon_capture.energy_demand_mix': self.energy_demand_mix['carbon_capture.energy_demand_mix'],
                       f'{self.name}.{self.model_name}.total_energy_demand': self.total_energy_demand}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        # gather discipline outputs
        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        h2_demand = disc.get_sosdisc_outputs(
            'hydrogen.gaseous_hydrogen.energy_demand')
        ch4_demand = disc.get_sosdisc_outputs('methane.energy_demand')

        # build ref data
        total_demand = self.total_energy_demand['demand']
        h2_mix = self.energy_demand_mix['hydrogen.gaseous_hydrogen.energy_demand_mix']['mix']
        h2_dmd_ref = pd.DataFrame(
            {'years': self.years, 'demand': total_demand * h2_mix / 100.})
        ch4_mix = self.energy_demand_mix['methane.energy_demand_mix']['mix']
        ch4_dmd_ref = pd.DataFrame(
            {'years': self.years, 'demand': total_demand * ch4_mix / 100.})
        # compare outputs to ref
        assert_frame_equal(h2_demand, h2_dmd_ref)
        assert_frame_equal(ch4_demand, ch4_dmd_ref)
