'''
Copyright 2023 Capgemini

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
from os.path import dirname

import numpy as np
import pandas as pd
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tests.core.abstract_jacobian_unit_test import (
    AbstractJacobianUnittest,
)

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.resources_data_disc import (
    get_default_resources_CO2_emissions,
    get_default_resources_prices,
)
from energy_models.glossaryenergy import GlossaryEnergy


class CleanEnergySimpleTechnoJacobianTestCase(AbstractJacobianUnittest):
    """CleanEnergySimpleTechnoJacobianTestCase"""

    def analytic_grad_entry(self):
        return [
            self.test_01_discipline_analytic_grad,
        ]

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.energy_name = GlossaryEnergy.CleanEnergySimpleTechno
        self.year_end = GlossaryEnergy.YearEndDefaultValueGradientTest
        self.years = np.arange(GlossaryEnergy.YearStartDefault, self.year_end + 1)
        self.resource_list = [
            'oil_resource', 'natural_gas_resource', 'uranium_resource', 'coal_resource']
        self.ratio_available_resource = pd.DataFrame(
            {GlossaryEnergy.Years: self.years})
        for types in self.resource_list:
            self.ratio_available_resource[types] = np.linspace(
                1, 1, len(self.ratio_available_resource.index))
        # We take biomass price of methane/5.0
        self.stream_prices = pd.DataFrame({GlossaryEnergy.Years: self.years, GlossaryEnergy.electricity: 90.
                                           })

        self.stream_co2_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.electricity: 10.0})

        self.invest_level = pd.DataFrame(
            {GlossaryEnergy.Years: self.years,
             GlossaryEnergy.InvestValue: 33.0 * 1.10 ** (self.years - GlossaryEnergy.YearStartDefault)})
        

        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.CO2Tax: np.linspace(14., 40., len(self.years))})
        self.margin = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.MarginValue: 110.0})
        # From future of hydrogen
        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, 'transport': 13.})
        self.scaling_factor_techno_consumption = 1e3
        self.scaling_factor_techno_production = 1e3
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.ones((len(self.years), len(self.years)))))
        demand_ratio_dict[GlossaryEnergy.Years] = self.years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)
        self.is_stream_demand = True
        self.is_apply_resource_ratio = True

    def tearDown(self):
        pass

    def test_01_discipline_analytic_grad(self):
        self.name = 'Test'
        self.model_name = GlossaryEnergy.CleanEnergySimpleTechno
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name,
                   'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_clean_energy': self.name,
                   'ns_resource': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.clean_energy.clean_energy_simple_techno.clean_energy_simple_techno_disc.CleanEnergySimpleTechnoDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        techno_infos_dict = {'maturity': 0,
                             'Opex_percentage': 0.12,
                             'WACC': 0.058,
                             'learning_rate': 0.00,
                                                  'Capex_init': 230.0,
                             'Capex_init_unit': '$/MWh',
                             'techno_evo_eff': 'no',
                             'efficiency': 1.0,
                             'CO2_from_production': 0.0,
                             'CO2_from_production_unit': 'kg/kg',
                             GlossaryEnergy.ConstructionDelay: 3,
                             'resource_price': 70.0,
                             'resource_price_unit': '$/MWh'}

        invest_before_ystart = pd.DataFrame(
            {'past years': np.arange(-3, 0), GlossaryEnergy.InvestValue: [0.0, 635.0, 638.0]})

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.ConstructionDelay}': 3,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                           np.arange(GlossaryEnergy.YearStartDefault, self.year_end + 1)),
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_default_resources_prices(
                           np.arange(GlossaryEnergy.YearStartDefault, self.year_end + 1)),
                       f'{self.name}.techno_infos_dict': techno_infos_dict,
                       f'{self.name}.{GlossaryEnergy.InvestmentBeforeYearStartValue}': invest_before_ystart,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)
        self.ee.execute()
        disc_techno = self.ee.root_process.proxy_disciplines[0].discipline_wrapp.discipline
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-18, derr_approx='complex_step',
                            local_data=disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}',
                                    f'{self.name}.{GlossaryEnergy.StreamPricesValue}',
                                    f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}',
                                    f'{self.name}.{GlossaryEnergy.CO2TaxesValue}',
                                    f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}',
                                    f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}',
                                    f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}',
                                    ],
                            outputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoPricesValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.CO2EmissionsValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoProductionValue}',
                                     ], )

    def test_02_discipline_analytic_grad_construction_delay_0(self):
        self.name = 'Test'
        self.model_name = GlossaryEnergy.CleanEnergySimpleTechno
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name,
                   'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_clean_energy': self.name,
                   'ns_resource': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.clean_energy.clean_energy_simple_techno.clean_energy_simple_techno_disc.CleanEnergySimpleTechnoDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        techno_infos_dict = {'maturity': 0,
                             'Opex_percentage': 0.12,
                             'WACC': 0.058,
                             'learning_rate': 0.00,
                                                  'Capex_init': 230.0,
                             'Capex_init_unit': '$/MWh',
                             'techno_evo_eff': 'no',
                             'efficiency': 1.0,
                             'CO2_from_production': 0.0,
                             'CO2_from_production_unit': 'kg/kg',
                             GlossaryEnergy.ConstructionDelay: 0,
                             'resource_price': 70.0,
                             'resource_price_unit': '$/MWh'}

        invest_before_ystart = pd.DataFrame(
            {'past years': [], GlossaryEnergy.InvestValue: []})

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                           np.arange(GlossaryEnergy.YearStartDefault, self.year_end + 1)),
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_default_resources_prices(
                           np.arange(GlossaryEnergy.YearStartDefault, self.year_end + 1)),
                       f'{self.name}.techno_infos_dict': techno_infos_dict,
                       f'{self.name}.{GlossaryEnergy.InvestmentBeforeYearStartValue}': invest_before_ystart,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)
        self.ee.execute()
        disc_techno = self.ee.root_process.proxy_disciplines[0].discipline_wrapp.discipline
        self.check_jacobian(location=dirname(__file__),
                            filename=f'jacobian_{self.energy_name}_{self.model_name}_construction_delay_0.pkl',
                            discipline=disc_techno, step=1.0e-18, derr_approx='complex_step',
                            local_data=disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}',
                                    f'{self.name}.{GlossaryEnergy.StreamPricesValue}',
                                    f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}',
                                    f'{self.name}.{GlossaryEnergy.CO2TaxesValue}',
                                    f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}',
                                    f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}',
                                    ],
                            outputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoPricesValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.CO2EmissionsValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoProductionValue}',
                                     ], )
