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
import numpy as np
import pandas as pd

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.energy_process_builder import (
    INVEST_DISCIPLINE_OPTIONS,
)
from energy_models.core.energy_study_manager import (
    AGRI_TYPE,
    EnergyStudyManager,
    DEFAULT_TECHNO_DICT,
    CCUS_TYPE,
    ENERGY_TYPE,
)
from sostrades_core.execution_engine.func_manager.func_manager import FunctionManager
from sostrades_core.execution_engine.func_manager.func_manager_disc import FunctionManagerDisc
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.carbon_models.carbon_storage import CarbonStorage
from energy_models.core.stream_type.carbon_models.flue_gas import FlueGas
from energy_models.core.stream_type.energy_models.biodiesel import BioDiesel
from energy_models.core.stream_type.energy_models.biogas import BioGas
from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.ethanol import Ethanol
from energy_models.core.stream_type.energy_models.fossil import Fossil
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import (
    GaseousHydrogen,
)
from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from energy_models.core.stream_type.energy_models.heat import lowtemperatureheat
from energy_models.core.stream_type.energy_models.heat import mediumtemperatureheat
from energy_models.core.stream_type.energy_models.hydrotreated_oil_fuel import (
    HydrotreatedOilFuel,
)
from energy_models.core.stream_type.energy_models.liquid_fuel import LiquidFuel
from energy_models.core.stream_type.energy_models.liquid_hydrogen import LiquidHydrogen
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.energy_models.renewable import Renewable
from energy_models.core.stream_type.energy_models.solid_fuel import SolidFuel
from energy_models.core.stream_type.energy_models.syngas import Syngas
from energy_models.core.stream_type.resources_data_disc import (
    get_static_CO2_emissions,
    get_static_prices,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.sos_processes.energy.techno_mix.carbon_capture_mix.usecase import (
    DEFAULT_FLUE_GAS_LIST,
)

INVEST_DISC_NAME = "InvestmentDistribution"


class Study(EnergyStudyManager):
    def __init__(
            self,
            file_path=__file__,
            year_start=GlossaryEnergy.YeartStartDefault,
            year_end=2050,
            main_study=True,
            bspline=True,
            execution_engine=None,
            use_utilisation_ratio: bool = False,
            techno_dict=DEFAULT_TECHNO_DICT
    ):
        super().__init__(
            file_path=file_path,
            run_usecase=True,
            main_study=main_study,
            execution_engine=execution_engine,
            techno_dict=techno_dict,
        )
        self.year_start = year_start
        self.year_end = year_end
        self.time_step = 1
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.dict_technos = {}
        self.coupling_name = "MDA"

        self.lower_bound_techno = 1.0e-6
        self.upper_bound_techno = 3000

        self.sub_study_dict = None
        self.sub_study_path_dict = None
        self.use_utilisation_ratio = use_utilisation_ratio

        self.create_study_list()
        self.bspline = bspline
        self.invest_discipline = INVEST_DISCIPLINE_OPTIONS[2]

    def create_study_list(self):
        self.sub_study_dict = {}
        self.sub_study_path_dict = {}
        for energy in self.energy_list + self.ccs_list:
            cls, path = self.get_energy_mix_study_cls(energy)
            self.sub_study_dict[energy] = cls
            self.sub_study_path_dict[energy] = path

    def get_investments_mix(self):
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
        if self.coarse_mode:
            years = np.arange(GlossaryEnergy.NB_POLES_COARSE)
        else:
            years = np.arange(GlossaryEnergy.NB_POLES_FULL)

        invest_energy_mix_dict = {
            GlossaryEnergy.Years: years,
            Electricity.name: [4.49, 35, 35, 35, 35, 35, 35, 35],
            BioGas.name: [0.05, 2.0, 1.8, 1.3, 1.0, 0.1, 0.01, 0.01],
            BiomassDry.name: [0.003, 0.5, 1.0, 1.0, 1.0, 0.8, 0.8, 0.8],
            Methane.name: [1.2, 0.5, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0],
            GaseousHydrogen.name: [0.02, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            LiquidFuel.name: [3.15, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            hightemperatureheat.name: [3.15, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            mediumtemperatureheat.name: [3.15, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            lowtemperatureheat.name: [3.15, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            SolidFuel.name: [0.00001, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01],
            BioDiesel.name: [0.02, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            Syngas.name: [1.005, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            LiquidHydrogen.name: [0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            HydrotreatedOilFuel.name: [3.15, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            Ethanol.name: [0.02, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            Renewable.name: np.linspace(1000.0, 15.625, len(years)),
            Fossil.name: np.linspace(1500.0, 77.5, len(years)),
        }

        if self.bspline:
            invest_energy_mix_dict[GlossaryEnergy.Years] = self.years

            for energy in self.energy_list:
                invest_energy_mix_dict[energy], _ = self.invest_bspline(invest_energy_mix_dict[energy], len(self.years))

        energy_mix_invest_df = pd.DataFrame(
            {
                key: value
                for key, value in invest_energy_mix_dict.items()
                if key in self.energy_list or key == GlossaryEnergy.Years
            }
        )

        return energy_mix_invest_df

    def get_investments_ccs_mix(self):
        if self.coarse_mode:
            invest_ccs_mix_dict = {
                GlossaryEnergy.Years: np.arange(GlossaryEnergy.NB_POLES_COARSE),
                CarbonCapture.name: np.ones(GlossaryEnergy.NB_POLES_COARSE),
                CarbonStorage.name: np.ones(GlossaryEnergy.NB_POLES_COARSE),
            }

        else:
            invest_ccs_mix_dict = {
                GlossaryEnergy.Years: np.arange(GlossaryEnergy.NB_POLES_FULL),
                CarbonCapture.name: [2.0] + [25] * (GlossaryEnergy.NB_POLES_FULL - 1),
                CarbonStorage.name: [0.003] + [5] * (GlossaryEnergy.NB_POLES_FULL - 1),
            }

        if self.bspline:
            invest_ccs_mix_dict[GlossaryEnergy.Years] = self.years
            for ccs in self.ccs_list:
                invest_ccs_mix_dict[ccs], _ = self.invest_bspline(invest_ccs_mix_dict[ccs], len(self.years))

        ccs_mix_invest_df = pd.DataFrame(invest_ccs_mix_dict)

        return ccs_mix_invest_df

    def get_total_mix(self, instanciated_studies):
        """
        Get the total mix of each techno with the invest distribution discipline
         with ccs percentage, mixes by energy and by techno
        """
        energy_mix = self.get_investments_mix()
        invest_mix_df = pd.DataFrame({GlossaryEnergy.Years: energy_mix[GlossaryEnergy.Years].values})

        ccs_mix = self.get_investments_ccs_mix()
        for study in instanciated_studies:
            if study is not None:
                invest_techno = study.get_investments()
                energy = study.energy_name
                if energy in energy_mix.columns:
                    pass
                elif energy in ccs_mix.columns:
                    pass
                else:
                    raise Exception(f"{energy} not in investment_mixes")
                for techno in invest_techno.columns:
                    if techno != GlossaryEnergy.Years:
                        invest_mix_df[f"{energy}.{techno}"] = invest_techno[techno].values

        return invest_mix_df

    def get_absolute_total_mix(self, instanciated_studies):

        invest_mix_df = self.get_total_mix(instanciated_studies)

        indep_invest_df = pd.DataFrame({GlossaryEnergy.Years: invest_mix_df[GlossaryEnergy.Years].values})
        for column in invest_mix_df.columns:
            if column != GlossaryEnergy.Years:
                indep_invest_df[column] = invest_mix_df[column].values

        return indep_invest_df

    def setup_usecase_sub_study_list(self, merge_design_spaces=False):
        """
        Instantiate sub studies and values dict from setup_usecase
        """
        values_dict_list = []
        instanced_sub_studies = []
        dspace_list = []
        for sub_study_name, sub_study in self.sub_study_dict.items():
            if self.techno_dict[sub_study_name]["type"] == CCUS_TYPE:
                prefix_name = f"{self.coupling_name}.{GlossaryEnergy.CCUS}"
                instance_sub_study = sub_study(
                    self.year_start,
                    self.year_end,
                    bspline=self.bspline,
                    main_study=False,
                    prefix_name=prefix_name,
                    execution_engine=self.execution_engine,
                    invest_discipline=self.invest_discipline,
                    technologies_list=self.techno_dict[sub_study_name]["value"],
                )
            elif self.techno_dict[sub_study_name]["type"] == ENERGY_TYPE:
                instance_sub_study = sub_study(
                    self.year_start,
                    self.year_end,
                    bspline=self.bspline,
                    main_study=False,
                    execution_engine=self.execution_engine,
                    invest_discipline=self.invest_discipline,
                    technologies_list=self.techno_dict[sub_study_name]["value"],
                )
            elif self.techno_dict[sub_study_name]["type"] == AGRI_TYPE:
                pass
            else:
                raise Exception(
                    f"The type of {sub_study_name} : {self.techno_dict[sub_study_name]['type']} is not in [{ENERGY_TYPE},{CCUS_TYPE},{AGRI_TYPE}]"
                )
            if self.techno_dict[sub_study_name]["type"] != AGRI_TYPE:
                instance_sub_study.configure_ds_boundaries(
                    lower_bound_techno=self.lower_bound_techno,
                    upper_bound_techno=self.upper_bound_techno,
                )
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

    def create_technolist_per_energy(self, instanciated_studies):
        self.dict_technos = {}
        dict_studies = dict(zip(self.energy_list + self.ccs_list, instanciated_studies))

        for energy_name, study_val in dict_studies.items():
            if study_val is not None:
                self.dict_technos[energy_name] = study_val.technologies_list
            else:
                # the study_val == None is for the biomass_dry that is taken into account with the agriculture_mix
                # so it has no dedicated technology in the energy_mix
                self.dict_technos[energy_name] = []

    def get_dvar_dscriptor(self):
        """Returns design variable descriptor based on techno list"""
        design_var_descriptor = {}
        for energy in self.energy_list:
            energy_wo_dot = energy.replace('.', '_')
            for technology in self.dict_technos[energy]:
                technology_wo_dot = technology.replace('.', '_')

                design_var_descriptor[f'{energy}.{technology}.{energy_wo_dot}_{technology_wo_dot}_array_mix'] = {
                    'out_name': GlossaryEnergy.invest_mix,
                    'out_type': 'dataframe',
                    'key': f'{energy}.{technology}',
                    'index': self.years,
                    'index_name': GlossaryEnergy.Years,
                    'namespace_in': GlossaryEnergy.NS_ENERGY_MIX,
                    'namespace_out': 'ns_invest'
                }
                if self.use_utilisation_ratio:
                    design_var_descriptor[f'{energy}.{technology}.utilization_ratio_array'] = {
                        'out_name': f'{energy}.{technology}.{GlossaryEnergy.UtilisationRatioValue}',
                        'out_type': 'dataframe',
                        'key': GlossaryEnergy.UtilisationRatioValue,
                        'index': self.years,
                        'index_name': GlossaryEnergy.Years,
                        'namespace_in': GlossaryEnergy.NS_ENERGY_MIX,
                        'namespace_out': GlossaryEnergy.NS_WITNESS
                    }


        for ccs in self.ccs_list:
            ccs_wo_dot = ccs.replace('.', '_')
            for technology in self.dict_technos[ccs]:
                technology_wo_dot = technology.replace('.', '_')

                design_var_descriptor[f'{ccs}.{technology}.{ccs_wo_dot}_{technology_wo_dot}_array_mix'] = {
                    'out_name': GlossaryEnergy.invest_mix,
                    'out_type': 'dataframe',
                    'key': f'{ccs}.{technology}',
                    'index': self.years,
                    'index_name': GlossaryEnergy.Years,
                    'namespace_in': GlossaryEnergy.NS_CCS,
                    'namespace_out': 'ns_invest'
                }

                if self.use_utilisation_ratio:
                    # add design variable for utilization ratio per technology
                    design_var_descriptor[f'{ccs}.{technology}.utilization_ratio_array'] = {
                        'out_name': f'{ccs}.{technology}.{GlossaryEnergy.UtilisationRatioValue}',
                        'out_type': 'dataframe',
                        'key': GlossaryEnergy.UtilisationRatioValue,
                        'index': self.years,
                        'index_name': GlossaryEnergy.Years,
                        'namespace_in': GlossaryEnergy.NS_CCS,
                        'namespace_out': GlossaryEnergy.NS_WITNESS
                    }

        return design_var_descriptor

    def get_dspace(self):
        """returns design space"""
        invest_mix_dict = self.get_investments_mix()

        for energy in self.energy_list:
            energy_wodot = energy.replace('.', '_')
            techno_list = self.techno_dict[energy]
            for techno in techno_list:
                techno_wo_dot = techno.replace('.', '_')
                self.update_dspace_dict_with(
                    f'{energy}.{techno}.{energy_wodot}_{techno_wo_dot}_array_mix', np.maximum(
                        self.lower_bound_techno, invest_mix_dict[techno].values),
                    self.lower_bound_techno, self.upper_bound_techno, enable_variable=True)

    def make_dspace_invests(self, dspace_list: list) -> pd.DataFrame:
        dspaces_cleaned = []
        for ds in dspace_list:
            ds.pop('dspace_size')
            for var_name, sub_ds_dict in ds.items():
                sub_ds_dict['variable'] = var_name
                ds_value = {var_name: sub_ds_dict}
                dspaces_cleaned.append(pd.DataFrame(ds_value).T)

        dspace = pd.concat(dspaces_cleaned)
        return dspace

    def make_dspace_utilisation_ratio(self) -> pd.DataFrame:
        variables = []
        for energy_or_ccs in self.energy_list + self.ccs_list:
            for techno in self.dict_technos[energy_or_ccs]:
                variables.append(
                    f"{energy_or_ccs}.{techno}.utilization_ratio_array"
                )
        low_bound = [1e-6] * GlossaryEnergy.NB_POLES_UTILIZATION_RATIO
        upper_bound = [100.] * GlossaryEnergy.NB_POLES_UTILIZATION_RATIO
        value = [100.] * GlossaryEnergy.NB_POLES_UTILIZATION_RATIO
        n_dvar_ur = len(variables)
        dspace_ur = {
            'variable': variables,
            'value': [value] * n_dvar_ur,
            'activated_elem': [[True] * GlossaryEnergy.NB_POLES_UTILIZATION_RATIO] * n_dvar_ur,
            'lower_bnd': [low_bound] * n_dvar_ur,
            'upper_bnd': [upper_bound] * n_dvar_ur,
            'enable_variable': [True] * n_dvar_ur
        }

        dspace_ur = pd.DataFrame(dspace_ur)
        return dspace_ur

    def make_func_df(self):
        func_df = pd.DataFrame({
            "variable": [GlossaryEnergy.CO2EmissionsObjectiveValue, GlossaryEnergy.TargetProductionConstraintValue, GlossaryEnergy.MaxBudgetConstraintValue,],
            "parent": ["objectives", "constraints", "constraints"],
            "ftype": [FunctionManagerDisc.OBJECTIVE, FunctionManagerDisc.INEQ_CONSTRAINT, FunctionManagerDisc.INEQ_CONSTRAINT] ,
            "weight": [1.0, 0.0, 0.0,],
            FunctionManagerDisc.AGGR_TYPE: [FunctionManager.AGGR_TYPE_SUM, FunctionManager.AGGR_TYPE_SUM, FunctionManager.AGGR_TYPE_SUM,],
            "namespace": [GlossaryEnergy.NS_FUNCTIONS, GlossaryEnergy.NS_FUNCTIONS, GlossaryEnergy.NS_FUNCTIONS,]
        })
        return func_df

    def get_dvar_values(self, dspace):
        out_dict = {}

        for ccs in self.ccs_list:
            ccs_wo_dot = ccs.replace('.', '_')
            for technology in self.dict_technos[ccs]:
                technology_wo_dot = technology.replace('.', '_')
                array_invest_var_name = f"{ccs}.{technology}.{ccs_wo_dot}_{technology_wo_dot}_array_mix"
                value = dspace.loc[dspace['variable'] == array_invest_var_name, 'value'].values[0]
                out_dict.update({
                    f"{self.study_name}.{self.coupling_name}.{GlossaryEnergy.CCUS}.{array_invest_var_name}": np.array(value)
                })

                if self.use_utilisation_ratio:
                    array_utilization_ratio_var_name = f"{ccs}.{technology}.utilization_ratio_array"
                    value = dspace.loc[dspace['variable'] == array_utilization_ratio_var_name, 'value'].values[0]
                    out_dict.update({
                        f"{self.study_name}.{self.coupling_name}.{GlossaryEnergy.CCUS}.{ccs}.{technology}.utilization_ratio_array": np.array(value)
                    })

        for energy in self.energy_list:
            energy_wo_dot = energy.replace('.', '_')
            for technology in self.dict_technos[energy]:
                technology_wo_dot = technology.replace('.', '_')

                array_invest_var_name = f"{energy}.{technology}.{energy_wo_dot}_{technology_wo_dot}_array_mix"
                value = dspace.loc[dspace['variable'] == array_invest_var_name, 'value'].values[0]
                out_dict.update({
                    f"{self.study_name}.{self.coupling_name}.EnergyMix.{array_invest_var_name}": np.array(value)
                })

                if self.use_utilisation_ratio:
                    array_utilization_ratio_var_name = f"{energy}.{technology}.utilization_ratio_array"
                    value = dspace.loc[dspace['variable'] == array_utilization_ratio_var_name, 'value'].values[0]
                    out_dict.update({
                        f"{self.study_name}.{self.coupling_name}.EnergyMix.{energy}.{technology}.utilization_ratio_array": np.array(
                            value)
                    })

        return out_dict

    def make_dspace(self, dspace_list: list):
        dspace = self.make_dspace_invests(dspace_list)
        if self.use_utilisation_ratio:
            dspace_utilisation_ratio = self.make_dspace_utilisation_ratio()
            dspace = pd.concat([dspace, dspace_utilisation_ratio])
        dspace.reset_index(drop=True, inplace=True)
        return dspace

    def get_input_value_from_agriculture_mix(self):
        agri_mix_name = "AgricultureMix"

        N2O_per_use = pd.DataFrame({GlossaryEnergy.Years: self.years, "N2O_per_use": 5.34e-5})
        CH4_per_use = pd.DataFrame({GlossaryEnergy.Years: self.years, "CH4_per_use": 0.0})
        CO2_per_use = pd.DataFrame({GlossaryEnergy.Years: self.years, "CO2_per_use": 0.277})

        energy_consumption = pd.DataFrame({GlossaryEnergy.Years: self.years, "CO2_resource (Mt)": 3.5})
        energy_production = pd.DataFrame({GlossaryEnergy.Years: self.years, GlossaryEnergy.biomass_dry: 12.5})
        energy_prices = pd.DataFrame(
            {
                GlossaryEnergy.Years: self.years,
                GlossaryEnergy.biomass_dry: 9.8,
                "biomass_dry_wotaxes": 9.8,
            }
        )

        land_use_required = pd.DataFrame({GlossaryEnergy.Years: self.years, "Crop (GHa)": 0.07, "Forest (Gha)": 1.15})

        CO2_emissions = pd.DataFrame({GlossaryEnergy.Years: self.years, GlossaryEnergy.biomass_dry: -0.277})

        energy_type_capital = pd.DataFrame({GlossaryEnergy.Years: self.years, GlossaryEnergy.Capital: 0.0})

        agri_values_dict = {
            f"{self.study_name}.{self.coupling_name}.{agri_mix_name}.N2O_per_use": N2O_per_use,
            f"{self.study_name}.{self.coupling_name}.{agri_mix_name}.CH4_per_use": CH4_per_use,
            f"{self.study_name}.{self.coupling_name}.{agri_mix_name}.CO2_per_use": CO2_per_use,
            f"{self.study_name}.{self.coupling_name}.{agri_mix_name}.{GlossaryEnergy.EnergyConsumptionValue}": energy_consumption,
            f"{self.study_name}.{self.coupling_name}.{agri_mix_name}.{GlossaryEnergy.EnergyConsumptionWithoutRatioValue}": energy_consumption,
            f"{self.study_name}.{self.coupling_name}.{agri_mix_name}.{GlossaryEnergy.EnergyProductionValue}": energy_production,
            f"{self.study_name}.{self.coupling_name}.EnergyMix.{agri_mix_name}.{GlossaryEnergy.EnergyTypeCapitalDfValue}": energy_type_capital,
            f"{self.study_name}.{self.coupling_name}.{agri_mix_name}.{GlossaryEnergy.EnergyPricesValue}": energy_prices,
            f"{self.study_name}.{self.coupling_name}.{agri_mix_name}.{GlossaryEnergy.LandUseRequiredValue}": land_use_required,
            f"{self.study_name}.{self.coupling_name}.{agri_mix_name}.{GlossaryEnergy.CO2EmissionsValue}": CO2_emissions,

        }

        return agri_values_dict

    def setup_usecase(self, study_folder_path=None):

        energy_mix_name = EnergyMix.name

        # price in $/MWh
        energy_prices = pd.DataFrame(
            {
                GlossaryEnergy.Years: self.years,
                Electricity.name: 9.0,
                BiomassDry.name: 68.12 / 3.36,
                BioGas.name: 90,
                Methane.name: 34.0,
                SolidFuel.name: 8.6,
                GaseousHydrogen.name: 90.0,
                LiquidFuel.name: 70.0,
                hightemperatureheat.name: 71.0,
                mediumtemperatureheat.name: 71.0,
                lowtemperatureheat.name: 71.0,
                Syngas.name: 40.0,
                CarbonCapture.name: 0.0,
                CarbonStorage.name: 0.0,
                BioDiesel.name: 210.0,
                LiquidHydrogen.name: 120.0,
                Renewable.name: 90.0,
                Fossil.name: 110.0,
                HydrotreatedOilFuel.name: 70.0,
            }
        )

        co2_taxes = pd.DataFrame({GlossaryEnergy.Years: self.years, GlossaryEnergy.CO2Tax: 750})

        # price in $/MWh
        energy_carbon_emissions = pd.DataFrame(
            {
                GlossaryEnergy.Years: self.years,
                Electricity.name: 0.0,
                BiomassDry.name: -0.425 * 44.01 / 12.0 / 3.36,
                BioGas.name: -0.618,
                Methane.name: 0.123 / 15.4,
                SolidFuel.name: 0.64 / 4.86,
                GaseousHydrogen.name: 0.0,
                LiquidFuel.name: 0.0,
                hightemperatureheat.name: 0.0,
                mediumtemperatureheat.name: 0.0,
                lowtemperatureheat.name: 0.0,
                Syngas.name: 0.0,
                CarbonCapture.name: 0.0,
                CarbonStorage.name: 0.0,
                BioDiesel.name: 0.0,
                LiquidHydrogen.name: 0.0,
                Renewable.name: 0.0,
                Fossil.name: 0.64 / 4.86,
                HydrotreatedOilFuel.name: 0.0,
            }
        )

        resources_CO2_emissions = get_static_CO2_emissions(self.years)
        resources_prices = get_static_prices(self.years)

        all_streams_demand_ratio = {GlossaryEnergy.Years: self.years}
        all_streams_demand_ratio.update({energy: 100.0 for energy in self.energy_list})
        all_streams_demand_ratio = pd.DataFrame(all_streams_demand_ratio)

        forest_invest_df = pd.DataFrame({GlossaryEnergy.Years: self.years, GlossaryEnergy.ForestInvestmentValue: 5})

        co2_land_emissions = pd.DataFrame({
            GlossaryEnergy.Years: self.years
        })

        CO2_indus_emissions_df = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            "indus_emissions": 0.
        })


        target_energy_prod = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.TargetEnergyProductionValue: np.geomspace(1, 150 * 1e3, len(self.years))
        })

        max_invest = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.MaxBudgetValue: np.geomspace(3000, 6000, len(self.years))
        })

        values_dict = {
            f"{self.study_name}.{GlossaryEnergy.YearStart}": self.year_start,
            f"{self.study_name}.{GlossaryEnergy.YearEnd}": self.year_end,
            f"{self.study_name}.{GlossaryEnergy.energy_list}": self.energy_list,
            f"{self.study_name}.{GlossaryEnergy.ccs_list}": self.ccs_list,
            f"{self.study_name}.{self.coupling_name}.{energy_mix_name}.{GlossaryEnergy.EnergyPricesValue}": energy_prices,
            f"{self.study_name}.{GlossaryEnergy.CO2TaxesValue}": co2_taxes,
            f"{self.study_name}.{self.coupling_name}.{energy_mix_name}.{GlossaryEnergy.EnergyCO2EmissionsValue}": energy_carbon_emissions,
            f"{self.study_name}.{self.coupling_name}.{energy_mix_name}.{GlossaryEnergy.AllStreamsDemandRatioValue}": all_streams_demand_ratio,
            f"{self.study_name}.is_stream_demand": True,
            f"{self.study_name}.max_mda_iter": 50,
            f"{self.study_name}.sub_mda_class": "MDAGaussSeidel",
            f"{self.study_name}.{self.coupling_name}.{energy_mix_name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}": resources_CO2_emissions,
            f"{self.study_name}.{self.coupling_name}.{energy_mix_name}.{GlossaryEnergy.ResourcesPriceValue}": resources_prices,
            f"{self.study_name}.{self.coupling_name}.{energy_mix_name}.{GlossaryEnergy.TargetEnergyProductionValue}": target_energy_prod,
            f"{self.study_name}.{self.coupling_name}.{energy_mix_name}.{GlossaryEnergy.MaxBudgetValue}": max_invest,
            f"{self.study_name}.{self.coupling_name}.InvestmentDistribution.{GlossaryEnergy.ForestInvestmentValue}": forest_invest_df,
            f"{self.study_name}.{self.coupling_name}.CO2_land_emissions": co2_land_emissions,
            f"{self.study_name}.{self.coupling_name}.CH4_land_emissions": co2_land_emissions,
            f"{self.study_name}.{self.coupling_name}.N2O_land_emissions": co2_land_emissions,
            f"{self.study_name}.{self.coupling_name}.CO2_indus_emissions_df": CO2_indus_emissions_df,
        }

        (
            values_dict_list,
            dspace_list,
            instanciated_studies,
        ) = self.setup_usecase_sub_study_list()

        # The flue gas list will depend on technologies present in the
        # techno_dict
        possible_technos = [
            f"{energy}.{techno}" for energy, tech_dict in self.techno_dict.items() for techno in tech_dict["value"]
        ]
        flue_gas_list = [techno for techno in DEFAULT_FLUE_GAS_LIST if techno in possible_technos]

        if CarbonCapture.name in DEFAULT_TECHNO_DICT:
            values_dict[
                f"{self.study_name}.{GlossaryEnergy.CCUS}.{CarbonCapture.name}.{FlueGas.node_name}.{GlossaryEnergy.techno_list}"
            ] = flue_gas_list

        if self.coarse_mode:
            values_dict.update({f"{self.study_name}.{self.coupling_name}.EnergyMix.heat_losses_percentage": 0.0})
        invest_mix_df = self.get_absolute_total_mix(instanciated_studies)

        managed_wood_investment = pd.DataFrame({GlossaryEnergy.Years: self.years, GlossaryEnergy.InvestmentsValue: 0.0})

        deforestation_investment = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.InvestmentsValue: 0.0}
        )

        crop_investment = pd.DataFrame({GlossaryEnergy.Years: self.years, GlossaryEnergy.InvestmentsValue: 0.0})

        values_dict.update({
             f"{self.study_name}.{self.coupling_name}.{INVEST_DISC_NAME}.{GlossaryEnergy.invest_mix}": invest_mix_df,
        })

        values_dict_list.append(values_dict)

        self.create_technolist_per_energy(instanciated_studies)

        possible_technos = [
            f"{energy}.{techno}"
            for energy, tech_dict in self.techno_dict.items()
            for techno in tech_dict["value"]
        ]
        flue_gas_list = [
            techno for techno in DEFAULT_FLUE_GAS_LIST if techno in possible_technos
        ]

        if CarbonCapture.name in DEFAULT_TECHNO_DICT:
            values_dict[
                f"{self.study_name}.{self.coupling_name}.{GlossaryEnergy.CCUS}.{CarbonCapture.name}.{FlueGas.node_name}.{GlossaryEnergy.techno_list}"
            ] = flue_gas_list

        if not self.coarse_mode:
            agri_values_dict = self.get_input_value_from_agriculture_mix()
            values_dict_list.append(agri_values_dict)

            values_dict.update({
                 f"{self.study_name}.{self.coupling_name}.{INVEST_DISC_NAME}.{GlossaryEnergy.invest_mix}": invest_mix_df,
                f"{self.study_name}.{self.coupling_name}.{INVEST_DISC_NAME}.{GlossaryEnergy.ManagedWoodInvestmentName}": managed_wood_investment,
                f"{self.study_name}.{self.coupling_name}.{INVEST_DISC_NAME}.{GlossaryEnergy.DeforestationInvestmentName}": deforestation_investment,
                f"{self.study_name}.{self.coupling_name}.{INVEST_DISC_NAME}.{GlossaryEnergy.CropInvestmentName}": crop_investment,
            })

        design_var_descriptor = self.get_dvar_dscriptor()
        # self.get_dspace()

        values_dict_list_, dspace_list, instanced_sub_studies = self.setup_usecase_sub_study_list()
        func_df = self.make_func_df()
        dspace = self.make_dspace(dspace_list)
        values_mdo = {
            f"{self.study_name}.{self.coupling_name}.DesignVariables.design_var_descriptor": design_var_descriptor,
            f"{self.study_name}.design_space": dspace,
            f"{self.study_name}.{self.coupling_name}.FunctionsManager.function_df": func_df,
            f"{self.study_name}.{self.coupling_name}.max_mda_iter": 200,
            f"{self.study_name}.{self.coupling_name}.sub_mda_class": "MDANewtonRaphson",
        }

        dvar_values = self.get_dvar_values(dspace)
        values_mdo.update(dvar_values)
        values_dict_list.append(values_mdo)

        return values_dict_list


if "__main__" == __name__:
    uc_cls = Study()
    #uc_cls.execution_engine.display_treeview_nodes(display_variables=True)
    uc_cls.load_data()
    uc_cls.run()
