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

from energy_models.core.process_builder_database import ProcessBuilderDatabase
from energy_models.core.stream_type.energy_models.electricity import Electricity
from os.path import join, dirname 

class ProcessBuilder(ProcessBuilderDatabase):

    # ontology information
    _ontology_data = {
        'label': 'Nuclear regionalization process',
        'description': '',
        'category': '',
        'version': '',
    }

    def get_builders(self):

        ns_study = self.ee.study_name

        electricity_name = Electricity.name
        ns_dict = {'ns_electricity': f'{ns_study}',
                   'ns_energy': f'{ns_study}',
                   'ns_energy_study': f'{ns_study}',
                   'ns_public': f'{ns_study}',
                   'ns_functions': f'{ns_study}',
                   'ns_ref': f'{ns_study}',
                   'ns_resource': f'{ns_study}'}
        mods_dict_europe = {'Nuclear_Europe': 'energy_models.models.electricity.nuclear_modified.nuclear_disc.NuclearDiscipline'}
        mods_dict_us = {'Nuclear_US': 'energy_models.models.electricity.nuclear_modified.nuclear_disc.NuclearDiscipline'}

        ns_us = {'ns_electricity_nuc': f'{ns_study}.Nuclear_US'}
        #ns_us.update(ns_dict) 

        ns_europe = {'ns_electricity_nuc': f'{ns_study}.Nuclear_Europe'} 
        #ns_europe.update(ns_dict)       
        builder_europe = self.create_builder_list(mods_dict_europe, ns_dict=ns_dict, associate_namespace=False)
        builder_US = self.create_builder_list(mods_dict_us, ns_dict=ns_dict, associate_namespace=False)
        file_path = join(dirname(dirname(dirname(dirname(__file__)))), 'regionalization_data', 'data_nuclear_test.json')
        self.set_builder_specific_ns_database(builder_europe , ns_dict = ns_europe, associate_namespace=True, database_location=file_path, database_name='Europe')
        self.set_builder_specific_ns_database(builder_US , ns_dict = ns_us, associate_namespace=True, database_location=file_path, database_name='US')

        return [builder_europe, builder_US]
