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
import logging
from os.path import dirname

import numpy as np
import pandas as pd
import scipy.interpolate as sc
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tests.core.abstract_jacobian_unit_test import (
    AbstractJacobianUnittest,
)

from energy_models.glossaryenergy import GlossaryEnergy


class BaseStreamTestCase(AbstractJacobianUnittest):
    """
    Base Stream (electricity) jacobian test class
    """

    def analytic_grad_entry(self):
        return [
            self.test_01_base_stream
        ]

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.energy_name = GlossaryEnergy.electricity
        logging.disable(logging.INFO)
        years = np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefaultValueGradientTest + 1)

        self.years = years

        self.hydropower_techno_prices = pd.DataFrame({
            GlossaryEnergy.Years: years,
            GlossaryEnergy.Hydropower: np.linspace(100, 100 + len(years) - 1, len(years)),
                                                      'Hydropower_wotaxes': np.linspace(100, 100 + len(years) - 1,
                                                                                        len(years))})

        self.gasturbine_techno_prices = pd.DataFrame({GlossaryEnergy.Years: years,
                                                      GlossaryEnergy.GasTurbine: np.linspace(10, 10 + len(years) - 1, len(years)),
                                                      'GasTurbine_wotaxes': np.linspace(10, 10 + len(years) - 1,
                                                                                        len(years))
                                                      })

        self.hydropower_consumption = pd.DataFrame({GlossaryEnergy.Years: years
                                                    })

        self.gasturbine_consumption = pd.DataFrame({GlossaryEnergy.Years: years,
                                                    f'{GlossaryEnergy.methane} ({GlossaryEnergy.energy_unit})': 4.192699
                                                    })

        self.techno_capital = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.Capital: 0.0, GlossaryEnergy.NonUseCapital: 0.})

        self.hydropower_carbon_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.Hydropower: 0.0})

        self.gasturbine_carbon_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.GasTurbine: 0.366208})

        self.land_use_required_GasTurbine = pd.DataFrame(
            {GlossaryEnergy.Years: years, f'{GlossaryEnergy.GasTurbine} ({GlossaryEnergy.surface_unit})': 0.0})
        self.land_use_required_Hydropower = pd.DataFrame(
            {GlossaryEnergy.Years: years, f'{GlossaryEnergy.Hydropower} ({GlossaryEnergy.surface_unit})': 0.0})
        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [0.01486, 0.01722, 0.02027,
                     0.02901, 0.03405, 0.03908, 0.04469, 0.05029]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.CO2Tax: np.linspace(15., 40., len(years))})

    def tearDown(self):
        pass

    def test_01_base_stream(self):
        '''
        The objective is to test output energy price and energy co2 emissions when
        one techno has low prod compare to the other
        We want to kill the low influence to reduce gradients
        '''
        self.name = 'Test'
        self.model_name = GlossaryEnergy.electricity
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': f'{self.name}',
                   'ns_electricity': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   GlossaryEnergy.NS_FUNCTIONS: f'{self.name}',
                   GlossaryEnergy.NS_ENERGY_MIX: self.name, }
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.stream_type.energy_disciplines.electricity_disc.ElectricityDiscipline'

        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        hydropower_production = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                              f'{GlossaryEnergy.electricity} ({GlossaryEnergy.energy_unit})': 100.,
                                              f"{GlossaryEnergy.CO2FromFlueGas} ({GlossaryEnergy.mass_unit})": 844.})

        gasturbine_production = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                              f"{GlossaryEnergy.CH4} ({GlossaryEnergy.mass_unit})": 0.,
                                              f"{GlossaryEnergy.CO2FromFlueGas} ({GlossaryEnergy.mass_unit})": 0.,
                                              f"{GlossaryEnergy.N2O} ({GlossaryEnergy.mass_unit})": 0.,
                                              f"{GlossaryEnergy.heat}.{GlossaryEnergy.hightemperatureheat} ({GlossaryEnergy.energy_unit})": 0.,
                                              f'{GlossaryEnergy.electricity} ({GlossaryEnergy.energy_unit})': np.linspace(.1, 100., len(self.years)),
                                              'O2 (Mt)': 0.019217})
        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearStart}': GlossaryEnergy.YearStartDefault,
                       f'{self.name}.{GlossaryEnergy.YearEnd}': GlossaryEnergy.YearEndDefaultValueGradientTest,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryEnergy.techno_list}': [GlossaryEnergy.Hydropower, GlossaryEnergy.GasTurbine],
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.Hydropower}.{GlossaryEnergy.TechnoConsumptionValue}': self.hydropower_consumption,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.Hydropower}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}': self.hydropower_consumption,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.Hydropower}.{GlossaryEnergy.TechnoProductionValue}': hydropower_production,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.Hydropower}.{GlossaryEnergy.TechnoPricesValue}': self.hydropower_techno_prices,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.Hydropower}.{GlossaryEnergy.CO2EmissionsValue}': self.hydropower_carbon_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.Hydropower}.{GlossaryEnergy.LandUseRequiredValue}': self.land_use_required_Hydropower,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.GasTurbine}.{GlossaryEnergy.TechnoConsumptionValue}': self.gasturbine_consumption,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.Hydropower}.{GlossaryEnergy.TechnoCapitalValue}': self.techno_capital,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.GasTurbine}.{GlossaryEnergy.TechnoCapitalValue}': self.techno_capital,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.GasTurbine}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}': self.gasturbine_consumption,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.GasTurbine}.{GlossaryEnergy.TechnoProductionValue}': gasturbine_production,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.GasTurbine}.{GlossaryEnergy.TechnoPricesValue}': self.gasturbine_techno_prices,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.GasTurbine}.{GlossaryEnergy.CO2EmissionsValue}': self.gasturbine_carbon_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.GasTurbine}.{GlossaryEnergy.LandUseRequiredValue}': self.land_use_required_GasTurbine}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()
        print(self.ee.display_treeview_nodes(True))
        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.electricity')[0].mdo_discipline_wrapp.mdo_discipline
        inputs_checked = [f'Test.electricity.{GlossaryEnergy.GasTurbine}.{GlossaryEnergy.TechnoProductionValue}',
                       f'Test.electricity.{GlossaryEnergy.GasTurbine}.{GlossaryEnergy.TechnoConsumptionValue}',
                       f'Test.electricity.Hydropower.{GlossaryEnergy.TechnoProductionValue}',
                       f'Test.electricity.Hydropower.{GlossaryEnergy.TechnoConsumptionValue}']
        outputs_checked = ['Test.prod_hydropower_constraint']
        self.check_jacobian(location=dirname(__file__), filename='jacobian_energy_mix_electricity_stream.pkl',
                            local_data=disc.local_data,
                            discipline=disc, step=1.0e-12, derr_approx='complex_step', threshold=1e-5,
                            inputs=inputs_checked, outputs=outputs_checked)
