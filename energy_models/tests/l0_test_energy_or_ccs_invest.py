'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2023/11/09 Copyright 2023 Capgemini

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
from os.path import join, dirname

import numpy as np
import pandas as pd

from energy_models.core.investments.energy_or_ccsinvest import EnergyOrCCSInvest
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.carbon_models.carbon_storage import CarbonStorage
from energy_models.glossaryenergy import GlossaryEnergy
from sostrades_core.execution_engine.execution_engine import ExecutionEngine


class TestEnergyorCCSInvest(unittest.TestCase):
    """
    Energy or CCS test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.y_s = GlossaryEnergy.YearStartDefault
        self.y_e = GlossaryEnergy.YearEndDefault
        self.y_step = 1
        self.energy_invest = EnergyOrCCSInvest()

        self.years = np.arange(self.y_s, self.y_e + 1)
        dict2 = {}
        dict2[GlossaryEnergy.Years] = self.years
        self.percentage = 0.1
        dict2['ccs_percentage'] = np.ones(
            len(self.years)) * self.percentage * 100.0
        self.ccs_percentage = pd.DataFrame(dict2)

        dict2 = {}
        dict2[GlossaryEnergy.Years] = self.years
        dict2[GlossaryEnergy.carbon_capture] = np.ones(len(self.years))
        dict2[GlossaryEnergy.carbon_storage] = np.ones(len(self.years)) * 0.5
        self.ccs_mix = pd.DataFrame(dict2)

        invest_ref = 1.0e3  # G$ means 1 milliard of dollars
        invest = np.zeros(len(self.years))
        invest[0] = invest_ref
        for i in range(1, len(self.years)):
            invest[i] = 1.02 * invest[i - 1]
        self.invest_df = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.EnergyInvestmentsValue: invest})

        self.input_dict = {GlossaryEnergy.EnergyInvestmentsValue: self.invest_df,
                           'ccs_percentage': self.ccs_percentage,
                           'ccs_investment': self.invest_df,
                           GlossaryEnergy.YearStart: self.y_s,
                           GlossaryEnergy.YearEnd: self.y_e,
                           'invest_ccs_mix': self.ccs_mix}

    def test_01_compute(self):
        self.energy_invest.configure(self.input_dict)

        self.energy_invest.compute()
        # in G$
        rescaling_factor = 100.0
        ccs_invest = self.energy_invest.get_ccs_investment(rescaling_factor)
        # in 100G$

        energy_conversion_invest = self.energy_invest.get_energy_conversion_investment(
        )

        self.assertListEqual(np.around(
            ccs_invest[GlossaryEnergy.EnergyInvestmentsValue].values / rescaling_factor + energy_conversion_invest[
                GlossaryEnergy.EnergyInvestmentsValue].values, 8).tolist(),
                             np.around(self.invest_df[GlossaryEnergy.EnergyInvestmentsValue].values, 8).tolist())
        ccs_invest_theory = self.percentage * \
                            self.invest_df[GlossaryEnergy.EnergyInvestmentsValue].values

        self.assertListEqual(
            np.around(ccs_invest[GlossaryEnergy.EnergyInvestmentsValue].values / rescaling_factor, 8).tolist(),
            np.around(ccs_invest_theory, 8).tolist())

    def test_02_energy_invest_disc(self):
        self.name = 'Energy'
        self.model_name = 'Invest'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {GlossaryEnergy.NS_WITNESS: f'{self.name}.{self.model_name}',
                   GlossaryEnergy.NS_CCS: f'{self.name}.{self.model_name}',
                   GlossaryEnergy.NS_ENERGY_MIX: f'{self.name}.{self.model_name}.Energy'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.investments.disciplines.energy_or_ccs_invest_disc.InvestCCSorEnergyDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        namespaced_input_dict = {
            f'{self.name}.{self.model_name}.{key}': value for key, value in self.input_dict.items()}
        self.ee.load_study_from_input_dict(namespaced_input_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)

    #         for graph in graph_list:
    #             graph.to_plotly().show()

    def test_03_energy_invest_disc_check_jacobian(self):
        self.name = 'Energy'
        self.model_name = 'Invest'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {GlossaryEnergy.NS_WITNESS: f'{self.name}.{self.model_name}',
                   GlossaryEnergy.NS_CCS: f'{self.name}.{self.model_name}',
                   GlossaryEnergy.NS_ENERGY_MIX: f'{self.name}.{self.model_name}.Energy'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.investments.disciplines.energy_or_ccs_invest_disc.InvestCCSorEnergyDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        namespaced_input_dict = {
            f'{self.name}.{self.model_name}.{key}': value for key, value in self.input_dict.items()}
        self.ee.load_study_from_input_dict(namespaced_input_dict)
        self.ee.execute()
        disc = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline
        succeed = disc.check_jacobian(derr_approx='complex_step',
                                      inputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.EnergyInvestmentsValue}',
                                              f'{self.name}.{self.model_name}.ccs_percentage'],
                                      outputs=[
                                          f'{self.name}.{self.model_name}.Energy.energy_investment',
                                          f'{self.name}.{self.model_name}.ccs_investment'],
                                      input_data=disc.local_data,
                                      load_jac_path=join(dirname(__file__), 'jacobian_pkls',
                                                         f'jacobian_energy_invest_or_ccs_disc.pkl'))

        self.assertTrue(
            succeed, msg=f"Wrong gradient")

    def test_04_ccs_invest_disc(self):
        self.name = 'Energy'
        self.model_name = 'Invest'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {GlossaryEnergy.NS_WITNESS: f'{self.name}.{self.model_name}',
                   GlossaryEnergy.NS_CCS: f'{self.name}.{self.model_name}',
                   GlossaryEnergy.NS_ENERGY_MIX: f'{self.name}.{self.model_name}.Energy',
                   'ns_public': f'{self.name}.{self.model_name}',
                   'ns_energy_study': f'{self.name}.{self.model_name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.investments.disciplines.ccs_invest_disc.InvestCCSDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        namespaced_input_dict = {
            f'{self.name}.{self.model_name}.{key}': value for key, value in self.input_dict.items()}
        self.ee.load_study_from_input_dict(namespaced_input_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)

    #         for graph in graph_list:
    #             graph.to_plotly().show()

    def test_05_ccs_invest_disc_check_jacobian(self):
        self.name = 'Energy'
        self.model_name = 'Invest'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {GlossaryEnergy.NS_WITNESS: f'{self.name}.{self.model_name}',
                   GlossaryEnergy.NS_CCS: f'{self.name}.{self.model_name}',
                   GlossaryEnergy.NS_ENERGY_MIX: f'{self.name}.{self.model_name}.Energy',
                   'ns_public': f'{self.name}.{self.model_name}',
                   'ns_energy_study': f'{self.name}.{self.model_name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.investments.disciplines.ccs_invest_disc.InvestCCSDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        namespaced_input_dict = {
            f'{self.name}.{self.model_name}.{key}': value for key, value in self.input_dict.items()}
        self.ee.load_study_from_input_dict(namespaced_input_dict)
        self.ee.execute()
        ccs_list = [CarbonCapture.name, CarbonStorage.name]
        disc = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline
        succeed = disc.check_jacobian(derr_approx='complex_step',
                                      inputs=[f'{self.name}.{self.model_name}.ccs_investment',
                                              f'{self.name}.{self.model_name}.invest_ccs_mix'],
                                      outputs=[
                                          f'{self.name}.{self.model_name}.{ccs}.{GlossaryEnergy.InvestLevelValue}' for
                                          ccs in ccs_list],
                                      input_data=disc.local_data,
                                      load_jac_path=join(dirname(__file__), 'jacobian_pkls',
                                                         f'jacobian_invest_ccs_disc.pkl'))
        self.assertTrue(
            succeed, msg=f"Wrong gradient")
