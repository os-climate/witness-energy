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
from energy_models.core.energy_process_builder import (
    INVEST_DISCIPLINE_DEFAULT,
    INVEST_DISCIPLINE_OPTIONS,
)
from energy_models.database_witness_energy import DatabaseWitnessEnergy
from energy_models.glossaryenergy import GlossaryEnergy


class Study(EnergyMixStudyManager):
    def __init__(self, year_start=GlossaryEnergy.YearStartDefault, year_end=GlossaryEnergy.YearEndDefault,
                 technologies_list=GlossaryEnergy.DEFAULT_TECHNO_DICT[GlossaryEnergy.carbon_storage]["value"],
                 bspline=True, main_study=True, prefix_name=None, execution_engine=None,
                 invest_discipline=INVEST_DISCIPLINE_DEFAULT):
        super().__init__(__file__, technologies_list=technologies_list,
                         main_study=main_study, execution_engine=execution_engine, invest_discipline=invest_discipline)
        self.year_start = year_start
        self.year_end = year_end
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.stream_name = None
        self.bspline = bspline
        self.prefix_name = 'EnergyMix'
        if prefix_name is not None:
            self.prefix_name = prefix_name

    def get_investments(self):
        invest_carbon_storage_mix_dict = {}

        l_ctrl = np.arange(GlossaryEnergy.NB_POLES_FULL)

        if GlossaryEnergy.BiomassBuryingFossilization in self.technologies_list:
            invest_carbon_storage_mix_dict[GlossaryEnergy.BiomassBuryingFossilization] = [
                5 * (1 + 0.03) ** i for i in l_ctrl]

        if GlossaryEnergy.DeepOceanInjection in self.technologies_list:
            invest_carbon_storage_mix_dict[GlossaryEnergy.DeepOceanInjection] = [
                10 * (1 + 0.03) ** i for i in l_ctrl]

        if GlossaryEnergy.DeepSalineFormation in self.technologies_list:
            invest_carbon_storage_mix_dict[GlossaryEnergy.DeepSalineFormation] = [
                10 * (1 - 0.04) ** i for i in l_ctrl]

        if GlossaryEnergy.DepletedOilGas in self.technologies_list:
            invest_carbon_storage_mix_dict[GlossaryEnergy.DepletedOilGas] = [
                10 * (1 - 0.04) ** i for i in l_ctrl]

        if GlossaryEnergy.EnhancedOilRecovery in self.technologies_list:
            invest_carbon_storage_mix_dict[GlossaryEnergy.EnhancedOilRecovery] = [
                1 * (1 + 0.0) ** i for i in l_ctrl]

        if GlossaryEnergy.GeologicMineralization in self.technologies_list:
            invest_carbon_storage_mix_dict[GlossaryEnergy.GeologicMineralization] = [
                2 * (1 + 0.0) ** i for i in l_ctrl]

        if GlossaryEnergy.PureCarbonSolidStorage in self.technologies_list:
            invest_carbon_storage_mix_dict[GlossaryEnergy.PureCarbonSolidStorage] = [
                5 * (1 + 0.0) ** i for i in l_ctrl]

        if GlossaryEnergy.CarbonStorageTechno in self.technologies_list:
            invest_carbon_storage_mix_dict[GlossaryEnergy.CarbonStorageTechno] = np.ones(GlossaryEnergy.NB_POLES_COARSE) * 1e-6
            invest_2020_ccus = DatabaseWitnessEnergy.InvestCCUS2020.value
            invest_carbon_storage_mix_dict[GlossaryEnergy.CarbonStorageTechno][0] = invest_2020_ccus / 3.

        if GlossaryEnergy.Reforestation in self.technologies_list:
            invest_carbon_storage_mix_dict[GlossaryEnergy.Reforestation] = [
                5 * (1 + 0.0) ** i for i in l_ctrl]

        if self.bspline:
            invest_carbon_storage_mix_dict[GlossaryEnergy.Years] = self.years

            for techno in self.technologies_list:
                invest_carbon_storage_mix_dict[techno], _ = self.invest_bspline(
                    invest_carbon_storage_mix_dict[techno], len(self.years))

        carbon_storage_mix_invest_df = pd.DataFrame(
            invest_carbon_storage_mix_dict)

        return carbon_storage_mix_invest_df

    def setup_usecase(self, study_folder_path=None):
        energy_mix_name = 'EnergyMix'
        self.stream_name = GlossaryEnergy.carbon_storage
        ccs_name = f'{self.prefix_name}.{self.stream_name}'

        years = np.arange(self.year_start, self.year_end + 1)
        # reference_data_name = 'Reference_aircraft_data'
        energy_prices = pd.DataFrame({GlossaryEnergy.Years: years,
                                      GlossaryEnergy.electricity: 10.,
                                      GlossaryEnergy.biomass_dry: 11.,
                                      GlossaryEnergy.carbon_capture: 70.,
                                      })

        # the value for invest_level is just set as an order of magnitude
        invest_level = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.InvestValue: 10.0})

        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [0.01486, 0.01722, 0.02027,
                     0.02901, 0.03405, 0.03908, 0.04469, 0.05029]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.CO2Tax: func(years)})
        margin = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.MarginValue: np.ones(len(years)) * 110.0})
        # From future of hydrogen
        transport = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'transport': np.ones(len(years)) * 0.0})
        energy_carbon_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.electricity: 0.0,
             GlossaryEnergy.biomass_dry: - 0.64 / 4.86, GlossaryEnergy.carbon_capture: 0.})
        investment_mix = self.get_investments()

        values_dict = {f'{self.study_name}.{GlossaryEnergy.YearStart}': self.year_start,
                       f'{self.study_name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.study_name}.{ccs_name}.{GlossaryEnergy.techno_list}': self.technologies_list,
                       f'{self.study_name}.{ccs_name}.{GlossaryEnergy.TransportCostValue}': transport,
                       f'{self.study_name}.{ccs_name}.{GlossaryEnergy.TransportMarginValue}': margin,
                       #f'{self.study_name}.{ccs_name}.invest_techno_mix': investment_mix,
                       }
        techno_margin_dict = {
            f'{self.study_name}.{ccs_name}.{techno}.{GlossaryEnergy.MarginValue}': margin for techno in
            self.technologies_list}
        values_dict.update(techno_margin_dict)
        if self.main_study:
            values_dict.update(
                {
                    f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': energy_carbon_emissions,
                    f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.StreamPricesValue}': energy_prices,
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
                        f'{self.study_name}.{ccs_name}.{techno}.{GlossaryEnergy.InvestLevelValue}'] = invest_level_techno
            else:
                values_dict[f'{self.study_name}.{ccs_name}.{GlossaryEnergy.InvestLevelValue}'] = invest_level
        else:

            self.update_dv_arrays()

        return [values_dict]


if '__main__' == __name__:
    uc_cls = Study(main_study=True)
    uc_cls.test()