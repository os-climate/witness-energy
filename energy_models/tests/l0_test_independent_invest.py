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
from energy_models.core.investments.independent_invest import IndependentInvest
from sos_trades_core.execution_engine.execution_engine import ExecutionEngine
from sos_trades_core.tools.base_functions.exp_min import compute_func_with_exp_min
from sos_trades_core.tools.cst_manager.func_manager_common import smooth_maximum


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

        self.ccs_list = [
            'carbon_capture', 'carbon_storage']
        self.years = np.arange(self.y_s, self.y_e + 1)
        year_range = self.y_e - self.y_s + 1
        dict2 = {}
        dict2['years'] = self.years
        dict2['electricity.SolarPV'] = np.ones(len(self.years)) * 10.0
        dict2['electricity.WindOnshore'] = np.ones(len(self.years)) * 20.0
        dict2['electricity.CoalGen'] = np.ones(len(self.years)) * 30.0
        dict2['methane.FossilGas'] = np.ones(len(self.years)) * 40.0
        dict2['methane.UpgradingBiogas'] = np.ones(len(self.years)) * 50.0
        dict2['hydrogen.gaseous_hydrogen.SMR'] = np.ones(
            len(self.years)) * 60.0
        dict2['hydrogen.gaseous_hydrogen.CoalGasification'] = np.ones(
            len(self.years)) * 70.0
        dict2['carbon_capture.direct_air_capture.AmineScrubbing'] = np.ones(
            len(self.years)) * 80.0
        dict2['carbon_capture.flue_gas_capture.CalciumLooping'] = np.ones(
            len(self.years)) * 90.0
        dict2['carbon_storage.DeepSalineFormation'] = np.ones(
            len(self.years)) * 100.0
        dict2['carbon_storage.GeologicMineralization'] = np.ones(
            len(self.years)) * 110.0
        self.energy_mix = pd.DataFrame(dict2)

        invest_ref = 5.0  # 100G$ means 1 milliard of dollars
        invest = np.zeros(len(self.years))
        invest[0] = invest_ref
        for i in range(1, len(self.years)):
            invest[i] = 1.02 * invest[i - 1]
        self.energy_investment = pd.DataFrame(
            {'years': self.years, 'energy_investment': invest})

        self.scaling_factor_techno_consumption = 1e3
        self.scaling_factor_techno_production = 1e3

        forest_invest = np.linspace(5, 8, year_range)
        self.forest_invest_df = pd.DataFrame(
            {"years": self.years, "forest_investment": forest_invest})
        managed_wood_invest = np.linspace(0.5, 2, year_range)
        self.managed_wood_invest_df = pd.DataFrame(
            {"years": self.years, "investment": managed_wood_invest})
        unmanaged_wood_invest = np.linspace(2, 3, year_range)
        self.unmanaged_wood_invest_df = pd.DataFrame(
            {"years": self.years, "investment": unmanaged_wood_invest})
        crop_invest = np.linspace(0.5, 0.25, year_range)
        self.crop_invest_df = pd.DataFrame(
            {"years": self.years, "investment": crop_invest})

    def test_01_independent_invest_model(self):
        scaling_factor_energy_investment = 100
        invest_constraint_ref = 10.0
        invest_objective_ref = 0.05
        is_dev = False
        inputs_dict = {'year_start': self.y_s,
                       'year_end': self.y_e,
                       'energy_list': self.energy_list,
                       'ccs_list': self.ccs_list,
                       'electricity.technologies_list': ['SolarPV', 'WindOnshore', 'CoalGen'],
                       'methane.technologies_list': ['FossilGas', 'UpgradingBiogas'],
                       'hydrogen.gaseous_hydrogen.technologies_list': ['SMR', 'CoalGasification'],
                       'carbon_capture.technologies_list': ['direct_air_capture.AmineScrubbing', 'flue_gas_capture.CalciumLooping'],
                       'carbon_storage.technologies_list': ['DeepSalineFormation', 'GeologicMineralization'],
                       'invest_mix': self.energy_mix,
                       'energy_investment': self.energy_investment,
                       'forest_investment': self.forest_invest_df,
                       'scaling_factor_energy_investment': scaling_factor_energy_investment,
                       'invest_constraint_ref': invest_constraint_ref,
                       'invest_objective_ref': invest_objective_ref,
                       'is_dev': is_dev,
                       'invest_sum_ref': 2.,
                       'invest_limit_ref': 300.}
        one_invest_model = IndependentInvest()
        invest_constraint, invest_objective, invest_objective_sum, invest_objective_cons, invest_objective_cons_dc = one_invest_model.compute_invest_constraint_and_objective(
            inputs_dict)

        delta = (self.energy_investment['energy_investment'].values * scaling_factor_energy_investment  -
                 self.energy_mix[one_invest_model.distribution_list].sum(
            axis=1).values - self.forest_invest_df['forest_investment'].values) / (self.energy_investment['energy_investment'].values * scaling_factor_energy_investment)
        abs_delta = np.sqrt(compute_func_with_exp_min(delta**2, 1e-15))
        smooth_delta = np.asarray([smooth_maximum(abs_delta, alpha=10)])

        invest_constraint_th = delta / invest_constraint_ref
        invest_objective_th = smooth_delta / invest_objective_ref

        self.assertListEqual(np.round(invest_constraint_th, 8).tolist(
        ), np.round(invest_constraint['invest_constraint'].values, 8).tolist())

        self.assertListEqual(np.round(invest_objective_th, 8).tolist(
        ), np.round(invest_objective, 8).tolist())

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

        inputs_dict = {f'{self.name}.year_start': self.y_s,
                       f'{self.name}.year_end': self.y_e,
                       f'{self.name}.energy_list': self.energy_list,
                       f'{self.name}.ccs_list': self.ccs_list,
                       f'{self.name}.electricity.technologies_list': ['SolarPV', 'WindOnshore', 'CoalGen'],
                       f'{self.name}.methane.technologies_list': ['FossilGas', 'UpgradingBiogas'],
                       f'{self.name}.hydrogen.gaseous_hydrogen.technologies_list': ['SMR', 'CoalGasification'],
                       f'{self.name}.CCUS.carbon_capture.technologies_list': ['direct_air_capture.AmineScrubbing', 'flue_gas_capture.CalciumLooping'],
                       f'{self.name}.CCUS.carbon_storage.technologies_list': ['DeepSalineFormation', 'GeologicMineralization'],
                       f'{self.name}.{self.model_name}.invest_mix': self.energy_mix,
                       f'{self.name}.energy_investment': self.energy_investment,
                       f'{self.name}.{self.model_name}.forest_investment': self.forest_invest_df}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        for column in self.energy_mix.columns:
            if column != 'years':
                invest_techno_in = self.energy_mix[column].values

                if 'carbon_capture' in column or 'carbon_storage' in column:
                    invest_techno_out = self.ee.dm.get_value(
                        f'{self.name}.CCUS.{column}.invest_level')['invest'].values
                else:
                    invest_techno_out = self.ee.dm.get_value(
                        f'{self.name}.{column}.invest_level')['invest'].values

                self.assertListEqual(
                    invest_techno_in.tolist(), invest_techno_out.tolist())
        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)
