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
import unittest
import pandas as pd
import numpy as np
from os.path import join, dirname
from sos_trades_core.execution_engine.execution_engine import ExecutionEngine


class FlueGasRatioTestCase(unittest.TestCase):
    """
    FlueGas ratio prices test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        years = np.arange(2020, 2051)

        self.electricity_CoalGen_production = pd.DataFrame({'years': years,
                                                            'CO2 from Flue Gas (Mt)': 10000.0})

        self.hydrogen_WaterGasShift_production = pd.DataFrame({'years': years,
                                                               'CO2 from Flue Gas (Mt)': 20000.0})
        self.scaling_factor_techno_consumption = 1e3
        self.scaling_factor_techno_production = 1e3

    def tearDown(self):
        pass

    def test_01_fluegas_discipline(self):

        self.name = 'Test'
        self.model_name = 'flue_gas'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_flue_gas': f'{self.name}.{self.model_name}',
                   'ns_energy_mix': f'{self.name}',
                   'ns_public': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.stream_type.carbon_disciplines.flue_gas_disc.FlueGasDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{self.model_name}.technologies_list': ['hydrogen.gaseous_hydrogen.WaterGasShift', 'electricity.CoalGen'],
                       f'{self.name}.electricity.CoalGen.techno_production': self.electricity_CoalGen_production,
                       f'{self.name}.hydrogen.gaseous_hydrogen.WaterGasShift.techno_production': self.hydrogen_WaterGasShift_production,
                       f'{self.name}.electricity.CoalGen.flue_gas_co2_ratio': [0.2],
                       f'{self.name}.hydrogen.gaseous_hydrogen.WaterGasShift.flue_gas_co2_ratio': [0.4],
                       f'{self.name}.{self.model_name}.scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       f'{self.name}.{self.model_name}.scaling_factor_techno_production': self.scaling_factor_techno_production, }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)
#         for graph in graph_list:
#             graph.to_plotly().show()

    def test_02_fluegas_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'flue_gas'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_flue_gas': f'{self.name}.{self.model_name}',
                   'ns_energy_mix': f'{self.name}',
                   'ns_public': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.stream_type.carbon_disciplines.flue_gas_disc.FlueGasDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.year_end': 2050,
                       f'{self.name}.{self.model_name}.technologies_list': ['hydrogen.gaseous_hydrogen.WaterGasShift', 'electricity.CoalGen'],
                       f'{self.name}.electricity.CoalGen.techno_production': self.electricity_CoalGen_production,
                       f'{self.name}.hydrogen.gaseous_hydrogen.WaterGasShift.techno_production': self.hydrogen_WaterGasShift_production,
                       f'{self.name}.electricity.CoalGen.flue_gas_co2_ratio': [0.2],
                       f'{self.name}.hydrogen.gaseous_hydrogen.WaterGasShift.flue_gas_co2_ratio': [0.4],
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production, }
        self.ee.load_study_from_input_dict(inputs_dict)

        disc_techno = self.ee.root_process.sos_disciplines[0]

        succeed = disc_techno.check_jacobian(derr_approx='complex_step', inputs=[f'{self.name}.electricity.CoalGen.techno_production',
                                                                                 f'{self.name}.hydrogen.gaseous_hydrogen.WaterGasShift.techno_production',
                                                                                 f'{self.name}.electricity.CoalGen.flue_gas_co2_ratio'],
                                             outputs=[
            f'{self.name}.{self.model_name}.flue_gas_mean',
            f'{self.name}.{self.model_name}.flue_gas_production',
            f'{self.name}.{self.model_name}.flue_gas_prod_ratio'],
            load_jac_path=join(dirname(__file__), 'jacobian_pkls',
                               f'jacobian_fluegas_discipline.pkl'))

        self.assertTrue(
            succeed, msg=f"Wrong gradient in {disc_techno.get_disc_full_name()}")
