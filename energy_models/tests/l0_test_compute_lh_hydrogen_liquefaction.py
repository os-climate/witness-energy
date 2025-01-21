'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2024/06/24 Copyright 2023 Capgemini

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
from copy import deepcopy

import numpy as np
import pandas as pd
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tools.compare_data_manager_tooling import compare_dict

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.resources_data_disc import (
    get_default_resources_CO2_emissions,
)
from energy_models.glossaryenergy import GlossaryEnergy


class LiquefactionPriceTestCase(unittest.TestCase):
    """
    Hydrogen Liquefaction prices test class
    """

    def setUp(self):
        
        

        # We take biomass price of methane/5.0
        years = np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)
        self.resource_list = [
            'oil_resource', 'natural_gas_resource', 'uranium_resource', 'coal_resource']
        self.ratio_available_resource = pd.DataFrame(
            {GlossaryEnergy.Years: np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)})
        for types in self.resource_list:
            self.ratio_available_resource[types] = np.linspace(
                1, 1, len(self.ratio_available_resource.index))
        self.stream_prices = pd.DataFrame({GlossaryEnergy.Years: years, GlossaryEnergy.electricity: 90.,
                                           f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}': 126,
                                           })

        self.stream_co2_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.electricity: 0.2, f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}': 0})

        self.invest_level = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.InvestValue: 0.1715})
        

        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.CO2Tax: np.linspace(15., 40., len(years))})
        self.margin = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.MarginValue: 110.0})
        # From future of hydrogen
        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'transport': 500.0})

        self.resources_price = pd.DataFrame(
            {GlossaryEnergy.Years: np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1),
             'water': 0.002,
             'uranium fuel': 1390,
             GlossaryEnergy.CO2: .04,
             GlossaryEnergy.biomass_dry: 0.06,
             GlossaryEnergy.wet_biomass: 0.056,
             })
        self.scaling_factor_techno_consumption = 1e3
        self.scaling_factor_techno_production = 1e3
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.ones((len(years), len(years)))))
        demand_ratio_dict[GlossaryEnergy.Years] = years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)
        self.is_stream_demand = True
        self.is_apply_resource_ratio = True

    def test_02_liquefaction_H2_discipline(self):

        self.name = 'Test'
        self.model_name = 'LH2'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': f'{self.name}',
                   'ns_energy': f'{self.name}',
                   'ns_liquid_hydrogen': f'{self.name}',
                   'ns_hydrogen': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_resource': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.liquid_hydrogen.hydrogen_liquefaction.hydrogen_liquefaction_disc.HydrogenLiquefactionDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearEnd}': GlossaryEnergy.YearEndDefault,
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': self.resources_price,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                           np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1))}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

    def test_03_liquefaction_H2_double_run(self):

        self.name = 'Test'
        self.model_name = 'LH2'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': f'{self.name}',
                   'ns_energy': f'{self.name}',
                   'ns_liquid_hydrogen': f'{self.name}',
                   'ns_hydrogen': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_resource': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.liquid_hydrogen.hydrogen_liquefaction.hydrogen_liquefaction_disc.HydrogenLiquefactionDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearEnd}': GlossaryEnergy.YearEndDefault,
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': self.resources_price,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                           np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1))}

        self.ee.load_study_from_input_dict(inputs_dict)

        proxy_disc = self.ee.execute()
        disc_techno = self.ee.root_process.proxy_disciplines[0].discipline_wrapp.discipline
        local_data = proxy_disc.proxy_disciplines[0].discipline_wrapp.discipline.local_data
        # self.ee.root_process.pre_run_mda()
        output_error = ''
        test_passed = True
        # RUN 1
        local_data1 = disc_techno.execute(deepcopy(local_data))
        # RUN 2
        local_data2 = disc_techno.execute(deepcopy(local_data))
        # COMPARE DICT
        dict_error = {}
        compare_dict(local_data1, local_data2, '', dict_error)
        if dict_error != {}:
            test_passed = False
            for error in dict_error:
                output_error += f'Mismatch in {error} for disc {disc_techno.name}: {dict_error.get(error)}'
                output_error += '\n---------------------------------------------------------\n'
        if not test_passed:
            raise Exception(f'{output_error}')
