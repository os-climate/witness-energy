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
import numpy as np
import pandas as pd
import scipy.interpolate as sc
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tests.core.abstract_jacobian_unit_test import (
    AbstractJacobianUnittest,
)

from energy_models.glossaryenergy import GlossaryEnergy


class InvestLimitsTestCase(AbstractJacobianUnittest):
    """
    Low invest case test class
    """

    def analytic_grad_entry(self):
        return [
            self.test_01_low_influence_one_techno
        ]

    def setUp(self):

        self.energy_name = GlossaryEnergy.hydrogen

        years = np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)
        self.years = years

        self.electrolysis_techno_prices = pd.DataFrame(
            {GlossaryEnergy.ElectrolysisPEM: np.linspace(100, 100 + len(years) - 1, len(years)),
             f'{GlossaryEnergy.ElectrolysisPEM}_wotaxes': np.linspace(100, 100 + len(years) - 1, len(years))})

        self.wgs_techno_prices = pd.DataFrame({GlossaryEnergy.WaterGasShift: np.linspace(10, 10 + len(years) - 1, len(years)),
                                               f"{GlossaryEnergy.WaterGasShift}_wotaxes": np.linspace(10, 10 + len(years) - 1, len(years))
                                               })

        self.wgs_consumption = pd.DataFrame({GlossaryEnergy.Years: years,
                                             f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen} ({GlossaryEnergy.energy_unit})': [230.779470] * len(years),
                                             f'{GlossaryEnergy.electricity} ({GlossaryEnergy.energy_unit})': [82.649011] * len(years),
                                             f'{GlossaryEnergy.syngas} ({GlossaryEnergy.energy_unit})': [3579.828092] * len(years),
                                             'water (Mt)': [381.294427] * len(years)})

        self.electrolysis_consumption = pd.DataFrame({GlossaryEnergy.Years: years,
                                                      f'{GlossaryEnergy.electricity} ({GlossaryEnergy.energy_unit})': [4.192699] * len(years),
                                                      'water (Mt)': [0.021638] * len(years)})

        self.electrolysis_carbon_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.ElectrolysisPEM: 0.0, GlossaryEnergy.electricity: 0.0, 'production': 0.0})

        self.wgs_carbon_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.WaterGasShift: 0.366208, GlossaryEnergy.syngas: 0.0, GlossaryEnergy.electricity: 0.0,
             'production': 0.366208})

        self.land_use_required_WaterGasShift = pd.DataFrame(
            {GlossaryEnergy.Years: years, f'{GlossaryEnergy.WaterGasShift} ({GlossaryEnergy.surface_unit})': 0.0})
        self.land_use_required_Electrolysis = pd.DataFrame(
            {GlossaryEnergy.Years: years, f'{GlossaryEnergy.ElectrolysisPEM} (Gha)': 0.0})
        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [0.01486, 0.01722, 0.02027,
                     0.02901, 0.03405, 0.03908, 0.04469, 0.05029]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.CO2Tax: np.linspace(15., 40., len(years))})

    def test_01_low_influence_one_techno(self):
        '''
        The objective is to test output energy price and energy co2 emissions when 
        one techno has low prod compare to the other 
        We want to kill the low influence to reduce gradients
        '''
        self.name = 'Test'
        self.model_name = f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': f'{self.name}',
                   'ns_hydrogen': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   GlossaryEnergy.NS_ENERGY_MIX: self.name,
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
        wgs_production = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                       f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen} ({GlossaryEnergy.energy_unit})': np.linspace(100, 100, len(self.years)),
                                       f"{GlossaryEnergy.CO2FromFlueGas} ({GlossaryEnergy.mass_unit})": [844.027980] * len(self.years)})

        electrolysis_production = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                                f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen} ({GlossaryEnergy.energy_unit})': [low_prod] * years_low_prod + [
                                                    100] * (len(self.years) - years_low_prod),
                                                'O2 (Mt)': [0.019217] * len(self.years)})
        inputs_dict = {f'{self.name}.{self.model_name}.{GlossaryEnergy.YearStart}': GlossaryEnergy.YearStartDefault,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.YearEnd}': GlossaryEnergy.YearEndDefault,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryEnergy.techno_list}': [GlossaryEnergy.WaterGasShift, GlossaryEnergy.ElectrolysisPEM],
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.TechnoConsumptionValue}': self.wgs_consumption,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}': self.wgs_consumption,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.TechnoProductionValue}': wgs_production,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.TechnoPricesValue}': self.wgs_techno_prices,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.CO2EmissionsValue}': self.wgs_carbon_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.LandUseRequiredValue}': self.land_use_required_WaterGasShift,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.ElectrolysisPEM}.{GlossaryEnergy.TechnoConsumptionValue}': self.electrolysis_consumption,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.ElectrolysisPEM}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}': self.electrolysis_consumption,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.ElectrolysisPEM}.{GlossaryEnergy.TechnoProductionValue}': electrolysis_production,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.ElectrolysisPEM}.{GlossaryEnergy.TechnoPricesValue}': self.electrolysis_techno_prices,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.ElectrolysisPEM}.{GlossaryEnergy.CO2EmissionsValue}': self.electrolysis_carbon_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.ElectrolysisPEM}.{GlossaryEnergy.LandUseRequiredValue}': self.land_use_required_Electrolysis}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        energy_prices = self.ee.dm.get_value(
            f'{self.name}.{self.model_name}.{GlossaryEnergy.StreamPricesValue}')
        co2_emissions = self.ee.dm.get_value(
            f'{self.name}.{self.model_name}.{GlossaryEnergy.CO2EmissionsValue}')
        # Check if for the first year_low_prod values the price value of hydrogen is equal to the price value of WGS
        # We erase the influence of low prod to the price BUT the mix weight is
        # not 100% for the other techno

        self.assertListEqual(np.around(energy_prices[f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}'].values[0:10].tolist(), 2).tolist(),
                             np.around(
                                 (self.wgs_techno_prices[GlossaryEnergy.WaterGasShift].values[0:10] * (100 - low_prod) / 100),
                                 2).tolist()
                             )
        self.assertListEqual(np.around(co2_emissions[f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}'].values[0:10].tolist(), 2).tolist(),
                             np.around(
                                 (self.wgs_carbon_emissions[GlossaryEnergy.WaterGasShift].values[0:10] * (100 - low_prod) / 100),
                                 2).tolist()
                             )

        self.assertEqual(energy_prices[f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}'].values[-1],
                         (self.wgs_techno_prices[GlossaryEnergy.WaterGasShift].values[-1] +
                          self.electrolysis_techno_prices[GlossaryEnergy.ElectrolysisPEM].values[-1]) / 2.0)

    def test_02_low_prod_for_both_technos(self):
        '''
        The objective is to test the energy price and co2 emissions when all technos prod are low
        '''
        self.name = 'Test'
        self.model_name = f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': f'{self.name}',
                   'ns_hydrogen': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   GlossaryEnergy.NS_ENERGY_MIX: self.name,
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
        wgs_production = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                       f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen} ({GlossaryEnergy.energy_unit})': np.linspace(1e-6, 1e-6, len(self.years)),
                                       f"{GlossaryEnergy.CO2FromFlueGas} ({GlossaryEnergy.mass_unit})": [844.027980] * len(self.years)})

        electrolysis_production = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                                f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen} ({GlossaryEnergy.energy_unit})': [low_prod] * years_low_prod + [
                                                    100] * (len(self.years) - years_low_prod),
                                                'O2 (Mt)': [0.019217] * len(self.years)})
        inputs_dict = {f'{self.name}.{self.model_name}.{GlossaryEnergy.YearStart}': GlossaryEnergy.YearStartDefault,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.YearEnd}': GlossaryEnergy.YearEndDefault,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryEnergy.techno_list}': [GlossaryEnergy.WaterGasShift, GlossaryEnergy.ElectrolysisPEM],
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.TechnoConsumptionValue}': self.wgs_consumption,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}': self.wgs_consumption,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.TechnoProductionValue}': wgs_production,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.TechnoPricesValue}': self.wgs_techno_prices,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.CO2EmissionsValue}': self.wgs_carbon_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.LandUseRequiredValue}': self.land_use_required_WaterGasShift,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.ElectrolysisPEM}.{GlossaryEnergy.TechnoConsumptionValue}': self.electrolysis_consumption,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.ElectrolysisPEM}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}': self.electrolysis_consumption,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.ElectrolysisPEM}.{GlossaryEnergy.TechnoProductionValue}': electrolysis_production,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.ElectrolysisPEM}.{GlossaryEnergy.TechnoPricesValue}': self.electrolysis_techno_prices,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.ElectrolysisPEM}.{GlossaryEnergy.CO2EmissionsValue}': self.electrolysis_carbon_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.ElectrolysisPEM}.{GlossaryEnergy.LandUseRequiredValue}': self.land_use_required_Electrolysis}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        energy_prices = self.ee.dm.get_value(
            f'{self.name}.{self.model_name}.{GlossaryEnergy.StreamPricesValue}')
        co2_emissions = self.ee.dm.get_value(
            f'{self.name}.{self.model_name}.{GlossaryEnergy.CO2EmissionsValue}')

        # Twe two low prods are reduced to 1e-3 and they have both  almost same effect
        # on price and CO2 emissions ( the exponential is here to smooth the
        # cut off)
        self.assertListEqual(np.round(energy_prices[f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}'].values[0:10], 1).tolist(),
                             ((self.wgs_techno_prices[GlossaryEnergy.WaterGasShift].values[0:10] +
                               self.electrolysis_techno_prices[GlossaryEnergy.ElectrolysisPEM].values[0:10]) / 2.0).tolist()
                             )
        self.assertListEqual(np.round(co2_emissions[f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}'].values[0:10], 4).tolist(),
                             np.round((self.wgs_carbon_emissions[GlossaryEnergy.WaterGasShift].values[0:10] +
                                       self.electrolysis_carbon_emissions[GlossaryEnergy.ElectrolysisPEM].values[0:10]) / 2.0,
                                      4).tolist()
                             )
