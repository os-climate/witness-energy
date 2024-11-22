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

from energy_models.core.stream_type.resources_data_disc import (
    get_default_resources_CO2_emissions,
    get_default_resources_prices,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.ethanol.biomass_fermentation.biomass_fermentation_disc import (
    BiomassFermentationDiscipline,
)

warnings.filterwarnings("ignore")


class EthanolJacobianCase(AbstractJacobianUnittest):
    """
    Ethanol Fuel jacobian test class
    """

    def analytic_grad_entry(self):
        return [
            self.test_01_biomass_fermentation_discipline_analytic_grad,
        ]

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
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

    def tearDown(self):
        pass

    def test_01_biomass_fermentation_discipline_analytic_grad(self):
        self.name = 'Test'
        self.model_name = 'BiomassFermentation'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_ethanol': f'{self.name}',
                   'ns_resource': f'{self.name}'
                   }
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.ethanol.biomass_fermentation.biomass_fermentation_disc.BiomassFermentationDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        # overload value of lifetime to reduce test duration
        techno_infos_dict = BiomassFermentationDiscipline.techno_infos_dict_default
        techno_infos_dict[GlossaryEnergy.LifetimeName] = GlossaryEnergy.LifetimeDefaultValueGradientTest
        utilisation_ratio = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                          GlossaryEnergy.UtilisationRatioValue: 50.0 * np.ones_like(self.years)})

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.UtilisationRatioValue}': utilisation_ratio,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                           np.arange(GlossaryEnergy.YearStartDefault, self.year_end + 1)),
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_default_resources_prices(
                           np.arange(GlossaryEnergy.YearStartDefault, self.year_end + 1)),
                       f'{self.name}.techno_infos_dict': techno_infos_dict, }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline
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


if '__main__' == __name__:
    cls = EthanolJacobianCase()
    cls.setUp()
    cls.test_01_biomass_fermentation_discipline_analytic_grad()
