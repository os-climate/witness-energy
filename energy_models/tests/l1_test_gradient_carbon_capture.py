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

from energy_models.core.stream_type.ressources_data_disc import get_static_CO2_emissions,\
    get_static_prices
from energy_models.models.carbon_capture.direct_air_capture.amine_scrubbing.amine_scrubbing_disc import AmineScrubbingDiscipline
from sos_trades_core.execution_engine.execution_engine import ExecutionEngine
from energy_models.models.carbon_capture.direct_air_capture.calcium_potassium_scrubbing.calcium_potassium_scrubbing_disc import CalciumPotassiumScrubbingDiscipline
from energy_models.models.carbon_capture.flue_gas_capture.calcium_looping.calcium_looping_disc import CalciumLoopingDiscipline

from sos_trades_core.tests.core.abstract_jacobian_unit_test import AbstractJacobianUnittest
from energy_models.core.energy_mix.energy_mix import EnergyMix
import pickle


class CarbonCaptureJacobianTestCase(AbstractJacobianUnittest):
    """
    Carbon capture jacobian test class
    """
    #AbstractJacobianUnittest.DUMP_JACOBIAN = True

    def analytic_grad_entry(self):
        return [
            self.test_01_amine_jacobian,
            self.test_02_CaKOH_jacobian,
            self.test_03_Calcium_looping_jacobian,
            self.test_04_carbon_capture_discipline_jacobian,
        ]

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.energy_name = 'carbon_capture'
        KOH_price = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                              1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                              1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                              1.0, 1.0, 1.0, 1.0]) * 500.0

        # KOH price :
        # https://www.made-in-china.com/price/potassium-hydroxide-price.html
        amine_price = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                                1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                                1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                                1.0, 1.0, 1.0, 1.0]) * 1300.0

        CaO_price = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                              1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                              1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                              1.0, 1.0, 1.0, 1.0]) * 85.0

        years = np.arange(2020, 2051)

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
                                                                                    0.1628246539459331]) * 1000.0
                                           })

        self.energy_carbon_emissions = pd.DataFrame(
            {'years': years, 'amine': 0.0, 'electricity': 0.0})
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
                           ]) * 0.02 / 1000 * 1.0e-9

        self.ressources_prices = pd.DataFrame({'years': years, 'amine': amine_price, 'potassium': KOH_price,
                                               'calcium': CaO_price,
                                               })
        self.flue_gas_mean = pd.DataFrame(
            {'years': years, 'flue_gas_mean': np.linspace(0.1, 0.46, len(years))})
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
            {'years': years, 'transport': np.ones(len(years)) * 0.0})
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

    def test_01_amine_jacobian(self):

        self.name = 'Test'
        self.model_name = 'amine_scrubbing'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_carbon_capture': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.carbon_capture.direct_air_capture.amine_scrubbing.amine_scrubbing_disc.AmineScrubbingDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.ressources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.ressources_price': get_static_prices(np.arange(2020, 2051)),
                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.transport_margin': self.margin,
                       f'{self.name}.transport_cost': self.transport,
                       f'{self.name}.{self.model_name}.margin':  self.margin,
                       f'{self.name}.{self.model_name}.invest_before_ystart':
                       AmineScrubbingDiscipline.invest_before_year_start,
                       f'{self.name}.ressources_price': self.ressources_prices,
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        disc_techno = self.ee.root_process.sos_disciplines[0]

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,
                            inputs=[f'{self.name}.{self.model_name}.invest_level',
                                    f'{self.name}.energy_prices',
                                    f'{self.name}.energy_CO2_emissions', f'{self.name}.CO2_taxes'],
                            outputs=[f'{self.name}.{self.model_name}.techno_prices',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.techno_consumption',
                                     f'{self.name}.{self.model_name}.techno_consumption_woratio',
                                     f'{self.name}.{self.model_name}.techno_production'],)

    def test_02_CaKOH_jacobian(self):

        self.name = 'Test'
        self.model_name = 'calcium_potassium_scrubbing'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_carbon_capture': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.carbon_capture.direct_air_capture.calcium_potassium_scrubbing.calcium_potassium_scrubbing_disc.CalciumPotassiumScrubbingDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.ressources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.ressources_price': get_static_prices(np.arange(2020, 2051)),
                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.transport_margin': self.margin,
                       f'{self.name}.transport_cost': self.transport,
                       f'{self.name}.{self.model_name}.margin':  self.margin,
                       f'{self.name}.{self.model_name}.invest_before_ystart':
                       CalciumPotassiumScrubbingDiscipline.invest_before_year_start,
                       f'{self.name}.ressources_price': self.ressources_prices,
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        disc_techno = self.ee.root_process.sos_disciplines[0]

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,
                            inputs=[f'{self.name}.{self.model_name}.invest_level',
                                    f'{self.name}.energy_prices',
                                    f'{self.name}.energy_CO2_emissions', f'{self.name}.CO2_taxes'],
                            outputs=[f'{self.name}.{self.model_name}.techno_prices',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.techno_consumption',
                                     f'{self.name}.{self.model_name}.techno_consumption_woratio',
                                     f'{self.name}.{self.model_name}.techno_production', ],)

    def test_03_Calcium_looping_jacobian(self):

        self.name = 'Test'
        self.model_name = 'calcium_looping'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_carbon_capture': self.name,
                   'ns_flue_gas': f'{self.name}',
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.carbon_capture.flue_gas_capture.calcium_looping.calcium_looping_disc.CalciumLoopingDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.ressources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.ressources_price': get_static_prices(np.arange(2020, 2051)),
                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.transport_margin': self.margin,
                       f'{self.name}.transport_cost': self.transport,
                       f'{self.name}.{self.model_name}.margin':  self.margin,
                       f'{self.name}.{self.model_name}.invest_before_ystart':
                       CalciumLoopingDiscipline.invest_before_year_start,
                       f'{self.name}.ressources_price': self.ressources_prices,
                       f'{self.name}.flue_gas_mean': self.flue_gas_mean,
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        disc_techno = self.ee.root_process.sos_disciplines[0]

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,
                            inputs=[f'{self.name}.{self.model_name}.invest_level',
                                    f'{self.name}.energy_prices',
                                    f'{self.name}.energy_CO2_emissions',
                                    f'{self.name}.flue_gas_mean', f'{self.name}.CO2_taxes'],
                            outputs=[f'{self.name}.{self.model_name}.techno_prices',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.techno_consumption',
                                     f'{self.name}.{self.model_name}.techno_consumption_woratio',
                                     f'{self.name}.{self.model_name}.techno_production']
                            )

    def test_04_carbon_capture_discipline_jacobian(self):

        self.name = 'Test'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': f'{self.name}',
                   'ns_carbon_capture': f'{self.name}',
                   'ns_flue_gas': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_resource': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.stream_type.carbon_disciplines.carbon_capture_disc.CarbonCaptureDiscipline'
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
                       'scaling_factor_techno_consumption', 'scaling_factor_techno_production',
                       'flue_gas_prod_ratio', 'flue_gas_production']:
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
        #AbstractJacobianUnittest.DUMP_JACOBIAN = True

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}.pkl',
                            discipline=disc, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,
                            inputs=coupled_inputs,
                            outputs=coupled_outputs,)


if '__main__' == __name__:
    AbstractJacobianUnittest.DUMP_JACOBIAN = True
    cls = CarbonCaptureJacobianTestCase()
    cls.setUp()
    cls.test_04_carbon_capture_discipline_jacobian()
