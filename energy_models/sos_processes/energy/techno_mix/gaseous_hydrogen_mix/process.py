'''
Copyright 2022 Airbus SAS
Modifications on 23/11/2023 Copyright 2023 Capgemini

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

from energy_models.core.energy_process_builder import EnergyProcessBuilder
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import GaseousHydrogen
from energy_models.core.stream_type.energy_models.syngas import Syngas
from energy_models.models.carbon_storage.pure_carbon_solid_storage.pure_carbon_solid_storage import PureCarbonSS
from energy_models.sos_processes.energy.techno_mix.gaseous_hydrogen_mix.usecase import TECHNOLOGIES_LIST


class ProcessBuilder(EnergyProcessBuilder):

    # ontology information
    _ontology_data = {
        'label': 'Energy Technology Mix - Gaseous Hydrogen Mix',
        'description': '',
        'category': '',
        'version': '',
    }

    def __init__(self, ee):
        EnergyProcessBuilder.__init__(self, ee)
        self.techno_list = TECHNOLOGIES_LIST

    def get_builders(self):

        ns_study = self.ee.study_name

        gaseous_hydrogen_name = GaseousHydrogen.name
        carbon_storage = PureCarbonSS.energy_name
        energy_mix = 'EnergyMix'
        ns_dict = {'ns_hydrogen': f'{ns_study}.{energy_mix}.{gaseous_hydrogen_name}',
                   'ns_energy': f'{ns_study}.{energy_mix}',
                   'ns_energy_study': f'{ns_study}',
                   'ns_public': f'{ns_study}',
                   'ns_syngas': f'{ns_study}.{energy_mix}.{Syngas.name}',
                   'ns_energy_mix': f'{ns_study}.{energy_mix}',
                   'ns_carb':  f'{ns_study}.{energy_mix}.{carbon_storage}.PureCarbonSolidStorage',
                   'ns_resource': f'{ns_study}.{energy_mix}'}
        mods_dict = {}
        mods_dict[f'{energy_mix}.{gaseous_hydrogen_name}'] = self.get_stream_disc_path(
            'energy_disciplines', 'GaseousHydrogen')
        for techno_name in self.techno_list:
            mods_dict[f'{energy_mix}.{gaseous_hydrogen_name}.{techno_name}'] = self.get_techno_disc_path(
                GaseousHydrogen.short_name, techno_name)

        builder_list = self.create_builder_list(mods_dict, ns_dict=ns_dict, associate_namespace=self.associate_namespace)
        return builder_list
