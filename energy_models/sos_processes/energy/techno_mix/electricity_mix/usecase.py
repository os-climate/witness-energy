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
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.glossaryenergy import GlossaryEnergy

DEFAULT_TECHNOLOGIES_LIST = ['WindOffshore', 'WindOnshore', 'SolarPv', 'SolarThermal',
                             'Hydropower', 'Nuclear', 'CombinedCycleGasTurbine', 'GasTurbine', 'BiogasFired',
                             'Geothermal', 'CoalGen', 'OilGen', 'BiomassFired']
TECHNOLOGIES_LIST = ['WindOffshore', 'WindOnshore', 'SolarPv', 'SolarThermal',
                     'Hydropower', 'Nuclear', 'CombinedCycleGasTurbine', 'GasTurbine',
                     'BiogasFired', 'Geothermal', 'CoalGen', 'OilGen', 'BiomassFired']
TECHNOLOGIES_LIST_DEV = ['WindOffshore', 'WindOnshore', 'SolarPv', 'SolarThermal',
                         'Hydropower', 'Nuclear', 'CombinedCycleGasTurbine', 'GasTurbine',
                         'BiogasFired', 'Geothermal', 'CoalGen', 'OilGen', 'BiomassFired']


class Study(EnergyMixStudyManager):
    def __init__(self, year_start=2020, year_end=2050, time_step=1, technologies_list=DEFAULT_TECHNOLOGIES_LIST,
                 bspline=True, main_study=True, execution_engine=None, invest_discipline=INVEST_DISCIPLINE_DEFAULT):
        super().__init__(__file__, technologies_list=technologies_list,
                         main_study=main_study, execution_engine=execution_engine, invest_discipline=invest_discipline)
        self.year_start = year_start
        self.year_end = year_end
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.energy_name = None
        self.bspline = bspline

    def get_investments(self):
        invest_electricity_mix_dict = {}
        l_ctrl = np.arange(0, 8)

        if 'WindOnshore' in self.technologies_list:
            #             invest_electricity_mix_dict['WindOnshore'] = [
            #                 304.4 * 0.00838 + 0.6 * i for i in l_ctrl]
            invest_electricity_mix_dict['WindOnshore'] = np.array([
                304.4 * 0.00838, 0, 0, 0, 0, 0, 0, 0])

        if 'WindOffshore' in self.technologies_list:
            #             invest_electricity_mix_dict['WindOffshore'] = [
            #                 304.4 * 0.00838 + 0.3 * i for i in l_ctrl]
            #             invest_electricity_mix_dict['WindOffshore'] = np.array([
            #                 304.4 * 0.00838, 0, 0, 0, 0, 0, 0, 0])
            invest_electricity_mix_dict['WindOffshore'] = np.array([
                304.4 * 0.00838, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0])

        if 'SolarPv' in self.technologies_list:
            #             invest_electricity_mix_dict['SolarPv'] = [
            #                 5 + 0.3 * i for i in l_ctrl]
            #             invest_electricity_mix_dict['SolarPv'] = np.array([
            #                 5.0, 20, 20, 20, 20, 20, 20, 20])
            invest_electricity_mix_dict['SolarPv'] = np.array([
                5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0])

        if 'SolarThermal' in self.technologies_list:
            #             invest_electricity_mix_dict['SolarThermal'] = [
            #                 304.4 * 0.00456 + i for i in l_ctrl]
            invest_electricity_mix_dict['SolarThermal'] = np.array([
                304.4 * 0.00456, 0, 0, 0, 0, 0, 0, 0])

        if 'Geothermal' in self.technologies_list:
            #             invest_electricity_mix_dict['Geothermal'] = [
            # 304.4 * 0.00081 * (1 + 0.0236)**i for i in l_ctrl]
            #             invest_electricity_mix_dict['Geothermal'] = np.array([
            #                 304.4 * 0.00081, 0, 0, 0, 0, 0, 0, 0])
            invest_electricity_mix_dict['Geothermal'] = np.array([
                304.4 * 0.00081, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0])

        if 'Hydropower' in self.technologies_list:
            #             invest_electricity_mix_dict['Hydropower'] = [
            #                 1.5 + 0.2 * i for i in l_ctrl]
            #             invest_electricity_mix_dict['Hydropower'] = np.array([
            #                 1.5, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0])
            invest_electricity_mix_dict['Hydropower'] = np.array([
                0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2])

        if 'Nuclear' in self.technologies_list:
            #             invest_electricity_mix_dict['Nuclear'] = [
            #                 2.1 + 0.05 * i for i in l_ctrl]
            #             invest_electricity_mix_dict['Nuclear'] = np.array([
            #                 2.1, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5, 7.5])
            invest_electricity_mix_dict['Nuclear'] = np.array([
                2.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

        if 'CombinedCycleGasTurbine' in self.technologies_list:
            #             invest_electricity_mix_dict['CombinedCycleGasTurbine'] = [
            #                 max(0.01, 2.1 - 0.2 * i) for i in l_ctrl]
            invest_electricity_mix_dict['CombinedCycleGasTurbine'] = np.array([
                2.1, 0, 0, 0, 0, 0, 0, 0])

        if 'GasTurbine' in self.technologies_list:
            #             invest_electricity_mix_dict['GasTurbine'] = [
            #                 max(0.01, 0.5 - 0.3 * i) for i in l_ctrl]
            invest_electricity_mix_dict['GasTurbine'] = np.array([
                2.1, 0, 0, 0, 0, 0, 0, 0])

        if 'BiogasFired' in self.technologies_list:
            #             invest_electricity_mix_dict['GasTurbine'] = [
            #                 max(0.01, 0.5 - 0.3 * i) for i in l_ctrl]
            invest_electricity_mix_dict['BiogasFired'] = np.array([
                1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

        if 'BiomassFired' in self.technologies_list:
            #             invest_electricity_mix_dict['GasTurbine'] = [
            #                 max(0.01, 0.5 - 0.3 * i) for i in l_ctrl]
            invest_electricity_mix_dict['BiomassFired'] = np.array([
                1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

        if 'CoalGen' in self.technologies_list:
            #             invest_electricity_mix_dict['CoalGen'] = [
            #                 max(0.01, 0.1 - 0.2 * i) for i in l_ctrl]
            #             invest_electricity_mix_dict['CoalGen'] = np.array([
            #                 0.1, 0, 0, 0, 0, 0, 0, 0])
            invest_electricity_mix_dict['CoalGen'] = np.array([
                0.1, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001])
        if 'OilGen' in self.technologies_list:
            #             invest_electricity_mix_dict['CoalGen'] = [
            #                 max(0.01, 0.1 - 0.2 * i) for i in l_ctrl]
            #             invest_electricity_mix_dict['CoalGen'] = np.array([
            #                 0.1, 0, 0, 0, 0, 0, 0, 0])
            invest_electricity_mix_dict['OilGen'] = np.array([
                0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001])

        if 'RenewableElectricitySimpleTechno' in self.technologies_list:

            invest_electricity_mix_dict['RenewableElectricitySimpleTechno'] = np.array([
                0.1, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001])

        if self.bspline:
            invest_electricity_mix_dict[GlossaryEnergy.Years] = self.years

            for techno in self.technologies_list:
                invest_electricity_mix_dict[techno], _ = self.invest_bspline(
                    invest_electricity_mix_dict[techno], len(self.years))

        electricity_mix_invest_df = pd.DataFrame(invest_electricity_mix_dict)

        return electricity_mix_invest_df

    def setup_usecase(self):
        energy_mix_name = 'EnergyMix'
        self.energy_name = Electricity.name
        electricity_name = f'EnergyMix.{self.energy_name}'
        years = np.arange(self.year_start, self.year_end + 1)

        # reference_data_name = 'Reference_aircraft_data'
        # prices are now in $/MWh
        self.energy_prices = pd.DataFrame({GlossaryEnergy.Years: years, 'electricity': 10.0,
                                           'methane': 60.0,
                                           'biogas': 5.0,
                                           'biomass_dry': 11.0,
                                           'solid_fuel': 5.7,
                                           'fuel.liquid_fuel': 40,
                                           })

        #  IRENA invest data - Future of wind 2019
        self.energy_carbon_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'solid_fuel': 0.64 / 4.86, 'electricity': 0.0, 'methane': 0.123 / 15.4,
             'biogas': 0.123 / 15.4, 'biomass_dry': - 0.64 / 4.86, 'syngas': 0.0, 'hydrogen.gaseous_hydrogen': 0.0,
             'fuel.liquid_fuel': 0.64 / 4.86, 'heat.hightemperatureheat': 0.56 / 3.18, 'heat.mediumtemperatureheat': 0.42 / 2.48, 'heat.lowtemperatureheat': 0.52 / 2.24
             })

        # the value for invest_level is just set as an order of magnitude
        self.invest_level = pd.DataFrame({GlossaryEnergy.Years: years, GlossaryEnergy.InvestValue: 10.0})

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
        transport_cost = 11.0,  # $/MWh
        # It is noteworthy that the cost of transmission has generally been held (and can
        # continue to be held)    within the £10-12/MWhr range despite transmission distances
        # increasing by almost an order of magnitude from an average of 20km for the
        # leftmost bar to 170km for the 2020 scenarios / OWPB 2016

        self.transport_offshore = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'transport': np.ones(len(years)) * transport_cost})

        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'transport': np.zeros(len(years))})

        # define invest mix
        investment_mix = self.get_investments()

        values_dict = {f'{self.study_name}.{GlossaryEnergy.YearStart}': self.year_start,
                       f'{self.study_name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.study_name}.{electricity_name}.{GlossaryEnergy.techno_list}': self.technologies_list,
                       f'{self.study_name}.{electricity_name}.WindOffshore.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.study_name}.{electricity_name}.WindOffshore.{GlossaryEnergy.TransportCostValue}': self.transport_offshore,
                       f'{self.study_name}.{electricity_name}.WindOnshore.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.study_name}.{electricity_name}.SolarPv.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.study_name}.{electricity_name}.SolarThermal.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.study_name}.{electricity_name}.Hydropower.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.study_name}.{electricity_name}.Nuclear.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.study_name}.{electricity_name}.CombinedCycleGasTurbine.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.study_name}.{electricity_name}.GasTurbine.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.study_name}.{electricity_name}.BiogasFired.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.study_name}.{electricity_name}.BiomassFired.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.study_name}.{electricity_name}.Geothermal.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.study_name}.{electricity_name}.CoalGen.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.study_name}.{electricity_name}.RenewableElectricitySimpleTechno.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.study_name}.{electricity_name}.OilGen.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.study_name}.{electricity_name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.study_name}.{electricity_name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.study_name}.{electricity_name}.invest_techno_mix': investment_mix,

                       }

        if self.main_study:

            values_dict.update(
                {f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.EnergyPricesValue}': self.energy_prices,
                 f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.EnergyCO2EmissionsValue}': self.energy_carbon_emissions,
                 f'{self.study_name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                 })
            if self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[1]:
                investment_mix_sum = investment_mix.drop(
                    columns=[GlossaryEnergy.Years]).sum(axis=1)
                for techno in self.technologies_list:
                    invest_level_techno = pd.DataFrame({GlossaryEnergy.Years: self.invest_level[GlossaryEnergy.Years].values,
                                                        GlossaryEnergy.InvestValue: self.invest_level[GlossaryEnergy.InvestValue].values * investment_mix[techno].values / investment_mix_sum})
                    values_dict[f'{self.study_name}.{electricity_name}.{techno}.{GlossaryEnergy.InvestLevelValue}'] = invest_level_techno
            else:
                values_dict[f'{self.study_name}.{electricity_name}.{GlossaryEnergy.InvestLevelValue}'] = self.invest_level
        else:
            self.update_dv_arrays()

        return [values_dict]


if '__main__' == __name__:
    uc_cls = Study(main_study=True,
                   technologies_list=DEFAULT_TECHNOLOGIES_LIST)
    uc_cls.test()
