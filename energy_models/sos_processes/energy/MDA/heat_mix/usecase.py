'''
Copyright 2024 Capgemini

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

import pandas as pd
import numpy as np
import pandas as pd
import numpy as np
from sostrades_core.study_manager.study_manager import StudyManager
from energy_models.core.energy_mix_study_manager import EnergyMixStudyManager
from importlib import import_module
from energy_models.core.demand.energy_demand_disc import EnergyDemandDiscipline
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.heat_mix.heat_mix import HeatMix
from energy_models.core.energy_process_builder import INVEST_DISCIPLINE_DEFAULT, \
    INVEST_DISCIPLINE_OPTIONS
from energy_models.core.energy_study_manager import AGRI_TYPE, EnergyStudyManager, \
    DEFAULT_TECHNO_DICT, CCUS_TYPE, ENERGY_TYPE
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.carbon_models.carbon_storage import CarbonStorage
from energy_models.core.stream_type.carbon_models.flue_gas import FlueGas
from energy_models.core.stream_type.energy_models.biodiesel import BioDiesel
from energy_models.core.stream_type.energy_models.biogas import BioGas
from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.ethanol import Ethanol
from energy_models.core.stream_type.energy_models.fossil import Fossil
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import GaseousHydrogen
from energy_models.core.stream_type.energy_models.hydrotreated_oil_fuel import HydrotreatedOilFuel
from energy_models.core.stream_type.energy_models.liquid_fuel import LiquidFuel
from energy_models.core.stream_type.energy_models.liquid_hydrogen import LiquidHydrogen
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.energy_models.renewable import Renewable
from energy_models.core.stream_type.energy_models.solid_fuel import SolidFuel
from energy_models.core.stream_type.energy_models.syngas import Syngas
from energy_models.core.stream_type.resources_data_disc import get_static_CO2_emissions, get_static_prices
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.carbon_storage.pure_carbon_solid_storage.pure_carbon_solid_storage import PureCarbonSS
from energy_models.sos_processes.energy.techno_mix.carbon_capture_mix.usecase import DEFAULT_FLUE_GAS_LIST
from sostrades_core.execution_engine.func_manager.func_manager import FunctionManager
from sostrades_core.execution_engine.func_manager.func_manager_disc import FunctionManagerDisc
from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from energy_models.core.stream_type.energy_models.heat import lowtemperatureheat
from energy_models.core.stream_type.energy_models.heat import mediumtemperatureheat
from energy_models.sos_processes.energy.techno_mix.hightemperatureheat_mix.usecase import \
    TECHNOLOGIES_LIST_DEV as hightemperatureheat_technos_dev
from energy_models.sos_processes.energy.techno_mix.lowtemperatureheat_mix.usecase import \
    TECHNOLOGIES_LIST_DEV as lowtemperatureheat_technos_dev
from energy_models.sos_processes.energy.techno_mix.mediumtemperatureheat_mix.usecase import \
    TECHNOLOGIES_LIST_DEV as mediumtemperatureheat_technos_dev
DEFAULT_TECHNO_DICT = {
                       hightemperatureheat.name: {'type': ENERGY_TYPE, 'value': hightemperatureheat_technos_dev},
                       mediumtemperatureheat.name: {'type': ENERGY_TYPE, 'value': mediumtemperatureheat_technos_dev},
                       lowtemperatureheat.name: {'type': ENERGY_TYPE, 'value': lowtemperatureheat_technos_dev},
                       }

INVEST_DISC_NAME = 'InvestmentDistribution'
class Study(EnergyStudyManager):
    def __init__(self, execution_engine=None):
        super().__init__(__file__, execution_engine=execution_engine)
        self.heat_mix = 'EnergyMix'

        self.year_start = 2023
        self.year_end = 2050
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.heat_techno_list = list(DEFAULT_TECHNO_DICT.keys())
        self.techno_heat_dict = {}
        self.techno_dict = DEFAULT_TECHNO_DICT
        self.energy_list = self.heat_techno_list


        self.techno_usecases = None
        self.ns_public = None
        self.ns_mix = None
        self.ns_functions = None
        self.create_study_list()

    def get_energy_mix_study_cls(self, energy_name, add_name=None):
        dot_split = energy_name.split('.')  # -- case hydrogen.liquid_hydrogen
        lower_name = dot_split[-1].lower()
        if add_name is None:
            path = 'energy_models.sos_processes.energy.techno_mix.' + \
                   lower_name + '_mix.usecase'
        else:
            path = 'energy_models.sos_processes.energy.techno_mix.' + \
                   lower_name + f'_{add_name}' + '_mix.usecase' + f'_{add_name}'
        study_cls = getattr(import_module(path), 'Study')
        return study_cls, path
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
            # if self.techno_dict[sub_study_name]['type'] == CCUS_TYPE:
            #     prefix_name = 'CCUS'
            #     instance_sub_study = sub_study(
            #         self.year_start, self.year_end, self.time_step, bspline=self.bspline, main_study=False,
            #         prefix_name=prefix_name, execution_engine=self.execution_engine,
            #         invest_discipline=self.invest_discipline,
            #         technologies_list=self.techno_dict[sub_study_name]['value'])
            if self.techno_dict[sub_study_name]['type'] == ENERGY_TYPE:
                prefix_name = 'EnergyMix'
                instance_sub_study = sub_study(
                    self.year_start, self.year_end,  main_study=False,
                    execution_engine=self.execution_engine,
                    technologies_list=self.techno_dict[sub_study_name]['value'])
            elif self.techno_dict[sub_study_name]['type'] == AGRI_TYPE:
                pass
            else:
                raise Exception(
                    f"The type of {sub_study_name} : {self.techno_dict[sub_study_name]['type']} is not in [{ENERGY_TYPE},{CCUS_TYPE},{AGRI_TYPE}]")
            if self.techno_dict[sub_study_name]['type'] != AGRI_TYPE:
                # instance_sub_study.configure_ds_boundaries(lower_bound_techno=self.lower_bound_techno,
                #                                            upper_bound_techno=self.upper_bound_techno, )
                instance_sub_study.study_name = self.study_name
                data_dict = instance_sub_study.setup_usecase()
                values_dict_list.extend(data_dict)
                instanced_sub_studies.append(instance_sub_study)
                dspace_list.append(instance_sub_study.dspace)
            else:
                # Add an empty study because biomass_dry is not an energy_mix study,
                # it is integrated in the witness_wo_energy datacase in the agriculture_mix usecase
                instanced_sub_studies.append(None)
        return values_dict_list,  instanced_sub_studies
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

    def get_investments_mix_custom(self):
        """
        put a X0 tested on optim subprocess that satisfy all constraints
        """

        # Source for invest: IEA 2022; World Energy Investment,
        # https://www.iea.org/reports/world-energy-investment-2020,
        # License: CC BY 4.0.
        # Take variation from 2015 to 2019 (2020 is a covid year)
        # And assume a variation per year with this
        # invest of ref are 1295-electricity_networks- crude oil (only liquid_fuel
        # is taken into account)

        # invest from WEI 2020 miss hydrogen
        invest_energy_mix_dict = {}
        if 'renewable' in self.energy_list and 'fossil' in self.energy_list:
            years = np.arange(0, GlossaryEnergy.NB_POLES_COARSE)
        else:
            years = np.arange(0, 8)
        invest_energy_mix_dict[GlossaryEnergy.Years] = years
        invest_energy_mix_dict[hightemperatureheat.name] = [
            3.15, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        invest_energy_mix_dict[mediumtemperatureheat.name] = [
            3.15, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        invest_energy_mix_dict[lowtemperatureheat.name] = [
            3.15, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        invest_energy_mix_dict[Renewable.name] = np.linspace(
            1000.0, 15.625, len(years))
        invest_energy_mix_dict[Fossil.name] = np.linspace(
            1500.0, 77.5, len(years))
        invest_energy_mix_dict[HydrotreatedOilFuel.name] = [
            3.15, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        invest_energy_mix_dict[Ethanol.name] = [
            0.02, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        energy_mix_invest_df = pd.DataFrame(
            {key: value for key, value in invest_energy_mix_dict.items() if
             key in self.energy_list or key == GlossaryEnergy.Years})

        return energy_mix_invest_df

    def get_total_mix(self, instanciated_studies):
        '''
        Get the total mix of each techno with the invest distribution discipline
         with ccs percentage, mixes by energy and by techno
        '''
        energy_mix = self.get_investments_mix_custom()
        invest_mix_df = pd.DataFrame({GlossaryEnergy.Years: energy_mix[GlossaryEnergy.Years].values})
        norm_energy_mix = energy_mix.drop(
            GlossaryEnergy.Years, axis=1).sum(axis=1).values

        # if self.bspline:
        #     ccs_percentage_array = ccs_percentage['ccs_percentage'].values
        # else:
        #     ccs_percentage_array = np.ones_like(norm_energy_mix) * 25.0

        # ccs_mix = self.get_investments_ccs_mix_custom()
        # norm_ccs_mix = ccs_mix.drop(
        #     GlossaryEnergy.Years, axis=1).sum(axis=1)
        for study in instanciated_studies:
            if study is not None:
                invest_techno = study.get_investments()
                # if GlossaryEnergy.Years in invest_techno.columns:
                #     norm_techno_mix = invest_techno.drop(
                #         GlossaryEnergy.Years, axis=1).sum(axis=1)
                # else:
                #     norm_techno_mix = invest_techno.sum(axis=1)
                energy = study.energy_name
                if energy in energy_mix.columns:
                    pass
                    # mix_energy = energy_mix[energy].values / norm_energy_mix * \
                    #              (100.0 - ccs_percentage_array) / 100.0
                # elif energy in ccs_mix.columns:
                #     mix_energy = ccs_mix[energy].values / norm_ccs_mix * \
                #                  ccs_percentage_array / 100.0
                else:
                    raise Exception(f'{energy} not in investment_mixes')
                for techno in invest_techno.columns:
                    if techno != GlossaryEnergy.Years:
                        invest_mix_df[f'{energy}.{techno}'] = invest_techno[techno].values
                                                              #  * mix_energy / norm_techno_mix
        print('')
        print(invest_mix_df.to_string())
        return invest_mix_df

    def get_co2_taxes_df_custom(self):

        co2_taxes = np.linspace(750, 750, len(self.years))
        co2_taxes_df = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.CO2Tax: co2_taxes}, index=self.years)

        return co2_taxes_df
    def setup_usecase(self):

        hydrogen_name = GaseousHydrogen.name
        liquid_fuel_name = LiquidFuel.name
        high_heat_name = hightemperatureheat.name
        medium_heat_name = mediumtemperatureheat.name
        methane_name = Methane.name
        biogas_name = BioGas.name
        electricity_name = Electricity.name
        energy_mix_name = EnergyMix.name
        energy_price_dict = {GlossaryEnergy.Years: self.years,
                             electricity_name: 9.0,
                             biogas_name: 90,
                             methane_name: 34.0,
                             hydrogen_name: 90.0,
                             liquid_fuel_name: 70.0,
                             high_heat_name: 71.0,
                             medium_heat_name: 71.0,
                             }

        # price in $/MWh
        self.energy_prices = pd.DataFrame({key: value for key, value in energy_price_dict.items(
        ) if key in self.techno_dict or key == GlossaryEnergy.Years})

        self.energy_prices[methane_name] = 34.0
        self.energy_prices[electricity_name] = 9.0
        self.energy_prices[hydrogen_name] = 90.0

        energy_carbon_emissions_dict = {GlossaryEnergy.Years: self.years,
                                        electricity_name: 0.0,
                                        biogas_name: -0.618,
                                        methane_name: 0.123 / 15.4,
                                        hydrogen_name: 0.0,
                                        liquid_fuel_name: 0.0,
                                        high_heat_name: 0.0,
                                        medium_heat_name: 0.0,
                                        }
        # price in $/MWh
        # self.energy_carbon_emissions = pd.DataFrame(
        #     {key: value for key, value in energy_carbon_emissions_dict.items() if
        #      key in self.techno_dict or key == GlossaryEnergy.Years})
        # self.energy_carbon_emissions[methane_name] = 0.123 / 15.4
        # # --- resources price and co2 emissions
        # self.resources_CO2_emissions = get_static_CO2_emissions(self.years)
        # self.resources_prices = get_static_prices(self.years)

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

        self.co2_taxes = self.get_co2_taxes_df_custom()

        values_dict = {
            f'{self.study_name}.{GlossaryEnergy.EnergyInvestmentsValue}': invest_df,
            f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.EnergyInvestmentsValue}': invest_df,
            # f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.InvestLevelValue}': invest_df,
            f'{self.study_name}.{GlossaryEnergy.YearStart}': self.year_start,
            f'{self.study_name}.{GlossaryEnergy.YearEnd}': self.year_end,
            f'{self.study_name}.{GlossaryEnergy.energy_list}': self.energy_list,
            # f'{self.study_name}.{GlossaryEnergy.ccs_list}': self.ccs_list,
            f'{self.study_name}.{GlossaryEnergy.EnergyPricesValue}': self.energy_prices,
            f'{self.study_name}.{energy_mix_name}.{GlossaryEnergy.EnergyPricesValue}': self.energy_prices,
            f'{self.study_name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
            f'{self.study_name}.is_stream_demand': True,
            f'{self.study_name}.max_mda_iter': 10,
            f'{self.study_name}.sub_mda_class': 'MDAGaussSeidel',
        }

        values_dict_list,  instanciated_studies = self.setup_usecase_sub_study_list()

        invest_mix_df = self.get_total_mix(
            instanciated_studies)
        print('')
        print(invest_mix_df.to_string())
        values_dict.update(
            {f'{self.study_name}.{INVEST_DISC_NAME}.{GlossaryEnergy.invest_mix}': invest_mix_df})

        # The flue gas list will depend on technologies present in the
        # techno_dict
        # possible_technos = [f'{energy}.{techno}' for energy, tech_dict in self.techno_dict.items(
        # ) for techno in tech_dict['value']]

        values_dict_list.append(values_dict)

        # self.create_technolist_per_energy(instanciated_studies)

        return values_dict_list


    # def get_sub_usecase_instances(self):
    #     self.techno_usecases = {}
    #     for techno, UseCase in DEFAULT_TECHNO_DICT.items():
    #         uc_instance = UseCase()
    #         uc_instance.study_name = self.study_name
    #         self.ns_public = self.study_name
    #         self.ns_mix = f"{self.study_name}.{self.heat_mix}"
    #         self.ns_functions = self.ns_mix
    #         ns_asset = f"{self.ns_mix}.{techno}"
    #         uc_instance.ns_public = self.ns_public
    #         uc_instance.ns_mix = self.ns_mix
    #         uc_instance.ns_asset = ns_asset
    #         self.techno_usecases[techno] = uc_instance

    # def setup_usecase(self):
    #     self.get_sub_usecase_instances()
    #
    #     self.selling_price_strategy = Glossary.FixedMarginStrategy
    #     years_countries = [Glossary.Years, Glossary.Country]
    #
    #     values_dict = {f"{self.ns_mix}.{Glossary.TechnologyList['var_name']}": list(self.techno_usecases.keys())}
    #     shared_dict = {
    #         f"{self.ns_public}.{Glossary.CountryParameters['var_name']}":
    #             pd.DataFrame(),
    #         f"{self.ns_public}.{Glossary.CountryEnergyInfo['var_name']}":
    #             pd.DataFrame(),
    #     }
    #
    #     for techno, uc_instance in self.techno_usecases.items():
    #
    #         values_dict.update(uc_instance.setup_usecase()[0])
    #         self.techno_heat_dict[techno] = values_dict[f'{self.study_name}.AssetMix.{techno}.techno_asset_list']
    #         for _k, shared_df in shared_dict.items():
    #             shared_dict[_k] = pd.concat((shared_df, values_dict[_k])
    #                                         ).dropna().drop_duplicates(subset=years_countries, keep='last'
    #                                                                    ).reset_index(drop=True)
    #
    #     shared_dict.update({
    #         f"{self.ns_public}.{Glossary.YearsVariable['var_name']}": self.years,
    #         f"{self.ns_public}.{Glossary.SellingPriceStrategy['var_name']}": self.selling_price_strategy,
    #         f"{self.ns_mix}.{Glossary.WACCFormula['var_name']}": 'Vanilla',
    #         f"{self.ns_mix}.{Glossary.EnergyProductionIncrementsGrowthRate['var_name']}": np.array(
    #             [0.] * (len(self.years) - 1)),
    #         f"{self.ns_mix}.{Glossary.CO2EmissionsIncrementsGrowthRate['var_name']}": np.array(
    #             [0.] * (len(self.years) - 1)),
    #     })
    #     values_dict.update(shared_dict)
    #
    #     return [values_dict]


if '__main__' == __name__:
    uc_cls = Study()
    uc_cls.load_data()
    uc_cls.run()
