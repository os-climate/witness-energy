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
from sos_trades_core.execution_engine.execution_engine import ExecutionEngine
from energy_models.core.stream_type.resources_data_disc import get_static_CO2_emissions,\
    get_static_prices
from sos_trades_core.tests.core.abstract_jacobian_unit_test import AbstractJacobianUnittest
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
from energy_models.core.energy_mix.energy_mix import EnergyMix
import pickle


class HydrogenJacobianTestCase(AbstractJacobianUnittest):
    """
    Hydrogen jacobian test class
    """
    #AbstractJacobianUnittest.DUMP_JACOBIAN = True

    def analytic_grad_entry(self):
        return [
            self.test_01_wgs_jacobian,
            self.test_02_plasma_cracking_jacobian,
            self.test_03_electrolysis_PEMjacobian,
            self.test_04_electrolysis_SOEC_jacobian,
            self.test_05_electrolysis_AWE_jacobian,
            self.test_06_hydrogen_jacobian,
            self.test_07_wgs_jacobian_invest_negative,
            self.test_08_gaseous_hydrogen_discipline_jacobian,
        ]

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.energy_name = 'hydrogen'

        years = np.arange(2020, 2051)

        self.electrolysis_techno_prices = pd.DataFrame({'Electrolysis': np.array([0.09, 0.08974117039450046, 0.08948672733558984,
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
                                                        'Electrolysis_wotaxes': np.array([0.09, 0.08974117039450046, 0.08948672733558984,
                                                                                          0.089236536471781, 0.08899046935409588, 0.08874840310033885,
                                                                                          0.08875044941298937, 0.08875249600769718, 0.08875454288453355,
                                                                                          0.08875659004356974, 0.0887586374848771, 0.08893789675406477,
                                                                                          0.08911934200930778, 0.08930302260662477, 0.08948898953954933,
                                                                                          0.08967729551117891, 0.08986799501019029, 0.09006114439108429,
                                                                                          0.09025680195894345, 0.09045502805900876, 0.09065588517140537,
                                                                                          0.0908594380113745, 0.09106575363539733, 0.09127490155362818,
                                                                                          0.09148695384909017, 0.0917019853041231, 0.0919200735346165,
                                                                                          0.09214129913260598, 0.09236574581786147, 0.09259350059915213,
                                                                                          0.0928246539459331]) * 1000.0})

        self.smr_techno_prices = pd.DataFrame({'WaterGasShift': np.array([0.06363, 0.0612408613576689, 0.059181808246196024, 0.05738028027202377,
                                                                          0.0557845721244601, 0.05435665353332419, 0.05225877624361548,
                                                                          0.05045797192512811, 0.04888746457113824, 0.04750006564084081,
                                                                          0.04626130284326101, 0.044848110567750024, 0.043596892851567724,
                                                                          0.04247763196812953, 0.04146768302263715, 0.04054957955940597,
                                                                          0.03970959176775726, 0.03893674917609171, 0.038222160192931814,
                                                                          0.03755852715493717, 0.03693979356326306, 0.03636088278590117,
                                                                          0.03581750135963429, 0.03530598876014997, 0.03482320115289285,
                                                                          0.03436642036567466, 0.03393328183670935, 0.033521717015978045,
                                                                          0.03312990690071806, 0.032756244237772174, 0.03239930253734476]) * 1000.0,
                                               'WaterGasShift_wotaxes': np.array([0.06363, 0.0612408613576689, 0.059181808246196024, 0.05738028027202377,
                                                                                  0.0557845721244601, 0.05435665353332419, 0.05225877624361548,
                                                                                  0.05045797192512811, 0.04888746457113824, 0.04750006564084081,
                                                                                  0.04626130284326101, 0.044848110567750024, 0.043596892851567724,
                                                                                  0.04247763196812953, 0.04146768302263715, 0.04054957955940597,
                                                                                  0.03970959176775726, 0.03893674917609171, 0.038222160192931814,
                                                                                  0.03755852715493717, 0.03693979356326306, 0.03636088278590117,
                                                                                  0.03581750135963429, 0.03530598876014997, 0.03482320115289285,
                                                                                  0.03436642036567466, 0.03393328183670935, 0.033521717015978045,
                                                                                  0.03312990690071806, 0.032756244237772174, 0.03239930253734476]) * 1000.0
                                               })

        self.plasmacracking_techno_prices = pd.DataFrame({'PlasmaCracking':
                                                          np.array([0.06363, 0.0612408613576689, 0.059181808246196024, 0.05738028027202377,
                                                                    0.0557845721244601, 0.05435665353332419, 0.05225877624361548,
                                                                    0.05045797192512811, 0.04888746457113824, 0.04750006564084081,
                                                                    0.04626130284326101, 0.044848110567750024, 0.043596892851567724,
                                                                    0.04247763196812953, 0.04146768302263715, 0.04054957955940597,
                                                                    0.03970959176775726, 0.03893674917609171, 0.038222160192931814,
                                                                    0.03755852715493717, 0.03693979356326306, 0.03636088278590117,
                                                                    0.03581750135963429, 0.03530598876014997, 0.03482320115289285,
                                                                    0.03436642036567466, 0.03393328183670935, 0.033521717015978045,
                                                                    0.03312990690071806, 0.032756244237772174, 0.03239930253734476]) * 1000.0,
                                                          'PlasmaCracking_wotaxes':
                                                          np.array([0.06363, 0.0612408613576689, 0.059181808246196024, 0.05738028027202377,
                                                                    0.0557845721244601, 0.05435665353332419, 0.05225877624361548,
                                                                    0.05045797192512811, 0.04888746457113824, 0.04750006564084081,
                                                                    0.04626130284326101, 0.044848110567750024, 0.043596892851567724,
                                                                    0.04247763196812953, 0.04146768302263715, 0.04054957955940597,
                                                                    0.03970959176775726, 0.03893674917609171, 0.038222160192931814,
                                                                    0.03755852715493717, 0.03693979356326306, 0.03636088278590117,
                                                                    0.03581750135963429, 0.03530598876014997, 0.03482320115289285,
                                                                    0.03436642036567466, 0.03393328183670935, 0.033521717015978045,
                                                                    0.03312990690071806, 0.032756244237772174, 0.03239930253734476]) * 1000.0
                                                          })

        self.smr_consumption = pd.DataFrame({'years': years,
                                             'hydrogen.gaseous_hydrogen (TWh)': [230.779470] * len(years),
                                             'electricity (TWh)': [82.649011] * len(years),
                                             'syngas (TWh)': [3579.828092] * len(years),
                                             f"{ResourceGlossary.Water['name']} (Mt)": [381.294427] * len(years)})

        self.smr_production = pd.DataFrame({'years': years,
                                            'hydrogen.gaseous_hydrogen (TWh)': [2304.779470] * len(years),
                                            'CO2 from Flue Gas (Mt)': [844.027980] * len(years)})

        self.plasmacracking_production = pd.DataFrame({'years': years,
                                                       'hydrogen.gaseous_hydrogen (TWh)': np.linspace(1e-5, 1, len(years)),
                                                       f"{ResourceGlossary.Carbon['name']} (Mt)":   [0.008622] * len(years)})

        self.plasmacracking_consumption = pd.DataFrame({'years': years,
                                                        'electricity (TWh)': [0.019325] * len(years),
                                                        'methane (TWh)':  [0.213945] * len(years)})

        self.electrolysis_consumption = pd.DataFrame({'years': years,
                                                      'electricity (TWh)': [4.192699] * len(years),
                                                      f"{ResourceGlossary.Water['name']} (Mt)": [0.021638] * len(years)})

        self.electrolysis_production = pd.DataFrame({'years': years,
                                                     'hydrogen.gaseous_hydrogen (TWh)': [2.684940] * len(years),
                                                     f"{ResourceGlossary.Dioxygen['name']} (Mt)": [0.019217] * len(years)})

        self.electrolysis_carbon_emissions = pd.DataFrame(
            {'years': years, 'Electrolysis': 0.0, 'electricity': 0.0, 'production': 0.0})

        self.plasma_cracking_carbon_emissions = pd.DataFrame(
            {'years': years, 'PlasmaCracking': -0.243905, 'carbon storage': -0.327803, 'methane': 0.0, 'electricity': 0.0, 'production': 0.0})
        self.smr_carbon_emissions = pd.DataFrame(
            {'years': years, 'WaterGasShift': 0.366208, 'syngas': 0.0, 'electricity': 0.0, 'production': 0.366208})
        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [0.01486, 0.01722, 0.02027,
                     0.02901,  0.03405,   0.03908,  0.04469,   0.05029]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {'years': years, 'CO2_tax': func(years)})

        electricity_price = np.array([0.09, 0.08974117039450046, 0.08948672733558984,
                                      0.089236536471781, 0.08899046935409588, 0.08874840310033885,
                                      0.08875044941298937, 0.08875249600769718, 0.08875454288453355,
                                      0.08875659004356974, 0.0887586374848771, 0.08893789675406477,
                                      0.08911934200930778, 0.08930302260662477, 0.08948898953954933,
                                      0.08967729551117891, 0.08986799501019029, 0.09006114439108429,
                                      0.09025680195894345, 0.09045502805900876, 0.09065588517140537,
                                      0.0908594380113745, 0.09106575363539733, 0.09127490155362818,
                                      0.09148695384909017, 0.0917019853041231, 0.0919200735346165,
                                      0.09214129913260598, 0.09236574581786147, 0.09259350059915213,
                                      0.0928246539459331]) * 1000

        self.energy_prices = pd.DataFrame({'years': years, 'electricity': electricity_price,
                                           'syngas': np.ones(len(years)) * 33.,
                                           'methane': np.array([0.06363, 0.0612408613576689, 0.059181808246196024, 0.05738028027202377,
                                                                0.0557845721244601, 0.05435665353332419, 0.05225877624361548,
                                                                0.05045797192512811, 0.04888746457113824, 0.04750006564084081,
                                                                0.04626130284326101, 0.044848110567750024, 0.043596892851567724,
                                                                0.04247763196812953, 0.04146768302263715, 0.04054957955940597,
                                                                0.03970959176775726, 0.03893674917609171, 0.038222160192931814,
                                                                0.03755852715493717, 0.03693979356326306, 0.03636088278590117,
                                                                0.03581750135963429, 0.03530598876014997, 0.03482320115289285,
                                                                0.03436642036567466, 0.03393328183670935, 0.033521717015978045,
                                                                0.03312990690071806, 0.032756244237772174, 0.03239930253734476]) * 1000 / 1.5,
                                           'hydrogen.gaseous_hydrogen': 50
                                           })

        self.energy_carbon_emissions = pd.DataFrame(
            {'years': years, 'electricity': 0.02, 'syngas': 0.2, 'methane': -0.1})
        self.invest_level = pd.DataFrame(
            {'years': years, 'invest': np.ones(len(years)) * 0.1715})

        self.invest_level_negative = pd.DataFrame(
            {'years': years, 'invest': np.linspace(5000, -5000, len(years))})
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
            {'years': years, 'transport': np.ones(len(years)) * 500.0})

        self.syngas_ratio = np.linspace(33.0, 209.0, len(years))
        self.syngas_detailed_prices = pd.DataFrame({'SMR': np.ones(len(years)) * 34.,
                                                    # price to be updated for
                                                    # CO2
                                                    'CoElectrolysis': np.ones(len(years)) * 60.,
                                                    'BiomassGasification': np.ones(len(years)) * 50.
                                                    })
        self.syngas_ratio_technos = {'SMR': 33.0,
                                     'CoElectrolysis': 100.0,
                                     'BiomassGasification': 200.0
                                     }
        CO2_tax = np.array([0.01722, 0.033496, 0.049772, 0.066048, 0.082324, 0.0986,
                            0.114876, 0.131152, 0.147428, 0.163704, 0.17998, 0.217668,
                            0.255356, 0.293044, 0.330732, 0.36842, 0.406108, 0.443796,
                            0.481484, 0.519172, 0.55686, 0.591706, 0.626552, 0.661398,
                            0.696244, 0.73109, 0.765936, 0.800782, 0.835628, 0.870474,
                            0.90532]) * 1000
        self.CO2_taxes = pd.DataFrame({'years': years,
                                       'CO2_tax': CO2_tax})

        self.invest = pd.DataFrame({'years': years,
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
        self.land_use_required_mock = pd.DataFrame(
            {'years': years, 'random techno (Gha)': 0.0})

        self.land_use_required_WaterGasShift = pd.DataFrame(
            {'years': years, 'WaterGasShift (Gha)': 0.0})
        self.land_use_required_Electrolysis = pd.DataFrame(
            {'years': years, 'Electrolysis (Gha)': 0.0})
        self.land_use_required_PlasmaCracking = pd.DataFrame(
            {'years': years, 'PlasmaCracking (Gha)': 0.0})

        self.invest_plasmacracking = pd.DataFrame({'years': years,
                                                   'invest': [1.0e-11] + list(np.linspace(0.001, 0.4, len(years) - 1))})
        #---Ratios---
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.linspace(100, 100, len(years))))

        demand_ratio_dict['years'] = years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)
        self.all_streams_demand_ratio['syngas'] = np.linspace(
            100, 50, len(years))
        self.all_streams_demand_ratio['electricity'] = np.linspace(
            60, 40, len(years))

        resource_ratio_dict = dict(
            zip(EnergyMix.RESOURCE_LIST, np.linspace(1.0, 1.0, len(years))))
        resource_ratio_dict['years'] = years
        self.all_resource_ratio_usable_demand = pd.DataFrame(
            resource_ratio_dict)

    def tearDown(self):
        pass

    def test_01_wgs_jacobian(self):

        self.name = 'Test'
        self.model_name = 'WGS'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_hydrogen': f'{self.name}',
                   'ns_syngas': f'{self.name}',
                   'ns_energy_mix': f'{self.name}',
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.gaseous_hydrogen.water_gas_shift.water_gas_shift_disc.WaterGasShiftDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.year_end': 2050,
                       f'{self.name}.resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.resources_price': get_static_prices(np.arange(2020, 2051)),
                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.transport_margin': self.margin,
                       f'{self.name}.transport_cost': self.transport,
                       f'{self.name}.{self.model_name}.margin':  self.margin,
                       f'{self.name}.syngas_ratio': self.syngas_ratio,
                       f'{self.name}.syngas_ratio_technos': self.syngas_ratio_technos,
                       f'{self.name}.energy_detailed_techno_prices': self.syngas_detailed_prices,
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       f'{self.name}.is_stream_demand': True,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        disc_techno = self.ee.root_process.sos_disciplines[0]
        self.ee.execute()
        print('---------')
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step',
                            inputs=[f'{self.name}.{self.model_name}.invest_level',
                                    f'{self.name}.energy_prices',
                                    f'{self.name}.energy_CO2_emissions',
                                    f'{self.name}.syngas_ratio',
                                    f'{self.name}.CO2_taxes',
                                    f'{self.name}.resources_price',
                                    f'{self.name}.resources_CO2_emissions',
                                    ],
                            outputs=[f'{self.name}.{self.model_name}.techno_prices',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.techno_consumption',
                                     f'{self.name}.{self.model_name}.techno_consumption_woratio',
                                     f'{self.name}.{self.model_name}.techno_production',
                                     f'{self.name}.{self.model_name}.techno_capital',
                                     f'{self.name}.{self.model_name}.non_use_capital',
                                     ],)

    def test_02_plasma_cracking_jacobian(self):

        self.name = 'Test'
        self.model_name = 'plasma_cracking'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_hydrogen': self.name,
                   'ns_energy_mix': self.name,
                   'ns_carb': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.gaseous_hydrogen.plasma_cracking.plasma_cracking_disc.PlasmaCrackingDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        inputs_dict = {f'{self.name}.year_end': 2050,
                       f'{self.name}.resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.resources_price': get_static_prices(np.arange(2020, 2051)),
                       f'{self.name}.{self.model_name}.margin': self.margin,
                       f'{self.name}.CO2_taxes': self.CO2_taxes,
                       f'{self.name}.{self.model_name}.invest_level':  self.invest_plasmacracking,
                       f'{self.name}.transport_cost':  self.transport,
                       f'{self.name}.transport_margin':  pd.concat([self.margin['years'], self.margin['margin'] / 1.1], axis=1, keys=['years', 'margin']),
                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': self.energy_carbon_emissions,
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        disc_techno = self.ee.root_process.sos_disciplines[0]

        #AbstractJacobianUnittest.DUMP_JACOBIAN = True
        np.set_printoptions(100)
        # np.set_printoptions(threshold=50)

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step',
                            inputs=[
                                f'{self.name}.{self.model_name}.invest_level',
                                f'{self.name}.energy_prices',
                                f'{self.name}.energy_CO2_emissions',
                                f'{self.name}.CO2_taxes',
                                f'{self.name}.all_streams_demand_ratio',
                                f'{self.name}.resources_price',
                                f'{self.name}.resources_CO2_emissions'
        ],
            outputs=[f'{self.name}.{self.model_name}.percentage_resource',
                     f'{self.name}.{self.model_name}.techno_prices',
                     f'{self.name}.{self.model_name}.CO2_emissions',
                     f'{self.name}.{self.model_name}.techno_consumption',
                     f'{self.name}.{self.model_name}.techno_consumption_woratio',
                     f'{self.name}.{self.model_name}.techno_production',
                     ],)
        # outputs=[f'{self.name}.{self.model_name}.percentage_resource',
        #          f'{self.name}.{self.model_name}.techno_prices',
        #                             f'{self.name}.{self.model_name}.CO2_emissions',
        #                             f'{self.name}.{self.model_name}.techno_consumption',
        #                             f'{self.name}.{self.model_name}.techno_production'],)

        # AbstractJacobianUnittest.DUMP_JACOBIAN = True
        # self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
        #                     discipline=disc_techno, step=1.0e-18, derr_approx='complex_step',
        #                     inputs=[
        #                         f'{self.name}.{self.model_name}.invest_level'],
        #                     outputs=[f'{self.name}.{self.model_name}.percentage_resource'])

    def test_03_electrolysis_PEMjacobian(self):

        self.name = 'Test'
        self.model_name = 'PEM'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_hydrogen': self.name,
                   'ns_energy_mix': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.gaseous_hydrogen.electrolysis.pem.electrolysis_pem_disc.ElectrolysisPEMDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        inputs_dict = {f'{self.name}.year_end': 2050,
                       f'{self.name}.resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.resources_price': get_static_prices(np.arange(2020, 2051)),
                       f'{self.name}.{self.model_name}.margin': self.margin,
                       f'{self.name}.CO2_taxes': self.CO2_taxes,
                       f'{self.name}.{self.model_name}.invest_level':  self.invest,
                       f'{self.name}.transport_cost':  self.transport,
                       f'{self.name}.transport_margin': pd.concat([self.margin['years'], self.margin['margin'] / 1.1], axis=1, keys=['years', 'margin']),
                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': self.energy_carbon_emissions,
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        disc_techno = self.ee.root_process.sos_disciplines[0]

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step',
                            inputs=[f'{self.name}.{self.model_name}.invest_level',
                                    f'{self.name}.energy_prices',
                                    f'{self.name}.energy_CO2_emissions',
                                    f'{self.name}.CO2_taxes',
                                    f'{self.name}.resources_price',
                                    f'{self.name}.resources_CO2_emissions',
                                    ],
                            outputs=[f'{self.name}.{self.model_name}.techno_prices',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.techno_consumption',
                                     f'{self.name}.{self.model_name}.techno_consumption_woratio',
                                     f'{self.name}.{self.model_name}.techno_production',
                                     ],)

    def test_04_electrolysis_SOEC_jacobian(self):

        self.name = 'Test'
        self.model_name = 'SOEC'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_hydrogen': self.name,
                   'ns_energy_mix': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.gaseous_hydrogen.electrolysis.soec.electrolysis_soec_disc.ElectrolysisSOECDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        inputs_dict = {f'{self.name}.year_end': 2050,
                       f'{self.name}.resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.resources_price': get_static_prices(np.arange(2020, 2051)),
                       f'{self.name}.{self.model_name}.margin': self.margin,
                       f'{self.name}.CO2_taxes': self.CO2_taxes,
                       f'{self.name}.{self.model_name}.invest_level':  self.invest,
                       f'{self.name}.transport_cost':  self.transport,
                       f'{self.name}.transport_margin': pd.concat([self.margin['years'], self.margin['margin'] / 1.1], axis=1, keys=['years', 'margin']),
                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': self.energy_carbon_emissions,
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        disc_techno = self.ee.root_process.sos_disciplines[0]

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step',
                            inputs=[f'{self.name}.{self.model_name}.invest_level',
                                    f'{self.name}.energy_prices',
                                    f'{self.name}.energy_CO2_emissions',
                                    f'{self.name}.CO2_taxes',
                                    f'{self.name}.resources_price',
                                    f'{self.name}.resources_CO2_emissions',
                                    ],
                            outputs=[f'{self.name}.{self.model_name}.techno_prices',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.techno_consumption',
                                     f'{self.name}.{self.model_name}.techno_consumption_woratio',
                                     f'{self.name}.{self.model_name}.techno_production',
                                     ],)

    def test_05_electrolysis_AWE_jacobian(self):

        self.name = 'Test'
        self.model_name = 'AWE'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_hydrogen': self.name,
                   'ns_energy_mix': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.gaseous_hydrogen.electrolysis.awe.electrolysis_awe_disc.ElectrolysisAWEDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        inputs_dict = {f'{self.name}.year_end': 2050,
                       f'{self.name}.resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.resources_price': get_static_prices(np.arange(2020, 2051)),
                       f'{self.name}.{self.model_name}.margin': self.margin,
                       f'{self.name}.CO2_taxes': self.CO2_taxes,
                       f'{self.name}.{self.model_name}.invest_level':  self.invest,
                       f'{self.name}.transport_cost':  self.transport,
                       f'{self.name}.transport_margin': pd.concat([self.margin['years'], self.margin['margin'] / 1.1], axis=1, keys=['years', 'margin']),
                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': self.energy_carbon_emissions,
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        disc_techno = self.ee.root_process.sos_disciplines[0]

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step',
                            inputs=[f'{self.name}.{self.model_name}.invest_level',
                                    f'{self.name}.energy_prices',
                                    f'{self.name}.energy_CO2_emissions',
                                    f'{self.name}.CO2_taxes',
                                    f'{self.name}.resources_price',
                                    f'{self.name}.resources_CO2_emissions',
                                    ],
                            outputs=[f'{self.name}.{self.model_name}.techno_prices',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.techno_consumption',
                                     f'{self.name}.{self.model_name}.techno_consumption_woratio',
                                     f'{self.name}.{self.model_name}.techno_production',
                                     ],)

    def test_06_hydrogen_jacobian(self):

        self.name = 'Test'
        self.model_name = 'hydrogen.gaseous_hydrogen'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': f'{self.name}',
                   'ns_hydrogen': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_energy_mix': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.stream_type.energy_disciplines.gaseous_hydrogen_disc.GaseousHydrogenDiscipline'

        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.year_start': 2020,
                       f'{self.name}.year_end': 2050,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.technologies_list': ['WaterGasShift', 'Electrolysis', 'PlasmaCracking'],
                       f'{self.name}.{self.model_name}.WaterGasShift.techno_consumption': self.smr_consumption,
                       f'{self.name}.{self.model_name}.WaterGasShift.techno_consumption_woratio': self.smr_consumption,
                       f'{self.name}.{self.model_name}.WaterGasShift.techno_production': self.smr_production,
                       f'{self.name}.{self.model_name}.WaterGasShift.techno_prices': self.smr_techno_prices,
                       f'{self.name}.{self.model_name}.WaterGasShift.CO2_emissions': self.smr_carbon_emissions,
                       f'{self.name}.{self.model_name}.WaterGasShift.land_use_required': self.land_use_required_WaterGasShift,
                       f'{self.name}.{self.model_name}.Electrolysis.techno_consumption': self.electrolysis_consumption,
                       f'{self.name}.{self.model_name}.Electrolysis.techno_consumption_woratio': self.electrolysis_consumption,
                       f'{self.name}.{self.model_name}.Electrolysis.techno_production': self.electrolysis_production,
                       f'{self.name}.{self.model_name}.Electrolysis.techno_prices': self.electrolysis_techno_prices,
                       f'{self.name}.{self.model_name}.Electrolysis.CO2_emissions': self.electrolysis_carbon_emissions,
                       f'{self.name}.{self.model_name}.Electrolysis.land_use_required': self.land_use_required_Electrolysis,
                       f'{self.name}.{self.model_name}.PlasmaCracking.techno_consumption': self.plasmacracking_consumption,
                       f'{self.name}.{self.model_name}.PlasmaCracking.techno_consumption_woratio': self.plasmacracking_consumption,
                       f'{self.name}.{self.model_name}.PlasmaCracking.techno_production': self.plasmacracking_production,
                       f'{self.name}.{self.model_name}.PlasmaCracking.techno_prices': self.plasmacracking_techno_prices,
                       f'{self.name}.{self.model_name}.PlasmaCracking.CO2_emissions': self.plasma_cracking_carbon_emissions,
                       f'{self.name}.{self.model_name}.PlasmaCracking.land_use_required': self.land_use_required_PlasmaCracking,
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        disc = self.ee.root_process.sos_disciplines[0]
        #AbstractJacobianUnittest.DUMP_JACOBIAN = True
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}.pkl',
                            discipline=disc, step=1.0e-16, derr_approx='complex_step',
                            inputs=[f'{self.name}.{self.model_name}.WaterGasShift.techno_prices',
                                    f'{self.name}.{self.model_name}.Electrolysis.techno_prices',
                                    f'{self.name}.{self.model_name}.PlasmaCracking.techno_prices',
                                    f'{self.name}.{self.model_name}.WaterGasShift.techno_consumption',
                                    f'{self.name}.{self.model_name}.Electrolysis.techno_consumption',
                                    f'{self.name}.{self.model_name}.PlasmaCracking.techno_consumption',
                                    f'{self.name}.{self.model_name}.WaterGasShift.techno_production',
                                    f'{self.name}.{self.model_name}.Electrolysis.techno_production',
                                    f'{self.name}.{self.model_name}.PlasmaCracking.techno_production',
                                    f'{self.name}.{self.model_name}.WaterGasShift.CO2_emissions',
                                    f'{self.name}.{self.model_name}.Electrolysis.CO2_emissions',
                                    f'{self.name}.{self.model_name}.PlasmaCracking.CO2_emissions'],
                            outputs=[f'{self.name}.{self.model_name}.techno_mix',
                                     f'{self.name}.{self.model_name}.energy_prices',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.energy_consumption',
                                     f'{self.name}.{self.model_name}.energy_production'],)

    def test_07_wgs_jacobian_invest_negative(self):

        self.name = 'Test'
        self.model_name = 'WGS'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_hydrogen': f'{self.name}',
                   'ns_syngas': f'{self.name}',
                   'ns_energy_mix': f'{self.name}',
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.gaseous_hydrogen.water_gas_shift.water_gas_shift_disc.WaterGasShiftDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        years = np.arange(2020, 2101)
        invest_level_negative2 = pd.DataFrame({'years': years,
                                               'invest': np.array([7.522704294248678, 4.397620762690489, 1.5216552248664645, 1.188019520330695, -0.11546691751734979, -0.41257105779015807, -0.4713142430480846, -0.31319746735224685, -0.16690328690379208, -0.2953674896238757, -0.10974176540497296, -0.04431473225889518, -0.009472623663265742, 0.003885814982979086, -0.0007055694012350421, -0.00011393262926813614, -3.3872685261797596e-06, -8.703924997983814e-06, -1.4665049507677525e-05, -2.059072317888171e-05, -2.7161719216380482e-05, -3.232975034347975e-05, -3.740296952280585e-05, -4.1313311172826386e-05, -4.425645492583682e-05, -4.942777344794076e-05, -5.789847124589841e-05, -6.394565578633993e-05, -7.021021300977133e-05, -7.867891647474875e-05, -8.579207644338409e-05, -9.338662083573423e-05, -0.00010113459523832584, -0.00010845302260167102, -0.00011443000492139687, -0.00010865689835255025, -0.00010368334812116829, -0.00010068363662879728, -0.00010599120272783614, -0.00011274413831999701, -0.00011912062944804567, -0.0001249199735100783, -0.00013069513039263067, -0.0001359019662573468, -0.0001407205675829992, -0.0001452117877664538, -0.00014966926328034255, -0.00015110222500280956, -0.0001549273958409783, -0.00015934286275895378, -0.00018506627721642197, -0.00018140220007749428, -0.00018605319822709022, 5.645360614672786e-05, 6.97404167835828e-05, 8.446630853955446e-05, 9.723269684086941e-05, 0.0001111989952842278, 0.0001260053875234035, -0.00017068704360819484, -0.00016918266244392158, -0.00016731387735505638, -0.00016504898644959532, -0.00016233409099583162, -0.00015912052652645257, -0.00015522827707199142, -0.00015081428989517791, -0.00014587866079774755, -0.000140485363697795, -0.00013466196390039706, -0.0001284964685488301, -0.00012192138193752173, -0.00011523504936734278, -0.00010836777114685064, -0.00010147728121516361, -9.435997374668482e-05, -8.703097533026997e-05, -7.959580181418732e-05, -7.205334764454085e-05, -6.515432417398242e-05, -5.75540845705268e-05]
                                                                  )})
        self.margin = pd.DataFrame(
            {'years': years, 'margin': np.ones(len(years)) * 110.0})
        # From future of hydrogen
        self.transport = pd.DataFrame(
            {'years': years, 'transport': np.ones(len(years)) * 500.0})

        self.energy_prices = pd.DataFrame({'years': years, 'electricity': [173.742946887766, 161.84399453690324, 151.0934568827067, 145.6720973278901, 139.49228409317507, 134.44503997718164, 132.45608774522722, 130.3584078226701, 127.52060230536652, 124.30846852212048, 121.876714113205, 118.62252128746763, 116.71795424022687, 167.2752172558162, -523.0953324896045, -528.918111017801, -576.4099643084801, -658.0053605080111, -730.6772680971285, -785.5266209814772, -797.9132007448316, -919.81739396033, -1001.1917968512837, -1139.770790907132, -1324.287325439736, -1583.6405633514464, -1881.9375254927998, -2385.5670253259154, -2934.5316632089543, -3616.0518596314323, -4293.301858706722, -5068.310247660651, -5043.909966796937, -4348.314196842799, -3847.051012653862, -2678.331915097737, -4237.473863666849, -43997.76378234717, -57662.84806857981, -90126.1643728083, -102675.91850176449, -107866.10982901936, -105709.67721833434, -103247.16861615339, -99293.19215669605, -95071.34667193386, -99969.47462787508, -89384.8277706707, -74820.72665615268, -46336.79536478433, -8582.926048690295, 121.14749473739688, 4723.561371265998, 7341.6159759343645, 10136.876821286804, 9101.82865778828, 6342.1123055137, 3400.678548474711, 1317.1235285578846, 57.577622122128446, -1556.491379958502, -1527.8815394492137, 71.19007491205002, 71.90450247400986, 73.04452588592403, 74.72620422345085, 80.01340034976249, 79.31149528661388, 78.16811743522783, 76.69328078463764, 74.99219539004162, 73.40249943334788, 72.22664294400238, 71.50963387473212, 71.1772779622413, 71.03516293997427, 69.38040456950807, 70.4079758082903, 71.08045334986878, -3584275.060458262, -2329800.890993138],
                                           'syngas': [42.028563729469255, 40.35463927282826, 29.575202670848103, 27.981919244567436, 28.4608102544913, 28.316848016389194, 28.452220125409035, 28.518772400245417, 28.501110014065095, 27.802297099840523, 27.54682646939144, 27.40656801644799, 27.418462806739104, 31.189223179572366, -24.728921039893294, -26.90568354985612, -28.046716015497623, -30.283415453810335, -28.941595757550658, -29.623696591942917, -26.827592950710255, -32.19992387033324, 18.685880841868766, 40.69582987939884, 142.60965964394347, 213.09181927146068, 194.33247797013246, -129.31362139791605, -364.9916318174153, -519.3552689543824, -1010.3229687947791, -1238.001976203692, -1449.289469300725, -1694.2997749860065, -2121.542803304289, -2292.2389944663987, -1970.1782123951261, -13857.241135917333, -18464.406232355203, -44623.42352636267, -36883.118331365426, -276527.30046885303, -283830.4624060912, -289873.5496481876, -291191.58706974133, -289994.6496434041, -310037.8691776446, -315590.19067057036, -278918.3571185783, -200771.45970661443, -240.72505607533458, 298.34936101320636, 578.3289269483685, 824.8085556685874, 1014.4612670341266, 987.8777994816628, 864.4956766893301, 733.1669150263551, 652.787040677038, 1432.7407835413906, -103796.36080491258, -186994.15306408596, -242071.3490095643, -281081.499027305, -308138.371225125, -328301.5728409703, -344507.7832830466, -360106.32007487403, -374850.788867449, -390003.2486380353, -405411.9698128317, -421287.7163667318, -437160.30903796665, -447053.30091864016, -450237.3621336989, -449052.56334736367, -444609.502771713, -437862.4445371982, -425706.8529415283, -7278394.372789974, -4730642.794054429],
                                           'methane': [36.24200626025384, 36.037823693272635, 37.922057939185905, 37.90938443561647, 37.71337829342477, 37.615460321755776, 37.596894718251846, 37.60924247396737, 37.609470425462696, 37.60927931634897, 37.62597197711281, 37.59995375203008, 37.61604157099432, 38.77860433560488, 22.382983420806866, 22.275678495945428, 21.62480529876592, 19.445196396998853, 8.154240159827438, -5.857045203886088, -20.563162020445404, -50.210373050097886, 121.61528877354448, 194.63500860026892, 245.76877691107757, 308.4145147936679, 316.5737812410774, 229.09745306790273, 99.86876122757712, -133.12886967265482, -287.34739201224124, -669.0498204280948, -916.9026678776249, -1124.128059939944, -1254.2082389576522, -440.2872259645119, -521.3212032762165, -3606.7845279730577, -4894.332073118214, -66201.79861344596, -78797.26601912473, -82098.07410868577, -79776.82854354587, -75569.07982767557, -68873.98794564557, -59804.53414011265, -54773.25302469927, -42431.50638366799, -28839.296760449794, -12237.940018254447, -569.2832658906525, 46.47003318644073, 368.3591878117193, 551.9127707602042, 748.0989259948619, 675.9516783858733, 483.23689784187656, 277.90238181355824, 132.7431105126285, 45.98482807592597, -68.87724240212421, -65.8466467440932, 48.67526346490955, 49.110304914707, 49.484762952469, 49.827024334513965, 50.40288573635448, 50.54081705712744, 51.53823505104759, 52.685303924832965, 56.2277300574674, 70.42627292948146, 121.95161931317762, 157.0563442922703, 161.15421153352872, 165.15600888621702, 168.89473198397354, 172.84836967336923, 176.61716464734127, -253334.87584684434, -164597.48887207167],
                                           'hydrogen.gaseous_hydrogen': 50
                                           })
        self.energy_carbon_emissions = pd.DataFrame(
            {'years': years, 'electricity': 0.02, 'syngas': 0.2, 'methane': 0.1})
        #---Ratios---
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.linspace(0.2, 0.8, len(years))))
        demand_ratio_dict['years'] = years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)

        resource_ratio_dict = dict(
            zip(EnergyMix.RESOURCE_LIST, np.linspace(0.9, 0.3, len(years))))
        resource_ratio_dict['years'] = years
        self.all_resource_ratio_usable_demand = pd.DataFrame(
            resource_ratio_dict)
        inputs_dict = {f'{self.name}.year_start': 2020,
                       f'{self.name}.year_end': 2100,
                       f'{self.name}.resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2101)),
                       f'{self.name}.resources_price': get_static_prices(np.arange(2020, 2101)),
                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.invest_level': invest_level_negative2,
                       f'{self.name}.CO2_taxes': pd.DataFrame({'years': years,
                                                               'CO2_tax': [123.54384121665328, 114.7082570056495, 111.79900662991061, 112.3606560123489, 112.24318143946093, 108.5973365343437, 111.64328685134457, 113.73818514404302, 115.44107859484396, 117.29642045913171, 119.82439960611056, 121.464647487607, 122.5798798443514, 122.71077795239975, -1.7955406835675085e-164, -9.38522063906998e-05, 59.58305264461431, 42.666185997774306, 58.18945121886229, 77.59910169875373, 79.02437166207574, 56.846842881037986, 36.84087540937685, 8.375739638451805, -26.271722405364585, -73.13382129365696, -126.22396480678202, -216.74846182912307, -320.8891223045025, -454.43147688511283, -592.8993534945333, -755.2557919477246, -771.1848158848073, -652.3226212321947, -530.2039192199904, -53.28278546561114, 262.27957667462624, -12389.602358460908, -16331.512721893621, -25706.169003479095, -29335.130871510242, -30839.9018083875, -30222.41584546385, -29516.449359907347, -28378.57140441338, -27161.3708567085, -28583.725076098905, -25519.90979099596, -21284.997839858734, -13030.47433106795, -1.796069506092857e-177, -8.646541630835338e-50, -0.006235676979016444, 7.577971430943959, 7.805235704875154, 8.043943276838133, 8.194668613555146, 8.350701949669254, 8.511980365280179, 190.31707811919773, 35.44528076658935, 110.84893364939308, 401.56773487563987, 433.883395822344, 455.0193279201958, 467.252737051429, 476.77566104458674, 484.77931831720707, 492.4141556543145, 499.85661992787936, 507.25923472515206, 514.7195372202477, 522.1622160510997, 528.0688453927651, 532.2967343650598, 535.4132571425507, 537.3738970934646, 539.1620166124048, 539.4654629652432, -538303.205284354, -349711.48482286936]
                                                               }),
                       f'{self.name}.transport_margin': self.margin,
                       f'{self.name}.transport_cost': self.transport,
                       f'{self.name}.{self.model_name}.margin':  self.margin,
                       f'{self.name}.syngas_ratio': np.array([75.44562167,  75.9365319,  50.6136473,  46.25021383,
                                                              48.09049977,  48.58538416,  48.67268041,  48.7293315,
                                                              48.74871786,  48.87523068,  48.00221129,  47.64452911,
                                                              47.48546312,  47.02906479,  46.78210832,  46.79495308,
                                                              46.55321567,  46.14947879,  45.51084103,  45.15597608,
                                                              44.61375801,  44.10023154,  43.59883491,  43.13656167,
                                                              39.20492351,  36.7976312,  35.50088456,  35.99507168,
                                                              36.4371484,  36.789612,  37.44521793,  37.38248237,
                                                              36.96999069,  37.05880692,  36.92689153,  36.87091339,
                                                              35.98975497,  34.50696386,  34.64195472,  35.2896656,
                                                              84.30570468, 110.28022157, 110.28022157, 110.28022157,
                                                              110.28022157, 110.28022157, 110.28022157, 110.28022157,
                                                              110.28022157, 110.28022157, 110.28022157, 110.28022157,
                                                              110.28022157, 110.28022157, 110.28022157, 110.28022157,
                                                              110.28022157, 110.28022157, 110.28022157, 110.28022157,
                                                              110.28022157, 110.28022157, 110.28022157, 110.28022157,
                                                              110.28022157, 110.28022157, 110.28022157, 110.28022157,
                                                              110.28022157, 110.28022157, 110.28022157, 110.28022157,
                                                              110.28022157, 110.28022157, 110.28022157, 110.28022157,
                                                              110.28022157, 110.28022157, 110.28022157, 110.28022157,
                                                              110.28022157]),
                       f'{self.name}.syngas_ratio_technos': self.syngas_ratio_technos,
                       f'{self.name}.energy_detailed_techno_prices': self.syngas_detailed_prices,
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        disc_techno = self.ee.root_process.sos_disciplines[0]

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}_negative.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step',
                            inputs=[f'{self.name}.{self.model_name}.invest_level',
                                    f'{self.name}.energy_prices',
                                    f'{self.name}.energy_CO2_emissions',
                                    f'{self.name}.syngas_ratio',
                                    f'{self.name}.CO2_taxes',
                                    f'{self.name}.resources_price',
                                    f'{self.name}.resources_CO2_emissions',
                                    ],
                            outputs=[f'{self.name}.{self.model_name}.techno_prices',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.techno_consumption',
                                     f'{self.name}.{self.model_name}.techno_consumption_woratio',
                                     f'{self.name}.{self.model_name}.techno_production',
                                     ],)

    def test_08_gaseous_hydrogen_discipline_jacobian(self):

        self.name = 'Test'
        self.energy_name = 'hydrogen.gaseous_hydrogen'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': f'{self.name}',
                   'ns_hydrogen': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_resource': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.stream_type.energy_disciplines.gaseous_hydrogen_disc.GaseousHydrogenDiscipline'
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
    cls = HydrogenJacobianTestCase()
    cls.setUp()
    # unittest.main()
    cls.test_01_wgs_jacobian()
    print('------')
