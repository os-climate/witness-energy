'''
TODO Header
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

    def process_namespace(self, ns_dict=None,database_location=None, database_name=None):
        '''
        Adds a namespace definition to the EE namespace manager and returns the associated namespace ID(s).

        Parameters:
        ns_dict (dict): The namespace definition to add.
        associate_namespace (bool): If True, associates the namespace with builders. 
        database_location (str): The path to the directory where the database will be saved.
        database_name (str): The name of the database.

        Returns:
        A list of namespace IDs associated with the added namespace definition.
        '''
        ns_ids = []
        if ns_dict is not None:
            ns_ids = self.ee.ns_manager.add_ns_def(ns_dict, database_name=database_name)
        if database_location is not None:
            self.ee.ns_manager.database_location = database_location
        return ns_ids

    def create_builder_list(self, mods_dict, ns_dict=None, associate_namespace=False, database_location=None, database_name=None):
        ''' 
        define a base namespace
        instantiate builders iterating over a list of module paths
        return the list of disciplines built
        '''
        ns_ids = self.process_namespace(ns_dict, database_location, database_name)
        builders = []
        for disc_name, mod_path in mods_dict.items():
            a_b = self.ee.factory.get_builder_from_module(disc_name, mod_path)
            if associate_namespace:
                a_b.associate_namespaces(ns_ids)
            builders.append(a_b)
        return builders

    def set_builder_specific_ns_database(self, builders_list, ns_dict=None, associate_namespace=False, database_location=None, database_name=None):
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
        ns_ids = self.process_namespace(ns_dict, database_location, database_name)
        for builder in builders_list:
            if associate_namespace: 
                builder.associate_namespaces(ns_ids)
