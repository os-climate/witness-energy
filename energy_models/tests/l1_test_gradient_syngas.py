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

import pickle
import unittest
from os.path import dirname, join

import numpy as np
import pandas as pd
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tests.core.abstract_jacobian_unit_test import (
    AbstractJacobianUnittest,
)

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.resources_data_disc import (
    get_default_resources_CO2_emissions,
)
from energy_models.glossaryenergy import GlossaryEnergy
from sostrades_optimization_plugins.tools.discipline_tester import discipline_test_function


class SyngasJacobianTestCase(unittest.TestCase):
    """Syngas jacobian test class"""
    def setUp(self):
        self.name = "Test"
        self.ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_syngas': f'{self.name}',
                   'ns_resource': f'{self.name}'}
        self.energy_name = GlossaryEnergy.syngas
        self.year_end = GlossaryEnergy.YearEndDefaultValueGradientTest
        self.years = np.arange(GlossaryEnergy.YearStartDefault, self.year_end + 1)
        self.stream_prices = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                           GlossaryEnergy.methane: 0.034,
                                           GlossaryEnergy.carbon_capture: 0.034,
                                           GlossaryEnergy.electricity: 90.,
                                           GlossaryEnergy.syngas: 90.,
                                           GlossaryEnergy.solid_fuel: 48,
                                           GlossaryEnergy.biomass_dry: 6812 / 3.36
                                           })

        self.resources_prices = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                              GlossaryEnergy.OxygenResource: len(self.years) * [60.0],
                                              GlossaryEnergy.WaterResource: 1.4
                                              })
        self.stream_co2_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.methane: 0.123 / 15.4, GlossaryEnergy.electricity: 0.03,
             GlossaryEnergy.syngas: 0.2,
             GlossaryEnergy.carbon_capture: -2.,
             GlossaryEnergy.solid_fuel: 0.02,
             GlossaryEnergy.biomass_dry: - 0.425 * 44.01 / 12.0})

        self.invest_level_rwgs = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.InvestValue: 0.1715})
        self.invest_level = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.InvestValue: [0.0] + (len(self.years) - 1) * [1.0]})
        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.CO2Tax: np.linspace(14., 40., len(self.years))})
        self.margin = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.MarginValue: 100.0})

        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, 'transport': 0})

        self.land_use_required_Pyrolysis = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, f'{GlossaryEnergy.Pyrolysis} (Gha)': 0.0})
        self.land_use_required_SMR = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, f'{GlossaryEnergy.SMR} (Gha)': 0.0})
        self.land_use_required_AutothermalReforming = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, f'{GlossaryEnergy.AutothermalReforming} (Gha)': 0.0})
        self.land_use_required_BiomassGasification = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, f'{GlossaryEnergy.BiomassGasification} (Gha)': 0.0})
        self.land_use_required_CoalGasification = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, f'{GlossaryEnergy.CoalGasification} (Gha)': 0.0})
        self.land_use_required_CoElectrolysis = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, f'{GlossaryEnergy.CoElectrolysis} (Gha)': 0.0})
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

    def get_inputs_dict(self):
        return {f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                           self.years),
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': self.resources_prices,
                       f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.LifetimeName}': GlossaryEnergy.LifetimeDefaultValueGradientTest,
                       }
    def test_01_atr_discipline_jacobian(self):
        self.model_name = 'ATR'
        discipline_test_function(
            module_path='energy_models.models.syngas.autothermal_reforming.autothermal_reforming_disc.AutothermalReformingDiscipline',
            model_name=self.model_name,
            name=self.name,
            jacobian_test=True,
            show_graphs=False,
            inputs_dict=self.get_inputs_dict(),
            namespaces_dict=self.ns_dict,
            pickle_directory=dirname(__file__),
            pickle_name=f'methane_{self.model_name}.pkl',
            override_dump_jacobian=True
        )


    def test_02_coelectrolysis_discipline_jacobian(self):
        self.model_name = 'coelectrolysis'
        discipline_test_function(
            module_path='energy_models.models.syngas.co_electrolysis.co_electrolysis_disc.CoElectrolysisDiscipline',
            model_name=self.model_name,
            name=self.name,
            jacobian_test=True,
            show_graphs=False,
            inputs_dict=self.get_inputs_dict(),
            namespaces_dict=self.ns_dict,
            pickle_directory=dirname(__file__),
            pickle_name=f'methane_{self.model_name}.pkl',
            override_dump_jacobian=True
        )


    def test_03_smr_discipline_jac(self):
        self.model_name = GlossaryEnergy.SMR
        discipline_test_function(
            module_path='energy_models.models.syngas.smr.smr_disc.SMRDiscipline',
            model_name=self.model_name,
            name=self.name,
            jacobian_test=True,
            show_graphs=False,
            inputs_dict=self.get_inputs_dict(),
            namespaces_dict=self.ns_dict,
            pickle_directory=dirname(__file__),
            pickle_name=f'methane_{self.model_name}.pkl',
            override_dump_jacobian=True
        )


    def test_04_rwgs_discipline_jacobian(self):
        self.model_name = GlossaryEnergy.RWGS
        discipline_test_function(
            module_path='energy_models.models.syngas.reversed_water_gas_shift.reversed_water_gas_shift_disc.ReversedWaterGasShiftDiscipline',
            model_name=self.model_name,
            name=self.name,
            jacobian_test=True,
            show_graphs=False,
            inputs_dict=self.get_inputs_dict(),
            namespaces_dict=self.ns_dict,
            pickle_directory=dirname(__file__),
            pickle_name=f'methane_{self.model_name}.pkl',
            override_dump_jacobian=True
        )


    def test_05_coal_gasification_discipline_jacobian(self):
        self.model_name = 'coal_gasification'
        discipline_test_function(
            module_path='energy_models.models.syngas.coal_gasification.coal_gasification_disc.CoalGasificationDiscipline',
            model_name=self.model_name,
            name=self.name,
            jacobian_test=True,
            show_graphs=False,
            inputs_dict=self.get_inputs_dict(),
            namespaces_dict=self.ns_dict,
            pickle_directory=dirname(__file__),
            pickle_name=f'methane_{self.model_name}.pkl',
            override_dump_jacobian=True
        )


    def test_06_biomass_gas_discipline_jacobian(self):
        self.model_name = 'biomass_gasification'
        discipline_test_function(
            module_path='energy_models.models.syngas.biomass_gasification.biomass_gasification_disc.BiomassGasificationDiscipline',
            model_name=self.model_name,
            name=self.name,
            jacobian_test=True,
            show_graphs=False,
            inputs_dict=self.get_inputs_dict(),
            namespaces_dict=self.ns_dict,
            pickle_directory=dirname(__file__),
            pickle_name=f'methane_{self.model_name}.pkl',
            override_dump_jacobian=True
        )


    def test_07_pyrolysis_discipline_jacobian(self):
        self.model_name = 'pyrolysis'
        discipline_test_function(
            module_path='energy_models.models.syngas.pyrolysis.pyrolysis_disc.PyrolysisDiscipline',
            model_name=self.model_name,
            name=self.name,
            jacobian_test=True,
            show_graphs=False,
            inputs_dict=self.get_inputs_dict(),
            namespaces_dict=self.ns_dict,
            pickle_directory=dirname(__file__),
            pickle_name=f'methane_{self.model_name}.pkl',
            override_dump_jacobian=True
        )

