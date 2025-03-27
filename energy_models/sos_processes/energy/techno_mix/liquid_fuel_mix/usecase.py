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

from energy_models.core.energy_mix_study_manager import EnergyMixStudyManager
from energy_models.core.energy_process_builder import (
    INVEST_DISCIPLINE_DEFAULT,
    INVEST_DISCIPLINE_OPTIONS,
)
from energy_models.core.stream_type.energy_models.liquid_fuel import LiquidFuel
from energy_models.glossaryenergy import GlossaryEnergy

DEFAULT_TECHNOLOGIES_LIST = [GlossaryEnergy.Refinery]#, GlossaryEnergy.FischerTropsch]
TECHNOLOGIES_LIST = [GlossaryEnergy.Refinery]#, GlossaryEnergy.FischerTropsch]


class Study(EnergyMixStudyManager):
    def __init__(self, year_start=GlossaryEnergy.YearStartDefault, year_end=GlossaryEnergy.YearEndDefault,
                 technologies_list=GlossaryEnergy.DEFAULT_TECHNO_DICT[f'{GlossaryEnergy.fuel}.{GlossaryEnergy.liquid_fuel}']["value"],
                 bspline=True, main_study=True, execution_engine=None, invest_discipline=INVEST_DISCIPLINE_DEFAULT):
        super().__init__(__file__, technologies_list=technologies_list,
                         main_study=main_study, execution_engine=execution_engine, invest_discipline=invest_discipline)
        self.syngas_detailed_prices = None
        self.year_start = year_start
        self.year_end = year_end
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.stream_name = None
        self.bspline = bspline

    def get_investments(self):

        invest_liquid_fuel_mix_dict = {}
        l_ctrl = np.arange(GlossaryEnergy.NB_POLES_FULL)

        if GlossaryEnergy.Refinery in self.technologies_list:
            invest_liquid_fuel_mix_dict[GlossaryEnergy.Refinery] = [
                max(10.0, 100.0 - 5.0 * i) for i in l_ctrl]

        if GlossaryEnergy.FischerTropsch in self.technologies_list:
            invest_liquid_fuel_mix_dict[GlossaryEnergy.FischerTropsch] = [
                min(100.0, 0.1 + 10 * i) for i in l_ctrl]

        if self.bspline:
            invest_liquid_fuel_mix_dict[GlossaryEnergy.Years] = self.years
            for techno in self.technologies_list:
                invest_liquid_fuel_mix_dict[techno], _ = self.invest_bspline(
                    invest_liquid_fuel_mix_dict[techno], len(self.years))

        liquid_fuel_mix_invest_df = pd.DataFrame(invest_liquid_fuel_mix_dict)

        return liquid_fuel_mix_invest_df

    def setup_usecase(self, study_folder_path=None):
        energy_mix_name = 'EnergyMix'
        self.stream_name = LiquidFuel.name
        energy_name = f'{energy_mix_name}.{self.stream_name}'

        years = np.arange(self.year_start, self.year_end + 1)

        energy_prices = pd.DataFrame({GlossaryEnergy.Years: years,
                                      GlossaryEnergy.electricity: 16.0,
                                      GlossaryEnergy.CO2: 0.0,
                                      'crude oil': 38.0,
                                      GlossaryEnergy.carbon_captured: 70.,
                                      f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}': 15.,
                                      GlossaryEnergy.syngas: 50.0})

        self.syngas_detailed_prices = pd.DataFrame({GlossaryEnergy.CoalGasification: np.ones(len(years)) * 50.0,
                                                    GlossaryEnergy.CoElectrolysis: 2.0 * 50.0,
                                                    'ATR': 1.5 * 50.0,
                                                    GlossaryEnergy.SMR: 50.0})

        # the value for invest_level is just set as an order of magnitude
        invest_level = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.InvestValue: 10.0})
        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [14.86, 17.22, 20.27,
                     29.01, 34.05, 39.08, 44.69, 50.29]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.CO2Tax: func(years)})
        margin = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.MarginValue: np.ones(len(years)) * 110.0})
        # From smart ap
        transport = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'transport': np.ones(len(years)) * 200.0})
        energy_carbon_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.solid_fuel: 0.64 / 4.86, GlossaryEnergy.electricity: 0.0, GlossaryEnergy.methane: 0.123 / 15.4,
             GlossaryEnergy.syngas: 0.0, f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}': 0.0, 'crude oil': 0.02533, GlossaryEnergy.carbon_captured: 0.})

        # define invest mix
        investment_mix = self.get_investments()

        values_dict = {f'{self.study_name}.{GlossaryEnergy.YearStart}': self.year_start,
                       f'{self.study_name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.study_name}.{energy_name}.{GlossaryEnergy.techno_list}': self.technologies_list,
                       f'{self.study_name}.{energy_name}.{GlossaryEnergy.Refinery}.{GlossaryEnergy.MarginValue}': margin,
                       f'{self.study_name}.{energy_name}.{GlossaryEnergy.FischerTropsch}.{GlossaryEnergy.MarginValue}': margin,
                       f'{self.study_name}.{energy_name}.{GlossaryEnergy.TransportCostValue}': transport,
                       f'{self.study_name}.{energy_name}.{GlossaryEnergy.TransportMarginValue}': margin,
                       # f'{self.study_name}.{energy_name}.{GlossaryEnergy.invest_techno_mix}.: investment_mix,
                       }
        if self.main_study:
            values_dict.update({
                f'{self.study_name}.{GlossaryEnergy.CO2TaxesValue}': co2_taxes,
                f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.CO2}_intensity_by_energy': energy_carbon_emissions,
                f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.CH4}_intensity_by_energy': energy_carbon_emissions,
                f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.N2O}_intensity_by_energy': energy_carbon_emissions,
                f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.StreamPricesValue}': energy_prices,
                f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy. syngas}.{GlossaryEnergy.syngas_ratio}': np.ones(len(years)) * 0.33,
            })
            if self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[1]:
                investment_mix_sum = investment_mix.drop(
                    columns=[GlossaryEnergy.Years]).sum(axis=1)
                for techno in self.technologies_list:
                    invest_level_techno = pd.DataFrame({GlossaryEnergy.Years: invest_level[GlossaryEnergy.Years].values,
                                                        GlossaryEnergy.InvestValue: invest_level[
                                                                                        GlossaryEnergy.InvestValue].values *
                                                                                    investment_mix[
                                                                                        techno].values / investment_mix_sum})
                    values_dict[
                        f'{self.study_name}.{energy_name}.{techno}.{GlossaryEnergy.InvestLevelValue}'] = invest_level_techno
            else:
                values_dict[f'{self.study_name}.{energy_name}.{GlossaryEnergy.InvestLevelValue}'] = invest_level
        else:
            self.update_dv_arrays()
        return [values_dict]


if '__main__' == __name__:
    uc_cls = Study(main_study=True)
    uc_cls.load_data()
    uc_cls.run()