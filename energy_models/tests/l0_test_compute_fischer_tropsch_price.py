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

        self.stream_prices = pd.DataFrame({GlossaryEnergy.Years: years, GlossaryEnergy.electricity: np.ones(len(years)) * 20,
                                           GlossaryEnergy.syngas: 34, GlossaryEnergy.carbon_capture: 12.
                                           })
        self.syngas_detailed_prices = pd.DataFrame({GlossaryEnergy.SMR: np.ones(len(years)) * 34,
                                                    
                                                    GlossaryEnergy.CoElectrolysis: np.ones(len(years)) * 60,
                                                    GlossaryEnergy.BiomassGasification: np.ones(len(years)) * 50
                                                    })
        self.syngas_ratio_technos = {GlossaryEnergy.SMR: 0.33,
                                     GlossaryEnergy.CoElectrolysis: 1.0,
                                     GlossaryEnergy.BiomassGasification: 2.0
                                     }
        self.stream_co2_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.electricity: 0.2, GlossaryEnergy.syngas: 0.2, GlossaryEnergy.carbon_capture: 12.})

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

        # CO2 Taxe Data
        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [14.86, 17.22, 20.27,
                     29.01, 34.05, 39.08, 44.69, 50.29]

        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.CO2Tax: func(years)})

        self.margin = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.MarginValue: np.ones(len(years)) * 110.0})
        # From future of hydrogen
        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'transport': np.ones(len(years)) * 100})
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
