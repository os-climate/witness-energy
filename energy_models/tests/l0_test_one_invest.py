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

import numpy as np
import pandas as pd
from os.path import join, dirname
from energy_models.core.investments.one_invest import OneInvest
from sos_trades_core.execution_engine.execution_engine import ExecutionEngine


class TestOneInvest(unittest.TestCase):
    """
    OneInvest test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.y_s = 2020
        self.y_e = 2050
        self.y_step = 1
        self.energy_list = [
            'electricity', 'hydrogen.gaseous_hydrogen', 'methane']

        self.ccs_list = [
            'carbon_capture', 'carbon_storage']
        self.years = np.arange(self.y_s, self.y_e + 1)
        dict2 = {}
        dict2['years'] = self.years
        dict2['electricity.SolarPv'] = np.ones(len(self.years)) * 0.1
        dict2['electricity.WindOnshore'] = np.ones(len(self.years)) * 0.2
        dict2['electricity.CoalGen'] = np.ones(len(self.years)) * 0.3
        dict2['methane.FossilGas'] = np.ones(len(self.years)) * 0.4
        dict2['methane.UpgradingBiogas'] = np.ones(len(self.years)) * 0.5
        dict2['hydrogen.gaseous_hydrogen.WaterGasShift'] = np.ones(
            len(self.years)) * 0.6
        dict2['hydrogen.gaseous_hydrogen.Electrolysis.AWE'] = np.ones(
            len(self.years)) * 0.7
        dict2['carbon_capture.direct_air_capture.AmineScrubbing'] = np.ones(
            len(self.years)) * 0.8
        dict2['carbon_capture.flue_gas_capture.CalciumLooping'] = np.ones(
            len(self.years)) * 0.9
        dict2['carbon_storage.DeepSalineFormation'] = np.ones(
            len(self.years)) * 1.0
        dict2['carbon_storage.GeologicMineralization'] = np.ones(
            len(self.years)) * 1.1

        self.energy_mix = pd.DataFrame(dict2)

        invest_ref = 1.0e3  # G$ means 1 milliard of dollars
        invest = np.zeros(len(self.years))
        invest[0] = invest_ref
        for i in range(1, len(self.years)):
            invest[i] = 1.02 * invest[i - 1]
        self.energy_investment = pd.DataFrame(
            {'years': self.years, 'energy_investment': invest})

        self.scaling_factor_techno_consumption = 1e3
        self.scaling_factor_techno_production = 1e3

    def test_01_one_invest_model(self):
        scaling_factor_energy_investment = 100
        inputs_dict = {'year_start': self.y_s,
                       'year_end': self.y_e,
                       'energy_list': self.energy_list,
                       'ccs_list': self.ccs_list,
                       'electricity.technologies_list': ['SolarPv', 'WindOnshore', 'CoalGen'],
                       'methane.technologies_list': ['FossilGas', 'UpgradingBiogas'],
                       'hydrogen.gaseous_hydrogen.technologies_list': ['WaterGasShift', 'Electrolysis.AWE'],
                       'carbon_capture.technologies_list': ['direct_air_capture.AmineScrubbing', 'flue_gas_capture.CalciumLooping'],
                       'carbon_storage.technologies_list': ['DeepSalineFormation', 'GeologicMineralization'],
                       'invest_mix': self.energy_mix,
                       'energy_investment': self.energy_investment,
                       'scaling_factor_energy_investment': scaling_factor_energy_investment,
                       'is_dev': False}
        one_invest_model = OneInvest()
        all_invest_df = one_invest_model.compute(inputs_dict)
        norm_mix = self.energy_mix[[
            col for col in self.energy_mix if col != 'years']].sum(axis=1)

        for column in all_invest_df.columns:
            if column != 'years':
                invest_techno = all_invest_df[column].values
                invest_theory = self.energy_investment[
                    'energy_investment'].values * self.energy_mix[column] / norm_mix * scaling_factor_energy_investment

                self.assertListEqual(np.round(invest_techno, 8).tolist(
                ), np.round(invest_theory, 8).tolist())

    def test_02_one_invest_disc(self):

        self.name = 'Energy'
        self.model_name = 'Invest'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_witness': self.name,
                   'ns_public': self.name,
                   'ns_energy_study': self.name,
                   'ns_ccs': f'{self.name}.CCUS',
                   'ns_energy': self.name,
                   }

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.investments.disciplines.one_invest_disc.OneInvestDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.year_start': self.y_s,
                       f'{self.name}.year_end': self.y_e,
                       f'{self.name}.energy_list': self.energy_list,
                       f'{self.name}.ccs_list': self.ccs_list,
                       f'{self.name}.electricity.technologies_list': ['SolarPv', 'WindOnshore', 'CoalGen'],
                       f'{self.name}.methane.technologies_list': ['FossilGas', 'UpgradingBiogas'],
                       f'{self.name}.hydrogen.gaseous_hydrogen.technologies_list': ['WaterGasShift', 'Electrolysis.AWE'],
                       f'{self.name}.CCUS.carbon_capture.technologies_list': ['direct_air_capture.AmineScrubbing', 'flue_gas_capture.CalciumLooping'],
                       f'{self.name}.CCUS.carbon_storage.technologies_list': ['DeepSalineFormation', 'GeologicMineralization'],
                       f'{self.name}.{self.model_name}.invest_mix': self.energy_mix,
                       f'{self.name}.energy_investment': self.energy_investment}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)
        # for graph in graph_list:
        # graph.to_plotly().show()

    def test_03_one_invest_disc_check_jacobian(self):

        self.name = 'Energy'
        self.model_name = 'Invest'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_witness': self.name,
                   'ns_public': self.name,
                   'ns_energy_study': self.name,
                   'ns_energy': self.name,
                   'ns_ccs': f'{self.name}',
                   }
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.investments.disciplines.one_invest_disc.OneInvestDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        energy_list = ['electricity', 'methane', 'hydrogen.gaseous_hydrogen']
        inputs_dict = {f'{self.name}.year_start': self.y_s,
                       f'{self.name}.year_end': self.y_e,
                       f'{self.name}.energy_list': energy_list,
                       f'{self.name}.ccs_list': self.ccs_list,
                       f'{self.name}.electricity.technologies_list': ['SolarPv', 'WindOnshore', 'CoalGen'],
                       f'{self.name}.methane.technologies_list': ['FossilGas', 'UpgradingBiogas'],
                       f'{self.name}.hydrogen.gaseous_hydrogen.technologies_list': ['WaterGasShift', 'Electrolysis.AWE'],
                       f'{self.name}.carbon_capture.technologies_list': ['direct_air_capture.AmineScrubbing', 'flue_gas_capture.CalciumLooping'],
                       f'{self.name}.carbon_storage.technologies_list': ['DeepSalineFormation', 'GeologicMineralization'],
                       f'{self.name}.{self.model_name}.invest_mix': self.energy_mix,
                       f'{self.name}.energy_investment': self.energy_investment}

        self.ee.load_study_from_input_dict(inputs_dict)

        disc = self.ee.root_process.sos_disciplines[0]

        all_technos_list = [
            f'{energy}.{techno}' for energy in energy_list + self.ccs_list for techno in inputs_dict[f'{self.name}.{energy}.technologies_list']]

        succeed = disc.check_jacobian(derr_approx='complex_step', inputs=[f'{self.name}.energy_investment',
                                                                          f'{self.name}.{self.model_name}.invest_mix'],
                                      outputs=[
            f'{self.name}.{techno}.invest_level' for techno in all_technos_list],
            load_jac_path=join(dirname(__file__), 'jacobian_pkls',
                               f'jacobian_all_invest_disc.pkl'))
        self.assertTrue(
            succeed, msg=f"Wrong gradient in {disc.get_disc_full_name()}")


if '__main__' == __name__:

    cls = TestOneInvest()
    cls.setUp()
    cls.test_01_one_invest_model()
