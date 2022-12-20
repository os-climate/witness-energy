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
from os.path import join, dirname

from energy_models.models.liquid_fuel.fischer_tropsch.fischer_tropsch_disc import FischerTropschDiscipline
from energy_models.models.liquid_fuel.fischer_tropsch.fischer_tropsch import FischerTropsch
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from energy_models.core.stream_type.resources_data_disc import get_static_prices,\
    get_static_CO2_emissions

from climateeconomics.core.core_resources.resource_mix.resource_mix import ResourceMixModel
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.energy_models.kerosene import Kerosene
from energy_models.core.stream_type.energy_models.gasoline import Gasoline
from energy_models.core.stream_type.energy_models.lpg import LiquefiedPetroleumGas
from energy_models.core.stream_type.energy_models.heating_oil import HeatingOil
from energy_models.core.stream_type.energy_models.ultralowsulfurdiesel import UltraLowSulfurDiesel
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import GaseousHydrogen
from energy_models.core.stream_type.energy_models.syngas import Syngas


class FTPriceTestCase(unittest.TestCase):
    """
    FischerTropsch prices test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        elec_price = np.array([0.09, 0.08974117039450046, 0.08948672733558984,
                               0.089236536471781, 0.08899046935409588, 0.08874840310033885,
                               0.08875044941298937, 0.08875249600769718, 0.08875454288453355,
                               0.08875659004356974, 0.0887586374848771, 0.08893789675406477,
                               0.08911934200930778, 0.08930302260662477, 0.08948898953954933,
                               0.08967729551117891, 0.08986799501019029, 0.09006114439108429,
                               0.09025680195894345, 0.09045502805900876, 0.09065588517140537,
                               0.0908594380113745, 0.09106575363539733, 0.09127490155362818,
                               0.09148695384909017, 0.0917019853041231, 0.0919200735346165,
                               0.09214129913260598, 0.09236574581786147, 0.09259350059915213,
                               0.0928246539459331]
                              ) * 1000.0

        years = np.arange(2020, 2051)

        self.resource_list = [
            'oil_resource', 'natural_gas_resource', 'uranium_resource', 'coal_resource', 'copper_resource', 'platinum_resource']
        self.ratio_available_resource = pd.DataFrame(
            {'years': np.arange(2020, 2050 + 1)})
        for types in self.resource_list:
            self.ratio_available_resource[types] = np.linspace(
                1, 1, len(self.ratio_available_resource.index))

        self.energy_prices = pd.DataFrame({'years': years, 'electricity': np.ones(len(years)) * 20,
                                           'syngas': 34
                                           })
        self.syngas_detailed_prices = pd.DataFrame({'SMR': np.ones(len(years)) * 34,
                                                    # price to be updated for
                                                    # CO2
                                                    'CoElectrolysis': np.ones(len(years)) * 60,
                                                    'BiomassGasification': np.ones(len(years)) * 50
                                                    })
        self.syngas_ratio_technos = {'SMR': 0.33,
                                     'CoElectrolysis': 1.0,
                                     'BiomassGasification': 2.0
                                     }
        self.energy_carbon_emissions = pd.DataFrame(
            {'years': years, 'electricity': 0.2, 'syngas': 0.2})

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

        # CO2 Taxe Data
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

    def test_01_compute_FT_price(self):

        years = np.arange(2020, 2051)
        inputs_dict = {'year_start': 2020,
                       'year_end': 2050,
                       'techno_infos_dict': FischerTropschDiscipline.techno_infos_dict_default,
                       'invest_level': self.invest_level,
                       'energy_prices': self.energy_prices,
                       'energy_CO2_emissions': self.energy_carbon_emissions,
                       'CO2_taxes': self.co2_taxes,
                       'margin': self.margin,
                       'transport_cost': self.transport,
                       'transport_margin': self.margin,
                       'initial_production': FischerTropschDiscipline.initial_production,
                       'initial_age_distrib': FischerTropschDiscipline.initial_age_distribution,
                       'invest_before_ystart': FischerTropschDiscipline.invest_before_year_start,
                       'resources_price': get_static_prices(np.arange(2020, 2051)),
                       'resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       'syngas_ratio': np.ones(len(years)),
                       'syngas_ratio_technos': self.syngas_ratio_technos,
                       'energy_detailed_techno_prices': self.syngas_detailed_prices,
                       'scaling_factor_invest_level': 1e3,
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production,
                       ResourceMixModel.RATIO_USABLE_DEMAND: self.ratio_available_resource,
                       'all_streams_demand_ratio': self.all_streams_demand_ratio,
                       'is_stream_demand': self.is_stream_demand,
                       'is_apply_resource_ratio': self.is_apply_resource_ratio,
                       'smooth_type': 'smooth_max',
                       'data_fuel_dict': self.data_fuel,
                       'syngas.data_fuel_dict': Syngas.data_energy_dict,
                       'hydrogen.gaseous_hydrogen.data_fuel_dict': GaseousHydrogen.data_energy_dict,
                       }

        ptl_model = FischerTropsch('FischerTropsch')

        ptl_model.configure_parameters(inputs_dict)
        ptl_model.configure_parameters_update(inputs_dict)
        price_details = ptl_model.compute_price()

    def test_02_FT_discipline(self):

        self.name = 'Test'
        self.model_name = 'FischerTropsch'
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
        years = np.arange(2020, 2051)
        inputs_dict = {f'{self.name}.year_end': 2050,

                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level,
                       f'{self.name}.{self.model_name}.margin': self.margin,
                       f'{self.name}.transport_margin': self.margin,
                       f'{self.name}.transport_cost': self.transport,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.syngas_ratio': np.ones(len(years)),
                       f'{self.name}.syngas_ratio_technos': self.syngas_ratio_technos,
                       f'{self.name}.energy_detailed_techno_prices': self.syngas_detailed_prices}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)

        # graph_list[-1].to_plotly().show()

    def test_03_FT_with_ratio_available_cc(self):

        self.name = 'Test'
        self.model_name = 'FischerTropsch'
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
        years = np.arange(2020, 2051)

        inputs_dict = {f'{self.name}.year_end': 2050,

                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level,
                       f'{self.name}.{self.model_name}.margin': self.margin,
                       f'{self.name}.transport_margin': self.margin,
                       f'{self.name}.transport_cost': self.transport,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.syngas_ratio': np.ones(len(years)),
                       f'{self.name}.syngas_ratio_technos': self.syngas_ratio_technos,
                       f'{self.name}.energy_detailed_techno_prices': self.syngas_detailed_prices,
                       f'{self.name}.{ResourceMixModel.RATIO_USABLE_DEMAND}': self.ratio_available_resource,
                       f'{self.name}.is_apply_resource_ratio': True}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        techno_production_wo_ratio = self.ee.dm.get_value(
            f'{self.name}.{self.model_name}.techno_production')
        techno_consumption_wo_ratio = self.ee.dm.get_value(
            f'{self.name}.{self.model_name}.techno_consumption')

        self.ee2 = ExecutionEngine(self.name)
        self.ee2.ns_manager.add_ns_def(ns_dict)
        builder = self.ee2.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee2.factory.set_builders_to_coupling_builder(builder)

        self.ee2.configure()

        self.ee2.load_study_from_input_dict(inputs_dict)

        self.ee2.execute()
        ratio = self.ee.dm.get_disciplines_with_name(f'{self.name}.{self.model_name}')[
            0].mdo_discipline_wrapp.mdo_discipline.techno_model.applied_ratio['applied_ratio'].values
        ratio2 = self.ee2.dm.get_disciplines_with_name(f'{self.name}.{self.model_name}')[
            0].mdo_discipline_wrapp.mdo_discipline.techno_model.applied_ratio['applied_ratio'].values
        techno_production_with_ratio = self.ee2.dm.get_value(
            f'{self.name}.{self.model_name}.techno_production')

        for column in techno_production_with_ratio.columns:
            if column != 'years':
                for i in range(len(techno_production_with_ratio[column].values)):
                    self.assertAlmostEqual(techno_production_with_ratio[column].values[i],
                                           techno_production_wo_ratio[column].values[i] * ratio2[i] / ratio[i], delta=1.0e-8)

        techno_consumption_with_ratio = self.ee2.dm.get_value(
            f'{self.name}.{self.model_name}.techno_consumption')
        for column in techno_consumption_with_ratio.columns:
            if column != 'years':
                for i in range(len(techno_consumption_with_ratio[column].values)):
                    self.assertAlmostEqual(techno_consumption_with_ratio[column].values[i],
                                           techno_consumption_wo_ratio[column].values[i] * ratio2[i] / ratio[i], delta=1.0e-8)


if '__main__' == __name__:

    cls = FTPriceTestCase()
    cls.setUp()
    cls.test_03_FT_with_ratio_available_cc()
