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

from energy_models.core.stream_type.resources_models.water import Water
from sos_trades_core.execution_engine.execution_engine import ExecutionEngine
from energy_models.core.stream_type.resources_data_disc import get_static_CO2_emissions,\
    get_static_prices
from sos_trades_core.tests.core.abstract_jacobian_unit_test import AbstractJacobianUnittest
from energy_models.core.energy_mix.energy_mix import EnergyMix
import pickle


class ElectricityJacobianTestCase(AbstractJacobianUnittest):
    """
    Electricity jacobian test class
    """
    #AbstractJacobianUnittest.DUMP_JACOBIAN = True

    def analytic_grad_entry(self):
        return [
            self.test_01_combined_cycle_gas_turbine_discipline_analytic_grad,
            self.test_02_geothermal_discipline_analytic_grad,
            self.test_03_hydropower_discipline_analytic_grad,
            self.test_04_coal_gen_discipline_analytic_grad,
            self.test_05_gas_turbine_discipline_analytic_grad,
            self.test_06_wind_on_shore_discipline_analytic_grad,
            self.test_07_wind_off_shore_discipline_analytic_grad,
            self.test_08_solar_thermal_discipline_analytic_grad,
            self.test_09_solar_pv_discipline_analytic_grad,
            self.test_10_nuclear_discipline_analytic_grad,
            self.test_11_electricity_discipline_jacobian,
        ]

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.energy_name = 'electricity'

        years = np.arange(2020, 2051)

        # --- energy prices ---
        solid_fuel_price = np.array(
            [5.7] * 31)
        self.energy_prices = pd.DataFrame({'years': years, 'electricity': np.array([0.09, 0.08974117039450046, 0.08948672733558984,
                                                                                    0.089236536471781, 0.08899046935409588, 0.08874840310033885,
                                                                                    0.08875044941298937, 0.08875249600769718, 0.08875454288453355,
                                                                                    0.08875659004356974, 0.0887586374848771, 0.08893789675406477,
                                                                                    0.08911934200930778, 0.08930302260662477, 0.08948898953954933,
                                                                                    0.08967729551117891, 0.08986799501019029, 0.09006114439108429,
                                                                                    0.09025680195894345, 0.09045502805900876, 0.09065588517140537,
                                                                                    0.0908594380113745, 0.09106575363539733, 0.09127490155362818,
                                                                                    0.09148695384909017, 0.0917019853041231, 0.0919200735346165,
                                                                                    0.09214129913260598, 0.09236574581786147, 0.09259350059915213,
                                                                                    0.0928246539459331]) * 1000.0,
                                           'solid_fuel': solid_fuel_price,
                                           'methane': np.ones(len(years)) * 27.07
                                           })
