'''
Copyright 2025 Capgemini

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
from os.path import dirname

import numpy as np
import pandas as pd
from sostrades_optimization_plugins.models.test_class import GenericDisciplinesTestClass

from energy_models.glossaryenergy import GlossaryEnergy


class EnergyMarketDiscTestCase(GenericDisciplinesTestClass):
    """Energy Market discipline test class"""

    def setUp(self):
        self.name = 'Test'
        self.model_name = 'Energy market'
        self.mod_path = 'energy_models.core.energy_market.energy_market_disc.EnergyMarketDiscipline'
        self.ns_dict = {'ns_public': self.name, GlossaryEnergy.NS_ENERGY_MIX: self.name, GlossaryEnergy.NS_WITNESS: self.name, "ns_energy_market": self.name}
        self.pickle_prefix = self.model_name
        self.jacobian_test = False
        self.show_graphs = False
        self.override_dump_jacobian = False
        self.pickle_directory = dirname(__file__)


        self.year_start = GlossaryEnergy.YearStartDefault
        self.year_end = GlossaryEnergy.YearEndDefaultValueGradientTest
        self.years = np.arange(self.year_start, self.year_end + 1)


        self.energy_mix_net_production = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.electricity: 10,
            GlossaryEnergy.syngas: 20,
            GlossaryEnergy.biogas: 10,
            "coal": 30.,
            "Total": 70.,
        })

        self.ccus_energies_demand = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.electricity: 10,
            "coal": 45.,
            GlossaryEnergy.syngas: 10,
        })


    def get_inputs_dict(self) -> dict:
        return {
            f'{self.name}.{GlossaryEnergy.YearStart}': self.year_start,
            f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
            f'{self.name}.consumers_actors': [GlossaryEnergy.CCUS],
            f'{self.name}.{GlossaryEnergy.EnergyMixNetProductionsDfValue}': self.energy_mix_net_production,
            f'{self.name}.{GlossaryEnergy.CCUS}_{GlossaryEnergy.EnergyDemandValue}': self.ccus_energies_demand,
        }
    def test_01_energy_market_discipline(self):
        self.model_name = 'energy_market_1'


    def test_02_energy_market_discipline_non_simplified_ratios(self):
        self.model_name = 'energy_market_2'
        self.inputs_dicts = {
            f'{self.name}.{GlossaryEnergy.SimplifiedMarketEnergyDemandValue}': False,
        }

    def test_03_energy_market_discipline_multiple_consumers(self):
        self.model_name = 'energy_market_3'
        self.macro_eco_demands = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.electricity: 3,
            "coal": 15.,
            GlossaryEnergy.syngas: 6,
        })
        self.inputs_dicts = {
            f'{self.name}.{GlossaryEnergy.SimplifiedMarketEnergyDemandValue}': False,
            f'{self.name}.Macroeconomics_{GlossaryEnergy.EnergyDemandValue}': self.macro_eco_demands,
            f'{self.name}.consumers_actors': [GlossaryEnergy.CCUS, 'Macroeconomics'],
        }

    def test_04_energy_market_discipline_multiple_consumers_simplified(self):
        self.model_name = 'energy_market_4'
        self.macro_eco_demands = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.electricity: 3,
            "coal": 15.,
            GlossaryEnergy.syngas: 6,
        })
        self.inputs_dicts = {
            f'{self.name}.{GlossaryEnergy.SimplifiedMarketEnergyDemandValue}': True,
            f'{self.name}.Macroeconomics_{GlossaryEnergy.EnergyDemandValue}': self.macro_eco_demands,
            f'{self.name}.consumers_actors': [GlossaryEnergy.CCUS, 'Macroeconomics'],
        }

