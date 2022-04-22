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

from sos_trades_core.tools.post_processing.post_processing_factory import PostProcessingFactory
from energy_models.core.energy_mix_study_manager import EnergyMixStudyManager
from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
from energy_models.core.energy_process_builder import INVEST_DISCIPLINE_OPTIONS,\
    INVEST_DISCIPLINE_DEFAULT

DEFAULT_TECHNOLOGIES_LIST = ['ManagedWood', 'UnmanagedWood', 'CropEnergy']
TECHNOLOGIES_LIST = ['ManagedWood', 'UnmanagedWood', 'CropEnergy']
TECHNOLOGIES_LIST_DEV = []


class Study(EnergyMixStudyManager):
    def __init__(self, year_start=2020, year_end=2050, time_step=1, technologies_list=TECHNOLOGIES_LIST,
                 bspline=True, main_study=True, execution_engine=None, invest_discipline=INVEST_DISCIPLINE_DEFAULT):
        super().__init__(__file__, technologies_list=technologies_list,
                         main_study=main_study, execution_engine=execution_engine, invest_discipline=invest_discipline)
        self.year_start = year_start
        self.year_end = year_end
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.energy_name = None
        self.bspline = bspline

    def get_investments(self):
        invest_biomass_dry_mix_dict = {}
        l_ctrl = np.arange(0, 8)

        if 'ManagedWood' in self.technologies_list:
            invest_biomass_dry_mix_dict['ManagedWood'] = [
                (1 + 0.03)**i for i in l_ctrl]

        if 'UnmanagedWood' in self.technologies_list:
            invest_biomass_dry_mix_dict['UnmanagedWood'] = [
                (1 - 0.04)**i for i in l_ctrl]

        if 'CropEnergy' in self.technologies_list:
            #             invest_biomass_dry_mix_dict['CropEnergy'] = [
            #                 (1 + 0.0)**i for i in l_ctrl]
            invest_biomass_dry_mix_dict['CropEnergy'] = np.array([
                1.0, 1.0, 0.8, 0.6, 0.4, 0.4, 0.4, 0.4])

        if self.bspline:
            invest_biomass_dry_mix_dict['years'] = self.years

            for techno in self.technologies_list:
                invest_biomass_dry_mix_dict[techno], _ = self.invest_bspline(
                    invest_biomass_dry_mix_dict[techno], len(self.years))

        biomass_dry_mix_invest_df = pd.DataFrame(invest_biomass_dry_mix_dict)

        return biomass_dry_mix_invest_df

    def setup_usecase(self):
        energy_mix = 'EnergyMix'
        self.energy_name = BiomassDry.name
        energy_name = f'{energy_mix}.{self.energy_name}'
        years = np.arange(self.year_start, self.year_end + 1)
        # reference_data_name = 'Reference_aircraft_data'
        self.energy_prices = pd.DataFrame({'years': years,
                                           'electricity': 16.0})

        # We use the IEA H2 demand to fake the invest level through years

        # the value for invest_level is just set as an order of magnitude
        self.invest_level = pd.DataFrame(
            {'years': years, 'invest': 1e4})

        land_surface_for_food = pd.DataFrame({'years': years,
                                              'Agriculture total (Gha)': np.ones(len(years)) * 4.8})

        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [14.86, 17.22, 20.27,
                     29.01,  34.05,   39.08,  44.69,   50.29]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {'years': years, 'CO2_tax': func(years)})
        self.margin = pd.DataFrame(
            {'years': years, 'margin': np.ones(len(years)) * 110.0})
        # From future of hydrogen
        self.transport = pd.DataFrame(
            {'years': years, 'transport': np.ones(len(years)) * 7.6})

        self.resources_price = pd.DataFrame(columns=['years', 'CO2', 'water'])
        self.resources_price['years'] = years
        self.resources_price['CO2'] = np.linspace(
            50.0, 100.0, len(years))         # biomass_dry price in $/kg
        self.energy_carbon_emissions = pd.DataFrame(
            {'years': years, 'biomass_dry': - 0.64 / 4.86, 'solid_fuel': 0.64 / 4.86, 'electricity': 0.0, 'methane': 0.123 / 15.4, 'syngas': 0.0, 'hydrogen.gaseous_hydrogen': 0.0, 'crude oil': 0.02533})

        # define invest mix
        investment_mix = self.get_investments()

        values_dict = {f'{self.study_name}.year_start': self.year_start,
                       f'{self.study_name}.year_end': self.year_end,
                       f'{self.study_name}.{energy_name}.technologies_list': self.technologies_list,
                       f'{self.study_name}.{energy_name}.ManagedWood.margin': self.margin,
                       f'{self.study_name}.{energy_name}.UnmanagedWood.margin': self.margin,
                       f'{self.study_name}.{energy_name}.CropEnergy.margin': self.margin,
                       f'{self.study_name}.{energy_name}.transport_cost': self.transport,
                       f'{self.study_name}.{energy_name}.transport_margin': self.margin,
                       f'{self.study_name}.{energy_name}.invest_techno_mix': investment_mix,
                       }
        if self.main_study:
            values_dict.update(
                {f'{self.study_name}.land_surface_for_food_df': land_surface_for_food,
                 f'{self.study_name}.CO2_taxes': self.co2_taxes,
                 f'{self.study_name}.{energy_mix}.energy_CO2_emissions': self.energy_carbon_emissions,
                 f'{self.study_name}.{energy_mix}.energy_prices': self.energy_prices,
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
    uc_cls = Study(main_study=True,
                   technologies_list=DEFAULT_TECHNOLOGIES_LIST)
    uc_cls.load_data()
    uc_cls.run()
    ppf = PostProcessingFactory()
    for disc in uc_cls.execution_engine.root_process.sos_disciplines:
        filters = ppf.get_post_processing_filters_by_discipline(
            disc)
        graph_list = ppf.get_post_processing_by_discipline(
            disc, filters, as_json=False)

        for graph in graph_list:
            graph.to_plotly().show()
