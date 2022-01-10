'''
Copyright 2022 Airbus SAS

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

from energy_models.core.stream_type.energy_models.biogas import BioGas
from energy_models.core.energy_mix_study_manager import EnergyMixStudyManager

DEFAULT_TECHNOLOGIES_LIST = ['AnaerobicDigestion']
TECHNOLOGIES_LIST_FOR_OPT = ['AnaerobicDigestion']


class Study(EnergyMixStudyManager):
    def __init__(self, year_start=2020, year_end=2050, time_step=1, technologies_list=DEFAULT_TECHNOLOGIES_LIST,
                 bspline=True,  main_study=True, execution_engine=None, one_invest_discipline=False):
        super().__init__(__file__, technologies_list=technologies_list,
                         main_study=main_study, execution_engine=execution_engine, one_invest_discipline=one_invest_discipline)
        self.year_start = year_start
        self.year_end = year_end
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.energy_name = None
        self.bspline = bspline

    def get_investments(self):
        invest_biogas_mix_dict = {}
        l_ctrl = np.arange(0, 8)

        if 'AnaerobicDigestion' in self.technologies_list:
            invest_biogas_mix_dict['AnaerobicDigestion'] = np.ones(
                len(l_ctrl))
        if self.bspline:
            invest_biogas_mix_dict['years'] = self.years

            for techno in self.technologies_list:
                invest_biogas_mix_dict[techno], _ = self.invest_bspline(
                    invest_biogas_mix_dict[techno], len(self.years))

        biogas_mix_invest_df = pd.DataFrame(invest_biogas_mix_dict)

        return biogas_mix_invest_df

    def setup_usecase(self):
        energy_mix = 'EnergyMix'
        self.energy_name = BioGas.name
        energy_name = f'{energy_mix}.{BioGas.name}'

        years = np.arange(self.year_start, self.year_end + 1)
        self.energy_prices = pd.DataFrame({'years': years,
                                           'electricity': 16.0,
                                           'syngas': 80.0,
                                           'biomass_dry': 10.0})

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
            {'years': years, 'margin': 110.0})
        # From future of hydrogen
        self.transport = pd.DataFrame(
            {'years': years, 'transport': 200.0})

        self.ressources_price = pd.DataFrame(columns=['years', 'CO2', 'water'])
        self.ressources_price['years'] = years
        self.ressources_price['CO2'] = np.linspace(50.0, 100.0, len(years))
        # biomass_dry price in $/kg
        self.energy_carbon_emissions = pd.DataFrame(
            {'years': years, 'biomass_dry': - 0.64 / 4.86, 'biogas': - 0.05, 'solid_fuel': 0.64 / 4.86, 'electricity': 0.0, 'methane': 0.123 / 15.4, 'syngas': 0.0, 'hydrogen.gaseous_hydrogen': 0.0, 'crude oil': 0.02533})
        # define invest mix
        investment_mix = self.get_investments()

        values_dict = {f'{self.study_name}.year_start': self.year_start,
                       f'{self.study_name}.year_end': self.year_end,
                       f'{self.study_name}.{energy_name}.technologies_list': self.technologies_list,
                       f'{self.study_name}.EnergyMix.syngas_ratio': np.ones(len(years)) * 0.5,
                       f'{self.study_name}.{energy_name}.AnaerobicDigestion.invest_level': self.invest_level,
                       f'{self.study_name}.{energy_name}.AnaerobicDigestion.margin': self.margin,
                       f'{self.study_name}.{energy_name}.transport_cost': self.transport,
                       f'{self.study_name}.{energy_name}.transport_margin': self.margin,
                       f'{self.study_name}.{energy_name}.invest_techno_mix': investment_mix,
                       }
        if self.main_study:
            values_dict.update(
                {f'{self.study_name}.CO2_taxes': self.co2_taxes,
                 f'{self.study_name}.{energy_mix}.energy_CO2_emissions': self.energy_carbon_emissions,
                 f'{self.study_name}.{energy_mix}.energy_prices': self.energy_prices,
                 })
            if self.one_invest_discipline:
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
