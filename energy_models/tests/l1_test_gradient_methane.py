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

from os.path import dirname

import numpy as np
import pandas as pd
from sostrades_optimization_plugins.models.test_class import GenericDisciplinesTestClass

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.resources_data_disc import (
    get_default_resources_CO2_emissions,
    get_default_resources_prices,
)
from energy_models.glossaryenergy import GlossaryEnergy


class MethaneJacobianTestCase(GenericDisciplinesTestClass):
    """Methane jacobian test class"""

    def setUp(self):
        self.name = "Test"
        self.override_dump_jacobian = False
        self.show_graph = False
        self.jacobian_test = False
        self.pickle_directory = dirname(__file__)
        self.ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   GlossaryEnergy.NS_WITNESS: f'{self.name}',
                   GlossaryEnergy.NS_ENERGY_MIX: f'{self.name}',
                   
                   GlossaryEnergy.NS_CCS: f'{self.name}',
                   'ns_methane': self.name,
                   'ns_resource': f'{self.name}'}

        self.stream_name = GlossaryEnergy.methane
        self.year_start = GlossaryEnergy.YearStartDefault
        self.year_end = GlossaryEnergy.YearEndDefaultValueGradientTest
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.stream_prices = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                           GlossaryEnergy.carbon_captured: 70,
                                           GlossaryEnergy.electricity: 90.,
                                           f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}': 120.,
                                           GlossaryEnergy.biogas: 63.
                                           })

        self.stream_co2_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.electricity: 0.0,
             GlossaryEnergy.carbon_captured: -2, f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}': 0.0, GlossaryEnergy.biogas: -0.51})
        # Use the same inest as SMR techno

        self.invest_level_methanation = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                                      GlossaryEnergy.InvestValue: np.linspace(4., 5.0, len(self.years))})

        self.invest_level = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                          GlossaryEnergy.InvestValue: np.linspace(4., 5.0, len(self.years))})

        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.CO2Tax: np.linspace(14., 40., len(self.years))})
        self.margin = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.MarginValue: 110.0})
        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, 'transport': 200.0})

        self.resources_price = pd.DataFrame(
            columns=[GlossaryEnergy.Years, GlossaryEnergy.WaterResource])
        self.resources_price[GlossaryEnergy.Years] = self.years
        self.resources_price[GlossaryEnergy.WaterResource] = 1.4
        # ---Ratios---
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.linspace(100.0, 100.0, len(self.years))))
        demand_ratio_dict[GlossaryEnergy.Years] = self.years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)
        self.all_streams_demand_ratio[GlossaryEnergy.carbon_captured] = 1.0

        resource_ratio_dict = dict(
            zip(EnergyMix.resource_list, np.linspace(0.8, 0.1, len(self.years))))
        resource_ratio_dict[GlossaryEnergy.Years] = self.years
        self.all_resource_ratio_usable_demand = pd.DataFrame(
            resource_ratio_dict)

    def get_inputs_dict(self):
        return {f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                           self.years),
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_default_resources_prices(
                           self.years),
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.CO2}_intensity_by_energy': self.stream_co2_emissions,
                       f'{self.name}.{GlossaryEnergy.CH4}_intensity_by_energy': self.stream_co2_emissions * 0.1,
                       f'{self.name}.{GlossaryEnergy.N2O}_intensity_by_energy': self.stream_co2_emissions * 0.01,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.LifetimeName}': GlossaryEnergy.LifetimeDefaultValueGradientTest,
                       }
    def test_01_fossil_gas_discipline_jacobian(self):
        self.model_name = 'fossil_gas'
        self.mod_path = 'energy_models.models.methane.fossil_gas.fossil_gas_disc.FossilGasDiscipline'

    def test_02_methanation_discipline_jacobian(self):
        self.model_name = 'methanation'
        self.mod_path = 'energy_models.models.methane.methanation.methanation_disc.MethanationDiscipline'

    def test_03_upgrading_biogas_jacobian(self):
        self.model_name = 'upgrading_biogas'
        self.mod_path = 'energy_models.models.methane.upgrading_biogas.upgrading_biogas_disc.UpgradingBiogasDiscipline'
