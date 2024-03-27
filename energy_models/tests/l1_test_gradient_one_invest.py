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
import scipy.interpolate as sc

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import GaseousHydrogen
from energy_models.core.stream_type.energy_models.methanol import Methanol
from energy_models.core.stream_type.resources_data_disc import get_static_CO2_emissions, \
    get_static_prices
from energy_models.core.stream_type.resources_models.water import Water
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.methanol.co2_hydrogenation.co2_hydrogenation_disc import CO2HydrogenationDiscipline
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tests.core.abstract_jacobian_unit_test import AbstractJacobianUnittest

warnings.filterwarnings("ignore")


class OneInvestJacobianCase(AbstractJacobianUnittest):
    """
    Methanol Fuel jacobian test class
    """

    #AbstractJacobianUnittest.DUMP_JACOBIAN = True

    def analytic_grad_entry(self):
        return [
            self.test_01_one_invest_analytic_grad,
        ]

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.y_s = GlossaryEnergy.YearStartDefault
        self.y_e = GlossaryEnergy.YearEndDefault
        self.y_step = 1
        self.energy_list = [
            GlossaryEnergy.electricity, f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}',
            GlossaryEnergy.methane]

        self.ccs_list = [
            GlossaryEnergy.carbon_capture, GlossaryEnergy.carbon_storage]
        self.years = np.arange(self.y_s, self.y_e + 1)
        dict2 = {}
        dict2[GlossaryEnergy.Years] = self.years
        dict2[f'{GlossaryEnergy.electricity}.SolarPv'] = np.ones(len(self.years)) * 0.1
        dict2[f'{GlossaryEnergy.electricity}.WindOnshore'] = np.ones(len(self.years)) * 0.2
        dict2[f'{GlossaryEnergy.electricity}.CoalGen'] = np.ones(len(self.years)) * 0.3
        dict2[f'{GlossaryEnergy.methane}.FossilGas'] = np.ones(len(self.years)) * 0.4
        dict2[f'{GlossaryEnergy.methane}.UpgradingBiogas'] = np.ones(len(self.years)) * 0.5
        dict2[f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.WaterGasShift'] = np.ones(
            len(self.years)) * 0.6
        dict2[f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.Electrolysis.AWE'] = np.ones(
            len(self.years)) * 0.7
        dict2[f'{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.direct_air_capture}.AmineScrubbing'] = np.ones(
            len(self.years)) * 0.8
        dict2[f'{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.flue_gas_capture}.CalciumLooping'] = np.ones(
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
        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearStart}': self.y_s,
                       f'{self.name}.{GlossaryEnergy.YearEnd}': self.y_e,
                       f'{self.name}.{GlossaryEnergy.energy_list}': energy_list,
                       f'{self.name}.{GlossaryEnergy.ccs_list}': self.ccs_list,
                       f'{self.name}.{GlossaryEnergy.electricity}.technologies_list': ['SolarPv', 'WindOnshore',
                                                                                       'CoalGen'],
                       f'{self.name}.{GlossaryEnergy.methane}.technologies_list': ['FossilGas', 'UpgradingBiogas'],
                       f'{self.name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.technologies_list': [
                           'WaterGasShift',
                           'Electrolysis.AWE'],
                       f'{self.name}.{GlossaryEnergy.carbon_capture}.technologies_list': [
                           f'{GlossaryEnergy.direct_air_capture}.AmineScrubbing',
                           f'{GlossaryEnergy.flue_gas_capture}.CalciumLooping'],
                       f'{self.name}.{GlossaryEnergy.carbon_storage}.technologies_list': ['DeepSalineFormation',
                                                                                          'GeologicMineralization'],
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
    # AbstractJacobianUnittest.DUMP_JACOBIAN = True
    pass
