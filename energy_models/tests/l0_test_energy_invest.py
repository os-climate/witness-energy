'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2023/11/16 Copyright 2023 Capgemini

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

from os.path import dirname

import numpy as np
import pandas as pd
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tests.core.abstract_jacobian_unit_test import (
    AbstractJacobianUnittest,
)

from energy_models.core.investments.energy_invest import EnergyInvest
from energy_models.glossaryenergy import GlossaryEnergy


class TestEnergyInvest(AbstractJacobianUnittest):
    """
    Energy Invest test class
    """

    def analytic_grad_entry(self):
        return [
            self.test_06_techno_invest_disc_check_jacobian,
            self.test_07_energy_invest_disc_check_jacobian,
        ]

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.y_s = GlossaryEnergy.YearStartDefault
        self.y_e = GlossaryEnergy.YearEndDefault
        self.y_step = 1
        self.energy_invest = EnergyInvest()
        self.energy_list = [
            GlossaryEnergy.electricity, f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}',
            GlossaryEnergy.methane]
        self.energy_invest.set_energy_list(self.energy_list)

        self.years = np.arange(self.y_s, self.y_e + 1)
        dict2 = {}
        dict2[GlossaryEnergy.Years] = self.years
        dict2[GlossaryEnergy.electricity] = np.ones(len(self.years))
        dict2[GlossaryEnergy.methane] = np.ones(len(self.years)) * 0.5
        dict2[f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}'] = np.ones(len(self.years)) * 0.5
        self.energy_mix = pd.DataFrame(dict2)

        dict3 = {}
        dict3[GlossaryEnergy.Years] = self.years
        dict3['SMR'] = np.ones(len(self.years))
        dict3['Electrolysis'] = np.ones(len(self.years)) * 0.5
        dict3['CoalGasification'] = np.ones(len(self.years)) * 0.5
        self.techno_mix = pd.DataFrame(dict3)
        invest_ref = 1.0e3  # G$ means 1 milliard of dollars
        invest = np.zeros(len(self.years))
        invest[0] = invest_ref
        for i in range(1, len(self.years)):
            invest[i] = 1.02 * invest[i - 1]
        self.invest_df = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.EnergyInvestmentsValue: invest})
        self.invest_df_techno = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.InvestValue: invest})
        self.scaling_factor_techno_consumption = 1e3
        self.scaling_factor_techno_production = 1e3

    def test_01_set_invest_mix(self):

        dict1 = {}
        dict1[GlossaryEnergy.Years] = self.years
        dict1[GlossaryEnergy.electricity] = np.ones(len(self.years))
        mix_df1 = pd.DataFrame(dict1)

        # -- assert fail if not enough information
        fail = False
        try:
            self.energy_invest.set_invest_mix(mix_df1)
            fail = False
        except:
            fail = True
        self.assertTrue(fail)

        fail = False
        try:
            self.energy_invest.set_invest_mix(self.energy_mix)
            fail = False
        except:
            fail = True
        self.assertFalse(fail)

    def test_02_get_invest_distrib(self):
        unit = '$'
        fail = False
        try:
            self.energy_invest.get_invest_distrib(
                self.invest_df_techno, [1., 2., 3.], input_unit=unit, output_unit=unit)
            fail = False
        except:
            fail = True
        self.assertTrue(fail)

        invest_distrib, runit = self.energy_invest.get_invest_distrib(
            self.invest_df_techno, self.energy_mix, input_unit=unit, output_unit=unit)
        expected_output = pd.DataFrame()
        for energy in self.energy_list:
            expected_output[energy] = self.energy_mix[energy] * self.invest_df_techno[GlossaryEnergy.InvestValue] / \
                                      np.linalg.norm(
                                          self.energy_mix[self.energy_list], ord=1, axis=1)
        diff = np.linalg.norm(
            invest_distrib[self.energy_list] - expected_output)
        self.assertEqual(diff, 0.)
        self.assertEqual(runit, unit)

    def test_03_get_invest_dict(self):
        fail = False
        try:
            self.energy_invest.get_invest_dict(
                self.invest_df_techno, [1., 2., 3.], input_unit='M$', output_unit='$')
            fail = False
        except:
            fail = True
        self.assertTrue(fail)

        invest_dict, runit = self.energy_invest.get_invest_dict(
            self.invest_df_techno, self.energy_mix, input_unit='M$', output_unit='$')
        expected_output = {GlossaryEnergy.Years: list(self.years)}
        for energy in self.energy_list:
            expected_output[energy] = list(
                self.energy_mix[energy].values * self.invest_df_techno[GlossaryEnergy.InvestValue].values /
                np.linalg.norm(self.energy_mix[self.energy_list], ord=1, axis=1) * 1.0e6)
        self.maxDiff = None
        self.assertEqual(invest_dict, expected_output)
        self.assertEqual(runit, '$')

    def test_04_energy_invest_disc(self):

        self.name = 'Energy'
        self.model_name = 'Invest'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_energy': self.name,
                   'ns_energy_study': self.name,
                   'ns_public': self.name,
                   }
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.investments.disciplines.energy_invest_disc.InvestEnergyDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{self.model_name}.{GlossaryEnergy.YearStart}': self.y_s,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.YearEnd}': self.y_e,
                       f'{self.name}.{GlossaryEnergy.energy_list}': [GlossaryEnergy.electricity, GlossaryEnergy.methane,
                                                                     f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}'],
                       f'{self.name}.{self.model_name}.invest_energy_mix': self.energy_mix,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.EnergyInvestmentsValue}': self.invest_df}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)

    #         for graph in graph_list:
    #             graph.to_plotly().show()

    def test_05_techno_invest_disc(self):

        self.name = 'Techno'
        self.model_name = 'Invest'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.investments.disciplines.techno_invest_disc.InvestTechnoDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{self.model_name}.{GlossaryEnergy.YearStart}': self.y_s,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.YearEnd}': self.y_e,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.techno_list}': ['SMR', 'Electrolysis',
                                                                                       'CoalGasification'],
                       f'{self.name}.{self.model_name}.invest_techno_mix': self.techno_mix,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_df_techno}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)

    #         for graph in graph_list:
    #             graph.to_plotly().show()

    def test_06_techno_invest_disc_check_jacobian(self):

        self.name = 'Techno'
        self.model_name = 'Invest'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.investments.disciplines.techno_invest_disc.InvestTechnoDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        technology_list = ['SMR', 'Electrolysis', 'CoalGasification']
        inputs_dict = {f'{self.name}.{self.model_name}.{GlossaryEnergy.YearStart}': self.y_s,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.YearEnd}': self.y_e,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.techno_list}': technology_list,
                       f'{self.name}.{self.model_name}.invest_techno_mix': self.techno_mix,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_df_techno}

        self.ee.load_study_from_input_dict(inputs_dict)
        self.ee.execute()
        disc = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline


        self.check_jacobian(location=dirname(__file__), filename='jacobian_techno_invest_disc.pkl',
                            discipline=disc, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc.local_data,
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}',
                                              f'{self.name}.{self.model_name}.invest_techno_mix'],
                            outputs=[
                                          f'{self.name}.{self.model_name}.{techno}.{GlossaryEnergy.InvestLevelValue}'
                                          for techno in technology_list], )


    def test_07_energy_invest_disc_check_jacobian(self):

        self.name = 'Energy'
        self.model_name = 'Invest'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_energy': self.name,
                   'ns_energy_study': self.name,
                   'ns_public': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.investments.disciplines.energy_invest_disc.InvestEnergyDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        energy_list = [GlossaryEnergy.electricity, GlossaryEnergy.methane,
                       f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}']
        inputs_dict = {f'{self.name}.{self.model_name}.{GlossaryEnergy.YearStart}': self.y_s,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.YearEnd}': self.y_e,
                       f'{self.name}.{GlossaryEnergy.energy_list}': energy_list,
                       f'{self.name}.{self.model_name}.invest_energy_mix': self.energy_mix,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.EnergyInvestmentsValue}': self.invest_df}

        self.ee.load_study_from_input_dict(inputs_dict)
        self.ee.execute()
        disc = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline

        self.check_jacobian(location=dirname(__file__), filename='jacobian_energy_invest_disc.pkl',
                            discipline=disc, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc.local_data,
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.EnergyInvestmentsValue}',
                                    f'{self.name}.{self.model_name}.invest_energy_mix'],
                            outputs=[
                                f'{self.name}.{self.model_name}.{energy}.{GlossaryEnergy.InvestLevelValue}'
                                for energy in energy_list], )

