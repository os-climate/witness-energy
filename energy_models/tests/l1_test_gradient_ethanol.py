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
import unittest
import warnings
from os.path import dirname

import numpy as np
import pandas as pd
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tests.core.abstract_jacobian_unit_test import (
    AbstractJacobianUnittest,
)

from energy_models.core.stream_type.resources_data_disc import (
    get_default_resources_CO2_emissions,
    get_default_resources_prices,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.ethanol.biomass_fermentation.biomass_fermentation_disc import (
    BiomassFermentationDiscipline,
)
from sostrades_optimization_plugins.tools.discipline_tester import discipline_test_function

warnings.filterwarnings("ignore")


class EthanolJacobianCase(unittest.TestCase):
    """Ethanol Fuel jacobian test class"""

    def setUp(self):
        self.name = 'Test'
        self.ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                        'ns_energy_study': f'{self.name}',
                        'ns_ethanol': f'{self.name}',
                        'ns_resource': f'{self.name}'
                        }
        self.year_end = GlossaryEnergy.YearEndDefaultValueGradientTest
        years = np.arange(GlossaryEnergy.YearStartDefault, self.year_end + 1)
        self.years = years
        self.energy_name = 'ethanol'
        self.stream_prices = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.electricity: 135.,
             GlossaryEnergy.biomass_dry: 45.0,
             })

        self.stream_co2_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: years,
             GlossaryEnergy.electricity: 0.0,
             GlossaryEnergy.biomass_dry: - 0.64 / 4.86,
             })

        self.invest_level = pd.DataFrame({GlossaryEnergy.Years: years,
                                          GlossaryEnergy.InvestValue: np.linspace(0.001, 0.0008, len(years))
                                          })
        
        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.CO2Tax: np.linspace(15., 40., len(years))})
        self.margin = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.MarginValue: 110.0})
        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'transport': 200.0})

    def get_inputs_dict(self):
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
                    np.arange(GlossaryEnergy.YearStartDefault, self.year_end + 1)),}

    def test_01_biomass_fermentation_discipline_analytic_grad(self):
        self.model_name = 'BiomassFermentation'
        discipline_test_function(
            module_path='energy_models.models.ethanol.biomass_fermentation.biomass_fermentation_disc.BiomassFermentationDiscipline',
            model_name=self.model_name,
            name=self.name,
            jacobian_test=True,
            show_graphs=False,
            inputs_dict=self.get_inputs_dict(),
            namespaces_dict=self.ns_dict,
            pickle_directory=dirname(__file__),
            pickle_name=f'{self.energy_name}_{self.model_name}.pkl',
            override_dump_jacobian=False
        )

