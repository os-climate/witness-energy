'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/08-2024/06/24 Copyright 2023 Capgemini

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
from energy_models.models.carbon_capture.direct_air_capture.calcium_potassium_scrubbing.calcium_potassium_scrubbing_disc import (
    CalciumPotassiumScrubbingDiscipline,
)
from energy_models.models.carbon_capture.direct_air_capture.direct_air_capture_techno.direct_air_capture_techno_disc import (
    DirectAirCaptureTechnoDiscipline,
)
from energy_models.models.carbon_capture.flue_gas_capture.calcium_looping.calcium_looping_disc import (
    CalciumLoopingDiscipline,
)
from sostrades_optimization_plugins.tools.discipline_tester import discipline_test_function


class CarbonCaptureJacobianTestCase(unittest.TestCase):
    """Carbon capture jacobian test class"""

    def setUp(self):
        self.name = "Test"
        self.ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                        'ns_energy_study': f'{self.name}',
                        "ns_flue_gas": self.name,
                        'ns_carbon_capture': self.name,
                        'ns_resource': f'{self.name}'}
        self.energy_name = GlossaryEnergy.carbon_capture
        self.year_end = GlossaryEnergy.YearEndDefaultValueGradientTest
        years = np.arange(GlossaryEnergy.YearStartDefault, self.year_end + 1)

        self.years = years

        self.stream_prices = pd.DataFrame(
            {GlossaryEnergy.Years: years,
             GlossaryEnergy.electricity: 160.,
             GlossaryEnergy.clean_energy: 160.,
             GlossaryEnergy.methane: 160.,
             GlossaryEnergy.fossil: 160.
             })

        self.stream_co2_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'amine': 0.0, GlossaryEnergy.electricity: 0.0, GlossaryEnergy.methane: 0.2, GlossaryEnergy.fossil: 0.2,
             GlossaryEnergy.clean_energy: 0.0})
        self.resources_prices = pd.DataFrame(
            {GlossaryEnergy.Years: years,
             GlossaryEnergy.AmineResource: 1300.,
             GlossaryEnergy.PotassiumResource: 500.,
             GlossaryEnergy.CalciumResource: 85.,
             })
        self.flue_gas_mean = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.FlueGasMean: np.linspace(0.1, 0.46, len(years))})
        self.invest_level = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.InvestValue: np.linspace(0.001, 0.0008, len(years))})

        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.CO2Tax: np.linspace(15., 40., len(years))})
        self.margin = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.MarginValue: 110.0})
        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'transport': 0.0})
        # ---Ratios---
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.linspace(0.7, 1.0, len(years))))
        demand_ratio_dict[GlossaryEnergy.Years] = years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)

        resource_ratio_dict = dict(
            zip(EnergyMix.RESOURCE_LIST, np.linspace(1.0, 1.0, len(years))))
        resource_ratio_dict[GlossaryEnergy.Years] = years
        self.all_resource_ratio_usable_demand = pd.DataFrame(
            resource_ratio_dict)

    def get_inputs_dicts(self):
        return {f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                    np.arange(GlossaryEnergy.YearStartDefault, self.year_end + 1)),
                f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
                f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level,
                f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': self.resources_prices,
                f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                f'{self.name}.{GlossaryEnergy.FlueGasMean}': self.flue_gas_mean,
                f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                }

    def test_01_amine_jacobian(self):
        self.model_name = 'amine_scrubbing'
        discipline_test_function(
            module_path='energy_models.models.carbon_capture.direct_air_capture.amine_scrubbing.amine_scrubbing_disc.AmineScrubbingDiscipline',
            model_name=self.model_name,
            name=self.name,
            jacobian_test=True,
            show_graphs=False,
            inputs_dict=self.get_inputs_dicts(),
            namespaces_dict=self.ns_dict,
            pickle_directory=dirname(__file__),
            pickle_name=f'carbon_capture_{self.model_name}.pkl',
            override_dump_jacobian=False
        )

    def test_02_CaKOH_jacobian(self):
        self.model_name = 'calcium_potassium_scrubbing'
        discipline_test_function(
            module_path='energy_models.models.carbon_capture.direct_air_capture.calcium_potassium_scrubbing.calcium_potassium_scrubbing_disc.CalciumPotassiumScrubbingDiscipline',
            model_name=self.model_name,
            name=self.name,
            jacobian_test=True,
            show_graphs=False,
            inputs_dict=self.get_inputs_dicts(),
            namespaces_dict=self.ns_dict,
            pickle_directory=dirname(__file__),
            pickle_name=f'carbon_capture_{self.model_name}.pkl',
            override_dump_jacobian=False
        )


    def test_03_Calcium_looping_jacobian(self):
        self.model_name = 'calcium_looping'
        discipline_test_function(
            module_path='energy_models.models.carbon_capture.flue_gas_capture.calcium_looping.calcium_looping_disc.CalciumLoopingDiscipline',
            model_name=self.model_name,
            name=self.name,
            jacobian_test=True,
            show_graphs=False,
            inputs_dict=self.get_inputs_dicts(),
            namespaces_dict=self.ns_dict,
            pickle_directory=dirname(__file__),
            pickle_name=f'carbon_capture_{self.model_name}.pkl',
            override_dump_jacobian=False
        )
