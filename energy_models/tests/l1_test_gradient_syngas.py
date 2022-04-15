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
from os.path import join, dirname

from sos_trades_core.execution_engine.execution_engine import ExecutionEngine
from energy_models.core.stream_type.resources_data_disc import get_static_CO2_emissions,\
    get_static_prices
from sos_trades_core.tests.core.abstract_jacobian_unit_test import AbstractJacobianUnittest
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
from energy_models.core.energy_mix.energy_mix import EnergyMix
import pickle


class SyngasJacobianTestCase(AbstractJacobianUnittest):
    """
    Syngas jacobian test class
    """
    AbstractJacobianUnittest.DUMP_JACOBIAN = True

    def analytic_grad_entry(self):
        return [
            self.test_01_atr_discipline_jacobian,
            self.test_02_coelectrolysis_discipline_jacobian,
            self.test_03_smr_discipline_jac,
            self.test_04_rwgs_discipline_jacobian,
            self.test_05_coal_gasification_discipline_jacobian,
            self.test_06_biomass_gas_discipline_jacobian,
            self.test_07_pyrolysis_discipline_jacobian,
            self.test_08_syngas_discipline_jacobian,
            self.test_09_generic_syngas_discipline_jacobian,
        ]

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.energy_name = 'syngas'
        years = np.arange(2020, 2051)
        self.years = years
        self.energy_prices = pd.DataFrame({'years': years,
                                           'methane': 0.034,
                                           'electricity': np.array([0.09, 0.08974117039450046, 0.08948672733558984,
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
                                           'syngas': np.ones(len(years)) * 90.,
                                           'solid_fuel': np.ones(len(years)) * 48,
                                           'biomass_dry': np.ones(len(years)) * 6812 / 3.36
                                           })

        self.resources_prices = pd.DataFrame({'years': years,
                                              ResourceGlossary.Oxygen['name']: len(years) * [60.0],
                                              ResourceGlossary.CO2['name']: np.array([0.04, 0.041, 0.042, 0.043, 0.044, 0.045, 0.0464, 0.047799999999999995, 0.049199999999999994, 0.0506, 0.052, 0.0542, 0.0564, 0.0586, 0.0608, 0.063, 0.0652, 0.0674, 0.0696, 0.0718, 0.074, 0.0784, 0.0828, 0.0872, 0.0916, 0.096, 0.1006, 0.1052, 0.1098, 0.1144, 0.119]) * 1000.0,
                                              ResourceGlossary.Water['name']: 1.4
                                              })
        self.energy_carbon_emissions = pd.DataFrame(
            {'years': years, 'methane': 0.123 / 15.4, 'electricity': 0.03, 'syngas': 0.2, 'solid_fuel': 0.02, 'biomass_dry': - 0.425 * 44.01 / 12.0})

        self.invest_level_rwgs = pd.DataFrame(
            {'years': years, 'invest': np.ones(len(years)) * 0.1715})
        self.invest_level = pd.DataFrame(
            {'years': years, 'invest':  [0.0] + (len(years) - 1) * [1.0]})
        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [14.86, 17.22, 20.27,
                     29.01,  34.05,   39.08,  44.69,   50.29]

        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {'years': years, 'CO2_tax': func(years)})
        self.margin = pd.DataFrame(
            {'years': years, 'margin': np.ones(len(years)) * 100.0})

        self.transport = pd.DataFrame(
            {'years': years, 'transport': np.ones(len(years)) * 0})

        self.land_use_required_Pyrolysis = pd.DataFrame(
            {'years': self.years, 'Pyrolysis (Gha)': 0.0})
        self.land_use_required_SMR = pd.DataFrame(
            {'years': self.years, 'SMR (Gha)': 0.0})
        self.land_use_required_AutothermalReforming = pd.DataFrame(
            {'years': self.years, 'AutothermalReforming (Gha)': 0.0})
        self.land_use_required_BiomassGasification = pd.DataFrame(
            {'years': self.years, 'BiomassGasification (Gha)': 0.0})
        self.land_use_required_CoalGasification = pd.DataFrame(
            {'years': self.years, 'CoalGasification (Gha)': 0.0})
        self.land_use_required_CoElectrolysis = pd.DataFrame(
            {'years': self.years, 'CoElectrolysis (Gha)': 0.0})
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

    def test_01_atr_discipline_jacobian(self):

        self.name = 'Test'
        self.model_name = 'ATR'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_syngas': f'{self.name}',
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.syngas.autothermal_reforming.autothermal_reforming_disc.AutothermalReformingDiscipline'
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
                       f'{self.name}.resources_price': self.resources_prices,
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        disc_techno = self.ee.root_process.sos_disciplines[0]
        #AbstractJacobianUnittest.DUMP_JACOBIAN = True
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,
                            inputs=[f'{self.name}.{self.model_name}.invest_level',
                                    f'{self.name}.energy_prices',
                                    f'{self.name}.energy_CO2_emissions',
                                    f'{self.name}.CO2_taxes',
                                    f'{self.name}.resources_price',
                                    f'{self.name}.resources_CO2_emissions',
                                    ],
                            outputs=[f'{self.name}.{self.model_name}.techno_prices',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.syngas_ratio',
                                     f'{self.name}.{self.model_name}.techno_consumption',
                                     f'{self.name}.{self.model_name}.techno_consumption_woratio',
                                     f'{self.name}.{self.model_name}.techno_production',
                                     ],)

    def test_02_coelectrolysis_discipline_jacobian(self):

        self.name = 'Test'
        self.model_name = 'coelectrolysis'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_syngas': f'{self.name}',
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.syngas.co_electrolysis.co_electrolysis_disc.CoElectrolysisDiscipline'
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
                       f'{self.name}.resources_price': self.resources_prices,
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
                                    f'{self.name}.CO2_taxes',
                                    f'{self.name}.resources_price',
                                    f'{self.name}.resources_CO2_emissions',
                                    ],
                            outputs=[f'{self.name}.{self.model_name}.techno_prices',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.syngas_ratio',
                                     f'{self.name}.{self.model_name}.techno_consumption',
                                     f'{self.name}.{self.model_name}.techno_consumption_woratio',
                                     f'{self.name}.{self.model_name}.techno_production',
                                     ],)

    def test_03_smr_discipline_jac(self):

        self.name = 'Test'
        self.model_name = 'SMR'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_syngas': f'{self.name}',
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.syngas.smr.smr_disc.SMRDiscipline'
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
                       f'{self.name}.resources_price': self.resources_prices,
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
                                    f'{self.name}.CO2_taxes'],
                            outputs=[f'{self.name}.{self.model_name}.techno_prices',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.syngas_ratio',
                                     f'{self.name}.{self.model_name}.techno_consumption',
                                     f'{self.name}.{self.model_name}.techno_consumption_woratio',
                                     f'{self.name}.{self.model_name}.techno_production',
                                     ],)

    def test_04_rwgs_discipline_jacobian(self):

        self.name = 'Test'
        self.model_name = 'RWGS'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_syngas': f'{self.name}',
                   'ns_resource': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.syngas.reversed_water_gas_shift.reversed_water_gas_shift_disc.RWGSDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        years = np.arange(2020, 2051)
        inputs_dict = {f'{self.name}.resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.resources_price': get_static_prices(np.arange(2020, 2051)),
                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level_rwgs,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.transport_margin': self.margin,
                       f'{self.name}.transport_cost': self.transport,
                       f'{self.name}.{self.model_name}.margin':  self.margin,
                       f'{self.name}.{self.model_name}.syngas_ratio': np.ones(len(years)) * 33,
                       f'{self.name}.{self.model_name}.needed_syngas_ratio': 100.0,
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        disc_techno = self.ee.root_process.sos_disciplines[0]
        # 'invest', 'Capex_ReversedWaterGasShift', 'CO2_needs', 'syngas_needs','electricity',
        #AbstractJacobianUnittest.DUMP_JACOBIAN = True
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,
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

    def test_05_coal_gasification_discipline_jacobian(self):

        self.name = 'Test'
        self.model_name = 'coal_gasification'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_syngas': f'{self.name}',
                   'ns_liquid_fuel': f'{self.name}',
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.syngas.coal_gasification.coal_gasification_disc.CoalGasificationDiscipline'
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
                                    f'{self.name}.CO2_taxes'],
                            outputs=[f'{self.name}.{self.model_name}.techno_prices',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.syngas_ratio',
                                     f'{self.name}.{self.model_name}.techno_consumption',
                                     f'{self.name}.{self.model_name}.techno_consumption_woratio',
                                     f'{self.name}.{self.model_name}.techno_production',
                                     ],)

    def test_06_biomass_gas_discipline_jacobian(self):

        self.name = 'Test'
        self.model_name = 'biomass_gasification'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_syngas': f'{self.name}',
                   'ns_liquid_fuel': f'{self.name}',
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.syngas.biomass_gasification.biomass_gasification_disc.BiomassGasificationDiscipline'
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
                                    f'{self.name}.CO2_taxes'],
                            outputs=[f'{self.name}.{self.model_name}.techno_prices',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.syngas_ratio',
                                     f'{self.name}.{self.model_name}.techno_consumption',
                                     f'{self.name}.{self.model_name}.techno_consumption_woratio',
                                     f'{self.name}.{self.model_name}.techno_production',
                                     ],)

    def test_07_pyrolysis_discipline_jacobian(self):

        self.name = 'Test'
        self.model_name = 'pyrolysis'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_syngas': f'{self.name}',
                   'ns_liquid_fuel': f'{self.name}',
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.syngas.pyrolysis.pyrolysis_disc.PyrolysisDiscipline'
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
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        disc_techno = self.ee.root_process.sos_disciplines[0]
        #AbstractJacobianUnittest.DUMP_JACOBIAN = True

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,
                            inputs=[f'{self.name}.{self.model_name}.invest_level',
                                    f'{self.name}.energy_prices',
                                    f'{self.name}.energy_CO2_emissions',
                                    f'{self.name}.CO2_taxes',
                                    f'{self.name}.resources_price',
                                    f'{self.name}.resources_CO2_emissions',
                                    ],
                            outputs=[f'{self.name}.{self.model_name}.techno_prices',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.syngas_ratio',
                                     f'{self.name}.{self.model_name}.techno_consumption',
                                     f'{self.name}.{self.model_name}.techno_consumption_woratio',
                                     f'{self.name}.{self.model_name}.techno_production',
                                     ],)

    def test_08_syngas_discipline_jacobian(self):

        self.pyrolysis_consumption = pd.DataFrame({'years': self.years, 'wood (Mt)': [1.090599945663164e-13, 1.0097898717328532e-13, 9.579124389341809e-14, 9.088332882344123, 18.17666576468815, 27.26499864703218, 36.35333152937621, 45.44166441172024, 54.52999729406426, 63.61833017640825, 72.70666305875228, 81.79499594109633, 90.88332882344037, 99.9716617057844,
                                                                                      109.05999458812843, 118.14832747047245, 127.23666035281647, 136.3249932351605, 145.41332611750454, 154.50165899984856, 163.58999188219258, 172.6783247645366, 181.76665764688062, 181.76665764688062, 181.76665764688062, 181.76665764688062, 181.76665764688062, 181.76665764688062, 181.76665764688062, 181.76665764688062, 181.76665764688062]})
        self.pyrolysis_production = pd.DataFrame({'years': self.years,
                                                  'syngas (TWh)': [9.999999998e-13, 9.259031009e-13, 8.783353076e-13, 83.33333333333415, 166.66666666666742, 250.0000000000007, 333.33333333333405, 416.6666666666673, 500.00000000000057, 583.3333333333335, 666.6666666666669, 750.0000000000002, 833.3333333333336, 916.666666666667, 1000.0000000000003, 1083.3333333333335, 1166.6666666666667, 1250.0, 1333.3333333333333, 1416.6666666666665, 1499.9999999999998, 1583.333333333333, 1666.6666666666663, 1666.6666666666663, 1666.6666666666663, 1666.6666666666663, 1666.6666666666663, 1666.6666666666663, 1666.6666666666663, 1666.6666666666663, 1666.6666666666663],
                                                  'CO2 from Flue Gas (Mt)': [1.5268399239284294e-14, 1.4137058204259942e-14, 1.3410774145078533e-14, 1.272366603528177, 2.544733207056341, 3.8170998105845046, 5.089466414112669, 6.361833017640833, 7.634199621168996, 8.906566224697155, 10.178932828225319, 11.451299431753485, 12.72366603528165, 13.996032638809815, 15.26839924233798, 16.54076584586614, 17.813132449394306, 19.08549905292247, 20.35786565645063, 21.630232259978794, 22.90259886350696, 24.174965467035122, 25.447332070563284, 25.447332070563284, 25.447332070563284, 25.447332070563284, 25.447332070563284, 25.447332070563284, 25.447332070563284, 25.447332070563284, 25.447332070563284],
                                                  'char (Mt)': [2.1428571424285717e-13, 1.984078073357143e-13, 1.882147087714286e-13, 17.85714285714303, 35.71428571428588, 53.571428571428726, 71.42857142857159, 89.28571428571442, 107.14285714285727, 125.00000000000003, 142.85714285714292, 160.71428571428578, 178.5714285714286, 196.42857142857147, 214.2857142857144, 232.1428571428572, 250.00000000000003, 267.8571428571429, 285.71428571428567, 303.57142857142856, 321.4285714285714, 339.2857142857142, 357.1428571428571, 357.1428571428571, 357.1428571428571, 357.1428571428571, 357.1428571428571, 357.1428571428571, 357.1428571428571, 357.1428571428571, 357.1428571428571],
                                                  'bio_oil (Mt)': [2.1428571424285717e-13, 1.984078073357143e-13, 1.882147087714286e-13, 17.85714285714303, 35.71428571428588, 53.571428571428726, 71.42857142857159, 89.28571428571442, 107.14285714285727, 125.00000000000003, 142.85714285714292, 160.71428571428578, 178.5714285714286, 196.42857142857147, 214.2857142857144, 232.1428571428572, 250.00000000000003, 267.8571428571429, 285.71428571428567, 303.57142857142856, 321.4285714285714, 339.2857142857142, 357.1428571428571, 357.1428571428571, 357.1428571428571, 357.1428571428571, 357.1428571428571, 357.1428571428571, 357.1428571428571, 357.1428571428571, 357.1428571428571]
                                                  })
        self.pyrolysis_techno_prices = pd.DataFrame({'years': self.years, 'Pyrolysis': [18.59009081523392, 18.71782188089554, 18.845552946557156, 18.97328401221877, 19.101015077880387, 19.228746143542004, 19.594768934978894, 19.96079172641579, 20.326814517852682, 20.692837309289573, 21.05886010072647, 21.269930451852545, 21.481000802978627, 21.69207115410471, 21.90314150523079, 22.114211856356867, 22.324863417103728, 22.53551497785059, 22.746166538597453, 22.956818099344314, 23.16746966009118, 23.402411062832705, 23.637352465574235, 23.872293868315765, 24.107235271057295, 24.342176673798825, 24.576699286161137, 24.81122189852345, 25.045744510885758, 25.28026712324807, 25.514789735610382], 'Pyrolysis_wotaxes': [
            14.984305650163385, 14.984305650163387, 14.984305650163389, 14.984305650163385, 14.984305650163385, 14.984305650163389, 14.984305650163385, 14.984305650163385, 14.984305650163385, 14.984305650163385, 14.984305650163389, 14.984305650163384, 14.984305650163385, 14.984305650163389, 14.984305650163385, 14.984305650163385, 14.984305650163384, 14.984305650163384, 14.984305650163385, 14.984305650163385, 14.984305650163387, 14.984305650163385, 14.984305650163385, 14.984305650163385, 14.984305650163385, 14.984305650163385, 14.984305650163387, 14.984305650163387, 14.984305650163385, 14.984305650163385, 14.984305650163385]})
        self.pyrolysis_carbon_emissions = pd.DataFrame({'years': self.years, 'production': [0.015268399242337975, 0.015268399242337975, 0.015268399242337975, 0.015268399242337975, 0.015268399242337975, 0.015268399242337975, 0.015268399242337975, 0.015268399242337975, 0.015268399242337975, 0.015268399242337975, 0.015268399242337975, 0.015268399242337975, 0.015268399242337975, 0.015268399242337975, 0.015268399242337975, 0.015268399242337975, 0.015268399242337975, 0.015268399242337975, 0.015268399242337975, 0.015268399242337975, 0.015268399242337975, 0.015268399242337975, 0.015268399242337975, 0.015268399242337975, 0.015268399242337975, 0.015268399242337975, 0.015268399242337975, 0.015268399242337975, 0.015268399242337975, 0.015268399242337975, 0.015268399242337975], 'wood': [0.19412679036686856, 0.19412679036686856, 0.19412679036686856, 0.19412679036686856, 0.19412679036686856, 0.19412679036686856, 0.19412679036686856, 0.19412679036686856, 0.19412679036686856, 0.19412679036686856, 0.19412679036686856, 0.19412679036686856, 0.19412679036686856,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                0.19412679036686856, 0.19412679036686856, 0.19412679036686856, 0.19412679036686856, 0.19412679036686856, 0.19412679036686856, 0.19412679036686856, 0.19412679036686856, 0.19412679036686856, 0.19412679036686856, 0.19412679036686856, 0.19412679036686856, 0.19412679036686856, 0.19412679036686856, 0.19412679036686856, 0.19412679036686856, 0.19412679036686856, 0.19412679036686856], 'Pyrolysis': [0.20939518960920653, 0.20939518960920653, 0.20939518960920653, 0.20939518960920653, 0.20939518960920653, 0.20939518960920653, 0.20939518960920653, 0.20939518960920653, 0.20939518960920653, 0.20939518960920653, 0.20939518960920653, 0.20939518960920653, 0.20939518960920653, 0.20939518960920653, 0.20939518960920653, 0.20939518960920653, 0.20939518960920653, 0.20939518960920653, 0.20939518960920653, 0.20939518960920653, 0.20939518960920653, 0.20939518960920653, 0.20939518960920653, 0.20939518960920653, 0.20939518960920653, 0.20939518960920653, 0.20939518960920653, 0.20939518960920653, 0.20939518960920653, 0.20939518960920653, 0.20939518960920653]})
        self.smr_consumption = pd.DataFrame({'years': self.years, 'methane (TWh)': [2136.893073963169, 2172.719258968549, 2136.845263236073, 2124.2442018929078, 2070.3842437060734, 1995.4167284233306, 1972.7661968641671, 1909.520797917822, 1797.9931475815704, 1636.221782768063, 1521.072721706902, 1421.3538400958328, 1308.3089031297163, 1274.6597577837158, 1287.3794573403693, 1098.639970325437, 1006.663566604059, 964.567208460359, 893.0737042575123, 870.7008285810414, 853.3177841161436, 801.0961230723251, 727.1958842518671, 600.3933188764174, 546.8800253309834, 426.2424496668787, 305.5032203873456, 318.52279769889736, 319.11105404286803, 319.6970312930814, 320.280751213928], 'water (Mt)': [
            172.6651314945873, 175.55995717411028, 172.6612682945136, 171.6430779412856, 167.29108818759377, 161.23356661955842, 159.4033594567677, 154.29300776975273, 145.28135592566838, 132.20991387836986, 122.9056449788834, 114.84816469797474, 105.71391313252265, 102.99499650696022, 104.02277305941448, 88.77225409768941, 81.34038114323354, 77.93891323504073, 72.16209854337303, 70.35432651787556, 68.94974259419743, 64.730130447543, 58.75884690093551, 48.51295210574259, 44.188973531749575, 34.44122193901366, 24.685256535727856, 25.737263796125664, 25.784796056968197, 25.832144162586452, 25.87930987158567]})
        self.smr_production = pd.DataFrame({'years': self.years, 'methane (TWh)': [2136.893073963169, 2172.719258968549, 2136.845263236073, 2124.2442018929078, 2070.3842437060734, 1995.4167284233306, 1972.7661968641671, 1909.520797917822, 1797.9931475815704, 1636.221782768063, 1521.072721706902, 1421.3538400958328, 1308.3089031297163, 1274.6597577837158, 1287.3794573403693, 1098.639970325437, 1006.663566604059, 964.567208460359, 893.0737042575123, 870.7008285810414, 853.3177841161436, 801.0961230723251, 727.1958842518671, 600.3933188764174, 546.8800253309834, 426.2424496668787, 305.5032203873456, 318.52279769889736, 319.11105404286803, 319.6970312930814, 320.280751213928], 'water (Mt)': [172.6651314945873, 175.55995717411028, 172.6612682945136, 171.6430779412856, 167.29108818759377, 161.23356661955842, 159.4033594567677, 154.29300776975273, 145.28135592566838, 132.20991387836986, 122.9056449788834, 114.84816469797474, 105.71391313252265, 102.99499650696022,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         104.02277305941448, 88.77225409768941, 81.34038114323354, 77.93891323504073, 72.16209854337303, 70.35432651787556, 68.94974259419743, 64.730130447543, 58.75884690093551, 48.51295210574259, 44.188973531749575, 34.44122193901366, 24.685256535727856, 25.737263796125664, 25.784796056968197, 25.832144162586452, 25.87930987158567], 'syngas (TWh)': [3056.4928611111104, 3107.736641178544, 3056.4244753093903, 3038.400618848301, 2961.3623338242933, 2854.132974494688, 2821.7349154366575, 2731.2722185741004, 2571.7492778978817, 2340.3605258310063, 2175.6577209104307, 2033.02538545298, 1871.332202470795, 1823.2023387047088, 1841.3958886600585, 1571.4334363034664, 1439.8755100831906, 1379.6632235103466, 1277.4028961807517, 1245.4019806361873, 1220.538241800253, 1145.8432857818095, 1040.1404992730686, 858.7691707012409, 782.2267354764349, 609.6734648931626, 436.97479463891517, 455.5972730363196, 456.4386821539574, 457.27683138279497, 458.11175185340477]})
        self.smr_techno_prices = pd.DataFrame({'years': self.years, 'methane (TWh)': [2136.893073963169, 2172.719258968549, 2136.845263236073, 2124.2442018929078, 2070.3842437060734, 1995.4167284233306, 1972.7661968641671, 1909.520797917822, 1797.9931475815704, 1636.221782768063, 1521.072721706902, 1421.3538400958328, 1308.3089031297163, 1274.6597577837158, 1287.3794573403693, 1098.639970325437, 1006.663566604059, 964.567208460359, 893.0737042575123, 870.7008285810414, 853.3177841161436, 801.0961230723251, 727.1958842518671, 600.3933188764174, 546.8800253309834, 426.2424496668787, 305.5032203873456, 318.52279769889736, 319.11105404286803, 319.6970312930814, 320.280751213928], 'water (Mt)': [172.6651314945873, 175.55995717411028, 172.6612682945136, 171.6430779412856, 167.29108818759377, 161.23356661955842, 159.4033594567677, 154.29300776975273, 145.28135592566838, 132.20991387836986, 122.9056449788834, 114.84816469797474, 105.71391313252265, 102.99499650696022, 104.02277305941448, 88.77225409768941, 81.34038114323354, 77.93891323504073, 72.16209854337303, 70.35432651787556, 68.94974259419743, 64.730130447543, 58.75884690093551, 48.51295210574259, 44.188973531749575, 34.44122193901366, 24.685256535727856, 25.737263796125664, 25.784796056968197, 25.832144162586452, 25.87930987158567], 'syngas (TWh)': [3056.4928611111104, 3107.736641178544, 3056.4244753093903, 3038.400618848301, 2961.3623338242933, 2854.132974494688, 2821.7349154366575, 2731.2722185741004, 2571.7492778978817, 2340.3605258310063, 2175.6577209104307, 2033.02538545298, 1871.332202470795,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        1823.2023387047088, 1841.3958886600585, 1571.4334363034664, 1439.8755100831906, 1379.6632235103466, 1277.4028961807517, 1245.4019806361873, 1220.538241800253, 1145.8432857818095, 1040.1404992730686, 858.7691707012409, 782.2267354764349, 609.6734648931626, 436.97479463891517, 455.5972730363196, 456.4386821539574, 457.27683138279497, 458.11175185340477], 'SMR': [9.969986883747492, 9.953065724531859, 9.936345444392789, 9.919822132909381, 9.90349200553949, 9.887351397659122, 9.881793751760116, 9.876363084250082, 9.871057648924872, 9.865875733735196, 9.86081565992257, 9.854027501319644, 9.847390126221091, 9.840902678005708, 9.83456435427118, 9.828374407155977, 9.822320091772573, 9.816412822601892, 9.810652018158793, 9.805037153625978, 9.799567761613694, 9.79494244724187, 9.7904618464362, 9.78612566967081, 9.781933688936437, 9.777885739054392, 9.773969667151508, 9.770197490150824, 9.766569240593245, 9.763085020493312, 9.759745003392808], 'SMR_wotaxes': [9.866219427584232, 9.845622417714731, 9.825226286921794, 9.80502712478452, 9.785021146760762, 9.765204688226527, 9.749113621109554, 9.733149532381555, 9.717310675838378, 9.701595339430735, 9.686001844400144, 9.673139493241319, 9.660427925586868, 9.647866284815587, 9.63545376852516, 9.623189628854059, 9.611073172884115, 9.599103763126893, 9.587280818097252, 9.575603812977896, 9.56407228037907, 9.552685811198002, 9.541444055583089, 9.530346724008455, 9.519393588464839, 9.50858448377355, 9.49791930903078, 9.487398029190208, 9.477020676792742, 9.466787353852922, 9.456698233912531]})
        self.smr_carbon_emissions = pd.DataFrame({'years': self.years, 'methane (TWh)': [2136.893073963169, 2172.719258968549, 2136.845263236073, 2124.2442018929078, 2070.3842437060734, 1995.4167284233306, 1972.7661968641671, 1909.520797917822, 1797.9931475815704, 1636.221782768063, 1521.072721706902, 1421.3538400958328, 1308.3089031297163, 1274.6597577837158, 1287.3794573403693, 1098.639970325437, 1006.663566604059, 964.567208460359, 893.0737042575123, 870.7008285810414, 853.3177841161436, 801.0961230723251, 727.1958842518671, 600.3933188764174, 546.8800253309834, 426.2424496668787, 305.5032203873456, 318.52279769889736, 319.11105404286803, 319.6970312930814, 320.280751213928], 'water (Mt)': [172.6651314945873, 175.55995717411028, 172.6612682945136, 171.6430779412856, 167.29108818759377, 161.23356661955842, 159.4033594567677, 154.29300776975273, 145.28135592566838, 132.20991387836986, 122.9056449788834, 114.84816469797474, 105.71391313252265, 102.99499650696022, 104.02277305941448, 88.77225409768941, 81.34038114323354, 77.93891323504073, 72.16209854337303, 70.35432651787556, 68.94974259419743, 64.730130447543, 58.75884690093551, 48.51295210574259, 44.188973531749575, 34.44122193901366, 24.685256535727856, 25.737263796125664, 25.784796056968197, 25.832144162586452, 25.87930987158567], 'syngas (TWh)': [3056.4928611111104, 3107.736641178544, 3056.4244753093903, 3038.400618848301, 2961.3623338242933, 2854.132974494688, 2821.7349154366575, 2731.2722185741004, 2571.7492778978817, 2340.3605258310063, 2175.6577209104307, 2033.02538545298, 1871.332202470795, 1823.2023387047088, 1841.3958886600585, 1571.4334363034664, 1439.8755100831906, 1379.6632235103466, 1277.4028961807517, 1245.4019806361873, 1220.538241800253, 1145.8432857818095, 1040.1404992730686, 858.7691707012409, 782.2267354764349, 609.6734648931626, 436.97479463891517, 455.5972730363196, 456.4386821539574, 457.27683138279497, 458.11175185340477], 'SMR': [0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064], 'SMR_wotaxes': [9.866219427584232, 9.845622417714731, 9.825226286921794, 9.80502712478452, 9.785021146760762, 9.765204688226527, 9.749113621109554, 9.733149532381555, 9.717310675838378, 9.701595339430735, 9.686001844400144, 9.673139493241319, 9.660427925586868, 9.647866284815587, 9.63545376852516, 9.623189628854059, 9.611073172884115, 9.599103763126893, 9.587280818097252, 9.575603812977896, 9.56407228037907, 9.552685811198002, 9.541444055583089, 9.530346724008455, 9.519393588464839, 9.50858448377355, 9.49791930903078, 9.487398029190208, 9.477020676792742, 9.466787353852922, 9.456698233912531], 'production': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'methane': [0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028], 'electricity': [0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873]})
        self.AutothermalReforming_consumption = pd.DataFrame({'years': self.years, 'methane (TWh)': [1.2472228306010904e-12, 1.2472228306010904e-12, 1.2472228306010904e-12, 1.2472228306010904e-12, 1829049.8492991452, 4115362.16092307, 6720461.43907915, 9578351.828609051, 12649095.912929239, 15905470.010624332, 19327519.957208224, 22899882.944120593, 26610302.45600531, 30448732.561405543, 34406762.77576849, 38477230.39788736, 42653948.87172739, 46931511.304957256, 51305144.53345011, 53941548.41779143, 56208697.08384439, 58241622.195544206, 60103191.18676079, 61830484.73419089, 63448105.65039645, 64973593.471766226, 66420077.87331949, 67797742.88908336, 69114704.93168864, 70377572.80962573, 71591822.38412726], 'water (Mt)': [172.6651314945873, 175.55995717411028, 172.6612682945136, 171.6430779412856, 167.29108818759377, 161.23356661955842, 159.4033594567677, 154.29300776975273, 145.28135592566838, 132.20991387836986, 122.9056449788834, 114.84816469797474, 105.71391313252265, 102.99499650696022, 104.02277305941448, 88.77225409768941, 81.34038114323354, 77.93891323504073, 72.16209854337303, 70.35432651787556, 68.94974259419743, 64.730130447543, 58.75884690093551, 48.51295210574259, 44.188973531749575, 34.44122193901366, 24.685256535727856, 25.737263796125664, 25.784796056968197, 25.832144162586452, 25.87930987158567], 'syngas (TWh)': [3056.4928611111104, 3107.736641178544, 3056.4244753093903, 3038.400618848301, 2961.3623338242933, 2854.132974494688, 2821.7349154366575, 2731.2722185741004, 2571.7492778978817, 2340.3605258310063, 2175.6577209104307, 2033.02538545298, 1871.332202470795, 1823.2023387047088, 1841.3958886600585, 1571.4334363034664, 1439.8755100831906, 1379.6632235103466, 1277.4028961807517, 1245.4019806361873, 1220.538241800253, 1145.8432857818095, 1040.1404992730686, 858.7691707012409, 782.2267354764349, 609.6734648931626, 436.97479463891517, 455.5972730363196, 456.4386821539574, 457.27683138279497, 458.11175185340477], 'SMR': [0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064], 'SMR_wotaxes': [9.866219427584232, 9.845622417714731, 9.825226286921794, 9.80502712478452, 9.785021146760762, 9.765204688226527, 9.749113621109554, 9.733149532381555, 9.717310675838378, 9.701595339430735, 9.686001844400144, 9.673139493241319, 9.660427925586868, 9.647866284815587, 9.63545376852516, 9.623189628854059, 9.611073172884115,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            9.599103763126893, 9.587280818097252, 9.575603812977896, 9.56407228037907, 9.552685811198002, 9.541444055583089, 9.530346724008455, 9.519393588464839, 9.50858448377355, 9.49791930903078, 9.487398029190208, 9.477020676792742, 9.466787353852922, 9.456698233912531], 'production': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'methane': [0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028], 'electricity': [0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873], 'carbon_capture (Mt)': [1.2309665757986776e-13, 1.2309665757986776e-13, 1.2309665757986776e-13, 1.2309665757986776e-13, 180521.00833271, 406172.2687485968, 663286.7201014402, 945350.795621298, 1248422.807926263, 1569815.8721173168, 1907560.57992773, 2260140.6743275523, 2626346.478876536, 3005186.494257741, 3395830.634209376, 3797571.964448193, 4209799.892904256, 4631980.777667272, 5063643.523648476, 5323847.633315545, 5547607.506996878, 5748250.311330264, 5931980.848529177, 6102458.85545072, 6262112.546139032, 6412673.013268161, 6555436.11117169, 6691406.969421227, 6821386.650378588, 6946027.420997032, 7065869.730183177], 'dioxygen (Mt)': [8.391046869793303e-14, 8.391046869793303e-14, 8.391046869793303e-14, 8.391046869793303e-14, 123054.53874077028, 276872.7121667327, 452138.1868448809, 644410.9036273335, 851003.9590499408, 1070085.8023976258, 1300313.9604142674, 1540654.8563923328, 1790283.8983480136, 2048525.2176262722, 2314812.9749211837, 2588665.2791057895, 2869665.912000175, 3157451.1095209764, 3451699.743454994, 3629071.324686806, 3781600.209268493, 3918371.037034946, 4043613.3936804207, 4159821.987355638, 4268652.0423578955, 4371283.580959892, 4468599.939449005, 4561286.277724083, 4649888.650564819, 4734851.684387889, 4816543.783355949]})
        self.AutothermalReforming_production = pd.DataFrame({'years': self.years, 'methane (TWh)': [1.2472228306010904e-12, 1.2472228306010904e-12, 1.2472228306010904e-12, 1.2472228306010904e-12, 1829049.8492991452, 4115362.16092307, 6720461.43907915, 9578351.828609051, 12649095.912929239, 15905470.010624332, 19327519.957208224, 22899882.944120593, 26610302.45600531, 30448732.561405543, 34406762.77576849, 38477230.39788736, 42653948.87172739, 46931511.304957256, 51305144.53345011, 53941548.41779143, 56208697.08384439, 58241622.195544206, 60103191.18676079, 61830484.73419089, 63448105.65039645, 64973593.471766226, 66420077.87331949, 67797742.88908336, 69114704.93168864, 70377572.80962573, 71591822.38412726], 'water (Mt)': [3.023341177048998e-14, 3.023341177048998e-14, 3.023341177048998e-14, 3.023341177048998e-14, 44337.23941371648, 99758.78868086192, 162907.9206940569, 232184.85727798857, 306621.49206786434, 385557.907084358, 468510.40169543884, 555106.5724253533, 645049.31416462, 738095.1076519646, 834040.077816762, 932710.596587379, 1033956.6982227702, 1137647.3164866213, 1243666.7470853978, 1307574.7210840746, 1362531.7323606098, 1411811.0275214983, 1456936.5499780604, 1498807.1570473653, 1538019.235312987, 1574997.9534079025, 1610061.5823431376, 1643456.9890671421, 1675380.9201749472, 1705993.5770543888, 1735427.6977883352], 'syngas (TWh)': [1e-12, 1e-12, 1e-12, 1e-12, 1466498.0502462797, 3299620.6130541237, 5388340.619005723, 7679743.822515524, 10141809.147955617, 12752709.155395113, 15496444.96797213, 18360698.972359378, 21335644.123176176, 24413225.77997629, 27586700.573133662, 30850325.58243303, 34199140.54264916, 37628810.30837043, 41135507.8456381, 43249327.30087588, 45067084.81014175, 46697046.24271115, 48189617.53433785, 49574529.2798979, 50871507.55556493, 52094615.23443462, 53254379.44501769, 54358965.5558251, 55414881.15510143, 56427425.06221422, 57400987.72055357], 'SMR': [0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064], 'SMR_wotaxes': [9.866219427584232, 9.845622417714731, 9.825226286921794, 9.80502712478452, 9.785021146760762, 9.765204688226527, 9.749113621109554, 9.733149532381555, 9.717310675838378, 9.701595339430735, 9.686001844400144, 9.673139493241319, 9.660427925586868, 9.647866284815587, 9.63545376852516, 9.623189628854059, 9.611073172884115, 9.599103763126893,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           9.587280818097252, 9.575603812977896, 9.56407228037907, 9.552685811198002, 9.541444055583089, 9.530346724008455, 9.519393588464839, 9.50858448377355, 9.49791930903078, 9.487398029190208, 9.477020676792742, 9.466787353852922, 9.456698233912531], 'production': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'methane': [0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028], 'electricity': [0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873], 'carbon_capture (Mt)': [1.2309665757986776e-13, 1.2309665757986776e-13, 1.2309665757986776e-13, 1.2309665757986776e-13, 180521.00833271, 406172.2687485968, 663286.7201014402, 945350.795621298, 1248422.807926263, 1569815.8721173168, 1907560.57992773, 2260140.6743275523, 2626346.478876536, 3005186.494257741, 3395830.634209376, 3797571.964448193, 4209799.892904256, 4631980.777667272, 5063643.523648476, 5323847.633315545, 5547607.506996878, 5748250.311330264, 5931980.848529177, 6102458.85545072, 6262112.546139032, 6412673.013268161, 6555436.11117169, 6691406.969421227, 6821386.650378588, 6946027.420997032, 7065869.730183177], 'dioxygen (Mt)': [8.391046869793303e-14, 8.391046869793303e-14, 8.391046869793303e-14, 8.391046869793303e-14, 123054.53874077028, 276872.7121667327, 452138.1868448809, 644410.9036273335, 851003.9590499408, 1070085.8023976258, 1300313.9604142674, 1540654.8563923328, 1790283.8983480136, 2048525.2176262722, 2314812.9749211837, 2588665.2791057895, 2869665.912000175, 3157451.1095209764, 3451699.743454994, 3629071.324686806, 3781600.209268493, 3918371.037034946, 4043613.3936804207, 4159821.987355638, 4268652.0423578955, 4371283.580959892, 4468599.939449005, 4561286.277724083, 4649888.650564819, 4734851.684387889, 4816543.783355949]})
        self.AutothermalReforming_techno_prices = pd.DataFrame({'years': self.years, 'methane (TWh)': [1.2472228306010904e-12, 1.2472228306010904e-12, 1.2472228306010904e-12, 1.2472228306010904e-12, 1829049.8492991452, 4115362.16092307, 6720461.43907915, 9578351.828609051, 12649095.912929239, 15905470.010624332, 19327519.957208224, 22899882.944120593, 26610302.45600531, 30448732.561405543, 34406762.77576849, 38477230.39788736, 42653948.87172739, 46931511.304957256, 51305144.53345011, 53941548.41779143, 56208697.08384439, 58241622.195544206, 60103191.18676079, 61830484.73419089, 63448105.65039645, 64973593.471766226, 66420077.87331949, 67797742.88908336, 69114704.93168864, 70377572.80962573, 71591822.38412726], 'water (Mt)': [3.023341177048998e-14, 3.023341177048998e-14, 3.023341177048998e-14, 3.023341177048998e-14, 44337.23941371648, 99758.78868086192, 162907.9206940569, 232184.85727798857, 306621.49206786434, 385557.907084358, 468510.40169543884, 555106.5724253533, 645049.31416462, 738095.1076519646, 834040.077816762, 932710.596587379, 1033956.6982227702, 1137647.3164866213, 1243666.7470853978, 1307574.7210840746, 1362531.7323606098, 1411811.0275214983, 1456936.5499780604, 1498807.1570473653, 1538019.235312987, 1574997.9534079025, 1610061.5823431376, 1643456.9890671421, 1675380.9201749472, 1705993.5770543888, 1735427.6977883352], 'syngas (TWh)': [1e-12, 1e-12, 1e-12, 1e-12, 1466498.0502462797, 3299620.6130541237, 5388340.619005723, 7679743.822515524, 10141809.147955617, 12752709.155395113, 15496444.96797213, 18360698.972359378, 21335644.123176176, 24413225.77997629, 27586700.573133662, 30850325.58243303, 34199140.54264916, 37628810.30837043, 41135507.8456381, 43249327.30087588, 45067084.81014175, 46697046.24271115, 48189617.53433785, 49574529.2798979, 50871507.55556493, 52094615.23443462, 53254379.44501769, 54358965.5558251, 55414881.15510143, 56427425.06221422, 57400987.72055357], 'SMR': [0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064], 'SMR_wotaxes': [9.866219427584232, 9.845622417714731, 9.825226286921794, 9.80502712478452, 9.785021146760762, 9.765204688226527, 9.749113621109554, 9.733149532381555, 9.717310675838378, 9.701595339430735, 9.686001844400144, 9.673139493241319, 9.660427925586868, 9.647866284815587, 9.63545376852516, 9.623189628854059, 9.611073172884115, 9.599103763126893, 9.587280818097252, 9.575603812977896, 9.56407228037907, 9.552685811198002, 9.541444055583089, 9.530346724008455, 9.519393588464839, 9.50858448377355, 9.49791930903078, 9.487398029190208, 9.477020676792742, 9.466787353852922, 9.456698233912531], 'production': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'methane': [0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028, 0.005583979256342028], 'electricity': [0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873], 'carbon_capture (Mt)': [1.2309665757986776e-13, 1.2309665757986776e-13, 1.2309665757986776e-13, 1.2309665757986776e-13, 180521.00833271, 406172.2687485968, 663286.7201014402, 945350.795621298, 1248422.807926263, 1569815.8721173168, 1907560.57992773, 2260140.6743275523, 2626346.478876536, 3005186.494257741, 3395830.634209376, 3797571.964448193, 4209799.892904256, 4631980.777667272, 5063643.523648476, 5323847.633315545, 5547607.506996878, 5748250.311330264, 5931980.848529177, 6102458.85545072, 6262112.546139032, 6412673.013268161, 6555436.11117169, 6691406.969421227, 6821386.650378588, 6946027.420997032, 7065869.730183177], 'dioxygen (Mt)': [8.391046869793303e-14, 8.391046869793303e-14, 8.391046869793303e-14, 8.391046869793303e-14, 123054.53874077028, 276872.7121667327, 452138.1868448809, 644410.9036273335, 851003.9590499408, 1070085.8023976258, 1300313.9604142674, 1540654.8563923328, 1790283.8983480136, 2048525.2176262722, 2314812.9749211837, 2588665.2791057895, 2869665.912000175, 3157451.1095209764, 3451699.743454994, 3629071.324686806, 3781600.209268493, 3918371.037034946, 4043613.3936804207, 4159821.987355638, 4268652.0423578955, 4371283.580959892, 4468599.939449005, 4561286.277724083, 4649888.650564819, 4734851.684387889, 4816543.783355949], 'AutothermalReforming': [12.579640876545561, 10.124093796555668, 10.247171026602603, 10.370258174764777, 10.493348799735987, 10.616441148031017, 10.788773170393517, 10.961105849498313, 11.133438985530223, 11.30577245563159, 11.478106179325982, 11.74891742734208, 12.019728834077949, 12.290540370387767, 12.561352014223752, 12.832163748540234, 13.102975559911245, 13.373787437590376, 13.644599372854303, 13.915411358533802, 14.186223388671785, 14.72784810494528, 15.269472856446932, 15.811097639565736, 16.352722451197895, 16.8943472886579, 17.460591481123995, 18.02683569503386, 18.593079928586995, 19.159324180191653, 19.725568448434398], 'AutothermalReforming_wotaxes': [12.579640876545561, 10.124093796555668, 10.247171026602603, 10.370258174764777, 10.493348799735987, 10.616441148031017, 10.788773170393517, 10.961105849498313, 11.133438985530223, 11.30577245563159, 11.478106179325982, 11.74891742734208, 12.019728834077949, 12.290540370387767, 12.561352014223752, 12.832163748540234, 13.102975559911245, 13.373787437590376, 13.644599372854303, 13.915411358533802, 14.186223388671785, 14.72784810494528, 15.269472856446932, 15.811097639565736, 16.352722451197895, 16.8943472886579, 17.460591481123995, 18.02683569503386, 18.593079928586995, 19.159324180191653, 19.725568448434398]})
        self.AutothermalReforming_carbon_emissions = pd.DataFrame({'years':  self.years, 'methane (TWh)': [1.2472228306010904e-12, 1.2472228306010904e-12, 1.2472228306010904e-12, 1.2472228306010904e-12, 1829049.8492991452, 4115362.16092307, 6720461.43907915, 9578351.828609051, 12649095.912929239, 15905470.010624332, 19327519.957208224, 22899882.944120593, 26610302.45600531, 30448732.561405543, 34406762.77576849, 38477230.39788736, 42653948.87172739, 46931511.304957256, 51305144.53345011, 53941548.41779143, 56208697.08384439, 58241622.195544206, 60103191.18676079, 61830484.73419089, 63448105.65039645, 64973593.471766226, 66420077.87331949, 67797742.88908336, 69114704.93168864, 70377572.80962573, 71591822.38412726], 'water (Mt)': [3.023341177048998e-14, 3.023341177048998e-14, 3.023341177048998e-14, 3.023341177048998e-14, 44337.23941371648, 99758.78868086192, 162907.9206940569, 232184.85727798857, 306621.49206786434, 385557.907084358, 468510.40169543884, 555106.5724253533, 645049.31416462, 738095.1076519646, 834040.077816762, 932710.596587379, 1033956.6982227702, 1137647.3164866213, 1243666.7470853978, 1307574.7210840746, 1362531.7323606098, 1411811.0275214983, 1456936.5499780604, 1498807.1570473653, 1538019.235312987, 1574997.9534079025, 1610061.5823431376, 1643456.9890671421, 1675380.9201749472, 1705993.5770543888, 1735427.6977883352], 'syngas (TWh)': [1e-12, 1e-12, 1e-12, 1e-12, 1466498.0502462797, 3299620.6130541237, 5388340.619005723, 7679743.822515524, 10141809.147955617, 12752709.155395113, 15496444.96797213, 18360698.972359378, 21335644.123176176, 24413225.77997629, 27586700.573133662, 30850325.58243303, 34199140.54264916, 37628810.30837043, 41135507.8456381, 43249327.30087588, 45067084.81014175, 46697046.24271115, 48189617.53433785, 49574529.2798979, 50871507.55556493, 52094615.23443462, 53254379.44501769, 54358965.5558251, 55414881.15510143, 56427425.06221422, 57400987.72055357], 'SMR': [0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064, 0.0060259846784704064], 'SMR_wotaxes': [9.866219427584232, 9.845622417714731, 9.825226286921794, 9.80502712478452, 9.785021146760762, 9.765204688226527, 9.749113621109554, 9.733149532381555, 9.717310675838378, 9.701595339430735, 9.686001844400144, 9.673139493241319, 9.660427925586868, 9.647866284815587, 9.63545376852516, 9.623189628854059, 9.611073172884115, 9.599103763126893, 9.587280818097252, 9.575603812977896, 9.56407228037907, 9.552685811198002, 9.541444055583089, 9.530346724008455, 9.519393588464839, 9.50858448377355, 9.49791930903078, 9.487398029190208, 9.477020676792742, 9.466787353852922, 9.456698233912531], 'production': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'methane': [0.009961584945710008, 0.009961584945710008, 0.009961584945710008, 0.009961584945710008, 0.009961584945710008, 0.009961584945710008, 0.009961584945710008, 0.009961584945710008, 0.009961584945710008, 0.009961584945710008, 0.009961584945710008, 0.009961584945710008, 0.009961584945710008, 0.009961584945710008, 0.009961584945710008, 0.009961584945710008, 0.009961584945710008, 0.009961584945710008, 0.009961584945710008, 0.009961584945710008, 0.009961584945710008, 0.009961584945710008, 0.009961584945710008, 0.009961584945710008, 0.009961584945710008, 0.009961584945710008, 0.009961584945710008, 0.009961584945710008, 0.009961584945710008, 0.009961584945710008, 0.009961584945710008], 'electricity': [
            0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873, 0.00044200542212837873], 'carbon_capture (Mt)': [1.2309665757986776e-13, 1.2309665757986776e-13, 1.2309665757986776e-13, 1.2309665757986776e-13, 180521.00833271, 406172.2687485968, 663286.7201014402, 945350.795621298, 1248422.807926263, 1569815.8721173168, 1907560.57992773, 2260140.6743275523, 2626346.478876536, 3005186.494257741, 3395830.634209376, 3797571.964448193, 4209799.892904256, 4631980.777667272, 5063643.523648476, 5323847.633315545, 5547607.506996878, 5748250.311330264, 5931980.848529177, 6102458.85545072, 6262112.546139032, 6412673.013268161, 6555436.11117169, 6691406.969421227, 6821386.650378588, 6946027.420997032, 7065869.730183177], 'dioxygen (Mt)': [8.391046869793303e-14, 8.391046869793303e-14, 8.391046869793303e-14, 8.391046869793303e-14, 123054.53874077028, 276872.7121667327, 452138.1868448809, 644410.9036273335, 851003.9590499408, 1070085.8023976258, 1300313.9604142674, 1540654.8563923328, 1790283.8983480136, 2048525.2176262722, 2314812.9749211837, 2588665.2791057895, 2869665.912000175, 3157451.1095209764, 3451699.743454994, 3629071.324686806, 3781600.209268493, 3918371.037034946, 4043613.3936804207, 4159821.987355638, 4268652.0423578955, 4371283.580959892, 4468599.939449005, 4561286.277724083, 4649888.650564819, 4734851.684387889, 4816543.783355949], 'AutothermalReforming': [-0.11313507263415774, -0.11313507263415774, -0.11313507263415774, -0.11313507263415774, -0.11313507263415774, -0.11313507263415774, -0.11313507263415774, -0.11313507263415774, -0.11313507263415774, -0.11313507263415774, -0.11313507263415774, -0.11313507263415774, -0.11313507263415774, -0.11313507263415774, -0.11313507263415774, -0.11313507263415774, -0.11313507263415774, -0.11313507263415774, -0.11313507263415774, -0.11313507263415774, -0.11313507263415774, -0.11313507263415774, -0.11313507263415774, -0.11313507263415774, -0.11313507263415774, -0.11313507263415774, -0.11313507263415774, -0.11313507263415774, -0.11313507263415774, -0.11313507263415774, -0.11313507263415774], 'AutothermalReforming_wotaxes': [12.579640876545561, 10.124093796555668, 10.247171026602603, 10.370258174764777, 10.493348799735987, 10.616441148031017, 10.788773170393517, 10.961105849498313, 11.133438985530223, 11.30577245563159, 11.478106179325982, 11.74891742734208, 12.019728834077949, 12.290540370387767, 12.561352014223752, 12.832163748540234, 13.102975559911245, 13.373787437590376, 13.644599372854303, 13.915411358533802, 14.186223388671785, 14.72784810494528, 15.269472856446932, 15.811097639565736, 16.352722451197895, 16.8943472886579, 17.460591481123995, 18.02683569503386, 18.593079928586995, 19.159324180191653, 19.725568448434398], 'CO2': [-0.12309665757986775, -0.12309665757986775, -0.12309665757986775, -0.12309665757986775, -0.12309665757986775, -0.12309665757986775, -0.12309665757986775, -0.12309665757986775, -0.12309665757986775, -0.12309665757986775, -0.12309665757986775, -0.12309665757986775, -0.12309665757986775, -0.12309665757986775, -0.12309665757986775, -0.12309665757986775, -0.12309665757986775, -0.12309665757986775, -0.12309665757986775, -0.12309665757986775, -0.12309665757986775, -0.12309665757986775, -0.12309665757986775, -0.12309665757986775, -0.12309665757986775, -0.12309665757986775, -0.12309665757986775, -0.12309665757986775, -0.12309665757986775, -0.12309665757986775, -0.12309665757986775]})

        self.BiomassGasification_consumption = pd.DataFrame({'years': self.years, 'electricity (TWh)': [1.1179522967999008e-13, 1.063312543802752e-13, 1.0432926795430603e-13, 1.0293105521242787e-13, 5895.027161414338, 13263.811113181993, 21660.045370435742, 30871.025310145145, 40768.03264964183, 51263.32547120889, 62292.59150819377, 73806.31643283041, 85764.99749949579, 98136.25667386655, 110892.9869665414, 124012.10299350016, 137473.66548634376, 151260.2480325747, 165356.46672552478, 179748.62288132054, 194424.42636044903, 209372.77769378072, 224583.59398036308, 240047.6679483264, 255756.5525380768, 271702.4654039204, 287878.20915706805, 304277.10419076646, 320892.9316663697, 331824.8576210097, 341488.71574097464], 'biomass_dry (TWh)': [1.5300368073299489e-12, 1.4552564848883214e-12, 1.427857168045592e-12, 1.4087211372357353e-12, 80679.72634424597, 181529.38427454978, 296440.7941203515, 422502.86653322895, 557953.9546985314, 701593.2170057818, 852540.4715776057, 1010118.0620937011, 1173785.3514001674,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            1343099.2116067943, 1517688.6546880763, 1697237.7325721383, 1881473.55513076, 2070157.6233455378, 2263079.392066108, 2460051.3802112266, 2660905.384129666, 2865489.495762748, 3073665.719870193, 3285308.0451284745, 3500300.8645288744, 3718537.668380477, 3939919.9527507317, 4164356.3001058083, 4391761.599014262, 4541376.650868289, 4673636.843603573], 'water (Mt)': [4.468830305906666e-13, 4.25041688630025e-13, 4.170390773933972e-13, 4.114499520855502e-13, 23564.40083219987, 53019.901872448645, 86582.46640378943, 123401.84270409972, 162963.5006237844, 204916.70628795985, 249004.38199565336, 295028.6023710408, 342831.46169013734, 392283.5340897428, 443276.46384118695, 495717.970921406, 549528.3513867215, 604637.9460213378, 660985.2601903415, 718515.5356595756, 777179.6446191358, 836933.2187680063, 897735.953369145, 959551.0438686514, 1022344.724536076, 1086085.8867253812, 1150745.7600594803, 1216297.643909754, 1282716.6794922561, 1326415.2542416998, 1365044.9365296653]})
        self.BiomassGasification_production = pd.DataFrame({'years': self.years, 'syngas (TWh)': [9.999999999999998e-13, 9.511251480465191e-13, 9.332175286275173e-13, 9.207106198275578e-13, 52730.57874015416, 118643.80216534447, 193747.49202123255, 276139.02130271896, 364667.0145617025, 458546.6268815615, 557202.5898287799, 660192.001430637, 767161.5125707516,
                                                                                                  877821.5041444802, 991929.5061512791, 1109279.0215511022, 1229691.6950737278, 1353011.6487577495, 1479101.2747042233, 1607838.0392065442, 1739112.0078824658, 1872823.896807609, 2008883.515184196, 2147208.5046513556, 2287723.3068903824, 2430358.309398881, 2575049.132070387, 2721736.026320165, 2870363.3650998743, 2968148.6282630004, 3054591.1191244386]})
        self.BiomassGasification_techno_prices = pd.DataFrame({'years': self.years, 'BiomassGasification': [3134.6106061511327, 3112.0020261822406, 3111.973198301283, 3111.945040997693, 3111.9174131376644, 3111.8902664725356, 3111.8904303264153, 3111.8906071374254, 3111.8907929729344, 3111.890985414941, 3111.8911828795663, 3111.9111956831803, 3111.9314559934314, 3111.951968754458, 3111.972739233163, 3111.9937729860185, 3112.0150758403574, 3112.03665388484, 3112.058513466008, 3112.0806611890735, 3112.10310392177, 3112.1258488005737, 3112.148903238795, 3112.172274936266, 3112.1959718904395, 3112.2200024087692, 3112.2443751223313, 3112.2690990006568, 3112.294183367779, 3112.319637919537, 3112.345472742165], 'BiomassGasification_wotaxes': [
                                                              3134.6106061511327, 3112.0020261822406, 3111.973198301283, 3111.945040997693, 3111.9174131376644, 3111.8902664725356, 3111.8904303264153, 3111.8906071374254, 3111.8907929729344, 3111.890985414941, 3111.8911828795663, 3111.9111956831803, 3111.9314559934314, 3111.951968754458, 3111.972739233163, 3111.9937729860185, 3112.0150758403574, 3112.03665388484, 3112.058513466008, 3112.0806611890735, 3112.10310392177, 3112.1258488005737, 3112.148903238795, 3112.172274936266, 3112.1959718904395, 3112.2200024087692, 3112.2443751223313, 3112.2690990006568, 3112.294183367779, 3112.319637919537, 3112.345472742165]})
        self.BiomassGasification_carbon_emissions = pd.DataFrame({'years': self.years, 'production': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'electricity': [0.003353856890399703, 0.003353856890399703, 0.003353856890399703, 0.003353856890399703, 0.003353856890399703, 0.003353856890399703, 0.003353856890399703, 0.003353856890399703, 0.003353856890399703, 0.003353856890399703, 0.003353856890399703, 0.003353856890399703, 0.003353856890399703, 0.003353856890399703, 0.003353856890399703, 0.003353856890399703, 0.003353856890399703, 0.003353856890399703, 0.003353856890399703, 0.003353856890399703, 0.003353856890399703, 0.003353856890399703, 0.003353856890399703, 0.003353856890399703, 0.003353856890399703, 0.003353856890399703, 0.003353856890399703, 0.003353856890399703, 0.003353856890399703, 0.003353856890399703, 0.003353856890399703], 'biomass_dry': [-2.3848492461251, -2.3848492461251, -2.3848492461251, -2.3848492461251, -2.3848492461251, -2.3848492461251, -2.3848492461251, -2.3848492461251, -2.3848492461251, -2.3848492461251, -2.3848492461251, -2.3848492461251, -2.3848492461251, -2.3848492461251, -2.3848492461251, -2.3848492461251, -2.3848492461251, -2.3848492461251, -2.3848492461251, -2.3848492461251, -2.3848492461251, -2.3848492461251, -2.3848492461251, -2.3848492461251, -2.3848492461251, -2.3848492461251, -2.3848492461251, -2.3848492461251, -2.3848492461251, -2.3848492461251, -2.3848492461251], 'BiomassGasification': [-2.3814953892347, -2.3814953892347, -2.3814953892347, -2.3814953892347, -2.3814953892347, -2.3814953892347, -2.3814953892347, -2.3814953892347, -2.3814953892347, -2.3814953892347, -2.3814953892347, -2.3814953892347, -2.3814953892347, -2.3814953892347, -2.3814953892347, -2.3814953892347, -2.3814953892347, -2.3814953892347, -2.3814953892347, -2.3814953892347, -2.3814953892347, -2.3814953892347, -2.3814953892347, -2.3814953892347, -2.3814953892347, -2.3814953892347, -2.3814953892347, -2.3814953892347, -2.3814953892347, -2.3814953892347, -2.3814953892347]}
                                                                 )

        self.CoalGasification_consumption = pd.DataFrame({'years': self.years, 'solid_fuel (TWh)': [1108.4101094769846, 1144.1954062664238, 1158.7782627156437, 1148.146067463056, 1048.5382266534239, 997.2268053902488, 954.1275868383744, 904.2279340554692, 895.9244661587778, 911.9754901221262, 823.0174529452225, 784.7143865595392, 772.5922150208357,
                                                                                                    745.2678185726786, 743.7240078389488, 744.9235132188807, 728.0748643881823, 700.0455928992047, 644.5358188860093, 627.4134253523712, 590.9789803579271, 554.6850190831802, 518.5299868491913, 482.5123708729486, 509.3674984939647, 512.3840762429093, 515.3632988882629, 518.3063025702833, 521.2141687189784, 524.0879276420483, 526.9285618162111]})
        self.CoalGasification_production = pd.DataFrame({'years': self.years, 'syngas (TWh)': [931.4370667873822, 961.5087447617007, 973.7632459795325, 964.8286281202151, 881.1245602129613, 838.0057188153352, 801.7878880994743, 759.8554067693019, 752.8777026544352, 766.3659580858204, 691.6113049959854, 659.4238542517137, 649.2371554796939, 626.275477792167, 624.9781578478561, 625.9861455620846, 611.8276171329263, 588.2736074783234, 541.6267385596717, 527.2381725650179, 496.62099189741775, 466.1218647757818, 435.73948474721965, 405.47258056550305, 428.0399147008107, 430.574853985638, 433.0784024271117, 435.55151476494393, 437.9950997638474, 440.410023228612, 442.79711076992527], 'CO2 from Flue Gas (Mt)': [
                                                        144.66021201161772, 149.33060303042717, 151.23383278955896, 149.8462095567521, 136.84624569288948, 130.14951763611379, 124.52457607347219, 118.01209996994108, 116.92840232400944, 119.023244756146, 107.41320222033724, 102.41421343750977, 100.83213123721524, 97.26598460116097, 97.06449962178581, 97.2210488097501, 95.02210719859121, 91.36396629798183, 84.11930513077638, 81.88463670115407, 77.12952440800753, 72.39274684900121, 67.67410112073044, 62.97338978768887, 66.47829146806814, 66.87198940801001, 67.26081207916918, 67.64490776085954, 68.02441759208088, 68.39947603978642, 68.7702113284385]})
        self.CoalGasification_techno_prices = pd.DataFrame({'years': self.years, 'CoalGasification': [72.42389684469369, 72.4449406302368, 72.46854200700315, 72.49457351844165, 72.52291660457976, 72.5534608107061, 72.78992869854271, 73.02839836146852, 73.2687797103381, 73.51098834640658, 73.7549451024183, 73.86803524442895, 73.98272924930026, 74.09896131338351, 74.21666942857934, 74.33579510236385, 74.45592488556456, 74.5773647915476, 74.70006543197695, 74.82398003965643, 74.94906429038784, 75.09605274024305, 75.24412887315523, 75.39325476493, 75.54339435519373, 75.69451332995612, 75.84622079589974, 75.99884383186222, 76.15235274424872, 76.30671919826588, 76.46191613812256], 'CoalGasification_wotaxes': [
                                                           69.33964628716278, 69.25143381021496, 69.16577892449038, 69.08255417343796, 69.00164099708513, 68.92292894072054, 68.84631494850116, 68.771702731371, 68.69900220018458, 68.62812895619709, 68.55900383215283, 68.4915524781129, 68.42570498693361, 68.36139555496626, 68.29856217411151, 68.23714635184542, 68.17709285624962, 68.11834948343613, 68.06086684506897, 68.00459817395193, 67.94949914588682, 67.89552771620953, 67.8426439695892, 67.79080998183149, 67.7399896925627, 67.6901487877926, 67.64125459145778, 67.59327596514183, 67.5461832152499, 67.49994800698862, 67.45454328456687]})
        self.CoalGasification_carbon_emissions = pd.DataFrame({'years': self.years, 'production': [0.1553086270343148, 0.1553086270343148, 0.1553086270343148, 0.1553086270343148, 0.1553086270343148, 0.1553086270343148, 0.1553086270343148, 0.1553086270343148, 0.1553086270343148, 0.1553086270343148, 0.1553086270343148, 0.1553086270343148, 0.1553086270343148, 0.1553086270343148, 0.1553086270343148, 0.1553086270343148, 0.1553086270343148, 0.1553086270343148, 0.1553086270343148, 0.1553086270343148, 0.1553086270343148, 0.1553086270343148, 0.1553086270343148, 0.1553086270343148, 0.1553086270343148, 0.1553086270343148, 0.1553086270343148, 0.1553086270343148, 0.1553086270343148, 0.1553086270343148, 0.1553086270343148], 'solid_fuel': [0.023799999999999998, 0.023799999999999998, 0.023799999999999998, 0.023799999999999998, 0.023799999999999998, 0.023799999999999998, 0.023799999999999998, 0.023799999999999998, 0.023799999999999998, 0.023799999999999998, 0.023799999999999998, 0.023799999999999998, 0.023799999999999998, 0.023799999999999998,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               0.023799999999999998, 0.023799999999999998, 0.023799999999999998, 0.023799999999999998, 0.023799999999999998, 0.023799999999999998, 0.023799999999999998, 0.023799999999999998, 0.023799999999999998, 0.023799999999999998, 0.023799999999999998, 0.023799999999999998, 0.023799999999999998, 0.023799999999999998, 0.023799999999999998, 0.023799999999999998, 0.023799999999999998], 'CoalGasification': [0.1791086270343148, 0.1791086270343148, 0.1791086270343148, 0.1791086270343148, 0.1791086270343148, 0.1791086270343148, 0.1791086270343148, 0.1791086270343148, 0.1791086270343148, 0.1791086270343148, 0.1791086270343148, 0.1791086270343148, 0.1791086270343148, 0.1791086270343148, 0.1791086270343148, 0.1791086270343148, 0.1791086270343148, 0.1791086270343148, 0.1791086270343148, 0.1791086270343148, 0.1791086270343148, 0.1791086270343148, 0.1791086270343148, 0.1791086270343148, 0.1791086270343148, 0.1791086270343148, 0.1791086270343148, 0.1791086270343148, 0.1791086270343148, 0.1791086270343148, 0.1791086270343148]})
        self.CoElectrolysis_consumption = pd.DataFrame({'years': self.years, 'carbon_capture (Mt)': [2.769674795547024e-13, 2.769674795547024e-13, 2.769674795547024e-13, 35102.57277896557, 78980.78875267171, 128977.06799183114, 183824.83795896333, 242757.63180639612, 305252.9808553451, 370927.93080230337, 439487.6432612182, 510696.8948878652, 584362.8871971559, 660324.2087074767, 738443.3950186627, 818601.7156141319, 900695.4030478294, 984632.8521941697, 1070332.492767813, 1157721.1418121925, 1246732.706345501, 1337307.1466503947, 1429389.637037008, 1522929.8785811714, 1617881.530469072, 1714201.7350756535, 1811850.7179646357, 1910791.448392955, 2010989.3491372913, 2112412.0468738764, 2215029.156165998], 'water (Mt)': [
                                                       1.1337529413933742e-13, 1.1337529413933742e-13, 1.1337529413933742e-13, 14369.067878514948, 32330.402726658296, 52796.13709274883, 75247.80565292781, 99371.65892136178, 124953.82687897483, 151837.54903940286, 179902.13473962643, 209051.29644479573, 239206.11303033808, 270300.5114892895, 302278.2214363057, 335090.64111040585, 368695.29381094076, 403054.68142414413, 438135.4135494235, 473907.53309853125, 510343.98522999266, 547420.1929767763, 585113.7137087042, 623403.9578051764, 662271.9558788653, 701700.1643688645, 741672.3018026346, 782173.2098251451, 823188.7344177703, 864705.6237174736, 906711.4395931421]})
        self.CoElectrolysis_production = pd.DataFrame({'years': self.years, 'syngas (TWh)': [1e-12, 1e-12, 1e-12, 126738.96890494916, 285162.68003613263, 465675.85551630636, 663705.4944302839, 876484.2435534036, 1102125.7129036197, 1339247.233641534, 1586784.2822840048, 1843887.5773753072, 2109861.0137792057, 2384121.810145799, 2666173.6468335683, 2955587.84349068, 3251989.7444130722, 3555048.606346219, 3864469.9171493067, 4179989.4474020265, 4501368.566266153, 4828390.498409652, 5160857.293914525, 5498587.34689603, 5841413.34235427, 6189180.541454473, 6541745.337314183, 6898974.029243619, 7260741.775065009, 7626931.689850847, 7997434.066003836], 'dioxygen (Mt)': [
                                                      1.2172850430617795e-14, 1.2172850430617795e-14, 1.2172850430617795e-14, 1542.7745122106658, 3471.2426524739617, 5668.60253834998, 8079.187713679078, 10669.311601568763, 13416.011458913772, 16302.45626473704, 19315.687733898398, 22445.36769026381, 25683.022550125905, 29021.558203278568, 32454.93302495982, 35977.92875336425, 39585.984760643325, 43275.074958628764, 47041.61429508046, 50882.3863447856, 54794.48629024235, 58775.27535775681, 62822.343932584416, 66933.4813534529, 71106.65091989371, 75339.96901921536, 79631.68754631691, 83980.17898269917, 88383.9236432047, 92841.4987050934, 97351.56871419222]})
        self.CoElectrolysis_techno_prices = pd.DataFrame({'years': self.years, 'CoElectrolysis': [89.78635550136332, 71.3222182617535, 71.42936229722763, 71.5394697955606, 71.65237094910471, 71.76796094231511, 72.15703602893413, 72.54611988888327, 72.93520991009756, 73.3243044865501, 73.71340256624882, 74.442177187303, 75.17241069841161, 75.9041356110847, 76.63738562091791, 77.37219562820901, 78.10860177054535, 78.84664146399155, 79.58635345099314, 80.32777785394235, 81.07095623383661, 82.42526010877954, 83.78140565714286, 85.139439155643, 86.49940860227397, 87.8613637994138, 89.28074993827151, 90.70222720544805, 92.12585137109714, 93.55168040000196, 94.97977456559525], 'CoElectrolysis_wotaxes': [
                                                         89.78635550136332, 71.3222182617535, 71.42936229722763, 71.5394697955606, 71.65237094910471, 71.76796094231511, 72.15703602893413, 72.54611988888327, 72.93520991009756, 73.3243044865501, 73.71340256624882, 74.442177187303, 75.17241069841161, 75.9041356110847, 76.63738562091791, 77.37219562820901, 78.10860177054535, 78.84664146399155, 79.58635345099314, 80.32777785394235, 81.07095623383661, 82.42526010877954, 83.78140565714286, 85.139439155643, 86.49940860227397, 87.8613637994138, 89.28074993827151, 90.70222720544805, 92.12585137109714, 93.55168040000196, 94.97977456559525]})
        self.CoElectrolysis_carbon_emissions = pd.DataFrame({'years': self.years, 'production': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 'CO2': [-0.2769674795547024, -0.2769674795547024, -0.2769674795547024, -0.2769674795547024, -0.2769674795547024, -0.2769674795547024, -0.2769674795547024, -0.2769674795547024, -0.2769674795547024, -0.2769674795547024, -0.2769674795547024, -0.2769674795547024, -0.2769674795547024, -0.2769674795547024, -0.2769674795547024, -0.2769674795547024, -0.2769674795547024, -0.2769674795547024, -0.2769674795547024, -0.2769674795547024, -0.2769674795547024, -0.2769674795547024, -0.2769674795547024, -0.2769674795547024, -0.2769674795547024, -0.2769674795547024, -0.2769674795547024, -0.2769674795547024, -0.2769674795547024, -0.2769674795547024, -0.2769674795547024], 'electricity': [0.019993016386778098, 0.019993016386778098, 0.019993016386778098, 0.019993016386778098, 0.019993016386778098, 0.019993016386778098, 0.019993016386778098, 0.019993016386778098, 0.019993016386778098, 0.019993016386778098,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 0.019993016386778098, 0.019993016386778098, 0.019993016386778098, 0.019993016386778098, 0.019993016386778098, 0.019993016386778098, 0.019993016386778098, 0.019993016386778098, 0.019993016386778098, 0.019993016386778098, 0.019993016386778098, 0.019993016386778098, 0.019993016386778098, 0.019993016386778098, 0.019993016386778098, 0.019993016386778098, 0.019993016386778098, 0.019993016386778098, 0.019993016386778098, 0.019993016386778098, 0.019993016386778098], 'CoElectrolysis': [-0.2569744631679243, -0.2569744631679243, -0.2569744631679243, -0.2569744631679243, -0.2569744631679243, -0.2569744631679243, -0.2569744631679243, -0.2569744631679243, -0.2569744631679243, -0.2569744631679243, -0.2569744631679243, -0.2569744631679243, -0.2569744631679243, -0.2569744631679243, -0.2569744631679243, -0.2569744631679243, -0.2569744631679243, -0.2569744631679243, -0.2569744631679243, -0.2569744631679243, -0.2569744631679243, -0.2569744631679243, -0.2569744631679243, -0.2569744631679243, -0.2569744631679243, -0.2569744631679243, -0.2569744631679243, -0.2569744631679243, -0.2569744631679243, -0.2569744631679243, -0.2569744631679243]})

        self.name = 'Test'
        self.model_name = 'syngas'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': f'{self.name}',
                   'ns_hydrogen': f'{self.name}',
                   'ns_syngas': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_resource': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.stream_type.energy_disciplines.syngas_disc.SyngasDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{self.model_name}.year_start': 2020,
                       f'{self.name}.{self.model_name}.year_end': 2050,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.technologies_list': ['Pyrolysis', 'SMR', 'AutothermalReforming', 'BiomassGasification', 'CoalGasification', 'CoElectrolysis'],
                       f'{self.name}.{self.model_name}.Pyrolysis.techno_consumption': self.pyrolysis_consumption,
                       f'{self.name}.{self.model_name}.Pyrolysis.techno_consumption_woratio': self.pyrolysis_consumption,
                       f'{self.name}.{self.model_name}.Pyrolysis.techno_production': self.pyrolysis_production,
                       f'{self.name}.{self.model_name}.Pyrolysis.techno_prices': self.pyrolysis_techno_prices,
                       f'{self.name}.{self.model_name}.Pyrolysis.CO2_emissions': self.pyrolysis_carbon_emissions,
                       f'{self.name}.{self.model_name}.Pyrolysis.syngas_ratio': [111.111111],
                       f'{self.name}.{self.model_name}.Pyrolysis.land_use_required': self.land_use_required_Pyrolysis,
                       f'{self.name}.{self.model_name}.SMR.techno_consumption': self.smr_consumption,
                       f'{self.name}.{self.model_name}.SMR.techno_consumption_woratio': self.smr_consumption,
                       f'{self.name}.{self.model_name}.SMR.techno_production': self.smr_production,
                       f'{self.name}.{self.model_name}.SMR.techno_prices': self.smr_techno_prices,
                       f'{self.name}.{self.model_name}.SMR.CO2_emissions': self.smr_carbon_emissions,
                       f'{self.name}.{self.model_name}.SMR.syngas_ratio': [33.333333],
                       f'{self.name}.{self.model_name}.SMR.land_use_required': self.land_use_required_SMR,
                       f'{self.name}.{self.model_name}.AutothermalReforming.techno_consumption': self.AutothermalReforming_consumption,
                       f'{self.name}.{self.model_name}.AutothermalReforming.techno_consumption_woratio': self.AutothermalReforming_consumption,
                       f'{self.name}.{self.model_name}.AutothermalReforming.techno_production': self.AutothermalReforming_production,
                       f'{self.name}.{self.model_name}.AutothermalReforming.techno_prices': self.AutothermalReforming_techno_prices,
                       f'{self.name}.{self.model_name}.AutothermalReforming.CO2_emissions': self.AutothermalReforming_carbon_emissions,
                       f'{self.name}.{self.model_name}.AutothermalReforming.syngas_ratio': [100.],
                       f'{self.name}.{self.model_name}.AutothermalReforming.land_use_required': self.land_use_required_AutothermalReforming,
                       f'{self.name}.{self.model_name}.BiomassGasification.techno_consumption': self.BiomassGasification_consumption,
                       f'{self.name}.{self.model_name}.BiomassGasification.techno_consumption_woratio': self.BiomassGasification_consumption,
                       f'{self.name}.{self.model_name}.BiomassGasification.techno_production': self.BiomassGasification_production,
                       f'{self.name}.{self.model_name}.BiomassGasification.techno_prices': self.BiomassGasification_techno_prices,
                       f'{self.name}.{self.model_name}.BiomassGasification.CO2_emissions': self.BiomassGasification_carbon_emissions,
                       f'{self.name}.{self.model_name}.BiomassGasification.syngas_ratio': [83.870968],
                       f'{self.name}.{self.model_name}.BiomassGasification.land_use_required': self.land_use_required_BiomassGasification,
                       f'{self.name}.{self.model_name}.CoalGasification.techno_consumption': self.CoalGasification_consumption,
                       f'{self.name}.{self.model_name}.CoalGasification.techno_consumption_woratio': self.CoalGasification_consumption,
                       f'{self.name}.{self.model_name}.CoalGasification.techno_production': self.CoalGasification_production,
                       f'{self.name}.{self.model_name}.CoalGasification.techno_prices': self.CoalGasification_techno_prices,
                       f'{self.name}.{self.model_name}.CoalGasification.CO2_emissions': self.CoalGasification_carbon_emissions,
                       f'{self.name}.{self.model_name}.CoalGasification.syngas_ratio': [213.636364],
                       f'{self.name}.{self.model_name}.CoalGasification.land_use_required': self.land_use_required_CoalGasification,
                       f'{self.name}.{self.model_name}.CoElectrolysis.techno_consumption': self.CoElectrolysis_consumption,
                       f'{self.name}.{self.model_name}.CoElectrolysis.techno_consumption_woratio': self.CoElectrolysis_consumption,
                       f'{self.name}.{self.model_name}.CoElectrolysis.techno_production': self.CoElectrolysis_production,
                       f'{self.name}.{self.model_name}.CoElectrolysis.techno_prices': self.CoElectrolysis_techno_prices,
                       f'{self.name}.{self.model_name}.CoElectrolysis.CO2_emissions': self.CoElectrolysis_carbon_emissions,
                       f'{self.name}.{self.model_name}.CoElectrolysis.syngas_ratio': [100.],
                       f'{self.name}.{self.model_name}.CoElectrolysis.land_use_required': self.land_use_required_CoElectrolysis,
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        #AbstractJacobianUnittest.DUMP_JACOBIAN = True
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_specific_{self.energy_name}.pkl',
                            discipline=disc, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,
                            inputs=[f'{self.name}.{self.model_name}.Pyrolysis.techno_production', f'{self.name}.{self.model_name}.Pyrolysis.syngas_ratio',
                                    f'{self.name}.{self.model_name}.SMR.techno_production', f'{self.name}.{self.model_name}.SMR.syngas_ratio',
                                    f'{self.name}.{self.model_name}.AutothermalReforming.techno_production', f'{self.name}.{self.model_name}.AutothermalReforming.syngas_ratio',
                                    f'{self.name}.{self.model_name}.BiomassGasification.techno_production', f'{self.name}.{self.model_name}.BiomassGasification.syngas_ratio',
                                    f'{self.name}.{self.model_name}.CoalGasification.techno_production', f'{self.name}.{self.model_name}.CoalGasification.syngas_ratio',
                                    f'{self.name}.{self.model_name}.CoElectrolysis.techno_production', f'{self.name}.{self.model_name}.CoElectrolysis.syngas_ratio',
                                    f'{self.name}.CO2_taxes'],
                            outputs=[f'{self.name}.syngas_ratio',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.CO2_per_use',
                                     f'{self.name}.{self.model_name}.energy_prices',
                                     f'{self.name}.{self.model_name}.energy_consumption',
                                     f'{self.name}.{self.model_name}.energy_production'],)

    def test_09_generic_syngas_discipline_jacobian(self):

        self.name = 'Test'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': f'{self.name}',
                   'ns_syngas': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_resource': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.stream_type.energy_disciplines.syngas_disc.SyngasDiscipline'
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
                       'syngas_ratio', 'data_fuel_dict']:
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
            if key in ['syngas_ratio']:
                if mda_data_output_dict[self.energy_name][key]['is_coupling']:
                    coupled_outputs += [f'{namespace}.{key}']
            else:
                if mda_data_output_dict[self.energy_name][key]['is_coupling']:
                    coupled_outputs += [f'{namespace}.{self.energy_name}.{key}']

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.energy_name}')[0]
        # AbstractJacobianUnittest.DUMP_JACOBIAN = True

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_generic_{self.energy_name}.pkl',
                            discipline=disc, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,
                            inputs=coupled_inputs,
                            outputs=coupled_outputs,)


if '__main__' == __name__:
    AbstractJacobianUnittest.DUMP_JACOBIAN = True
    cls = SyngasJacobianTestCase()
    cls.setUp()
    cls.test_09_generic_syngas_discipline_jacobian()
