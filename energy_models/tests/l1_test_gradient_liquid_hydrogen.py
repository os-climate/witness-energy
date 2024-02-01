'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/14-2023/11/16 Copyright 2023 Capgemini

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

import pickle
from os.path import join, dirname

import numpy as np
import pandas as pd
import scipy.interpolate as sc

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.energy_models.liquid_hydrogen import LiquidHydrogen
from energy_models.core.stream_type.resources_data_disc import get_static_CO2_emissions, \
    get_static_prices
from energy_models.glossaryenergy import GlossaryEnergy
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tests.core.abstract_jacobian_unit_test import AbstractJacobianUnittest


class LiquidHydrogenJacobianTestCase(AbstractJacobianUnittest):
    """
    LiquidHydrogen jacobian test class
    """

    # AbstractJacobianUnittest.DUMP_JACOBIAN = True

    def analytic_grad_entry(self):
        return [
            self.test_01_hydrogen_liquefaction_jacobian,
            self.test_02_liquid_hydrogen_discipline_jacobian,
        ]

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.energy_name = 'liquid_hydrogen'

        years = np.arange(GlossaryEnergy.YeartStartDefault, 2050 + 1)

        self.years = years

        self.hydrogen_liquefaction_techno_prices = pd.DataFrame(
            {'HydrogenLiquefaction': np.array([0.09, 0.08974117039450046, 0.08948672733558984,
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
             'HydrogenLiquefaction_wotaxes': np.array([0.09, 0.08974117039450046, 0.08948672733558984,
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

        self.hydrogen_liquefaction_consumption = pd.DataFrame({GlossaryEnergy.Years: years,
                                                               'hydrogen.gaseous_hydrogen (TWh)': [230.779470] * len(
                                                                   years),
                                                               'electricity (TWh)': [82.649011] * len(years), })

        self.hydrogen_liquefaction_production = pd.DataFrame({GlossaryEnergy.Years: years,
                                                              LiquidHydrogen.name + ' (TWh)': [2304.779470] * len(
                                                                  years), })

        self.hydrogen_liquefaction_carbon_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'HydrogenLiquefaction': 0.0, 'hydrogen.gaseous_hydrogen': 0.0,
             'electricity': 0.0,
             'production': 0.0})

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

        self.energy_prices = pd.DataFrame({GlossaryEnergy.Years: years, 'electricity': electricity_price,
                                           'hydrogen.gaseous_hydrogen': np.ones(len(years)) * 33.,
                                           })

        self.energy_carbon_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'electricity': 0.02, 'hydrogen.gaseous_hydrogen': 0.0})

        self.invest_level = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.InvestValue: np.ones(len(years)) * 0.1715})

        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [14.86, 17.22, 20.27,
                     29.01, 34.05, 39.08, 44.69, 50.29]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.CO2Tax: func(years)})
        self.margin = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.MarginValue: np.ones(len(years)) * 110.0})
        # From future of hydrogen
        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'transport': np.ones(len(years)) * 500.0})

        CO2_tax = np.array([0.01722, 0.033496, 0.049772, 0.066048, 0.082324, 0.0986,
                            0.114876, 0.131152, 0.147428, 0.163704, 0.17998, 0.217668,
                            0.255356, 0.293044, 0.330732, 0.36842, 0.406108, 0.443796,
                            0.481484, 0.519172, 0.55686, 0.591706, 0.626552, 0.661398,
                            0.696244, 0.73109, 0.765936, 0.800782, 0.835628, 0.870474,
                            0.90532]) * 1000
        self.CO2_taxes = pd.DataFrame({GlossaryEnergy.Years: years,
                                       GlossaryEnergy.CO2Tax: CO2_tax})

        self.invest = pd.DataFrame({GlossaryEnergy.Years: years,
                                    GlossaryEnergy.InvestValue: np.array([4435750000.0, 4522000000.0, 4608250000.0,
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
            {GlossaryEnergy.Years: years, 'random techno (Gha)': 0.0})

        self.land_use_required_HydrogenLiquefaction = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'HydrogenLiquefaction (Gha)': 0.0})
        # ---Ratios---
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.linspace(1.0, 1.0, len(years))))
        demand_ratio_dict[GlossaryEnergy.Years] = years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)

        resource_ratio_dict = dict(
            zip(EnergyMix.RESOURCE_LIST, np.linspace(1.0, 1.0, len(years))))
        resource_ratio_dict[GlossaryEnergy.Years] = years
        self.all_resource_ratio_usable_demand = pd.DataFrame(
            resource_ratio_dict)

    def tearDown(self):
        pass

    def test_01_hydrogen_liquefaction_jacobian(self):

        self.name = 'Test'
        self.model_name = 'hydrogen_liquefaction'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_hydrogen': f'{self.name}',
                   'ns_liquid_hydrogen': f'{self.name}',
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.liquid_hydrogen.hydrogen_liquefaction.hydrogen_liquefaction_disc.HydrogenLiquefactionDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearEnd}': 2050,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_static_CO2_emissions(
                           np.arange(GlossaryEnergy.YeartStartDefault, 2050 + 1)),
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_static_prices(
                           np.arange(GlossaryEnergy.YeartStartDefault, 2050 + 1)),
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.CO2_taxes,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': pd.concat(
                           [self.margin[GlossaryEnergy.Years], self.margin[GlossaryEnergy.MarginValue] / 1.1],
                           axis=1, keys=[GlossaryEnergy.Years, GlossaryEnergy.MarginValue]),
                       f'{self.name}.{GlossaryEnergy.EnergyPricesValue}': self.energy_prices,
                       f'{self.name}.{GlossaryEnergy.EnergyCO2EmissionsValue}': self.energy_carbon_emissions,
                       f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline
        # AbstractJacobianUnittest.DUMP_JACOBIAN = True
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryEnergy.UtilisationRatioValue}',
                                    f'{self.name}.{GlossaryEnergy.EnergyPricesValue}',
                                    f'{self.name}.{GlossaryEnergy.EnergyCO2EmissionsValue}',
                                    f'{self.name}.{GlossaryEnergy.CO2TaxesValue}'],
                            outputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoPricesValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.CO2EmissionsValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoProductionValue}', ], )

    def test_02_liquid_hydrogen_discipline_jacobian(self):
        self.name = 'Test'
        self.energy_name = 'hydrogen.liquid_hydrogen'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': f'{self.name}',
                   'ns_liquid_hydrogen': f'{self.name}',
                   'ns_hydrogen': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_resource': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.stream_type.energy_disciplines.liquid_hydrogen_disc.LiquidHydrogenDiscipline'
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
            if key in [GlossaryEnergy.techno_list, GlossaryEnergy.CO2TaxesValue, GlossaryEnergy.YearStart,
                       GlossaryEnergy.YearEnd,
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

        inputs_dict[f'{namespace}.{self.energy_name}.HydrogenLiquefaction.{GlossaryEnergy.TechnoProductionValue}'][
            'hydrogen.liquid_hydrogen (TWh)'] *= np.linspace(5.0, 5.0, len(self.years))

        technos = inputs_dict[f"{self.name}.technologies_list"]
        techno_capital = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.Capital: 20000 * np.ones_like(self.years)
        })
        for techno in technos:
            inputs_dict[
                f"{self.name}.{self.energy_name}.{techno}.{GlossaryEnergy.TechnoCapitalValue}"] = techno_capital
            coupled_inputs.append(f"{self.name}.{self.energy_name}.{techno}.{GlossaryEnergy.TechnoCapitalValue}")

        coupled_outputs.append(f"{self.name}.{self.energy_name}.{GlossaryEnergy.EnergyTypeCapitalDfValue}")
        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.energy_name}')[0].mdo_discipline_wrapp.mdo_discipline
        # AbstractJacobianUnittest.DUMP_JACOBIAN = True

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}.pkl',
                            discipline=disc, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc.local_data,
                            inputs=coupled_inputs,
                            outputs=coupled_outputs, )


if '__main__' == __name__:
    # AbstractJacobianUnittest.DUMP_JACOBIAN = True
    cls = LiquidHydrogenJacobianTestCase()
    cls.setUp()
    cls.test_02_liquid_hydrogen_discipline_jacobian()
