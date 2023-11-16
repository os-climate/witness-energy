'''
Copyright 2022 Airbus SAS
Modifications on 2023/04/21-2023/11/09 Copyright 2023 Capgemini

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

from climateeconomics.glossarycore import GlossaryCore
from energy_models.core.investments.independent_invest import IndependentInvest
from sostrades_core.execution_engine.execution_engine import ExecutionEngine


class TestIndependentInvest(unittest.TestCase):
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
        self.energy_list_bis = [
            'electricity', 'hydrogen.gaseous_hydrogen', 'methane', 'biomass_dry']

        self.ccs_list = [
            'carbon_capture', 'carbon_storage']
        self.years = np.arange(self.y_s, self.y_e + 1)
        year_range = self.y_e - self.y_s + 1
        energy_mix_invest_dic = {}
        energy_mix_invest_dic[GlossaryCore.Years] = self.years
        energy_mix_invest_dic['electricity.SolarPv'] = np.ones(len(self.years)) * 10.0
        energy_mix_invest_dic['electricity.WindOnshore'] = np.ones(len(self.years)) * 20.0
        energy_mix_invest_dic['electricity.CoalGen'] = np.ones(len(self.years)) * 30.0
        energy_mix_invest_dic['methane.FossilGas'] = np.ones(len(self.years)) * 40.0
        energy_mix_invest_dic['methane.UpgradingBiogas'] = np.ones(len(self.years)) * 50.0
        energy_mix_invest_dic['hydrogen.gaseous_hydrogen.WaterGasShift'] = np.ones(
            len(self.years)) * 60.0
        energy_mix_invest_dic['hydrogen.gaseous_hydrogen.Electrolysis.AWE'] = np.ones(
            len(self.years)) * 70.0
        energy_mix_invest_dic['carbon_capture.direct_air_capture.AmineScrubbing'] = np.ones(
            len(self.years)) * 80.0
        energy_mix_invest_dic['carbon_capture.flue_gas_capture.CalciumLooping'] = np.ones(
            len(self.years)) * 90.0
        energy_mix_invest_dic['carbon_storage.DeepSalineFormation'] = np.ones(
            len(self.years)) * 100.0
        energy_mix_invest_dic['carbon_storage.GeologicMineralization'] = np.ones(
            len(self.years)) * 110.0
        self.energy_mix = pd.DataFrame(energy_mix_invest_dic)

        self.scaling_factor_techno_consumption = 1e3
        self.scaling_factor_techno_production = 1e3

        forest_invest = np.linspace(5, 8, year_range)
        self.forest_invest_df = pd.DataFrame(
            {GlossaryCore.Years: self.years, GlossaryCore.ForestInvestmentValue: forest_invest})
        managed_wood_invest = np.linspace(0.5, 2, year_range)
        self.managed_wood_invest_df = pd.DataFrame(
            {GlossaryCore.Years: self.years, "investment": managed_wood_invest})
        unmanaged_wood_invest = np.linspace(2, 3, year_range)
        self.unmanaged_wood_invest_df = pd.DataFrame(
            {GlossaryCore.Years: self.years, "investment": unmanaged_wood_invest})
        deforestation_invest = np.linspace(1.0, 0.1, year_range)
        self.deforestation_invest_df = pd.DataFrame(
            {GlossaryCore.Years: self.years, "investment": deforestation_invest})
        crop_invest = np.linspace(0.5, 0.25, year_range)
        self.crop_invest_df = pd.DataFrame(
            {GlossaryCore.Years: self.years, "investment": crop_invest})

    def test_01_independent_invest_model(self):
        scaling_factor_energy_investment = 100
        inputs_dict = {GlossaryCore.YearStart: self.y_s,
                       GlossaryCore.YearEnd: self.y_e,
                       GlossaryCore.energy_list: self.energy_list,
                       GlossaryCore.ccs_list: self.ccs_list,
                       'electricity.technologies_list': ['SolarPv', 'WindOnshore', 'CoalGen'],
                       'methane.technologies_list': ['FossilGas', 'UpgradingBiogas'],
                       'hydrogen.gaseous_hydrogen.technologies_list': ['WaterGasShift', 'Electrolysis.AWE'],
                       'carbon_capture.technologies_list': ['direct_air_capture.AmineScrubbing',
                                                            'flue_gas_capture.CalciumLooping'],
                       'carbon_storage.technologies_list': ['DeepSalineFormation', 'GeologicMineralization'],
                       GlossaryCore.invest_mix: self.energy_mix,
                       GlossaryCore.ForestInvestmentValue: self.forest_invest_df,
                       'scaling_factor_energy_investment': scaling_factor_energy_investment,}
        one_invest_model = IndependentInvest()
        energy_investment_wo_tax = one_invest_model.compute(inputs_dict)

    def test_02_independent_invest_disc(self):

        self.name = 'Energy'
        self.model_name = 'Invest'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_witness': self.name,
                   'ns_ref': self.name,
                   'ns_public': self.name,
                   'ns_energy_study': self.name,
                   'ns_ccs': f'{self.name}.CCUS',
                   'ns_energy': self.name,
                   'ns_functions': self.name,
                   'ns_invest': f'{self.name}.{self.model_name}'
                   }

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.investments.disciplines.independent_invest_disc.IndependentInvestDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryCore.YearStart}': self.y_s,
                       f'{self.name}.{GlossaryCore.YearEnd}': self.y_e,
                       f'{self.name}.{GlossaryCore.energy_list}': self.energy_list,
                       f'{self.name}.{GlossaryCore.ccs_list}': self.ccs_list,
                       f'{self.name}.electricity.technologies_list': ['SolarPv', 'WindOnshore', 'CoalGen'],
                       f'{self.name}.methane.technologies_list': ['FossilGas', 'UpgradingBiogas'],
                       f'{self.name}.hydrogen.gaseous_hydrogen.technologies_list': ['WaterGasShift',
                                                                                    'Electrolysis.AWE'],
                       f'{self.name}.CCUS.carbon_capture.technologies_list': ['direct_air_capture.AmineScrubbing',
                                                                              'flue_gas_capture.CalciumLooping'],
                       f'{self.name}.CCUS.carbon_storage.technologies_list': ['DeepSalineFormation',
                                                                              'GeologicMineralization'],
                       f'{self.name}.{self.model_name}.{GlossaryCore.invest_mix}': self.energy_mix,
                       f'{self.name}.{self.model_name}.{GlossaryCore.ForestInvestmentValue}': self.forest_invest_df,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        for column in self.energy_mix.columns:
            if column != GlossaryCore.Years:
                invest_techno_in = self.energy_mix[column].values

                if 'carbon_capture' in column or 'carbon_storage' in column:
                    invest_techno_out = self.ee.dm.get_value(
                        f'{self.name}.CCUS.{column}.{GlossaryCore.InvestLevelValue}')[GlossaryCore.InvestValue].values
                else:
                    invest_techno_out = self.ee.dm.get_value(
                        f'{self.name}.{column}.{GlossaryCore.InvestLevelValue}')[GlossaryCore.InvestValue].values

                self.assertListEqual(
                    invest_techno_in.tolist(), invest_techno_out.tolist())
        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)

        for graph in graph_list:
            pass
            #graph.to_plotly().show()

    def test_03_independent_invest_with_forest_disc(self):

        self.name = 'Energy'
        self.model_name = 'Invest'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_witness': self.name,
                   'ns_ref': self.name,
                   'ns_public': self.name,
                   'ns_energy_study': self.name,
                   'ns_ccs': f'{self.name}.CCUS',
                   'ns_energy': self.name,
                   'ns_functions': self.name,
                   'ns_invest': self.name,
                   'ns_forest': f'{self.name}.Forest',
                   'ns_crop': f'{self.name}.Crop'
                   }

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.investments.disciplines.independent_invest_disc.IndependentInvestDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryCore.YearStart}': self.y_s,
                       f'{self.name}.{GlossaryCore.YearEnd}': self.y_e,
                       f'{self.name}.{GlossaryCore.energy_list}': self.energy_list_bis,
                       f'{self.name}.{GlossaryCore.ccs_list}': self.ccs_list,
                       f'{self.name}.electricity.technologies_list': ['SolarPv', 'WindOnshore', 'CoalGen'],
                       f'{self.name}.methane.technologies_list': ['FossilGas', 'UpgradingBiogas'],
                       f'{self.name}.hydrogen.gaseous_hydrogen.technologies_list': ['WaterGasShift',
                                                                                    'Electrolysis.AWE'],
                       f'{self.name}.CCUS.carbon_capture.technologies_list': ['direct_air_capture.AmineScrubbing',
                                                                              'flue_gas_capture.CalciumLooping'],
                       f'{self.name}.CCUS.carbon_storage.technologies_list': ['DeepSalineFormation',
                                                                              'GeologicMineralization'],
                       f'{self.name}.{self.model_name}.{GlossaryCore.invest_mix}': self.energy_mix,
                       f'{self.name}.{GlossaryCore.ForestInvestmentValue}': self.forest_invest_df,
                       f'{self.name}.Forest.managed_wood_investment': self.managed_wood_invest_df,
                       f'{self.name}.Forest.deforestation_investment': self.deforestation_invest_df,
                       f'{self.name}.Crop.crop_investment': self.crop_invest_df}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        for column in self.energy_mix.columns:
            if column != GlossaryCore.Years:
                invest_techno_in = self.energy_mix[column].values

                if 'carbon_capture' in column or 'carbon_storage' in column:
                    invest_techno_out = self.ee.dm.get_value(
                        f'{self.name}.CCUS.{column}.{GlossaryCore.InvestLevelValue}')[GlossaryCore.InvestValue].values
                else:
                    invest_techno_out = self.ee.dm.get_value(
                        f'{self.name}.{column}.{GlossaryCore.InvestLevelValue}')[GlossaryCore.InvestValue].values

                self.assertListEqual(
                    invest_techno_in.tolist(), invest_techno_out.tolist())
        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)

        for graph in graph_list:
            pass
            #graph.to_plotly().show()


    def test_04_independent_invest_disc_check_jacobian(self):

        self.name = 'Energy'
        self.model_name = 'Invest'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_witness': self.name,
                   'ns_ref': self.name,
                   'ns_public': self.name,
                   'ns_energy_study': self.name,
                   'ns_energy': self.name,
                   'ns_ccs': f'{self.name}',
                   'ns_functions': self.name,
                   'ns_invest': self.name,
                   'ns_crop': self.name,
                   'ns_forest': self.name
                   }
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.investments.disciplines.independent_invest_disc.IndependentInvestDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        energy_list = ['electricity', 'methane',
                       'hydrogen.gaseous_hydrogen', 'biomass_dry']
        inputs_dict = {f'{self.name}.{GlossaryCore.YearStart}': self.y_s,
                       f'{self.name}.{GlossaryCore.YearEnd}': self.y_e,
                       f'{self.name}.{GlossaryCore.energy_list}': energy_list,
                       f'{self.name}.{GlossaryCore.ccs_list}': self.ccs_list,
                       f'{self.name}.electricity.technologies_list': ['SolarPv', 'WindOnshore', 'CoalGen'],
                       f'{self.name}.methane.technologies_list': ['FossilGas', 'UpgradingBiogas'],
                       f'{self.name}.biomass_dry.technologies_list': [],
                       f'{self.name}.hydrogen.gaseous_hydrogen.technologies_list': ['WaterGasShift',
                                                                                    'Electrolysis.AWE'],
                       f'{self.name}.carbon_capture.technologies_list': ['direct_air_capture.AmineScrubbing',
                                                                         'flue_gas_capture.CalciumLooping'],
                       f'{self.name}.carbon_storage.technologies_list': ['DeepSalineFormation',
                                                                         'GeologicMineralization'],
                       f'{self.name}.{self.model_name}.{GlossaryCore.invest_mix}': self.energy_mix,
                       f'{self.name}.{GlossaryCore.ForestInvestmentValue}': self.forest_invest_df,
                       f'{self.name}.managed_wood_investment': self.managed_wood_invest_df,
                       f'{self.name}.deforestation_investment': self.deforestation_invest_df,
                       f'{self.name}.crop_investment': self.crop_invest_df}

        self.ee.load_study_from_input_dict(inputs_dict)
        self.ee.execute()
        disc = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline
        all_technos_list = [
            f'{energy}.{techno}' for energy in energy_list + self.ccs_list for techno in
            inputs_dict[f'{self.name}.{energy}.{GlossaryCore.techno_list}']]
        succeed = disc.check_jacobian(derr_approx='complex_step', inputs=[f'{self.name}.{self.model_name}.{GlossaryCore.invest_mix}',
                                                                          f'{self.name}.{GlossaryCore.ForestInvestmentValue}',
                                                                          f'{self.name}.managed_wood_investment',
                                                                          f'{self.name}.deforestation_investment',
                                                                          f'{self.name}.crop_investment'],
                                      outputs=[
                                                  f'{self.name}.{techno}.{GlossaryCore.InvestLevelValue}' for techno in
                                                  all_technos_list] +
                                              [f'{self.name}.{GlossaryCore.EnergyInvestmentsWoTaxValue}',
                                               f'{self.name}.{GlossaryCore.EnergyInvestmentsMinimizationObjective}'],
                                      input_data=disc.local_data,
                                      load_jac_path=join(dirname(__file__), 'jacobian_pkls',
                                                         f'jacobian_independent_invest_disc.pkl'),
                                      dump_jac_path=None)
        self.assertTrue(
            succeed, msg=f"Wrong gradient")


if '__main__' == __name__:
    cls = TestIndependentInvest()
    cls.setUp()
    cls.test_04_independent_invest_disc_check_jacobian()
