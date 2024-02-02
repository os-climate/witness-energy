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
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.carbon_models.flue_gas import FlueGas
from energy_models.database_witness_energy import DatabaseWitnessEnergy
from energy_models.glossaryenergy import GlossaryEnergy

DEFAULT_TECHNOLOGIES_LIST = [f'{GlossaryEnergy.direct_air_capture}.AmineScrubbing', f'{GlossaryEnergy.direct_air_capture}.CalciumPotassiumScrubbing',
                             f'{GlossaryEnergy.flue_gas_capture}.CalciumLooping', f'{GlossaryEnergy.flue_gas_capture}.ChilledAmmoniaProcess',
                             f'{GlossaryEnergy.flue_gas_capture}.CO2Membranes', f'{GlossaryEnergy.flue_gas_capture}.MonoEthanolAmine',
                             f'{GlossaryEnergy.flue_gas_capture}.PiperazineProcess', f'{GlossaryEnergy.flue_gas_capture}.PressureSwingAdsorption']
TECHNOLOGIES_LIST = [f'{GlossaryEnergy.direct_air_capture}.AmineScrubbing', f'{GlossaryEnergy.direct_air_capture}.CalciumPotassiumScrubbing',
                     f'{GlossaryEnergy.flue_gas_capture}.CalciumLooping', f'{GlossaryEnergy.flue_gas_capture}.ChilledAmmoniaProcess',
                     f'{GlossaryEnergy.flue_gas_capture}.CO2Membranes', f'{GlossaryEnergy.flue_gas_capture}.MonoEthanolAmine',
                     f'{GlossaryEnergy.flue_gas_capture}.PiperazineProcess', f'{GlossaryEnergy.flue_gas_capture}.PressureSwingAdsorption']
TECHNOLOGIES_LIST_COARSE = [f'{GlossaryEnergy.direct_air_capture}.CalciumPotassiumScrubbing', f'{GlossaryEnergy.flue_gas_capture}.CalciumLooping']

TECHNOLOGIES_FLUE_GAS_LIST_COARSE = [f'{GlossaryEnergy.electricity}.GasTurbine']
DEFAULT_FLUE_GAS_LIST = [f'{GlossaryEnergy.electricity}.CoalGen', f'{GlossaryEnergy.electricity}.GasTurbine', f'{GlossaryEnergy.electricity}.CombinedCycleGasTurbine',
                         f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.WaterGasShift', f'{GlossaryEnergy.liquid_fuel}.FischerTropsch',
                         f'{GlossaryEnergy.liquid_fuel}.Refinery', f'{GlossaryEnergy.methane}.FossilGas',
                         f'{GlossaryEnergy.solid_fuel}.Pelletizing', f'{GlossaryEnergy.syngas}.CoalGasification', f'{GlossaryEnergy.fossil}.FossilSimpleTechno',
                         f'{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.direct_air_capture}.AmineScrubbing',
                         f'{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.direct_air_capture}.CalciumPotassiumScrubbing',
                         f'{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.direct_air_capture}.DirectAirCaptureTechno']
TECHNOLOGIES_LIST_DEV = [f'{GlossaryEnergy.direct_air_capture}.AmineScrubbing', f'{GlossaryEnergy.direct_air_capture}.CalciumPotassiumScrubbing',
                         f'{GlossaryEnergy.flue_gas_capture}.CalciumLooping', f'{GlossaryEnergy.flue_gas_capture}.ChilledAmmoniaProcess',
                         f'{GlossaryEnergy.flue_gas_capture}.CO2Membranes', f'{GlossaryEnergy.flue_gas_capture}.MonoEthanolAmine',
                         f'{GlossaryEnergy.flue_gas_capture}.PiperazineProcess', f'{GlossaryEnergy.flue_gas_capture}.PressureSwingAdsorption']


