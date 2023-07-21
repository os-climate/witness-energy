import unittest

from matplotlib import pyplot as plt
import numpy as np
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from energy_models.sos_processes.energy.MDA.energy_process_v0.usecase import Study
from sostrades_core.tools.post_processing.post_processing_factory import PostProcessingFactory


class PostProcessEnergy(unittest.TestCase):
    def setUp(self):
        """
        setup of test
        """
        self.year_start = 2023
        self.year_end = 2050
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.study_name = 'post-processing'
        self.repo = 'energy_models.sos_processes.energy.MDA'
        self.proc_name = 'energy_process_v0'

        self.ee = ExecutionEngine(self.study_name)
        builder = self.ee.factory.get_builder_from_process(repo=self.repo,
                                                           mod_id=self.proc_name)

        self.ee.factory.set_builders_to_coupling_builder(builder)
        self.ee.configure()

        self.usecase = Study()
        self.usecase.study_name = self.study_name
        values_dict = self.usecase.setup_usecase()
        for values_dict_i in values_dict:
            self.ee.load_study_from_input_dict(values_dict_i)
        self.ee.load_study_from_input_dict({f'{self.study_name}.sub_mda_class': 'MDAGaussSeidel',
                                            f'{self.study_name}.max_mda_iter':1})

        """
        All energy list
        """
        #energylist= ['electricity','methane', 'hydrogen.gaseous_hydrogen', 'biogas', 'syngas', 'fuel.liquid_fuel', \
                      #'fuel.hydrotreated_oil_fuel', 'solid_fuel', 'biomass_dry', \
                       #'fuel.biodiesel', 'fuel.ethanol', 'hydrogen.liquid_hydrogen']
        self.namespace_list = []
        """
        All energy list with study name for post processing
        """
        self.namespace_list.append(f'{self.study_name}')

    def test_post_processing_Table_plots(self):
        """
        Test to compare WITNESS energy capex, opex, CO2 tax prices
        tables for each energy / each techno per energy
        """
        self.ee.execute()
        ppf = PostProcessingFactory()

        for itm in self.namespace_list:
            filters = ppf.get_post_processing_filters_by_namespace(self.ee, itm)
            graph_list = ppf.get_post_processing_by_namespace(self.ee, itm, filters,
                                                              as_json=False)
            #

            for graph in graph_list:
                 #if 'InstanciatedTable' in str(graph.__class__):  # Plotting only  capex, opex, CO2 tax and prices Tables
                    #if graph.chart_name == '':
                graph.to_plotly().show()


if '__main__' == __name__:
    cls = PostProcessEnergy()
    cls.setUp()
    cls.test_post_processing_Table_plots()
