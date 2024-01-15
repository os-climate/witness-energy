'''
Copyright 2023 Capgemini

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
# -*- coding: utf-8 -*-

from sostrades_core.sos_processes.base_process_builder import BaseProcessBuilder


class ProcessBuilder(BaseProcessBuilder):

    COUPLING_NAME = "Heat_Mix"
    # ontology information
    _ontology_data = {
        'label': 'Energy Asset Portfolio Optimization Subprocess',
        'description': '',
        'category': '',
        'version': '',
    }

    def get_builders(self, proc_name='heat_process_v0'):
        designvariable_name = "DesignVariables"
        func_manager_name = "FunctionsManager"
        energy_mix_name = 'EnergyMix'

        # retrieve subprocess wieth the asset mix
        energy_mix_builder_list = self.ee.factory.get_builder_from_process(
            'energy_models.sos_processes.energy.MDA', proc_name)

        # design variables builder
        design_var_path = 'sostrades_core.execution_engine.design_var.design_var_disc.DesignVarDiscipline'
        design_var_builder = self.ee.factory.get_builder_from_module(
            f'{designvariable_name}', design_var_path)
        energy_mix_builder_list.append(design_var_builder)

        # function manager builder
        fmanager_path = 'sostrades_core.execution_engine.func_manager.func_manager_disc.FunctionManagerDisc'
        fmanager_builder = self.ee.factory.get_builder_from_module(
            f'{func_manager_name}', fmanager_path)
        energy_mix_builder_list.append(fmanager_builder)

        # modify namespaces defined in the shared_dict
        self.ee.ns_manager.update_namespace_list_with_extra_ns(
            self.COUPLING_NAME, after_name=self.ee.study_name)
        # update namespaces which are associated in builder_list
        for builder in energy_mix_builder_list:
            builder.update_associated_namespaces_with_extra_name(self.COUPLING_NAME, after_name=self.ee.study_name)

        # Add new namespaces in the shared_ns_dict
        ns_dict = {'ns_functions': f'{self.ee.study_name}.{energy_mix_name}',
                   'ns_optim': f'{self.ee.study_name}',
                   'ns_ref': f'{self.ee.study_name}.NormalizationReferences', }
        self.ee.ns_manager.add_ns_def(ns_dict)

        # create coupling builder
        coupling_builder = self.ee.factory.create_builder_coupling(
            self.COUPLING_NAME)
        coupling_builder.set_builder_info('cls_builder', energy_mix_builder_list)

        return coupling_builder
