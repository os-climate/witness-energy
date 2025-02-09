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

from os.path import dirname

import numpy as np
import pandas as pd
from sostrades_optimization_plugins.models.test_class import GenericDisciplinesTestClass

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.resources_data_disc import (
    get_default_resources_CO2_emissions,
)
from energy_models.glossaryenergy import GlossaryEnergy


class CarbonStorageJacobianTestCase(GenericDisciplinesTestClass):
    """Carbon Storage jacobian test class"""
    def setUp(self):
        self.name = "Test"
        self.override_dump_jacobian = False
        self.show_graph = False
        self.jacobian_test = True
        self.pickle_directory = dirname(__file__)
        self.stream_name = GlossaryEnergy.carbon_storage
        self.ns_dict = {'ns_public': self.name,
                        'ns_energy': self.name,
                        'ns_energy_study': self.name,
                        'ns_electricity': self.name,
                        'ns_carbon_storage': self.name,
                        'ns_functions': self.name,
                        'ns_resource': self.name,
                        'ns_carb': self.name}

        self.year_end = GlossaryEnergy.YearEndDefaultValueGradientTest
        years = np.arange(GlossaryEnergy.YearStartDefault, self.year_end + 1)
        self.years = years


        self.stream_prices = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.CO2: 0, GlossaryEnergy.biomass_dry: 2.43, GlossaryEnergy.carbon_capture: 12.})

        self.stream_co2_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.CO2: 0, GlossaryEnergy.biomass_dry : 2.43, GlossaryEnergy.carbon_capture: 7.23})

        self.invest_level = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.InvestValue: 0.0325})

        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.CO2Tax: np.linspace(15., 40., len(years))})
        self.co2_taxes_nul = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.CO2Tax: 0.})

        self.margin = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.MarginValue: 100.0})

        transport_cost = 0

        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'transport': transport_cost})
        self.resources_price = pd.DataFrame({GlossaryEnergy.Years: years, GlossaryEnergy.SolidCarbon: 50.})
        # ---Ratios---
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.linspace(1.0, 1.0, len(years))))
        demand_ratio_dict[GlossaryEnergy.Years] = years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)

        resource_ratio_dict = dict(
            zip(EnergyMix.resource_list, np.linspace(1.0, 1.0, len(years))))
        resource_ratio_dict[GlossaryEnergy.Years] = years
        self.all_resource_ratio_usable_demand = pd.DataFrame(
            resource_ratio_dict)

    def get_inputs_dict(self):
        return {f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
         f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
             np.arange(GlossaryEnergy.YearStartDefault, self.year_end + 1)),
         f'{self.name}.{GlossaryEnergy.EnergyPricesValue}': self.stream_prices,
         f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
         f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level,
         f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
         f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
         f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
         f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': self.resources_price,
         f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,}

    
    def test_01_biomass_bf_discipline_analytic_grad(self):
        self.model_name = 'biomass_bf'
        self.mod_path = 'energy_models.models.carbon_storage.biomass_burying_fossilization.biomass_burying_fossilization_disc.BiomassBuryingFossilizationDiscipline'


    def test_02_deep_ocean_injection_discipline_analytic_grad(self):
        self.model_name = 'DeepOceanInjection'
        self.mod_path = 'energy_models.models.carbon_storage.deep_ocean_injection.deep_ocean_injection_disc.DeepOceanInjectionDiscipline'

    def test_03_deep_saline_discipline_analytic_grad(self):
        self.model_name = GlossaryEnergy.DeepSalineFormation
        self.mod_path = 'energy_models.models.carbon_storage.deep_saline_formation.deep_saline_formation_disc.DeepSalineFormationDiscipline'

    def test_04_depleted_oil_gas_discipline_analytic_grad(self):
        self.model_name = 'DepletedOilGas'
        self.mod_path = 'energy_models.models.carbon_storage.depleted_oil_gas.depleted_oil_gas_disc.DepletedOilGasDiscipline'


    def test_05_pure_carbon_solid_storage_discipline_analytic_grad(self):
        self.model_name = 'Pure_Carbon_Solid_Storage'
        self.mod_path = 'energy_models.models.carbon_storage.pure_carbon_solid_storage.pure_carbon_solid_storage_disc.PureCarbonSolidStorageDiscipline'

    def test_06_geologic_mineralization_discipline_analytic_grad(self):
        self.model_name = GlossaryEnergy.GeologicMineralization
        self.mod_path = 'energy_models.models.carbon_storage.geologic_mineralization.geologic_mineralization_disc.GeologicMineralizationDiscipline'

    def test_07_enhanced_oil_recovery_discipline_analytic_grad(self):
        self.model_name = 'EnhancedOilRecovery'
        self.mod_path = 'energy_models.models.carbon_storage.enhanced_oil_recovery.enhanced_oil_recovery_disc.EnhancedOilRecoveryDiscipline'
