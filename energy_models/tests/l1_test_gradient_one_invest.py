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


class OneInvestJacobianCase(AbstractJacobianUnittest):
    """
    Methanol Fuel jacobian test class
    """

    def analytic_grad_entry(self):
        return [
            self.test_01_one_invest_analytic_grad,
        ]

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.year_start = GlossaryEnergy.YearStartDefault
        self.year_end = GlossaryEnergy.YearEndDefault
        self.energy_list = [
            GlossaryEnergy.electricity, f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}',
            GlossaryEnergy.methane]

        self.ccs_list = [
            GlossaryEnergy.carbon_capture, GlossaryEnergy.carbon_storage]
        self.years = np.arange(self.year_start, self.year_end + 1)

        self.energy_mix = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            f'{GlossaryEnergy.electricity}.{GlossaryEnergy.SolarPv}': 0.1,
            f'{GlossaryEnergy.electricity}.{GlossaryEnergy.WindOnshore}': 0.2,
            f'{GlossaryEnergy.electricity}.{GlossaryEnergy.CoalGen}': 0.3,
            f'{GlossaryEnergy.methane}.{GlossaryEnergy.FossilGas}': 0.4,
            f'{GlossaryEnergy.methane}.{GlossaryEnergy.UpgradingBiogas}': 0.5,
            f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.WaterGasShift}': 0.6,
            f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.ElectrolysisAWE}': 0.7,
            f'{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.direct_air_capture}.{GlossaryEnergy.AmineScrubbing}': 0.8,
            f'{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.flue_gas_capture}.{GlossaryEnergy.CalciumLooping}': 0.9,
            f'{GlossaryEnergy.carbon_storage}.{GlossaryEnergy.DeepSalineFormation}': 1.0,
            f'{GlossaryEnergy.carbon_storage}.{GlossaryEnergy.GeologicMineralization}': 1.1, })

        invest = 1e3 * (1.02 ** np.arange(len(self.years)))
        self.energy_investment = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.EnergyInvestmentsValue: invest})

        self.scaling_factor_techno_consumption = 1e3
        self.scaling_factor_techno_production = 1e3

    def tearDown(self):
        pass

    def test_01_one_invest_analytic_grad(self):
        self.name = 'Energy'
        self.model_name = 'Invest'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {GlossaryEnergy.NS_WITNESS: self.name,
                   'ns_public': self.name,
                   'ns_energy_study': self.name,
                   'ns_energy': self.name,
                   GlossaryEnergy.NS_CCS: f'{self.name}',
                   }
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.investments.disciplines.one_invest_disc.OneInvestDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        energy_list = [GlossaryEnergy.electricity, GlossaryEnergy.methane,
                       f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}']
        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearStart}': self.year_start,
                       f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.energy_list}': energy_list,
                       f'{self.name}.{GlossaryEnergy.ccs_list}': self.ccs_list,
                       f'{self.name}.{GlossaryEnergy.electricity}.{GlossaryEnergy.technologies_list}': [GlossaryEnergy.SolarPv, GlossaryEnergy.WindOnshore,
                                                                                       GlossaryEnergy.CoalGen],
                       f'{self.name}.{GlossaryEnergy.methane}.{GlossaryEnergy.technologies_list}': [GlossaryEnergy.FossilGas, GlossaryEnergy.UpgradingBiogas],
                       f'{self.name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.{GlossaryEnergy.technologies_list}': [
                           GlossaryEnergy.WaterGasShift,
                           GlossaryEnergy.ElectrolysisAWE],
                       f'{self.name}.{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.technologies_list}': [
                           f'{GlossaryEnergy.direct_air_capture}.{GlossaryEnergy.AmineScrubbing}',
                           f'{GlossaryEnergy.flue_gas_capture}.{GlossaryEnergy.CalciumLooping}'],
                       f'{self.name}.{GlossaryEnergy.carbon_storage}.{GlossaryEnergy.technologies_list}': [GlossaryEnergy.DeepSalineFormation,
                                                                                          GlossaryEnergy.GeologicMineralization],
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.invest_mix}': self.energy_mix,
                       f'{self.name}.{GlossaryEnergy.EnergyInvestmentsValue}': self.energy_investment}

        self.ee.load_study_from_input_dict(inputs_dict)
        self.ee.execute()

        all_technos_list = [
            f'{energy}.{techno}' for energy in energy_list + self.ccs_list for techno in
            inputs_dict[f'{self.name}.{energy}.{GlossaryEnergy.techno_list}']]
        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_one_invest_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc_techno.local_data,
                            inputs=[f'{self.name}.{GlossaryEnergy.EnergyInvestmentsValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryEnergy.invest_mix}'],
                            outputs=[
                                f'{self.name}.{techno}.{GlossaryEnergy.InvestLevelValue}' for techno in
                                all_technos_list],
                            )


if '__main__' == __name__:
    pass