class Study(EnergyMixStudyManager):
    def __init__(self, year_start=GlossaryEnergy.YeartStartDefault, year_end=2050,
                 technologies_list=TECHNOLOGIES_LIST,
                 bspline=True, main_study=True, prefix_name=None, execution_engine=None,
                 invest_discipline=INVEST_DISCIPLINE_DEFAULT):
        super().__init__(__file__, technologies_list=technologies_list,
                         main_study=main_study, execution_engine=execution_engine, invest_discipline=invest_discipline)
        self.flue_gas_mean = None
        self.techno_capital = None
        self.year_start = year_start
        self.year_end = year_end
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.energy_name = None
        self.bspline = bspline
        self.prefix_name = 'EnergyMix'
        if prefix_name is not None:
            self.prefix_name = prefix_name

    def get_investments(self):
        invest_carbon_capture_mix_dict = {}
        l_ctrl = np.arange(GlossaryEnergy.NB_POLES_FULL)

        if f'{GlossaryEnergy.direct_air_capture}.AmineScrubbing' in self.technologies_list:
            #             invest_carbon_capture_mix_dict[f'{GlossaryEnergy.direct_air_capture}.AmineScrubbing'] = [
            #                 0.5 * (1 + 0.03) ** i for i in l_ctrl]
            invest_carbon_capture_mix_dict[f'{GlossaryEnergy.direct_air_capture}.AmineScrubbing'] = np.array(
                [0.5] + [1.] * (GlossaryEnergy.NB_POLES_FULL - 1))

        if f'{GlossaryEnergy.direct_air_capture}.CalciumPotassiumScrubbing' in self.technologies_list:
            invest_carbon_capture_mix_dict[f'{GlossaryEnergy.direct_air_capture}.CalciumPotassiumScrubbing'] = [
                0.1 * (1 + 0.03) ** i for i in l_ctrl]

        if f'{GlossaryEnergy.flue_gas_capture}.CalciumLooping' in self.technologies_list:
            invest_carbon_capture_mix_dict[f'{GlossaryEnergy.flue_gas_capture}.CalciumLooping'] = [
                10 * (1 - 0.04) ** i for i in l_ctrl]

        if f'{GlossaryEnergy.flue_gas_capture}.ChilledAmmoniaProcess' in self.technologies_list:
            invest_carbon_capture_mix_dict[f'{GlossaryEnergy.flue_gas_capture}.ChilledAmmoniaProcess'] = [
                10 * (1 - 0.04) ** i for i in l_ctrl]

        if f'{GlossaryEnergy.flue_gas_capture}.CO2Membranes' in self.technologies_list:
            invest_carbon_capture_mix_dict[f'{GlossaryEnergy.flue_gas_capture}.CO2Membranes'] = [
                10 * (1 + 0.0) ** i for i in l_ctrl]

        if f'{GlossaryEnergy.flue_gas_capture}.MonoEthanolAmine' in self.technologies_list:
            invest_carbon_capture_mix_dict[f'{GlossaryEnergy.flue_gas_capture}.MonoEthanolAmine'] = [
                10 * (1 + 0.0) ** i for i in l_ctrl]

        if f'{GlossaryEnergy.flue_gas_capture}.PiperazineProcess' in self.technologies_list:
            invest_carbon_capture_mix_dict[f'{GlossaryEnergy.flue_gas_capture}.PiperazineProcess'] = [
                10 * (1 + 0.0) ** i for i in l_ctrl]

        if f'{GlossaryEnergy.flue_gas_capture}.PressureSwingAdsorption' in self.technologies_list:
            invest_carbon_capture_mix_dict[f'{GlossaryEnergy.flue_gas_capture}.PressureSwingAdsorption'] = [
                10 * (1 + 0.0) ** i for i in l_ctrl]

        if f'{GlossaryEnergy.direct_air_capture}.DirectAirCaptureTechno' in self.technologies_list:
            invest_carbon_capture_mix_dict[f'{GlossaryEnergy.direct_air_capture}.DirectAirCaptureTechno'] = np.ones(
                GlossaryEnergy.NB_POLES_COARSE) * 1e-6
            invest_2020_ccus = DatabaseWitnessEnergy.InvestCCUS2020.value
            invest_carbon_capture_mix_dict[f'{GlossaryEnergy.direct_air_capture}.DirectAirCaptureTechno'][0] = invest_2020_ccus / 3

        if f'{GlossaryEnergy.flue_gas_capture}.FlueGasTechno' in self.technologies_list:
            invest_carbon_capture_mix_dict[f'{GlossaryEnergy.flue_gas_capture}.FlueGasTechno'] = np.ones(
                GlossaryEnergy.NB_POLES_COARSE) * 1e-6
            invest_2020_ccus = DatabaseWitnessEnergy.InvestCCUS2020.value
            invest_carbon_capture_mix_dict[f'{GlossaryEnergy.flue_gas_capture}.FlueGasTechno'][0] = invest_2020_ccus / 3

        if self.bspline:
            invest_carbon_capture_mix_dict[GlossaryEnergy.Years] = self.years

            for techno in self.technologies_list:
                invest_carbon_capture_mix_dict[techno], _ = self.invest_bspline(
                    invest_carbon_capture_mix_dict[techno], len(self.years))

        carbon_capture_mix_invest_df = pd.DataFrame(
            invest_carbon_capture_mix_dict)

        return carbon_capture_mix_invest_df

    def setup_usecase(self, study_folder_path=None):
        energy_mix_name = 'EnergyMix'
        self.energy_name = CarbonCapture.name
        flue_gas_name = FlueGas.node_name
        ccs_name = f'{self.prefix_name}.{CarbonCapture.name}'

        years = np.arange(self.year_start, self.year_end + 1)
        # reference_data_name = 'Reference_aircraft_data'
        energy_prices = pd.DataFrame({GlossaryEnergy.Years: years,
                                      GlossaryEnergy.electricity: 10.0,
                                      'amine': 1300.0,
                                      'potassium': 50.0,
                                      'calcium': 85.0,
                                      GlossaryEnergy.methane: 10.
                                      })

        # the value for invest_level is just set as an order of magnitude
        invest_level = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.InvestValue: 10.0})
        self.flue_gas_mean = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.FlueGasMean: 0.13})

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
            {GlossaryEnergy.Years: years, 'transport': np.ones(len(years)) * 7.0})
        energy_carbon_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'amine': 0.0, 'potassium': 0.0, GlossaryEnergy.electricity: 0.0, 'calcium': 0.0,
             GlossaryEnergy.methane: 0.2})

        coal_gen_prod = pd.DataFrame({GlossaryEnergy.Years: years,
                                      f'{CarbonCapture.flue_gas_name} (Mt)': 0.1})
        gas_turbine_prod = pd.DataFrame({GlossaryEnergy.Years: years,
                                         f'{CarbonCapture.flue_gas_name} (Mt)': 0.1})
        cc_gas_turbine_prod = pd.DataFrame({GlossaryEnergy.Years: years,
                                            f'{CarbonCapture.flue_gas_name} (Mt)': 0.1})
        wgs_prod = pd.DataFrame({GlossaryEnergy.Years: years,
                                 f'{CarbonCapture.flue_gas_name} (Mt)': 0.1})
        ft_prod = pd.DataFrame({GlossaryEnergy.Years: years,
                                f'{CarbonCapture.flue_gas_name} (Mt)': 0.1})
        refinery_prod = pd.DataFrame({GlossaryEnergy.Years: years,
                                      f'{CarbonCapture.flue_gas_name} (Mt)': 0.1})
        CAKOH_production = pd.DataFrame({GlossaryEnergy.Years: years,
                                         f'{CarbonCapture.flue_gas_name} (Mt)': 0.1})
        aminescrubbing_production = pd.DataFrame({GlossaryEnergy.Years: years,
                                                  f'{CarbonCapture.flue_gas_name} (Mt)': 0.1})
        fossil_gas_prod = pd.DataFrame({GlossaryEnergy.Years: years,
                                        f'{CarbonCapture.flue_gas_name} (Mt)': 0.1})
        pelletizing_prod = pd.DataFrame({GlossaryEnergy.Years: years,
                                         f'{CarbonCapture.flue_gas_name} (Mt)': 0.1})
        coal_gas_prod = pd.DataFrame({GlossaryEnergy.Years: years,
                                      f'{CarbonCapture.flue_gas_name} (Mt)': 0.1})
        pyrolysis_prod = pd.DataFrame({GlossaryEnergy.Years: years,
                                       f'{CarbonCapture.flue_gas_name} (Mt)': 0.1})
        pyrolysis_prod = pd.DataFrame({GlossaryEnergy.Years: years,
                                       f'{CarbonCapture.flue_gas_name} (Mt)': 0.1})
        directaircapturetechno_prod = pd.DataFrame({GlossaryEnergy.Years: years,
                                                    f'{CarbonCapture.flue_gas_name} (Mt)': 0.1})

        investment_mix = self.get_investments()
        values_dict = {f'{self.study_name}.{GlossaryEnergy.YearStart}': self.year_start,
                       f'{self.study_name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.study_name}.{ccs_name}.{flue_gas_name}.{GlossaryEnergy.techno_list}': DEFAULT_FLUE_GAS_LIST,
                       f'{self.study_name}.{ccs_name}.{GlossaryEnergy.techno_list}': self.technologies_list,
                       f'{self.study_name}.{ccs_name}.{GlossaryEnergy.flue_gas_capture}.flue_gas_mean': self.flue_gas_mean,
                       f'{self.study_name}.{ccs_name}.{GlossaryEnergy.TransportCostValue}': transport,
                       f'{self.study_name}.{ccs_name}.{GlossaryEnergy.TransportMarginValue}': margin,
                       f'{self.study_name}.{ccs_name}.invest_techno_mix': investment_mix,
                       f'{self.study_name}.{GlossaryEnergy.ccs_list}': [GlossaryEnergy.carbon_capture, GlossaryEnergy.carbon_storage]

                       }

        techno_margin_dict = {
            f'{self.study_name}.{ccs_name}.{techno}.{GlossaryEnergy.MarginValue}': margin for techno in
            self.technologies_list}
        values_dict.update(techno_margin_dict)

        self.techno_capital = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.Capital: 0.0})

        if self.main_study:
            values_dict.update(
                {
                    f'{self.study_name}.{GlossaryEnergy.CO2TaxesValue}': co2_taxes,
                    f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.EnergyPricesValue}': energy_prices,
                    f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.EnergyCO2EmissionsValue}': energy_carbon_emissions,
                    f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.electricity}.CoalGen.flue_gas_co2_ratio': np.array([0.13]),
                    f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.electricity}.GasTurbine.flue_gas_co2_ratio': np.array([0.035]),
                    f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.electricity}.CombinedCycleGasTurbine.flue_gas_co2_ratio': np.array(
                        [0.035]),
                    f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.WaterGasShift.flue_gas_co2_ratio': np.array(
                        [0.175]),
                    f'{self.study_name}.{energy_mix_name}.liquid_fuel.FischerTropsch.flue_gas_co2_ratio': np.array(
                        [0.12]),
                    f'{self.study_name}.{energy_mix_name}.liquid_fuel.Refinery.flue_gas_co2_ratio': np.array([0.12]),
                    f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.methane}.FossilGas.flue_gas_co2_ratio': np.array([0.085]),
                    f'{self.study_name}.{energy_mix_name}.solid_fuel.Pelletizing.flue_gas_co2_ratio': np.array([0.12]),
                    f'{self.study_name}.{energy_mix_name}.syngas.CoalGasification.flue_gas_co2_ratio': np.array([0.13]),
                    f'{self.study_name}.{energy_mix_name}.syngas.Pyrolysis.flue_gas_co2_ratio': np.array([0.13]),
                    f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.fossil}.FossilSimpleTechno.flue_gas_co2_ratio': np.array(
                        [0.12]),
                    f'{self.study_name}.{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.direct_air_capture}.CalciumPotassiumScrubbing.flue_gas_co2_ratio': np.array(
                        [0.035]),
                    f'{self.study_name}.{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.direct_air_capture}.AmineScrubbing.flue_gas_co2_ratio': np.array(
                        [0.035]),
                    f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.electricity}.CoalGen.{GlossaryEnergy.TechnoProductionValue}': coal_gen_prod,
                    f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.electricity}.GasTurbine.{GlossaryEnergy.TechnoProductionValue}': gas_turbine_prod,
                    f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.electricity}.CombinedCycleGasTurbine.{GlossaryEnergy.TechnoProductionValue}': cc_gas_turbine_prod,
                    f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.WaterGasShift.{GlossaryEnergy.TechnoProductionValue}': wgs_prod,
                    f'{self.study_name}.{energy_mix_name}.liquid_fuel.FischerTropsch.{GlossaryEnergy.TechnoProductionValue}': ft_prod,
                    f'{self.study_name}.{energy_mix_name}.liquid_fuel.Refinery.{GlossaryEnergy.TechnoProductionValue}': refinery_prod,
                    f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.methane}.FossilGas.{GlossaryEnergy.TechnoProductionValue}': fossil_gas_prod,
                    f'{self.study_name}.{energy_mix_name}.solid_fuel.Pelletizing.{GlossaryEnergy.TechnoProductionValue}': pelletizing_prod,
                    f'{self.study_name}.{energy_mix_name}.syngas.CoalGasification.{GlossaryEnergy.TechnoProductionValue}': coal_gas_prod,
                    f'{self.study_name}.{energy_mix_name}.syngas.Pyrolysis.{GlossaryEnergy.TechnoProductionValue}': pyrolysis_prod,
                    f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.fossil}.FossilSimpleTechno.{GlossaryEnergy.TechnoProductionValue}': refinery_prod,
                    f'{self.study_name}.{GlossaryEnergy.CCUS}.{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.direct_air_capture}.CalciumPotassiumScrubbing.{GlossaryEnergy.TechnoProductionValue}': CAKOH_production,
                    f'{self.study_name}.{GlossaryEnergy.CCUS}.{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.direct_air_capture}.AmineScrubbing.{GlossaryEnergy.TechnoProductionValue}': aminescrubbing_production,
                    f'{self.study_name}.{GlossaryEnergy.CCUS}.{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.direct_air_capture}.DirectAirCaptureTechno.{GlossaryEnergy.TechnoProductionValue}': directaircapturetechno_prod,
                    f"{self.study_name}.{energy_mix_name}.{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.flue_gas_capture}.electricity.CoalGen.{GlossaryEnergy.TechnoCapitalValue}": self.techno_capital,
                    f"{self.study_name}.{energy_mix_name}.{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.flue_gas_capture}.electricity.GasTurbine.{GlossaryEnergy.TechnoCapitalValue}": self.techno_capital,
                    f"{self.study_name}.{energy_mix_name}.{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.flue_gas_capture}.electricity.CombinedCycleGasTurbine.{GlossaryEnergy.TechnoCapitalValue}": self.techno_capital,
                    f"{self.study_name}.{energy_mix_name}.{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.flue_gas_capture}.hydrogen.gaseous_hydrogen.WaterGasShift.{GlossaryEnergy.TechnoCapitalValue}": self.techno_capital,
                    f"{self.study_name}.{energy_mix_name}.{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.flue_gas_capture}.liquid_fuel.FischerTropsch.{GlossaryEnergy.TechnoCapitalValue}": self.techno_capital,
                    f"{self.study_name}.{energy_mix_name}.{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.flue_gas_capture}.liquid_fuel.Refinery.{GlossaryEnergy.TechnoCapitalValue}": self.techno_capital,
                    f"{self.study_name}.{energy_mix_name}.{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.flue_gas_capture}.methane.FossilGas.{GlossaryEnergy.TechnoCapitalValue}": self.techno_capital,
                    f"{self.study_name}.{energy_mix_name}.{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.flue_gas_capture}.solid_fuel.Pelletizing.{GlossaryEnergy.TechnoCapitalValue}": self.techno_capital,
                    f"{self.study_name}.{energy_mix_name}.{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.flue_gas_capture}.syngas.CoalGasification.{GlossaryEnergy.TechnoCapitalValue}": self.techno_capital,
                    f"{self.study_name}.{energy_mix_name}.{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.flue_gas_capture}.fossil.FossilSimpleTechno.{GlossaryEnergy.TechnoCapitalValue}": self.techno_capital,
                    f"{self.study_name}.{energy_mix_name}.{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.flue_gas_capture}.carbon_capture.direct_air_capture.AmineScrubbing.{GlossaryEnergy.TechnoCapitalValue}": self.techno_capital,
                    f"{self.study_name}.{energy_mix_name}.{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.flue_gas_capture}.carbon_capture.direct_air_capture.CalciumPotassiumScrubbing.{GlossaryEnergy.TechnoCapitalValue}": self.techno_capital,
                    f"{self.study_name}.{energy_mix_name}.{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.flue_gas_capture}.carbon_capture.direct_air_capture.DirectAirCaptureTechno.{GlossaryEnergy.TechnoCapitalValue}": self.techno_capital,
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
    uc_cls = Study(main_study=True,
                   technologies_list=DEFAULT_TECHNOLOGIES_LIST)
    uc_cls.test()
