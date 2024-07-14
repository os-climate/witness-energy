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
from energy_models.models.gaseous_hydrogen.electrolysis.awe.electrolysis_awe_disc import (
    ElectrolysisAWEDiscipline,
)
from energy_models.models.gaseous_hydrogen.electrolysis.pem.electrolysis_pem_disc import (
    ElectrolysisPEMDiscipline,
)
from energy_models.models.gaseous_hydrogen.electrolysis.soec.electrolysis_soec_disc import (
    ElectrolysisSOECDiscipline,
)
from energy_models.models.gaseous_hydrogen.plasma_cracking.plasma_cracking_disc import (
    PlasmaCrackingDiscipline,
)
from energy_models.models.gaseous_hydrogen.water_gas_shift.water_gas_shift_disc import (
    WaterGasShiftDiscipline,
)


class HydrogenJacobianTestCase(AbstractJacobianUnittest):
    """
    Hydrogen jacobian test class
    """

    def analytic_grad_entry(self):
        return [
            self.test_01_wgs_jacobian,
            # self.test_02_plasma_cracking_jacobian,
            self.test_03_electrolysis_PEMjacobian,
            self.test_04_electrolysis_SOEC_jacobian,
            self.test_05_electrolysis_AWE_jacobian,
            self.test_06_hydrogen_jacobian,
            self.test_07_wgs_jacobian_invest_negative,
            self.test_08_gaseous_hydrogen_discipline_jacobian,
        ]

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.energy_name = GlossaryEnergy.hydrogen
        self.year_end = GlossaryEnergy.YearEndDefaultValueGradientTest
        years = np.arange(GlossaryEnergy.YearStartDefault, self.year_end + 1)
        self.years = years

        self.electrolysis_techno_prices = pd.DataFrame(
            {GlossaryEnergy.Electrolysis: np.array([0.09, 0.08974117039450046, 0.08948672733558984,
                                       0.089236536471781, 0.08899046935409588, 0.08874840310033885,
                                       0.08875044941298937, 0.08875249600769718, 0.08875454288453355,
                                       0.08875659004356974, 0.0887586374848771, 0.08893789675406477,
                                       0.08911934200930778, 0.08930302260662477, 0.08948898953954933,
                                       0.08967729551117891, 0.08986799501019029, 0.09006114439108429,
                                       0.09025680195894345, 0.09045502805900876, 0.09065588517140537,
                                       0.0908594380113745, 0.09106575363539733, 0.09127490155362818,
                                       0.09148695384909017, 0.0917019853041231, 0.0919200735346165,
                                       0.09214129913260598, 0.09236574581786147, 0.09259350059915213,
                                       0.0928246539459331])[:len(self.years)] * 1000.0,
             'Electrolysis_wotaxes': np.array([0.09, 0.08974117039450046, 0.08948672733558984,
                                               0.089236536471781, 0.08899046935409588, 0.08874840310033885,
                                               0.08875044941298937, 0.08875249600769718, 0.08875454288453355,
                                               0.08875659004356974, 0.0887586374848771, 0.08893789675406477,
                                               0.08911934200930778, 0.08930302260662477, 0.08948898953954933,
                                               0.08967729551117891, 0.08986799501019029, 0.09006114439108429,
                                               0.09025680195894345, 0.09045502805900876, 0.09065588517140537,
                                               0.0908594380113745, 0.09106575363539733, 0.09127490155362818,
                                               0.09148695384909017, 0.0917019853041231, 0.0919200735346165,
                                               0.09214129913260598, 0.09236574581786147, 0.09259350059915213,
                                               0.0928246539459331])[:len(self.years)] * 1000.0})

        self.smr_techno_prices = pd.DataFrame(
            {GlossaryEnergy.Years: years,GlossaryEnergy.WaterGasShift: np.array([0.06363, 0.0612408613576689, 0.059181808246196024, 0.05738028027202377,
                                        0.0557845721244601, 0.05435665353332419, 0.05225877624361548,
                                        0.05045797192512811, 0.04888746457113824, 0.04750006564084081,
                                        0.04626130284326101, 0.044848110567750024, 0.043596892851567724,
                                        0.04247763196812953, 0.04146768302263715, 0.04054957955940597,
                                        0.03970959176775726, 0.03893674917609171, 0.038222160192931814,
                                        0.03755852715493717, 0.03693979356326306, 0.03636088278590117,
                                        0.03581750135963429, 0.03530598876014997, 0.03482320115289285,
                                        0.03436642036567466, 0.03393328183670935, 0.033521717015978045,
                                        0.03312990690071806, 0.032756244237772174, 0.03239930253734476])[:len(self.years)] * 1000.0,
             'WaterGasShift_wotaxes': np.array([0.06363, 0.0612408613576689, 0.059181808246196024, 0.05738028027202377,
                                                0.0557845721244601, 0.05435665353332419, 0.05225877624361548,
                                                0.05045797192512811, 0.04888746457113824, 0.04750006564084081,
                                                0.04626130284326101, 0.044848110567750024, 0.043596892851567724,
                                                0.04247763196812953, 0.04146768302263715, 0.04054957955940597,
                                                0.03970959176775726, 0.03893674917609171, 0.038222160192931814,
                                                0.03755852715493717, 0.03693979356326306, 0.03636088278590117,
                                                0.03581750135963429, 0.03530598876014997, 0.03482320115289285,
                                                0.03436642036567466, 0.03393328183670935, 0.033521717015978045,
                                                0.03312990690071806, 0.032756244237772174,
                                                0.03239930253734476])[:len(self.years)] * 1000.0
             })

        self.plasmacracking_techno_prices = pd.DataFrame({GlossaryEnergy.Years: years,
                                                          GlossaryEnergy.PlasmaCracking:
                                                              np.array(
                                                                  [0.06363, 0.0612408613576689, 0.059181808246196024,
                                                                   0.05738028027202377,
                                                                   0.0557845721244601, 0.05435665353332419,
                                                                   0.05225877624361548,
                                                                   0.05045797192512811, 0.04888746457113824,
                                                                   0.04750006564084081,
                                                                   0.04626130284326101, 0.044848110567750024,
                                                                   0.043596892851567724,
                                                                   0.04247763196812953, 0.04146768302263715,
                                                                   0.04054957955940597,
                                                                   0.03970959176775726, 0.03893674917609171,
                                                                   0.038222160192931814,
                                                                   0.03755852715493717, 0.03693979356326306,
                                                                   0.03636088278590117,
                                                                   0.03581750135963429, 0.03530598876014997,
                                                                   0.03482320115289285,
                                                                   0.03436642036567466, 0.03393328183670935,
                                                                   0.033521717015978045,
                                                                   0.03312990690071806, 0.032756244237772174,
                                                                   0.03239930253734476])[:len(self.years)] * 1000.0,
                                                          'PlasmaCracking_wotaxes':
                                                              np.array(
                                                                  [0.06363, 0.0612408613576689, 0.059181808246196024,
                                                                   0.05738028027202377,
                                                                   0.0557845721244601, 0.05435665353332419,
                                                                   0.05225877624361548,
                                                                   0.05045797192512811, 0.04888746457113824,
                                                                   0.04750006564084081,
                                                                   0.04626130284326101, 0.044848110567750024,
                                                                   0.043596892851567724,
                                                                   0.04247763196812953, 0.04146768302263715,
                                                                   0.04054957955940597,
                                                                   0.03970959176775726, 0.03893674917609171,
                                                                   0.038222160192931814,
                                                                   0.03755852715493717, 0.03693979356326306,
                                                                   0.03636088278590117,
                                                                   0.03581750135963429, 0.03530598876014997,
                                                                   0.03482320115289285,
                                                                   0.03436642036567466, 0.03393328183670935,
                                                                   0.033521717015978045,
                                                                   0.03312990690071806, 0.032756244237772174,
                                                                   0.03239930253734476])[:len(self.years)] * 1000.0
                                                          })

        self.smr_consumption = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                             f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen} ({GlossaryEnergy.energy_unit})': [230.779470] * len(self.years),
                                             f'{GlossaryEnergy.electricity} ({GlossaryEnergy.energy_unit})': [82.649011] * len(self.years),
                                             f'{GlossaryEnergy.syngas} ({GlossaryEnergy.energy_unit})': [3579.828092] * len(self.years),
                                             f"{GlossaryEnergy.WaterResource} ({GlossaryEnergy.mass_unit})": [381.294427] * len(self.years)})

        self.smr_production = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                            f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen} ({GlossaryEnergy.energy_unit})': [2304.779470] * len(self.years),
                                            f"{GlossaryEnergy.CO2FromFlueGas} ({GlossaryEnergy.mass_unit})": [844.027980] * len(self.years)})

        self.plasmacracking_production = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                                       f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen} ({GlossaryEnergy.energy_unit})': np.linspace(1e-5, 1, len(self.years)),
                                                       f"{GlossaryEnergy.SolidCarbon} ({GlossaryEnergy.mass_unit})": [0.008622] * len(self.years)})

        self.plasmacracking_consumption = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                                        f'{GlossaryEnergy.electricity} ({GlossaryEnergy.energy_unit})': [0.019325] * len(self.years),
                                                        f'{GlossaryEnergy.methane} ({GlossaryEnergy.energy_unit})': [0.213945] * len(self.years)})

        self.electrolysis_consumption = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                                      f'{GlossaryEnergy.electricity} ({GlossaryEnergy.energy_unit})': [4.192699] * len(self.years),
                                                      f"{GlossaryEnergy.WaterResource} ({GlossaryEnergy.mass_unit})": [0.021638] * len(
                                                          self.years)})

        self.electrolysis_production = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                                     f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen} ({GlossaryEnergy.energy_unit})': [2.684940] * len(self.years),
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
        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [0.01486, 0.01722, 0.02027,
                     0.02901, 0.03405, 0.03908, 0.04469, 0.05029]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.CO2Tax: func(self.years)})

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
                                      0.0928246539459331])[:len(self.years)] * 1000

        self.stream_prices = pd.DataFrame({GlossaryEnergy.Years: self.years, GlossaryEnergy.electricity: electricity_price,
                                           GlossaryEnergy.syngas: np.ones(len(self.years)) * 33.,
                                           GlossaryEnergy.methane: np.array(
                                               [0.06363, 0.0612408613576689, 0.059181808246196024, 0.05738028027202377,
                                                0.0557845721244601, 0.05435665353332419, 0.05225877624361548,
                                                0.05045797192512811, 0.04888746457113824, 0.04750006564084081,
                                                0.04626130284326101, 0.044848110567750024, 0.043596892851567724,
                                                0.04247763196812953, 0.04146768302263715, 0.04054957955940597,
                                                0.03970959176775726, 0.03893674917609171, 0.038222160192931814,
                                                0.03755852715493717, 0.03693979356326306, 0.03636088278590117,
                                                0.03581750135963429, 0.03530598876014997, 0.03482320115289285,
                                                0.03436642036567466, 0.03393328183670935, 0.033521717015978045,
                                                0.03312990690071806, 0.032756244237772174,
                                                0.03239930253734476])[:len(self.years)] * 1000 / 1.5,
                                           f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}': 50
                                           })

        self.stream_co2_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.electricity: 0.02, GlossaryEnergy.syngas: 0.2, GlossaryEnergy.methane: -0.1})
        self.invest_level = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.InvestValue: np.ones(len(self.years)) * 0.1715})

        self.invest_level_negative = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.InvestValue: np.linspace(5000, -5000, len(self.years))})
        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [14.86, 17.22, 20.27,
                     29.01, 34.05, 39.08, 44.69, 50.29]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.CO2Tax: func(self.years)})
        self.margin = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.MarginValue: np.ones(len(self.years)) * 110.0})
        # From future of hydrogen
        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, 'transport': np.ones(len(self.years)) * 500.0})

        self.syngas_ratio = np.linspace(33.0, 209.0, len(self.years))
        self.syngas_detailed_prices = pd.DataFrame({GlossaryEnergy.SMR: np.ones(len(self.years)) * 34.,
                                                    
                                                    GlossaryEnergy.CoElectrolysis: np.ones(len(self.years)) * 60.,
                                                    GlossaryEnergy.BiomassGasification: np.ones(len(self.years)) * 50.
                                                    })
        self.syngas_ratio_technos = {GlossaryEnergy.SMR: 33.0,
                                     GlossaryEnergy.CoElectrolysis: 100.0,
                                     GlossaryEnergy.BiomassGasification: 200.0
                                     }
        CO2_tax = np.array([0.01722, 0.033496, 0.049772, 0.066048, 0.082324, 0.0986,
                            0.114876, 0.131152, 0.147428, 0.163704, 0.17998, 0.217668,
                            0.255356, 0.293044, 0.330732, 0.36842, 0.406108, 0.443796,
                            0.481484, 0.519172, 0.55686, 0.591706, 0.626552, 0.661398,
                            0.696244, 0.73109, 0.765936, 0.800782, 0.835628, 0.870474,
                            0.90532])[:len(self.years)] * 1000
        self.CO2_taxes = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                       GlossaryEnergy.CO2Tax: CO2_tax})

        self.invest = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                    GlossaryEnergy.InvestValue: np.array([4435750000.0, 4522000000.0, 4608250000.0,
                                                                          4694500000.0, 4780750000.0, 4867000000.0,
                                                                          4969400000.0, 5071800000.0, 5174200000.0,
                                                                          5276600000.0, 5379000000.0, 5364700000.0,
                                                                          5350400000.0, 5336100000.0, 5321800000.0,
                                                                          5307500000.0, 5293200000.0, 5278900000.0,
                                                                          5264600000.0, 5250300000.0, 5236000000.0,
                                                                          5221700000.0, 5207400000.0, 5193100000.0,
                                                                          5178800000.0, 5164500000.0, 5150200000.0,
                                                                          5135900000.0, 5121600000.0, 5107300000.0,
                                                                          5093000000.0])[:len(self.years)] * 1.0e-9})
        self.land_use_required_mock = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, 'random techno (Gha)': 0.0})

        self.land_use_required_WaterGasShift = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, 'WaterGasShift (Gha)': 0.0})
        self.land_use_required_Electrolysis = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, 'Electrolysis (Gha)': 0.0})
        self.land_use_required_PlasmaCracking = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, 'PlasmaCracking (Gha)': 0.0})

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

    def tearDown(self):
        pass

    def test_01_wgs_jacobian(self):

        self.name = 'Test'
        self.model_name = 'WGS'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_hydrogen': f'{self.name}',
                   'ns_syngas': f'{self.name}',
                   GlossaryEnergy.NS_ENERGY_MIX: f'{self.name}',
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.gaseous_hydrogen.water_gas_shift.water_gas_shift_disc.WaterGasShiftDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        techno_infos_dict = WaterGasShiftDiscipline.techno_infos_dict_default
        techno_infos_dict["lifetime"] = GlossaryEnergy.LifetimeDefaultValueGradientTest

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
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
                       f'{self.name}.techno_infos_dict': techno_infos_dict
                       }

        self.ee.load_study_from_input_dict(inputs_dict)
        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step',
                            local_data=disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryEnergy.UtilisationRatioValue}',
                                    f'{self.name}.{GlossaryEnergy.StreamPricesValue}',
                                    f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}',
                                    f'{self.name}.syngas_ratio',
                                    f'{self.name}.{GlossaryEnergy.CO2TaxesValue}',
                                    f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}',
                                    f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}',
                                    ],
                            outputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoPricesValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.CO2EmissionsValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoProductionValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoCapitalValue}',
                                     f'{self.name}.{self.model_name}.non_use_capital',
                                     ], )

    def _test_02_plasma_cracking_jacobian(self):

        self.name = 'Test'
        self.model_name = 'plasma_cracking'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_hydrogen': self.name,
                   GlossaryEnergy.NS_ENERGY_MIX: self.name,
                   'ns_carb': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.gaseous_hydrogen.plasma_cracking.plasma_cracking_disc.PlasmaCrackingDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        techno_infos_dict = PlasmaCrackingDiscipline.techno_infos_dict_default
        techno_infos_dict["lifetime"] = GlossaryEnergy.LifetimeDefaultValueGradientTest

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                           self.years),
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_default_resources_prices(
                           self.years),
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.CO2_taxes,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_plasmacracking,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': pd.concat(
                           [self.margin[GlossaryEnergy.Years], self.margin[GlossaryEnergy.MarginValue] / 1.1],
                           axis=1, keys=[GlossaryEnergy.Years, GlossaryEnergy.MarginValue]),
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
                       f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       f'{self.name}.techno_infos_dict': techno_infos_dict
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline
        np.set_printoptions(100)
        # np.set_printoptions(threshold=50)

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step',
                            local_data=disc_techno.local_data,
                            inputs=[
                                f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}',
                                f'{self.name}.{GlossaryEnergy.StreamPricesValue}',
                                f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}',
                                f'{self.name}.{GlossaryEnergy.CO2TaxesValue}',
                                f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}',
                                f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}',
                                f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}'
                            ],
                            outputs=[f'{self.name}.{self.model_name}.percentage_resource',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoPricesValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.CO2EmissionsValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoProductionValue}',
                                     ], )
        # outputs=[f'{self.name}.{self.model_name}.percentage_resource',
        #          f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoPricesValue}',
        #                             f'{self.name}.{self.model_name}.{GlossaryEnergy.CO2EmissionsValue}',
        #                             f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionValue}',
        #                             f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoProductionValue}'],)
        # self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
        #                     discipline=disc_techno, step=1.0e-18, derr_approx='complex_step',
        #                     inputs=[
        #                         f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}'],
        #                     outputs=[f'{self.name}.{self.model_name}.percentage_resource'])

    def test_03_electrolysis_PEMjacobian(self):

        self.name = 'Test'
        self.model_name = 'PEM'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_hydrogen': self.name,
                   GlossaryEnergy.NS_ENERGY_MIX: self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.gaseous_hydrogen.electrolysis.pem.electrolysis_pem_disc.ElectrolysisPEMDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        techno_infos_dict = ElectrolysisPEMDiscipline.techno_infos_dict_default
        techno_infos_dict["lifetime"] = GlossaryEnergy.LifetimeDefaultValueGradientTest

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                           self.years),
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_default_resources_prices(
                           self.years),
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.CO2_taxes,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': pd.concat(
                           [self.margin[GlossaryEnergy.Years], self.margin[GlossaryEnergy.MarginValue] / 1.1],
                           axis=1, keys=[GlossaryEnergy.Years, GlossaryEnergy.MarginValue]),
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
                       f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       f'{self.name}.techno_infos_dict': techno_infos_dict
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-15, derr_approx='complex_step',
                            local_data=disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryEnergy.UtilisationRatioValue}',
                                    f'{self.name}.{GlossaryEnergy.StreamPricesValue}',
                                    f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}',
                                    f'{self.name}.{GlossaryEnergy.CO2TaxesValue}',
                                    f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}',
                                    f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}',
                                    ],
                            outputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoPricesValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.CO2EmissionsValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoProductionValue}',
                                     ], )

    def test_04_electrolysis_SOEC_jacobian(self):

        self.name = 'Test'
        self.model_name = 'SOEC'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_hydrogen': self.name,
                   GlossaryEnergy.NS_ENERGY_MIX: self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.gaseous_hydrogen.electrolysis.soec.electrolysis_soec_disc.ElectrolysisSOECDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        techno_infos_dict = ElectrolysisSOECDiscipline.techno_infos_dict_default
        techno_infos_dict["lifetime"] = GlossaryEnergy.LifetimeDefaultValueGradientTest

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                           self.years),
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_default_resources_prices(
                           self.years),
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.CO2_taxes,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': pd.concat(
                           [self.margin[GlossaryEnergy.Years], self.margin[GlossaryEnergy.MarginValue] / 1.1],
                           axis=1, keys=[GlossaryEnergy.Years, GlossaryEnergy.MarginValue]),
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
                       f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       f'{self.name}.techno_infos_dict': techno_infos_dict
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step',
                            local_data=disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryEnergy.UtilisationRatioValue}',
                                    f'{self.name}.{GlossaryEnergy.StreamPricesValue}',
                                    f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}',
                                    f'{self.name}.{GlossaryEnergy.CO2TaxesValue}',
                                    f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}',
                                    f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}',
                                    ],
                            outputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoPricesValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.CO2EmissionsValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoProductionValue}',
                                     ], )

    def test_05_electrolysis_AWE_jacobian(self):

        self.name = 'Test'
        self.model_name = 'AWE'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_hydrogen': self.name,
                   GlossaryEnergy.NS_ENERGY_MIX: self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.gaseous_hydrogen.electrolysis.awe.electrolysis_awe_disc.ElectrolysisAWEDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        techno_infos_dict = ElectrolysisAWEDiscipline.techno_infos_dict_default
        techno_infos_dict["lifetime"] = GlossaryEnergy.LifetimeDefaultValueGradientTest

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                           self.years),
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_default_resources_prices(
                           self.years),
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.CO2_taxes,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': pd.concat(
                           [self.margin[GlossaryEnergy.Years], self.margin[GlossaryEnergy.MarginValue] / 1.1],
                           axis=1, keys=[GlossaryEnergy.Years, GlossaryEnergy.MarginValue]),
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
                       f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       f'{self.name}.techno_infos_dict': techno_infos_dict
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step',
                            local_data=disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryEnergy.UtilisationRatioValue}',
                                    f'{self.name}.{GlossaryEnergy.StreamPricesValue}',
                                    f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}',
                                    f'{self.name}.{GlossaryEnergy.CO2TaxesValue}',
                                    f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}',
                                    f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}',
                                    ],
                            outputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoPricesValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.CO2EmissionsValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoProductionValue}',
                                     ], )

    def test_06_hydrogen_jacobian(self):

        self.name = 'Test'
        self.model_name = f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': f'{self.name}',
                   'ns_hydrogen': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   GlossaryEnergy.NS_ENERGY_MIX: self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.stream_type.energy_disciplines.gaseous_hydrogen_disc.GaseousHydrogenDiscipline'

        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        techno_capital = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.Capital: 20000 * np.ones_like(self.years)
        })

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearStart}': GlossaryEnergy.YearStartDefault,
                       f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryEnergy.techno_list}': [GlossaryEnergy.WaterGasShift, GlossaryEnergy.PlasmaCracking],
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.TechnoConsumptionValue}': self.smr_consumption,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}': self.smr_consumption,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.TechnoProductionValue}': self.smr_production,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.TechnoPricesValue}': self.smr_techno_prices,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.CO2EmissionsValue}': self.smr_carbon_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.LandUseRequiredValue}': self.land_use_required_WaterGasShift,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.PlasmaCracking}.{GlossaryEnergy.TechnoConsumptionValue}': self.plasmacracking_consumption,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.TechnoCapitalValue}': techno_capital,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.PlasmaCracking}.{GlossaryEnergy.TechnoCapitalValue}': techno_capital,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.PlasmaCracking}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}': self.plasmacracking_consumption,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.PlasmaCracking}.{GlossaryEnergy.TechnoProductionValue}': self.plasmacracking_production,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.PlasmaCracking}.{GlossaryEnergy.TechnoPricesValue}': self.plasmacracking_techno_prices,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.PlasmaCracking}.{GlossaryEnergy.CO2EmissionsValue}': self.plasma_cracking_carbon_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.PlasmaCracking}.{GlossaryEnergy.LandUseRequiredValue}': self.land_use_required_PlasmaCracking,
                       f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}.pkl',
                            discipline=disc, step=1.0e-16, derr_approx='complex_step', local_data=disc.local_data,
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.TechnoPricesValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryEnergy.PlasmaCracking}.{GlossaryEnergy.TechnoPricesValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.TechnoConsumptionValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryEnergy.PlasmaCracking}.{GlossaryEnergy.TechnoConsumptionValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.TechnoProductionValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryEnergy.PlasmaCracking}.{GlossaryEnergy.TechnoProductionValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.TechnoCapitalValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryEnergy.PlasmaCracking}.{GlossaryEnergy.TechnoCapitalValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryEnergy.WaterGasShift}.{GlossaryEnergy.CO2EmissionsValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryEnergy.PlasmaCracking}.{GlossaryEnergy.CO2EmissionsValue}'],
                            outputs=[f'{self.name}.{self.model_name}.techno_mix',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.StreamPricesValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.CO2EmissionsValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.EnergyConsumptionValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.EnergyTypeCapitalDfValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.EnergyProductionValue}'], )

    def test_08_gaseous_hydrogen_discipline_jacobian(self):

        self.name = 'Test'
        self.energy_name = f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': f'{self.name}',
                   'ns_hydrogen': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_resource': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.stream_type.energy_disciplines.gaseous_hydrogen_disc.GaseousHydrogenDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.energy_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_streams_input_dict.pkl'), 'rb')
        mda_data_input_dict = pickle.load(pkl_file)
        pkl_file.close()

        namespace = f'{self.name}'
        inputs_dict = {}
        coupled_inputs = []
        for key in mda_data_input_dict[self.energy_name].keys():
            if key in [GlossaryEnergy.techno_list, GlossaryEnergy.CO2TaxesValue, GlossaryEnergy.YearStart,
                       GlossaryEnergy.YearEnd,
                       'scaling_factor_energy_production', 'scaling_factor_energy_consumption',
                       'scaling_factor_techno_consumption', 'scaling_factor_techno_production', ]:
                inputs_dict[f'{namespace}.{key}'] = mda_data_input_dict[self.energy_name][key]['value']
                if mda_data_input_dict[self.energy_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{key}']
            else:
                inputs_dict[f'{namespace}.{self.energy_name}.{key}'] = mda_data_input_dict[self.energy_name][key][
                    'value']
                if mda_data_input_dict[self.energy_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{self.energy_name}.{key}']

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_streams_output_dict.pkl'), 'rb')
        mda_data_output_dict = pickle.load(pkl_file)
        pkl_file.close()

        coupled_outputs = []
        for key in mda_data_output_dict[self.energy_name].keys():
            if mda_data_output_dict[self.energy_name][key]['is_coupling']:
                coupled_outputs += [f'{namespace}.{self.energy_name}.{key}']

        technos = inputs_dict[f"{self.name}.technologies_list"]
        techno_capital = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.Capital: 20000 * np.ones_like(self.years)
        })
        for techno in technos:
            inputs_dict[
                f"{self.name}.{self.energy_name}.{techno}.{GlossaryEnergy.TechnoCapitalValue}"] = techno_capital
            coupled_inputs.append(f"{self.name}.{self.energy_name}.{techno}.{GlossaryEnergy.TechnoCapitalValue}")

        coupled_outputs.append(f"{self.name}.{self.energy_name}.{GlossaryEnergy.EnergyTypeCapitalDfValue}")
        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.energy_name}')[0].mdo_discipline_wrapp.mdo_discipline
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}.pkl',
                            discipline=disc, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc.local_data,
                            inputs=coupled_inputs,
                            outputs=coupled_outputs, )


if '__main__' == __name__:
    np.set_printoptions(threshold=np.inf)
    cls = HydrogenJacobianTestCase()
    cls.setUp()
    # unittest.main()
    cls.test_03_electrolysis_PEMjacobian()
    # cls.test_01_wgs_jacobian()
