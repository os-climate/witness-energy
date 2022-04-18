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
from energy_models.core.stream_type.resources_data_disc import get_static_CO2_emissions

from energy_models.models.carbon_capture.flue_gas_capture.piperazine_process.piperazine_process_disc \
    import PiperazineProcessDiscipline
from energy_models.models.carbon_capture.flue_gas_capture.piperazine_process.piperazine_process import PiperazineProcess

from sos_trades_core.execution_engine.execution_engine import ExecutionEngine

from climateeconomics.core.core_resources.all_resources_model import AllResourceModel
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture


class FGPiperazineProcessTestCase(unittest.TestCase):
    """
    Piperazine process prices test class
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
        self.flue_gas_mean = pd.DataFrame(
            {'years': years, 'flue_gas_mean': 0.2})

        self.energy_prices = pd.DataFrame(
            {'years': years, 'electricity': np.ones(len(np.arange(2020, 2051))) * 80.0})

        self.invest_level = pd.DataFrame(
            {'years': years, 'invest': np.array([22000.00, 22000.00, 22000.00, 22000.00,
                                                 22000.00, 22000.00, 22000.00, 22000.00,
                                                 22000.00, 22000.00, 31000.00, 31000.00,
                                                 31000.00, 31000.00, 31000.00, 31000.00,
                                                 31000.00, 31000.00, 31000.00, 31000.00,
                                                 31000.00, 31000.00, 31000.00, 31000.00,
                                                 31000.00, 31000.00, 31000.00, 31000.00,
                                                 31000.00, 31000.00, 31000.00]) * 1e-3})

        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [14.86, 17.22, 20.27,
                     29.01,  34.05,   39.08,  44.69,   50.29]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')
        self.co2_taxes = pd.DataFrame(
            {'years': years, 'CO2_tax': func(years)})

        self.margin = pd.DataFrame(
            {'years': np.arange(2020, 2051), 'margin': np.ones(len(np.arange(2020, 2051))) * 100})

        self.energy_carbon_emissions = pd.DataFrame(
            {'years': years, 'electricity': 0.0})

        transport_cost = 0,

        self.transport = pd.DataFrame(
            {'years': years, 'transport': np.ones(len(years)) * transport_cost})

        self.resources_price = pd.DataFrame({'years': years})
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

    def test_01_compute_piperazine_process_price(self):

        inputs_dict = {'year_start': 2020,
                       'year_end': 2050,
                       'techno_infos_dict': PiperazineProcessDiscipline.techno_infos_dict_default,
                       'invest_level': self.invest_level,
                       'invest_before_ystart': PiperazineProcessDiscipline.invest_before_year_start,
                       'margin':  self.margin,
                       'transport_cost': self.transport,
                       'resources_price': self.resources_price,
                       'energy_CO2_emissions': self.energy_carbon_emissions,
                       'resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       'energy_prices': self.energy_prices,
                       'flue_gas_mean': self.flue_gas_mean,
                       'CO2_taxes': self.co2_taxes,
                       'transport_margin': self.margin,
                       'initial_production': PiperazineProcessDiscipline.initial_capture,
                       'initial_age_distrib': PiperazineProcessDiscipline.initial_age_distribution,
                       'scaling_factor_invest_level': 1e3,
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production,
                       AllResourceModel.RATIO_USABLE_DEMAND: self.ratio_available_resource,
                       'all_streams_demand_ratio': self.all_streams_demand_ratio,
                       'is_stream_demand': self.is_stream_demand,
                       'is_apply_resource_ratio': self.is_apply_resource_ratio,
                       'is_softmax': False,
                       'data_fuel_dict': CarbonCapture.data_energy_dict,
                       }

        pz_model = PiperazineProcess('Flue_gas_capture.PiperazineProcess')
        pz_model.configure_parameters(inputs_dict)
        pz_model.configure_parameters_update(inputs_dict)
        price_details = pz_model.compute_price()

        # Comparison in $/kWH
        plt.figure()
        plt.xlabel('years')

        plt.plot(price_details['years'],
                 price_details['Flue_gas_capture.PiperazineProcess'], label='SoSTrades Total')

        plt.plot(price_details['years'], price_details['transport'],
                 label='SoSTrades Transport')

        plt.plot(price_details['years'], price_details['Flue_gas_capture.PiperazineProcess_factory'],
                 label='SoSTrades Factory')
        plt.legend()
        plt.ylabel('Price ($/kWh)')

    def test_02_compute_piperazine_process_price_prod_consumption(self):

        inputs_dict = {'year_start': 2020,
                       'year_end': 2050,
                       'techno_infos_dict': PiperazineProcessDiscipline.techno_infos_dict_default,
                       'invest_level': self.invest_level,
                       'invest_before_ystart': PiperazineProcessDiscipline.invest_before_year_start,
                       'margin':  self.margin,
                       'transport_cost': self.transport,
                       'resources_price': self.resources_price,
                       'energy_prices': self.energy_prices,
                       'flue_gas_mean': self.flue_gas_mean,
                       'CO2_taxes': self.co2_taxes,
                       'transport_margin': self.margin,
                       'initial_production': PiperazineProcessDiscipline.initial_capture,
                       'initial_age_distrib': PiperazineProcessDiscipline.initial_age_distribution,
                       'energy_CO2_emissions': self.energy_carbon_emissions,
                       'resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       'scaling_factor_invest_level': 1e3,
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production,
                       AllResourceModel.RATIO_USABLE_DEMAND: self.ratio_available_resource,
                       'all_streams_demand_ratio': self.all_streams_demand_ratio,
                       'is_stream_demand': self.is_stream_demand,
                       'is_apply_resource_ratio': self.is_apply_resource_ratio,
                       'is_softmax': False,
                       'data_fuel_dict': CarbonCapture.data_energy_dict,
                       }

        pz_model = PiperazineProcess('Flue_gas_capture.PiperazineProcess')
        pz_model.configure_parameters(inputs_dict)
        pz_model.configure_parameters_update(inputs_dict)
        price_details = pz_model.compute_price()
        pz_model.compute_consumption_and_production()

    def test_03_piperazine_process_discipline(self):

        self.name = 'Test'
        self.model_name = 'Flue_gas_capture.PiperazineProcess'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name,
                   'ns_energy': self.name,
                   'ns_flue_gas': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_carbon_capture': self.name,
                   'ns_resource': self.name}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.carbon_capture.flue_gas_capture.piperazine_process' \
                   '.piperazine_process_disc.PiperazineProcessDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.flue_gas_mean': self.flue_gas_mean,
                       f'{self.name}.energy_CO2_emissions': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.transport_margin': self.margin,
                       f'{self.name}.transport_cost': self.transport,
                       f'{self.name}.resources_price': self.resources_price,
                       f'{self.name}.{self.model_name}.margin': self.margin}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)
        # for graph in graph_list:
        #     graph.to_plotly().show()
