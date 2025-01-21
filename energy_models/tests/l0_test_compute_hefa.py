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
from sostrades_core.execution_engine.execution_engine import ExecutionEngine

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import (
    GaseousHydrogen,
)
from energy_models.core.stream_type.resources_models.natural_oil import NaturalOil
from energy_models.glossaryenergy import GlossaryEnergy


class HEFAPriceTestCase(unittest.TestCase):
    """
    HEFA prices test class
    """

    def setUp(self):
        
        years = np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)
        self.resource_list = [
            'oil_resource', 'natural_gas_resource', 'uranium_resource', 'coal_resource']
        self.ratio_available_resource = pd.DataFrame(
            {GlossaryEnergy.Years: np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)})
        for types in self.resource_list:
            self.ratio_available_resource[types] = np.linspace(
                1, 1, len(self.ratio_available_resource.index))

        self.stream_prices = pd.DataFrame({GlossaryEnergy.Years: years,
                                           GlossaryEnergy.electricity: 135,
                                           GaseousHydrogen.name: 120.,
                                           })

        self.stream_co2_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.electricity: 0.2, GaseousHydrogen.name: 0.0})
        default_resources_price_df = pd.DataFrame({GlossaryEnergy.Years: years,
                                                   # 'water':  years * [2],
                                                   # 'uranium fuel': 1390000,
                                                   # GlossaryEnergy.CO2: np.array([0.04, 0.041, 0.042, 0.043, 0.044, 0.045, 0.0464, 0.047799999999999995, 0.049199999999999994, 0.0506, 0.052, 0.0542, 0.0564, 0.0586, 0.0608, 0.063, 0.0652, 0.0674, 0.0696, 0.0718, 0.074, 0.0784, 0.0828, 0.0872, 0.0916, 0.096, 0.1006, 0.1052, 0.1098, 0.1144, 0.119]) * 1000,
                                                   # GlossaryEnergy.biomass_dry: 68.12,
                                                   # GlossaryEnergy.wet_biomass: 56,
                                                   # 'wood': years * [120],
                                                   # from
                                                   # https://biotechnologyforbiofuels.biomedcentral.com/articles/10.1186/s13068-017-0945-3/tables/3
                                                   NaturalOil.name: 1.054 * 1000,
                                                   })
        self.resources_prices = default_resources_price_df

        self.invest_level = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.InvestValue: 347.5 / 1000})
        

        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.CO2Tax: np.linspace(15., 40., len(years))})
        self.margin = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.MarginValue: 110.0})
        # From future of hydrogen
        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'transport': 100})
        self.scaling_factor_techno_consumption = 1e3
        self.scaling_factor_techno_production = 1e3
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.ones((len(years), len(years)))))
        demand_ratio_dict[GlossaryEnergy.Years] = years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)
        self.is_stream_demand = True
        self.is_apply_resource_ratio = True

    def test_02_hefa_discipline(self):
        self.name = 'Test'
        self.model_name = 'Hefa'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_hydrotreated_oil_fuel': f'{self.name}',
                   'ns_resource': self.name
                   }
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.hydrotreated_oil_fuel.hefa_decarboxylation.hefa_decarboxylation_disc.HefaDecarboxylationDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearEnd}': GlossaryEnergy.YearEndDefault,
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': self.resources_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)
        # for graph in graph_list:
        # graph.to_plotly().show()

    def test_04_hefa_green_discipline(self):
        self.name = 'Test'
        self.model_name = 'HefaGreen'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_hydrotreated_oil_fuel': f'{self.name}',
                   'ns_resource': self.name
                   }
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.hydrotreated_oil_fuel.hefa_deoxygenation.hefa_deoxygenation_disc.HefaDeoxygenationDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearEnd}': GlossaryEnergy.YearEndDefault,
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': self.resources_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)
        # for graph in graph_list:
        # graph.to_plotly().show()


if __name__ == "__main__":
    unittest.main()
