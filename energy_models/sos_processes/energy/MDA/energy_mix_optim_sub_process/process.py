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
from climateeconomics.sos_wrapping.sos_wrapping_emissions.ghgemissions.ghgemissions_discipline import (
    GHGemissionsDiscipline,
)
from sostrades_core.sos_processes.base_process_builder import BaseProcessBuilder

from energy_models.core.energy_process_builder import INVEST_DISCIPLINE_OPTIONS
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.sos_processes.energy.MDA.energy_process_v0.usecase import (
    INVEST_DISC_NAME,
)


class ProcessBuilder(BaseProcessBuilder):
    # ontology information
    _ontology_data = {
        'label': 'Energy Mix Optim sub process',
        'description': '',
        'category': '',
        'version': '',
    }

    def get_builders(self):
        coupling_name = "MDA"
        designvariable_name = "DesignVariables"
        func_manager_name = "FunctionsManager"

        builder_list = []

        chain_builders_energy = self.ee.factory.get_builder_from_process(
            'energy_models.sos_processes.energy.MDA', 'energy_process_v0_mda',
            techno_dict=GlossaryEnergy.DEFAULT_TECHNO_DICT, invest_discipline=INVEST_DISCIPLINE_OPTIONS[2], use_resources_bool=False)


        builder_list.extend(chain_builders_energy)
        builder_list.extend(self.create_builder_list(
            {GHGemissionsDiscipline.name: 'climateeconomics.sos_wrapping.sos_wrapping_emissions.ghgemissions.ghgemissions_discipline.GHGemissionsDiscipline'},
            ns_dict={
                "ns_ghg_emissions": f"{self.ee.study_name}"
            })
        )
        self.ee.ns_manager.update_namespace_list_with_extra_ns(
            'MDA', after_name=self.ee.study_name, clean_existing=True)

        # ---------------------------------------------
        # design variables builder
        design_var_path = 'sostrades_optimization_plugins.models.design_var.design_var_disc.DesignVarDiscipline'
        design_var_builder = self.ee.factory.get_builder_from_module(
            f'{designvariable_name}', design_var_path)
        builder_list.append(design_var_builder)

        # function manager builder
        fmanager_path = 'sostrades_optimization_plugins.models.func_manager.func_manager_disc.FunctionManagerDisc'
        fmanager_builder = self.ee.factory.get_builder_from_module(
            f'{func_manager_name}', fmanager_path)
        builder_list.append(fmanager_builder)

        ns_dict = {GlossaryEnergy.NS_FUNCTIONS: f'{self.ee.study_name}.{coupling_name}.{func_manager_name}',
                   'ns_public': f'{self.ee.study_name}',
                   'ns_optim': f'{self.ee.study_name}',
                   'ns_invest': f'{self.ee.study_name}.{coupling_name}.{INVEST_DISC_NAME}', }
        self.ee.ns_manager.add_ns_def(ns_dict)

        # ---------------------------------------------


        # create coupling builder
        coupling_builder = self.ee.factory.create_builder_coupling(coupling_name)
        coupling_builder.set_builder_info('cls_builder', builder_list)

        return coupling_builder
