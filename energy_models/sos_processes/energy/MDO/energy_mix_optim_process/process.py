'''
Copyright 2024 Capgemini
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

from sostrades_core.sos_processes.base_process_builder import BaseProcessBuilder


class ProcessBuilder(BaseProcessBuilder):
    # ontology information
    _ontology_data = {
        'label': 'Energy Mix Optim process',
        'description': '',
        'category': '',
        'version': '',
    }

    def get_builders(self):
        builders = self.ee.factory.get_builder_from_process('energy_models.sos_processes.energy.MDA', 'energy_mix_optim_sub_process')

        designvariable_name = "DesignVariables"
        func_manager_name = "FunctionsManager"

        # design variables builder
        ns_dict = {
            'ns_optim': self.ee.study_name
        }
        mods_dict = {
            designvariable_name: 'sostrades_core.execution_engine.design_var.design_var_disc.DesignVarDiscipline'
        }
        builder_dvar = self.create_builder_list(mods_dict, ns_dict=ns_dict, associate_namespace=False)
        builders.extend(builder_dvar)

        # function manager builder

        ns_dict = {
            #'ns_optim': self.ee.study_name
        }
        mods_dict = {
            func_manager_name: 'sostrades_core.execution_engine.func_manager.func_manager_disc.FunctionManagerDisc'
        }
        builder_fmanager = self.create_builder_list(mods_dict, ns_dict=ns_dict, associate_namespace=False)
        builders.extend(builder_fmanager)

        return builders
