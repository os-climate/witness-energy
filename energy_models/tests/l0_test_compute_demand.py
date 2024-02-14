'''
Copyright 2022 Airbus SAS
Modifications on 2023/09/06-2023/11/16 Copyright 2023 Capgemini

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

from energy_models.core.demand.energy_demand import EnergyDemand
from energy_models.glossaryenergy import GlossaryEnergy
from sostrades_core.execution_engine.execution_engine import ExecutionEngine


class DemandTestCase(unittest.TestCase):
    """
    Demand computation tests
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.year_start = GlossaryEnergy.YeartStartDefault
        self.year_end = GlossaryEnergy.YeartEndDefault
        self.years = np.arange(self.year_start, self.year_end + 1)

        self.energy_production_detailed = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                                        EnergyDemand.elec_prod_column: 25000.0})
        self.population = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                        GlossaryEnergy.PopulationValue: np.linspace(7794.79, 9000., len(self.years))})
        self.transport_demand = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                              GlossaryEnergy.TransportDemandValue: np.linspace(33000., 33000.,
                                                                                               len(self.years))})

    def tearDown(self):
        pass

    def test_01_demand_discipline(self):
        self.name = 'Test'
        self.model_name = 'Demand'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': f'{self.name}',
                   GlossaryEnergy.NS_REFERENCE: f'{self.name}',
                   GlossaryEnergy.NS_FUNCTIONS: f'{self.name}.{self.model_name}',
                   GlossaryEnergy.NS_ENERGY_MIX: f'{self.name}',
                   GlossaryEnergy.NS_WITNESS: f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.demand.energy_demand_disc.EnergyDemandDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearStart}': self.year_start,
                       f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.EnergyProductionDetailedValue}': self.energy_production_detailed,
                       f'{self.name}.{GlossaryEnergy.PopulationDfValue}': self.population,
                       f'{self.name}.Demand.{GlossaryEnergy.TransportDemandValue}': self.transport_demand
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
