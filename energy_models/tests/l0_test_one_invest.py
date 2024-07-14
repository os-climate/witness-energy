'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2024/06/24 Copyright 2023 Capgemini

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
from sostrades_core.execution_engine.execution_engine import ExecutionEngine

from energy_models.core.investments.one_invest import OneInvest
from energy_models.glossaryenergy import GlossaryEnergy


class TestOneInvest(unittest.TestCase):
    """
    OneInvest test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.y_s = GlossaryEnergy.YearStartDefault
        self.y_e = GlossaryEnergy.YearEndDefault
        self.y_step = 1
        self.energy_list = [
            GlossaryEnergy.electricity, f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}', GlossaryEnergy.methane]

        self.ccs_list = [
            GlossaryEnergy.carbon_capture, GlossaryEnergy.carbon_storage]
        self.years = np.arange(self.y_s, self.y_e + 1)
        dict2 = {}
        dict2[GlossaryEnergy.Years] = self.years
        dict2[f'{GlossaryEnergy.electricity}.{GlossaryEnergy.SolarPv}'] = np.ones(len(self.years)) * 0.1
        dict2[f'{GlossaryEnergy.electricity}.{GlossaryEnergy.WindOnshore}'] = np.ones(len(self.years)) * 0.2
        dict2[f'{GlossaryEnergy.electricity}.{GlossaryEnergy.CoalGen}'] = np.ones(len(self.years)) * 0.3
        dict2[f'{GlossaryEnergy.methane}.FossilGas'] = np.ones(len(self.years)) * 0.4
        dict2[f'{GlossaryEnergy.methane}.UpgradingBiogas'] = np.ones(len(self.years)) * 0.5
        dict2[f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.WaterGasShift'] = np.ones(
            len(self.years)) * 0.6
        dict2[f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.Electrolysis.AWE'] = np.ones(
            len(self.years)) * 0.7
        dict2[f'{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.direct_air_capture}.{GlossaryEnergy.AmineScrubbing}'] = np.ones(
            len(self.years)) * 0.8
        dict2[f'{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.flue_gas_capture}.{GlossaryEnergy.CalciumLooping}'] = np.ones(
            len(self.years)) * 0.9
        dict2[f'{GlossaryEnergy.carbon_storage}.DeepSalineFormation'] = np.ones(
            len(self.years)) * 1.0
        dict2[f'{GlossaryEnergy.carbon_storage}.GeologicMineralization'] = np.ones(
            len(self.years)) * 1.1

        self.energy_mix = pd.DataFrame(dict2)

        invest_ref = 1.0e3  # G$ means 1 milliard of dollars
        invest = np.zeros(len(self.years))
        invest[0] = invest_ref
        for i in range(1, len(self.years)):
            invest[i] = 1.02 * invest[i - 1]
        self.energy_investment = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.EnergyInvestmentsValue: invest})

        self.scaling_factor_techno_consumption = 1e3
        self.scaling_factor_techno_production = 1e3

    def test_01_one_invest_model(self):
        scaling_factor_energy_investment = 100
        inputs_dict = {GlossaryEnergy.YearStart: self.y_s,
                       GlossaryEnergy.YearEnd: self.y_e,
                       GlossaryEnergy.energy_list: self.energy_list,
                       GlossaryEnergy.ccs_list: self.ccs_list,
                       f'{GlossaryEnergy.electricity}.technologies_list': ['SolarPv', 'WindOnshore', 'CoalGen'],
                       f'{GlossaryEnergy.methane}.technologies_list': ['FossilGas', 'UpgradingBiogas'],
                       f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.technologies_list': [GlossaryEnergy.WaterGasShift, 'Electrolysis.AWE'],
                       f'{GlossaryEnergy.carbon_capture}.technologies_list': [f'{GlossaryEnergy.direct_air_capture}.{GlossaryEnergy.AmineScrubbing}',
                                                            f'{GlossaryEnergy.flue_gas_capture}.{GlossaryEnergy.CalciumLooping}'],
                       f'{GlossaryEnergy.carbon_storage}.technologies_list': ['DeepSalineFormation', 'GeologicMineralization'],
                       GlossaryEnergy.invest_mix: self.energy_mix,
                       GlossaryEnergy.EnergyInvestmentsValue: self.energy_investment,
                       'scaling_factor_energy_investment': scaling_factor_energy_investment,
                       'is_dev': False}
        one_invest_model = OneInvest()
        all_invest_df = one_invest_model.compute(inputs_dict)
        norm_mix = self.energy_mix[[
            col for col in self.energy_mix if col != GlossaryEnergy.Years]].sum(axis=1)

        for column in all_invest_df.columns:
            if column != GlossaryEnergy.Years:
                invest_techno = all_invest_df[column].values
                invest_theory = self.energy_investment[
                                    GlossaryEnergy.EnergyInvestmentsValue].values * self.energy_mix[
                                    column] / norm_mix * scaling_factor_energy_investment

                self.assertListEqual(np.round(invest_techno, 8).tolist(
                ), np.round(invest_theory, 8).tolist())

    def test_02_one_invest_disc(self):

        self.name = 'Energy'
        self.model_name = 'Invest'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {GlossaryEnergy.NS_WITNESS: self.name,
                   'ns_public': self.name,
                   'ns_energy_study': self.name,
                   GlossaryEnergy.NS_CCS: f'{self.name}.CCUS',
                   'ns_energy': self.name,
                   }

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.investments.disciplines.one_invest_disc.OneInvestDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearStart}': self.y_s,
                       f'{self.name}.{GlossaryEnergy.YearEnd}': self.y_e,
                       f'{self.name}.{GlossaryEnergy.energy_list}': self.energy_list,
                       f'{self.name}.{GlossaryEnergy.ccs_list}': self.ccs_list,
                       f'{self.name}.{GlossaryEnergy.electricity}.technologies_list': ['SolarPv', 'WindOnshore', 'CoalGen'],
                       f'{self.name}.{GlossaryEnergy.methane}.technologies_list': ['FossilGas', 'UpgradingBiogas'],
                       f'{self.name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.technologies_list': [GlossaryEnergy.WaterGasShift,
                                                                                    'Electrolysis.AWE'],
                       f'{self.name}.{GlossaryEnergy.CCUS}.{GlossaryEnergy.carbon_capture}.technologies_list': [f'{GlossaryEnergy.direct_air_capture}.{GlossaryEnergy.AmineScrubbing}',
                                                                              f'{GlossaryEnergy.flue_gas_capture}.{GlossaryEnergy.CalciumLooping}'],
                       f'{self.name}.{GlossaryEnergy.CCUS}.{GlossaryEnergy.carbon_storage}.technologies_list': ['DeepSalineFormation',
                                                                              'GeologicMineralization'],
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.invest_mix}': self.energy_mix,
                       f'{self.name}.{GlossaryEnergy.EnergyInvestmentsValue}': self.energy_investment}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)
        # for graph in graph_list:
        # graph.to_plotly().show()

if '__main__' == __name__:
    cls = TestOneInvest()
    cls.setUp()
    cls.test_01_one_invest_model()
