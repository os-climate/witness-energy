'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/14-2023/11/02 Copyright 2023 Capgemini

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
from os.path import join, dirname
import scipy.interpolate as sc

from climateeconomics.glossarycore import GlossaryCore
from energy_models.glossaryenergy import GlossaryEnergy
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from energy_models.core.stream_type.resources_data_disc import get_static_CO2_emissions, \
    get_static_prices
from sostrades_core.tests.core.abstract_jacobian_unit_test import AbstractJacobianUnittest
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
from energy_models.core.energy_mix.energy_mix import EnergyMix
import pickle


class MethaneJacobianTestCase(AbstractJacobianUnittest):
    """
    Methane jacobian test class
    """

    # AbstractJacobianUnittest.DUMP_JACOBIAN = True

    def analytic_grad_entry(self):
        return [
            self.test_01_fossil_gas_discipline_jacobian,
            self.test_02_methanation_discipline_jacobian,
            self.test_03_upgrading_biogas_discipline_jacobian,
            self.test_04_methane_discipline_jacobian,
        ]

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.energy_name = 'methane'
        self.year_start = 2020
        self.year_end = 2050
        years = np.arange(self.year_start, self.year_end + 1)
        self.years = years
        self.energy_prices = pd.DataFrame({'years': years,
                                           'electricity': np.array([0.09, 0.08974117039450046, 0.08948672733558984,
                                                                    0.089236536471781, 0.08899046935409588,
                                                                    0.08874840310033885,
                                                                    0.08875044941298937, 0.08875249600769718,
                                                                    0.08875454288453355,
                                                                    0.08875659004356974, 0.0887586374848771,
                                                                    0.08893789675406477,
                                                                    0.08911934200930778, 0.08930302260662477,
                                                                    0.08948898953954933,
                                                                    0.08967729551117891, 0.08986799501019029,
                                                                    0.09006114439108429,
                                                                    0.09025680195894345, 0.09045502805900876,
                                                                    0.09065588517140537,
                                                                    0.0908594380113745, 0.09106575363539733,
                                                                    0.09127490155362818,
                                                                    0.09148695384909017, 0.0917019853041231,
                                                                    0.0919200735346165,
                                                                    0.09214129913260598, 0.09236574581786147,
                                                                    0.09259350059915213,
                                                                    0.0928246539459331]) * 1000.0,
                                           'hydrogen.gaseous_hydrogen': np.array(
                                               [0.1266023955250543, 0.12472966837635774, 0.12308937523217356,
                                                0.12196584543238155,
                                                0.12101159171871603, 0.12018900859836591, 0.1192884942915236,
                                                0.11865333029969044,
                                                0.11827242819796199, 0.11804896544898459, 0.11796960162047375,
                                                0.11791110278481422,
                                                0.11784598237652186, 0.11776392989648421, 0.11836724143081659,
                                                0.11883282673049182,
                                                0.11917648165844891, 0.1197345556855176, 0.12008291652658049,
                                                0.1204305172545244,
                                                0.12102683407269707, 0.12186763004213008, 0.12326379102943016,
                                                0.12412292194034467,
                                                0.12433514237290824, 0.12511526161029957, 0.12590456744159823,
                                                0.1267030200703957,
                                                0.12691667296790637, 0.12714334679576733, 0.12738215136005188]) * 1000,
                                           'biogas': np.array(
                                               [0.06363, 0.0612408613576689, 0.059181808246196024, 0.05738028027202377,
                                                0.0557845721244601, 0.05435665353332419, 0.05225877624361548,
                                                0.05045797192512811, 0.04888746457113824, 0.04750006564084081,
                                                0.04626130284326101, 0.044848110567750024, 0.043596892851567724,
                                                0.04247763196812953, 0.04146768302263715, 0.04054957955940597,
                                                0.03970959176775726, 0.03893674917609171, 0.038222160192931814,
                                                0.03755852715493717, 0.03693979356326306, 0.03636088278590117,
                                                0.03581750135963429, 0.03530598876014997, 0.03482320115289285,
                                                0.03436642036567466, 0.03393328183670935, 0.033521717015978045,
                                                0.03312990690071806, 0.032756244237772174, 0.03239930253734476]) * 1000

                                           })

        self.energy_carbon_emissions = pd.DataFrame(
            {'years': years, 'electricity': 0.0, 'hydrogen.gaseous_hydrogen': 0.0, 'biogas': -0.51})
        # Use the same inest as SMR techno

        self.invest_level_methanation = pd.DataFrame({'years': years,
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
                     29.01, 34.05, 39.08, 44.69, 50.29]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {'years': years, 'CO2_tax': func(years)})
        self.margin = pd.DataFrame(
            {'years': years, 'margin': np.ones(len(years)) * 110.0})
        self.transport = pd.DataFrame(
            {'years': years, 'transport': np.ones(len(years)) * 200.0})

        self.resources_price = pd.DataFrame(
            columns=['years', ResourceGlossary.CO2['name'], ResourceGlossary.Water['name']])
        self.resources_price['years'] = years
        self.resources_price[ResourceGlossary.CO2['name']] = np.array(
            [0.04, 0.041, 0.042, 0.043, 0.044, 0.045, 0.0464, 0.047799999999999995, 0.049199999999999994, 0.0506, 0.052,
             0.0542,
             0.0564, 0.0586, 0.0608, 0.063, 0.0652, 0.0674, 0.0696, 0.0718, 0.074, 0.0784, 0.0828, 0.0872, 0.0916,
             0.096, 0.1006, 0.1052, 0.1098, 0.1144, 0.119]) * 1000.0
        self.resources_price[ResourceGlossary.Water['name']] = 1.4
        # ---Ratios---
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.linspace(1.0, 1.0, len(years))))
        demand_ratio_dict['years'] = years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)

        resource_ratio_dict = dict(
            zip(EnergyMix.RESOURCE_LIST, np.linspace(0.8, 0.1, len(years))))
        resource_ratio_dict['years'] = years
        self.all_resource_ratio_usable_demand = pd.DataFrame(
            resource_ratio_dict)

    def tearDown(self):
        pass

    def test_01_fossil_gas_discipline_jacobian(self):

        self.name = 'Test'
        self.model_name = 'fossil_gas'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_methane': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.methane.fossil_gas.fossil_gas_disc.FossilGasDiscipline'
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
                       f'{self.name}.{self.model_name}.margin': self.margin,
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline

        # AbstractJacobianUnittest.DUMP_JACOBIAN=True
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc_techno.local_data,
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
                                     ], )

    def test_02_methanation_discipline_jacobian(self):

        self.name = 'Test'
        self.model_name = 'methanation'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_methane': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.methane.methanation.methanation_disc.MethanationDiscipline'
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
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level_methanation,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.transport_margin': self.margin,
                       f'{self.name}.transport_cost': self.transport,
                       f'{self.name}.{self.model_name}.margin': self.margin,
                       f'{self.name}.resources_price': self.resources_price,
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc_techno.local_data,
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
                                     ], )

    def test_03_upgrading_biogas_discipline_jacobian(self):

        self.name = 'Test'
        self.model_name = 'upgrading_biogas'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_methane': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.methane.upgrading_biogas.upgrading_biogas_disc.UpgradingBiogasDiscipline'
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
                       f'{self.name}.{self.model_name}.margin': self.margin,
                       f'{self.name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc_techno.local_data,
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
                                     ], )

    def test_04_methane_discipline_jacobian(self):

        self.name = 'Test'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': f'{self.name}',
                   'ns_methane': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_resource': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.stream_type.energy_disciplines.methane_disc.MethaneDiscipline'
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
                inputs_dict[f'{namespace}.{self.energy_name}.{key}'] = mda_data_input_dict[self.energy_name][key][
                    'value']
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

        technos = inputs_dict[f"{self.name}.technologies_list"]
        techno_capital = pd.DataFrame({
            GlossaryCore.Years: self.years,
            GlossaryCore.Capital: 20000 * np.ones_like(self.years)
        })
        for techno in technos:
            inputs_dict[
                f"{self.name}.{self.energy_name}.{techno}.{GlossaryEnergy.TechnoCapitalDfValue}"] = techno_capital
            coupled_inputs.append(f"{self.name}.{self.energy_name}.{techno}.{GlossaryEnergy.TechnoCapitalDfValue}")

        coupled_outputs.append(f"{self.name}.{self.energy_name}.{GlossaryEnergy.EnergyTypeCapitalDfValue}")

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.energy_name}')[0].mdo_discipline_wrapp.mdo_discipline
        #AbstractJacobianUnittest.DUMP_JACOBIAN = True

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}.pkl',
                            discipline=disc, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc.local_data,
                            inputs=coupled_inputs,
                            outputs=coupled_outputs, )


if '__main__' == __name__:
    # AbstractJacobianUnittest.DUMP_JACOBIAN = True
    cls = MethaneJacobianTestCase()
    cls.setUp()
    cls.test_02_methanation_discipline_jacobian()
