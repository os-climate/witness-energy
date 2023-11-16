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
import pandas as pd
import numpy as np
import scipy.interpolate as sc

from climateeconomics.glossarycore import GlossaryCore
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tests.core.abstract_jacobian_unit_test import AbstractJacobianUnittest


class InvestLimitsTestCase(AbstractJacobianUnittest):
    """
    Low invest case test class
    """

    def analytic_grad_entry(self):
        return [
            self.test_01_low_influence_one_techno
        ]

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.energy_name = 'hydrogen'

        years = np.arange(2020, 2051)
        self.years = years

        self.electrolysis_techno_prices = pd.DataFrame({'Electrolysis.PEM': np.linspace(100, 100 + len(years) - 1, len(years)),
                                                        'Electrolysis.PEM_wotaxes': np.linspace(100, 100 + len(years) - 1, len(years))})

        self.wgs_techno_prices = pd.DataFrame({'WaterGasShift': np.linspace(10, 10 + len(years) - 1, len(years)),
                                               'WaterGasShift_wotaxes': np.linspace(10, 10 + len(years) - 1, len(years))
                                               })

        self.wgs_consumption = pd.DataFrame({GlossaryCore.Years: years,
                                             'hydrogen.gaseous_hydrogen (TWh)': [230.779470] * len(years),
                                             'electricity (TWh)': [82.649011] * len(years),
                                             'syngas (TWh)': [3579.828092] * len(years),
                                             'water (Mt)': [381.294427] * len(years)})

        self.electrolysis_consumption = pd.DataFrame({GlossaryCore.Years: years,
                                                      'electricity (TWh)': [4.192699] * len(years),
                                                      'water (Mt)': [0.021638] * len(years)})

        self.electrolysis_carbon_emissions = pd.DataFrame(
            {GlossaryCore.Years: years, 'Electrolysis.PEM': 0.0, 'electricity': 0.0, 'production': 0.0})

        self.wgs_carbon_emissions = pd.DataFrame(
            {GlossaryCore.Years: years, 'WaterGasShift': 0.366208, 'syngas': 0.0, 'electricity': 0.0, 'production': 0.366208})

        self.land_use_required_WaterGasShift = pd.DataFrame(
            {GlossaryCore.Years: years, 'WaterGasShift (Gha)': 0.0})
        self.land_use_required_Electrolysis = pd.DataFrame(
            {GlossaryCore.Years: years, 'Electrolysis.PEM (Gha)': 0.0})
        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [0.01486, 0.01722, 0.02027,
                     0.02901,  0.03405,   0.03908,  0.04469,   0.05029]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {GlossaryCore.Years: years, GlossaryCore.CO2Tax: func(years)})

    def tearDown(self):
        pass

    def test_01_low_influence_one_techno(self):
        '''
        The objective is to test output energy price and energy co2 emissions when 
        one techno has low prod compare to the other 
        We want to kill the low influence to reduce gradients
        '''
        self.name = 'Test'
        self.model_name = 'hydrogen.gaseous_hydrogen'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': f'{self.name}',
                   'ns_hydrogen': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_energy_mix': self.name,
                   'ns_resource': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.stream_type.energy_disciplines.gaseous_hydrogen_disc.GaseousHydrogenDiscipline'

        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        low_prod = 1.e-2
        years_low_prod = 10
        wgs_production = pd.DataFrame({GlossaryCore.Years: self.years,
                                       'hydrogen.gaseous_hydrogen (TWh)': np.linspace(100, 100, len(self.years)),
                                       'CO2 from Flue Gas (Mt)': [844.027980] * len(self.years)})

        electrolysis_production = pd.DataFrame({GlossaryCore.Years: self.years,
                                                'hydrogen.gaseous_hydrogen (TWh)': [low_prod] * years_low_prod + [100] * (len(self.years) - years_low_prod),
                                                'O2 (Mt)': [0.019217] * len(self.years)})
        inputs_dict = {f'{self.name}.{self.model_name}.{GlossaryCore.YearStart}': 2020,
                       f'{self.name}.{self.model_name}.{GlossaryCore.YearEnd}': 2050,
                       f'{self.name}.{GlossaryCore.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryCore.techno_list}': ['WaterGasShift', 'Electrolysis.PEM'],
                       f'{self.name}.{self.model_name}.WaterGasShift.techno_consumption': self.wgs_consumption,
                       f'{self.name}.{self.model_name}.WaterGasShift.techno_consumption_woratio': self.wgs_consumption,
                       f'{self.name}.{self.model_name}.WaterGasShift.techno_production': wgs_production,
                       f'{self.name}.{self.model_name}.WaterGasShift.techno_prices': self.wgs_techno_prices,
                       f'{self.name}.{self.model_name}.WaterGasShift.{GlossaryCore.CO2EmissionsValue}': self.wgs_carbon_emissions,
                       f'{self.name}.{self.model_name}.WaterGasShift.{GlossaryCore.LandUseRequiredValue}': self.land_use_required_WaterGasShift,
                       f'{self.name}.{self.model_name}.Electrolysis.PEM.techno_consumption': self.electrolysis_consumption,
                       f'{self.name}.{self.model_name}.Electrolysis.PEM.techno_consumption_woratio': self.electrolysis_consumption,
                       f'{self.name}.{self.model_name}.Electrolysis.PEM.techno_production': electrolysis_production,
                       f'{self.name}.{self.model_name}.Electrolysis.PEM.techno_prices': self.electrolysis_techno_prices,
                       f'{self.name}.{self.model_name}.Electrolysis.PEM.{GlossaryCore.CO2EmissionsValue}': self.electrolysis_carbon_emissions,
                       f'{self.name}.{self.model_name}.Electrolysis.PEM.{GlossaryCore.LandUseRequiredValue}': self.land_use_required_Electrolysis}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        energy_prices = self.ee.dm.get_value(
            f'{self.name}.{self.model_name}.{GlossaryCore.EnergyPricesValue}')
        co2_emissions = self.ee.dm.get_value(
            f'{self.name}.{self.model_name}.{GlossaryCore.CO2EmissionsValue}')
        # Check if for the first year_low_prod values the price value of hydrogen is equal to the price value of WGS
        # We erase the influence of low prod to the price BUT the mix weight is
        # not 100% for the other techno

        self.assertListEqual(np.around(energy_prices['hydrogen.gaseous_hydrogen'].values[0:10].tolist(), 2).tolist(),
                             np.around(
                                 (self.wgs_techno_prices['WaterGasShift'].values[0:10] * (100 - low_prod) / 100), 2).tolist()
                             )
        self.assertListEqual(np.around(co2_emissions['hydrogen.gaseous_hydrogen'].values[0:10].tolist(), 2).tolist(),
                             np.around(
                                 (self.wgs_carbon_emissions['WaterGasShift'].values[0:10] * (100 - low_prod) / 100), 2).tolist()
                             )

        self.assertEqual(energy_prices['hydrogen.gaseous_hydrogen'].values[-1],
                         (self.wgs_techno_prices['WaterGasShift'].values[-1] + self.electrolysis_techno_prices['Electrolysis.PEM'].values[-1]) / 2.0)

    def test_02_low_prod_for_both_technos(self):
        '''
        The objective is to test the energy price and co2 emissions when all technos prod are low
        '''
        self.name = 'Test'
        self.model_name = 'hydrogen.gaseous_hydrogen'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': f'{self.name}',
                   'ns_hydrogen': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_energy_mix': self.name,
                   'ns_resource': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.stream_type.energy_disciplines.gaseous_hydrogen_disc.GaseousHydrogenDiscipline'

        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        low_prod = 1.e-5
        years_low_prod = 10
        wgs_production = pd.DataFrame({GlossaryCore.Years: self.years,
                                       'hydrogen.gaseous_hydrogen (TWh)': np.linspace(1e-6, 1e-6, len(self.years)),
                                       'CO2 from Flue Gas (Mt)': [844.027980] * len(self.years)})

        electrolysis_production = pd.DataFrame({GlossaryCore.Years: self.years,
                                                'hydrogen.gaseous_hydrogen (TWh)': [low_prod] * years_low_prod + [100] * (len(self.years) - years_low_prod),
                                                'O2 (Mt)': [0.019217] * len(self.years)})
        inputs_dict = {f'{self.name}.{self.model_name}.{GlossaryCore.YearStart}': 2020,
                       f'{self.name}.{self.model_name}.{GlossaryCore.YearEnd}': 2050,
                       f'{self.name}.{GlossaryCore.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryCore.techno_list}': ['WaterGasShift', 'Electrolysis.PEM'],
                       f'{self.name}.{self.model_name}.WaterGasShift.techno_consumption': self.wgs_consumption,
                       f'{self.name}.{self.model_name}.WaterGasShift.techno_consumption_woratio': self.wgs_consumption,
                       f'{self.name}.{self.model_name}.WaterGasShift.techno_production': wgs_production,
                       f'{self.name}.{self.model_name}.WaterGasShift.techno_prices': self.wgs_techno_prices,
                       f'{self.name}.{self.model_name}.WaterGasShift.{GlossaryCore.CO2EmissionsValue}': self.wgs_carbon_emissions,
                       f'{self.name}.{self.model_name}.WaterGasShift.{GlossaryCore.LandUseRequiredValue}': self.land_use_required_WaterGasShift,
                       f'{self.name}.{self.model_name}.Electrolysis.PEM.techno_consumption': self.electrolysis_consumption,
                       f'{self.name}.{self.model_name}.Electrolysis.PEM.techno_consumption_woratio': self.electrolysis_consumption,
                       f'{self.name}.{self.model_name}.Electrolysis.PEM.techno_production': electrolysis_production,
                       f'{self.name}.{self.model_name}.Electrolysis.PEM.techno_prices': self.electrolysis_techno_prices,
                       f'{self.name}.{self.model_name}.Electrolysis.PEM.{GlossaryCore.CO2EmissionsValue}': self.electrolysis_carbon_emissions,
                       f'{self.name}.{self.model_name}.Electrolysis.PEM.{GlossaryCore.LandUseRequiredValue}': self.land_use_required_Electrolysis}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        energy_prices = self.ee.dm.get_value(
            f'{self.name}.{self.model_name}.{GlossaryCore.EnergyPricesValue}')
        co2_emissions = self.ee.dm.get_value(
            f'{self.name}.{self.model_name}.{GlossaryCore.CO2EmissionsValue}')

        # Twe two low prods are reduced to 1e-3 and they have both  almost same effect
        # on price and CO2 emissions ( the exponential is here to smooth the
        # cut off)
        self.assertListEqual(np.round(energy_prices['hydrogen.gaseous_hydrogen'].values[0:10], 1).tolist(),
                             ((self.wgs_techno_prices['WaterGasShift'].values[0:10] +
                               self.electrolysis_techno_prices['Electrolysis.PEM'].values[0:10]) / 2.0).tolist()
                             )
        self.assertListEqual(np.round(co2_emissions['hydrogen.gaseous_hydrogen'].values[0:10], 4).tolist(),
                             np.round((self.wgs_carbon_emissions['WaterGasShift'].values[0:10] +
                                       self.electrolysis_carbon_emissions['Electrolysis.PEM'].values[0:10]) / 2.0, 4).tolist()
                             )
