'''
Copyright 2022 Airbus SAS
Modifications on 2023/04/21-2023/11/16 Copyright 2023 Capgemini

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
from pandas import DataFrame, concat
from energy_models.core.demand.energy_demand_disc import EnergyDemandDiscipline
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.heat_mix.heat_mix import HeatMix
from energy_models.core.energy_process_builder import INVEST_DISCIPLINE_DEFAULT, \
    INVEST_DISCIPLINE_OPTIONS
from energy_models.core.energy_study_manager import AGRI_TYPE, EnergyStudyManager, \
    DEFAULT_TECHNO_DICT, CCUS_TYPE, ENERGY_TYPE

from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import GaseousHydrogen
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.resources_data_disc import get_static_CO2_emissions, get_static_prices
from energy_models.glossaryenergy import GlossaryEnergy
from sostrades_core.execution_engine.func_manager.func_manager import FunctionManager
from sostrades_core.execution_engine.func_manager.func_manager_disc import FunctionManagerDisc
from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from energy_models.core.stream_type.energy_models.heat import lowtemperatureheat
from energy_models.core.stream_type.energy_models.heat import mediumtemperatureheat
from energy_models.sos_processes.energy.heat_techno_mix.hightemperatureheat_mix.usecase import \
    TECHNOLOGIES_LIST_DEV as hightemperatureheat_technos_dev
from energy_models.sos_processes.energy.heat_techno_mix.lowtemperatureheat_mix.usecase import \
    TECHNOLOGIES_LIST_DEV as lowtemperatureheat_technos_dev
from energy_models.sos_processes.energy.heat_techno_mix.mediumtemperatureheat_mix.usecase import \
    TECHNOLOGIES_LIST_DEV as mediumtemperatureheat_technos_dev
DEFAULT_TECHNO_DICT = {
                       hightemperatureheat.name: {'type': ENERGY_TYPE, 'value': hightemperatureheat_technos_dev},
                       mediumtemperatureheat.name: {'type': ENERGY_TYPE, 'value': mediumtemperatureheat_technos_dev},
                       lowtemperatureheat.name: {'type': ENERGY_TYPE, 'value': lowtemperatureheat_technos_dev},
                       }

OBJECTIVE = FunctionManagerDisc.OBJECTIVE
INEQ_CONSTRAINT = FunctionManagerDisc.INEQ_CONSTRAINT
EQ_CONSTRAINT = FunctionManagerDisc.EQ_CONSTRAINT
OBJECTIVE_LAGR = FunctionManagerDisc.OBJECTIVE_LAGR
FUNC_DF = FunctionManagerDisc.FUNC_DF
CO2_TAX_MINUS_CCS_CONSTRAINT_DF = EnergyMix.CO2_TAX_MINUS_CCS_CONSTRAINT_DF
# TOTAL_PROD_MINUS_MIN_PROD_CONSTRAINT_DF = HeatMix.TOTAL_PROD_MINUS_MIN_PROD_CONSTRAINT_DF
INVEST_DISC_NAME = 'InvestmentDistribution'
hydropower_name = Electricity.hydropower_name
from sostrades_core.tools.post_processing.post_processing_factory import PostProcessingFactory

class Study(EnergyStudyManager):
    def __init__(self, year_start=2020, year_end=2050, time_step=1, lower_bound_techno=1.0e-6, upper_bound_techno=100.,
                 techno_dict=DEFAULT_TECHNO_DICT,
                 main_study=True, bspline=True, execution_engine=None, invest_discipline=INVEST_DISCIPLINE_DEFAULT,
                 energy_invest_input_in_abs_value=True):
        self.heat_mix = 'HeatMix'
        self.year_start = year_start
        self.year_end = year_end
        self.time_step = time_step
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.energy_list = techno_dict

        if invest_discipline == INVEST_DISCIPLINE_OPTIONS[2]:
            self.lower_bound_techno = 1.0e-6
            self.upper_bound_techno = 3000

        else:
            self.lower_bound_techno = lower_bound_techno
            self.upper_bound_techno = upper_bound_techno
        self.sub_study_dict = None
        self.sub_study_path_dict = None

        # -- Call class constructor after attributes have been set for setup_process usage
        # EnergyStudyManager init will compute energy_list and ccs_list with
        # the techno_dict
        super().__init__(__file__, main_study=main_study,
                         execution_engine=execution_engine, techno_dict=techno_dict)

        self.create_study_list()
        self.bspline = bspline
        self.invest_discipline = invest_discipline
        self.energy_invest_input_in_abs_value = energy_invest_input_in_abs_value

    def create_study_list(self):
        self.sub_study_dict = {}
        self.sub_study_path_dict = {}
        for energy in self.energy_list:
            cls, path = self.get_energy_mix_study_cls(energy)
            self.sub_study_dict[energy] = cls
            self.sub_study_path_dict[energy] = path

    def setup_usecase_sub_study_list(self):
        """
        Instantiate sub studies and values dict from setup_usecase
        """
        values_dict_list = []
        instanced_sub_studies = []
        dspace_list = []
        for sub_study_name, sub_study in self.sub_study_dict.items():
            if self.techno_dict[sub_study_name]['type'] == ENERGY_TYPE:
                prefix_name = 'HeatMix'
                instance_sub_study = sub_study(
                    self.year_start, self.year_end, self.time_step, bspline=self.bspline, main_study=False,
                    execution_engine=self.execution_engine,
                    invest_discipline=self.invest_discipline,
                    technologies_list=self.techno_dict[sub_study_name]['value'])
            if self.techno_dict[sub_study_name]['type'] != AGRI_TYPE:
                instance_sub_study.configure_ds_boundaries(lower_bound_techno=self.lower_bound_techno,
                                                           upper_bound_techno=self.upper_bound_techno, )
                instance_sub_study.study_name = self.study_name
                data_dict = instance_sub_study.setup_usecase()
                values_dict_list.extend(data_dict)
                instanced_sub_studies.append(instance_sub_study)
                dspace_list.append(instance_sub_study.dspace)
            else:
                # Add an empty study because biomass_dry is not an energy_mix study,
                # it is integrated in the witness_wo_energy datacase in the agriculture_mix usecase
                instanced_sub_studies.append(None)
        return values_dict_list, dspace_list, instanced_sub_studies
    def get_investments_mix_custom(self):
        # invest from WEI 2020 miss hydrogen
        invest_energy_mix_dict = {}
        years = np.arange(0, 8)
        invest_energy_mix_dict[GlossaryEnergy.Years] = years
        # invest_energy_mix_dict[Methane.name] = [
        #     1.2, 0.5, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0]
        invest_energy_mix_dict[hightemperatureheat.name] = [
            3.15, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        invest_energy_mix_dict[mediumtemperatureheat.name] = [
            3.15, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        invest_energy_mix_dict[lowtemperatureheat.name] = [
            3.15, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        if self.bspline:
            invest_energy_mix_dict[GlossaryEnergy.Years] = self.years
            for energy in self.energy_list:
                invest_energy_mix_dict[energy], _ = self.invest_bspline(
                    invest_energy_mix_dict[energy], len(self.years))

        energy_mix_invest_df = pd.DataFrame(
            {key: value for key, value in invest_energy_mix_dict.items() if
             key in self.energy_list or key == GlossaryEnergy.Years})
        return energy_mix_invest_df
    def get_total_mix(self, instanciated_studies, ccs_percentage):
        '''
        Get the total mix of each techno with the invest distribution discipline
         with ccs percentage, mixes by energy and by techno
        '''
        energy_mix = self.get_investments_mix_custom()
        invest_mix_df = pd.DataFrame({GlossaryEnergy.Years: energy_mix[GlossaryEnergy.Years].values})
        norm_energy_mix = energy_mix.drop(
            GlossaryEnergy.Years, axis=1).sum(axis=1).values

        for study in instanciated_studies:
            if study is not None:
                invest_techno = study.get_investments()
                energy = study.energy_name
                if energy in energy_mix.columns:
                    pass
                else:
                    raise Exception(f'{energy} not in investment_mixes')
                for techno in invest_techno.columns:
                    if techno != GlossaryEnergy.Years:
                        invest_mix_df[f'{energy}.{techno}'] = invest_techno[techno].values
                                                              #  * mix_energy / norm_techno_mix

        return invest_mix_df
    def create_technolist_per_energy(self, instanciated_studies):
        self.dict_technos = {}
        dict_studies = dict(
            zip(self.energy_list, instanciated_studies))

        for energy_name, study_val in dict_studies.items():
            if study_val is not None:
                self.dict_technos[energy_name] = study_val.technologies_list
            else:
                # the study_val == None is for the biomass_dry that is taken into account with the agriculture_mix
                # so it has no dedicated technology in the energy_mix
                self.dict_technos[energy_name] = []

    def setup_usecase(self):

        hydrogen_name = GaseousHydrogen.name
        high_heat_name = hightemperatureheat.name
        medium_heat_name = mediumtemperatureheat.name
        low_heat_name = lowtemperatureheat.name
        methane_name = Methane.name
        electricity_name = Electricity.name
        energy_mix_name = 'HeatMix' #EnergyMix.name
        energy_price_dict = {GlossaryEnergy.Years: self.years,
                             high_heat_name: 71.0,
                             medium_heat_name: 71.0,
                             low_heat_name: 71.0,
                             }

        # price in $/MWh
        self.energy_prices = pd.DataFrame({key: value for key, value in energy_price_dict.items(
        ) if key in self.techno_dict or key == GlossaryEnergy.Years})

        self.energy_prices[methane_name] = 34.0
        self.energy_prices[electricity_name] = 9.0
        self.energy_prices[hydrogen_name] = 90.0

        energy_carbon_emissions_dict = {GlossaryEnergy.Years: self.years,
                                        high_heat_name: 0.0,
                                        medium_heat_name: 0.0,
                                        low_heat_name: 0.0,
                                        }
        # price in $/MWh
        self.energy_carbon_emissions = pd.DataFrame(
            {key: value for key, value in energy_carbon_emissions_dict.items() if
             key in self.techno_dict or key == GlossaryEnergy.Years})
        self.energy_carbon_emissions[methane_name] = 0.123 / 15.4
        self.energy_carbon_emissions[electricity_name] = 0.0

        # --- resources price and co2 emissions
        self.resources_CO2_emissions = get_static_CO2_emissions(self.years)
        self.resources_prices = get_static_prices(self.years)

        demand_ratio_dict = dict(
            zip(self.energy_list, np.ones((len(self.years), len(self.years))) * 100.))
        demand_ratio_dict[GlossaryEnergy.Years] = self.years

        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)

        ratio_available_resource_dict = dict(
            zip(EnergyMix.RESOURCE_LIST, np.ones((len(self.years), len(self.years))) * 100.))
        ratio_available_resource_dict[GlossaryEnergy.Years] = self.years
        self.all_resource_ratio_usable_demand = pd.DataFrame(
            ratio_available_resource_dict)

        invest_ref = 10.55  # 100G$
        invest = np.ones(len(self.years)) * invest_ref
        invest[0] = invest_ref
        for i in range(1, len(self.years)):
            invest[i] = (1.0 - 0.0253) * invest[i - 1]
        invest_df = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.EnergyInvestmentsValue: invest})
        invest_df.index = self.years
        scaling_factor_energy_investment = 100.0
        # init land surface for food for biomass dry crop energy
        land_surface_for_food = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                              'Agriculture total (Gha)': np.ones(len(self.years)) * 4.8})

        ccs_percentage = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, 'ccs_percentage': 25.0})
        co2_emissions_from_energy_mix = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, 'carbon_capture from energy mix (Mt)': 25.0})

        population_df = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.PopulationValue: np.linspace(7886.69358, 9000., len(self.years))})
        transport_demand = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                         GlossaryEnergy.TransportDemandValue: np.linspace(33600., 30000., len(self.years))})

        self.forest_invest_df = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.ForestInvestmentValue: 5})

        if not self.energy_invest_input_in_abs_value:
            # if energy investments are expressed in percentage, the new corresponding inputs must be defined
            self.invest_percentage_gdp = pd.DataFrame(data={GlossaryEnergy.Years: self.years,
                                                            GlossaryEnergy.EnergyInvestPercentageGDPName: np.linspace(
                                                                10., 20., len(self.years))})

        energy_mix_high_heat_production_dic = {}
        energy_mix_high_heat_production_dic[GlossaryEnergy.Years] = self.years
        energy_mix_high_heat_production_dic['NaturalGasBoilerHighHeat'] = np.ones(len(self.years)) * 2
        energy_mix_high_heat_production_dic['ElectricBoilerHighHeat'] = np.ones(len(self.years)) * 3
        energy_mix_high_heat_production_dic['HeatPumpHighHeat'] = np.ones(len(self.years)) * 4
        energy_mix_high_heat_production_dic['GeothermalHighHeat'] = np.ones(len(self.years)) * 5
        energy_mix_high_heat_production_dic['CHPHighHeat'] = np.ones(len(self.years)) * 6
        energy_mix_high_heat_production_dic['HydrogenBoilerHighHeat'] = np.ones(len(self.years)) * 7
        self.high_heat_production = pd.DataFrame(energy_mix_high_heat_production_dic)

        energy_mix_low_heat_production_dic = {}
        energy_mix_low_heat_production_dic[GlossaryEnergy.Years] = self.years
        energy_mix_low_heat_production_dic['NaturalGasBoilerLowHeat'] = np.ones(len(self.years)) * 15.0
        energy_mix_low_heat_production_dic['ElectricBoilerLowHeat'] = np.ones(len(self.years)) * 16.0
        energy_mix_low_heat_production_dic['HeatPumpLowHeat'] = np.ones(len(self.years)) * 17.0
        energy_mix_low_heat_production_dic['GeothermalLowHeat'] = np.ones(len(self.years)) * 18.0
        energy_mix_low_heat_production_dic['CHPLowHeat'] = np.ones(len(self.years)) * 19.0
        energy_mix_low_heat_production_dic['HydrogenBoilerLowHeat'] = np.ones(len(self.years)) * 20.0
        self.low_heat_production = pd.DataFrame(energy_mix_low_heat_production_dic)

        energy_mix_mediun_heat_production_dic = {}
        energy_mix_mediun_heat_production_dic[GlossaryEnergy.Years] = self.years
        energy_mix_mediun_heat_production_dic['NaturalGasBoilerMediumHeat'] = np.ones(len(self.years)) * 22.0
        energy_mix_mediun_heat_production_dic['ElectricBoilerMediumHeat'] = np.ones(len(self.years)) * 23.0
        energy_mix_mediun_heat_production_dic['HeatPumpMediumHeat'] = np.ones(len(self.years)) * 24.0
        energy_mix_mediun_heat_production_dic['GeothermalMediumHeat'] = np.ones(len(self.years)) * 25.0
        energy_mix_mediun_heat_production_dic['CHPMediumHeat'] = np.ones(len(self.years)) * 13.0
        energy_mix_mediun_heat_production_dic['HydrogenBoilerMediumHeat'] = np.ones(len(self.years)) * 18.0
        self.medium_heat_production = pd.DataFrame(energy_mix_mediun_heat_production_dic)

        energy_mix_emission_dic = {}
        energy_mix_emission_dic[GlossaryEnergy.Years] = self.years
        energy_mix_emission_dic['heat.hightemperatureheat.NaturalGasBoilerHighHeat'] = np.ones(len(self.years)) * 10.0
        energy_mix_emission_dic['heat.hightemperatureheat.ElectricBoilerHighHeat'] = np.ones(len(self.years)) * 20.0
        energy_mix_emission_dic['heat.hightemperatureheat.HeatPumpHighHeat'] = np.ones(len(self.years)) * 30.0
        energy_mix_emission_dic['heat.hightemperatureheat.GeothermalHighHeat'] = np.ones(len(self.years)) * 40.0
        energy_mix_emission_dic['heat.hightemperatureheat.CHPHighHeat'] = np.ones(len(self.years)) * 50.0
        energy_mix_emission_dic['heat.hightemperatureheat.HydrogenBoilerHighHeat'] = np.ones(len(self.years)) * 60.0

        energy_mix_emission_dic['heat.lowtemperatureheat.NaturalGasBoilerLowHeat'] = np.ones(len(self.years)) * 10.0
        energy_mix_emission_dic['heat.lowtemperatureheat.ElectricBoilerLowHeat'] = np.ones(len(self.years)) * 20.0
        energy_mix_emission_dic['heat.lowtemperatureheat.HeatPumpLowHeat'] = np.ones(len(self.years)) * 30.0
        energy_mix_emission_dic['heat.lowtemperatureheat.GeothermalLowHeat'] = np.ones(len(self.years)) * 40.0
        energy_mix_emission_dic['heat.lowtemperatureheat.CHPLowHeat'] = np.ones(len(self.years)) * 50.0
        energy_mix_emission_dic['heat.lowtemperatureheat.HydrogenBoilerLowHeat'] = np.ones(len(self.years)) * 60.0

        energy_mix_emission_dic['heat.mediumtemperatureheat.NaturalGasBoilerMediumHeat'] = np.ones(
            len(self.years)) * 10.0
        energy_mix_emission_dic['heat.mediumtemperatureheat.ElectricBoilerMediumHeat'] = np.ones(len(self.years)) * 20.0
        energy_mix_emission_dic['heat.mediumtemperatureheat.HeatPumpMediumHeat'] = np.ones(len(self.years)) * 30.0
        energy_mix_emission_dic['heat.mediumtemperatureheat.GeothermalMediumHeat'] = np.ones(len(self.years)) * 40.0
        energy_mix_emission_dic['heat.mediumtemperatureheat.CHPMediumHeat'] = np.ones(len(self.years)) * 50.0
        energy_mix_emission_dic['heat.mediumtemperatureheat.HydrogenBoilerMediumHeat'] = np.ones(len(self.years)) * 60.0

        energy_mix_emission = pd.DataFrame(energy_mix_emission_dic)

        energy_mix_target_production_dic = {}
        energy_mix_target_production_dic[GlossaryEnergy.Years] = self.years
        energy_mix_target_production_dic['target production'] = 260

        self.traget_production = pd.DataFrame(energy_mix_target_production_dic)

        values_dict = {
                       f'{self.study_name}.{GlossaryEnergy.EnergyInvestmentsValue}': invest_df,
                       f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.InvestLevelValue}': invest_df,
                       f'{self.study_name}.{GlossaryEnergy.YearStart}': self.year_start,
                       f'{self.study_name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.study_name}.{GlossaryEnergy.energy_list}': self.energy_list,
                       f'{self.study_name}.{energy_mix_name}.CO2_emission_mix': energy_mix_emission,
                       f'{self.study_name}.{GlossaryEnergy.ccs_list}': self.ccs_list,
                       f'{self.study_name}.{GlossaryEnergy.EnergyPricesValue}': self.energy_prices,
                       f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.EnergyPricesValue}': self.energy_prices,
                       f'{self.study_name}.{GlossaryEnergy.EnergyCO2EmissionsValue}': self.energy_carbon_emissions,
                       f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.EnergyCO2EmissionsValue}': self.energy_carbon_emissions,
                       f'{self.study_name}.max_mda_iter': 1,
                       f'{self.study_name}.sub_mda_class': 'MDAGaussSeidel',
                       f'{self.study_name}.{energy_mix_name}.heat.hightemperatureheat.{GlossaryEnergy.EnergyProductionValue}': self.high_heat_production,
                       f'{self.study_name}.{energy_mix_name}.heat.mediumtemperatureheat.{GlossaryEnergy.EnergyProductionValue}': self.medium_heat_production,
                       f'{self.study_name}.{energy_mix_name}.heat.lowtemperatureheat.{GlossaryEnergy.EnergyProductionValue}': self.low_heat_production,
                       f'{self.study_name}.{energy_mix_name}.target_heat_production': self.traget_production,
                       f'{self.study_name}.{energy_mix_name}.heat.hightemperatureheat.{GlossaryEnergy.EnergyCO2EmissionsValue}': self.energy_carbon_emissions,
                       f'{self.study_name}.{energy_mix_name}.heat.mediumtemperatureheat.{GlossaryEnergy.EnergyCO2EmissionsValue}': self.energy_carbon_emissions,
                       f'{self.study_name}.{energy_mix_name}.heat.lowtemperatureheat.{GlossaryEnergy.EnergyCO2EmissionsValue}': self.energy_carbon_emissions,
                       }

        values_dict_list = []
        values_dict_list, dspace_list, instanciated_studies = self.setup_usecase_sub_study_list()

        if self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[1]:

            invest_mix_df = self.get_total_mix(
                instanciated_studies, ccs_percentage)
            values_dict.update(
                {f'{self.study_name}.{INVEST_DISC_NAME}.{GlossaryEnergy.invest_mix}': invest_mix_df})
        elif self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[2]:
            invest_mix_df = self.get_absolute_total_mix(
                instanciated_studies, ccs_percentage, invest_df, scaling_factor_energy_investment)
            values_dict.update(
                {f'{self.study_name}.{INVEST_DISC_NAME}.{GlossaryEnergy.invest_mix}': invest_mix_df})
            if not self.energy_invest_input_in_abs_value:
                # if energy investments are expressed in percentage, the new corresponding inputs must be defined
                values_dict.update(
                    {f'{self.study_name}.{INVEST_DISC_NAME}.{GlossaryEnergy.EnergyInvestPercentageGDPName}': self.invest_percentage_gdp,
                     }
                )

        values_dict_list.append(values_dict)

        # self.func_df = concat(
        #     [self.setup_objectives(), self.setup_constraints()])

        self.create_technolist_per_energy(instanciated_studies)

        return values_dict_list


if '__main__' == __name__:
    uc_cls = Study()
    uc_cls.load_data()
    uc_cls.ee.display_treeview_nodes()
    uc_cls.test()