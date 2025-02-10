'''
Copyright 2022 Airbus SAS
Modifications on 2023/04/21-2024/06/24 Copyright 2023 Capgemini

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

from energy_models.glossaryenergy import GlossaryEnergy


class TestIndependentInvest(unittest.TestCase):
    """
    OneInvest test class
    """

    def setUp(self):
        
        self.year_start = GlossaryEnergy.YearStartDefault
        self.year_end = GlossaryEnergy.YearEndDefault
        self.energy_list = [
            GlossaryEnergy.electricity, f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}', GlossaryEnergy.methane]
        self.energy_list_bis = [
            GlossaryEnergy.electricity, f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}', GlossaryEnergy.methane]

        self.ccs_list = [
            GlossaryEnergy.carbon_capture, GlossaryEnergy.carbon_storage]
        self.years = np.arange(self.year_start, self.year_end + 1)
        year_range = self.year_end - self.year_start + 1
        energy_mix_invest_dic = {}
        energy_mix_invest_dic[GlossaryEnergy.Years] = self.years
        energy_mix_invest_dic[f'{GlossaryEnergy.electricity}.{GlossaryEnergy.SolarPv}'] = np.ones(len(self.years)) * 10.0
        energy_mix_invest_dic[f'{GlossaryEnergy.electricity}.{GlossaryEnergy.WindOnshore}'] = np.ones(len(self.years)) * 20.0
        energy_mix_invest_dic[f'{GlossaryEnergy.electricity}.{GlossaryEnergy.CoalGen}'] = np.ones(len(self.years)) * 30.0
        energy_mix_invest_dic[f'{GlossaryEnergy.methane}.{GlossaryEnergy.FossilGas}'] = np.ones(len(self.years)) * 40.0
        energy_mix_invest_dic[f'{GlossaryEnergy.methane}.{GlossaryEnergy.UpgradingBiogas}'] = np.ones(len(self.years)) * 50.0
        energy_mix_invest_dic[f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.WaterGasShift}'] = np.ones(
            len(self.years)) * 60.0
        energy_mix_invest_dic[f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.ElectrolysisAWE}'] = np.ones(
            len(self.years)) * 70.0
        energy_mix_invest_dic[f'{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.direct_air_capture}.{GlossaryEnergy.AmineScrubbing}'] = np.ones(
            len(self.years)) * 80.0
        energy_mix_invest_dic[f'{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.flue_gas_capture}.{GlossaryEnergy.CalciumLooping}'] = np.ones(
            len(self.years)) * 90.0
        energy_mix_invest_dic[f'{GlossaryEnergy.carbon_storage}.{GlossaryEnergy.DeepSalineFormation}'] = np.ones(
            len(self.years)) * 100.0
        energy_mix_invest_dic[f'{GlossaryEnergy.carbon_storage}.{GlossaryEnergy.GeologicMineralization}'] = np.ones(
            len(self.years)) * 110.0
        self.energy_mix = pd.DataFrame(energy_mix_invest_dic)

        self.scaling_factor_techno_consumption = 1e3
        self.scaling_factor_techno_production = 1e3

        forest_invest = np.linspace(5, 8, year_range)
        self.reforestation_investment_df = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.ReforestationInvestmentValue: forest_invest})
        managed_wood_invest = np.linspace(0.5, 2, year_range)
        self.managed_wood_invest_df = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, "investment": managed_wood_invest})
        unmanaged_wood_invest = np.linspace(2, 3, year_range)
        self.unmanaged_wood_invest_df = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, "investment": unmanaged_wood_invest})
        deforestation_invest = np.linspace(1.0, 0.1, year_range)
        self.deforestation_invest_df = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, "investment": deforestation_invest})
        crop_invest = np.linspace(0.5, 0.25, year_range)
        self.crop_invest_df = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, "investment": crop_invest})

    def test_02_independent_invest_disc(self):

        self.name = 'Energy'
        self.model_name = 'Invest'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {GlossaryEnergy.NS_WITNESS: self.name,
                   'ns_public': self.name,
                   'ns_energy_study': self.name,
                   GlossaryEnergy.NS_CCS: f'{self.name}.CCUS',
                   'ns_energy': self.name,
                   GlossaryEnergy.NS_ENERGY_MIX: self.name,
                   GlossaryEnergy.NS_FUNCTIONS: self.name,
                   'ns_invest': f'{self.name}.{self.model_name}'
                   }

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.investments.disciplines.independent_invest_disc.IndependentInvestDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearStart}': self.year_start,
                       f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.energy_list}': self.energy_list,
                       f'{self.name}.{GlossaryEnergy.ccs_list}': self.ccs_list,
                       f'{self.name}.{GlossaryEnergy.electricity}.{GlossaryEnergy.technologies_list}': [GlossaryEnergy.SolarPv, GlossaryEnergy.WindOnshore, GlossaryEnergy.CoalGen],
                       f'{self.name}.{GlossaryEnergy.methane}.{GlossaryEnergy.technologies_list}': [GlossaryEnergy.FossilGas, GlossaryEnergy.UpgradingBiogas],
                       f'{self.name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.technologies_list}': [GlossaryEnergy.WaterGasShift,
                                                                                    GlossaryEnergy.ElectrolysisAWE],
                       f'{self.name}.{GlossaryEnergy.ccus_type}.{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.technologies_list}': [f'{GlossaryEnergy.direct_air_capture}.{GlossaryEnergy.AmineScrubbing}',
                                                                              f'{GlossaryEnergy.flue_gas_capture}.{GlossaryEnergy.CalciumLooping}'],
                       f'{self.name}.{GlossaryEnergy.ccus_type}.{GlossaryEnergy.carbon_storage}.{GlossaryEnergy.technologies_list}': [GlossaryEnergy.DeepSalineFormation,
                                                                                                                                      GlossaryEnergy.GeologicMineralization],
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.invest_mix}': self.energy_mix,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.ReforestationInvestmentValue}': self.reforestation_investment_df,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        for column in self.energy_mix.columns:
            if column != GlossaryEnergy.Years:
                invest_techno_in = self.energy_mix[column].values

                if GlossaryEnergy.carbon_capture in column or GlossaryEnergy.carbon_storage in column:
                    invest_techno_out = self.ee.dm.get_value(
                        f'{self.name}.{GlossaryEnergy.ccus_type}.{column}.{GlossaryEnergy.InvestLevelValue}')[
                        GlossaryEnergy.InvestValue].values
                else:
                    invest_techno_out = self.ee.dm.get_value(
                        f'{self.name}.{column}.{GlossaryEnergy.InvestLevelValue}')[GlossaryEnergy.InvestValue].values

                self.assertListEqual(
                    invest_techno_in.tolist(), invest_techno_out.tolist())
        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)

        for graph in graph_list:
            pass
            # graph.to_plotly().show()

    def test_03_independent_invest_with_forest_disc(self):

        self.name = 'Energy'
        self.model_name = 'Invest'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {GlossaryEnergy.NS_WITNESS: self.name,
                   'ns_public': self.name,
                   'ns_energy_study': self.name,
                   GlossaryEnergy.NS_CCS: f'{self.name}.CCUS',
                   'ns_energy': self.name,
                   GlossaryEnergy.NS_FUNCTIONS: self.name,
                   'ns_invest': self.name,
                   'ns_forest': f'{self.name}.Forest',
                   'ns_crop': f'{self.name}.Crop',
                   GlossaryEnergy.NS_ENERGY_MIX: self.name
                   }

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.investments.disciplines.independent_invest_disc.IndependentInvestDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        max_budget = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.MaxBudgetValue: np.linspace(800, 970, len(self.years))
        })

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearStart}': self.year_start,
                       f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.MaxBudgetValue}': max_budget,
                       f'{self.name}.{GlossaryEnergy.energy_list}': self.energy_list_bis,
                       f'{self.name}.{GlossaryEnergy.ccs_list}': self.ccs_list,
                       f'{self.name}.{GlossaryEnergy.electricity}.{GlossaryEnergy.technologies_list}': [GlossaryEnergy.SolarPv, GlossaryEnergy.WindOnshore, GlossaryEnergy.CoalGen],
                       f'{self.name}.{GlossaryEnergy.methane}.{GlossaryEnergy.technologies_list}': [GlossaryEnergy.FossilGas, GlossaryEnergy.UpgradingBiogas],
                       f'{self.name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.technologies_list}': [GlossaryEnergy.WaterGasShift,
                                                                                    GlossaryEnergy.ElectrolysisAWE],
                       f'{self.name}.{GlossaryEnergy.ccus_type}.{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.technologies_list}': [f'{GlossaryEnergy.direct_air_capture}.{GlossaryEnergy.AmineScrubbing}',
                                                                              f'{GlossaryEnergy.flue_gas_capture}.{GlossaryEnergy.CalciumLooping}'],
                       f'{self.name}.{GlossaryEnergy.ccus_type}.{GlossaryEnergy.carbon_storage}.{GlossaryEnergy.technologies_list}': [GlossaryEnergy.DeepSalineFormation,
                                                                                                                                      GlossaryEnergy.GeologicMineralization],
                       f'{self.name}.{GlossaryEnergy.invest_mix}': self.energy_mix,
                       f'{self.name}.{GlossaryEnergy.ReforestationInvestmentValue}': self.reforestation_investment_df,
                       f'{self.name}.Forest.managed_wood_investment': self.managed_wood_invest_df,
                       f'{self.name}.Forest.deforestation_investment': self.deforestation_invest_df,
                       f'{self.name}.Crop.crop_investment': self.crop_invest_df}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        for column in self.energy_mix.columns:
            if column != GlossaryEnergy.Years:
                invest_techno_in = self.energy_mix[column].values

                if GlossaryEnergy.carbon_capture in column or GlossaryEnergy.carbon_storage in column:
                    invest_techno_out = self.ee.dm.get_value(
                        f'{self.name}.{GlossaryEnergy.ccus_type}.{column}.{GlossaryEnergy.InvestLevelValue}')[
                        GlossaryEnergy.InvestValue].values
                else:
                    invest_techno_out = self.ee.dm.get_value(
                        f'{self.name}.{column}.{GlossaryEnergy.InvestLevelValue}')[GlossaryEnergy.InvestValue].values

                self.assertListEqual(
                    invest_techno_in.tolist(), invest_techno_out.tolist())
        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)

        for graph in graph_list:
            pass
            #graph.to_plotly().show()


if '__main__' == __name__:
    cls = TestIndependentInvest()
    cls.setUp()
