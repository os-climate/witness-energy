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

from energy_models.models.carbon_storage.pure_carbon_solid_storage.pure_carbon_solid_storage import PureCarbonSS
from energy_models.models.carbon_storage.pure_carbon_solid_storage.pure_carbon_solid_storage_disc import PureCarbonSolidStorageDiscipline

from sos_trades_core.execution_engine.execution_engine import ExecutionEngine
from energy_models.core.stream_type.resources_data_disc import get_static_CO2_emissions
from climateeconomics.core.core_resources.all_resources_model import AllResourceModel
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.carbon_models.carbon_storage import CarbonStorage


class PureCarbonSSPriceTestCase(unittest.TestCase):
    """
    Pure Carbon Solid Storage prices test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        years = np.arange(2020, 2051)
        self.resource_list = [
            'oil_resource', 'natural_gas_resource', 'uranium_resource', 'coal_resource']
        self.ratio_available_resource = pd.DataFrame(
            {'years': np.arange(2020, 2050 + 1)})
        for types in self.resource_list:
            self.ratio_available_resource[types] = np.linspace(
                1, 1, len(self.ratio_available_resource.index))
        self.energy_carbon_emissions = pd.DataFrame(
            {'years': years, 'CO2': 0})
        self.invest_level_2 = pd.DataFrame(
            {'years': years, 'invest': np.ones(len(years)) * 0.0325})

        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        # co2_taxes = [0.01486, 0.01722, 0.02027,
        #             0.02901,  0.03405,   0.03908,  0.04469,   0.05029]
        co2_taxes = [0, 0, 0,
                     0,  0,   0,  0,   0]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {'years': years, 'CO2_tax': func(years)})
        self.margin = pd.DataFrame(
            {'years': years, 'margin': np.ones(len(years)) * 100.0})

        transport_cost = 0

        self.transport = pd.DataFrame(
            {'years': years, 'transport': np.ones(len(years)) * transport_cost})
        self.resources_price = pd.DataFrame({'years': years})

        self.carbon_quantity_to_be_stored = pd.DataFrame(
            {'years': range(2020, 2051), 'carbon_storage': 10.})

        self.scaling_factor_invest_level = 1e3
        self.scaling_factor_techno_consumption = 1e3
        self.scaling_factor_techno_production = 1e3
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.ones((len(years), len(years)))))
        demand_ratio_dict['years'] = years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)
        self.is_stream_demand = True
        self.is_apply_resource_ratio = True

    def tearDown(self):
        pass

    def test_01_compute_pure_carbon_solid_storage_price(self):

        inputs_dict = {'year_start': 2020,
                       'year_end': 2050,
                       'techno_infos_dict': PureCarbonSolidStorageDiscipline.techno_infos_dict_default,
                       'invest_level': self.invest_level_2,
                       'invest_before_ystart': PureCarbonSolidStorageDiscipline.invest_before_year_start,
                       'CO2_taxes': self.co2_taxes,
                       'margin':  self.margin,
                       'transport_cost': self.transport,
                       'transport_margin': self.margin,
                       'resources_price': self.resources_price,
                       'energy_prices': pd.DataFrame({'years': np.arange(2020, 2051)}),
                       'initial_production': PureCarbonSolidStorageDiscipline.initial_storage,
                       'initial_age_distrib': PureCarbonSolidStorageDiscipline.initial_age_distribution,
                       'energy_CO2_emissions': self.energy_carbon_emissions,
                       'resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       'scaling_factor_invest_level': self.scaling_factor_invest_level,
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production,
                       AllResourceModel.RATIO_USABLE_DEMAND: self.ratio_available_resource,
                       'all_streams_demand_ratio': self.all_streams_demand_ratio,
                       'is_stream_demand': self.is_stream_demand,
                       'is_apply_resource_ratio': self.is_apply_resource_ratio,
                       'data_fuel_dict': CarbonStorage.data_energy_dict,
                       }

        pure_carbon_solid_storage_model = PureCarbonSS(
            'PureCarbonSolidStorage')
        pure_carbon_solid_storage_model.configure_parameters(inputs_dict)
        pure_carbon_solid_storage_model.configure_parameters_update(
            inputs_dict)
        price_details = pure_carbon_solid_storage_model.compute_price()

        # Comparison in $/kgCO2
        # plt.figure()
        # plt.xlabel('years')

        # plt.plot(price_details['years'],
        # price_details['Simplified_Carbon_Storage'], label='SoSTrades Total')

        # # plt.plot(price_details['years'], price_details['transport'],
        # #          label='SoSTrades Transport')

        # plt.legend()
        # plt.ylabel('Price ($/kgCO2)')
        # plt.show()

    def test_02_compute_pure_carbon_solid_storage_price_prod_consumption(self):

        inputs_dict = {'year_start': 2020,
                       'year_end': 2050,
                       'techno_infos_dict': PureCarbonSolidStorageDiscipline.techno_infos_dict_default,
                       'energy_prices': pd.DataFrame({'years': np.arange(2020, 2051)}),
                       'invest_level': self.invest_level_2,
                       'invest_before_ystart': PureCarbonSolidStorageDiscipline.invest_before_year_start,
                       'CO2_taxes': self.co2_taxes,
                       'margin':  self.margin,
                       'transport_cost': self.transport,
                       'resources_price': self.resources_price,
                       'transport_margin': self.margin,
                       'initial_production': PureCarbonSolidStorageDiscipline.initial_storage,
                       'initial_age_distrib': PureCarbonSolidStorageDiscipline.initial_age_distribution,
                       'energy_CO2_emissions': self.energy_carbon_emissions,
                       'resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       'scaling_factor_invest_level': self.scaling_factor_invest_level,
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production,
                       AllResourceModel.RATIO_USABLE_DEMAND: self.ratio_available_resource,
                       'all_streams_demand_ratio': self.all_streams_demand_ratio,
                       'is_stream_demand': self.is_stream_demand,
                       'is_apply_resource_ratio': self.is_apply_resource_ratio,
                       'data_fuel_dict': CarbonStorage.data_energy_dict,
                       }

        pure_carbon_solid_storage_model = PureCarbonSS(
            'PureCarbonSolidStorage')
        pure_carbon_solid_storage_model.configure_parameters(inputs_dict)
        pure_carbon_solid_storage_model.configure_parameters_update(
            inputs_dict)
        price_details = pure_carbon_solid_storage_model.compute_price()

        pure_carbon_solid_storage_model.compute_consumption_and_production()

    def test_03_pure_carbon_solid_storage_discipline(self):

        self.name = 'Test'
        self.model_name = 'PureCarbonSolidStorage'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name,
                   'ns_energy': self.name,
                   'ns_energy_study': self.name,
                   'ns_electricity': self.name,
                   'ns_carbon_storage': self.name,
                   'ns_carb': self.name,
                   'ns_functions': self.name,
                   'ns_resource': self.name
                   }
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.carbon_storage.pure_carbon_solid_storage.pure_carbon_solid_storage_disc.PureCarbonSolidStorageDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        import traceback
        try:
            self.ee.configure()
        except:
            traceback.print_exc()
        self.ee.display_treeview_nodes()

        carbon = [0.0, 0.8651783141413611, 1.7845680696378616, 2.70525797662332, 3.6258387241643946, 4.545445236338747, 5.463461182612219, 6.3793970326745875, 7.293107469201024, 8.200999856054061, 9.100399893483209, 9.98929061188071, 10.866138061016379, 11.729770619165382, 12.57929297278459, 13.414023343767314,
                  14.233446783229535, 15.037179855774266, 15.824946381059533, 16.596567148338323, 17.351944905009482, 18.091049892900365, 18.81390807653675, 19.52059149020655, 20.21121027018144, 20.88590603982225, 20.629668075861527, 20.353652183454564, 20.060976034308823, 19.75326948534016, 19.431629541578427]
        carbon_to_be_stored = pd.DataFrame(
            {'years': np.arange(2020, 2051), 'carbon_storage': np.array(carbon) / 2})

        inputs_dict = {f'{self.name}.energy_prices': pd.DataFrame({'years': np.arange(2020, 2051)}),
                       f'{self.name}.energy_CO2_emissions': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level_2,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.transport_margin': self.margin,
                       f'{self.name}.transport_cost': self.transport,
                       f'{self.name}.resources_price': self.resources_price,
                       f'{self.name}.{self.model_name}.margin':  self.margin,
                       f'{self.name}.carbon_quantity_to_be_stored':  carbon_to_be_stored}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)
#         for graph in graph_list:
#             graph.to_plotly().show()
