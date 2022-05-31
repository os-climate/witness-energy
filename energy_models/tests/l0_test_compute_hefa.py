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

from energy_models.models.hydrotreated_oil_fuel.hefa_deoxygenation.hefa_deoxygenation_disc import HefaDeoxygenationDiscipline
from energy_models.models.hydrotreated_oil_fuel.hefa_deoxygenation.hefa_deoxygenation import HefaDeoxygenation
from energy_models.models.hydrotreated_oil_fuel.hefa_decarboxylation.hefa_decarboxylation_disc import HefaDecarboxylationDiscipline
from energy_models.models.hydrotreated_oil_fuel.hefa_decarboxylation.hefa_decarboxylation import HefaDecarboxylation
from sos_trades_core.execution_engine.execution_engine import ExecutionEngine
from energy_models.core.stream_type.resources_models.natural_oil import NaturalOil
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import GaseousHydrogen
from energy_models.core.stream_type.resources_data_disc import get_static_CO2_emissions
from climateeconomics.core.core_resources.resource_mix.resource_mix import ResourceMixModel
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.energy_models.hydrotreated_oil_fuel import HydrotreatedOilFuel


class HEFAPriceTestCase(unittest.TestCase):
    """
    HEFA prices test class
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

        # electricity_price = np.array([0.09, 0.08974117039450046, 0.08948672733558984,
        #                               0.089236536471781, 0.08899046935409588, 0.08874840310033885,
        #                               0.08875044941298937, 0.08875249600769718, 0.08875454288453355,
        #                               0.08875659004356974, 0.0887586374848771, 0.08893789675406477,
        #                               0.08911934200930778, 0.08930302260662477, 0.08948898953954933,
        #                               0.08967729551117891, 0.08986799501019029, 0.09006114439108429,
        #                               0.09025680195894345, 0.09045502805900876, 0.09065588517140537,
        #                               0.0908594380113745, 0.09106575363539733, 0.09127490155362818,
        #                               0.09148695384909017, 0.0917019853041231, 0.0919200735346165,
        #                               0.09214129913260598, 0.09236574581786147, 0.09259350059915213,
        #                               0.0928246539459331]) * 1000

        self.energy_prices = pd.DataFrame({'years': years,
                                           'electricity': np.ones(len(years)) * 0.135 * 1000,
                                           f'{GaseousHydrogen.name}': np.ones(len(years)) * 0.1266023955250543 * 1000,
                                           })

        self.energy_carbon_emissions = pd.DataFrame(
            {'years': years, 'electricity': 0.2, f'{GaseousHydrogen.name}': 0.0})
        default_resources_price_df = pd.DataFrame({'years': years,
                                                   # 'water':  years * [2],
                                                   # 'uranium fuel': 1390000,
                                                   # 'CO2': np.array([0.04, 0.041, 0.042, 0.043, 0.044, 0.045, 0.0464, 0.047799999999999995, 0.049199999999999994, 0.0506, 0.052, 0.0542, 0.0564, 0.0586, 0.0608, 0.063, 0.0652, 0.0674, 0.0696, 0.0718, 0.074, 0.0784, 0.0828, 0.0872, 0.0916, 0.096, 0.1006, 0.1052, 0.1098, 0.1144, 0.119]) * 1000,
                                                   # 'biomass_dry': 68.12,
                                                   # 'wet_biomass': 56,
                                                   # 'wood': years * [120],
                                                   # from
                                                   # https://biotechnologyforbiofuels.biomedcentral.com/articles/10.1186/s13068-017-0945-3/tables/3
                                                   f'{NaturalOil.name}': np.ones(len(years)) * 1.054 * 1000,
                                                   })
        self.resources_prices = default_resources_price_df

        self.invest_level = pd.DataFrame(
            {'years': years, 'invest': np.ones(len(years)) * 347.5 / 1000})
        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [14.86, 17.22, 20.27,
                     29.01,  34.05,   39.08,  44.69,   50.29]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {'years': years, 'CO2_tax': func(years)})
        self.margin = pd.DataFrame(
            {'years': years, 'margin': np.ones(len(years)) * 110.0})
        # From future of hydrogen
        self.transport = pd.DataFrame(
            {'years': years, 'transport': np.ones(len(years)) * 100})
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

    def test_01_compute_hefa_price_prod_consumption(self):

        inputs_dict = {'year_start': 2020,
                       'year_end': 2050,
                       'techno_infos_dict': HefaDecarboxylationDiscipline.techno_infos_dict_default,
                       'energy_prices': self.energy_prices,
                       'resources_price': self.resources_prices,
                       'invest_level': self.invest_level,
                       'invest_before_ystart': HefaDecarboxylationDiscipline.invest_before_year_start,
                       'CO2_taxes': self.co2_taxes,
                       'margin':  self.margin,
                       'transport_cost': self.transport,
                       'transport_margin': self.margin,
                       'initial_production': HefaDecarboxylationDiscipline.initial_production,
                       'initial_age_distrib': HefaDecarboxylationDiscipline.initial_age_distribution,
                       'energy_CO2_emissions': self.energy_carbon_emissions,
                       'resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       'scaling_factor_invest_level': 1e3,
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production,
                       ResourceMixModel.RATIO_USABLE_DEMAND: self.ratio_available_resource,
                       'all_streams_demand_ratio': self.all_streams_demand_ratio,
                       'is_stream_demand': self.is_stream_demand,
                       'is_apply_resource_ratio': self.is_apply_resource_ratio,
                       'smooth_type': 'smooth_max',
                       'data_fuel_dict': HydrotreatedOilFuel.data_energy_dict,
                       }

        hefa_model = HefaDecarboxylation('Hefa')
        hefa_model.configure_parameters(inputs_dict)
        hefa_model.configure_parameters_update(inputs_dict)
        price_details = hefa_model.compute_price()
        hefa_model.compute_consumption_and_production()

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

        inputs_dict = {f'{self.name}.year_end': 2050,
                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.resources_price': self.resources_prices,
                       f'{self.name}.energy_CO2_emissions': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.transport_margin': self.margin,
                       f'{self.name}.transport_cost': self.transport,
                       f'{self.name}.{self.model_name}.margin':  self.margin
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)
        # for graph in graph_list:
        # graph.to_plotly().show()

    def test_03_compute_hefa_green_price_prod_consumption(self):

        inputs_dict = {'year_start': 2020,
                       'year_end': 2050,
                       'techno_infos_dict': HefaDeoxygenationDiscipline.techno_infos_dict_default,
                       'energy_prices': self.energy_prices,
                       'resources_price': self.resources_prices,
                       'invest_level': self.invest_level,
                       'invest_before_ystart': HefaDeoxygenationDiscipline.invest_before_year_start,
                       'CO2_taxes': self.co2_taxes,
                       'margin':  self.margin,
                       'transport_cost': self.transport,
                       'transport_margin': self.margin,
                       'initial_production': HefaDeoxygenationDiscipline.initial_production,
                       'initial_age_distrib': HefaDeoxygenationDiscipline.initial_age_distribution,
                       'energy_CO2_emissions': self.energy_carbon_emissions,
                       'resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       'scaling_factor_invest_level': 1e3,
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production,
                       ResourceMixModel.RATIO_USABLE_DEMAND: self.ratio_available_resource,
                       'all_streams_demand_ratio': self.all_streams_demand_ratio,
                       'is_stream_demand': self.is_stream_demand,
                       'is_apply_resource_ratio': self.is_apply_resource_ratio,
                       'smooth_type': 'smooth_max',
                       'data_fuel_dict': HydrotreatedOilFuel.data_energy_dict,
                       }

        hefa_model = HefaDeoxygenation('HefaGreen')
        hefa_model.configure_parameters(inputs_dict)
        hefa_model.configure_parameters_update(inputs_dict)
        price_details = hefa_model.compute_price()
        hefa_model.compute_consumption_and_production()

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

        inputs_dict = {f'{self.name}.year_end': 2050,
                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.resources_price': self.resources_prices,
                       f'{self.name}.energy_CO2_emissions': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.transport_margin': self.margin,
                       f'{self.name}.transport_cost': self.transport,
                       f'{self.name}.{self.model_name}.margin':  self.margin
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
