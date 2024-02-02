'''
Copyright 2022 Airbus SAS
Modifications on 2023/10/23-2023/11/16 Copyright 2023 Capgemini

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
from energy_models.core.stream_type.energy_models.syngas import Syngas
from energy_models.glossaryenergy import GlossaryEnergy

DEFAULT_TECHNOLOGIES_LIST = ['BiomassGasification', 'SMR',
                             'CoalGasification', 'Pyrolysis', 'AutothermalReforming', 'CoElectrolysis']
TECHNOLOGIES_LIST = ['BiomassGasification', 'SMR', 'CoalGasification', 'Pyrolysis', 'AutothermalReforming',
                     'CoElectrolysis']
TECHNOLOGIES_LIST_DEV = ['BiomassGasification', 'SMR', 'CoalGasification', 'Pyrolysis', 'AutothermalReforming',
                         'CoElectrolysis']


class Study(EnergyMixStudyManager):
    def __init__(self, year_start=GlossaryEnergy.YeartStartDefault, year_end=2050,
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
        invest_syngas_mix_dict = {}
        l_ctrl = np.arange(GlossaryEnergy.NB_POLES_FULL)

        if 'BiomassGasification' in self.technologies_list:
            invest_syngas_mix_dict['BiomassGasification'] = [
                0.5 * (1 + 0.06) ** i for i in l_ctrl]

        if 'SMR' in self.technologies_list:
            invest_syngas_mix_dict['SMR'] = [
                10 * (1 - 0.04) ** i for i in l_ctrl]

        if 'Pyrolysis' in self.technologies_list:
            invest_syngas_mix_dict['Pyrolysis'] = [
                0.1 * (1 - 0.03) ** i for i in l_ctrl]

        if 'AutothermalReforming' in self.technologies_list:
            invest_syngas_mix_dict['AutothermalReforming'] = [
                0.001 * (1 - 0.04) ** i for i in l_ctrl]

        if 'CoElectrolysis' in self.technologies_list:
            invest_syngas_mix_dict['CoElectrolysis'] = [
                0.01 * (1 - 0.04) ** i for i in l_ctrl]

        if 'CoalGasification' in self.technologies_list:
            invest_syngas_mix_dict['CoalGasification'] = [
                0.5 * (1 - 0.03) ** i for i in l_ctrl]

        if self.bspline:

            invest_syngas_mix_dict[GlossaryEnergy.Years] = self.years

            for techno in self.technologies_list:
                invest_syngas_mix_dict[techno], _ = self.invest_bspline(
                    invest_syngas_mix_dict[techno], len(self.years))

        syngas_mix_invest_df = pd.DataFrame(invest_syngas_mix_dict)

        return syngas_mix_invest_df

    def setup_usecase(self, study_folder_path=None):
        energy_mix_name = 'EnergyMix'
        self.energy_name = Syngas.name

        energy_name = f'{energy_mix_name}.{self.energy_name}'
        years = np.arange(self.year_start, self.year_end + 1)
        # reference_data_name = 'Reference_aircraft_data'
        energy_prices = pd.DataFrame({GlossaryEnergy.Years: years, GlossaryEnergy.electricity: 16.0,
                                      GlossaryEnergy.methane: 80.0,
                                      GlossaryEnergy.biomass_dry: 50.0,
                                      GlossaryEnergy.solid_fuel: 50.0})

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
            {GlossaryEnergy.Years: years, GlossaryEnergy.MarginValue: np.ones(len(years)) * 100.0})
        # From future of hydrogen
        transport = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'transport': np.ones(len(years)) * 0.0})

        resources_price = pd.DataFrame(columns=[GlossaryEnergy.Years, 'CO2', 'water'])
        resources_price[GlossaryEnergy.Years] = years
        resources_price['CO2'] = np.linspace(
            50.0, 100.0, len(years))  # biomass_dry price in $/kg
        energy_carbon_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.biomass_dry: - 0.64 / 4.86, GlossaryEnergy.solid_fuel: 0.64 / 4.86, GlossaryEnergy.electricity: 0.0,
             GlossaryEnergy.methane: 0.123 / 15.4, GlossaryEnergy.syngas: 0.0, f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}': 0.0, 'crude oil': 0.02533})

        # define invest mix
        investment_mix = self.get_investments()
        technologies_list = self.technologies_list
        values_dict = {f'{self.study_name}.{GlossaryEnergy.YearStart}': self.year_start,
                       f'{self.study_name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.study_name}.{energy_name}.{GlossaryEnergy.techno_list}': technologies_list,
                       f'{self.study_name}.{energy_name}.BiomassGasification.{GlossaryEnergy.MarginValue}': margin,
                       f'{self.study_name}.{energy_name}.SMR.{GlossaryEnergy.MarginValue}': margin,
                       f'{self.study_name}.{energy_name}.Pyrolysis.{GlossaryEnergy.MarginValue}': margin,
                       f'{self.study_name}.{energy_name}.CoalGasification.{GlossaryEnergy.MarginValue}': margin,
                       f'{self.study_name}.{energy_name}.AutothermalReforming.{GlossaryEnergy.MarginValue}': margin,
                       f'{self.study_name}.{energy_name}.CoElectrolysis.{GlossaryEnergy.MarginValue}': margin,
                       f'{self.study_name}.{energy_name}.{GlossaryEnergy.TransportCostValue}': transport,
                       f'{self.study_name}.{energy_name}.{GlossaryEnergy.TransportMarginValue}': margin,
                       f'{self.study_name}.{energy_name}.invest_techno_mix': investment_mix,
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
                        f'{self.study_name}.{energy_name}.{techno}.{GlossaryEnergy.InvestLevelValue}'] = invest_level_techno
            else:
                values_dict[f'{self.study_name}.{energy_name}.{GlossaryEnergy.InvestLevelValue}'] = invest_level
        else:
            self.update_dv_arrays()

        return [values_dict]


if '__main__' == __name__:
    uc_cls = Study(main_study=True,
                   technologies_list=TECHNOLOGIES_LIST)
    uc_cls.test()
