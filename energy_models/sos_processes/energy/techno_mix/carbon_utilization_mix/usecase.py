'''
Copyright 2023 Capgemini

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

from energy_models.core.energy_mix_study_manager import EnergyMixStudyManager
from energy_models.core.energy_process_builder import INVEST_DISCIPLINE_DEFAULT, INVEST_DISCIPLINE_OPTIONS
from energy_models.core.stream_type.carbon_models.carbon_utilization import CarbonUtilization
from energy_models.core.stream_type.carbon_models.food_storage import FoodStorage
from energy_models.database_witness_energy import DatabaseWitnessEnergy
from energy_models.glossaryenergy import GlossaryEnergy

DEFAULT_TECHNOLOGIES_LIST = ['food_storage_applications.BeverageCarbonation', 'food_storage_applications.CarbonatedWater',
                             'food_storage_applications.AlgaeCultivation']
TECHNOLOGIES_LIST = ['food_storage_applications.BeverageCarbonation', 'food_storage_applications.CarbonatedWater',
                             'food_storage_applications.AlgaeCultivation']
TECHNOLOGIES_LIST_COARSE = ['food_storage_applications.BeverageCarbonation']
TECHNOLOGIES_FOOD_STORAGE_LIST_COARSE = ['food_storage_applications.BeverageCarbonation']
DEFAULT_FOOD_STORAGE_LIST = ['food_storage_applications.BeverageCarbonation']
TECHNOLOGIES_LIST_DEV = ['food_storage_applications.BeverageCarbonation', 'food_storage_applications.CarbonatedWater',
                             'food_storage_applications.AlgaeCultivation']
FOOD_STORAGE_TECHNOLOGIES_LIST_DEV = ['carbon_utilization.food_storage_applications.BeverageCarbonation', 'carbon_utilization.food_storage_applications.CarbonatedWater']


class Study(EnergyMixStudyManager):
    def __init__(self, year_start=GlossaryEnergy.YeartStartDefault, year_end=2050, time_step=1, technologies_list=TECHNOLOGIES_LIST,
                 bspline=True, main_study=True, prefix_name=None, execution_engine=None, invest_discipline=INVEST_DISCIPLINE_DEFAULT):
        super().__init__(__file__, technologies_list=technologies_list,
                         main_study=main_study, execution_engine=execution_engine, invest_discipline=invest_discipline)
        self.year_start = year_start
        self.year_end = year_end
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.energy_name = None
        self.bspline = bspline
        self.prefix_name = 'EnergyMix'
        if prefix_name is not None:
            self.prefix_name = prefix_name

    def get_investments(self):
        invest_carbon_utilization_mix_dict = {}
        l_ctrl = np.arange(0, 8)

        if 'food_storage_applications.BeverageCarbonation' in self.technologies_list:
            invest_carbon_utilization_mix_dict['food_storage_applications.BeverageCarbonation'] = np.array(
                [0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])

        if 'food_storage_applications.CarbonatedWater' in self.technologies_list:
            invest_carbon_utilization_mix_dict['food_storage_applications.CarbonatedWater'] = [
                0.1 * (1 + 0.03) ** i for i in l_ctrl]

        if 'food_storage_applications.AlgaeCultivation' in self.technologies_list:
            invest_carbon_utilization_mix_dict['food_storage_applications.AlgaeCultivation'] = [
                10 * (1 - 0.04) ** i for i in l_ctrl]

        if 'food_storage_applications.FoodStorageApplicationsTechno' in self.technologies_list:
            invest_carbon_utilization_mix_dict['food_storage_applications.FoodStorageApplicationsTechno'] = np.ones(GlossaryEnergy.NB_POLES_COARSE) * 1e-6
            invest_2020_ccus = DatabaseWitnessEnergy.InvestCCUS2020.value
            invest_carbon_utilization_mix_dict['food_storage_applications.FoodStorageApplicationsTechno'][0] = invest_2020_ccus / 3.

        if self.bspline:
            invest_carbon_utilization_mix_dict[GlossaryEnergy.Years] = self.years

            for techno in self.technologies_list:
                invest_carbon_utilization_mix_dict[techno], _ = self.invest_bspline(
                    invest_carbon_utilization_mix_dict[techno], len(self.years))

        carbon_utilization_mix_invest_df = pd.DataFrame(
            invest_carbon_utilization_mix_dict)

        return carbon_utilization_mix_invest_df

    def setup_usecase(self):
        energy_mix_name = 'EnergyMix'
        self.energy_name = CarbonUtilization.name
        food_storage_name = FoodStorage.node_name
        ccs_name = f'{self.prefix_name}.{CarbonUtilization.name}'

        years = np.arange(self.year_start, self.year_end + 1)
        # reference_data_name = 'Reference_aircraft_data'
        self.energy_prices = pd.DataFrame({GlossaryEnergy.Years: years,
                                           'electricity': 10.0
                                           })

        # the value for invest_level is just set as an order of magnitude
        self.invest_level = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.InvestValue: 10.0})
        self.food_storage_mean = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.FoodStorageMean: 0.13})

        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [0.01486, 0.01722, 0.02027,
                     0.02901,  0.03405,   0.03908,  0.04469,   0.05029]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.CO2Tax: func(years)})
        self.margin = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.MarginValue: np.ones(len(years)) * 110.0})
        # From future of hydrogen
        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'transport': np.ones(len(years)) * 7.0})
        self.energy_carbon_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'electricity': 0.0
             })

        algaecultivation_production = pd.DataFrame({GlossaryEnergy.Years: years,
                                      f'{CarbonUtilization.food_storage_name} (Mt)': 0.1})
        algaecultivation_consumption = pd.DataFrame({GlossaryEnergy.Years: years,
                                         f'{CarbonUtilization.food_storage_name} (Mt)': 0.1})
        beveragecarbonation_production = pd.DataFrame({GlossaryEnergy.Years: years,
                                      f'{CarbonUtilization.food_storage_name} (Mt)': 0.1})
        beveragecarbonation_consumption = pd.DataFrame({GlossaryEnergy.Years: years,
                                      f'{CarbonUtilization.food_storage_name} (Mt)': 0.1})
        carbonatedwater_prod = pd.DataFrame({GlossaryEnergy.Years: years,
                                        f'{CarbonUtilization.food_storage_name} (Mt)': 0.1})
        carbonatedwater_cons = pd.DataFrame({GlossaryEnergy.Years: years,
                                        f'{CarbonUtilization.food_storage_name} (Mt)': 0.1})
        foodstorageapplicationstechno_prod = pd.DataFrame({GlossaryEnergy.Years: years,
                                                    f'{CarbonUtilization.food_storage_name} (Mt)': 0.1})
        foodstorageapplicationstechno_cons = pd.DataFrame({GlossaryEnergy.Years: years,
                                                    f'{CarbonUtilization.food_storage_name} (Mt)': 0.1})


        investment_mix = self.get_investments()
        values_dict = {f'{self.study_name}.{GlossaryEnergy.YearStart}': self.year_start,
                       f'{self.study_name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       # f'{self.study_name}.{ccs_name}.{food_storage_name}.{GlossaryEnergy.food_storage_emission_techno_list}': DEFAULT_FOOD_STORAGE_LIST,
                       f'{self.study_name}.{ccs_name}.{GlossaryEnergy.techno_list}': self.technologies_list,
                       f'{self.study_name}.{ccs_name}.food_storage_applications.{GlossaryEnergy.techno_list}': FOOD_STORAGE_TECHNOLOGIES_LIST_DEV,
                       f'{self.study_name}.{ccs_name}.food_storage_applications.food_storage_mean': self.food_storage_mean,
                       f'{self.study_name}.{ccs_name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.study_name}.{ccs_name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.study_name}.{ccs_name}.invest_techno_mix': investment_mix,
                       f'{self.study_name}.{GlossaryEnergy.ccs_list}' : ['carbon_capture', 'carbon_storage', 'carbon_utilization']


                       }

        techno_margin_dict = {
            f'{self.study_name}.{ccs_name}.{techno}.{GlossaryEnergy.MarginValue}': self.margin for techno in self.technologies_list}
        values_dict.update(techno_margin_dict)

        self.techno_capital = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.Capital: 0.0})

        if self.main_study:
            values_dict.update(
                {
                    f'{self.study_name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                    f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.EnergyPricesValue}': self.energy_prices,
                    f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.EnergyCO2EmissionsValue}': self.energy_carbon_emissions,
                    # f'{self.study_name}.{energy_mix_name}.electricity.CoalGen.flue_gas_co2_ratio': np.array([0.13]),
                    # f'{self.study_name}.{energy_mix_name}.electricity.GasTurbine.flue_gas_co2_ratio': np.array([0.035]),
                    # f'{self.study_name}.{energy_mix_name}.electricity.CombinedCycleGasTurbine.flue_gas_co2_ratio': np.array([0.035]),
                    # f'{self.study_name}.{energy_mix_name}.hydrogen.gaseous_hydrogen.WaterGasShift.flue_gas_co2_ratio': np.array([0.175]),
                    # f'{self.study_name}.{energy_mix_name}.liquid_fuel.FischerTropsch.flue_gas_co2_ratio': np.array([0.12]),
                    # f'{self.study_name}.{energy_mix_name}.liquid_fuel.Refinery.flue_gas_co2_ratio': np.array([0.12]),
                    # f'{self.study_name}.{energy_mix_name}.methane.FossilGas.flue_gas_co2_ratio': np.array([0.085]),
                    # f'{self.study_name}.{energy_mix_name}.solid_fuel.Pelletizing.flue_gas_co2_ratio': np.array([0.12]),
                    # f'{self.study_name}.{energy_mix_name}.syngas.CoalGasification.flue_gas_co2_ratio': np.array([0.13]),
                    # f'{self.study_name}.{energy_mix_name}.syngas.Pyrolysis.flue_gas_co2_ratio': np.array([0.13]),
                    # f'{self.study_name}.{energy_mix_name}.fossil.FossilSimpleTechno.flue_gas_co2_ratio': np.array([0.12]),
                    f'{self.study_name}.carbon_utilization.food_storage_applications.CarbonatedWater.food_storage_co2_ratio': np.array([0.035]),
                    f'{self.study_name}.carbon_utilization.food_storage_applications.BeverageCarbonation.food_storage_co2_ratio': np.array([0.035]),
                    f'{self.study_name}.carbon_utilization.food_storage_applications.AlgaeCultivation.food_storage_co2_ratio': np.array([0.035]),
                    f'{self.study_name}.carbon_utilization.food_storage_applications.FoodStorageApplicationsTechno.food_storage_co2_ratio': np.array(
                        [0.035]),

                    f'{self.study_name}.CCUS.carbon_utilization.food_storage_applications.CarbonatedWater.{GlossaryEnergy.TechnoProductionValue}': carbonatedwater_prod,
                    f'{self.study_name}.CCUS.carbon_utilization.food_storage_applications.BeverageCarbonation.{GlossaryEnergy.TechnoProductionValue}': beveragecarbonation_production,
                    f'{self.study_name}.CCUS.carbon_utilization.food_storage_applications.AlgaeCultivation.{GlossaryEnergy.TechnoProductionValue}': algaecultivation_production,
                    f'{self.study_name}.CCUS.carbon_utilization.food_storage_applications.FoodStorageApplicationsTechno.{GlossaryEnergy.TechnoProductionValue}': foodstorageapplicationstechno_prod,

                    f'{self.study_name}.CCUS.carbon_utilization.food_storage_applications.CarbonatedWater.{GlossaryEnergy.TechnoConsumptionValue}': carbonatedwater_cons,
                    f'{self.study_name}.CCUS.carbon_utilization.food_storage_applications.BeverageCarbonation.{GlossaryEnergy.TechnoConsumptionValue}': beveragecarbonation_consumption,
                    f'{self.study_name}.CCUS.carbon_utilization.food_storage_applications.AlgaeCultivation.{GlossaryEnergy.TechnoConsumptionValue}': algaecultivation_consumption,
                    f'{self.study_name}.CCUS.carbon_utilization.food_storage_applications.FoodStorageApplicationsTechno.{GlossaryEnergy.TechnoConsumptionValue}': foodstorageapplicationstechno_cons,

                    # f"{self.study_name}.{energy_mix_name}.carbon_capture.flue_gas_capture.electricity.CoalGen.{GlossaryEnergy.TechnoCapitalValue}": self.techno_capital,
                    # f"{self.study_name}.{energy_mix_name}.carbon_capture.flue_gas_capture.electricity.GasTurbine.{GlossaryEnergy.TechnoCapitalValue}": self.techno_capital,
                    # f"{self.study_name}.{energy_mix_name}.carbon_capture.flue_gas_capture.electricity.CombinedCycleGasTurbine.{GlossaryEnergy.TechnoCapitalValue}": self.techno_capital,
                    # f"{self.study_name}.{energy_mix_name}.carbon_capture.flue_gas_capture.hydrogen.gaseous_hydrogen.WaterGasShift.{GlossaryEnergy.TechnoCapitalValue}": self.techno_capital,
                    # f"{self.study_name}.{energy_mix_name}.carbon_capture.flue_gas_capture.liquid_fuel.FischerTropsch.{GlossaryEnergy.TechnoCapitalValue}": self.techno_capital,
                    # f"{self.study_name}.{energy_mix_name}.carbon_capture.flue_gas_capture.liquid_fuel.Refinery.{GlossaryEnergy.TechnoCapitalValue}": self.techno_capital,
                    # f"{self.study_name}.{energy_mix_name}.carbon_capture.flue_gas_capture.methane.FossilGas.{GlossaryEnergy.TechnoCapitalValue}": self.techno_capital,
                    # f"{self.study_name}.{energy_mix_name}.carbon_capture.flue_gas_capture.solid_fuel.Pelletizing.{GlossaryEnergy.TechnoCapitalValue}": self.techno_capital,
                    # f"{self.study_name}.{energy_mix_name}.carbon_capture.flue_gas_capture.syngas.CoalGasification.{GlossaryEnergy.TechnoCapitalValue}": self.techno_capital,
                    # f"{self.study_name}.{energy_mix_name}.carbon_capture.flue_gas_capture.fossil.FossilSimpleTechno.{GlossaryEnergy.TechnoCapitalValue}": self.techno_capital,
                    f"{self.study_name}.{energy_mix_name}.carbon_utilization.food_storage_applications.carbon_utilization.food_storage_applications.BeverageCarbonation.{GlossaryEnergy.TechnoCapitalValue}": self.techno_capital,
                    f"{self.study_name}.{energy_mix_name}.carbon_utilization.food_storage_applications.carbon_utilization.food_storage_applications.CarbonatedWater.{GlossaryEnergy.TechnoCapitalValue}": self.techno_capital,
                    f"{self.study_name}.{energy_mix_name}.carbon_utilization.food_storage_applications.carbon_utilization.food_storage_applications.AlgaeCultivation.{GlossaryEnergy.TechnoCapitalValue}": self.techno_capital,
                    f"{self.study_name}.{energy_mix_name}.carbon_utilization.food_storage_applications.carbon_utilization.food_storage_applications.FoodStorageApplicationsTechno.{GlossaryEnergy.TechnoCapitalValue}": self.techno_capital,

                    f'{self.study_name}.{ccs_name}.food_storage_applications.{GlossaryEnergy.InvestLevelValue}': self.invest_level,
                })

            if self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[1]:
                investment_mix_sum = investment_mix.drop(
                    columns=[GlossaryEnergy.Years]).sum(axis=1)
                for techno in self.technologies_list:
                    invest_level_techno = pd.DataFrame({GlossaryEnergy.Years: self.invest_level[GlossaryEnergy.Years].values,
                                                        GlossaryEnergy.InvestValue: self.invest_level[GlossaryEnergy.InvestValue].values * investment_mix[techno].values / investment_mix_sum})
                    values_dict[f'{self.study_name}.{ccs_name}.{techno}.{GlossaryEnergy.InvestLevelValue}'] = invest_level_techno
                    # print(f'{self.study_name}.{ccs_name}.{techno}.{GlossaryEnergy.InvestLevelValue}')
            else:
                values_dict[f'{self.study_name}.{ccs_name}.{GlossaryEnergy.InvestLevelValue}'] = self.invest_level

        else:
            self.update_dv_arrays()

        return [values_dict]


if '__main__' == __name__:
    uc_cls = Study(main_study=True,
                   technologies_list=DEFAULT_TECHNOLOGIES_LIST)
    uc_cls.ee.display_treeview_nodes()
    uc_cls.test()
