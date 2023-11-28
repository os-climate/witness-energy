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
from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from energy_models.glossaryenergy import GlossaryEnergy

DEFAULT_TECHNOLOGIES_LIST = ['NaturalGasBoilerHighHeat', 'ElectricBoilerHighHeat',
                         'HeatPumpHighHeat', 'GeothermalHighHeat', 'CHPHighHeat', 'HydrogenBoilerHighHeat']
TECHNOLOGIES_LIST = ['NaturalGasBoilerHighHeat', 'ElectricBoilerHighHeat',
                         'HeatPumpHighHeat', 'GeothermalHighHeat', 'CHPHighHeat', 'HydrogenBoilerHighHeat']
TECHNOLOGIES_LIST_COARSE = ['NaturalGasBoilerHighHeat']
TECHNOLOGIES_LIST_DEV = ['NaturalGasBoilerHighHeat', 'ElectricBoilerHighHeat',
                         'HeatPumpHighHeat', 'GeothermalHighHeat', 'CHPHighHeat', 'HydrogenBoilerHighHeat']


class Study(EnergyMixStudyManager):
    def __init__(self, year_start=2020, year_end=2050, time_step=1, technologies_list=TECHNOLOGIES_LIST, bspline=True, main_study=True, execution_engine=None,
                 invest_discipline=INVEST_DISCIPLINE_DEFAULT):
        super().__init__(__file__, technologies_list=technologies_list,
                         main_study=main_study, execution_engine=execution_engine, invest_discipline=invest_discipline)
        self.year_start = year_start
        self.year_end = year_end
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.energy_name = None
        self.bspline = bspline

    def get_investments(self):
        invest_high_heat_mix_dict = {}
        l_ctrl = np.arange(0, 8)

        if 'NaturalGasBoilerHighHeat' in self.technologies_list:
            invest_high_heat_mix_dict['NaturalGasBoilerHighHeat'] = [
                0.02, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0]

        if 'ElectricBoilerHighHeat' in self.technologies_list:
            invest_high_heat_mix_dict['ElectricBoilerHighHeat'] = [
                0.02, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]

        if 'HeatPumpHighHeat' in self.technologies_list:
            invest_high_heat_mix_dict['HeatPumpHighHeat'] = list(np.ones(
                len(l_ctrl)) * 0.001)

        if 'GeothermalHighHeat' in self.technologies_list:
            invest_high_heat_mix_dict['GeothermalHighHeat'] = list(np.ones(
                len(l_ctrl)) * 0.001)

        if 'CHPHighHeat' in self.technologies_list:
            invest_high_heat_mix_dict['CHPHighHeat'] = list(np.ones(
                len(l_ctrl)) * 0.001)
        if 'HydrogenBoilerHighHeat' in self.technologies_list:
            invest_high_heat_mix_dict['HydrogenBoilerHighHeat'] = list(np.ones(
                len(l_ctrl)) * 0.001)

        if self.bspline:
            invest_high_heat_mix_dict[GlossaryEnergy.Years] = self.years

            for techno in self.technologies_list:
                invest_high_heat_mix_dict[techno], _ = self.invest_bspline(
                    invest_high_heat_mix_dict[techno], len(self.years))

        high_heat_mix_invest_df = pd.DataFrame(invest_high_heat_mix_dict)

        return high_heat_mix_invest_df

    def setup_usecase(self):
        energy_mix_name = 'EnergyMix'
        self.energy_name = hightemperatureheat.name
        energy_name = f'EnergyMix.{self.energy_name}'

        years = np.arange(self.year_start, self.year_end + 1)
        # energy_prices data came from test files  of corresponding technologies
        self.energy_prices = pd.DataFrame({GlossaryEnergy.Years: years,
                                           'electricity': 148.0,
                                           'syngas': 80.0,
                                           'biogas': 70.0,
                                           'methane': 100,
                                           'biomass_dry': 45,
                                           'hydrogen.gaseous_hydrogen': 60
                                        })

        # the value for invest_level is just set as an order of magnitude
        self.invest_level = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.InvestValue: 10.0})
        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [14.86, 17.22, 20.27,
                     29.01, 34.05, 39.08, 44.69, 50.29]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.CO2Tax: func(years)})
        self.margin = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.MarginValue: np.ones(len(years)) * 110.0})
        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'transport': np.ones(len(years)) * 0})

        self.resources_price = pd.DataFrame(columns=[GlossaryEnergy.Years, 'CO2', 'water'])
        self.resources_price[GlossaryEnergy.Years] = years
        self.resources_price['CO2'] = np.linspace(50.0, 100.0, len(years))
        # biomass_dry price in $/kg
        self.energy_carbon_emissions = pd.DataFrame({GlossaryEnergy.Years: years, 'biomass_dry': - 0.64 / 4.86, 'electricity': 0.0, 'methane': 0.0, 'water': 0.0})

        investment_mix = self.get_investments()
        #land_rate = {'land_rate': 5000.0, 'land_rate_unit': '$/Gha', }

        values_dict = {f'{self.study_name}.{GlossaryEnergy.YearStart}': self.year_start,
                       f'{self.study_name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.study_name}.{energy_name}.{GlossaryEnergy.techno_list}': self.technologies_list,
                       f'{self.study_name}.{energy_name}.NaturalGasBoilerHighHeat.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.study_name}.{energy_name}.ElectricBoilerHighHeat.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.study_name}.{energy_name}.HeatPumpHighHeat.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.study_name}.{energy_name}.GeothermalHighHeat.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.study_name}.{energy_name}.CHPHighHeat.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.study_name}.{energy_name}.HydrogenBoilerHighHeat.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.study_name}.{energy_name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.study_name}.{energy_name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.study_name}.{energy_name}.invest_techno_mix': investment_mix,
                       # f'{self.study_name}.{energy_name}.ElectricBoiler.flux_input_dict': land_rate,
                       # f'{self.study_name}.{energy_name}.NaturalGasBoiler.flux_input_dict': land_rate,
                       # f'{self.study_name}.{energy_name}.HeatPump.flux_input_dict': land_rate,
                       # f'{self.study_name}.{energy_name}.Geothermal.flux_input_dict': land_rate,
                       }

        if self.main_study:
            values_dict.update(
                {f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.EnergyPricesValue}': self.energy_prices,
                 f'{self.study_name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                 f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.EnergyCO2EmissionsValue}': self.energy_carbon_emissions,
                 })
            if self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[1]:
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
    import logging
    import sys
    print("test stderr", file=sys.stderr)
    for handler in logging.getLogger().handlers:
        print(handler)
    logging.info('TEST')
    uc_cls = Study(main_study=True,
                   technologies_list=TECHNOLOGIES_LIST)
    uc_cls.load_data()
    print(len(uc_cls.execution_engine.root_process.proxy_disciplines))
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
