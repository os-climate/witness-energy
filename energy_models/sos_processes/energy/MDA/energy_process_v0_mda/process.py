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

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.models.carbon_storage.pure_carbon_solid_storage.pure_carbon_solid_storage import PureCarbonSS
from energy_models.sos_processes.energy.MDA.energy_process_v0.usecase import CCS_NAME
from energy_models.sos_processes.witness_sub_process_builder import WITNESSSubProcessBuilder


class ProcessBuilder(WITNESSSubProcessBuilder):

    # ontology information
    _ontology_data = {
        'label': 'Energy MDA v0 Process',
        'description': '',
        'category': '',
        'version': '',
    }

    def get_builders(self):

        ns_study = self.ee.study_name
        energy_mix = EnergyMix.name
        carbon_storage = PureCarbonSS.energy_name
        ccs_mix = CCS_NAME
        # if one invest discipline then we need to setup all subprocesses
        # before get them
        if hasattr(self, 'techno_dict') and hasattr(self, 'invest_discipline'):
            builder_list = self.ee.factory.get_builder_from_process(
                'energy_models.sos_processes.energy.MDA', 'energy_process_v0',
                techno_dict=self.techno_dict, invest_discipline=self.invest_discipline)
        else:
            # else we get them the old fashioned way
            builder_list = self.ee.factory.get_builder_from_process(
                'energy_models.sos_processes.energy.MDA', 'energy_process_v0')

        ns_dict = {'ns_energy': f'{ns_study}.{energy_mix}',
                   'ns_carb':  f'{ns_study}.{ccs_mix}.{carbon_storage}.PureCarbonSolidStorage',
                   'ns_ref': f'{ns_study}.NormalizationReferences',
                   'ns_emissions': f'{ns_study}.{energy_mix}', }

        self.ee.ns_manager.add_ns_def(ns_dict)

        self.ee.post_processing_manager.add_post_processing_module_to_namespace(
            'ns_energy', 'energy_models.sos_processes.post_processing.post_proc_capex_comparison')

        return builder_list
