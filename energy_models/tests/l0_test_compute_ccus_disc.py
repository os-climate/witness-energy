'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/01-2024/06/24 Copyright 2023 Capgemini

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


class CCUSDiscTestCase(GenericDisciplinesTestClass):
    """CCUS discipline test class"""

    def setUp(self):
        self.name = 'Test'
        self.model_name = 'CCUS'
        self.ns_dict = {'ns_public': self.name, GlossaryEnergy.NS_CCS: self.name, GlossaryEnergy.NS_ENERGY_MIX: self.name}
        self.pickle_prefix = self.model_name
        self.jacobian_test = True
        self.show_graphs = False
        self.override_dump_jacobian = False
        self.pickle_directory = dirname(__file__)


        self.year_start = GlossaryEnergy.YearStartDefault
        self.year_end = GlossaryEnergy.YearEndDefaultValueGradientTest
        self.years = np.arange(self.year_start, self.year_end + 1)

        self.carbon_capture_energies_consumption = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            f"{GlossaryEnergy.electricity} (TWh)": 10.,
            f"{GlossaryEnergy.heat} (TWh)": 12.,
        })

        self.carbon_capture_energies_demand = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            f"{GlossaryEnergy.electricity} (TWh)": 10.,
            f"{GlossaryEnergy.heat} (TWh)": 12.,
        })

        self.carbon_storage_energies_consumption = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            f"{GlossaryEnergy.electricity} (TWh)": 10.,
        })

        self.carbon_storage_energies_demand = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            f"{GlossaryEnergy.electricity} (TWh)": 10.,
        })

        self.carbon_capture_prod = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            f"{GlossaryEnergy.carbon_captured} (Mt)": 10. * 1e3,
        })

        self.carbon_storage_prod = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            f"{GlossaryEnergy.carbon_storage} (Mt)": 9.5 * 1e3,
        })

        self.carbon_capture_land_use = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            "Land use": 54.,
        })

        self.carbon_storage_land_use = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            "Land use": 7.,
        })

        self.carbon_capture_prices = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.carbon_captured: 70.,
        })

        self.carbon_storage_prices = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.carbon_storage: 5.4,
        })

        self.energy_mix_ccs_consumptions = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.carbon_captured: 1.,
            GlossaryEnergy.carbon_storage: 0.,
        })

        self.energy_mix_ccs_demands = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.carbon_captured: 1.,
            GlossaryEnergy.carbon_storage: 0.,
        })


    def get_inputs_dict(self) -> dict:
        return {
            f'{self.name}.{GlossaryEnergy.YearStart}': self.year_start,
            f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,

            f'{self.name}.{GlossaryEnergy.carbon_captured}.{GlossaryEnergy.StreamPricesValue}': self.carbon_capture_prices,
            f'{self.name}.{GlossaryEnergy.carbon_captured}.{GlossaryEnergy.StreamProductionValue}': self.carbon_capture_prod,
            f'{self.name}.{GlossaryEnergy.carbon_captured}.{GlossaryEnergy.StreamEnergyDemandValue}': self.carbon_capture_energies_demand,
            f'{self.name}.{GlossaryEnergy.carbon_captured}.{GlossaryEnergy.StreamEnergyConsumptionValue}': self.carbon_capture_energies_demand,
            f'{self.name}.{GlossaryEnergy.carbon_captured}.{GlossaryEnergy.LandUseRequiredValue}': self.carbon_capture_land_use,

            f'{self.name}.{GlossaryEnergy.carbon_storage}.{GlossaryEnergy.StreamPricesValue}': self.carbon_storage_prices,
            f'{self.name}.{GlossaryEnergy.carbon_storage}.{GlossaryEnergy.StreamProductionValue}': self.carbon_storage_prod,
            f'{self.name}.{GlossaryEnergy.carbon_storage}.{GlossaryEnergy.StreamEnergyDemandValue}': self.carbon_storage_energies_demand,
            f'{self.name}.{GlossaryEnergy.carbon_storage}.{GlossaryEnergy.StreamEnergyConsumptionValue}': self.carbon_storage_energies_demand,
            f'{self.name}.{GlossaryEnergy.carbon_storage}.{GlossaryEnergy.LandUseRequiredValue}': self.carbon_storage_land_use,

            f'{self.name}.{GlossaryEnergy.EnergyMixCCSDemandsDfValue}': self.energy_mix_ccs_demands,
            f'{self.name}.{GlossaryEnergy.EnergyMixCCSConsumptionDfValue}': self.energy_mix_ccs_consumptions,
        }
    def test_01_CCUS_discipline(self):
        self.mod_path = 'energy_models.core.ccus.ccus_disc.CCUS_Discipline'