#         for graph in graph_list:
#             graph.to_plotly().show()

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
                   }

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.investments.disciplines.independent_invest_disc.IndependentInvestDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.year_start': self.y_s,
                       f'{self.name}.year_end': self.y_e,
                       f'{self.name}.energy_list': self.energy_list,
                       f'{self.name}.ccs_list': self.ccs_list,
                       f'{self.name}.electricity.technologies_list': ['SolarPV', 'WindOnshore', 'CoalGen'],
                       f'{self.name}.methane.technologies_list': ['FossilGas', 'UpgradingBiogas'],
                       f'{self.name}.hydrogen.gaseous_hydrogen.technologies_list': ['SMR', 'CoalGasification'],
                       f'{self.name}.CCUS.carbon_capture.technologies_list': ['direct_air_capture.AmineScrubbing', 'flue_gas_capture.CalciumLooping'],
                       f'{self.name}.CCUS.carbon_storage.technologies_list': ['DeepSalineFormation', 'GeologicMineralization'],
                       f'{self.name}.{self.model_name}.invest_mix': self.energy_mix,
                       f'{self.name}.energy_investment': self.energy_investment,
                       f'{self.name}.is_dev': True,
                       f'{self.name}.forest_investment': self.forest_invest_df,
                       f'{self.name}.managed_wood_investment': self.managed_wood_invest_df,
                       f'{self.name}.unmanaged_wood_investment': self.unmanaged_wood_invest_df,
                       f'{self.name}.crop_investment': self.crop_invest_df}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        for column in self.energy_mix.columns:
            if column != 'years':
                invest_techno_in = self.energy_mix[column].values

                if 'carbon_capture' in column or 'carbon_storage' in column:
                    invest_techno_out = self.ee.dm.get_value(
                        f'{self.name}.CCUS.{column}.invest_level')['invest'].values
                else:
                    invest_techno_out = self.ee.dm.get_value(
                        f'{self.name}.{column}.invest_level')['invest'].values

                self.assertListEqual(
                    invest_techno_in.tolist(), invest_techno_out.tolist())
        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)
        # for graph in graph_list:
        #    graph.to_plotly().show()

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
                   }
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.investments.disciplines.independent_invest_disc.IndependentInvestDiscipline'
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
                       f'{self.name}.electricity.technologies_list': ['SolarPV', 'WindOnshore', 'CoalGen'],
                       f'{self.name}.methane.technologies_list': ['FossilGas', 'UpgradingBiogas'],
                       f'{self.name}.hydrogen.gaseous_hydrogen.technologies_list': ['SMR', 'CoalGasification'],
                       f'{self.name}.carbon_capture.technologies_list': ['direct_air_capture.AmineScrubbing', 'flue_gas_capture.CalciumLooping'],
                       f'{self.name}.carbon_storage.technologies_list': ['DeepSalineFormation', 'GeologicMineralization'],
                       f'{self.name}.{self.model_name}.invest_mix': self.energy_mix,
                       f'{self.name}.energy_investment': self.energy_investment,
                       f'{self.name}.forest_investment': self.forest_invest_df,
                       f'{self.name}.is_dev': True,
                       f'{self.name}.managed_wood_investment': self.managed_wood_invest_df,
                       f'{self.name}.unmanaged_wood_investment': self.unmanaged_wood_invest_df,
                       f'{self.name}.crop_investment': self.crop_invest_df}

        self.ee.load_study_from_input_dict(inputs_dict)

        disc = self.ee.root_process.sos_disciplines[0]
        all_technos_list = [
            f'{energy}.{techno}' for energy in energy_list + self.ccs_list for techno in inputs_dict[f'{self.name}.{energy}.technologies_list']]

        succeed = disc.check_jacobian(derr_approx='complex_step', inputs=[f'{self.name}.energy_investment',
                                                                          f'{self.name}.{self.model_name}.invest_mix', f'{self.name}.forest_investment',
                                                                          f'{self.name}.managed_wood_investment', f'{self.name}.unmanaged_wood_investment',
                                                                          f'{self.name}.crop_investment'],
                                      outputs=[
            f'{self.name}.{techno}.invest_level' for techno in all_technos_list] + [f'{self.name}.invest_objective',
                                                                                    f'{self.name}.invest_objective_sum' ,
                                                                                    f'{self.name}.invest_sum_cons',
                                                                                    f'{self.name}.invest_sum_cons_dc'],
            load_jac_path=join(dirname(__file__), 'jacobian_pkls',
                               f'jacobian_independent_invest_disc.pkl'))
        self.assertTrue(
            succeed, msg=f"Wrong gradient in {disc.get_disc_full_name()}")


if '__main__' == __name__:

    cls = TestIndependentInvest()
    cls.setUp()
    cls.test_03_independent_invest_disc_check_jacobian()
