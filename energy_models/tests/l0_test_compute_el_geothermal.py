'''
Copyright 2022 Airbus SAS

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
from os.path import join, dirname

import scipy.interpolate as sc
import matplotlib.pyplot as plt

from climateeconomics.glossarycore import GlossaryCore
from energy_models.models.electricity.geothermal.geothermal import Geothermal
from energy_models.models.electricity.geothermal.geothermal_disc import GeothermalDiscipline
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from energy_models.core.stream_type.resources_data_disc import get_static_CO2_emissions

from climateeconomics.core.core_resources.resource_mix.resource_mix import ResourceMixModel
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.energy_models.electricity import Electricity


class GeothermalTestCase(unittest.TestCase):
    """
    Geothermal prices test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        years = np.arange(2020, 2051)
        self.resource_list = [
            'oil_resource', 'natural_gas_resource', 'uranium_resource', 'coal_resource']
        self.ratio_available_resource = pd.DataFrame(
            {GlossaryCore.Years: np.arange(2020, 2050 + 1)})
        for types in self.resource_list:
            self.ratio_available_resource[types] = np.linspace(
                1, 1, len(self.ratio_available_resource.index))

        self.invest_level = pd.DataFrame({GlossaryCore.Years: years})
        self.invest_level[GlossaryCore.InvestValue] = 5.0 * \
            1.10 ** (self.invest_level[GlossaryCore.Years] - 2020)

        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [14.86, 17.22, 20.27,
                     29.01,  34.05,   39.08,  44.69,   50.29]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')
        self.co2_taxes = pd.DataFrame(
            {GlossaryCore.Years: years, GlossaryCore.CO2Tax: func(years)})

        self.margin = pd.DataFrame(
            {GlossaryCore.Years: np.arange(2020, 2051), GlossaryCore.MarginValue: np.ones(len(np.arange(2020, 2051))) * 110})

        self.transport = pd.DataFrame(
            {GlossaryCore.Years: years, 'transport': np.zeros(len(years))})

        self.resources_price = pd.DataFrame({GlossaryCore.Years: years})
        self.energy_prices = pd.DataFrame({GlossaryCore.Years: years})

        biblio_data_path = join(
            dirname(__file__), 'output_values_check', 'biblio_data.csv')
        self.biblio_data = pd.read_csv(biblio_data_path)
        self.biblio_data = self.biblio_data.loc[self.biblio_data['sos_name']
                                                == 'electricity.Geothermal']
        self.scaling_factor_techno_consumption = 1e3
        self.scaling_factor_techno_production = 1e3
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.ones((len(years), len(years)))))
        demand_ratio_dict[GlossaryCore.Years] = years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)
        self.is_stream_demand = True
        self.is_apply_resource_ratio = True

    def tearDown(self):
        pass

    def test_01_compute_geothermal_price(self):

        inputs_dict = {GlossaryCore.YearStart: 2020,
                       GlossaryCore.YearEnd: 2050,
                       'techno_infos_dict': GeothermalDiscipline.techno_infos_dict_default,
                       GlossaryCore.InvestLevelValue: self.invest_level,
                       GlossaryCore.InvestmentBeforeYearStartValue: GeothermalDiscipline.invest_before_year_start,
                       GlossaryCore.MarginValue:  self.margin,
                       GlossaryCore.TransportCostValue: self.transport,
                       GlossaryCore.ResourcesPriceValue: self.resources_price,
                       GlossaryCore.EnergyPricesValue: self.energy_prices,
                       GlossaryCore.CO2TaxesValue: self.co2_taxes,
                       'initial_production': GeothermalDiscipline.initial_production,
                       'initial_age_distrib': GeothermalDiscipline.initial_age_distribution,
                       GlossaryCore.EnergyCO2EmissionsValue: pd.DataFrame(),
                       GlossaryCore.RessourcesCO2EmissionsValue: get_static_CO2_emissions(np.arange(2020, 2051)),
                       GlossaryCore.TransportMarginValue: self.margin,
                       'scaling_factor_invest_level': 1e3,
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production,
                       ResourceMixModel.RATIO_USABLE_DEMAND: self.ratio_available_resource,
                       GlossaryCore.AllStreamsDemandRatioValue: self.all_streams_demand_ratio,
                       'is_stream_demand': self.is_stream_demand,
                       'is_apply_resource_ratio': self.is_apply_resource_ratio,
                       'smooth_type': 'smooth_max',
                       'data_fuel_dict': Electricity.data_energy_dict,
                       }

        geothermal_model = Geothermal('Geothermal')
        geothermal_model.configure_parameters(inputs_dict)
        geothermal_model.configure_parameters_update(inputs_dict)
        price_details = geothermal_model.compute_price()

        # Comparison in $/kWH
        plt.figure()
        plt.xlabel(GlossaryCore.Years)

        plt.plot(price_details[GlossaryCore.Years],
                 price_details['Geothermal'], label='SoSTrades Total')

        plt.plot(price_details[GlossaryCore.Years], price_details['transport'],
                 label='SoSTrades Transport')

        plt.plot(price_details[GlossaryCore.Years], price_details['Geothermal_factory'],
                 label='SoSTrades Factory')
        plt.legend()
        plt.ylabel('Price ($/kWh)')

    def test_02_compute_geothermal_price_prod_consumption(self):

        inputs_dict = {GlossaryCore.YearStart: 2020,
                       GlossaryCore.YearEnd: 2050,
                       'techno_infos_dict': GeothermalDiscipline.techno_infos_dict_default,
                       GlossaryCore.InvestLevelValue: self.invest_level,
                       GlossaryCore.InvestmentBeforeYearStartValue: GeothermalDiscipline.invest_before_year_start,
                       GlossaryCore.MarginValue:  self.margin,
                       GlossaryCore.TransportCostValue: self.transport,
                       GlossaryCore.ResourcesPriceValue: self.resources_price,
                       GlossaryCore.EnergyPricesValue: self.energy_prices,
                       GlossaryCore.CO2TaxesValue: self.co2_taxes,
                       GlossaryCore.TransportMarginValue: self.margin,
                       'initial_production': GeothermalDiscipline.initial_production,
                       'initial_age_distrib': GeothermalDiscipline.initial_age_distribution,
                       GlossaryCore.EnergyCO2EmissionsValue: pd.DataFrame(),
                       GlossaryCore.RessourcesCO2EmissionsValue: get_static_CO2_emissions(np.arange(2020, 2051)),
                       'scaling_factor_invest_level': 1e3,
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production,
                       ResourceMixModel.RATIO_USABLE_DEMAND: self.ratio_available_resource,
                       GlossaryCore.AllStreamsDemandRatioValue: self.all_streams_demand_ratio,
                       'is_stream_demand': self.is_stream_demand,
                       'is_apply_resource_ratio': self.is_apply_resource_ratio,
                       'smooth_type': 'smooth_max',
                       'data_fuel_dict': Electricity.data_energy_dict,
                       }

        geothermal_model = Geothermal('Geothermal')
        geothermal_model.configure_parameters(inputs_dict)
        geothermal_model.configure_parameters_update(inputs_dict)
        price_details = geothermal_model.compute_price()
        geothermal_model.compute_consumption_and_production()
        geothermal_model.check_outputs_dict(self.biblio_data)
    
    def test_04_compute_geothermal_power(self):

        inputs_dict = {GlossaryCore.YearStart: 2020,
                       GlossaryCore.YearEnd: 2050,
                       'techno_infos_dict': GeothermalDiscipline.techno_infos_dict_default,
                       GlossaryCore.InvestLevelValue: self.invest_level,
                       GlossaryCore.InvestmentBeforeYearStartValue: GeothermalDiscipline.invest_before_year_start,
                       GlossaryCore.MarginValue:  self.margin,
                       GlossaryCore.TransportCostValue: self.transport,
                       GlossaryCore.ResourcesPriceValue: self.resources_price,
                       GlossaryCore.EnergyPricesValue: self.energy_prices,
                       GlossaryCore.CO2TaxesValue: self.co2_taxes,
                       GlossaryCore.TransportMarginValue: self.margin,
                       'initial_production': GeothermalDiscipline.initial_production,
                       'initial_age_distrib': GeothermalDiscipline.initial_age_distribution,
                       GlossaryCore.EnergyCO2EmissionsValue: pd.DataFrame(),
                       GlossaryCore.RessourcesCO2EmissionsValue: get_static_CO2_emissions(np.arange(2020, 2051)),
                       'scaling_factor_invest_level': 1e3,
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production,
                       ResourceMixModel.RATIO_USABLE_DEMAND: self.ratio_available_resource,
                       GlossaryCore.AllStreamsDemandRatioValue: self.all_streams_demand_ratio,
                       'is_stream_demand': self.is_stream_demand,
                       'is_apply_resource_ratio': self.is_apply_resource_ratio,
                       'smooth_type': 'smooth_max',
                       'data_fuel_dict': Electricity.data_energy_dict,
                       }

        geothermal_model = Geothermal('Geothermal')
        geothermal_model.configure_parameters(inputs_dict)
        geothermal_model.configure_parameters_update(inputs_dict)
        price_details = geothermal_model.compute_price()
        geothermal_model.compute_consumption_and_production()
        geothermal_model.compute_consumption_and_power_production()

        print(geothermal_model.power_production)

        print(geothermal_model.power_production * geothermal_model.techno_infos_dict['full_load_hours'] / 1000)

        print(geothermal_model.production[f'electricity ({geothermal_model.product_energy_unit})'])

        self.assertLessEqual(list(geothermal_model.production[f'electricity ({geothermal_model.product_energy_unit})'].values),
                            list(geothermal_model.power_production['total_installed_power'] * geothermal_model.techno_infos_dict['full_load_hours'] / 1000 * 1.001) )
        self.assertGreaterEqual(list(geothermal_model.production[f'electricity ({geothermal_model.product_energy_unit})'].values),
                            list(geothermal_model.power_production['total_installed_power'] * geothermal_model.techno_infos_dict['full_load_hours'] / 1000 * 0.999) )

    def test_03_geothermal_discipline(self):

        self.name = 'Test'
        self.model_name = 'Geothermal'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name,
                   'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name, 'ns_resource': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.electricity.geothermal.geothermal_disc.GeothermalDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryCore.YearEnd}': 2050,
                       f'{self.name}.{GlossaryCore.EnergyPricesValue}': self.energy_prices,
                       f'{self.name}.{GlossaryCore.EnergyCO2EmissionsValue}': pd.DataFrame(),
                       f'{self.name}.{self.model_name}.{GlossaryCore.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{GlossaryCore.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryCore.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryCore.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryCore.ResourcesPriceValue}': self.resources_price,
                       f'{self.name}.{self.model_name}.{GlossaryCore.MarginValue}':  self.margin}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)
#         for graph in graph_list:
#             graph.to_plotly().show()
# if __name__ == "__main__":
#     unittest.main()
