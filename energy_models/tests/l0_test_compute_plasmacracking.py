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

import numpy as np
import pandas as pd
import scipy.interpolate as sc
from sostrades_core.execution_engine.execution_engine import ExecutionEngine

from energy_models.core.stream_type.resources_data_disc import (
    get_default_resources_CO2_emissions,
    get_default_resources_prices,
)
from energy_models.glossaryenergy import GlossaryEnergy


class PlasmaCrackingPriceTestCase(unittest.TestCase):
    """
    PlasmaCracking prices test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''

        self.hydro_techno_margin = pd.DataFrame({'H2plasmacracking': [120, 115, 110],
                                                 GlossaryEnergy.Years: [2020, 2030, 2050]})

        func = sc.interp1d(list(self.hydro_techno_margin[GlossaryEnergy.Years]),
                           self.hydro_techno_margin['H2plasmacracking'],
                           kind='linear', fill_value='extrapolate')
        years = np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)

        self.stream_co2_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.electricity: 0.0, GlossaryEnergy.methane: 0.123 / 15.4})
        hydro_margin = list(func(list(years)))

        self.margin = pd.DataFrame({GlossaryEnergy.Years: years,
                                    GlossaryEnergy.MarginValue: hydro_margin})
        self.CO2_taxes = pd.DataFrame({GlossaryEnergy.Years: years,
                                       GlossaryEnergy.CO2Tax: np.linspace(10., 90., len(years))})
        self.scaling_factor_techno_consumption = 1e3
        self.scaling_factor_techno_production = 1e3
        self.invest = pd.DataFrame({GlossaryEnergy.Years: years,
                                    GlossaryEnergy.InvestValue: np.linspace(4., 5.0, len(years))})

        self.invest_for_grad = pd.DataFrame({GlossaryEnergy.Years: years,
                                             GlossaryEnergy.InvestValue: [1.0e-11] + list(
                                                 np.linspace(10, 100, len(years) - 1))})
        self.transport = pd.DataFrame({GlossaryEnergy.Years: years,
                                       'transport': np.linspace(2000., 110., len(years))})

        self.stream_prices = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.electricity: 90.,
             GlossaryEnergy.methane: np.linspace(63., 32., len(years)) / 1.5,
             f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}': np.linspace(95., 165., len(years)),
             })

    def test_01_plasma_cracking_discipline(self):
        """
        Test discpline and post processing

        Returns
        -------
        None.

        """

        self.name = 'Test'
        self.model_name = 'Plasmacracking'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_hydrogen': self.name,
                   GlossaryEnergy.NS_ENERGY_MIX: self.name,
                   'ns_carb': self.name, 'ns_resource': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.gaseous_hydrogen.plasma_cracking.\
plasma_cracking_disc.PlasmaCrackingDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        invest_before_year_start = pd.DataFrame({
            GlossaryEnergy.Years: -np.arange(1, 2 + 1), GlossaryEnergy.InvestValue: [1000.0, 1000.0]})
        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearEnd}': GlossaryEnergy.YearEndDefault,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.CO2_taxes,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': invest_before_year_start,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                           np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)),
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_default_resources_prices(
                           np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1))}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)

    def test_02_plasma_cracking_discipline_strong_invest_first_year(self):
        """
        Test discpline and post processing

        Returns
        -------
        None.

        """

        self.name = 'Test'
        self.model_name = 'Plasmacracking'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_hydrogen': self.name,
                   GlossaryEnergy.NS_ENERGY_MIX: self.name,
                   'ns_carb': self.name, 'ns_resource': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.gaseous_hydrogen.plasma_cracking.\
plasma_cracking_disc.PlasmaCrackingDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        invest_before_year_start = pd.DataFrame({
            GlossaryEnergy.Years: -np.arange(1, 2 + 1), GlossaryEnergy.InvestValue: [1000.0, 1000.0]})

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearEnd}': GlossaryEnergy.YearEndDefault,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.CO2_taxes,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_for_grad,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': invest_before_year_start,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                           np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)),
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_default_resources_prices(
                           np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1))}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        capex = self.ee.dm.get_value(
            f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoDetailedPricesValue}')['Capex_PlasmaCracking']
        ratio_capex = [capex[i + 1] / capex[i] for i in range(len(capex) - 1)]
        # check that the ratio capex is never below 0.92
        self.assertEqual(min(min(ratio_capex), 0.92), 0.92)
