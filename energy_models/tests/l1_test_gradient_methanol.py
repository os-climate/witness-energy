'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/14-2024/06/24 Copyright 2023 Capgemini

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

import warnings
from os.path import dirname

import numpy as np
import pandas as pd
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tests.core.abstract_jacobian_unit_test import (
    AbstractJacobianUnittest,
)

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import (
    GaseousHydrogen,
)
from energy_models.core.stream_type.energy_models.methanol import Methanol
from energy_models.core.stream_type.resources_data_disc import (
    get_default_resources_CO2_emissions,
    get_default_resources_prices,
)
from energy_models.core.stream_type.resources_models.water import Water
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.methanol.co2_hydrogenation.co2_hydrogenation_disc import (
    CO2HydrogenationDiscipline,
)

warnings.filterwarnings("ignore")


class MethanolJacobianCase(AbstractJacobianUnittest):
    """
    Methanol Fuel jacobian test class
    """

    def analytic_grad_entry(self):
        return [
            self.test_01_co2_hydrogenation_discipline_analytic_grad,
            self.test_02_methanol_discipline_jacobian,
        ]

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.year_end = GlossaryEnergy.YearEndDefaultValueGradientTest
        self.years = np.arange(GlossaryEnergy.YearStartDefault, self.year_end + 1)

        self.energy_name = 'methanol'
        self.product_unit = 'TWh'
        self.land_use_unit = 'Gha'
        self.stream_prices = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                           GaseousHydrogen.name: 300.0,
                                           GlossaryEnergy.carbon_capture: 150.0,
                                           GlossaryEnergy.electricity: 10,
                                           })

        self.stream_co2_emissions = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                                     GaseousHydrogen.name: 10.0,
                                                     GlossaryEnergy.carbon_capture: 0.0,
                                                     GlossaryEnergy.electricity: 0.0,
                                                     })

        self.resources_price = pd.DataFrame({GlossaryEnergy.Years: self.years, Water.name: 2.0})

        self.invest_level = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                          GlossaryEnergy.InvestValue: np.linspace(0.001, 0.0008, len(self.years))
                                          })

        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.CO2Tax: np.linspace(14., 40., len(self.years))})
        self.margin = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.MarginValue: 110.0})
        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, 'transport': 200.0})

        # ---Ratios---
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.linspace(1.0, 1.0, len(self.years))))
        demand_ratio_dict[GlossaryEnergy.Years] = self.years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)

        resource_ratio_dict = dict(
            zip(EnergyMix.RESOURCE_LIST, np.linspace(1.0, 1.0, len(self.years))))
        resource_ratio_dict[GlossaryEnergy.Years] = self.years
        self.all_resource_ratio_usable_demand = pd.DataFrame(
            resource_ratio_dict)

    def tearDown(self):
        pass

    def test_01_co2_hydrogenation_discipline_analytic_grad(self):
        self.name = 'Test'
        self.model_name = GlossaryEnergy.CO2Hydrogenation
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_methanol': f'{self.name}',
                   'ns_resource': f'{self.name}'
                   }
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.methanol.co2_hydrogenation.co2_hydrogenation_disc.CO2HydrogenationDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(self.years),
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_default_resources_prices(self.years),
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.LifetimeName}': GlossaryEnergy.LifetimeDefaultValueGradientTest,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].discipline_wrapp.discipline

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryEnergy.UtilisationRatioValue}',
                                    f'{self.name}.{GlossaryEnergy.StreamPricesValue}',
                                    f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}',
                                    f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}',
                                    f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}',
                                    f'{self.name}.{GlossaryEnergy.CO2TaxesValue}'],
                            outputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoPricesValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.CO2EmissionsValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoProductionValue}'],
                            )

    def test_02_methanol_discipline_jacobian(self):
        self.co2_hydrogenation_consumption = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                                           f'{GlossaryEnergy.carbon_capture} ({self.product_unit})': 1.0,
                                                           f'{GaseousHydrogen.name} ({self.product_unit})': 1.0,
                                                           f'{GlossaryEnergy.electricity} ({self.product_unit})': 1.0,
                                                           f'{Water.name} ({GlossaryEnergy.mass_unit})': 1.0,
                                                           })
        self.co2_hydrogenation_production = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                                          f'{Methanol.name} ({self.product_unit})': 1.0
                                                          })
        self.co2_hydrogenation_techno_prices = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                                             f'{CO2HydrogenationDiscipline.techno_name}': 100.0,
                                                             f'{CO2HydrogenationDiscipline.techno_name}_wotaxes': 100.0,
                                                             })
        self.co2_hydrogenation_carbon_emissions = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                                                'production': 1.0,
                                                                f'{CO2HydrogenationDiscipline.techno_name}': 0.5,
                                                                })
        self.land_use_required_CO2Hydrogenation = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, f'{CO2HydrogenationDiscipline.techno_name} ({self.land_use_unit})': 0.0})
        self.name = 'Test'
        self.model_name = 'methanol'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': f'{self.name}',
                   'ns_methanol': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_resource': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.stream_type.energy_disciplines.methanol_disc.MethanolDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        techno_capital = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.Capital: 20000,
            GlossaryEnergy.NonUseCapital: 1000.,
        })
        techno_name = GlossaryEnergy.CO2Hydrogenation
        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearStart}': GlossaryEnergy.YearStartDefault,
                       f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryEnergy.techno_list}': [techno_name],
                       f'{self.name}.{self.model_name}.{techno_name}.{GlossaryEnergy.TechnoConsumptionValue}': self.co2_hydrogenation_consumption,
                       f'{self.name}.{self.model_name}.{techno_name}.{GlossaryEnergy.TechnoCapitalValue}': techno_capital,
                       f'{self.name}.{self.model_name}.{techno_name}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}': self.co2_hydrogenation_consumption,
                       f'{self.name}.{self.model_name}.{techno_name}.{GlossaryEnergy.TechnoProductionValue}': self.co2_hydrogenation_production,
                       f'{self.name}.{self.model_name}.{techno_name}.{GlossaryEnergy.TechnoPricesValue}': self.co2_hydrogenation_techno_prices,
                       f'{self.name}.{self.model_name}.{techno_name}.{GlossaryEnergy.CO2EmissionsValue}': self.co2_hydrogenation_carbon_emissions,
                       f'{self.name}.{self.model_name}.{techno_name}.{GlossaryEnergy.LandUseRequiredValue}': self.land_use_required_CO2Hydrogenation,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0].discipline_wrapp.discipline
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_specific_{self.energy_name}.pkl',
                            discipline=disc, step=1.0e-15, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc.local_data,
                            inputs=[
                                f'{self.name}.{self.model_name}.{techno_name}.{GlossaryEnergy.TechnoProductionValue}',
                                f'{self.name}.{self.model_name}.{techno_name}.{GlossaryEnergy.TechnoConsumptionValue}',
                                f'{self.name}.{self.model_name}.{techno_name}.{GlossaryEnergy.TechnoPricesValue}',
                                f'{self.name}.{self.model_name}.{techno_name}.{GlossaryEnergy.TechnoConsumptionValue}',
                                f'{self.name}.{GlossaryEnergy.CO2TaxesValue}'],
                            outputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.CO2EmissionsValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.CO2PerUse}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.StreamPricesValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.StreamConsumptionValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.EnergyProductionValue}'], )


if '__main__' == __name__:
    cls = MethanolJacobianCase()
    cls.setUp()
    cls.test_01_co2_hydrogenation_discipline_analytic_grad()
