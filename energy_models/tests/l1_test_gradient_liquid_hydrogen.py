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
from energy_models.core.stream_type.energy_models.liquid_hydrogen import LiquidHydrogen
from energy_models.core.stream_type.resources_data_disc import (
    get_default_resources_CO2_emissions,
    get_default_resources_prices,
)
from energy_models.glossaryenergy import GlossaryEnergy


class LiquidHydrogenJacobianTestCase(GenericDisciplinesTestClass):
    """LiquidHydrogen jacobian test class"""

    def setUp(self):
        self.name = 'Test'
        self.override_dump_jacobian = False
        self.show_graph = False
        self.jacobian_test = False
        self.pickle_directory = dirname(__file__)
        self.stream_name = GlossaryEnergy.liquid_hydrogen
        self.year_end = GlossaryEnergy.YearEndDefaultValueGradientTest
        self.ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                        'ns_energy_study': f'{self.name}',
                        'ns_hydrogen': f'{self.name}',
                        'ns_liquid_hydrogen': f'{self.name}',
                        'ns_resource': f'{self.name}'}
        self.years = np.arange(GlossaryEnergy.YearStartDefault, self.year_end + 1)

        self.hydrogen_liquefaction_techno_prices = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.HydrogenLiquefaction: 90.,
             'HydrogenLiquefaction_wotaxes': 90.})

        self.hydrogen_liquefaction_consumption = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                                               f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen} ({GlossaryEnergy.energy_unit})': 230.779470,
                                                               f'{GlossaryEnergy.electricity} ({GlossaryEnergy.energy_unit})': 82.649011})

        self.hydrogen_liquefaction_production = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                                              LiquidHydrogen.name + ' (TWh)': 2304.779470, })

        self.hydrogen_liquefaction_carbon_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.HydrogenLiquefaction: 0.0, f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}': 0.0,
             GlossaryEnergy.electricity: 0.0,
             'production': 0.0})

        self.stream_prices = pd.DataFrame({GlossaryEnergy.Years: self.years, GlossaryEnergy.electricity: 90.,
                                           f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}': 33.,
                                           })

        self.stream_co2_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.electricity: 0.02, f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}': 0.0})

        self.invest_level = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.InvestValue: 0.1715})

        

        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.CO2Tax: np.linspace(14., 40., len(self.years))})
        self.margin = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.MarginValue: 110.0})
        # From future of hydrogen
        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, 'transport': 500.0})

        CO2_tax = np.linspace(10., 90., len(self.years))
        self.CO2_taxes = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                       GlossaryEnergy.CO2Tax: CO2_tax})

        self.invest = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                    GlossaryEnergy.InvestValue: np.linspace(4., 5.0, len(self.years))})
        self.land_use_required_mock = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, 'random techno (Gha)': 0.0})

        self.land_use_required_HydrogenLiquefaction = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, f'{GlossaryEnergy.HydrogenLiquefaction} (Gha)': 0.0})
        # ---Ratios---
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.linspace(1.0, 1.0, len(self.years))))
        demand_ratio_dict[GlossaryEnergy.Years] = self.years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)

        resource_ratio_dict = dict(
            zip(EnergyMix.resource_list, np.linspace(1.0, 1.0, len(self.years))))
        resource_ratio_dict[GlossaryEnergy.Years] = self.years
        self.all_resource_ratio_usable_demand = pd.DataFrame(
            resource_ratio_dict)

    def get_inputs_dict(self):
        return {f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                           self.years),
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_default_resources_prices(
                           self.years),
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.CO2_taxes,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': pd.concat(
                           [self.margin[GlossaryEnergy.Years], self.margin[GlossaryEnergy.MarginValue] / 1.1],
                           axis=1, keys=[GlossaryEnergy.Years, GlossaryEnergy.MarginValue]),
                       f'{self.name}.{GlossaryEnergy.EnergyPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
                       f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.LifetimeName}': GlossaryEnergy.LifetimeDefaultValueGradientTest,
                       }
    def test_01_hydrogen_liquefaction_jacobian(self):
        self.model_name = 'hydrogen_liquefaction'
        self.mod_path = 'energy_models.models.liquid_hydrogen.hydrogen_liquefaction.hydrogen_liquefaction_disc.HydrogenLiquefactionDiscipline'