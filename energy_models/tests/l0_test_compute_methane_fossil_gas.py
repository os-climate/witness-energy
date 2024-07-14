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


class UpgradingBiogasPriceTestCase(unittest.TestCase):
    """
    Fossil Gas prices test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        years = np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)
        self.resource_list = [
            'oil_resource', 'natural_gas_resource', 'uranium_resource', 'coal_resource']
        self.ratio_available_resource = pd.DataFrame(
            {GlossaryEnergy.Years: np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)})
        for types in self.resource_list:
            self.ratio_available_resource[types] = np.linspace(
                1, 1, len(self.ratio_available_resource.index))
        self.stream_prices = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.electricity: np.array([0.09, 0.08974117039450046, 0.08948672733558984,
                                                                   0.089236536471781, 0.08899046935409588,
                                                                   0.08874840310033885,
                                                                   0.08875044941298937, 0.08875249600769718,
                                                                   0.08875454288453355,
                                                                   0.08875659004356974, 0.0887586374848771,
                                                                   0.08893789675406477,
                                                                   0.08911934200930778, 0.08930302260662477,
                                                                   0.08948898953954933,
                                                                   0.08967729551117891, 0.08986799501019029,
                                                                   0.09006114439108429,
                                                                   0.09025680195894345, 0.09045502805900876,
                                                                   0.09065588517140537,
                                                                   0.0908594380113745, 0.09106575363539733,
                                                                   0.09127490155362818,
                                                                   0.09148695384909017, 0.0917019853041231,
                                                                   0.0919200735346165,
                                                                   0.09214129913260598, 0.09236574581786147,
                                                                   0.09259350059915213,
                                                                   0.0928246539459331]) * 1000.0
             })

        self.stream_co2_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.electricity: 0.0})
        # Use the same inest as SMR techno
        self.invest_level = pd.DataFrame({GlossaryEnergy.Years: years,
                                          GlossaryEnergy.InvestValue: np.array(
                                              [4435750000.0, 4522000000.0, 4608250000.0,
                                               4694500000.0, 4780750000.0, 4867000000.0,
                                               4969400000.0, 5071800000.0, 5174200000.0,
                                               5276600000.0, 5379000000.0, 5364700000.0,
                                               5350400000.0, 5336100000.0, 5321800000.0,
                                               5307500000.0, 5293200000.0, 5278900000.0,
                                               5264600000.0, 5250300000.0, 5236000000.0,
                                               5221700000.0, 5207400000.0, 5193100000.0,
                                               5178800000.0, 5164500000.0, 5150200000.0,
                                               5135900000.0, 5121600000.0, 5107300000.0,
                                               5093000000.0]) * 1.0e-9})
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
            {GlossaryEnergy.Years: years, 'transport': np.ones(len(years)) * 200.0})
        self.resources_price = pd.DataFrame(
            columns=[GlossaryEnergy.Years, 'CO2', 'water', 'natural_gas_resource'])
        self.resources_price[GlossaryEnergy.Years] = years
        self.resources_price['CO2'] = np.array(
            [0.04, 0.041, 0.042, 0.043, 0.044, 0.045, 0.0464, 0.047799999999999995, 0.049199999999999994, 0.0506, 0.052,
             0.0542,
             0.0564, 0.0586, 0.0608, 0.063, 0.0652, 0.0674, 0.0696, 0.0718, 0.074, 0.0784, 0.0828, 0.0872, 0.0916,
             0.096, 0.1006, 0.1052, 0.1098, 0.1144, 0.119]) * 1000.0
        self.resources_price['water'] = 1.4
        self.resources_price['natural_gas_resource'] = 10.0
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

    def test_02_fossil_gas_discipline(self):
        self.name = 'Test'
        self.model_name = 'fossil_gas'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_methane': self.name,
                   'ns_resource': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.methane.fossil_gas.fossil_gas_disc.FossilGasDiscipline'
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
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': self.resources_price}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)
#         for graph in graph_list:
#             graph.to_plotly().show()
