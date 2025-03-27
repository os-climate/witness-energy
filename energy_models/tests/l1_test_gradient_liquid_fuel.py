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
from os.path import dirname, join

import numpy as np
import pandas as pd
from sostrades_optimization_plugins.models.test_class import GenericDisciplinesTestClass

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.resources_data_disc import (
    get_default_resources_CO2_emissions,
    get_default_resources_prices,
)
from energy_models.glossaryenergy import GlossaryEnergy

warnings.filterwarnings("ignore")


class LiquidFuelJacobianCase(GenericDisciplinesTestClass):
    """Liquid Fuel jacobian test class"""

    def setUp(self):

        self.name = 'Test'
        self.override_dump_jacobian = False
        self.show_graph = False
        self.jacobian_test = False
        self.pickle_directory = dirname(__file__)

        self.ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   GlossaryEnergy.NS_WITNESS: f'{self.name}',
                   GlossaryEnergy.NS_ENERGY_MIX: f'{self.name}',
                   
                   'ns_liquid_fuel': f'{self.name}',
                   #    'ns_biogas': f'{self.name}'
                   'ns_biodiesel': f'{self.name}',
                   'ns_resource': f'{self.name}'
                   }

        self.year_end = GlossaryEnergy.YearEndDefaultValueGradientTest
        years = np.arange(GlossaryEnergy.YearStartDefault, self.year_end + 1)

        self.years = years
        self.stream_name = GlossaryEnergy.liquid_fuel
        # crude oil price : 1.3$/gallon
        self.stream_prices = pd.DataFrame(
            {GlossaryEnergy.Years: years,
             GlossaryEnergy.electricity: 16.,
             GlossaryEnergy.CO2: 0.0,
             GlossaryEnergy.syngas: 34,
             f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}': 15.,
             })

        self.syngas_detailed_prices = pd.DataFrame({GlossaryEnergy.Years: years,
                                                    GlossaryEnergy.SMR: 34,
                                                    GlossaryEnergy.CoElectrolysis: 60,
                                                    GlossaryEnergy.BiomassGasification: 50
                                                    })
        self.syngas_ratio_technos = {GlossaryEnergy.Years: years,
                                     GlossaryEnergy.SMR: 0.33,
                                     GlossaryEnergy.CoElectrolysis: 1.0,
                                     GlossaryEnergy.BiomassGasification: 2.0
                                     }
        self.stream_co2_emissions = pd.DataFrame({
            GlossaryEnergy.Years: years,
            GlossaryEnergy.electricity: 0.0,
            GlossaryEnergy.syngas: 0.0,
             f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}': 0.})

        self.invest_level = pd.DataFrame({GlossaryEnergy.Years: years,
                                          GlossaryEnergy.InvestValue: np.linspace(4435750000.0, 5093000000.0, len(self.years)) * 1.0e-9})

        self.invest_level_negative = pd.DataFrame({GlossaryEnergy.Years: years,
                                                   GlossaryEnergy.InvestValue: -np.linspace(4435750000.0, 5093000000.0, len(self.years)) * 1.0e-9})

        self.invest_level_negative2 = pd.DataFrame({GlossaryEnergy.Years: years,
                                                    GlossaryEnergy.InvestValue: np.linspace(4435750000.0, 5093000000.0, len(self.years)) * 1.0e-9})

        self.invest_level = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.InvestValue: np.linspace(4435750000.0, 5093000000.0, len(self.years)) * 1.0e-9})

        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.CO2Tax: np.linspace(14.86, 50.29, len(self.years))})
        self.margin = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.MarginValue: 110.0})
        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'transport': 200.0})

        biblio_data_path = join(
            dirname(__file__), 'output_values_check', 'biblio_data.csv')
        self.biblio_data = pd.read_csv(biblio_data_path)
        self.biblio_data = self.biblio_data.loc[self.biblio_data['sos_name']
                                                == f'{GlossaryEnergy.liquid_fuel}.{GlossaryEnergy.Refinery}']
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
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.CO2}_intensity_by_energy': self.stream_co2_emissions,
                       f'{self.name}.{GlossaryEnergy.CH4}_intensity_by_energy': self.stream_co2_emissions * 0.1,
                       f'{self.name}.{GlossaryEnergy.N2O}_intensity_by_energy': self.stream_co2_emissions * 0.01,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                           self.years),
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_default_resources_prices(
                           self.years),
                       f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.LifetimeName}': GlossaryEnergy.LifetimeDefaultValueGradientTest,
                       }
    def test_01_refinery_jacobian(self):
        self.model_name = 'refinery'
        self.mod_path = 'energy_models.models.liquid_fuel.refinery.refinery_disc.RefineryDiscipline'



    def test_02_transesterification_discipline_analytic_grad(self):
        self.model_name = GlossaryEnergy.Transesterification
        self.mod_path = f'energy_models.models.{GlossaryEnergy.biodiesel}.transesterification.transesterification_disc.TransesterificationDiscipline'

       
    def test_03_transesterification_discipline_analytic_grad_negative_invest(self):
        self.model_name = GlossaryEnergy.Transesterification
        self.mod_path = f'energy_models.models.{GlossaryEnergy.biodiesel}.transesterification.transesterification_disc.TransesterificationDiscipline'

