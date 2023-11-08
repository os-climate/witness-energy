'''
Copyright 2023 Capgemini

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
import pandas as pd
import numpy as np
import scipy.interpolate as sc
from os.path import join, dirname

from climateeconomics.glossarycore import GlossaryCore
from energy_models.models.heat.high.electric_boiler_high_heat.electric_boiler_high_heat import ElectricBoilerHighHeat
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from energy_models.core.stream_type.resources_data_disc import get_static_CO2_emissions
from climateeconomics.core.core_resources.resource_mix.resource_mix import ResourceMixModel
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from energy_models.models.heat.high.electric_boiler_high_heat.electric_boiler_high_heat_disc import ElectricBoilerHighHeatDiscipline


class ElectricBoilerTestCase(unittest.TestCase):
    """
    Electric Boiler test class
    """
    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        years = np.arange(2020, 2051)
        self.resource_list = [
            'oil_resource', 'natural_gas_resource', 'uranium_resource', 'coal_resource']
        from climateeconomics.glossarycore import GlossaryCore
        self.ratio_available_resource = pd.DataFrame(
            {GlossaryCore.Years: np.arange(2020, 2050 + 1)})
        for types in self.resource_list:
            self.ratio_available_resource[types] = np.linspace(
                1, 1, len(self.ratio_available_resource.index))

        self.energy_prices = pd.DataFrame({GlossaryCore.Years: years,
                                           'electricity': np.ones(len(years)) * 181.0,  #$/MWh
                                                                                        #https://tradingeconomics.com/france/electricity-price
                                           })

        self.energy_carbon_emissions = pd.DataFrame({GlossaryCore.Years: years, 'electricity': 0.0, 'water': 0.0})
        self.resources_price = pd.DataFrame({GlossaryCore.Years: years, 'water_resource': 2.0})
        self.resources_CO2_emissions = pd.DataFrame({GlossaryCore.Years: years, 'water': 0.0})
        self.invest_level = pd.DataFrame(
            {GlossaryCore.Years: years, GlossaryCore.InvestValue: np.array([4435750000.0, 4522000000.0, 4608250000.0,
                                                 4694500000.0, 4780750000.0, 4867000000.0,
                                                 4969400000.0, 5071800000.0, 5174200000.0,
                                                 5276600000.0, 5379000000.0, 5364700000.0,
                                                 5350400000.0, 5336100000.0, 5321800000.0,
                                                 5307500000.0, 5293200000.0, 5278900000.0,
                                                 5264600000.0, 5250300000.0, 5236000000.0,
                                                 5221700000.0, 5207400000.0, 5193100000.0,
                                                 5178800000.0, 5164500000.0, 5150200000.0,
                                                 5135900000.0, 5121600000.0, 5107300000.0,
                                                 5093000000.0]) / 5.0e9})

        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [14.86, 17.22, 20.27,
                     29.01, 34.05, 39.08, 44.69,   50.29]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {GlossaryCore.Years: years, GlossaryCore.CO2Tax: func(years)})
        self.margin = pd.DataFrame(
            {GlossaryCore.Years: years, GlossaryCore.MarginValue: np.ones(len(years)) * 110.0})
        # From future of hydrogen
        self.transport = pd.DataFrame(
            {GlossaryCore.Years: years, 'transport': np.ones(len(years)) * 0.0})
        self.scaling_factor_techno_consumption = 1e3
        self.scaling_factor_techno_production = 1e3
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.ones((len(years), len(years)))))
        demand_ratio_dict[GlossaryCore.Years] = years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)
        self.is_stream_demand = True
        self.is_apply_resource_ratio = True

        biblio_data_path = join(
            dirname(__file__), 'output_values_check', 'biblio_data.csv')
        self.biblio_data = pd.read_csv(biblio_data_path)
        self.biblio_data = self.biblio_data.loc[self.biblio_data['sos_name']
                                                == 'electricity.ElectricBoiler']

    def tearDown(self):
        pass

    def test_01_compute_electric_boiler_price_prod_consumption(self):

        inputs_dict = {GlossaryCore.YearStart: 2020,
                       GlossaryCore.YearEnd: 2050,
                       'techno_infos_dict': ElectricBoilerHighHeatDiscipline.techno_infos_dict_default,
                       GlossaryCore.EnergyPricesValue: self.energy_prices,
                       GlossaryCore.ResourcesPriceValue: self.resources_price,
                       GlossaryCore.InvestLevelValue: self.invest_level,
                       GlossaryCore.InvestmentBeforeYearStartValue: ElectricBoilerHighHeatDiscipline.invest_before_year_start,
                       GlossaryCore.CO2TaxesValue: self.co2_taxes,
                       GlossaryCore.MarginValue:  self.margin,
                       GlossaryCore.TransportCostValue: self.transport,
                       GlossaryCore.TransportMarginValue: self.margin,
                       'initial_production': ElectricBoilerHighHeatDiscipline.initial_production,
                       'initial_age_distrib': ElectricBoilerHighHeatDiscipline.initial_age_distribution,
                       GlossaryCore.EnergyCO2EmissionsValue: self.energy_carbon_emissions,
                       GlossaryCore.RessourcesCO2EmissionsValue: get_static_CO2_emissions(np.arange(2020, 2051)),
                       'scaling_factor_invest_level': 1e3,
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production,
                       ResourceMixModel.RATIO_USABLE_DEMAND: self.ratio_available_resource,
                       GlossaryCore.AllStreamsDemandRatioValue: self.all_streams_demand_ratio,
                       'is_stream_demand': self.is_stream_demand,
                       'is_apply_resource_ratio': self.is_apply_resource_ratio,
                       'smooth_type': 'smooth_max',
                       'data_fuel_dict': hightemperatureheat.data_energy_dict
                       }

        ng_model = ElectricBoilerHighHeat('Electric Boiler')
        ng_model.configure_parameters(inputs_dict)
        ng_model.configure_parameters_update(inputs_dict)
        price_details = ng_model.compute_price()
        ng_model.compute_consumption_and_production()

        #print('price_details', price_details)

    def test_02_electric_boiler_discipline(self):

        self.name = 'Test'
        self.model_name = 'ElectricBoiler'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_resource': self.name,
                   'ns_heat_high': f'{self.name}'
                   }
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.heat.high.electric_boiler_high_heat.electric_boiler_high_heat_disc.ElectricBoilerHighHeatDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryCore.YearEnd}': 2050,
                       f'{self.name}.{GlossaryCore.EnergyPricesValue}': self.energy_prices,
                       #f'{self.name}.{GlossaryCore.ResourcesPriceValue}': self.resources_price,
                       f'{self.name}.{GlossaryCore.EnergyCO2EmissionsValue}': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryCore.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{GlossaryCore.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryCore.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryCore.TransportCostValue}': self.transport,
                       f'{self.name}.{self.model_name}.{GlossaryCore.MarginValue}':  self.margin,
                       # f'{self.name}.{self.model_name}.flux_input_dict':  {'land_rate': 5000.0,
                       #                                  'land_rate_unit': '$/Gha',
                       #                                  }
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)
        # for graph in graph_list:
        #     graph.to_plotly().show()


if __name__ == "__main__":
    unittest.main()
