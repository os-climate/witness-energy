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
import unittest

from sostrades_core.execution_engine.execution_engine import ExecutionEngine

from energy_models.glossaryenergy import GlossaryEnergy


class ResourcesDisc(unittest.TestCase):
    """
    Resources prices test class
    """

    def setUp(self):
        

        pass

    def test_01_resources_discipline(self):
        self.name = 'Test'
        self.model_name = 'resources'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name,
                   'ns_energy': self.name,
                   'ns_energy_study': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.stream_type.resources_data_disc.ResourcesDisc'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearStart}': GlossaryEnergy.YearStartDefault,
                       f'{self.name}.{GlossaryEnergy.YearEnd}': GlossaryEnergy.YearEndDefault
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

#         for graph in graph_list:
#             graph.to_plotly().show()
