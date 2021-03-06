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
from energy_models.core.demand.energy_demand import EnergyDemand
from energy_models.core.demand.energy_demand_disc import EnergyDemandDiscipline


class DemandTestCase(unittest.TestCase):
    """
    Demand computation tests
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.year_start = 2020
        self.year_end = 2100
        self.years = np.arange(self.year_start, self.year_end + 1)

        self.energy_production_detailed = pd.DataFrame({'years': self.years,
                                                        EnergyDemand.elec_prod_column: 25000.0})
        self.population = pd.DataFrame({'years': self.years,
                                        'population': np.linspace(7794.79, 9000., len(self.years))})
        self.transport_demand = pd.DataFrame({'years': self.years,
                                        'transport_demand': np.linspace(33000., 33000., len(self.years))})
    def tearDown(self):
        pass

    def test_01_demand_discipline(self):

        self.name = 'Test'
        self.model_name = 'Demand'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': f'{self.name}',
                   'ns_ref': f'{self.name}',
                   'ns_functions': f'{self.name}.{self.model_name}',
                   'ns_energy_mix': f'{self.name}',
                   'ns_witness': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.demand.energy_demand_disc.EnergyDemandDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.year_start': self.year_start,
                       f'{self.name}.year_end': self.year_end,
                       f'{self.name}.energy_production_detailed': self.energy_production_detailed,
                       f'{self.name}.population_df': self.population,
                       f'{self.name}.Demand.transport_demand': self.transport_demand
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        # gather discipline outputs
        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]

        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)
#         for graph in graph_list:
#             graph.to_plotly().show()