#         self.energy_prices = pd.DataFrame(
#             {'methane': np.ones(len(years)) * 27.07})
        self.energy_carbon_emissions = pd.DataFrame(
            {'years': years, 'methane': 0.123 / 15.4, 'solid_fuel': 0.64 / 4.86, 'electricity': 0.0})
        #  IEA invest data NPS Scenario 22bn to 2030 and 31bn after 2030

        # --- invest level ---
        self.invest_level_ccgast = pd.DataFrame(
            {'years': years, 'invest': np.ones(len(years)) * 21.0})

        self.invest_level_geothermal = pd.DataFrame({'years': years})
        self.invest_level_geothermal['invest'] = 5.0 * \
            1.10 ** (self.invest_level_geothermal['years'] - 2020)

        self.invest_level_solar_pv = pd.DataFrame(
            {'years': years, 'invest': np.ones(len(years)) * 130.0})

        self.invest_level_solar_thermal = pd.DataFrame(
            {'years': years, 'invest': np.ones(len(years)) * 15.0})

        self.invest_level_coal = pd.DataFrame(
            {'years': years, 'invest': np.ones(len(years)) * 50.0})

        self.invest_level_nuclear = pd.DataFrame({'years': years})
        self.invest_level_nuclear['invest'] = 33.0 * \
            1.10 ** (self.invest_level_nuclear['years'] - 2020)

        self.invest_level_hydropower = pd.DataFrame({'years': years,
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
        self.invest_level_windonshore = pd.DataFrame(
            {'years': years, 'invest': np.array([22000.00, 22000.00, 22000.00, 22000.00,
                                                 22000.00, 22000.00, 22000.00, 22000.00,
                                                 22000.00, 22000.00, 31000.00, 31000.00,
                                                 31000.00, 31000.00, 31000.00, 31000.00,
                                                 31000.00, 31000.00, 31000.00, 31000.00,
                                                 31000.00, 31000.00, 31000.00, 31000.00,
                                                 31000.00, 31000.00, 31000.00, 31000.00,
                                                 31000.00, 31000.00, 31000.00]) * 1e-3})

        # --- CO2 taxes ---
        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        # co2_taxes = [0.01486, 0.01722, 0.02027,
        #             0.02901,  0.03405,   0.03908,  0.04469,   0.05029]

        co2_taxes = [14.86, 17.22, 20.27,
                     29.01,  34.05,   39.08,  44.69,   50.29]
        co2_taxes_nul = [0, 0, 0,
                         0,  0,   0,  0,   0]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')
        func_nul = sc.interp1d(co2_taxes_year, co2_taxes_nul,
                               kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {'years': years, 'CO2_tax': func(years)})
        self.co2_taxes_nul = pd.DataFrame(
            {'years': years, 'CO2_tax': func_nul(years)})

        self.margin = pd.DataFrame(
            {'years': years, 'margin': np.ones(len(years)) * 110.0})

        # --- Transport ---
        transport_cost = 11.0
        # It is noteworthy that the cost of transmission has generally been held (and can
        # continue to be held)    within the �10-12/MWhr range despite transmission distances
        # increasing by almost an order of magnitude from an average of 20km for the
        # leftmost bar to 170km for the 2020 scenarios / OWPB 2016

        self.transport = pd.DataFrame(
            {'years': years, 'transport': np.ones(len(years)) * transport_cost})

        self.transport_nul = pd.DataFrame(
            {'years': years, 'transport': np.zeros(len(years))})

        # --- resources ---
        self.resources_price = pd.DataFrame(
            columns=['years', 'water'])
        self.resources_price['years'] = years
        self.resources_price['water'] = Water.data_energy_dict['cost_now']
        self.resources_price['uranium fuel'] = 1390.0e3

        biblio_data_path = join(
            dirname(__file__), 'output_values_check', 'biblio_data.csv')
        self.biblio_data = pd.read_csv(biblio_data_path)
        self.biblio_data = self.biblio_data.loc[self.biblio_data['sos_name']
                                                == 'electricity.CombinedCycleGasTurbine']
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

    def test_01_combined_cycle_gas_turbine_discipline_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'cc_gas_turbine'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.electricity.gas.combined_cycle_gas_turbine.combined_cycle_gas_turbine_disc.CombinedCycleGasTurbineDiscipline'

        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        inputs_dict = {f'{self.name}.resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.resources_price': get_static_prices(np.arange(2020, 2051)),
                       f'{self.name}.{self.model_name}.margin': self.margin,
                       f'{self.name}.CO2_taxes': self.co2_taxes_nul,
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level_ccgast,
                       f'{self.name}.transport_cost':  self.transport,
                       f'{self.name}.transport_margin': pd.concat([self.margin['years'], self.margin['margin'] / 1.1], axis=1, keys=['years', 'margin']),
                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': self.energy_carbon_emissions,
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand, }

        self.ee.load_study_from_input_dict(inputs_dict)

        disc_techno = self.ee.root_process.sos_disciplines[0]

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            inputs=[f'{self.name}.{self.model_name}.invest_level',
                                    f'{self.name}.energy_prices',
                                    f'{self.name}.energy_CO2_emissions'],
                            outputs=[f'{self.name}.{self.model_name}.techno_prices',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.techno_consumption',
                                     f'{self.name}.{self.model_name}.techno_consumption_woratio',
                                     f'{self.name}.{self.model_name}.techno_production',
                                     ],)

    def test_02_geothermal_discipline_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'geothermal'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.electricity.geothermal.geothermal_disc.GeothermalDiscipline'

        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        inputs_dict = {f'{self.name}.resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.resources_price': get_static_prices(np.arange(2020, 2051)),
                       f'{self.name}.{self.model_name}.margin': self.margin,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level_geothermal,
                       f'{self.name}.transport_cost':  self.transport_nul,
                       f'{self.name}.transport_margin':  pd.concat([self.margin['years'], self.margin['margin'] / 1.1], axis=1, keys=['years', 'margin']),
                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': pd.DataFrame(),
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        disc_techno = self.ee.root_process.sos_disciplines[0]

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            inputs=[f'{self.name}.{self.model_name}.invest_level',
                                    f'{self.name}.energy_prices',
                                    f'{self.name}.energy_CO2_emissions'],
                            outputs=[f'{self.name}.{self.model_name}.techno_prices',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.techno_consumption',
                                     f'{self.name}.{self.model_name}.techno_consumption_woratio',
                                     f'{self.name}.{self.model_name}.techno_production',
                                     ],)

    def test_03_hydropower_discipline_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'hydropower'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.electricity.hydropower.hydropower_disc.HydropowerDiscipline'

        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        inputs_dict = {f'{self.name}.resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.resources_price': get_static_prices(np.arange(2020, 2051)),
                       f'{self.name}.{self.model_name}.margin': self.margin,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level_hydropower,
                       f'{self.name}.transport_cost':  self.transport,
                       f'{self.name}.transport_margin':  pd.concat([self.margin['years'], self.margin['margin'] / 1.1], axis=1, keys=['years', 'margin']),
                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': pd.DataFrame(),
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        disc_techno = self.ee.root_process.sos_disciplines[0]

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            inputs=[f'{self.name}.{self.model_name}.invest_level',
                                    f'{self.name}.energy_prices',
                                    f'{self.name}.energy_CO2_emissions'],
                            outputs=[f'{self.name}.{self.model_name}.techno_prices',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.techno_consumption',
                                     f'{self.name}.{self.model_name}.techno_consumption_woratio',
                                     f'{self.name}.{self.model_name}.techno_production',
                                     ],)

    def test_04_coal_gen_discipline_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'coal_gen'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_resource': f'{self.name}',
                   'ns_solid_fuel': f'{self.name}',
                   }
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.electricity.coal_gen.coal_gen_disc.CoalGenDiscipline'

        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        inputs_dict = {f'{self.name}.resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.resources_price': get_static_prices(np.arange(2020, 2051)),
                       f'{self.name}.{self.model_name}.margin': self.margin,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level_coal,
                       f'{self.name}.transport_cost':  self.transport_nul,
                       f'{self.name}.transport_margin':  pd.concat([self.margin['years'], self.margin['margin'] / 1.1], axis=1, keys=['years', 'margin']),
                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': self.energy_carbon_emissions,
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        disc_techno = self.ee.root_process.sos_disciplines[0]

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            inputs=[f'{self.name}.{self.model_name}.invest_level',
                                    f'{self.name}.energy_prices',
                                    f'{self.name}.energy_CO2_emissions'],
                            outputs=[f'{self.name}.{self.model_name}.techno_prices',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.techno_consumption',
                                     f'{self.name}.{self.model_name}.techno_consumption_woratio',
                                     f'{self.name}.{self.model_name}.techno_production',
                                     ],)

    def test_05_gas_turbine_discipline_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'gas_turbine'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.electricity.gas.gas_turbine.gas_turbine_disc.GasTurbineDiscipline'

        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        inputs_dict = {f'{self.name}.resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.resources_price': get_static_prices(np.arange(2020, 2051)),
                       f'{self.name}.{self.model_name}.margin': self.margin,
                       f'{self.name}.CO2_taxes': self.co2_taxes_nul,
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level_ccgast,
                       f'{self.name}.transport_cost':  self.transport,
                       f'{self.name}.transport_margin':  pd.concat([self.margin['years'], self.margin['margin'] / 1.1], axis=1, keys=['years', 'margin']),
                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': self.energy_carbon_emissions,
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        disc_techno = self.ee.root_process.sos_disciplines[0]

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            inputs=[f'{self.name}.{self.model_name}.invest_level',
                                    f'{self.name}.energy_prices',
                                    f'{self.name}.energy_CO2_emissions'],
                            outputs=[f'{self.name}.{self.model_name}.techno_prices',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.techno_consumption',
                                     f'{self.name}.{self.model_name}.techno_consumption_woratio',
                                     f'{self.name}.{self.model_name}.techno_production',
                                     ],)

    def test_06_wind_on_shore_discipline_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'wind_on_shore'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.electricity.wind_onshore.wind_onshore_disc.WindOnshoreDiscipline'

        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        inputs_dict = {f'{self.name}.resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.resources_price': get_static_prices(np.arange(2020, 2051)),
                       f'{self.name}.{self.model_name}.margin': self.margin,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level_windonshore,
                       f'{self.name}.transport_cost':  self.transport,
                       f'{self.name}.transport_margin':  pd.concat([self.margin['years'], self.margin['margin'] / 1.1], axis=1, keys=['years', 'margin']),
                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': pd.DataFrame(),
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        disc_techno = self.ee.root_process.sos_disciplines[0]
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            inputs=[f'{self.name}.{self.model_name}.invest_level',
                                    f'{self.name}.energy_prices',
                                    f'{self.name}.energy_CO2_emissions'],
                            outputs=[f'{self.name}.{self.model_name}.techno_prices',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.techno_consumption',
                                     f'{self.name}.{self.model_name}.techno_consumption_woratio',
                                     f'{self.name}.{self.model_name}.techno_production',
                                     ],)

    def test_07_wind_off_shore_discipline_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'wind_off_shore'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.electricity.wind_offshore.wind_offshore_disc.WindOffshoreDiscipline'

        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        inputs_dict = {f'{self.name}.resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.resources_price': get_static_prices(np.arange(2020, 2051)),
                       f'{self.name}.{self.model_name}.margin': self.margin,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       # same invest on and off shore
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level_windonshore,
                       f'{self.name}.{self.model_name}.transport_cost':  self.transport,
                       f'{self.name}.transport_margin': pd.concat([self.margin['years'], self.margin['margin'] / 1.1], axis=1, keys=['years', 'margin']),
                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': pd.DataFrame(),
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        disc_techno = self.ee.root_process.sos_disciplines[0]

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            inputs=[f'{self.name}.{self.model_name}.invest_level',
                                    f'{self.name}.energy_prices',
                                    f'{self.name}.energy_CO2_emissions'],
                            outputs=[f'{self.name}.{self.model_name}.techno_prices',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.techno_consumption',
                                     f'{self.name}.{self.model_name}.techno_consumption_woratio',
                                     f'{self.name}.{self.model_name}.techno_production',
                                     ],)

    def test_08_solar_thermal_discipline_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'solar_thermal'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.electricity.solar_thermal.solar_thermal_disc.SolarThermalDiscipline'

        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        inputs_dict = {f'{self.name}.resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.resources_price': get_static_prices(np.arange(2020, 2051)),
                       f'{self.name}.{self.model_name}.margin': self.margin,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level_solar_thermal,
                       f'{self.name}.transport_cost':  self.transport,
                       f'{self.name}.transport_margin': pd.concat([self.margin['years'], self.margin['margin'] / 1.1], axis=1, keys=['years', 'margin']),
                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': pd.DataFrame(),
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        disc_techno = self.ee.root_process.sos_disciplines[0]

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            inputs=[f'{self.name}.{self.model_name}.invest_level',
                                    f'{self.name}.energy_prices',
                                    f'{self.name}.energy_CO2_emissions'],
                            outputs=[f'{self.name}.{self.model_name}.techno_prices',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.techno_consumption',
                                     f'{self.name}.{self.model_name}.techno_consumption_woratio',
                                     f'{self.name}.{self.model_name}.techno_production',

                                     f'{self.name}.{self.model_name}.land_use_required'],)

    def test_09_solar_pv_discipline_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'solar_pv'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.electricity.solar_pv.solar_pv_disc.SolarPvDiscipline'

        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        inputs_dict = {f'{self.name}.resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.resources_price': get_static_prices(np.arange(2020, 2051)),
                       f'{self.name}.{self.model_name}.margin': self.margin,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level_solar_pv,
                       f'{self.name}.transport_cost':  self.transport,
                       f'{self.name}.transport_margin': pd.concat([self.margin['years'], self.margin['margin'] / 1.1], axis=1, keys=['years', 'margin']),
                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': pd.DataFrame(),
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        disc_techno = self.ee.root_process.sos_disciplines[0]

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5, inputs=[f'{self.name}.{self.model_name}.invest_level',
                                                                                                                      f'{self.name}.energy_prices',
                                                                                                                      f'{self.name}.energy_CO2_emissions'],
                            outputs=[f'{self.name}.{self.model_name}.techno_prices',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.techno_consumption',
                                     f'{self.name}.{self.model_name}.techno_consumption_woratio',
                                     f'{self.name}.{self.model_name}.techno_production',

                                     f'{self.name}.{self.model_name}.land_use_required'])

    def test_10_nuclear_discipline_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'nuclear'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.electricity.nuclear.nuclear_disc.NuclearDiscipline'

        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        inputs_dict = {f'{self.name}.resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.resources_price': get_static_prices(np.arange(2020, 2051)),
                       f'{self.name}.{self.model_name}.margin': self.margin,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level_nuclear,
                       f'{self.name}.transport_cost':  self.transport_nul,
                       f'{self.name}.transport_margin': pd.concat([self.margin['years'], self.margin['margin'] / 1.1], axis=1, keys=['years', 'margin']),
                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': pd.DataFrame(),
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        disc_techno = self.ee.root_process.sos_disciplines[0]

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            inputs=[f'{self.name}.{self.model_name}.invest_level',
                                    f'{self.name}.energy_prices',
                                    f'{self.name}.energy_CO2_emissions'],
                            outputs=[f'{self.name}.{self.model_name}.techno_prices',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.techno_consumption',
                                     f'{self.name}.{self.model_name}.techno_consumption_woratio',
                                     f'{self.name}.{self.model_name}.techno_production',
                                     ],)

    def test_11_electricity_discipline_jacobian(self):

        self.name = 'Test'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': f'{self.name}',
                   'ns_electricity': f'{self.name}',
                   'ns_ref': f'{self.name}',
                   'ns_functions': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_resource': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.stream_type.energy_disciplines.electricity_disc.ElectricityDiscipline'
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
        #AbstractJacobianUnittest.DUMP_JACOBIAN = True

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}.pkl',
                            discipline=disc, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,
                            inputs=coupled_inputs,
                            outputs=coupled_outputs,)


if '__main__' == __name__:
    AbstractJacobianUnittest.DUMP_JACOBIAN = True
    cls = ElectricityJacobianTestCase()
    cls.setUp()
    cls.test_11_electricity_discipline_jacobian()
