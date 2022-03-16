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

from energy_models.models.liquid_fuel.refinery.refinery_disc import RefineryDiscipline
from sos_trades_core.execution_engine.execution_engine import ExecutionEngine
from energy_models.core.stream_type.resources_data_disc import get_static_CO2_emissions,\
    get_static_prices
from sos_trades_core.tests.core.abstract_jacobian_unit_test import AbstractJacobianUnittest
from energy_models.core.energy_mix.energy_mix import EnergyMix
import pickle
import warnings
warnings.filterwarnings("ignore")


class LiquidFuelJacobianCase(AbstractJacobianUnittest):
    """
    Liquid Fuel jacobian test class
    """
    #AbstractJacobianUnittest.DUMP_JACOBIAN = True

    def analytic_grad_entry(self):
        return [
            self.test_01_refinery_jacobian,
            self.test_02_transesterification_discipline_analytic_grad,
            self.test_03_transesterification_discipline_analytic_grad_negative_invest,
            self.test_04_transesterification_discipline_analytic_grad_negative_invest2,
            self.test_05_liquid_fuel_discipline_jacobian,
        ]

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        years = np.arange(2020, 2051)
        self.energy_name = 'liquid_fuel'
        # crude oil price : 1.3$/gallon
        self.energy_prices = pd.DataFrame({'years': years, 'electricity': np.array([0.16, 0.15974117039450046, 0.15948672733558984,
                                                                                    0.159236536471781, 0.15899046935409588, 0.15874840310033885,
                                                                                    0.15875044941298937, 0.15875249600769718, 0.15875454288453355,
                                                                                    0.15875659004356974, 0.1587586374848771, 0.15893789675406477,
                                                                                    0.15911934200930778, 0.15930302260662477, 0.15948898953954933,
                                                                                    0.15967729551117891, 0.15986799501019029, 0.16006114439108429,
                                                                                    0.16025680195894345, 0.16045502805900876, 0.16065588517140537,
                                                                                    0.1608594380113745, 0.16106575363539733, 0.16127490155362818,
                                                                                    0.16148695384909017, 0.1617019853041231, 0.1619200735346165,
                                                                                    0.16214129913260598, 0.16236574581786147, 0.16259350059915213,
                                                                                    0.1628246539459331]) * 1000.0,
                                           'CO2': 0.0,
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
            {'years': years, 'electricity': 0.0, 'syngas': 0.0})
        # We use the IEA H2 demand to fake the invest level through years
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

        self.invest_level_negative = pd.DataFrame({'years': years,
                                                   'invest': -np.array([4435750000.0, 4522000000.0, 4608250000.0,
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

        self.invest_level_negative2 = pd.DataFrame({'years': years,
                                                    'invest': np.array([4435750000.0, 4522000000.0, 4608250000.0,
                                                                        4694500000.0, 4780750000.0, 4867000000.0,
                                                                        4969400000.0, 5071800000.0, 5174200000.0,
                                                                        5276600000.0, 5379000000.0, 5364700000.0,
                                                                        5350400000.0, -5336100000.0, -5321800000.0,
                                                                        -5307500000.0, -5293200000.0, -5278900000.0,
                                                                        -5264600000.0, -5250300000.0, 5236000000.0,
                                                                        5221700000.0, 5207400000.0, 5193100000.0,
                                                                        5178800000.0, 5164500000.0, 5150200000.0,
                                                                        5135900000.0, 5121600000.0, 5107300000.0,
                                                                        5093000000.0]) * 1.0e-9})
        invest = np.array([5093000000.0, 5107300000.0, 5121600000.0, 5135900000.0,
                           5150200000.0, 5164500000.0, 5178800000.0,
                           5221700000.0, 5207400000.0, 5193100000.0,
                           5064600000.0, 4950300000.0, 4836000000.0,
                           4707500000.0, 4793200000.0, 4678900000.0,
                           4550400000.0, 4336100000.0, 4321800000.0,
                           4435750000.0, 4522000000.0, 4608250000.0,
                           4276600000.0, 4379000000.0, 4364700000.0,
                           4169400000.0, 4071800000.0, 4174200000.0,
                           3894500000.0, 3780750000.0, 3567000000.0,
                           ]) * 0.8e-9
        # We use the IEA Kero demand to fake the invest level through years
        self.invest_level = pd.DataFrame(
            {'years': years, 'invest': invest})
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
            {'years': years, 'transport': np.ones(len(years)) * 200.0})

        biblio_data_path = join(
            dirname(__file__), 'output_values_check', 'biblio_data.csv')
        self.biblio_data = pd.read_csv(biblio_data_path)
        self.biblio_data = self.biblio_data.loc[self.biblio_data['sos_name']
                                                == 'liquid_fuel.Refinery']
        #---Ratios---
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.linspace(1.0, 1.0, len(years))))
        demand_ratio_dict['years'] = years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)

        resource_ratio_dict = dict(
            zip(EnergyMix.RESOURCE_LIST, np.linspace(1.0, 1.0, len(years))))
        resource_ratio_dict['years'] = years
        self.all_resource_ratio_usable_demand = pd.DataFrame(
            resource_ratio_dict)

    def tearDown(self):
        pass

    def test_01_refinery_jacobian(self):

        self.name = 'Test'
        self.model_name = 'refinery'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_liquid_fuel': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.liquid_fuel.refinery.refinery_disc.RefineryDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.resources_price': get_static_prices(np.arange(2020, 2051)),
                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.transport_margin': self.margin,
                       f'{self.name}.transport_cost': self.transport,
                       f'{self.name}.{self.model_name}.margin':  self.margin,
                       f'{self.name}.{self.model_name}.invest_before_ystart':
                       RefineryDiscipline.invest_before_year_start,
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        disc_techno = self.ee.root_process.sos_disciplines[0]

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            inputs=[f'{self.name}.{self.model_name}.invest_level',
                                    f'{self.name}.energy_prices',
                                    f'{self.name}.energy_CO2_emissions',
                                    f'{self.name}.CO2_taxes',
                                    f'{self.name}.resources_price',
                                    f'{self.name}.resources_CO2_emissions',],
                            outputs=[f'{self.name}.{self.model_name}.techno_prices',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.techno_consumption',
                                     f'{self.name}.{self.model_name}.techno_consumption_woratio',
                                     f'{self.name}.{self.model_name}.techno_production',
                                     ],)

    def test_02_transesterification_discipline_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'Transesterification'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   #    'ns_biogas': f'{self.name}'
                   'ns_biodiesel': f'{self.name}',
                   'ns_resource': f'{self.name}'
                   }
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.biodiesel.transesterification.transesterification_disc.TransesterificationDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.transport_margin': self.margin,
                       f'{self.name}.transport_cost': self.transport,
                       f'{self.name}.{self.model_name}.margin':  self.margin,
                       f'{self.name}.resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.resources_price': get_static_prices(np.arange(2020, 2051)),
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        disc_techno = self.ee.root_process.sos_disciplines[0]

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            inputs=[f'{self.name}.{self.model_name}.invest_level',
                                    f'{self.name}.energy_prices',
                                    f'{self.name}.energy_CO2_emissions',
                                    f'{self.name}.CO2_taxes'],
                            outputs=[f'{self.name}.{self.model_name}.techno_prices',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.techno_consumption',
                                     f'{self.name}.{self.model_name}.techno_consumption_woratio',
                                     f'{self.name}.{self.model_name}.techno_production',
                                     ],)

    def test_03_transesterification_discipline_analytic_grad_negative_invest(self):

        self.name = 'Test'
        self.model_name = 'Transesterification'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   #    'ns_biogas': f'{self.name}'
                   'ns_biodiesel': f'{self.name}',
                   'ns_resource': f'{self.name}'
                   }
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.biodiesel.transesterification.transesterification_disc.TransesterificationDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level_negative,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.transport_margin': self.margin,
                       f'{self.name}.transport_cost': self.transport,
                       f'{self.name}.{self.model_name}.margin':  self.margin,
                       f'{self.name}.resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.resources_price': get_static_prices(np.arange(2020, 2051)),
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)
        #AbstractJacobianUnittest.DUMP_JACOBIAN = True
        disc_techno = self.ee.root_process.sos_disciplines[0]
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}_negative.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step',
                            inputs=[f'{self.name}.{self.model_name}.invest_level',
                                    f'{self.name}.energy_prices',
                                    f'{self.name}.energy_CO2_emissions',
                                    f'{self.name}.CO2_taxes'],
                            outputs=[f'{self.name}.{self.model_name}.techno_prices',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.techno_consumption',
                                     f'{self.name}.{self.model_name}.techno_consumption_woratio',
                                     f'{self.name}.{self.model_name}.techno_production',
                                     ],)

    def test_04_transesterification_discipline_analytic_grad_negative_invest2(self):

        self.name = 'Test'
        self.model_name = 'Transesterification'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   #    'ns_biogas': f'{self.name}'
                   'ns_biodiesel': f'{self.name}',
                   'ns_resource': f'{self.name}'
                   }
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.biodiesel.transesterification.transesterification_disc.TransesterificationDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level_negative2,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.transport_margin': self.margin,
                       f'{self.name}.transport_cost': self.transport,
                       f'{self.name}.{self.model_name}.margin':  self.margin,
                       f'{self.name}.resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.resources_price': get_static_prices(np.arange(2020, 2051)),
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)
        disc_techno = self.ee.root_process.sos_disciplines[0]
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}_negative2.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step',
                            inputs=[f'{self.name}.{self.model_name}.invest_level',
                                    f'{self.name}.energy_prices',
                                    f'{self.name}.energy_CO2_emissions',
                                    f'{self.name}.CO2_taxes'],
                            outputs=[f'{self.name}.{self.model_name}.techno_prices',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.techno_consumption',
                                     f'{self.name}.{self.model_name}.techno_consumption_woratio',
                                     f'{self.name}.{self.model_name}.techno_production',
                                     ],)

    def test_05_liquid_fuel_discipline_jacobian(self):

        self.name = 'Test'
        self.energy_name = 'fuel.liquid_fuel'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': f'{self.name}',
                   'ns_liquid_fuel': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_resource': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.stream_type.energy_disciplines.liquid_fuel_disc.LiquidFuelDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.energy_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_streams_input_dict.pkl'), 'rb')
        mda_data_input_dict = pickle.load(pkl_file)
        pkl_file.close()

        namespace = f'{self.name}'
        inputs_dict = {}
        coupled_inputs = []
        for key in mda_data_input_dict[self.energy_name].keys():
            if key in ['technologies_list', 'CO2_taxes', 'year_start', 'year_end',
                       'scaling_factor_energy_production', 'scaling_factor_energy_consumption',
                       'scaling_factor_techno_consumption', 'scaling_factor_techno_production', ]:
                inputs_dict[f'{namespace}.{key}'] = mda_data_input_dict[self.energy_name][key]['value']
                if mda_data_input_dict[self.energy_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{key}']
            else:
                inputs_dict[f'{namespace}.{self.energy_name}.{key}'] = mda_data_input_dict[self.energy_name][key]['value']
                if mda_data_input_dict[self.energy_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{self.energy_name}.{key}']

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_streams_output_dict.pkl'), 'rb')
        mda_data_output_dict = pickle.load(pkl_file)
        pkl_file.close()

        coupled_outputs = []
        for key in mda_data_output_dict[self.energy_name].keys():
            if mda_data_output_dict[self.energy_name][key]['is_coupling']:
                coupled_outputs += [f'{namespace}.{self.energy_name}.{key}']

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.energy_name}')[0]

        # AbstractJacobianUnittest.DUMP_JACOBIAN = True
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}.pkl',
                            discipline=disc, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,
                            inputs=coupled_inputs,
                            outputs=coupled_outputs,)


if '__main__' == __name__:
    AbstractJacobianUnittest.DUMP_JACOBIAN = True
    cls = LiquidFuelJacobianCase()
    cls.setUp()
    cls.test_05_liquid_fuel_discipline_jacobian()
