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
from energy_models.core.energy_process_builder import EnergyProcessBuilder
from energy_models.core.stream_type.energy_models.heat import mediumtemperatureheat
from energy_models.glossaryenergy import GlossaryEnergy


class ProcessBuilder(EnergyProcessBuilder):
    # ontology information
    _ontology_data = {
        'label': 'Energy Technology Mix - Medium Heat Mix',
        'description': '',
        'category': '',
        'version': '',
    }

    def __init__(self, ee):
        EnergyProcessBuilder.__init__(self, ee)
        self.techno_list = GlossaryEnergy.DEFAULT_TECHNO_DICT_DEV[GlossaryEnergy.mediumtemperatureheat_energyname]['value']

    def get_builders(self):
        ns_study = self.ee.study_name
        # heat = 'Heat'
        heat_name = mediumtemperatureheat.name
        energy_mix = 'EnergyMix'
        ns_dict = {'ns_heat_medium': f'{ns_study}.{energy_mix}.{heat_name}',
                   'ns_energy': f'{ns_study}.{energy_mix}',
                   'ns_energy_study': f'{ns_study}',
                   GlossaryEnergy.NS_ENERGY_MIX: f'{ns_study}.{energy_mix}',
                   GlossaryEnergy.NS_WITNESS: f'{ns_study}',
                   GlossaryEnergy.NS_CCS: f'{ns_study}.{GlossaryEnergy.CCUS}',
                   'ns_public': f'{ns_study}', 'ns_resource': f'{ns_study}.{energy_mix}'}

        mods_dict = {}
        mods_dict[f'{energy_mix}.{heat_name}'] = self.get_stream_disc_path(
            'energy_disciplines', 'MediumHeat')
        # to get sub dictionary
        for techno_name in self.techno_list:
            mods_dict[f'{energy_mix}.{heat_name}.{techno_name}'] = self.get_techno_disc_path(
                GlossaryEnergy.heat, techno_name, sub_dir='medium')

        builder_list = self.create_builder_list(mods_dict, ns_dict=ns_dict,
                                                associate_namespace=self.associate_namespace)
        return builder_list
