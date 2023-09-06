'''
Copyright (c) 2023 Capgemini

All rights reserved

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer
in the documentation and/or mother materials provided with the distribution.
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
INCLUDING BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND OR ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''
from energy_models.core.energy_process_builder import EnergyProcessBuilder,\
    INVEST_DISCIPLINE_OPTIONS
from energy_models.core.stream_type.energy_models.heat import mediumtemperatureheat
from energy_models.sos_processes.energy.techno_mix.mediumheattemperature_mix.usecase import TECHNOLOGIES_LIST


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
        self.techno_list = TECHNOLOGIES_LIST

    def get_builders(self):

        ns_study = self.ee.study_name
        heat = 'Heat'
        heat_name = mediumtemperatureheat.name
        energy_mix = 'EnergyMix'
        ns_dict = {'ns_heat': f'{ns_study}.{energy_mix}.{heat}.{heat_name}',
                   'ns_energy': f'{ns_study}.{energy_mix}',
                   'ns_energy_study': f'{ns_study}',
                   'ns_public': f'{ns_study}', 'ns_resource': f'{ns_study}.{energy_mix}'}

        mods_dict = {}
        mods_dict[f'{energy_mix}.{heat}.{heat_name}'] = self.get_stream_disc_path(
            'energy_disciplines', 'MediumHeat')
        #to get sub dictionary
        for techno_name in self.techno_list:
            mods_dict[f'{energy_mix}.{heat}.{heat_name}.{techno_name}'] = self.get_techno_disc_path(
                'heat', techno_name, sub_dir='medium')

        builder_list = self.create_builder_list(mods_dict, ns_dict=ns_dict, associate_namespace=self.associate_namespace)
        if self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[0]:
            # for sub dictionary
            mods_dict_invest = {f'{energy_mix}.{heat}.{heat_name}': 'energy_models.core.investments.disciplines.techno_invest_disc.InvestTechnoDiscipline',
                                }

            builder_list_invest = self.create_builder_list(
                mods_dict_invest, ns_dict=ns_dict, associate_namespace=self.associate_namespace)

            builder_list.extend(builder_list_invest)
        return builder_list
