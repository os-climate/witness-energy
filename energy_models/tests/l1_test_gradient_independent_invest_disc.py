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

        self.year_start = GlossaryEnergy.YearStartDefault
        self.year_end = GlossaryEnergy.YearEndDefaultValueGradientTest
        self.energy_list = [
            GlossaryEnergy.electricity, f"{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}", GlossaryEnergy.methane]
        self.energy_list_bis = [
            GlossaryEnergy.electricity, f"{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}", GlossaryEnergy.methane]

        self.ccs_list = [
            GlossaryEnergy.carbon_captured, GlossaryEnergy.carbon_storage]
        self.years = np.arange(self.year_start, self.year_end + 1)
        year_range = self.year_end - self.year_start + 1
        self.energy_mix = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            f'{GlossaryEnergy.electricity}.{GlossaryEnergy.SolarPv}': 10.0,
            f'{GlossaryEnergy.electricity}.{GlossaryEnergy.WindOnshore}': 20.0,
            f'{GlossaryEnergy.electricity}.{GlossaryEnergy.CoalGen}': 30.0,
            f'{GlossaryEnergy.methane}.{GlossaryEnergy.FossilGas}': 40.0,
            f'{GlossaryEnergy.methane}.{GlossaryEnergy.UpgradingBiogas}': 50.0,
            f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.WaterGasShift}': 60.0,
            f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.ElectrolysisAWE}': 70.0,
            f'{GlossaryEnergy.carbon_captured}.{GlossaryEnergy.direct_air_capture}.{GlossaryEnergy.AmineScrubbing}': 80.0,
            f'{GlossaryEnergy.carbon_captured}.{GlossaryEnergy.flue_gas_capture}.{GlossaryEnergy.CalciumLooping}': 90.0,
            f'{GlossaryEnergy.carbon_storage}.{GlossaryEnergy.DeepSalineFormation}': 100.0,
            f'{GlossaryEnergy.carbon_storage}.{GlossaryEnergy.GeologicMineralization}': 110.0})

        self.scaling_factor_techno_consumption = 1e3
        self.scaling_factor_techno_production = 1e3

        self.reforestation_investment_df = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.ReforestationInvestmentValue: np.linspace(5, 8, year_range)})

        self.managed_wood_invest_df = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, "investment": np.linspace(0.5, 2, year_range)})

        self.unmanaged_wood_invest_df = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, "investment": np.linspace(2, 3, year_range)})

        self.deforestation_invest_df = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, "investment": np.linspace(1.0, 0.1, year_range)})

        self.crop_invest_df = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, "investment": np.linspace(0.5, 0.25, year_range)})

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
                       f"{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}"]
        max_budget = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.MaxBudgetValue: np.linspace(800, 970, len(self.years))
        })
        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearStart}': self.year_start,
                       f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.energy_list}': energy_list,
                       f'{self.name}.{GlossaryEnergy.ccs_list}': self.ccs_list,
                       f'{self.name}.{GlossaryEnergy.MaxBudgetValue}': max_budget,
                       f'{self.name}.{GlossaryEnergy.electricity}.{GlossaryEnergy.technologies_list}': [GlossaryEnergy.SolarPv, GlossaryEnergy.WindOnshore, GlossaryEnergy.CoalGen],
                       f'{self.name}.{GlossaryEnergy.methane}.{GlossaryEnergy.technologies_list}': [GlossaryEnergy.FossilGas, GlossaryEnergy.UpgradingBiogas],
                       f'{self.name}.{GlossaryEnergy.biomass_dry}.{GlossaryEnergy.technologies_list}': [],
                       f'{self.name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.technologies_list}': [GlossaryEnergy.WaterGasShift, GlossaryEnergy.ElectrolysisAWE],
                       f'{self.name}.{GlossaryEnergy.carbon_captured}.{GlossaryEnergy.technologies_list}': [f'{GlossaryEnergy.direct_air_capture}.{GlossaryEnergy.AmineScrubbing}',
                                                                         f'{GlossaryEnergy.flue_gas_capture}.{GlossaryEnergy.CalciumLooping}'],
                       f'{self.name}.{GlossaryEnergy.carbon_storage}.{GlossaryEnergy.technologies_list}': [GlossaryEnergy.DeepSalineFormation,
                                                                         GlossaryEnergy.GeologicMineralization],
                       f'{self.name}.{GlossaryEnergy.invest_mix}': self.energy_mix, }

        self.ee.load_study_from_input_dict(inputs_dict)
        self.ee.execute()

        disc = self.ee.root_process.proxy_disciplines[0].discipline_wrapp.discipline
        all_technos_list = [
            f'{energy}.{techno}' for energy in energy_list + self.ccs_list for techno in
            inputs_dict[f'{self.name}.{energy}.{GlossaryEnergy.techno_list}']]
        self.check_jacobian(derr_approx='complex_step',
                            inputs=[f'{self.name}.{GlossaryEnergy.invest_mix}',],
                            outputs=[
                                        f'{self.name}.{techno}.{GlossaryEnergy.InvestLevelValue}' for techno
                                        in
                                        all_technos_list] +
                                    [f'{self.name}.{GlossaryEnergy.EnergyMix}.{GlossaryEnergy.InvestmentsValue}',
                                     f'{self.name}.{GlossaryEnergy.CCUS}.{GlossaryEnergy.InvestmentsValue}',
                                     f'{self.name}.{GlossaryEnergy.MaxBudgetConstraintValue}',],
                            local_data=disc.local_data,
                            location=dirname(__file__),
                            discipline=disc,
                            filename='jacobian_independent_invest_disc.pkl', threshold=1e-5, )
