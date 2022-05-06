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
import scipy.interpolate as sc

from sos_trades_core.execution_engine.execution_engine import ExecutionEngine
from energy_models.models.methane.methanation.methanation_disc import MethanationDiscipline
from energy_models.models.methane.methanation.methanation import Methanation
from energy_models.core.stream_type.resources_data_disc import get_static_CO2_emissions

from climateeconomics.core.core_resources.resource_mix.resource_mix import ResourceMixModel
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary


class MethanationPriceTestCase(unittest.TestCase):
    """
    Methanation prices test class
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
        self.energy_prices = pd.DataFrame({'years': years, 'hydrogen.gaseous_hydrogen': np.array([0.1266023955250543, 0.12472966837635774, 0.12308937523217356, 0.12196584543238155,
                                                                                                  0.12101159171871603, 0.12018900859836591, 0.1192884942915236, 0.11865333029969044,
                                                                                                  0.11827242819796199, 0.11804896544898459, 0.11796960162047375, 0.11791110278481422,
                                                                                                  0.11784598237652186, 0.11776392989648421, 0.11836724143081659, 0.11883282673049182,
                                                                                                  0.11917648165844891, 0.1197345556855176, 0.12008291652658049, 0.1204305172545244,
                                                                                                  0.12102683407269707, 0.12186763004213008, 0.12326379102943016, 0.12412292194034467,
                                                                                                  0.12433514237290824, 0.12511526161029957, 0.12590456744159823, 0.1267030200703957,
                                                                                                  0.12691667296790637, 0.12714334679576733, 0.12738215136005188]) * 1000
                                           })

        self.energy_carbon_emissions = pd.DataFrame(
            {'years': years, 'hydrogen.gaseous_hydrogen': 0.0})
        # Use the same inest as SMR techno
        self.invest_level = pd.DataFrame({'years': years,
                                          'invest': np.array([4435750000.0, 4522000000.0, 4608250000.0,
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
                     29.01,  34.05,   39.08,  44.69,   50.29]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {'years': years, 'CO2_tax': func(years)})
        self.margin = pd.DataFrame(
            {'years': years, 'margin': np.ones(len(years)) * 110.0})
        self.transport = pd.DataFrame(
            {'years': years, 'transport': np.ones(len(years)) * 200})

        self.resources_price = pd.DataFrame(
            columns=['years', ResourceGlossary.CO2['name'], ResourceGlossary.Water['name']])
        self.resources_price['years'] = years
        self.resources_price[ResourceGlossary.CO2['name']] = np.array([0.04, 0.041, 0.042, 0.043, 0.044, 0.045, 0.0464, 0.047799999999999995, 0.049199999999999994, 0.0506, 0.052, 0.0542,
                                                                       0.0564, 0.0586, 0.0608, 0.063, 0.0652, 0.0674, 0.0696, 0.0718, 0.074, 0.0784, 0.0828, 0.0872, 0.0916, 0.096, 0.1006, 0.1052, 0.1098, 0.1144, 0.119]) * 1000.0
        self.resources_price[ResourceGlossary.Water['name']] = 1.4
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

    def test_01_compute_emethane_price(self):

        inputs_dict = {'year_start': 2020,
                       'year_end': 2050,
                       'techno_infos_dict': MethanationDiscipline.techno_infos_dict_default,
                       'energy_prices': self.energy_prices,
                       'invest_level': self.invest_level,
                       'CO2_taxes': self.co2_taxes,
                       'margin':  self.margin,
                       'transport_cost': self.transport,
                       'transport_margin': self.margin,
                       'initial_production': MethanationDiscipline.initial_production,
                       'initial_age_distrib': MethanationDiscipline.initial_age_distribution,
                       'invest_before_ystart': MethanationDiscipline.invest_before_year_start,
                       'resources_price': self.resources_price,
                       'energy_CO2_emissions': self.energy_carbon_emissions,
                       'resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       'scaling_factor_invest_level': 1e3,
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production,
                       ResourceMixModel.RATIO_USABLE_DEMAND: self.ratio_available_resource,
                       'all_streams_demand_ratio': self.all_streams_demand_ratio,
                       'is_stream_demand': self.is_stream_demand,
                       'is_apply_resource_ratio': self.is_apply_resource_ratio,
                       'is_softmax': False,
                       'data_fuel_dict': Methane.data_energy_dict,
                       }

        methane = Methanation('Methanation')
        methane.configure_parameters(inputs_dict)
        methane.configure_parameters_update(inputs_dict)
        price_details = methane.compute_price()

    def test_02_emethane_discipline(self):

        self.name = 'Test'
        self.model_name = 'PtG'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_methane': self.name,
                   'ns_resource': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.methane.methanation.methanation_disc.MethanationDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.year_end': 2050,
                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.transport_margin': self.margin,
                       f'{self.name}.transport_cost': self.transport,
                       f'{self.name}.{self.model_name}.margin':  self.margin,
                       f'{self.name}.resources_price': self.resources_price}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)
#         for graph in graph_list:
#             graph.to_plotly().show()
