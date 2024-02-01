'''
Copyright 2022 Airbus SAS
Modifications on 2023/09/06-2023/11/16 Copyright 2023 Capgemini

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
from energy_models.core.stream_type.energy_models.fossil import Fossil
from energy_models.database_witness_energy import DatabaseWitnessEnergy
from energy_models.glossaryenergy import GlossaryEnergy

DEFAULT_TECHNOLOGIES_LIST = ['FossilSimpleTechno']
TECHNOLOGIES_LIST = ['FossilSimpleTechno']


class Study(EnergyMixStudyManager):
    def __init__(self, year_start=GlossaryEnergy.YeartStartDefault, year_end=2050, time_step=1,
                 technologies_list=TECHNOLOGIES_LIST,
                 bspline=True, main_study=True, execution_engine=None, invest_discipline=INVEST_DISCIPLINE_DEFAULT):
        super().__init__(__file__, technologies_list=technologies_list,
                         main_study=main_study, execution_engine=execution_engine, invest_discipline=invest_discipline)
        self.year_start = year_start
        self.year_end = year_end
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.energy_name = None
        self.bspline = bspline

    def get_investments(self):
        invest_fossil_mix_dict = {}

        if 'FossilSimpleTechno' in self.technologies_list:
            invest_fossil_mix_dict['FossilSimpleTechno'] = np.ones(GlossaryEnergy.NB_POLES_COARSE) * 1e-6
            invest_fossil_mix_dict['FossilSimpleTechno'][0] = DatabaseWitnessEnergy.InvestFossil2020.value

        if self.bspline:
            invest_fossil_mix_dict[GlossaryEnergy.Years] = self.years

            for techno in self.technologies_list:
                invest_fossil_2020 = DatabaseWitnessEnergy.InvestFossil2020.value
                invest_fossil_mix_dict[techno] = np.linspace(invest_fossil_2020, invest_fossil_2020 / 2,
                                                             len(self.years))

        fossil_mix_invest_df = pd.DataFrame(invest_fossil_mix_dict)

        return fossil_mix_invest_df

    def setup_usecase(self, study_folder_path=None):
        energy_mix_name = 'EnergyMix'
        self.energy_name = Fossil.name
        fossil_name = f'EnergyMix.{self.energy_name}'
        years = np.arange(self.year_start, self.year_end + 1)

        # the value for invest_level is just set as an order of magnitude
        invest_level = pd.DataFrame({GlossaryEnergy.Years: years, GlossaryEnergy.InvestValue: 10.0})

        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [14.86, 17.22, 20.27,
                     29.01, 34.05, 39.08, 44.69, 50.29]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.CO2Tax: func(years)})
        margin = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.MarginValue: np.ones(len(years)) * 110.0})
        # From future of hydrogen
        # It is noteworthy that the cost of transmission has generally been held (and can
        # continue to be held)    within the £10-12/MWhr range despite transmission distances
        # increasing by almost an order of magnitude from an average of 20km for the
        # leftmost bar to 170km for the 2020 scenarios / OWPB 2016

        transport = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'transport': np.zeros(len(years))})
        energy_prices = pd.DataFrame({GlossaryEnergy.Years: years})
        energy_carbon_emissions = pd.DataFrame({GlossaryEnergy.Years: years})

        # define invest mix
        investment_mix = self.get_investments()

        values_dict = {f'{self.study_name}.{GlossaryEnergy.YearStart}': self.year_start,
                       f'{self.study_name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.study_name}.{fossil_name}.{GlossaryEnergy.techno_list}': self.technologies_list,
                       f'{self.study_name}.{fossil_name}.FossilSimpleTechno.{GlossaryEnergy.MarginValue}': margin,

                       f'{self.study_name}.{fossil_name}.{GlossaryEnergy.TransportCostValue}': transport,
                       f'{self.study_name}.{fossil_name}.{GlossaryEnergy.TransportMarginValue}': margin,
                       f'{self.study_name}.{fossil_name}.invest_techno_mix': investment_mix,

                       }

        if self.main_study:
            values_dict.update(
                {f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.EnergyPricesValue}': energy_prices,
                 f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.EnergyCO2EmissionsValue}': energy_carbon_emissions,
                 f'{self.study_name}.{GlossaryEnergy.CO2TaxesValue}': co2_taxes,
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
                        f'{self.study_name}.{fossil_name}.{techno}.{GlossaryEnergy.InvestLevelValue}'] = invest_level_techno
            else:
                values_dict[f'{self.study_name}.{fossil_name}.{GlossaryEnergy.InvestLevelValue}'] = invest_level
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
#         if disc.sos_name == 'Electricity':
#             for graph in graph_list:
#                 graph.to_plotly().show()
