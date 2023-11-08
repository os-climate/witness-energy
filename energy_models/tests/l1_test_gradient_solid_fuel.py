'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/14-2023/11/03 Copyright 2023 Capgemini

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

from climateeconomics.glossarycore import GlossaryCore
from energy_models.glossaryenergy import GlossaryEnergy
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from energy_models.core.stream_type.resources_data_disc import get_static_CO2_emissions, \
    get_static_prices
from sostrades_core.tests.core.abstract_jacobian_unit_test import AbstractJacobianUnittest
from energy_models.core.energy_mix.energy_mix import EnergyMix
import pickle


class SolidFuelJacobianTestCase(AbstractJacobianUnittest):
    """
    Solid fuel jacobian test class
    """

    # AbstractJacobianUnittest.DUMP_JACOBIAN = True

    def analytic_grad_entry(self):
        return [
            self.test_01_coal_extraction_jacobian,
            self.test_02_pelletizing_jacobian,
            self.test_03_solid_fuel_discipline_jacobian,
        ]

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.energy_name = 'solid_fuel'
        years = np.arange(2020, 2051)
        self.years = years
        # crude oil price : 1.5$/gallon /43.9
        self.energy_prices = pd.DataFrame(
            {GlossaryCore.Years: years, 'electricity': np.array([0.16, 0.15974117039450046, 0.15948672733558984,
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
             'biomass_dry': np.ones(len(years)) * 68.12 / 3.36

             })

        self.energy_carbon_emissions = pd.DataFrame(
            {GlossaryCore.Years: years, 'electricity': 0.0, 'biomass_dry': - 0.425 * 44.01 / 12.0})
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
                           ]) / 40 * 1e-9

        self.invest_level_pellet = pd.DataFrame(
            {GlossaryCore.Years: years, GlossaryCore.InvestValue: np.array([12009047700.0, 13746756900.0, 15735912630.0,
                                                 18012899180.0, 20619365690.0, 23602987910.0,
                                                 23602987910.0, 23602987910.0, 23602987910.0,
                                                 23602987910.0, 23602987910.0, 23602987910.0,
                                                 23602987910.0, 23602987910.0, 23602987910.0,
                                                 23602987910.0, 23602987910.0, 23602987910.0,
                                                 23602987910.0, 23602987910.0, 23602987910.0,
                                                 23602987910.0, 23602987910.0, 23602987910.0,
                                                 23602987910.0, 23602987910.0, 23602987910.0,
                                                 23602987910.0, 23602987910.0, 23602987910.0,
                                                 23602987910.0]) * 1e-9})

        self.invest_level = pd.DataFrame(
            {GlossaryCore.Years: years, GlossaryCore.InvestValue: invest})
        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [14.86, 17.22, 20.27,
                     29.01, 34.05, 39.08, 44.69, 50.29]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {GlossaryCore.Years: years, GlossaryCore.CO2Tax: func(years)})
        self.margin = pd.DataFrame(
            {GlossaryCore.Years: years, GlossaryCore.MarginValue: np.ones(len(years)) * 110.0})
        self.transport = pd.DataFrame(
            {GlossaryCore.Years: years, 'transport': np.ones(len(years)) * 7.6})

        self.transport_pellet = pd.DataFrame(
            {GlossaryCore.Years: years, 'transport': np.ones(len(years)) * 0.0097187})

        biblio_data_path = join(
            dirname(__file__), 'output_values_check', 'biblio_data.csv')
        self.biblio_data = pd.read_csv(biblio_data_path)
        self.biblio_data = self.biblio_data.loc[self.biblio_data['sos_name']
                                                == 'solid_fuel.CoalExtraction']

        self.resources_price = pd.DataFrame(columns=[GlossaryCore.Years, 'CO2', 'water'])
        self.resources_price[GlossaryCore.Years] = years
        self.resources_price['CO2'] = np.array(
            [0.04, 0.041, 0.042, 0.043, 0.044, 0.045, 0.0464, 0.047799999999999995, 0.049199999999999994, 0.0506, 0.052,
             0.0542,
             0.0564, 0.0586, 0.0608, 0.063, 0.0652, 0.0674, 0.0696, 0.0718, 0.074, 0.0784, 0.0828, 0.0872, 0.0916,
             0.096, 0.1006, 0.1052, 0.1098, 0.1144, 0.119]) * 1000.0
        # ---Ratios---
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.linspace(1.0, 1.0, len(years))))
        demand_ratio_dict[GlossaryCore.Years] = years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)

        resource_ratio_dict = dict(
            zip(EnergyMix.RESOURCE_LIST, np.linspace(1.0, 1.0, len(years))))
        resource_ratio_dict[GlossaryCore.Years] = years
        self.all_resource_ratio_usable_demand = pd.DataFrame(
            resource_ratio_dict)

    def tearDown(self):
        pass

    def test_01_coal_extraction_jacobian(self):

        self.name = 'Test'
        self.model_name = 'coal_extraction'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_solid_fuel': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.solid_fuel.coal_extraction.coal_extraction_disc.CoalExtractionDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryCore.YearEnd}': 2050,
                       f'{self.name}.{GlossaryCore.RessourcesCO2EmissionsValue}': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.{GlossaryCore.ResourcesPriceValue}': get_static_prices(np.arange(2020, 2051)),
                       f'{self.name}.{GlossaryCore.EnergyPricesValue}': self.energy_prices,
                       f'{self.name}.{GlossaryCore.EnergyCO2EmissionsValue}': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryCore.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{GlossaryCore.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryCore.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryCore.TransportCostValue}': self.transport,
                       f'{self.name}.{self.model_name}.{GlossaryCore.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryCore.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }
        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryCore.InvestLevelValue}',
                                    f'{self.name}.{GlossaryCore.EnergyPricesValue}',
                                    f'{self.name}.{GlossaryCore.EnergyCO2EmissionsValue}',
                                    f'{self.name}.{GlossaryCore.CO2TaxesValue}',
                                    f'{self.name}.{GlossaryCore.ResourcesPriceValue}',
                                    f'{self.name}.{GlossaryCore.RessourcesCO2EmissionsValue}', ],
                            outputs=[f'{self.name}.{self.model_name}.{GlossaryCore.TechnoPricesValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.CO2EmissionsValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.TechnoConsumptionValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.TechnoConsumptionWithoutRatioValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.TechnoProductionValue}',
                                     ], )

    def test_02_pelletizing_jacobian(self):

        self.name = 'Test'
        self.model_name = 'pelletizing'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_solid_fuel': self.name, 'ns_energy_study': f'{self.name}',
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.solid_fuel.pelletizing.pelletizing_disc.PelletizingDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryCore.YearEnd}': 2050,
                       f'{self.name}.{GlossaryCore.RessourcesCO2EmissionsValue}': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.{GlossaryCore.ResourcesPriceValue}': get_static_prices(np.arange(2020, 2051)),
                       f'{self.name}.{GlossaryCore.EnergyPricesValue}': self.energy_prices,
                       f'{self.name}.{GlossaryCore.EnergyCO2EmissionsValue}': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryCore.InvestLevelValue}': self.invest_level_pellet,
                       f'{self.name}.{GlossaryCore.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryCore.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryCore.TransportCostValue}': self.transport_pellet,
                       f'{self.name}.{self.model_name}.{GlossaryCore.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryCore.ResourcesPriceValue}': self.resources_price,
                       f'{self.name}.{GlossaryCore.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryCore.InvestLevelValue}',
                                    f'{self.name}.{GlossaryCore.EnergyPricesValue}',
                                    f'{self.name}.{GlossaryCore.EnergyCO2EmissionsValue}',
                                    f'{self.name}.{GlossaryCore.CO2TaxesValue}'],
                            outputs=[f'{self.name}.{self.model_name}.{GlossaryCore.TechnoPricesValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.CO2EmissionsValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.TechnoConsumptionValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.TechnoConsumptionWithoutRatioValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.TechnoProductionValue}',
                                     ], )

    def test_03_solid_fuel_discipline_jacobian(self):

        self.name = 'Test'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': f'{self.name}',
                   'ns_solid_fuel': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_resource': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.stream_type.energy_disciplines.solid_fuel_disc.SolidFuelDiscipline'
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
            if key in [GlossaryCore.techno_list, GlossaryCore.CO2TaxesValue, GlossaryCore.YearStart, GlossaryCore.YearEnd,
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
    cls = SolidFuelJacobianTestCase()
    cls.setUp()
    cls.test_01_coal_extraction_jacobian()
