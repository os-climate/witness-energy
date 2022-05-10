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
import scipy.interpolate as sc

from energy_models.models.gaseous_hydrogen.electrolysis.pem.electrolysis_pem import ElectrolysisPEM
from energy_models.models.gaseous_hydrogen.electrolysis.pem.electrolysis_pem_disc import ElectrolysisPEMDiscipline
from energy_models.models.gaseous_hydrogen.electrolysis.soec.electrolysis_soec import ElectrolysisSOEC
from energy_models.models.gaseous_hydrogen.electrolysis.soec.electrolysis_soec_disc import ElectrolysisSOECDiscipline
from energy_models.models.gaseous_hydrogen.electrolysis.awe.electrolysis_awe import ElectrolysisAWE
from energy_models.models.gaseous_hydrogen.electrolysis.awe.electrolysis_awe_disc import ElectrolysisAWEDiscipline
from sos_trades_core.execution_engine.execution_engine import ExecutionEngine
from energy_models.core.stream_type.resources_data_disc import get_static_CO2_emissions

from climateeconomics.core.core_resources.resource_mix.resource_mix import ResourceMixModel
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import GaseousHydrogen
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary


class ElectrolysisPriceTestCase(unittest.TestCase):
    """
    Electrolysis prices test class
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
        self.energy_prices = pd.DataFrame(
            {'years': years, 'electricity': 60.0})
        self.energy_co2_emissions = pd.DataFrame(
            {'years': years, 'electricity': 0.0})
        # price of 1 kg of wood
        self.resources_prices = pd.DataFrame({'years': years, ResourceGlossary.Water['name']: 0.0
                                              })

        self.invest_level = pd.DataFrame(
            {'years': years, 'invest': len(years) * [0.3]})
        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [14.86, 17.22, 20.27,
                     29.01,  34.05,   39.08,  44.69,   50.29]

        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {'years': years, 'CO2_tax': func(years)})
        self.margin = pd.DataFrame(
            {'years': years, 'margin': np.ones(len(years)) * 110.0})

        self.transport = pd.DataFrame(
            {'years': years, 'transport': np.ones(len(years)) * 500.0})
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

    def test_01_compute_pemel(self):

        inputs_dict = {'year_start': 2020,
                       'year_end': 2050,
                       'techno_infos_dict': ElectrolysisPEMDiscipline.techno_infos_dict_default,
                       'energy_prices': self.energy_prices,
                       'resources_price': self.resources_prices,
                       'invest_level': self.invest_level,
                       'invest_before_ystart': ElectrolysisPEMDiscipline.invest_before_year_start,
                       'CO2_taxes': self.co2_taxes,
                       'margin':  self.margin,
                       'transport_cost': self.transport,
                       'transport_margin': self.margin,
                       'initial_production': ElectrolysisPEMDiscipline.initial_production,
                       'initial_age_distrib': ElectrolysisPEMDiscipline.initial_age_distribution,
                       'energy_CO2_emissions': self.energy_co2_emissions,
                       'resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       'scaling_factor_invest_level': 1e3,
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production,
                       ResourceMixModel.RATIO_USABLE_DEMAND: self.ratio_available_resource,
                       'all_streams_demand_ratio': self.all_streams_demand_ratio,
                       'is_stream_demand': self.is_stream_demand,
                       'is_apply_resource_ratio': self.is_apply_resource_ratio,
                       'is_softmax': False,
                       'data_fuel_dict': GaseousHydrogen.data_energy_dict,
                       }

        pem = ElectrolysisPEM('PEM')
        pem.configure_parameters(inputs_dict)
        pem.configure_parameters_update(inputs_dict)
        price_details = pem.compute_price()
        pem.compute_consumption_and_production()

    def test_02_pem_discipline(self):

        self.name = 'Test'
        self.model_name = 'PEM'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_hydrogen': f'{self.name}',
                   'ns_resource': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.gaseous_hydrogen.electrolysis.pem.electrolysis_pem_disc.ElectrolysisPEMDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.year_end': 2050,
                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': self.energy_co2_emissions,
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.transport_margin': self.margin,
                       f'{self.name}.transport_cost': self.transport,
                       f'{self.name}.{self.model_name}.margin':  self.margin,
                       f'{self.name}.resources_price': self.resources_prices,
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)
#         for graph in graph_list:
#             graph.to_plotly().show()

    def test_03_compute_soec(self):

        inputs_dict = {'year_start': 2020,
                       'year_end': 2050,
                       'techno_infos_dict': ElectrolysisSOECDiscipline.techno_infos_dict_default,
                       'energy_prices': self.energy_prices,
                       'resources_price': self.resources_prices,
                       'invest_level': self.invest_level,
                       'invest_before_ystart': ElectrolysisSOECDiscipline.invest_before_year_start,
                       'CO2_taxes': self.co2_taxes,
                       'margin':  self.margin,
                       'transport_cost': self.transport,
                       'transport_margin': self.margin,
                       'initial_production': ElectrolysisSOECDiscipline.initial_production,
                       'initial_age_distrib': ElectrolysisSOECDiscipline.initial_age_distribution,
                       'energy_CO2_emissions': self.energy_co2_emissions,
                       'resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       'scaling_factor_invest_level': 1e3,
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production,
                       ResourceMixModel.RATIO_USABLE_DEMAND: self.ratio_available_resource,
                       'all_streams_demand_ratio': self.all_streams_demand_ratio,
                       'is_stream_demand': self.is_stream_demand,
                       'is_apply_resource_ratio': self.is_apply_resource_ratio,
                       'is_softmax': False,
                       'data_fuel_dict': GaseousHydrogen.data_energy_dict,
                       }

        SOEC = ElectrolysisSOEC('SOEC')
        SOEC.configure_parameters(inputs_dict)
        SOEC.configure_parameters_update(inputs_dict)
        price_details = SOEC.compute_price()
        SOEC.compute_consumption_and_production()

    def test_04_soec_discipline(self):

        self.name = 'Test'
        self.model_name = 'SOEC'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_hydrogen': f'{self.name}',
                   'ns_resource': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.gaseous_hydrogen.electrolysis.soec.electrolysis_soec_disc.ElectrolysisSOECDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.year_end': 2050,
                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': self.energy_co2_emissions,
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.transport_margin': self.margin,
                       f'{self.name}.transport_cost': self.transport,
                       f'{self.name}.{self.model_name}.margin':  self.margin,
                       f'{self.name}.resources_price': self.resources_prices,
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)
#         for graph in graph_list:
#             graph.to_plotly().show()

    def test_05_compute_awe(self):

        inputs_dict = {'year_start': 2020,
                       'year_end': 2050,
                       'techno_infos_dict': ElectrolysisAWEDiscipline.techno_infos_dict_default,
                       'energy_prices': self.energy_prices,
                       'resources_price': self.resources_prices,
                       'invest_level': self.invest_level,
                       'invest_before_ystart': ElectrolysisAWEDiscipline.invest_before_year_start,
                       'CO2_taxes': self.co2_taxes,
                       'margin':  self.margin,
                       'transport_cost': self.transport,
                       'transport_margin': self.margin,
                       'initial_production': ElectrolysisAWEDiscipline.initial_production,
                       'initial_age_distrib': ElectrolysisAWEDiscipline.initial_age_distribution,
                       'energy_CO2_emissions': self.energy_co2_emissions,
                       'resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       'scaling_factor_invest_level': 1e3,
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production,
                       ResourceMixModel.RATIO_USABLE_DEMAND: self.ratio_available_resource,
                       'all_streams_demand_ratio': self.all_streams_demand_ratio,
                       'is_stream_demand': self.is_stream_demand,
                       'is_apply_resource_ratio': self.is_apply_resource_ratio,
                       'is_softmax': False,
                       'data_fuel_dict': GaseousHydrogen.data_energy_dict,
                       }

        AWE = ElectrolysisAWE('AWE')
        AWE.configure_parameters(inputs_dict)
        AWE.configure_parameters_update(inputs_dict)
        price_details = AWE.compute_price()
        AWE.compute_consumption_and_production()

    def test_06_awe_discipline(self):

        self.name = 'Test'
        self.model_name = 'AWE'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_hydrogen': f'{self.name}',
                   'ns_resource': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.gaseous_hydrogen.electrolysis.awe.electrolysis_awe_disc.ElectrolysisAWEDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.year_end': 2050,
                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': self.energy_co2_emissions,
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.transport_margin': self.margin,
                       f'{self.name}.transport_cost': self.transport,
                       f'{self.name}.{self.model_name}.margin':  self.margin,
                       f'{self.name}.resources_price': self.resources_prices
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)
#         for graph in graph_list:
#             graph.to_plotly().show()
