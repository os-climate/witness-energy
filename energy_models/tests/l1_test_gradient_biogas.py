'''
Copyright 2022 Airbus SAS
Modifications on 2023/10/23-2024/06/24 Copyright 2023 Capgemini

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
from sostrades_optimization_plugins.tools.discipline_tester import discipline_test_function


class BiogasJacobianTestCase(unittest.TestCase):
    """Anaerobic Digestion prices test class"""
    def setUp(self):
        self.name = "Test"
        self.ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_biogas': f'{self.name}',
                   'ns_resource': self.name}
        self.energy_name = GlossaryEnergy.biogas
        years = np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefaultValueGradientTest + 1)

        self.resource_list = [
            'oil_resource', 'natural_gas_resource', 'uranium_resource', 'coal_resource']
        self.ratio_available_resource = pd.DataFrame(
            {GlossaryEnergy.Years: np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefaultValueGradientTest + 1)})
        for types in self.resource_list:
            self.ratio_available_resource[types] = np.linspace(
                1, 1, len(self.ratio_available_resource.index))
        self.stream_prices = pd.DataFrame({GlossaryEnergy.Years: years, GlossaryEnergy.electricity: 90.
                                           })
        self.resources_prices = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.WetBiomassResource: 9.
             })

        self.stream_co2_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.electricity: 0.0})

        self.invest_level = pd.DataFrame(
            {GlossaryEnergy.Years: years,
             GlossaryEnergy.InvestValue: np.linspace(4., 5.0, len(years))})
        

        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.CO2Tax: np.linspace(15., 40., len(years))})
        self.margin = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.MarginValue: 110.0})
        # From future of hydrogen
        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'transport': 0.0})
        self.scaling_factor_techno_consumption = 1e3
        self.scaling_factor_techno_production = 1e3
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.ones((len(years), len(years)))))
        demand_ratio_dict[GlossaryEnergy.Years] = years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)
        self.is_stream_demand = True
        self.is_apply_resource_ratio = True
        self.year_end = GlossaryEnergy.YearEndDefaultValueGradientTest

    def get_inputs_dicts(self):
        return {f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
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
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.LifetimeName}': GlossaryEnergy.LifetimeDefaultValueGradientTest,
                       }

    def test_01_biomass_gas_discipline_analytic_grad(self):
        self.model_name = GlossaryEnergy.AnaerobicDigestion
        discipline_test_function(
            module_path=f'energy_models.models.{GlossaryEnergy.biogas}.anaerobic_digestion.anaerobic_digestion_disc.AnaerobicDigestionDiscipline',
            model_name=self.model_name,
            name=self.name,
            jacobian_test=True,
            show_graphs=False,
            inputs_dict=self.get_inputs_dicts(),
            namespaces_dict=self.ns_dict,
            pickle_directory=dirname(__file__),
            pickle_name=f'{self.energy_name}_{self.model_name}.pkl',
            override_dump_jacobian=False
        )
