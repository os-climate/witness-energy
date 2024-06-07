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
import scipy.interpolate as sc
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tests.core.abstract_jacobian_unit_test import (
    AbstractJacobianUnittest,
)

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.resources_data_disc import (
    get_static_CO2_emissions,
    get_static_prices,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.fossil.fossil_simple_techno.fossil_simple_techno_disc import (
    FossilSimpleTechnoDiscipline,
)


class FossilSimpleTechnoJacobianTestCase(AbstractJacobianUnittest):
    """FossilSimpleTechnoJacobianTestCase"""

    def analytic_grad_entry(self):
        return [
            self.test_01_discipline_analytic_grad,
        ]

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.override_dump_jacobian = True
        self.energy_name = 'FossilSimpleTechno'
        self.year_end = GlossaryEnergy.YearEndDefaultValueGradientTest
        years = np.arange(GlossaryEnergy.YearStartDefault, self.year_end + 1)
        self.resource_list = [
            'oil_resource', 'natural_gas_resource', 'uranium_resource', 'coal_resource']
        self.ratio_available_resource = pd.DataFrame(
            {GlossaryEnergy.Years: years})
        for types in self.resource_list:
            self.ratio_available_resource[types] = np.linspace(
                1, 1, len(self.ratio_available_resource.index))
        electricity_price = 1000 * np.array([0.09, 0.08974117039450046, 0.08948672733558984,
                                             0.089236536471781, 0.08899046935409588, 0.08874840310033885,
                                             0.08875044941298937, 0.08875249600769718, 0.08875454288453355,
                                             0.08875659004356974, 0.0887586374848771, 0.08893789675406477,
                                             0.08911934200930778, 0.08930302260662477, 0.08948898953954933,
                                             0.08967729551117891, 0.08986799501019029, 0.09006114439108429,
                                             0.09025680195894345, 0.09045502805900876, 0.09065588517140537,
                                             0.0908594380113745, 0.09106575363539733, 0.09127490155362818,
                                             0.09148695384909017, 0.0917019853041231, 0.0919200735346165,
                                             0.09214129913260598, 0.09236574581786147, 0.09259350059915213,
                                             0.0928246539459331])[:len(years)]
        # We take biomass price of methane/5.0
        self.energy_prices = pd.DataFrame({GlossaryEnergy.Years: years, GlossaryEnergy.electricity: electricity_price
                                           })

        self.energy_carbon_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.electricity: 10.0})

        self.invest_level = pd.DataFrame(
            {GlossaryEnergy.Years: years,
             GlossaryEnergy.InvestValue: 33.0 * 1.10 ** (years - GlossaryEnergy.YearStartDefault)})
        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [14.86, 17.22, 20.27,
                     29.01, 34.05, 39.08, 44.69, 50.29]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.CO2Tax: func(years)})
        self.margin = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.MarginValue: np.ones_like(years) * 110.0})
        # From future of hydrogen
        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'transport': np.ones_like(years) * 13.})
        self.scaling_factor_techno_consumption = 1e3
        self.scaling_factor_techno_production = 1e3
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.ones((len(years), len(years)))))
        demand_ratio_dict[GlossaryEnergy.Years] = years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)
        self.is_stream_demand = True
        self.is_apply_resource_ratio = True

    def tearDown(self):
        pass

    def test_01_discipline_analytic_grad(self):
        self.name = 'Test'
        self.model_name = 'FossilSimpleTechno'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name,
                   'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_fossil': self.name,
                   'ns_resource': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.fossil.fossil_simple_techno.fossil_simple_techno_disc.FossilSimpleTechnoDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        techno_infos_dict = FossilSimpleTechnoDiscipline.techno_infos_dict_default
        techno_infos_dict["lifetime"] = GlossaryEnergy.LifetimeDefaultValueGradientTest

        invest_before_ystart = pd.DataFrame(
            {'past years': np.arange(-3, 0), GlossaryEnergy.InvestValue: [0.0, 1483.79, 1489.95]})

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.EnergyPricesValue}': self.energy_prices,
                       f'{self.name}.{GlossaryEnergy.EnergyCO2EmissionsValue}': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_static_CO2_emissions(
                           np.arange(GlossaryEnergy.YearStartDefault, self.year_end + 1)),
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_static_prices(
                           np.arange(GlossaryEnergy.YearStartDefault, self.year_end + 1)),
                       f'{self.name}.techno_infos_dict': techno_infos_dict,
                       f'{self.name}.{GlossaryEnergy.InvestmentBeforeYearStartValue}': invest_before_ystart,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)
        self.ee.execute()
        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-18, derr_approx='complex_step',
                            local_data=disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}',
                                    f'{self.name}.{GlossaryEnergy.EnergyPricesValue}',
                                    f'{self.name}.{GlossaryEnergy.EnergyCO2EmissionsValue}',
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

    def test_02_discipline_analytic_grad_construction_delay_0(self):
        self.name = 'Test'
        self.model_name = 'FossilSimpleTechno'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name,
                   'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_fossil': self.name,
                   'ns_resource': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.fossil.fossil_simple_techno.fossil_simple_techno_disc.FossilSimpleTechnoDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        techno_infos_dict = {'maturity': 0, 'Opex_percentage': 0.024, 'WACC': 0.058, 'learning_rate': 0.00,
                             'lifetime_unit': GlossaryEnergy.Years, 'Capex_init': 100.,
                             'Capex_init_unit': '$/MWh', 'techno_evo_eff': 'no', 'efficiency': 1.0,
                             'CO2_from_production': 0.37077040550222284, 'CO2_from_production_unit': 'kg/kg',
                             GlossaryEnergy.ConstructionDelay: 0, 'resource_price': 75.0,
                             'resource_price_unit': '$/MWh', 'CH4_venting_emission_factor': (21.9 + 7.2) / 50731.,
                             'CH4_flaring_emission_factor': (1.4 + 6.9) / 50731.,
                             'CH4_unintended_leakage_emission_factor': (0.6 + 1.7) / 50731.,
                             'CH4_emission_factor_unit': 'Mt/TWh',
                             "lifetime": GlossaryEnergy.LifetimeDefaultValueGradientTest}

        invest_before_ystart = pd.DataFrame(
            {'past years': [], GlossaryEnergy.InvestValue: []})

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.EnergyPricesValue}': self.energy_prices,
                       f'{self.name}.{GlossaryEnergy.EnergyCO2EmissionsValue}': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_static_CO2_emissions(
                           np.arange(GlossaryEnergy.YearStartDefault, self.year_end + 1)),
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_static_prices(
                           np.arange(GlossaryEnergy.YearStartDefault, self.year_end + 1)),
                       f'{self.name}.techno_infos_dict': techno_infos_dict,
                       f'{self.name}.{GlossaryEnergy.InvestmentBeforeYearStartValue}': invest_before_ystart,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)
        self.ee.execute()
        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline
        self.check_jacobian(location=dirname(__file__),
                            filename=f'jacobian_{self.energy_name}_{self.model_name}_construction_delay_0.pkl',
                            discipline=disc_techno, step=1.0e-18, derr_approx='complex_step',
                            local_data=disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}',
                                    f'{self.name}.{GlossaryEnergy.EnergyPricesValue}',
                                    f'{self.name}.{GlossaryEnergy.EnergyCO2EmissionsValue}',
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
