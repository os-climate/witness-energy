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
from os.path import join, dirname

import numpy as np
import pandas as pd
from pandas import read_csv
from climateeconomics.sos_processes.iam.witness.witness_coarse.usecase_witness_coarse_new import \
    DEFAULT_COARSE_TECHNO_DICT
from energy_models.core.energy_process_builder import INVEST_DISCIPLINE_OPTIONS
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.sos_processes.energy.MDA.heat_optim_sub_process.usecase_witness_optim_sub import Study
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tests.core.abstract_jacobian_unit_test import AbstractJacobianUnittest
from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from energy_models.core.stream_type.energy_models.heat import lowtemperatureheat
from energy_models.core.stream_type.energy_models.heat import mediumtemperatureheat
from energy_models.sos_processes.energy.techno_mix.hightemperatureheat_mix.usecase import \
    TECHNOLOGIES_LIST_DEV as hightemperatureheat_technos_dev
from energy_models.sos_processes.energy.techno_mix.lowtemperatureheat_mix.usecase import \
    TECHNOLOGIES_LIST_DEV as lowtemperatureheat_technos_dev
from energy_models.sos_processes.energy.techno_mix.mediumtemperatureheat_mix.usecase import \
    TECHNOLOGIES_LIST_DEV as mediumtemperatureheat_technos_dev
from energy_models.core.energy_study_manager import AGRI_TYPE, ENERGY_TYPE

DEFAULT_TECHNO_DICT = {
                       hightemperatureheat.name: {'type': ENERGY_TYPE, 'value': hightemperatureheat_technos_dev},
                       mediumtemperatureheat.name: {'type': ENERGY_TYPE, 'value': mediumtemperatureheat_technos_dev},
                       lowtemperatureheat.name: {'type': ENERGY_TYPE, 'value': lowtemperatureheat_technos_dev},
                       }

class HeatMixJacobianTestCase(AbstractJacobianUnittest):
    # AbstractJacobianUnittest.DUMP_JACOBIAN = True

    def analytic_grad_entry(self):
        return []
    def setUp(self):
        self.name = 'Test'
        self.model_name = 'HeatMix'
        # self.year_start =GlossaryCore.YeartStartDefault
        #self.year_end = 2030 #GlossaryCore.YeartEndDefault
        self.techno_dict = DEFAULT_TECHNO_DICT

        self.ee = ExecutionEngine(self.name)
        repo = 'energy_models.sos_processes.energy.MDA'
        builder = self.ee.factory.get_builder_from_process(
            repo, 'heat_optim_sub_process',
            techno_dict=DEFAULT_TECHNO_DICT, invest_discipline=INVEST_DISCIPLINE_OPTIONS[2])

        self.ee.factory.set_builders_to_coupling_builder(builder)
        self.ee.configure()
        usecase = Study(execution_engine=self.ee,
                         techno_dict=DEFAULT_TECHNO_DICT, main_study=True)
        usecase.study_name = self.name
        values_dict = usecase.setup_usecase()


        self.ee.display_treeview_nodes()
        self.full_values_dict = {}
        for dict_v in values_dict:
            self.full_values_dict.update(dict_v)
        self.full_values_dict[f'{self.name}.epsilon0'] = 1.0
        self.full_values_dict[f'{self.name}.tolerance'] = 1.0e-8
        self.full_values_dict[f'{self.name}.max_mda_iter'] = 2
        forest_investment = pd.DataFrame({
            GlossaryEnergy.Years: np.arange(GlossaryEnergy.YeartStartDefault, 2050 + 1),
            GlossaryEnergy.ForestInvestmentValue: 5.
        })
        self.full_values_dict.update({
            f"{self.name}.InvestmentDistribution.{GlossaryEnergy.ForestInvestmentValue}": forest_investment,

        })
        self.ee.load_study_from_input_dict(self.full_values_dict)

        self.ee.execute()

        self.disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.MDA.HeatMix')[0].mdo_discipline_wrapp.mdo_discipline
        self.energy_list = [GlossaryEnergy.renewable, GlossaryEnergy.fossil]
        # AbstractJacobianUnittest.DUMP_JACOBIAN = True

    def TearDown(self):
        '''
        To execute after tests
        '''
        # desactivate dump
        # AbstractJacobianUnittest.DUMP_JACOBIAN = False

    def test_01_heat_mix_analytic_grad(self):
        self.ee.execute()
        AbstractJacobianUnittest.DUMP_JACOBIAN = True
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_heat_mix_discipline.pkl', discipline=self.disc, step=1e-15, local_data=self.disc.local_data,
                            inputs=[f'{self.name}.MDA.{self.model_name}.CO2_emission_mix',
                                    f'{self.name}.MDA.{self.model_name}.{GlossaryEnergy.TargetHeatProductionValue}',
                                    f'{self.name}.MDA.{self.model_name}.heat.hightemperatureheat.{GlossaryEnergy.EnergyProductionValue}',
                                    f'{self.name}.MDA.{self.model_name}.heat.mediumtemperatureheat.{GlossaryEnergy.EnergyProductionValue}',
                                    f'{self.name}.MDA.{self.model_name}.heat.lowtemperatureheat.{GlossaryEnergy.EnergyProductionValue}'
                                    ],
                            outputs=[f'{self.name}.MDA.FunctionsManager.{GlossaryEnergy.CO2MinimizationObjective}',
                                     f'{self.name}.MDA.{self.model_name}.{GlossaryEnergy.EnergyCO2EmissionsValue}',
                                     f'{self.name}.MDA.{self.model_name}.{GlossaryEnergy.EnergyProductionValue}',
                                     f'{self.name}.MDA.FunctionsManager.{GlossaryEnergy.TargetHeatProductionConstraintValue}',
                            ],
                            derr_approx='complex_step')

