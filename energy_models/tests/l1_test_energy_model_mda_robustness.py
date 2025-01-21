'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/14-2024/06/24 Copyright 2023 Capgemini

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

import logging
from pathlib import Path
from shutil import rmtree
from time import sleep

import numpy as np
import pandas as pd
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tests.core.abstract_jacobian_unit_test import (
    AbstractJacobianUnittest,
)

from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.sos_processes.energy.MDA.energy_process_v0_mda.usecase import Study


class TestMDARobustness(AbstractJacobianUnittest):
    """
    MDA Robustness test class
    """

    def analytic_grad_entry(self):
        return [
            self.test_01_multi_scenario_perfos_execute,
        ]

    def setUp(self):
        
        self.dirs_to_del = []
        self.namespace = 'MyCase'
        self.study_name = f'{self.namespace}'
        self.year_start = GlossaryEnergy.YearStartDefault
        self.year_end = GlossaryEnergy.YearEndDefault
        logging.disable(logging.INFO)

    def tearDown(self):

        for dir_to_del in self.dirs_to_del:
            sleep(0.5)
            if Path(dir_to_del).is_dir():
                rmtree(dir_to_del)
        sleep(0.5)

    def test_01_multi_scenario_perfos_execute(self):

        self.name = 'Test'
        self.ee = ExecutionEngine(self.name)
        repo = 'energy_models.sos_processes.energy.MDA'  # O_subprocesses'
        builder = self.ee.factory.get_builder_from_process(
            repo, 'energy_process_v0_mda')

        self.ee.factory.set_builders_to_coupling_builder(builder)
        self.ee.configure()
        usecase = Study(execution_engine=self.ee)
        usecase.study_name = self.name
        values_dict = usecase.setup_usecase()

        full_values_dict = {}
        for dict_v in values_dict:
            full_values_dict.update(dict_v)
        self.ee.load_study_from_input_dict(full_values_dict)

        self.ee.execute()

        energy_prices0 = self.ee.dm.get_value(f'{self.name}.EnergyMix.{GlossaryEnergy.StreamPricesValue}')

        self.ee2 = ExecutionEngine(self.name)
        repo = 'energy_models.sos_processes.energy.MDA'
        builder = self.ee2.factory.get_builder_from_process(
            repo, 'energy_process_v0_mda')

        self.ee2.factory.set_builders_to_coupling_builder(builder)
        self.ee2.configure()
        usecase = Study(execution_engine=self.ee2)
        usecase.study_name = self.name
        values_dict = usecase.setup_usecase()
        years = np.arange(self.year_start, self.year_end + 1)

        values_dict[1][f'{self.name}.EnergyMix.{GlossaryEnergy.StreamPricesValue}'] = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.electricity: 90.,
             GlossaryEnergy.biomass_dry: 0.0,
             GlossaryEnergy.biogas: 0.0,
             GlossaryEnergy.methane: 0.0,
             GlossaryEnergy.solid_fuel: 0.0,
             f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}': 0.0,
             GlossaryEnergy.liquid_fuel: 0.0,
             GlossaryEnergy.syngas: 0.0,
             GlossaryEnergy.carbon_capture: 0.0,
             GlossaryEnergy.carbon_storage: 0.0,
             'BioDiesel': 0.0})

        full_values_dict = {}
        for dict_v in values_dict:
            full_values_dict.update(dict_v)
        self.ee2.load_study_from_input_dict(full_values_dict)

        self.ee2.execute()

        energy_prices1 = self.ee2.dm.get_value(f'{self.name}.EnergyMix.{GlossaryEnergy.StreamPricesValue}')
        tolerance = full_values_dict[f'{self.name}.tolerance']
        for column in energy_prices0:
            for value1, value2 in zip(list(energy_prices0[column].values), list(energy_prices1[column].values)):
                self.assertAlmostEqual(
                    abs(value1 - value2) / value1, 0.0, delta=100 * tolerance,
                    msg=f'{column} : {value1} and {value2} are different')


if '__main__' == __name__:
    cls = TestMDARobustness()
    cls.test_01_multi_scenario_perfos_execute()
