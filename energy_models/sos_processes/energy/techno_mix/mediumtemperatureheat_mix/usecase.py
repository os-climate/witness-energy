'''
Copyright (c) 2023 Capgemini

All rights reserved

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer
in the documentation and/or mother materials provided with the distribution.
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
INCLUDING BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND OR ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''
import numpy as np
import pandas as pd
import scipy.interpolate as sc

from energy_models.core.energy_mix_study_manager import EnergyMixStudyManager
from energy_models.core.stream_type.energy_models.heat import mediumtemperatureheat
from energy_models.core.energy_process_builder import INVEST_DISCIPLINE_DEFAULT, INVEST_DISCIPLINE_OPTIONS

DEFAULT_TECHNOLOGIES_LIST = ['NaturalGasBoilerMediumHeat', 'ElectricBoilerMediumHeat',
                             'HeatPumpMediumHeat', 'GeothermalMediumHeat', 'CHPMediumHeat', 'HydrogenBoilerMediumHeat']
TECHNOLOGIES_LIST = ['NaturalGasBoilerMediumHeat', 'ElectricBoilerMediumHeat',
                     'HeatPumpMediumHeat', 'GeothermalMediumHeat', 'CHPMediumHeat', 'HydrogenBoilerMediumHeat']
TECHNOLOGIES_LIST_COARSE = ['NaturalGasBoilerMediumHeat']
TECHNOLOGIES_LIST_DEV = ['NaturalGasBoilerMediumHeat', 'ElectricBoilerMediumHeat',
                         'HeatPumpMediumHeat', 'GeothermalMediumHeat', 'CHPMediumHeat', 'HydrogenBoilerMediumHeat']


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
        invest_medium_heat_mix_dict = {}
        l_ctrl = np.arange(0, 8)

        if 'NaturalGasBoilerMediumHeat' in self.technologies_list:
            invest_medium_heat_mix_dict['NaturalGasBoilerMediumHeat'] = [
                0.02, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0]

        if 'ElectricBoilerMediumHeat' in self.technologies_list:
            invest_medium_heat_mix_dict['ElectricBoilerMediumHeat'] = [
                0.02, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]

        if 'HeatPumpMediumHeat' in self.technologies_list:
            invest_medium_heat_mix_dict['HeatPumpMediumHeat'] = list(np.ones(
                len(l_ctrl)) * 0.001)

        if 'GeothermalMediumHeat' in self.technologies_list:
            invest_medium_heat_mix_dict['GeothermalMediumHeat'] = list(np.ones(
                len(l_ctrl)) * 0.001)

        if 'CHPMediumHeat' in self.technologies_list:
            invest_medium_heat_mix_dict['CHPMediumHeat'] = list(np.ones(
                len(l_ctrl)) * 0.001)

        if 'HydrogenBoilerMediumHeat' in self.technologies_list:
            invest_medium_heat_mix_dict['HydrogenBoilerMediumHeat'] = list(np.ones(
                len(l_ctrl)) * 0.001)

        if self.bspline:
            invest_medium_heat_mix_dict['years'] = self.years

            for techno in self.technologies_list:
                invest_medium_heat_mix_dict[techno], _ = self.invest_bspline(
                    invest_medium_heat_mix_dict[techno], len(self.years))

        medium_heat_mix_invest_df = pd.DataFrame(invest_medium_heat_mix_dict)

        return medium_heat_mix_invest_df

    def setup_usecase(self):
        energy_mix_name = 'EnergyMix'
        self.energy_name = mediumtemperatureheat.name
        energy_name = f'EnergyMix.{self.energy_name}'

        years = np.arange(self.year_start, self.year_end + 1)
        # energy_prices data came from test files  of corresponding technologies
        self.energy_prices = pd.DataFrame({'years': years,
                                           'electricity': 148.0,
                                           'syngas': 80.0,
                                           'biogas': 70.0,
                                           'methane': 100,
                                           'biomass_dry': 45})

        # the value for invest_level is just set as an order of magnitude
        self.invest_level = pd.DataFrame(
            {'years': years, 'invest': 10.0})
        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [14.86, 17.22, 20.27,
                     29.01,  34.05,   39.08,  44.69,   50.29]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {'years': years, 'CO2_tax': func(years)})
        self.margin = pd.DataFrame(
            {'years': years, 'margin': np.ones(len(years)) * 110.0})
        self.transport = pd.DataFrame(
            {'years': years, 'transport': np.ones(len(years)) * 0})

        self.resources_price = pd.DataFrame(columns=['years', 'CO2', 'water'])
        self.resources_price['years'] = years
        self.resources_price['CO2'] = np.linspace(50.0, 100.0, len(years))
        # biomass_dry price in $/kg
        self.energy_carbon_emissions = pd.DataFrame(
            {'years': years, 'biomass_dry': - 0.64 / 4.86, 'electricity': 0.0, 'methane': 0.0, 'water': 0.0})
        investment_mix = self.get_investments()
        #land_rate = {'land_rate': 5000.0, 'land_rate_unit': '$/Gha', }
        values_dict = {f'{self.study_name}.year_start': self.year_start,
                       f'{self.study_name}.year_end': self.year_end,
                       f'{self.study_name}.{energy_name}.technologies_list': self.technologies_list,
                       f'{self.study_name}.{energy_name}.NaturalGasBoiler.margin': self.margin,
                       f'{self.study_name}.{energy_name}.ElectricBoiler.margin': self.margin,
                       f'{self.study_name}.{energy_name}.HeatPump.margin': self.margin,
                       f'{self.study_name}.{energy_name}.Geothermal.margin': self.margin,
                       f'{self.study_name}.{energy_name}.CHP.margin': self.margin,
                       f'{self.study_name}.{energy_name}.transport_cost': self.transport,
                       f'{self.study_name}.{energy_name}.transport_margin': self.margin,
                       f'{self.study_name}.{energy_name}.invest_techno_mix': investment_mix,
                       # f'{self.study_name}.{energy_name}.ElectricBoiler.flux_input_dict': land_rate,
                       # f'{self.study_name}.{energy_name}.NaturalGasBoiler.flux_input_dict': land_rate,
                       # f'{self.study_name}.{energy_name}.HeatPump.flux_input_dict': land_rate,
                       # f'{self.study_name}.{energy_name}.Geothermal.flux_input_dict': land_rate,
                       }

        if self.main_study:
            values_dict.update(
                {f'{self.study_name}.{energy_mix_name}.energy_prices': self.energy_prices,
                 f'{self.study_name}.CO2_taxes': self.co2_taxes,
                 f'{self.study_name}.{energy_mix_name}.energy_CO2_emissions': self.energy_carbon_emissions,
                 })
            if self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[1]:
                investment_mix_sum = investment_mix.drop(
                    columns=['years']).sum(axis=1)
                for techno in self.technologies_list:
                    invest_level_techno = pd.DataFrame({'years': self.invest_level['years'].values,
                                                        'invest': self.invest_level['invest'].values * investment_mix[techno].values / investment_mix_sum})
                    values_dict[f'{self.study_name}.{energy_name}.{techno}.invest_level'] = invest_level_techno
            else:
                values_dict[f'{self.study_name}.{energy_name}.invest_level'] = self.invest_level
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
