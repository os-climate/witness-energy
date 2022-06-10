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

import numpy as np
import pandas as pd
import re
import scipy.interpolate as sc
from os.path import join, dirname
from climateeconomics.core.core_resources.resource_mix.resource_mix import ResourceMixModel
from energy_models.models.electricity.nuclear.nuclear_disc import NuclearDiscipline
from energy_models.models.electricity.nuclear.nuclear import Nuclear

from sos_trades_core.execution_engine.execution_engine import ExecutionEngine
from energy_models.core.stream_type.resources_data_disc import get_static_CO2_emissions
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary


class NuclearTestCase(unittest.TestCase):
    """
    Nuclear prices test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        years = np.arange(2020, 2051)

        self.resources_price = pd.DataFrame(
            columns=['years', ResourceGlossary.Water['name'], ResourceGlossary.Uranium['name']])
        self.resources_price['years'] = years
        self.resources_price[ResourceGlossary.Water['name']] = 2.0
        self.resources_price[ResourceGlossary.Uranium['name']] = 1390.0e3

        self.invest_level = pd.DataFrame({'years': years})
        self.invest_level['invest'] = 10.

        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [14.86, 17.22, 20.27,
                     29.01,  34.05,   39.08,  44.69,   50.29]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')
        self.co2_taxes = pd.DataFrame(
            {'years': years, 'CO2_tax': func(years)})

        self.margin = pd.DataFrame(
            {'years': np.arange(2020, 2051), 'margin': np.ones(len(np.arange(2020, 2051))) * 110})

        self.transport = pd.DataFrame(
            {'years': years, 'transport': np.zeros(len(years))})

        self.energy_prices = pd.DataFrame({'years': years})

        biblio_data_path = join(
            dirname(__file__), 'output_values_check', 'biblio_data.csv')
        self.biblio_data = pd.read_csv(biblio_data_path)
        self.biblio_data = self.biblio_data.loc[self.biblio_data['sos_name']
                                                == 'electricity.Nuclear']
        self.scaling_factor_techno_consumption = 1e3
        self.scaling_factor_techno_production = 1e3
        self.resource_list = [
            'oil_resource', 'natural_gas_resource', 'uranium_resource', 'coal_resource', 'copper_resource']
        self.ratio_available_resource = pd.DataFrame(
            {'years': np.arange(2020, 2050 + 1)})
        for types in self.resource_list:
            self.ratio_available_resource[types] = np.linspace(
                0.5, 0.5, len(self.ratio_available_resource.index))

        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.ones((len(years), len(years)))))
        demand_ratio_dict['years'] = years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)
        self.is_stream_demand = True
        self.is_apply_resource_ratio = True

    def tearDown(self):
        pass

    def test_01_compute_nuclear_price(self):

        inputs_dict = {'year_start': 2020,
                       'year_end': 2050,
                       'techno_infos_dict': NuclearDiscipline.techno_infos_dict_default,
                       'invest_level': self.invest_level,
                       'invest_before_ystart': NuclearDiscipline.invest_before_year_start,
                       'margin':  self.margin,
                       'transport_cost': self.transport,
                       'resources_price': self.resources_price,
                       'energy_prices': self.energy_prices,
                       'CO2_taxes': self.co2_taxes,
                       'transport_margin': self.margin,
                       'initial_production': NuclearDiscipline.initial_production,
                       'initial_age_distrib': NuclearDiscipline.initial_age_distribution,
                       'energy_CO2_emissions': pd.DataFrame(),
                       'resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       'scaling_factor_invest_level': 1e3,
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production,
                       ResourceMixModel.RATIO_USABLE_DEMAND: self.ratio_available_resource,
                       'all_streams_demand_ratio': self.all_streams_demand_ratio,
                       'is_stream_demand': self.is_stream_demand,
                       'is_apply_resource_ratio': self.is_apply_resource_ratio,
                       'smooth_type': 'smooth_max',
                       'data_fuel_dict': Electricity.data_energy_dict,
                       }

        nuclear_model = Nuclear(NuclearDiscipline.techno_name)
        nuclear_model.configure_parameters(inputs_dict)
        nuclear_model.configure_parameters_update(inputs_dict)
        price_details = nuclear_model.compute_price()

    def test_02_compute_nuclear_price_prod_consumption(self):

        inputs_dict = {'year_start': 2020,
                       'year_end': 2050,
                       'techno_infos_dict': NuclearDiscipline.techno_infos_dict_default,
                       'invest_level': self.invest_level,
                       'invest_before_ystart': NuclearDiscipline.invest_before_year_start,
                       'margin':  self.margin,
                       'transport_cost': self.transport,
                       'resources_price': self.resources_price,
                       'energy_prices': self.energy_prices,
                       'CO2_taxes': self.co2_taxes,
                       'transport_margin': self.margin,
                       'initial_production': NuclearDiscipline.initial_production,
                       'initial_age_distrib': NuclearDiscipline.initial_age_distribution,
                       'energy_CO2_emissions': pd.DataFrame(),
                       'resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       'scaling_factor_invest_level': 1e3,
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production,
                       ResourceMixModel.RATIO_USABLE_DEMAND: self.ratio_available_resource,
                       'all_streams_demand_ratio': self.all_streams_demand_ratio,
                       'is_stream_demand': self.is_stream_demand,
                       'is_apply_resource_ratio': self.is_apply_resource_ratio,
                       'smooth_type': 'smooth_max',
                       'data_fuel_dict': Electricity.data_energy_dict,
                       }

        nuclear_model = Nuclear(NuclearDiscipline.techno_name)
        nuclear_model.configure_parameters(inputs_dict)
        nuclear_model.configure_parameters_update(inputs_dict)
        price_details = nuclear_model.compute_price()
        nuclear_model.compute_consumption_and_production()
        nuclear_model.check_outputs_dict(self.biblio_data)

    def test_04_compute_nuclear_ratio_prod_consumption(self):

        inputs_dict = {'year_start': 2020,
                       'year_end': 2050,
                       'techno_infos_dict': NuclearDiscipline.techno_infos_dict_default,
                       'invest_level': self.invest_level,
                       'invest_before_ystart': NuclearDiscipline.invest_before_year_start,
                       'margin':  self.margin,
                       'transport_cost': self.transport,
                       'resources_price': self.resources_price,
                       'energy_prices': self.energy_prices,
                       'CO2_taxes': self.co2_taxes,
                       'transport_margin': self.margin,
                       'initial_production': NuclearDiscipline.initial_production,
                       'initial_age_distrib': NuclearDiscipline.initial_age_distribution,
                       'energy_CO2_emissions': pd.DataFrame(),
                       'resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       'scaling_factor_invest_level': 1e3,
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production,
                       ResourceMixModel.RATIO_USABLE_DEMAND: self.ratio_available_resource,
                       'all_streams_demand_ratio': self.all_streams_demand_ratio,
                       'is_stream_demand': self.is_stream_demand,
                       'is_apply_resource_ratio': self.is_apply_resource_ratio,
                       'smooth_type': 'smooth_max',
                       'data_fuel_dict': Electricity.data_energy_dict,
                       }

        nuclear_model = Nuclear(NuclearDiscipline.techno_name)
        nuclear_model.configure_parameters(inputs_dict)
        nuclear_model.configure_parameters_update(inputs_dict)
        price_details = nuclear_model.compute_price()
        nuclear_model.compute_consumption_and_production()
        consumption_without_ratio = nuclear_model.consumption['uranium_resource (Mt)'].values * \
            self.ratio_available_resource['uranium_resource'].values
        nuclear_model.select_ratios()
        nuclear_model.apply_ratios_on_consumption_and_production(True)
        # self.assertListEqual(list(nuclear_model.consumption['uranium_resource'].values),list(consumption_without_ratio))

    def test_03_nuclear_discipline(self):

        self.name = 'Test'
        self.model_name = 'Nuclear'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name,
                   'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_resource': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.electricity.nuclear.nuclear_disc.NuclearDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.year_end': 2050,
                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': pd.DataFrame(),
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.transport_margin': self.margin,
                       f'{self.name}.transport_cost': self.transport,
                       f'{self.name}.resources_price': self.resources_price,
                       ResourceMixModel.RATIO_USABLE_DEMAND: self.ratio_available_resource,
                       f'{self.name}.{self.model_name}.margin':  self.margin}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)
        # for graph in graph_list:
        #     graph.to_plotly().show()
