'''
Copyright 2022 Airbus SAS
Modifications on 2023/03/21-2023/11/03 Copyright 2023 Capgemini

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
from sostrades_core.sos_processes.base_process_builder import BaseProcessBuilder


class ProcessBuilderDatabase(BaseProcessBuilder):
    '''
    Generic class to inherit to build processes
    '''

    def __init__(self, ee):
        '''
        Constructor
        link to execution engine
        '''
        self.ee = ee

    def get_builders(self):
        return []

    def process_namespace(self, ns_dict=None, get_from_database=False):
        '''
        Adds a namespace definition to the EE namespace manager and returns the associated namespace ID(s).

        Parameters:
        ns_dict (dict): The namespace definition to add.
        associate_namespace (bool): If True, associates the namespace with builders. 
        database_name (str): The name of the database.

        Returns:
        A list of namespace IDs associated with the added namespace definition.
        '''
        ns_ids = []
        if ns_dict is not None:
            ns_ids = self.ee.ns_manager.add_ns_def(ns_dict, get_from_database=get_from_database)

        return ns_ids

    def create_builder_list(self, mods_dict, ns_dict=None, associate_namespace=False,  get_from_database=False):
        ''' 
        define a base namespace
        instantiate builders iterating over a list of module paths
        return the list of disciplines built
        '''
        ns_ids = self.process_namespace(ns_dict, get_from_database)
        builders = []
        for disc_name, mod_path in mods_dict.items():
            a_b = self.ee.factory.get_builder_from_module(disc_name, mod_path)
            if associate_namespace:
                a_b.associate_namespaces(ns_ids)
            builders.append(a_b)
        return builders

    def set_builder_specific_ns_database(self, builders_list, ns_dict=None, associate_namespace=False, get_from_database=False):
        '''
        Associates specific namespace dictionaries with their respective builders and/or saves them to a database.

        Parameters:
        builders_list (list): A list of builder objects.
        ns_dict (dict): A dictionary of namespaces.
        associate_namespace (bool): If True, associates the namespace dictionary with the builder(s). 
        database_location (str): The path to the directory where the database will be saved.
        database_name (str): The name of the database.

        Returns:
        None
        '''
        ns_ids = self.process_namespace(ns_dict, get_from_database)
        for builder in builders_list:
            if associate_namespace: 
                builder.associate_namespaces(ns_ids)
