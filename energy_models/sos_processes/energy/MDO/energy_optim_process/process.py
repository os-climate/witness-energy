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
from sos_trades_core.sos_processes.base_process_builder import BaseProcessBuilder


class ProcessBuilder(BaseProcessBuilder):

    # ontology information
    _ontology_data = {
        'label': 'Energy Optimisation Process',
        'description': '',
        'category': '',
        'version': '',
    }

    def get_builders(self):

        optim_name = "EnergyOptimization"

        #-- retrieve energy optim sub process
        coupling_builder = self.ee.factory.get_builder_from_process(
            'energy_models.sos_processes.energy.MDO_subprocesses', 'energy_optim_sub_process_mda')

        # modify namespaces defined in the child process
        self.ee.ns_manager.update_namespace_list_with_extra_ns(
            optim_name, after_name=self.ee.study_name)  # optim_name

        #-- set optim builder
        opt_builder = self.ee.factory.create_optim_builder(
            optim_name, [coupling_builder])

        return opt_builder
