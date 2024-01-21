'''
Copyright 2022 Airbus SAS
Modifications on 2023/07/13-2023/11/03 Copyright 2023 Capgemini

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

from climateeconomics.sos_processes.iam.witness.witness_optim_sub_process.usecase_witness_optim_sub import OPTIM_NAME
from energy_models.core.energy_process_builder import INVEST_DISCIPLINE_OPTIONS
from energy_models.core.energy_study_manager import DEFAULT_TECHNO_DICT
from energy_models.sos_processes.witness_sub_process_builder import WITNESSSubProcessBuilder
from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from energy_models.core.stream_type.energy_models.heat import lowtemperatureheat
from energy_models.core.stream_type.energy_models.heat import mediumtemperatureheat
from energy_models.sos_processes.energy.techno_mix.hightemperatureheat_mix.usecase import \
    TECHNOLOGIES_LIST_DEV as hightemperatureheat_technos_dev
from energy_models.sos_processes.energy.techno_mix.lowtemperatureheat_mix.usecase import \
    TECHNOLOGIES_LIST_DEV as lowtemperatureheat_technos_dev
from energy_models.sos_processes.energy.techno_mix.mediumtemperatureheat_mix.usecase import \
    TECHNOLOGIES_LIST_DEV as mediumtemperatureheat_technos_dev
from energy_models.core.energy_study_manager import AGRI_TYPE, ENERGY_TYPE
from energy_models.sos_processes.energy.techno_mix.methane_mix.usecase import \
    TECHNOLOGIES_LIST_DEV as Methane_technos_dev
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.sos_processes.energy.techno_mix.electricity_mix.usecase import \
    TECHNOLOGIES_LIST_DEV as Electricity_technos_dev
from energy_models.core.stream_type.energy_models.electricity import Electricity
DEFAULT_TECHNO_DICT = {
                       # Electricity.name: {'type': ENERGY_TYPE, 'value': Electricity_technos_dev},
                       # Methane.name: {'type': ENERGY_TYPE, 'value': Methane_technos_dev},
                       hightemperatureheat.name: {'type': ENERGY_TYPE, 'value': hightemperatureheat_technos_dev},
                       mediumtemperatureheat.name: {'type': ENERGY_TYPE, 'value': mediumtemperatureheat_technos_dev},
                       lowtemperatureheat.name: {'type': ENERGY_TYPE, 'value': lowtemperatureheat_technos_dev},
                       }

class ProcessBuilder(WITNESSSubProcessBuilder):

    # ontology information
    _ontology_data = {
        'label': 'Heat Optimization Process',
        'description': '',
        'category': '',
        'version': '',
    }

    def get_builders(self):

        optim_name = OPTIM_NAME


        # if one invest discipline then we need to setup all subprocesses
        # before get them
        techno_dict = DEFAULT_TECHNO_DICT

        coupling_builder = self.ee.factory.get_builder_from_process(
            'witness-energy.energy_models.sos_processes.energy.MDA', 'heat_optim_sub_process', #_v0
            techno_dict=techno_dict, invest_discipline=INVEST_DISCIPLINE_OPTIONS[1])

        # coupling_builder = self.ee.factory.get_builder_from_process(
        #     'energy_models.sos_processes.energy.MDA', 'heat_process_v0',
        #     techno_dict=techno_dict, invest_discipline=INVEST_DISCIPLINE_OPTIONS[1])

        # modify namespaces defined in the child process
        self.ee.ns_manager.update_namespace_list_with_extra_ns(
            optim_name, after_name=self.ee.study_name, clean_namespaces = True, clean_all_ns_with_name = True)  # optim_name

        #-- set optim builder
        opt_builder = self.ee.factory.create_optim_builder(
            optim_name, [coupling_builder])
        self.ee.post_processing_manager.add_post_processing_module_to_namespace(
            'ns_optim',
            'climateeconomics.sos_wrapping.sos_wrapping_witness.post_proc_witness_optim.post_processing_witness_full')

        return opt_builder
