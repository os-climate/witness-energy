'''
Copyright 2022 Airbus SAS
Modifications on 2023/05/02-2023/11/03 Copyright 2023 Capgemini

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
from climateeconomics.glossarycore import GlossaryCore
from energy_models.core.energy_process_builder import INVEST_DISCIPLINE_OPTIONS
# from energy_models.core.energy_study_manager import DEFAULT_TECHNO_DICT
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
        'label': 'WITNESS Process',
        'description': '',
        'category': '',
        'version': '',
    }

    def __init__(self, ee, process_level='val'):
        WITNESSSubProcessBuilder.__init__(
            self, ee)
        self.invest_discipline = INVEST_DISCIPLINE_OPTIONS[1]
        self.process_level = process_level

    def get_builders(self):

        chain_builders = []
        # retrieve energy process

        # if self.process_level == 'dev':
        #     chain_builders_witness = self.ee.factory.get_builder_from_process(
        #         'climateeconomics.sos_processes.iam', 'witness_wo_energy_dev')
        #     # chain_builders_witness = self.ee.factory.get_builder_from_process(
        #     #     'energy_models.sos_processes.energy.MDA', 'heat_process_v0')
        #
        # # 'energy_models.sos_processes.energy.MDA.heat_process_v0'
        #
        # else:
        #     chain_builders_witness = self.ee.factory.get_builder_from_process(
        #         'climateeconomics.sos_processes.iam', 'witness_wo_energy')


        # chain_builders.extend(chain_builders_witness)

        # if one invest discipline then we need to setup all subprocesses
        # before get them
        techno_dict = DEFAULT_TECHNO_DICT

        chain_builders_energy = self.ee.factory.get_builder_from_process(
            'energy_models.sos_processes.energy.MDA', 'heat_process_v0_mda',
            techno_dict=self.techno_dict, invest_discipline=self.invest_discipline)
        chain_builders.extend(chain_builders_energy)

        # Update namespace regarding land use and energy mix coupling
        ns_dict = {'ns_land_use': f'{self.ee.study_name}.EnergyMix',
                   'ns_functions': f'{self.ee.study_name}.EnergyMix',
                   'ns_ref': f'{self.ee.study_name}.NormalizationReferences',
                   'ns_invest': f'{self.ee.study_name}.InvestmentDistribution',
                   }

        self.ee.ns_manager.add_ns_def(ns_dict)

        # # FIXME: post_processing is broken after merge of witness-full !
        # # self.ee.post_processing_manager.add_post_processing_module_to_namespace(
        # #     GlossaryCore.NS_WITNESS,
        # #     'climateeconomics.sos_wrapping.sos_wrapping_witness.post_proc_witness_optim.post_processing_witness_full')
        # for resource_namespace in ['ns_coal_resource', 'ns_oil_resource', 'ns_natural_gas_resource',
        #                            'ns_uranium_resource', 'ns_copper_resource']:
        #     self.ee.post_processing_manager.add_post_processing_module_to_namespace(
        #         resource_namespace,
        #         'climateeconomics.sos_wrapping.sos_wrapping_resources.post_proc_resource.post_processing_resource')
        #
        # self.ee.post_processing_manager.add_post_processing_module_to_namespace(GlossaryCore.NS_WITNESS,
        #                                                                         'climateeconomics.sos_wrapping.sos_wrapping_witness.post_proc_ssp_comparison.post_processing_ssp_comparison')
        #
        return chain_builders
