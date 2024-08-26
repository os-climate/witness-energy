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
from climateeconomics.core.core_resources.resource_mix.resource_mix import (
    ResourceMixModel,
)
from sostrades_core.execution_engine.execution_engine import ExecutionEngine

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.energy_models.gasoline import Gasoline
from energy_models.core.stream_type.energy_models.heating_oil import HeatingOil
from energy_models.core.stream_type.energy_models.kerosene import Kerosene
from energy_models.core.stream_type.energy_models.lpg import LiquefiedPetroleumGas
from energy_models.core.stream_type.energy_models.ultralowsulfurdiesel import (
    UltraLowSulfurDiesel,
)
from energy_models.glossaryenergy import GlossaryEnergy


class FTPriceTestCase(unittest.TestCase):
    """
    FischerTropsch prices test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''

        years = np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)

        self.resource_list = [
            'oil_resource', 'natural_gas_resource', 'uranium_resource', 'coal_resource', 'copper_resource',
            'platinum_resource']
        self.ratio_available_resource = pd.DataFrame(
            {GlossaryEnergy.Years: np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)})
        for types in self.resource_list:
            self.ratio_available_resource[types] = np.linspace(
                1, 1, len(self.ratio_available_resource.index))

        self.stream_prices = pd.DataFrame({GlossaryEnergy.Years: years, GlossaryEnergy.electricity: 20,
                                           GlossaryEnergy.syngas: 34, GlossaryEnergy.carbon_capture: 12.
                                           })
        self.syngas_detailed_prices = pd.DataFrame({GlossaryEnergy.Years: years,
                                                    GlossaryEnergy.SMR: 34,
                                                    GlossaryEnergy.CoElectrolysis: 60,
                                                    GlossaryEnergy.BiomassGasification: 50
                                                    })
        self.syngas_ratio_technos = {GlossaryEnergy.Years: years,
                                     GlossaryEnergy.SMR: 0.33,
                                     GlossaryEnergy.CoElectrolysis: 1.0,
                                     GlossaryEnergy.BiomassGasification: 2.0
                                     }
        self.stream_co2_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.electricity: 0.2, GlossaryEnergy.syngas: 0.2, GlossaryEnergy.carbon_capture: 12.})

        self.invest_level = pd.DataFrame({GlossaryEnergy.Years: years,
                                          GlossaryEnergy.InvestValue: np.linspace(4., 5.0, len(years))})

        # CO2 Taxe Data
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
        self.data_fuel = {Kerosene.name: Kerosene.data_energy_dict,
                          Gasoline.name: Gasoline.data_energy_dict,
                          LiquefiedPetroleumGas.name: LiquefiedPetroleumGas.data_energy_dict,
                          HeatingOil.name: HeatingOil.data_energy_dict,
                          UltraLowSulfurDiesel.name: UltraLowSulfurDiesel.data_energy_dict,
                          'calorific_value': 12.0,
                          'high_calorific_value': 13.0,
                          'density': 800,
                          'molar_mass': 170.0,
                          'molar_mass_unit': 'g/mol',
                          }

    def tearDown(self):
        pass

    def test_02_FT_discipline(self):

        self.name = 'Test'
        self.model_name = GlossaryEnergy.FischerTropsch
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_liquid_fuel': self.name,
                   'ns_syngas': self.name,
                   'ns_resource': self.name,
                   }
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.liquid_fuel.fischer_tropsch.fischer_tropsch_disc.FischerTropschDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        years = np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)
        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearEnd}': GlossaryEnergy.YearEndDefault,
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.syngas_ratio': np.ones(len(years)),
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)

        # graph_list[-1].to_plotly().show()

    def test_03_FT_with_ratio_available_cc(self):

        self.name = 'Test'
        self.model_name = GlossaryEnergy.FischerTropsch
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name,
                   'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_liquid_fuel': self.name,
                   'ns_syngas': self.name,
                   'ns_resource': self.name,
                   }
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.liquid_fuel.fischer_tropsch.fischer_tropsch_disc.FischerTropschDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        years = np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearEnd}': GlossaryEnergy.YearEndDefault,

                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.syngas_ratio': np.ones(len(years)),
                       f'{self.name}.{ResourceMixModel.RATIO_USABLE_DEMAND}': self.ratio_available_resource,
                       f'{self.name}.is_apply_resource_ratio': True}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        techno_production_wo_ratio = self.ee.dm.get_value(
            f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoProductionValue}')
        techno_consumption_wo_ratio = self.ee.dm.get_value(
            f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionValue}')

        self.ee2 = ExecutionEngine(self.name)
        self.ee2.ns_manager.add_ns_def(ns_dict)
        builder = self.ee2.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee2.factory.set_builders_to_coupling_builder(builder)

        self.ee2.configure()

        self.ee2.load_study_from_input_dict(inputs_dict)

        self.ee2.execute()
        ratio = self.ee.dm.get_disciplines_with_name(f'{self.name}.{self.model_name}')[
            0].mdo_discipline_wrapp.wrapper.techno_model.applied_ratio['applied_ratio'].values
        ratio2 = self.ee2.dm.get_disciplines_with_name(f'{self.name}.{self.model_name}')[
            0].mdo_discipline_wrapp.wrapper.techno_model.applied_ratio['applied_ratio'].values
        techno_production_with_ratio = self.ee2.dm.get_value(
            f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoProductionValue}')

        for column in techno_production_with_ratio.columns:
            if column != GlossaryEnergy.Years:
                for i in range(len(techno_production_with_ratio[column].values)):
                    self.assertAlmostEqual(techno_production_with_ratio[column].values[i],
                                           techno_production_wo_ratio[column].values[i] * ratio2[i] / ratio[i],
                                           delta=1.0e-8)

        techno_consumption_with_ratio = self.ee2.dm.get_value(
            f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionValue}')
        for column in techno_consumption_with_ratio.columns:
            if column != GlossaryEnergy.Years:
                for i in range(len(techno_consumption_with_ratio[column].values)):
                    self.assertAlmostEqual(techno_consumption_with_ratio[column].values[i],
                                           techno_consumption_wo_ratio[column].values[i] * ratio2[i] / ratio[i],
                                           delta=1.0e-8)


if '__main__' == __name__:
    cls = FTPriceTestCase()
    cls.setUp()
    cls.test_03_FT_with_ratio_available_cc()
