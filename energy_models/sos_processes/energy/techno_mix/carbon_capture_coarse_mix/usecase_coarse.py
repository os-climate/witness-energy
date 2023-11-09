'''
Copyright 2022 Airbus SAS
Modifications on 2023/10/23-2023/11/07 Copyright 2023 Capgemini

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

from climateeconomics.glossarycore import GlossaryCore
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.carbon_models.flue_gas import FlueGas
from energy_models.core.energy_mix_study_manager import EnergyMixStudyManager
from energy_models.core.energy_process_builder import INVEST_DISCIPLINE_DEFAULT, INVEST_DISCIPLINE_OPTIONS
from energy_models.glossaryenergy import GlossaryEnergy

DEFAULT_TECHNOLOGIES_LIST = [
    'direct_air_capture.DirectAirCaptureTechno', 'flue_gas_capture.FlueGasTechno']
TECHNOLOGIES_LIST = [
    'direct_air_capture.DirectAirCaptureTechno', 'flue_gas_capture.FlueGasTechno']


class Study(EnergyMixStudyManager):
    def __init__(self, year_start=2020, year_end=2050, time_step=1, technologies_list=TECHNOLOGIES_LIST,
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
        invest_carbon_capture_mix_dict = {}
        l_ctrl = np.arange(0, 16)

        if 'direct_air_capture.DirectAirCaptureTechno' in self.technologies_list:
            invest_carbon_capture_mix_dict['direct_air_capture.DirectAirCaptureTechno'] = np.array(
                [0.5, 0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])

        if 'flue_gas_capture.FlueGasTechno' in self.technologies_list:
            invest_carbon_capture_mix_dict['flue_gas_capture.FlueGasTechno'] = [
                10 * (1 - 0.04) ** i for i in l_ctrl]

        if self.bspline:
            invest_carbon_capture_mix_dict[GlossaryCore.Years] = self.years

            for techno in self.technologies_list:
                invest_carbon_capture_mix_dict[techno], _ = self.invest_bspline(
                    invest_carbon_capture_mix_dict[techno], len(self.years))

        carbon_capture_mix_invest_df = pd.DataFrame(
            invest_carbon_capture_mix_dict)

        return carbon_capture_mix_invest_df

    def setup_usecase(self):
        energy_mix_name = 'EnergyMix'
        self.energy_name = CarbonCapture.name
        flue_gas_name = FlueGas.node_name
        ccs_name = f'{self.prefix_name}.{CarbonCapture.name}'

        years = np.arange(self.year_start, self.year_end + 1)
        # reference_data_name = 'Reference_aircraft_data'
        self.energy_prices = pd.DataFrame({GlossaryCore.Years: years,
                                           'renewable': 10.0,
                                           'fossil': 2.0,
                                           })

        # the value for invest_level is just set as an order of magnitude
        self.invest_level = pd.DataFrame(
            {GlossaryCore.Years: years, GlossaryCore.InvestValue: 10.0})
        self.flue_gas_mean = pd.DataFrame(
            {GlossaryCore.Years: years, GlossaryCore.FlueGasMean: 0.13})

        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [0.01486, 0.01722, 0.02027,
                     0.02901,  0.03405,   0.03908,  0.04469,   0.05029]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {GlossaryCore.Years: years, GlossaryCore.CO2Tax: func(years)})
        self.margin = pd.DataFrame(
            {GlossaryCore.Years: years, GlossaryCore.MarginValue: np.ones(len(years)) * 110.0})
        # From future of hydrogen
        self.transport = pd.DataFrame(
            {GlossaryCore.Years: years, 'transport': np.ones(len(years)) * 7.0})
        self.energy_carbon_emissions = pd.DataFrame(
            {GlossaryCore.Years: years, 'amine': 0.0, 'potassium': 0.0, 'electricity': 0.0, 'calcium': 0.0, 'renewable': 0.0, 'fossil': 5.0})

        flue_gas_list = ['fossil.FossilSimpleTechno', 'carbon_capture.direct_air_capture.DirectAirCaptureTechno' ]
        fossil_simple_techno_prod = pd.DataFrame({GlossaryCore.Years: years,
                                                  f'{CarbonCapture.flue_gas_name} (Mt)': 0.1})

        investment_mix = self.get_investments()
        values_dict = {f'{self.study_name}.{GlossaryCore.YearStart}': self.year_start,
                       f'{self.study_name}.{GlossaryCore.YearEnd}': self.year_end,
                       f'{self.study_name}.{GlossaryCore.ccs_list}': ['carbon_capture', 'carbon_storage'],
                       f'{self.study_name}.{ccs_name}.{flue_gas_name}.{GlossaryCore.techno_list}': flue_gas_list,
                       f'{self.study_name}.{ccs_name}.{GlossaryCore.techno_list}': self.technologies_list,
                       f'{self.study_name}.{ccs_name}.flue_gas_capture.flue_gas_mean': self.flue_gas_mean,
                       f'{self.study_name}.{ccs_name}.direct_air_capture.DirectAirCaptureTechno.{GlossaryCore.MarginValue}': self.margin,
                       f'{self.study_name}.{ccs_name}.flue_gas_capture.FlueGasTechno.{GlossaryCore.MarginValue}': self.margin,
                       f'{self.study_name}.{ccs_name}.{GlossaryCore.TransportCostValue}': self.transport,
                       f'{self.study_name}.{ccs_name}.{GlossaryCore.TransportMarginValue}': self.margin,
                       f'{self.study_name}.{ccs_name}.invest_techno_mix': investment_mix,
                       }

        techno_capital = pd.DataFrame({GlossaryCore.Years: years, GlossaryCore.Capital: 0.0})
        if self.main_study:
            values_dict.update(
                {

                    f'{self.study_name}.{GlossaryCore.CO2TaxesValue}': self.co2_taxes,
                    f'{self.study_name}.{energy_mix_name}.{GlossaryCore.EnergyPricesValue}': self.energy_prices,
                    f'{self.study_name}.{energy_mix_name}.{GlossaryCore.EnergyCO2EmissionsValue}': self.energy_carbon_emissions,
                    f'{self.study_name}.{energy_mix_name}.fossil.FossilSimpleTechno.flue_gas_co2_ratio': np.array([0.13]),
                    f'{self.study_name}.{energy_mix_name}.fossil.FossilSimpleTechno.techno_production': fossil_simple_techno_prod,
                    f'{self.study_name}.{energy_mix_name}.fossil.FossilSimpleTechno.{GlossaryEnergy.TechnoCapitalDfValue}': techno_capital,})
            if self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[1]:
                investment_mix_sum = investment_mix.drop(
                    columns=[GlossaryCore.Years]).sum(axis=1)
                for techno in self.technologies_list:
                    invest_level_techno = pd.DataFrame({GlossaryCore.Years: self.invest_level[GlossaryCore.Years].values,
                                                        GlossaryCore.InvestValue: self.invest_level[GlossaryCore.InvestValue].values * investment_mix[techno].values / investment_mix_sum})
                    values_dict[f'{self.study_name}.{ccs_name}.{techno}.{GlossaryCore.InvestLevelValue}'] = invest_level_techno
                    values_dict[f'{self.study_name}.{ccs_name}.{techno}.{GlossaryEnergy.TechnoCapitalDfValue}'] = techno_capital
            else:
                values_dict[f'{self.study_name}.{ccs_name}.{GlossaryCore.InvestLevelValue}'] = self.invest_level
        else:
            self.update_dv_arrays()

        return [values_dict]


if '__main__' == __name__:
    uc_cls = Study(main_study=True,
                   technologies_list=DEFAULT_TECHNOLOGIES_LIST)
    uc_cls.test()
