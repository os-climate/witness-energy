'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2023/11/09 Copyright 2023 Capgemini

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

from climateeconomics.glossarycore import GlossaryCore
from energy_models.core.stream_type.resources_data_disc import get_static_CO2_emissions, \
    get_static_prices
from sostrades_core.execution_engine.execution_engine import ExecutionEngine


class PlasmaCrackingPriceTestCase(unittest.TestCase):
    """
    PlasmaCracking prices test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''

        self.hydro_techno_margin = pd.DataFrame({'H2plasmacracking': [120, 115, 110],
                                                 GlossaryCore.Years: [2020, 2030, 2050]})

        func = sc.interp1d(list(self.hydro_techno_margin[GlossaryCore.Years]), self.hydro_techno_margin['H2plasmacracking'],
                           kind='linear', fill_value='extrapolate')
        years = np.arange(2020, 2050 + 1)

        self.energy_carbon_emissions = pd.DataFrame(
            {GlossaryCore.Years: years, 'electricity': 0.0, 'methane': 0.123 / 15.4})
        hydro_margin = list(func(list(years)))

        self.margin = pd.DataFrame({GlossaryCore.Years: years,
                                    GlossaryCore.MarginValue: hydro_margin})

        CO2_tax = np.array([0.01722, 0.033496, 0.049772, 0.066048, 0.082324, 0.0986,
                            0.114876, 0.131152, 0.147428, 0.163704, 0.17998, 0.217668,
                            0.255356, 0.293044, 0.330732, 0.36842, 0.406108, 0.443796,
                            0.481484, 0.519172, 0.55686, 0.591706, 0.626552, 0.661398,
                            0.696244, 0.73109, 0.765936, 0.800782, 0.835628, 0.870474,
                            0.90532]) * 1000
        self.CO2_taxes = pd.DataFrame({GlossaryCore.Years: years,
                                       GlossaryCore.CO2Tax: CO2_tax})
        self.scaling_factor_techno_consumption = 1e3
        self.scaling_factor_techno_production = 1e3
        self.invest = pd.DataFrame({GlossaryCore.Years: years,
                                    GlossaryCore.InvestValue: np.array([4435750000.0, 4522000000.0, 4608250000.0,
                                                        4694500000.0, 4780750000.0, 4867000000.0,
                                                        4969400000.0, 5071800000.0, 5174200000.0,
                                                        5276600000.0, 5379000000.0, 5364700000.0,
                                                        5350400000.0, 5336100000.0, 5321800000.0,
                                                        5307500000.0, 5293200000.0, 5278900000.0,
                                                        5264600000.0, 5250300000.0, 5236000000.0,
                                                        5221700000.0, 5207400000.0, 5193100000.0,
                                                        5178800000.0, 5164500000.0, 5150200000.0,
                                                        5135900000.0, 5121600000.0, 5107300000.0,
                                                        5093000000.0]) * 1.0e-9})

        self.invest_for_grad = pd.DataFrame({GlossaryCore.Years: years,
                                             GlossaryCore.InvestValue: [1.0e-11] + list(np.linspace(10, 100, len(years) - 1))})
        H2_transport = np.array([2.53376664, 2.43804818, 2.34232972, 2.24661127, 2.15089281,
                                 2.05517435, 1.95945589, 1.86373744, 1.76801898, 1.67230052,
                                 1.57658206, 1.48086361, 1.38514515, 1.28942669, 1.19370823,
                                 1.09798978, 1.00227132, 0.90655286, 0.8108344, 0.71511594,
                                 0.61939749, 0.56864131, 0.51788512, 0.46712894, 0.41637276,
                                 0.36561658, 0.3148604, 0.26410422, 0.21334804, 0.16259186,
                                 0.11183567]) * 1000
        self.transport = pd.DataFrame({GlossaryCore.Years: years,
                                       'transport': H2_transport})

        self.energy_prices = pd.DataFrame({GlossaryCore.Years: years, 'electricity': np.array([0.09, 0.08974117039450046, 0.08948672733558984,
                                                                                    0.089236536471781, 0.08899046935409588, 0.08874840310033885,
                                                                                    0.08875044941298937, 0.08875249600769718, 0.08875454288453355,
                                                                                    0.08875659004356974, 0.0887586374848771, 0.08893789675406477,
                                                                                    0.08911934200930778, 0.08930302260662477, 0.08948898953954933,
                                                                                    0.08967729551117891, 0.08986799501019029, 0.09006114439108429,
                                                                                    0.09025680195894345, 0.09045502805900876, 0.09065588517140537,
                                                                                    0.0908594380113745, 0.09106575363539733, 0.09127490155362818,
                                                                                    0.09148695384909017, 0.0917019853041231, 0.0919200735346165,
                                                                                    0.09214129913260598, 0.09236574581786147, 0.09259350059915213,
                                                                                    0.0928246539459331]) * 1000,
                                           'methane': np.array([0.06363, 0.0612408613576689, 0.059181808246196024, 0.05738028027202377,
                                                                0.0557845721244601, 0.05435665353332419, 0.05225877624361548,
                                                                0.05045797192512811, 0.04888746457113824, 0.04750006564084081,
                                                                0.04626130284326101, 0.044848110567750024, 0.043596892851567724,
                                                                0.04247763196812953, 0.04146768302263715, 0.04054957955940597,
                                                                0.03970959176775726, 0.03893674917609171, 0.038222160192931814,
                                                                0.03755852715493717, 0.03693979356326306, 0.03636088278590117,
                                                                0.03581750135963429, 0.03530598876014997, 0.03482320115289285,
                                                                0.03436642036567466, 0.03393328183670935, 0.033521717015978045,
                                                                0.03312990690071806, 0.032756244237772174, 0.03239930253734476]) * 1000 / 1.5,
                                           'hydrogen.gaseous_hydrogen': [94.39744156, 94.53049211, 95.3084315, 96.14172434, 97.07583326, 98.1816908,
                                                                         100.4999642, 103.1650511, 105.7810733, 108.2881198, 112.3278769, 115.498708,
                                                                         118.3399036, 121.7401092, 124.4554085, 127.2076686, 130.6775094, 134.686383,
                                                                         140.5627809, 144.2504245, 145.5922496, 147.085805, 148.963262, 151.1350341,
                                                                         153.4052581, 155.6826633, 157.1131109, 158.3327878, 159.4188099, 160.0814885,
                                                                         160.4196123],
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
                   'ns_energy_mix': self.name,
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
            GlossaryCore.Years: -np.arange(1, 2 + 1), GlossaryCore.InvestValue: [1000.0, 1000.0]})
        inputs_dict = {f'{self.name}.{GlossaryCore.YearEnd}': 2050,
                       f'{self.name}.{self.model_name}.{GlossaryCore.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryCore.CO2TaxesValue}': self.CO2_taxes,
                       f'{self.name}.{self.model_name}.{GlossaryCore.InvestLevelValue}':  self.invest,
                       f'{self.name}.{GlossaryCore.TransportCostValue}':  self.transport,
                       f'{self.name}.{GlossaryCore.TransportMarginValue}':  self.margin,
                       f'{self.name}.{GlossaryCore.EnergyPricesValue}': self.energy_prices,
                       f'{self.name}.{GlossaryCore.EnergyCO2EmissionsValue}': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryCore.EnergyCO2EmissionsValue}': invest_before_year_start,
                       f'{self.name}.{GlossaryCore.RessourcesCO2EmissionsValue}': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.{GlossaryCore.ResourcesPriceValue}': get_static_prices(np.arange(2020, 2051))}

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
                   'ns_energy_mix': self.name,
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
            GlossaryCore.Years: -np.arange(1, 2 + 1), GlossaryCore.InvestValue: [1000.0, 1000.0]})

        inputs_dict = {f'{self.name}.{GlossaryCore.YearEnd}': 2050,
                       f'{self.name}.{self.model_name}.{GlossaryCore.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryCore.CO2TaxesValue}': self.CO2_taxes,
                       f'{self.name}.{self.model_name}.{GlossaryCore.InvestLevelValue}':  self.invest_for_grad,
                       f'{self.name}.{GlossaryCore.TransportCostValue}':  self.transport,
                       f'{self.name}.{GlossaryCore.TransportMarginValue}':  self.margin,
                       f'{self.name}.{GlossaryCore.EnergyPricesValue}': self.energy_prices,
                       f'{self.name}.{GlossaryCore.EnergyCO2EmissionsValue}': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryCore.EnergyCO2EmissionsValue}': invest_before_year_start,
                       f'{self.name}.{GlossaryCore.RessourcesCO2EmissionsValue}': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.{GlossaryCore.ResourcesPriceValue}': get_static_prices(np.arange(2020, 2051))}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        capex = self.ee.dm.get_value(
            f'{self.name}.{self.model_name}.{GlossaryCore.TechnoDetailedPricesValue}')[f'Capex_PlasmaCracking']
        ratio_capex = [capex[i + 1] / capex[i] for i in range(len(capex) - 1)]
        # check that the ratio capex is never below 0.92
        self.assertEqual(min(min(ratio_capex), 0.92), 0.92)
