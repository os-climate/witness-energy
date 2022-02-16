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
from energy_models.core.stream_type.carbon_models.carbon_storage import CarbonStorage
from energy_models.models.carbon_storage.pure_carbon_solid_storage.pure_carbon_solid_storage import PureCarbonSS
from energy_models.sos_processes.energy.techno_mix.carbon_storage_coarse_mix.usecase_coarse import TECHNOLOGIES_LIST_FOR_OPT


class ProcessBuilder(EnergyProcessBuilder):

    # ontology information
    _ontology_data = {
        'label': 'Energy Technology Mix - Carbon Storage Coarse Mix',
        'description': '',
        'category': '',
        'version': '',
    }

    def __init__(self, ee):
        EnergyProcessBuilder.__init__(self, ee)
        self.techno_list = TECHNOLOGIES_LIST_FOR_OPT
        self.prefix_name = 'EnergyMix'

    def get_builders(self):

        ns_study = self.ee.study_name

        carbon_storage_name = CarbonStorage.name
        carbon_storage = PureCarbonSS.energy_name
        energy_mix = 'EnergyMix'
        func_manager_name = "FunctionManagerDisc"

        ns_dict = {'ns_carbon_storage': f'{ns_study}.{self.prefix_name}.{carbon_storage_name}',
                   'ns_energy': f'{ns_study}.{energy_mix}',
                   'ns_energy_study': f'{ns_study}',
                   'ns_public': f'{ns_study}',
                   'ns_functions': f'{ns_study}.{func_manager_name}',
                   'ns_resource': f'{ns_study}.{energy_mix}'}

        mods_dict = {}
        mods_dict[f'{self.prefix_name}.{carbon_storage_name}'] = self.get_stream_disc_path(
            'carbon_disciplines', 'CarbonStorage')
        for techno_name in self.techno_list:
            mods_dict[f'{self.prefix_name}.{carbon_storage_name}.{techno_name}'] = self.get_techno_disc_path(
                carbon_storage_name, techno_name)

        builder_list = self.create_builder_list(mods_dict, ns_dict=ns_dict)
        if self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[0]:
            mods_dict_invest = {f'{self.prefix_name}.{carbon_storage_name}': 'energy_models.core.investments.disciplines.techno_invest_disc.InvestTechnoDiscipline',
                                }

            builder_list_invest = self.create_builder_list(
                mods_dict_invest, ns_dict=ns_dict)
            builder_list.extend(builder_list_invest)

        return builder_list
