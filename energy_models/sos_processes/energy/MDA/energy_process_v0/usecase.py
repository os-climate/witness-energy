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

from climateeconomics.sos_processes.iam.witness.resources_process.usecase import (
    Study as datacase_resource,
)
from energy_models.core.demand.energy_demand_disc import EnergyDemandDiscipline
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.energy_process_builder import (
    INVEST_DISCIPLINE_DEFAULT,
    INVEST_DISCIPLINE_OPTIONS,
)
from energy_models.core.energy_study_manager import (
    AGRI_TYPE,
    EnergyStudyManager,
    DEFAULT_TECHNO_DICT,
    CCUS_TYPE,
    ENERGY_TYPE,
)
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
from energy_models.models.carbon_storage.pure_carbon_solid_storage.pure_carbon_solid_storage import (
    PureCarbonSS,
)
from energy_models.sos_processes.energy.techno_mix.carbon_capture_mix.usecase import (
    DEFAULT_FLUE_GAS_LIST,
)
from sostrades_core.execution_engine.func_manager.func_manager import FunctionManager
from sostrades_core.execution_engine.func_manager.func_manager_disc import FunctionManagerDisc

INVEST_DISC_NAME = "InvestmentDistribution"


class Study(EnergyStudyManager):
    def __init__(
            self,
            year_start=GlossaryEnergy.YearStartDefault,
            year_end=GlossaryEnergy.YearEndDefault,
            time_step=1,
            lower_bound_techno=1.0e-6,
            upper_bound_techno=100.0,
            techno_dict=DEFAULT_TECHNO_DICT,
            main_study=True,
            bspline=True,
            execution_engine=None,
            invest_discipline=INVEST_DISCIPLINE_DEFAULT,
            energy_invest_input_in_abs_value=True,
    ):
        self.year_start = year_start
        self.year_end = year_end
        self.time_step = time_step
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.dict_technos = {}

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
        super().__init__(
            __file__,
            main_study=main_study,
            execution_engine=execution_engine,
            techno_dict=techno_dict,
        )

        self.create_study_list()
        self.bspline = bspline
        self.invest_discipline = invest_discipline
        self.energy_invest_input_in_abs_value = energy_invest_input_in_abs_value

    def create_study_list(self):
        self.sub_study_dict = {}
        self.sub_study_path_dict = {}
        for energy in self.energy_list + self.ccs_list:
            cls, path = self.get_energy_mix_study_cls(energy)
            self.sub_study_dict[energy] = cls
            self.sub_study_path_dict[energy] = path

    def setup_objectives(self):

        func_df = pd.DataFrame({
            "variable": ["energy_production_objective", "syngas_prod_objective"],
            "parent": ["objectives", "objectives"],
            "ftype": [FunctionManagerDisc.OBJECTIVE, FunctionManagerDisc.OBJECTIVE],
            "weight": [0.0, 0.0],
            FunctionManagerDisc.AGGR_TYPE: [FunctionManager.AGGR_TYPE_SUM, FunctionManager.AGGR_TYPE_SUM],
            "namespace": [GlossaryEnergy.NS_FUNCTIONS, GlossaryEnergy.NS_FUNCTIONS]
        })

        return func_df

    def setup_constraints(self):

        func_df = pd.DataFrame(
            columns=["variable", "parent", "ftype", "weight", FunctionManagerDisc.AGGR_TYPE]
        )
        list_var = []
        list_parent = []
        list_ftype = []
        list_weight = []
        list_aggr_type = []
        list_namespaces = []

        if (
                LiquidFuel.name in self.energy_list
                and GaseousHydrogen.name in self.energy_list
                and LiquidHydrogen.name in self.energy_list
        ):
            list_var.append("primary_energies_production")
            list_parent.append("Energy_constraints")
            list_ftype.append(FunctionManagerDisc.INEQ_CONSTRAINT)
            list_weight.append(0.0)
            list_aggr_type.append(FunctionManager.AGGR_TYPE_SMAX)
            list_namespaces.append(GlossaryEnergy.NS_FUNCTIONS)

        if (
                hightemperatureheat.name in self.energy_list
                and GaseousHydrogen.name in self.energy_list
                and LiquidHydrogen.name in self.energy_list
        ):
            list_var.append("primary_energies_production")
            list_parent.append("Energy_constraints")
            list_ftype.append(FunctionManagerDisc.INEQ_CONSTRAINT)
            list_weight.append(0.0)
            list_aggr_type.append(FunctionManager.AGGR_TYPE_SMAX)
            list_namespaces.append(GlossaryEnergy.NS_FUNCTIONS)

        if GaseousHydrogen.name in self.energy_list:
            if "PlasmaCracking" in self.dict_technos[GaseousHydrogen.name]:
                list_var.extend([PureCarbonSS.CARBON_TO_BE_STORED_CONSTRAINT])
                list_parent.extend(["Carbon_to_be_stored_constraints"])
                list_ftype.extend([FunctionManagerDisc.INEQ_CONSTRAINT])
                list_weight.extend([0.0])
                list_aggr_type.append(FunctionManager.AGGR_TYPE_SMAX)
                list_namespaces.append(GlossaryEnergy.NS_FUNCTIONS)

        if CarbonStorage.name in self.ccs_list:
            list_var.extend(["carbon_storage_constraint"])
            list_parent.extend([""])
            list_ftype.extend([FunctionManagerDisc.INEQ_CONSTRAINT])
            list_weight.extend([0.0])
            list_aggr_type.append(FunctionManager.AGGR_TYPE_SMAX)
            list_namespaces.append(GlossaryEnergy.NS_FUNCTIONS)

        list_var.extend([EnergyMix.TOTAL_PROD_MINUS_MIN_PROD_CONSTRAINT_DF])
        list_parent.extend(["Energy_constraints"])
        list_ftype.extend([FunctionManagerDisc.INEQ_CONSTRAINT])
        list_weight.extend([-1.0])
        list_aggr_type.append(FunctionManager.AGGR_TYPE_SMAX)
        list_namespaces.append(GlossaryEnergy.NS_FUNCTIONS)

        if Electricity.name in self.energy_list:
            if Electricity.hydropower_name in self.dict_technos[Electricity.name]:
                list_var.extend(["prod_hydropower_constraint"])
                list_parent.extend(["Energy_constraints"])
                list_ftype.extend([FunctionManagerDisc.INEQ_CONSTRAINT])
                list_weight.extend([-1.0])
                list_aggr_type.append(FunctionManager.AGGR_TYPE_SMAX)
                list_namespaces.append(GlossaryEnergy.NS_FUNCTIONS)

        if SolidFuel.name in self.energy_list:
            list_var.extend(["total_prod_solid_fuel_elec"])
            list_parent.extend(["Energy_constraints"])
            list_ftype.extend([FunctionManagerDisc.INEQ_CONSTRAINT])
            list_weight.extend([0.0])
            list_aggr_type.append(FunctionManager.AGGR_TYPE_SMAX)
            list_namespaces.append(GlossaryEnergy.NS_FUNCTIONS)

        if LiquidHydrogen.name in self.energy_list:
            list_var.extend(["total_prod_h2_liquid"])
            list_parent.extend(["Energy_constraints"])
            list_ftype.extend([FunctionManagerDisc.INEQ_CONSTRAINT])
            list_weight.extend([0.0])
            list_aggr_type.append(FunctionManager.AGGR_TYPE_SMAX)
            list_namespaces.append(GlossaryEnergy.NS_FUNCTIONS)

        if Syngas.name in self.energy_list:
            list_var.extend(["syngas_prod_constraint"])
            list_parent.extend(["Energy_constraints"])
            list_ftype.extend([FunctionManagerDisc.INEQ_CONSTRAINT])
            list_weight.extend([-1.0])
            list_aggr_type.append(FunctionManager.AGGR_TYPE_SMAX)
            list_namespaces.append(GlossaryEnergy.NS_FUNCTIONS)

        if set(EnergyDemandDiscipline.energy_constraint_list).issubset(
                self.energy_list
        ):
            list_var.extend(
                ["electricity_demand_constraint", "transport_demand_constraint"]
            )
            list_parent.extend(["demand_constraint", "demand_constraint"])
            list_ftype.extend([FunctionManagerDisc.INEQ_CONSTRAINT, FunctionManagerDisc.INEQ_CONSTRAINT])
            list_weight.extend([-1.0, -1.0])
            list_aggr_type.extend([FunctionManager.AGGR_TYPE_SUM, FunctionManager.AGGR_TYPE_SUM])
            list_namespaces.extend(
                [GlossaryEnergy.NS_FUNCTIONS, GlossaryEnergy.NS_FUNCTIONS]
            )

        func_df["variable"] = list_var
        func_df["parent"] = list_parent
        func_df["ftype"] = list_ftype
        func_df["weight"] = list_weight
        func_df[FunctionManagerDisc.AGGR_TYPE] = list_aggr_type
        func_df["namespace"] = list_namespaces

        return func_df

    def update_dv_arrays(self):
        """
        Update design variable arrays
        """
        invest_mix_dict = self.get_investments_mix()
        invest_ccs_mix_dict = self.get_investments_ccs_mix()

        for energy in self.energy_list:
            energy_wo_dot = energy.replace(".", "_")
            self.update_dspace_dict_with(
                f"{energy}.{energy_wo_dot}_array_mix",
                list(
                    np.maximum(self.lower_bound_techno, invest_mix_dict[energy].values)
                ),
                self.lower_bound_techno,
                self.upper_bound_techno,
            )

        for ccs in self.ccs_list:
            ccs_wo_dot = ccs.replace(".", "_")
            self.update_dspace_dict_with(
                f"{ccs}.{ccs_wo_dot}_array_mix",
                list(
                    np.maximum(self.lower_bound_techno, invest_ccs_mix_dict[ccs].values)
                ),
                self.lower_bound_techno,
                self.upper_bound_techno,
            )

        activated_elem_list = [False] + (GlossaryEnergy.NB_POLES_FULL - 1) * [True]
        ccs_percentage = np.array([0] + (GlossaryEnergy.NB_POLES_FULL - 1) * [1])
        lbnd1 = [0.0] * GlossaryEnergy.NB_POLES_FULL
        ubnd1 = [50.0] * GlossaryEnergy.NB_POLES_FULL
        self.update_dspace_dict_with(
            "ccs_percentage_array",
            list(ccs_percentage),
            lbnd1,
            ubnd1,
            activated_elem=activated_elem_list,
        )

    def update_dv_arrays_technos(self, invest_mix_df):
        """
        Update design variable arrays for all technologies in the case where we have only one investment discipline
        """
        invest_mix_df_wo_years = invest_mix_df.drop(GlossaryEnergy.Years, axis=1)

        # check if we are in coarse usecase, in this case we deactivate first point of optim
        if GlossaryEnergy.fossil in self.energy_list:
            activated_elem = [False] + [True] * (GlossaryEnergy.NB_POLES_COARSE - 1)
        else:
            activated_elem = None
        for column in invest_mix_df_wo_years.columns:
            techno_wo_dot = column.replace(".", "_")
            self.update_dspace_dict_with(
                f"{column}.{techno_wo_dot}_array_mix",
                np.minimum(
                    np.maximum(
                        self.lower_bound_techno, invest_mix_df_wo_years[column].values
                    ),
                    self.upper_bound_techno,
                ),
                self.lower_bound_techno,
                self.upper_bound_techno,
                activated_elem=activated_elem,
            )

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
                invest_energy_mix_dict[energy], _ = self.invest_bspline(
                    invest_energy_mix_dict[energy], len(self.years)
                )

        energy_mix_invest_df = pd.DataFrame({
            key: value for key, value in invest_energy_mix_dict.items() if
            key in self.energy_list or key == GlossaryEnergy.Years
        })

        return energy_mix_invest_df

    def get_investments_ccs_mix(self):
        if self.coarse_mode:
            invest_ccs_mix_dict = {
                GlossaryEnergy.Years: np.arange(GlossaryEnergy.NB_POLES_COARSE),
                CarbonCapture.name: np.ones(GlossaryEnergy.NB_POLES_COARSE),
                CarbonStorage.name: np.ones(GlossaryEnergy.NB_POLES_COARSE)
            }

        else:
            invest_ccs_mix_dict = {
                GlossaryEnergy.Years: np.arange(GlossaryEnergy.NB_POLES_FULL),
                CarbonCapture.name: [2.0] + [25] * (GlossaryEnergy.NB_POLES_FULL - 1),
                CarbonStorage.name: [0.003] + [5] * (GlossaryEnergy.NB_POLES_FULL - 1)
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
        invest_mix_df = pd.DataFrame({GlossaryEnergy.Years: energy_mix[GlossaryEnergy.Years].values}
                                     )
        for study in instanciated_studies:
            if study is not None:
                invest_techno = study.get_investments()
                energy = study.energy_name

                for techno in invest_techno.columns:
                    if techno != GlossaryEnergy.Years:
                        invest_mix_df[f"{energy}.{techno}"] = invest_techno[techno].values

        return invest_mix_df

    def get_absolute_total_mix(self, instanciated_studies):

        invest_mix_df = self.get_total_mix(instanciated_studies)

        indep_invest_df = pd.DataFrame(
            {GlossaryEnergy.Years: invest_mix_df[GlossaryEnergy.Years].values}
        )
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
                prefix_name = GlossaryEnergy.CCUS
                instance_sub_study = sub_study(
                    year_start=self.year_start,
                    year_end=self.year_end,
                    bspline=self.bspline,
                    main_study=False,
                    prefix_name=prefix_name,
                    execution_engine=self.execution_engine,
                    invest_discipline=self.invest_discipline,
                    technologies_list=self.techno_dict[sub_study_name]["value"],
                )
            elif self.techno_dict[sub_study_name]["type"] == ENERGY_TYPE:
                instance_sub_study = sub_study(
                    year_start=self.year_start,
                    year_end=self.year_end,
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

        all_resource_ratio_usable_demand = {GlossaryEnergy.Years: self.years}
        all_resource_ratio_usable_demand.update({resource: 100.0 for resource in EnergyMix.RESOURCE_LIST})
        all_resource_ratio_usable_demand = pd.DataFrame(all_resource_ratio_usable_demand)

        invest_df = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.EnergyInvestmentsValue: 10.55 * (1.0 - 0.0253) ** np.arange(len(self.years)),
        })
        # init land surface for food for biomass dry crop energy

        population_df = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.PopulationValue: np.linspace(7886.69358, 9000.0, len(self.years)),
        })

        transport_demand = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.TransportDemandValue: np.linspace(33600.0, 30000.0, len(self.years)),
        })

        if not self.energy_invest_input_in_abs_value:
            # if energy investments are expressed in percentage, the new corresponding inputs must be defined
            invest_percentage_gdp = pd.DataFrame(
                {
                    GlossaryEnergy.Years: self.years,
                    GlossaryEnergy.EnergyInvestPercentageGDPName: np.linspace(
                        10.0, 20.0, len(self.years)
                    ),
                }
            )
            techno_list_fossil = [GlossaryEnergy.FossilSimpleTechno]
            techno_list_renewable = [GlossaryEnergy.RenewableSimpleTechno]
            techno_list_carbon_capture = [
                GlossaryEnergy.DirectAirCapture,
                GlossaryEnergy.FlueGasCapture,
            ]
            techno_list_carbon_storage = [GlossaryEnergy.CarbonStorageTechno]
            invest_percentage_per_techno = {GlossaryEnergy.Years: self.years}
            all_techno_list = [
                techno_list_fossil,
                techno_list_renewable,
                techno_list_carbon_capture,
                techno_list_carbon_storage,
            ]
            invest_percentage_per_techno.update(
                {
                    techno: 100.0 / 5.0
                    for sublist in all_techno_list
                    for techno in sublist
                }
            )
            invest_percentage_per_techno = pd.DataFrame(invest_percentage_per_techno)

        values_dict = {
            f"{self.study_name}.{GlossaryEnergy.EnergyInvestmentsValue}": invest_df,
            f"{self.study_name}.{GlossaryEnergy.YearStart}": self.year_start,
            f"{self.study_name}.{GlossaryEnergy.YearEnd}": self.year_end,
            f"{self.study_name}.{GlossaryEnergy.energy_list}": self.energy_list,
            f"{self.study_name}.{GlossaryEnergy.ccs_list}": self.ccs_list,
            f"{self.study_name}.{energy_mix_name}.{GlossaryEnergy.EnergyPricesValue}": energy_prices,
            f"{self.study_name}.{GlossaryEnergy.CO2TaxesValue}": co2_taxes,
            f"{self.study_name}.{energy_mix_name}.{GlossaryEnergy.EnergyCO2EmissionsValue}": energy_carbon_emissions,
            f"{self.study_name}.{energy_mix_name}.{GlossaryEnergy.AllStreamsDemandRatioValue}": all_streams_demand_ratio,
            f"{self.study_name}.is_stream_demand": True,
            f"{self.study_name}.max_mda_iter": 50,
            f"{self.study_name}.sub_mda_class": "GSPureNewtonMDA",
            f"{self.study_name}.NormalizationReferences.liquid_hydrogen_percentage": np.concatenate(
                (np.ones(5) * 1e-4, np.ones(len(self.years) - 5) / 4), axis=None
            ),
            f"{self.study_name}.{energy_mix_name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}": resources_CO2_emissions,
            f"{self.study_name}.{energy_mix_name}.{GlossaryEnergy.ResourcesPriceValue}": resources_prices,
            f"{self.study_name}.{GlossaryEnergy.PopulationDfValue}": population_df,
            f"{self.study_name}.Energy_demand.{GlossaryEnergy.TransportDemandValue}": transport_demand,

        }
        if self.main_study:
            values_dict.update({
                f"{self.study_name}.{energy_mix_name}.all_resource_ratio_usable_demand": all_resource_ratio_usable_demand,

            })

        (
            values_dict_list,
            dspace_list,
            instanciated_studies,
        ) = self.setup_usecase_sub_study_list()

        # The flue gas list will depend on technologies present in the
        # techno_dict
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
                f"{self.study_name}.{GlossaryEnergy.CCUS}.{CarbonCapture.name}.{FlueGas.node_name}.{GlossaryEnergy.techno_list}"
            ] = flue_gas_list

        # IF coarse process no need of heat loss percentage (raw prod is net prod)
        # IF renewable and fossil in energy_list then coarse process
        if self.coarse_mode:
            values_dict.update({f"{self.study_name}.EnergyMix.heat_losses_percentage": 0.0})
        if self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[1]:

            invest_mix_df = self.get_total_mix(instanciated_studies)
            values_dict.update({
                f"{self.study_name}.{INVEST_DISC_NAME}.{GlossaryEnergy.invest_mix}": invest_mix_df
            })
            self.update_dv_arrays_technos(invest_mix_df)
        elif self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[2]:
            invest_mix_df = self.get_absolute_total_mix(instanciated_studies)
            values_dict.update({
                f"{self.study_name}.{INVEST_DISC_NAME}.{GlossaryEnergy.invest_mix}": invest_mix_df
            })
            self.update_dv_arrays_technos(invest_mix_df)
            self.add_utilization_ratio_dv(instanciated_studies)

            if not self.energy_invest_input_in_abs_value:
                # if energy investments are expressed in percentage, the new corresponding inputs must be defined
                values_dict.update({
                        f"{self.study_name}.{INVEST_DISC_NAME}.{GlossaryEnergy.EnergyInvestPercentageGDPName}": invest_percentage_gdp,
                        f"{self.study_name}.{INVEST_DISC_NAME}.{GlossaryEnergy.TechnoInvestPercentageName}": invest_percentage_per_techno,
            })

        values_dict_list.append(values_dict)

        self.create_technolist_per_energy(instanciated_studies)

        dc_resource = datacase_resource(self.year_start, self.year_end, main_study=False)
        dc_resource.study_name = self.study_name
        resource_input_list = dc_resource.setup_usecase()
        values_dict_list.extend(resource_input_list)

        agri_values_dict = self.get_input_value_from_agriculture_mix()
        values_dict_list.append(agri_values_dict)
        return values_dict_list

    def add_utilization_ratio_dv(self, instanciated_studies):
        """
        Update design space with utilization ratio for each technology
        """
        dict_energy_studies = dict(zip(self.energy_list + self.ccs_list, instanciated_studies))
        len_utilization_ratio = GlossaryEnergy.NB_POLES_UTILIZATION_RATIO
        start_value_utilization_ratio = np.ones(len_utilization_ratio) * 100.
        lower_bound = np.ones(len_utilization_ratio) * 0.5
        upper_bound = np.ones(len_utilization_ratio) * 100.
        for energy_name, study in dict_energy_studies.items():
            if study is not None:
                for techno_name in study.technologies_list:
                    if energy_name in self.ccs_list:
                        # if energy is ccs, use different name
                        var_name_utilization_ratio = f"{energy_name}.{techno_name}_utilization_ratio_array"
                    else:
                        var_name_utilization_ratio = f"{energy_name}_{techno_name}_utilization_ratio_array"

                    self.update_dspace_dict_with(
                        var_name_utilization_ratio,
                        start_value_utilization_ratio,
                        lower_bound,
                        upper_bound,
                    )

    def get_input_value_from_agriculture_mix(self):
        agri_mix_name = "AgricultureMix"

        N2O_per_use = pd.DataFrame({GlossaryEnergy.Years: self.years, GlossaryEnergy.N2OPerUse: 5.34e-5})
        CH4_per_use = pd.DataFrame({GlossaryEnergy.Years: self.years, GlossaryEnergy.CH4PerUse: 0.0})
        CO2_per_use = pd.DataFrame({GlossaryEnergy.Years: self.years, GlossaryEnergy.CO2PerUse: 0.277})

        energy_consumption = pd.DataFrame({GlossaryEnergy.Years: self.years, "CO2_resource (Mt)": 3.5})
        energy_production = pd.DataFrame({GlossaryEnergy.Years: self.years, GlossaryEnergy.biomass_dry: 12.5})
        energy_prices = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.biomass_dry: 9.8,
            "biomass_dry_wotaxes": 9.8,
        })

        land_use_required = pd.DataFrame({GlossaryEnergy.Years: self.years, "Crop (GHa)": 0.07, "Forest (Gha)": 1.15})
        CO2_emissions = pd.DataFrame({GlossaryEnergy.Years: self.years, GlossaryEnergy.biomass_dry: -0.277})
        energy_type_capital = pd.DataFrame({GlossaryEnergy.Years: self.years, GlossaryEnergy.Capital: 0.0})

        agri_values_dict = {
            f"{self.study_name}.{agri_mix_name}.N2O_per_use": N2O_per_use,
            f"{self.study_name}.{agri_mix_name}.CH4_per_use": CH4_per_use,
            f"{self.study_name}.{agri_mix_name}.CO2_per_use": CO2_per_use,
            f"{self.study_name}.{agri_mix_name}.{GlossaryEnergy.EnergyConsumptionValue}": energy_consumption,
            f"{self.study_name}.{agri_mix_name}.{GlossaryEnergy.EnergyConsumptionWithoutRatioValue}": energy_consumption,
            f"{self.study_name}.{agri_mix_name}.{GlossaryEnergy.EnergyProductionValue}": energy_production,
            f"{self.study_name}.EnergyMix.{agri_mix_name}.{GlossaryEnergy.EnergyTypeCapitalDfValue}": energy_type_capital,
            f"{self.study_name}.{agri_mix_name}.{GlossaryEnergy.EnergyPricesValue}": energy_prices,
            f"{self.study_name}.{agri_mix_name}.{GlossaryEnergy.LandUseRequiredValue}": land_use_required,
            f"{self.study_name}.{agri_mix_name}.{GlossaryEnergy.CO2EmissionsValue}": CO2_emissions,
        }

        return agri_values_dict


if "__main__" == __name__:
    uc_cls = Study()
    uc_cls.load_data()
    uc_cls.run()
