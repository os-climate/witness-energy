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

import pickle
import unittest
from os.path import dirname, join

import numpy as np
import pandas as pd
import scipy.interpolate as sc
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tests.core.abstract_jacobian_unit_test import (
    AbstractJacobianUnittest,
)

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.resources_data_disc import (
    get_default_resources_CO2_emissions,
    get_default_resources_prices,
)
from energy_models.glossaryenergy import GlossaryEnergy
from sostrades_optimization_plugins.tools.discipline_tester import discipline_test_function


class HydrogenJacobianTestCase(unittest.TestCase):
    """Hydrogen jacobian test class"""
    def setUp(self):
        
        self.name = "Test"

        self.ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_hydrogen': self.name,
                   'ns_syngas': self.name,
                   GlossaryEnergy.NS_ENERGY_MIX: self.name,
                   'ns_carb': self.name,
                   'ns_resource': f'{self.name}'}
        self.energy_name = GlossaryEnergy.hydrogen
        self.year_end = GlossaryEnergy.YearEndDefaultValueGradientTest
        years = np.arange(GlossaryEnergy.YearStartDefault, self.year_end + 1)
        self.years = years

        self.electrolysis_techno_prices = pd.DataFrame(
            {GlossaryEnergy.Years: years,
             GlossaryEnergy.Electrolysis: 90.,
             'Electrolysis_wotaxes': 90.})

        self.smr_techno_prices = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.WaterGasShift: np.linspace(63., 32., len(years)),
             f"{GlossaryEnergy.WaterGasShift}_wotaxes": np.linspace(63., 32., len(years))
             })

        self.plasmacracking_techno_prices = pd.DataFrame({GlossaryEnergy.Years: years,
                                                          GlossaryEnergy.PlasmaCracking: np.linspace(63., 32., len(years)),
                                                          'PlasmaCracking_wotaxes' :np.linspace(63., 32., len(years))
                                                          })

        self.smr_consumption = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                             f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen} ({GlossaryEnergy.energy_unit})': 230.779470,
                                             f'{GlossaryEnergy.electricity} ({GlossaryEnergy.energy_unit})': 82.649011,
                                             f'{GlossaryEnergy.syngas} ({GlossaryEnergy.energy_unit})': 3579.828092,
                                             f"{GlossaryEnergy.WaterResource} ({GlossaryEnergy.mass_unit})": 381.294427})

        self.smr_production = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                            f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen} ({GlossaryEnergy.energy_unit})': 2304.779470,
                                            f"{GlossaryEnergy.CO2FromFlueGas} ({GlossaryEnergy.mass_unit})": 844.027980})

        self.plasmacracking_production = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                                       f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen} ({GlossaryEnergy.energy_unit})': np.linspace(1e-5, 1, len(self.years)),
                                                       f"{GlossaryEnergy.SolidCarbon} ({GlossaryEnergy.mass_unit})": 0.008622})

        self.plasmacracking_consumption = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                                        f'{GlossaryEnergy.electricity} ({GlossaryEnergy.energy_unit})': 0.019325,
                                                        f'{GlossaryEnergy.methane} ({GlossaryEnergy.energy_unit})': 0.213945})

        self.electrolysis_consumption = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                                      f'{GlossaryEnergy.electricity} ({GlossaryEnergy.energy_unit})': 4.192699,
                                                      f"{GlossaryEnergy.WaterResource} ({GlossaryEnergy.mass_unit})": [0.021638] * len(
                                                          self.years)})

        self.electrolysis_production = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                                     f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen} ({GlossaryEnergy.energy_unit})': 2.684940,
                                                     f"{GlossaryEnergy.DioxygenResource} ({GlossaryEnergy.mass_unit})": [0.019217] * len(
                                                         self.years)})

        self.electrolysis_carbon_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.Electrolysis: 0.0, GlossaryEnergy.electricity: 0.0, 'production': 0.0})

        self.plasma_cracking_carbon_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.PlasmaCracking: -0.243905, 'carbon storage': -0.327803, GlossaryEnergy.methane: 0.0,
             GlossaryEnergy.electricity: 0.0, 'production': 0.0})
        self.smr_carbon_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.WaterGasShift: 0.366208, GlossaryEnergy.syngas: 0.0, GlossaryEnergy.electricity: 0.0,
             'production': 0.366208})

        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.CO2Tax: np.linspace(14., 40., len(self.years))})

        self.stream_prices = pd.DataFrame({GlossaryEnergy.Years: self.years, GlossaryEnergy.electricity: 90.,
                                           GlossaryEnergy.syngas: 33.,
                                           GlossaryEnergy.methane: np.linspace(63., 32., len(years)) / 1.5,
                                           f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}': 50
                                           })

        self.stream_co2_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.electricity: 0.02, GlossaryEnergy.syngas: 0.2, GlossaryEnergy.methane: -0.1})
        self.invest_level = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.InvestValue: 0.1715})

        self.invest_level_negative = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.InvestValue: np.linspace(5000, -5000, len(self.years))})
        

        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.CO2Tax: np.linspace(14., 40., len(self.years))})
        self.margin = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.MarginValue: 110.0})
        # From future of hydrogen
        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, 'transport': 500.0})

        self.syngas_ratio = np.linspace(33.0, 209.0, len(self.years))
        self.syngas_detailed_prices = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                                    GlossaryEnergy.SMR: 34.,
                                                    GlossaryEnergy.CoElectrolysis: 60.,
                                                    GlossaryEnergy.BiomassGasification: 50.
                                                    })
        self.syngas_ratio_technos = {GlossaryEnergy.Years: self.years,
                                     GlossaryEnergy.SMR: 33.0,
                                     GlossaryEnergy.CoElectrolysis: 100.0,
                                     GlossaryEnergy.BiomassGasification: 200.0
                                     }
        CO2_tax = np.linspace(10., 90., len(self.years))

        self.CO2_taxes = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                       GlossaryEnergy.CO2Tax: CO2_tax})

        self.invest = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                    GlossaryEnergy.InvestValue: np.linspace(4., 5.0, len(years))})
        self.land_use_required_mock = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, 'random techno (Gha)': 0.0})

        self.land_use_required_WaterGasShift = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, f'{GlossaryEnergy.WaterGasShift} (Gha)': 0.0})
        self.land_use_required_Electrolysis = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, f'{GlossaryEnergy.Electrolysis} (Gha)': 0.0})
        self.land_use_required_PlasmaCracking = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, f'{GlossaryEnergy.PlasmaCracking} (Gha)': 0.0})

        self.invest_plasmacracking = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                                   GlossaryEnergy.InvestValue: [1.0e-11] + list(
                                                       np.linspace(0.001, 0.4, len(self.years) - 1))})
        # ---Ratios---
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.linspace(100, 100, len(self.years))))

        demand_ratio_dict[GlossaryEnergy.Years] = self.years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)
        self.all_streams_demand_ratio[GlossaryEnergy.syngas] = np.linspace(
            100, 50, len(self.years))
        self.all_streams_demand_ratio[GlossaryEnergy.electricity] = np.linspace(
            60, 40, len(years))

        resource_ratio_dict = dict(
            zip(EnergyMix.RESOURCE_LIST, np.linspace(1.0, 1.0, len(years))))
        resource_ratio_dict[GlossaryEnergy.Years] = years
        self.all_resource_ratio_usable_demand = pd.DataFrame(
            resource_ratio_dict)

    def get_inputs_dict(self):
        return {
            f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
               f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                   self.years),
               f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_default_resources_prices(
                   self.years),
               f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
               f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
               f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level,
               f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
               f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
               f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
               f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
               f'{self.name}.syngas_ratio': self.syngas_ratio,
               f'{self.name}.syngas_ratio_technos': self.syngas_ratio_technos,
               f'{self.name}.energy_detailed_techno_prices': self.syngas_detailed_prices,
               f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
               f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
               f'{self.name}.is_stream_demand': True,
               f'{self.name}.{self.model_name}.{GlossaryEnergy.LifetimeName}': GlossaryEnergy.LifetimeDefaultValueGradientTest,
               }

    def test_01_wgs_jacobian(self):

        self.model_name = 'WGS'

        discipline_test_function(
            module_path='energy_models.models.gaseous_hydrogen.water_gas_shift.water_gas_shift_disc.WaterGasShiftDiscipline',
            model_name=self.model_name,
            name=self.name,
            jacobian_test=True,
            show_graphs=False,
            inputs_dict=self.get_inputs_dict(),
            namespaces_dict=self.ns_dict,
            pickle_directory=dirname(__file__),
            pickle_name=f'hydrogen_{self.model_name}.pkl',
            override_dump_jacobian=False
        )


    def test_02_plasma_cracking_jacobian(self):

        self.model_name = 'plasma_cracking'

        discipline_test_function(
            module_path='energy_models.models.gaseous_hydrogen.plasma_cracking.plasma_cracking_disc.PlasmaCrackingDiscipline',
            model_name=self.model_name,
            name=self.name,
            jacobian_test=True,
            show_graphs=False,
            inputs_dict=self.get_inputs_dict(),
            namespaces_dict=self.ns_dict,
            pickle_directory=dirname(__file__),
            pickle_name=f'hydrogen_{self.model_name}.pkl',
            override_dump_jacobian=False
        )



    def test_03_electrolysis_PEMjacobian(self):

        self.model_name = 'PEM'

        discipline_test_function(
            module_path='energy_models.models.gaseous_hydrogen.electrolysis.pem.electrolysis_pem_disc.ElectrolysisPEMDiscipline',
            model_name=self.model_name,
            name=self.name,
            jacobian_test=True,
            show_graphs=False,
            inputs_dict=self.get_inputs_dict(),
            namespaces_dict=self.ns_dict,
            pickle_directory=dirname(__file__),
            pickle_name=f'hydrogen_{self.model_name}.pkl',
            override_dump_jacobian=False
        )


    def test_04_electrolysis_SOEC_jacobian(self):

        self.model_name = 'SOEC'

        discipline_test_function(
            module_path='energy_models.models.gaseous_hydrogen.electrolysis.soec.electrolysis_soec_disc.ElectrolysisSOECDiscipline',
            model_name=self.model_name,
            name=self.name,
            jacobian_test=True,
            show_graphs=False,
            inputs_dict=self.get_inputs_dict(),
            namespaces_dict=self.ns_dict,
            pickle_directory=dirname(__file__),
            pickle_name=f'hydrogen_{self.model_name}.pkl',
            override_dump_jacobian=False
        )


    def test_05_electrolysis_AWE_jacobian(self):

        self.model_name = 'AWE'

        discipline_test_function(
            module_path='energy_models.models.gaseous_hydrogen.electrolysis.awe.electrolysis_awe_disc.ElectrolysisAWEDiscipline',
            model_name=self.model_name,
            name=self.name,
            jacobian_test=True,
            show_graphs=False,
            inputs_dict=self.get_inputs_dict(),
            namespaces_dict=self.ns_dict,
            pickle_directory=dirname(__file__),
            pickle_name=f'hydrogen_{self.model_name}.pkl',
            override_dump_jacobian=False
        )



    def test_06_hydrogen_jacobian(self):

        self.model_name = f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}'

        discipline_test_function(
            module_path='energy_models.core.stream_type.energy_disciplines.gaseous_hydrogen_disc.GaseousHydrogenDiscipline',
            model_name=self.model_name,
            name=self.name,
            jacobian_test=True,
            show_graphs=False,
            inputs_dict=self.get_inputs_dict(),
            namespaces_dict=self.ns_dict,
            pickle_directory=dirname(__file__),
            pickle_name=f'hydrogen_{self.model_name}.pkl',
            override_dump_jacobian=False
        )
