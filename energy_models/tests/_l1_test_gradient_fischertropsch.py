'''
Copyright 2025 Capgemini

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
"""
from os.path import dirname

import numpy as np
import pandas as pd
from sostrades_optimization_plugins.models.test_class import GenericDisciplinesTestClass

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.resources_data_disc import (
    get_default_resources_CO2_emissions,
    get_default_resources_prices,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.liquid_fuel.fischer_tropsch.fischer_tropsch_disc import (
    FischerTropschDiscipline,
)


class FTJacobianTestCase(GenericDisciplinesTestClass):
        self.name = "Test"
        self.override_dump_jacobian = False
        self.pickle_directory = dirname(__file__)
        self.stream_name = GlossaryEnergy.liquid_fuel
        self.ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   GlossaryEnergy.NS_WITNESS: f'{self.name}',
                   GlossaryEnergy.NS_ENERGY_MIX: f'{self.name}',
                   
                   'ns_liquid_fuel': self.name,
                   'ns_syngas': self.name,
                   'ns_resource': f'{self.name}'}

        self.year_end = GlossaryEnergy.YearEndDefaultValueGradientTest
        self.years = np.arange(GlossaryEnergy.YearStartDefault, self.year_end + 1)

        self.stream_prices = pd.DataFrame({GlossaryEnergy.Years: self.years, GlossaryEnergy.electricity: 20,
                                           GlossaryEnergy.syngas: 34, GlossaryEnergy.carbon_captured: 12.4
                                           })
        self.syngas_detailed_prices = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                                    GlossaryEnergy.SMR: 34,
                                                    GlossaryEnergy.CoElectrolysis: 60,
                                                    GlossaryEnergy.BiomassGasification: 50
                                                    })
        self.syngas_ratio_technos = {GlossaryEnergy.SMR: 33,
                                     GlossaryEnergy.CoElectrolysis: 100.0,
                                     GlossaryEnergy.BiomassGasification: 200.0
                                     }
        self.stream_co2_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.electricity: 0.2, GlossaryEnergy.syngas: 0.2, GlossaryEnergy.carbon_captured: -2.})
        self.invest_level = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                          GlossaryEnergy.InvestValue: np.linspace(4., 5.0, len(self.years))})

        self.invest_level_negative = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                                   GlossaryEnergy.InvestValue: np.linspace(4., 5.0, len(self.years))})
        # CO2 Taxe Data
        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.CO2Tax: np.linspace(14., 40., len(self.years))})

        self.margin = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.MarginValue: 110.0})
        # From future of hydrogen
        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, 'transport': 100})
        # ---Ratios---
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.linspace(1.0, 1.0, len(self.years))))
        demand_ratio_dict[GlossaryEnergy.Years] = self.years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)

        resource_ratio_dict = dict(
            zip(EnergyMix.resource_list, np.linspace(1.0, 1.0, len(self.years))))
        resource_ratio_dict[GlossaryEnergy.Years] = self.years
        self.all_resource_ratio_usable_demand = pd.DataFrame(
            resource_ratio_dict)
        # overload value of lifetime to reduce test duration
        self.techno_infos_dict = FischerTropschDiscipline.techno_infos_dict_default

    def get_inputs_dict(self):
        return {f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
               f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                           self.years),
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_default_resources_prices(
                           self.years),
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.syngas_ratio': np.ones(len(self.years)) * 80.0,
                       f'{self.name}.syngas_ratio_technos': self.syngas_ratio_technos,
                       f'{self.name}.energy_detailed_techno_prices': self.syngas_detailed_prices,
                       f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       f'{self.name}.techno_infos_dict': self.techno_infos_dict
                       }


    def test_01_FT_gradient_syngas_ratio_08(self):
        self.model_name = 'fischer_tropsch_WGS'
        self.mod_path = 'energy_models.models.liquid_fuel.fischer_tropsch.fischer_tropsch_disc.FischerTropschDiscipline'


    def test_02_FT_gradient_syngas_ratio_03(self):
        self.model_name = 'fischer_tropsch_RWGS'
        self.mod_path = 'energy_models.models.liquid_fuel.fischer_tropsch.fischer_tropsch_disc.FischerTropschDiscipline'
    def test_03_FT_gradient_variable_syngas_ratio(self):
        self.model_name = 'fischer_tropsch_RWGS_and_WGS'
        self.mod_path = 'energy_models.models.liquid_fuel.fischer_tropsch.fischer_tropsch_disc.FischerTropschDiscipline'


    def test_04_FT_gradient_variable_syngas_ratio_bis(self):
        self.model_name = 'fischer_tropsch_RWGS_and_WGS_bis'
        self.mod_path = 'energy_models.models.liquid_fuel.fischer_tropsch.fischer_tropsch_disc.FischerTropschDiscipline'


    def test_05_FT_gradient_ratio_available_cc(self):
        self.model_name = 'fischer_tropsch_ratio_available_cc'
        self.mod_path = 'energy_models.models.liquid_fuel.fischer_tropsch.fischer_tropsch_disc.FischerTropschDiscipline'


    def test_06_FT_gradient_variable_syngas_ratio_invest_negative(self):
        self.model_name = 'fischer_tropsch_RWGS_and_WGS_negative'
        self.mod_path = 'energy_models.models.liquid_fuel.fischer_tropsch.fischer_tropsch_disc.FischerTropschDiscipline'

"""