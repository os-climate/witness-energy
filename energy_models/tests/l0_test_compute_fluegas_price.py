'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/14-2024/06/24 Copyright 2023 Capgemini

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
from os.path import dirname, join

import numpy as np
import pandas as pd
from sostrades_core.execution_engine.execution_engine import ExecutionEngine

from energy_models.glossaryenergy import GlossaryEnergy


class FlueGasRatioTestCase(unittest.TestCase):
    """
    FlueGas ratio prices test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        years = np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)

        self.electricity_CoalGen_production = pd.DataFrame({GlossaryEnergy.Years: years,
                                                            f"{GlossaryEnergy.CO2FromFlueGas} ({GlossaryEnergy.mass_unit})": 10000.0})

        self.hydrogen_WaterGasShift_production = pd.DataFrame({GlossaryEnergy.Years: years,
                                                               f"{GlossaryEnergy.CO2FromFlueGas} ({GlossaryEnergy.mass_unit})": 20000.0})
        self.dac_production = pd.DataFrame({GlossaryEnergy.Years: years,
                                            f"{GlossaryEnergy.CO2FromFlueGas} ({GlossaryEnergy.mass_unit})": 5000.0})
        self.scaling_factor_techno_consumption = 1e3
        self.scaling_factor_techno_production = 1e3

        self.techno_capital = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.Capital: 0.0, GlossaryEnergy.NonUseCapital: 0.})

    def tearDown(self):
        pass

    def test_01_fluegas_discipline(self):
        self.name = 'Test'
        self.model_name = 'flue_gas'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_flue_gas': f'{self.name}.{self.model_name}',
                   GlossaryEnergy.NS_ENERGY_MIX: f'{self.name}',
                   'ns_public': f'{self.name}',
                   GlossaryEnergy.NS_CCS: f'{self.name}',
                   'ns_energy_study': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.stream_type.carbon_disciplines.flue_gas_disc.FlueGasDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {
            f'{self.name}.{self.model_name}.{GlossaryEnergy.techno_list}': [f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.WaterGasShift}',
                                                                            f'{GlossaryEnergy.electricity}.{GlossaryEnergy.CoalGen}'],
            f'{self.name}.{GlossaryEnergy.electricity}.{GlossaryEnergy.CoalGen}.{GlossaryEnergy.TechnoProductionValue}': self.electricity_CoalGen_production,
            f'{self.name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.TechnoProductionValue}': self.hydrogen_WaterGasShift_production,
            f'{self.name}.{GlossaryEnergy.electricity}.{GlossaryEnergy.CoalGen}.flue_gas_co2_ratio': np.array([0.2]),
            f'{self.name}.{GlossaryEnergy.ccs_list}': [GlossaryEnergy.carbon_capture],
            f'{self.name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.WaterGasShift}.flue_gas_co2_ratio': np.array([0.4]),
            f'{self.name}.{self.model_name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.TechnoCapitalValue}': self.techno_capital,
            f'{self.name}.{self.model_name}.{GlossaryEnergy.electricity}.{GlossaryEnergy.CoalGen}.{GlossaryEnergy.TechnoCapitalValue}': self.techno_capital,
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
                   GlossaryEnergy.NS_ENERGY_MIX: f'{self.name}',
                   'ns_public': f'{self.name}',
                   GlossaryEnergy.NS_CCS: f'{self.name}',
                   'ns_energy_study': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.stream_type.carbon_disciplines.flue_gas_disc.FlueGasDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearEnd}': GlossaryEnergy.YearEndDefault,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.techno_list}': [
                           f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.WaterGasShift}', f'{GlossaryEnergy.electricity}.{GlossaryEnergy.CoalGen}',
                           f'{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.direct_air_capture}.{GlossaryEnergy.DirectAirCaptureTechno}'],
                       f'{self.name}.{GlossaryEnergy.electricity}.{GlossaryEnergy.CoalGen}.{GlossaryEnergy.TechnoProductionValue}': self.electricity_CoalGen_production,
                       f'{self.name}.{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.direct_air_capture}.{GlossaryEnergy.DirectAirCaptureTechno}.{GlossaryEnergy.TechnoProductionValue}': self.electricity_CoalGen_production,

                       f'{self.name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.TechnoProductionValue}': self.hydrogen_WaterGasShift_production,
                       f'{self.name}.{GlossaryEnergy.electricity}.{GlossaryEnergy.CoalGen}.flue_gas_co2_ratio': np.array([0.2]),
                       f'{self.name}.{GlossaryEnergy.carbon_capture}.flue_gas_co2_ratio': np.array([0.2]),
                       f'{self.name}.{GlossaryEnergy.ccs_list}': [GlossaryEnergy.carbon_capture],
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.TechnoCapitalValue}': self.techno_capital,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.electricity}.{GlossaryEnergy.CoalGen}.{GlossaryEnergy.TechnoCapitalValue}': self.techno_capital,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.direct_air_capture}.{GlossaryEnergy.DirectAirCaptureTechno}.{GlossaryEnergy.TechnoCapitalValue}': self.techno_capital,
                       f'{self.name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.WaterGasShift}.flue_gas_co2_ratio': np.array([0.4]),
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production, }
        self.ee.load_study_from_input_dict(inputs_dict)
        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].discipline_wrapp.discipline

        succeed = disc_techno.check_jacobian(derr_approx='complex_step', inputs=[
            f'{self.name}.{GlossaryEnergy.electricity}.{GlossaryEnergy.CoalGen}.{GlossaryEnergy.TechnoProductionValue}',
            f'{self.name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.TechnoProductionValue}',
            f'{self.name}.{GlossaryEnergy.electricity}.{GlossaryEnergy.CoalGen}.flue_gas_co2_ratio'],
                                             outputs=[
                                                 f'{self.name}.{self.model_name}.{GlossaryEnergy.FlueGasMean}',
                                                 f'{self.name}.{self.model_name}.flue_gas_production',
                                                 f'{self.name}.{self.model_name}.flue_gas_prod_ratio'],
                                             input_data=disc_techno.local_data,
                                             dump_jac_path=join(dirname(__file__), 'jacobian_pkls',
                                                                'jacobian_fluegas_discipline.pkl'))

        self.assertTrue(
            succeed, msg="Wrong gradient")
