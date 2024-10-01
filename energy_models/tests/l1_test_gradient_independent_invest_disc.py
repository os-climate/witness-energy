'''
Copyright 2024 Capgemini
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

import warnings
from os.path import dirname

import numpy as np
import pandas as pd
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tests.core.abstract_jacobian_unit_test import (
    AbstractJacobianUnittest,
)

from energy_models.glossaryenergy import GlossaryEnergy

warnings.filterwarnings("ignore")


class IndependentInvestDisciplineJacobianCase(AbstractJacobianUnittest):
    """
    Ethanol Fuel jacobian test class
    """

    def analytic_grad_entry(self):
        return [
            self.test_01_analytic_grad,
            ]

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.y_s = GlossaryEnergy.YearStartDefault
        self.y_e = GlossaryEnergy.YearEndDefaultValueGradientTest
        self.y_step = 1
        self.energy_list = [
            GlossaryEnergy.electricity, f"{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}", GlossaryEnergy.methane]
        self.energy_list_bis = [
            GlossaryEnergy.electricity, f"{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}", GlossaryEnergy.methane, GlossaryEnergy.biomass_dry]

        self.ccs_list = [
            GlossaryEnergy.carbon_capture, GlossaryEnergy.carbon_storage]
        self.years = np.arange(self.y_s, self.y_e + 1)
        year_range = self.y_e - self.y_s + 1
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
        self.forest_invest_df = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.ForestInvestmentValue: forest_invest})
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

    def tearDown(self):
        pass

    def test_01_analytic_grad(self):
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
                   'ns_forest': self.name,
                   GlossaryEnergy.NS_ENERGY_MIX: self.name
                   }
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.investments.disciplines.independent_invest_disc.IndependentInvestDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        energy_list = [GlossaryEnergy.electricity, GlossaryEnergy.methane,
                       f"{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}", GlossaryEnergy.biomass_dry]
        max_budget = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.MaxBudgetValue: np.linspace(800, 970, len(self.years))
        })
        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearStart}': self.y_s,
                       f'{self.name}.{GlossaryEnergy.YearEnd}': self.y_e,
                       f'{self.name}.{GlossaryEnergy.energy_list}': energy_list,
                       f'{self.name}.{GlossaryEnergy.ccs_list}': self.ccs_list,
                       f'{self.name}.{GlossaryEnergy.MaxBudgetValue}': max_budget,
                       f'{self.name}.{GlossaryEnergy.electricity}.{GlossaryEnergy.technologies_list}': [GlossaryEnergy.SolarPv, GlossaryEnergy.WindOnshore, GlossaryEnergy.CoalGen],
                       f'{self.name}.{GlossaryEnergy.methane}.{GlossaryEnergy.technologies_list}': [GlossaryEnergy.FossilGas, GlossaryEnergy.UpgradingBiogas],
                       f'{self.name}.{GlossaryEnergy.biomass_dry}.{GlossaryEnergy.technologies_list}': [],
                       f'{self.name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.technologies_list}': [GlossaryEnergy.WaterGasShift, GlossaryEnergy.ElectrolysisAWE],
                       f'{self.name}.{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.technologies_list}': [f'{GlossaryEnergy.direct_air_capture}.{GlossaryEnergy.AmineScrubbing}',
                                                                         f'{GlossaryEnergy.flue_gas_capture}.{GlossaryEnergy.CalciumLooping}'],
                       f'{self.name}.{GlossaryEnergy.carbon_storage}.{GlossaryEnergy.technologies_list}': [GlossaryEnergy.DeepSalineFormation,
                                                                         GlossaryEnergy.GeologicMineralization],
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.invest_mix}': self.energy_mix,
                       f'{self.name}.{GlossaryEnergy.ForestInvestmentValue}': self.forest_invest_df,
                       f'{self.name}.managed_wood_investment': self.managed_wood_invest_df,
                       f'{self.name}.deforestation_investment': self.deforestation_invest_df,
                       f'{self.name}.crop_investment': self.crop_invest_df}

        self.ee.load_study_from_input_dict(inputs_dict)
        self.ee.execute()

        disc = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline
        all_technos_list = [
            f'{energy}.{techno}' for energy in energy_list + self.ccs_list for techno in
            inputs_dict[f'{self.name}.{energy}.{GlossaryEnergy.techno_list}']]
        self.check_jacobian(derr_approx='complex_step',
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.invest_mix}',
                                    f'{self.name}.{GlossaryEnergy.ForestInvestmentValue}',
                                    f'{self.name}.managed_wood_investment',
                                    f'{self.name}.deforestation_investment',
                                    f'{self.name}.crop_investment'],
                            outputs=[
                                        f'{self.name}.{techno}.{GlossaryEnergy.InvestLevelValue}' for techno
                                        in
                                        all_technos_list] +
                                    [f'{self.name}.{GlossaryEnergy.EnergyInvestmentsWoTaxValue}',
                                     f'{self.name}.{GlossaryEnergy.MaxBudgetConstraintValue}',
                                     f'{self.name}.{GlossaryEnergy.EnergyInvestmentsMinimizationObjective}'],
                            local_data=disc.local_data,
                            location=dirname(__file__),
                            discipline=disc,
                            filename='jacobian_independent_invest_disc.pkl', threshold=1e-5, )
