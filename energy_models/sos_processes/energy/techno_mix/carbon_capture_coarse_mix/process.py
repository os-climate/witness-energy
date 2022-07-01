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

from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.carbon_models.flue_gas import FlueGas
from energy_models.sos_processes.energy.techno_mix.carbon_capture_coarse_mix.usecase_coarse import TECHNOLOGIES_LIST


class ProcessBuilder(EnergyProcessBuilder):

    # ontology information
    _ontology_data = {
        'label': 'Energy Technology Mix - Carbon Capture Coarse Mix',
        'description': '',
        'category': '',
        'version': '',
    }

    def __init__(self, ee):
        EnergyProcessBuilder.__init__(self, ee)
        self.techno_list = TECHNOLOGIES_LIST
        self.prefix_name = 'EnergyMix'

    def get_builders(self):

        ns_study = self.ee.study_name
        energy_mix = 'EnergyMix'
        flue_gas_name = FlueGas.node_name
        carbon_capture_name = CarbonCapture.name
        ns_dict = {'ns_carbon_capture': f'{ns_study}.{self.prefix_name}.{carbon_capture_name}',
                   'ns_energy': f'{ns_study}.{energy_mix}',
                   'ns_energy_study': f'{ns_study}',
                   'ns_flue_gas': f'{ns_study}.{self.prefix_name}.{carbon_capture_name}.{flue_gas_name}',
                   'ns_public': f'{ns_study}',
                   'ns_energy_mix': f'{ns_study}.{energy_mix}',
                   'ns_resource': f'{ns_study}.{energy_mix}',
                   'ns_ccs': f'{ns_study}.{energy_mix}',
                   }
        mods_dict = {}
        mods_dict[f'{self.prefix_name}.{carbon_capture_name}'] = self.get_stream_disc_path(
            'carbon_disciplines', 'CarbonCapture')
        mods_dict[f'{self.prefix_name}.{carbon_capture_name}.{flue_gas_name}'] = 'energy_models.core.stream_type.carbon_disciplines.flue_gas_disc.FlueGasDiscipline'
        for full_techno_name in self.techno_list:
            list_dot = full_techno_name.split('.')
            sub_dir = list_dot[0]
            techno_name = list_dot[1]
            mods_dict[f'{self.prefix_name}.{carbon_capture_name}.{full_techno_name}'] = self.get_techno_disc_path(
                carbon_capture_name, techno_name, sub_dir)

        builder_list = self.create_builder_list(mods_dict, ns_dict=ns_dict)

        if self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[0]:
            mods_dict_invest = {f'{self.prefix_name}.{carbon_capture_name}':
                                'energy_models.core.investments.disciplines.techno_invest_disc.InvestTechnoDiscipline'}

            builder_list_invest = self.create_builder_list(
                mods_dict_invest, ns_dict=ns_dict)
            builder_list.extend(builder_list_invest)

        return builder_list
