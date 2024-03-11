'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2023/11/16 Copyright 2023 Capgemini

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
import scipy.interpolate as sc

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.resources_data_disc import get_static_CO2_emissions
from energy_models.glossaryenergy import GlossaryEnergy
from gemseo.utils.compare_data_manager_tooling import compare_dict
from sostrades_core.execution_engine.execution_engine import ExecutionEngine


class LiquefactionPriceTestCase(unittest.TestCase):
    """
    Hydrogen Liquefaction prices test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        electricity_price = np.array([0.09, 0.08974117039450046, 0.08948672733558984,
                                      0.089236536471781, 0.08899046935409588, 0.08874840310033885,
                                      0.08875044941298937, 0.08875249600769718, 0.08875454288453355,
                                      0.08875659004356974, 0.0887586374848771, 0.08893789675406477,
                                      0.08911934200930778, 0.08930302260662477, 0.08948898953954933,
                                      0.08967729551117891, 0.08986799501019029, 0.09006114439108429,
                                      0.09025680195894345, 0.09045502805900876, 0.09065588517140537,
                                      0.0908594380113745, 0.09106575363539733, 0.09127490155362818,
                                      0.09148695384909017, 0.0917019853041231, 0.0919200735346165,
                                      0.09214129913260598, 0.09236574581786147, 0.09259350059915213,
                                      0.0928246539459331]) * 1000

        # We take biomass price of methane/5.0
        years = np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)
        self.resource_list = [
            'oil_resource', 'natural_gas_resource', 'uranium_resource', 'coal_resource']
        self.ratio_available_resource = pd.DataFrame(
            {GlossaryEnergy.Years: np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)})
        for types in self.resource_list:
            self.ratio_available_resource[types] = np.linspace(
                1, 1, len(self.ratio_available_resource.index))
        self.energy_prices = pd.DataFrame({GlossaryEnergy.Years: years, GlossaryEnergy.electricity: electricity_price,
                                           f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}': np.ones(len(years)) * 0.1266023955250543 * 1000
                                           })

        self.energy_carbon_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.electricity: 0.2, f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}': 0})

        self.invest_level = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.InvestValue: np.ones(len(years)) * 0.1715})
        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [14.86, 17.22, 20.27,
                     29.01, 34.05, 39.08, 44.69, 50.29]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.CO2Tax: func(years)})
        self.margin = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.MarginValue: np.ones(len(years)) * 110.0})
        # From future of hydrogen
        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'transport': np.ones(len(years)) * 500.0})

        self.resources_price = pd.DataFrame(
            {GlossaryEnergy.Years: np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1),
             'water': 31 * [0.002],
             'uranium fuel': 1390,
             'CO2': [0.04, 0.041, 0.042, 0.043, 0.044, 0.045, 0.0464, 0.047799999999999995, 0.049199999999999994,
                     0.0506, 0.052, 0.0542, 0.0564, 0.0586, 0.0608, 0.063, 0.0652, 0.0674, 0.0696, 0.0718, 0.074,
                     0.0784, 0.0828, 0.0872, 0.0916, 0.096, 0.1006, 0.1052, 0.1098, 0.1144, 0.119],
             GlossaryEnergy.biomass_dry: [0.06812, 0.06812, 0.06812, 0.06812, 0.06812, 0.06812, 0.06812, 0.06812, 0.06812, 0.06812,
                             0.06812, 0.06812, 0.06812, 0.06812, 0.06812, 0.06812, 0.06812, 0.06812, 0.06812, 0.06812,
                             0.06812, 0.06812, 0.06812, 0.06812, 0.06812, 0.06812, 0.06812, 0.06812, 0.06812, 0.06812,
                             0.06812],
             GlossaryEnergy.wet_biomass: [0.056, 0.056, 0.056, 0.056, 0.056, 0.056, 0.056, 0.056, 0.056, 0.056, 0.056, 0.056, 0.056,
                             0.056, 0.056, 0.056, 0.056, 0.056, 0.056, 0.056, 0.056, 0.056, 0.056, 0.056, 0.056, 0.056,
                             0.056, 0.056, 0.056, 0.056, 0.056]
             })
        self.scaling_factor_techno_consumption = 1e3
        self.scaling_factor_techno_production = 1e3
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.ones((len(years), len(years)))))
        demand_ratio_dict[GlossaryEnergy.Years] = years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)
        self.is_stream_demand = True
        self.is_apply_resource_ratio = True

    def tearDown(self):
        pass

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
                       f'{self.name}.{GlossaryEnergy.EnergyPricesValue}': self.energy_prices,
                       f'{self.name}.{GlossaryEnergy.EnergyCO2EmissionsValue}': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': self.resources_price,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_static_CO2_emissions(
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
                       f'{self.name}.{GlossaryEnergy.EnergyPricesValue}': self.energy_prices,
                       f'{self.name}.{GlossaryEnergy.EnergyCO2EmissionsValue}': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': self.resources_price,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_static_CO2_emissions(
                           np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1))}

        self.ee.load_study_from_input_dict(inputs_dict)

        proxy_disc = self.ee.execute()
        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline
        local_data = proxy_disc.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline.local_data
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
