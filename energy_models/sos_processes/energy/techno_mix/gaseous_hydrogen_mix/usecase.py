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

import numpy as np
import pandas as pd
import scipy.interpolate as sc

from energy_models.core.energy_mix_study_manager import EnergyMixStudyManager
from energy_models.core.energy_process_builder import INVEST_DISCIPLINE_DEFAULT, INVEST_DISCIPLINE_OPTIONS
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import GaseousHydrogen
from energy_models.glossaryenergy import GlossaryEnergy

DEFAULT_TECHNOLOGIES_LIST = [
    'WaterGasShift', 'Electrolysis.SOEC', 'Electrolysis.PEM', 'Electrolysis.AWE',  'PlasmaCracking']
TECHNOLOGIES_LIST = ['WaterGasShift', 'Electrolysis.SOEC',
                     'Electrolysis.PEM', 'Electrolysis.AWE', 'PlasmaCracking']
TECHNOLOGIES_LIST_DEV = ['WaterGasShift', 'Electrolysis.SOEC', 'Electrolysis.PEM', 'Electrolysis.AWE',
                         'PlasmaCracking'
                         ]


class Study(EnergyMixStudyManager):
    def __init__(self, year_start=GlossaryEnergy.YeartStartDefault, year_end=2050, time_step=1, technologies_list=TECHNOLOGIES_LIST,
                 bspline=True, main_study=True, execution_engine=None, invest_discipline=INVEST_DISCIPLINE_DEFAULT):
        super().__init__(__file__, technologies_list=technologies_list,
                         main_study=main_study, execution_engine=execution_engine, invest_discipline=invest_discipline)
        self.year_start = year_start
        self.year_end = year_end
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.energy_name = None
        self.bspline = bspline

    def get_investments(self):
        invest_hydrogen_mix_dict = {}
        l_ctrl = np.arange(0, 8)

        if 'PlasmaCracking' in self.technologies_list:
            invest_hydrogen_mix_dict['PlasmaCracking'] = [
                0.001 * (1 + 0.03)**i for i in l_ctrl]

        if 'WaterGasShift' in self.technologies_list:
            invest_hydrogen_mix_dict['WaterGasShift'] = [
                10.0 for i in l_ctrl]

        if 'Electrolysis.SOEC' in self.technologies_list:
            invest_hydrogen_mix_dict['Electrolysis.SOEC'] = [
                0.01 + 0.001 * i for i in l_ctrl]

        if 'Electrolysis.AWE' in self.technologies_list:
            invest_hydrogen_mix_dict['Electrolysis.AWE'] = [
                0.01 + 0.001 * i for i in l_ctrl]

        if 'Electrolysis.PEM' in self.technologies_list:
            invest_hydrogen_mix_dict['Electrolysis.PEM'] = [
                0.01 + 0.001 * i for i in l_ctrl]

        if self.bspline:
            invest_hydrogen_mix_dict[GlossaryEnergy.Years] = self.years
            for techno in self.technologies_list:
                invest_hydrogen_mix_dict[techno], _ = self.invest_bspline(
                    invest_hydrogen_mix_dict[techno], len(self.years))

        hydrogen_mix_invest_df = pd.DataFrame(invest_hydrogen_mix_dict)

        return hydrogen_mix_invest_df

    def setup_usecase(self):
        energy_mix_name = 'EnergyMix'
        self.energy_name = GaseousHydrogen.name

        energy_name = f'{energy_mix_name}.{self.energy_name}'

        years = np.arange(self.year_start, self.year_end + 1)
        # reference_data_name = 'Reference_aircraft_data'
        self.energy_prices = pd.DataFrame({GlossaryEnergy.Years: years,
                                           'electricity': 16,
                                           'syngas': 80.0,
                                           'methane': 70.0,
                                           'hydrogen.gaseous_hydrogen': 94.0})

        # the value for invest_level is just set as an order of magnitude
        self.invest_level = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.InvestValue: 10.0})

        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [14.86, 17.22, 20.27,
                     29.01,  34.05,   39.08,  44.69,   50.29]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.CO2Tax: func(years)})
        self.margin = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.MarginValue: np.ones(len(years)) * 110.0})
        # From future of hydrogen
        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'transport': np.ones(len(years)) * 500.0})

        self.resources_price = pd.DataFrame(columns=[GlossaryEnergy.Years, 'CO2', 'water'])
        self.resources_price[GlossaryEnergy.Years] = years
        self.resources_price['CO2'] = np.linspace(50.0, 100.0, len(years))
        # biomass_dry price in $/kg
        self.energy_carbon_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'biomass_dry': - 0.64 / 4.86, 'solid_fuel': 0.64 / 4.86, 'electricity': 0.0, 'methane': 0.123 / 15.4, 'syngas': 0.0, 'hydrogen.gaseous_hydrogen': 0.0, 'crude oil': 0.02533})

        # define invest mix
        investment_mix = self.get_investments()

        values_dict = {f'{self.study_name}.{GlossaryEnergy.YearStart}': self.year_start,
                       f'{self.study_name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.study_name}.{energy_name}.{GlossaryEnergy.techno_list}': self.technologies_list,
                       f'{self.study_name}.{energy_mix_name}.syngas.syngas_ratio': np.ones(len(years)) * 0.5,
                       f'{self.study_name}.{energy_name}.Electrolysis.PEM.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.study_name}.{energy_name}.Electrolysis.AWE.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.study_name}.{energy_name}.Electrolysis.SOEC.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.study_name}.{energy_name}.PlasmaCracking.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.study_name}.{energy_name}.WaterGasShift.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.study_name}.{energy_name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.study_name}.{energy_name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.study_name}.{energy_name}.invest_techno_mix': investment_mix,
                       }
        if self.main_study:
            values_dict.update(
                {f'{self.study_name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                 f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.EnergyPricesValue}': self.energy_prices,
                 f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.EnergyCO2EmissionsValue}': self.energy_carbon_emissions,


                 })
            if self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[1]:
                investment_mix_sum = investment_mix.drop(
                    columns=[GlossaryEnergy.Years]).sum(axis=1)
                for techno in self.technologies_list:
                    invest_level_techno = pd.DataFrame({GlossaryEnergy.Years: self.invest_level[GlossaryEnergy.Years].values,
                                                        GlossaryEnergy.InvestValue: self.invest_level[GlossaryEnergy.InvestValue].values * investment_mix[techno].values / investment_mix_sum})
                    values_dict[f'{self.study_name}.{energy_name}.{techno}.{GlossaryEnergy.InvestLevelValue}'] = invest_level_techno
            elif self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[2]:
                investment_mix_sum = investment_mix.drop(
                    columns=[GlossaryEnergy.Years]).sum(axis=1)
                for techno in self.technologies_list:
                    invest_level_techno = pd.DataFrame({GlossaryEnergy.Years: self.invest_level[GlossaryEnergy.Years].values,
                                                        GlossaryEnergy.InvestValue: self.invest_level[GlossaryEnergy.InvestValue].values * investment_mix[techno].values / investment_mix_sum})
                    values_dict[f'{self.study_name}.{energy_name}.{techno}.{GlossaryEnergy.InvestLevelValue}'] = invest_level_techno
            else:
                values_dict[f'{self.study_name}.{energy_name}.{GlossaryEnergy.InvestLevelValue}'] = self.invest_level
        else:
            self.update_dv_arrays()

        return [values_dict]


if '__main__' == __name__:
    uc_cls = Study(main_study=True,
                   technologies_list=DEFAULT_TECHNOLOGIES_LIST)
    uc_cls.load_data()
    uc_cls.run()
#     ppf = PostProcessingFactory()
#     for disc in uc_cls.execution_engine.root_process.sos_disciplines:
#         filters = ppf.get_post_processing_filters_by_discipline(
#             disc)
#         graph_list = ppf.get_post_processing_by_discipline(
#             disc, filters, as_json=False)
#
#         for graph in graph_list:
#             graph.to_plotly()
