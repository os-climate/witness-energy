'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2024/06/24 Copyright 2023 Capgemini

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
import unittest

import numpy as np
import pandas as pd
import scipy.interpolate as sc
from sostrades_core.execution_engine.execution_engine import ExecutionEngine

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.glossaryenergy import GlossaryEnergy


class CalciumPotassiumTestCase(unittest.TestCase):
    """
    CalciumPotassium prices test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''

        KOH_price = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                              1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                              1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                              1.0, 1.0, 1.0, 1.0]) * 500.0

        # KOH price :
        # https://www.made-in-china.com/price/potassium-hydroxide-price.html

        CaO_price = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                              1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                              1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                              1.0, 1.0, 1.0, 1.0]) * 85.0
        years = np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)
        self.resource_list = [
            'oil_resource', 'natural_gas_resource', 'uranium_resource', 'coal_resource']
        self.ratio_available_resource = pd.DataFrame(
            {GlossaryEnergy.Years: np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)})
        for types in self.resource_list:
            self.ratio_available_resource[types] = np.linspace(
                1, 1, len(self.ratio_available_resource.index))
        self.stream_prices = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.electricity: np.array([0.16, 0.15974117039450046, 0.15948672733558984,
                                                                   0.159236536471781, 0.15899046935409588,
                                                                   0.15874840310033885,
                                                                   0.15875044941298937, 0.15875249600769718,
                                                                   0.15875454288453355,
                                                                   0.15875659004356974, 0.1587586374848771,
                                                                   0.15893789675406477,
                                                                   0.15911934200930778, 0.15930302260662477,
                                                                   0.15948898953954933,
                                                                   0.15967729551117891, 0.15986799501019029,
                                                                   0.16006114439108429,
                                                                   0.16025680195894345, 0.16045502805900876,
                                                                   0.16065588517140537,
                                                                   0.1608594380113745, 0.16106575363539733,
                                                                   0.16127490155362818,
                                                                   0.16148695384909017, 0.1617019853041231,
                                                                   0.1619200735346165,
                                                                   0.16214129913260598, 0.16236574581786147,
                                                                   0.16259350059915213,
                                                                   0.1628246539459331]) * 1000.0,
             GlossaryEnergy.methane: np.array([0.16, 0.15974117039450046, 0.15948672733558984,
                                  0.159236536471781, 0.15899046935409588, 0.15874840310033885,
                                  0.15875044941298937, 0.15875249600769718, 0.15875454288453355,
                                  0.15875659004356974, 0.1587586374848771, 0.15893789675406477,
                                  0.15911934200930778, 0.15930302260662477, 0.15948898953954933,
                                  0.15967729551117891, 0.15986799501019029, 0.16006114439108429,
                                  0.16025680195894345, 0.16045502805900876, 0.16065588517140537,
                                  0.1608594380113745, 0.16106575363539733, 0.16127490155362818,
                                  0.16148695384909017, 0.1617019853041231, 0.1619200735346165,
                                  0.16214129913260598, 0.16236574581786147, 0.16259350059915213,
                                  0.1628246539459331]) * 1000.0,
             })

        self.resources_prices = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.PotassiumResource: KOH_price,
             GlossaryEnergy.CalciumResource: CaO_price,
             })

        years = np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)
        self.stream_co2_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.electricity: 0.0, GlossaryEnergy.methane: 0.2})
        invest = np.array([5093000000.0, 5107300000.0, 5121600000.0, 5135900000.0,
                           5150200000.0, 5164500000.0, 5178800000.0,
                           5221700000.0, 5207400000.0, 5193100000.0,
                           5064600000.0, 4950300000.0, 4836000000.0,
                           4707500000.0, 4793200000.0, 4678900000.0,
                           4550400000.0, 4336100000.0, 4321800000.0,
                           4435750000.0, 4522000000.0, 4608250000.0,
                           4276600000.0, 4379000000.0, 4364700000.0,
                           4169400000.0, 4071800000.0, 4174200000.0,
                           3894500000.0, 3780750000.0, 3567000000.0,
                           ]) * 0.05 / 10000 * 1e-9

        self.invest_level = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.InvestValue: invest})
        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [14.86, 17.22, 20.27,
                     29.01, 34.05, 39.08, 44.69, 50.29]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.CO2Tax: func(years)})
        self.margin = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.MarginValue: np.ones(len(years)) * 110.0})
        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'transport': np.ones(len(years)) * 0.0})
        self.scaling_factor_techno_consumption = 1e3
        self.scaling_factor_techno_production = 1e3
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.ones((len(years), len(years)))))
        demand_ratio_dict[GlossaryEnergy.Years] = years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)
        self.is_stream_demand = True
        self.is_apply_resource_ratio = True

    def tearDown(self):
        pass

    def test_03_CaOKOH_discipline(self):
        self.name = 'Test'
        self.model_name = f'{GlossaryEnergy.direct_air_capture}.{GlossaryEnergy.CalciumPotassiumScrubbing}'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_carbon_capture': self.name,
                   'ns_resource': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.carbon_capture.direct_air_capture.calcium_potassium_scrubbing.calcium_potassium_scrubbing_disc.CalciumPotassiumScrubbingDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearEnd}': GlossaryEnergy.YearEndDefault,
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': self.resources_prices,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)
#         for graph in graph_list:
#             graph.to_plotly().show()
