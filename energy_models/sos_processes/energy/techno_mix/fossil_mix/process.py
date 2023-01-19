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

from energy_models.core.energy_process_builder import EnergyProcessBuilder,\
    INVEST_DISCIPLINE_OPTIONS
from energy_models.core.stream_type.energy_models.fossil import Fossil
from energy_models.sos_processes.energy.techno_mix.fossil_mix.usecase import TECHNOLOGIES_LIST


class ProcessBuilder(EnergyProcessBuilder):

    # ontology information
    _ontology_data = {
        'label': 'Energy Technology Mix - Fossil Mix',
        'description': '',
        'category': '',
        'version': '',
    }

    def __init__(self, ee):
        EnergyProcessBuilder.__init__(self, ee)
        self.techno_list = TECHNOLOGIES_LIST

    def get_builders(self):

        ns_study = self.ee.study_name

        fossil_name = Fossil.name
        energy_mix = 'EnergyMix'
        ns_dict = {'ns_fossil': f'{ns_study}.{energy_mix}.{fossil_name}',
                   'ns_energy': f'{ns_study}.{energy_mix}',
                   'ns_energy_study': f'{ns_study}',
                   'ns_public': f'{ns_study}',
                   'ns_functions': f'{ns_study}',
                   'ns_ref': f'{ns_study}',
                   'ns_resource': f'{ns_study}.{energy_mix}'}
        mods_dict = {}
        mods_dict[f'{energy_mix}.{fossil_name}'] = self.get_stream_disc_path(
            'energy_disciplines', 'Fossil')
        for techno_name in self.techno_list:

            sub_dir = None
            mods_dict[f'{energy_mix}.{fossil_name}.{techno_name}'] = self.get_techno_disc_path(
                fossil_name, techno_name, sub_dir)

        builder_list = self.create_builder_list(mods_dict, ns_dict=ns_dict, associate_namespace=self.associate_namespace)
        if self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[0]:
            mods_dict_invest = {f'{energy_mix}.{fossil_name}': 'energy_models.core.investments.disciplines.techno_invest_disc.InvestTechnoDiscipline',
                                }

            builder_list_invest = self.create_builder_list(
                mods_dict_invest, ns_dict=ns_dict)
            builder_list.extend(builder_list_invest)

        return builder_list
