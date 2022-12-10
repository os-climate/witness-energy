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

from energy_models.core.stream_type.carbon_models.carbon_storage import CarbonStorage
from energy_models.core.energy_mix_study_manager import EnergyMixStudyManager
from energy_models.core.energy_process_builder import INVEST_DISCIPLINE_DEFAULT, INVEST_DISCIPLINE_OPTIONS


DEFAULT_TECHNOLOGIES_LIST = ['BiomassBuryingFossilization', 'DeepOceanInjection', 'DeepSalineFormation',
                             'DepletedOilGas', 'EnhancedOilRecovery', 'GeologicMineralization',
                             'PureCarbonSolidStorage']
TECHNOLOGIES_LIST = ['BiomassBuryingFossilization', 'DeepOceanInjection', 'DeepSalineFormation',
                     'DepletedOilGas', 'EnhancedOilRecovery', 'GeologicMineralization',
                     'PureCarbonSolidStorage']
TECHNOLOGIES_LIST_DEV = ['BiomassBuryingFossilization', 'DeepOceanInjection', 'DeepSalineFormation',
                         'DepletedOilGas', 'EnhancedOilRecovery', 'GeologicMineralization',
                         'PureCarbonSolidStorage']


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
        invest_carbon_storage_mix_dict = {}
        #invest_carbon_storage_mix_dict['years'] = self.years
        l_ctrl = np.arange(0, 8)

        if 'BiomassBuryingFossilization' in self.technologies_list:
            invest_carbon_storage_mix_dict['BiomassBuryingFossilization'] = [
                5 * (1 + 0.03) ** i for i in l_ctrl]

        if 'DeepOceanInjection' in self.technologies_list:
            invest_carbon_storage_mix_dict['DeepOceanInjection'] = [
                10 * (1 + 0.03) ** i for i in l_ctrl]

        if 'DeepSalineFormation' in self.technologies_list:
            invest_carbon_storage_mix_dict['DeepSalineFormation'] = [
                10 * (1 - 0.04) ** i for i in l_ctrl]

        if 'DepletedOilGas' in self.technologies_list:
            invest_carbon_storage_mix_dict['DepletedOilGas'] = [
                10 * (1 - 0.04) ** i for i in l_ctrl]

        if 'EnhancedOilRecovery' in self.technologies_list:
            invest_carbon_storage_mix_dict['EnhancedOilRecovery'] = [
                1 * (1 + 0.0) ** i for i in l_ctrl]

        if 'GeologicMineralization' in self.technologies_list:
            invest_carbon_storage_mix_dict['GeologicMineralization'] = [
                2 * (1 + 0.0) ** i for i in l_ctrl]

        if 'PureCarbonSolidStorage' in self.technologies_list:
            invest_carbon_storage_mix_dict['PureCarbonSolidStorage'] = [
                5 * (1 + 0.0) ** i for i in l_ctrl]

        if 'CarbonStorageTechno' in self.technologies_list:
            invest_carbon_storage_mix_dict['CarbonStorageTechno'] = [
                10 * (1 + 0.03) ** i for i in np.arange(0, 16)]
        if self.bspline:
            invest_carbon_storage_mix_dict['years'] = self.years

            for techno in self.technologies_list:
                invest_carbon_storage_mix_dict[techno], _ = self.invest_bspline(
                    invest_carbon_storage_mix_dict[techno], len(self.years))

        carbon_storage_mix_invest_df = pd.DataFrame(
            invest_carbon_storage_mix_dict)

        return carbon_storage_mix_invest_df

    def setup_usecase(self):
        energy_mix_name = 'EnergyMix'
        self.energy_name = CarbonStorage.name
        ccs_name = f'{self.prefix_name}.{self.energy_name}'

        years = np.arange(self.year_start, self.year_end + 1)
        # reference_data_name = 'Reference_aircraft_data'
        self.energy_prices = pd.DataFrame({'years': years,
                                           'electricity': 10.0
                                           })

        # the value for invest_level is just set as an order of magnitude
        self.invest_level = pd.DataFrame(
            {'years': years, 'invest': 10.0})

        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [0.01486, 0.01722, 0.02027,
                     0.02901,  0.03405,   0.03908,  0.04469,   0.05029]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {'years': years, 'CO2_tax': func(years)})
        self.margin = pd.DataFrame(
            {'years': years, 'margin': np.ones(len(years)) * 110.0})
        # From future of hydrogen
        self.transport = pd.DataFrame(
            {'years': years, 'transport': np.ones(len(years)) * 0.0})
        self.energy_carbon_emissions = pd.DataFrame(
            {'years': years, 'electricity': 0.0, })
        investment_mix = self.get_investments()

        values_dict = {f'{self.study_name}.year_start': self.year_start,
                       f'{self.study_name}.year_end': self.year_end,
                       f'{self.study_name}.{ccs_name}.technologies_list': self.technologies_list,
                       f'{self.study_name}.{ccs_name}.transport_cost': self.transport,
                       f'{self.study_name}.{ccs_name}.transport_margin': self.margin,
                       f'{self.study_name}.{ccs_name}.invest_techno_mix': investment_mix,
                       }
        techno_margin_dict = {
            f'{self.study_name}.{ccs_name}.{techno}.margin': self.margin for techno in self.technologies_list}
        values_dict.update(techno_margin_dict)
        if self.main_study:
            values_dict.update(
                {f'{self.study_name}.{energy_mix_name}.energy_CO2_emissions': self.energy_carbon_emissions,
                    f'{self.study_name}.{energy_mix_name}.energy_prices': self.energy_prices,
                    f'{self.study_name}.CO2_taxes': self.co2_taxes,
                 })
            if self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[1]:
                investment_mix_sum = investment_mix.drop(
                    columns=['years']).sum(axis=1)
                for techno in self.technologies_list:
                    invest_level_techno = pd.DataFrame({'years': self.invest_level['years'].values,
                                                        'invest': self.invest_level['invest'].values * investment_mix[techno].values / investment_mix_sum})
                    values_dict[f'{self.study_name}.{ccs_name}.{techno}.invest_level'] = invest_level_techno
            else:
                values_dict[f'{self.study_name}.{ccs_name}.invest_level'] = self.invest_level
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
