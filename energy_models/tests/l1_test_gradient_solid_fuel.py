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


class SolidFuelJacobianTestCase(GenericDisciplinesTestClass):
    """Solid fuel jacobian test class"""

    def setUp(self):
        self.name = 'Test'
        self.override_dump_jacobian = False
        self.show_graph = False
        self.jacobian_test = True
        self.pickle_directory = dirname(__file__)
        self.ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                        'ns_energy_study': f'{self.name}',
                        'ns_solid_fuel': self.name,
                        'ns_resource': f'{self.name}'}

        self.stream_name = GlossaryEnergy.solid_fuel
        self.year_end = GlossaryEnergy.YearEndDefaultValueGradientTest
        self.years = np.arange(GlossaryEnergy.YearStartDefault, self.year_end + 1)

        # crude oil price : 1.5$/gallon /43.9
        self.stream_prices = pd.DataFrame(
            {GlossaryEnergy.Years: self.years,
             GlossaryEnergy.electricity: 160.,
             GlossaryEnergy.biomass_dry: 68.12 / 3.36,

             })

        self.stream_co2_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.electricity: 0.0,
             GlossaryEnergy.biomass_dry: - 0.425 * 44.01 / 12.0})
        self.invest_level_pellet = pd.DataFrame(
            {GlossaryEnergy.Years: self.years,
             GlossaryEnergy.InvestValue: np.linspace(12, 23, len(self.years))})

        self.invest_level = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.InvestValue: np.linspace(0.001, 0.0008, len(self.years))})
        

        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.CO2Tax: np.linspace(14., 40., len(self.years))})
        self.margin = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.MarginValue: 110.0})
        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, 'transport': 7.6})

        self.transport_pellet = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, 'transport': 0.0097187})

        biblio_data_path = join(
            dirname(__file__), 'output_values_check', 'biblio_data.csv')
        self.biblio_data = pd.read_csv(biblio_data_path)
        self.biblio_data = self.biblio_data.loc[self.biblio_data['sos_name']
                                                == f'{GlossaryEnergy.solid_fuel}.{GlossaryEnergy.CoalExtraction}']

        self.resources_price = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.CO2: np.linspace(40, 47.8, len(self.years)),
            'water': np.linspace(40, 47.8, len(self.years)),
        })

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

    def get_inputs_dict(self):
        return {f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                    self.years),
                f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_default_resources_prices(
                    self.years),
                f'{self.name}.{GlossaryEnergy.EnergyPricesValue}': self.stream_prices,
                f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
                f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level,
                f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                f'{self.name}.{self.model_name}.{GlossaryEnergy.LifetimeName}': GlossaryEnergy.LifetimeDefaultValueGradientTest,
                }
    def test_01_coal_extraction_jacobian(self):
        self.model_name = 'coal_extraction'
        self.mod_path = 'energy_models.models.solid_fuel.coal_extraction.coal_extraction_disc.CoalExtractionDiscipline'

    def test_02_pelletizing_jacobian(self):
        self.model_name = 'pelletizing'
        self.mod_path = 'energy_models.models.solid_fuel.pelletizing.pelletizing_disc.PelletizingDiscipline'
