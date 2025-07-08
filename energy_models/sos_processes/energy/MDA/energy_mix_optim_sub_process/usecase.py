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
from sostrades_core.study_manager.study_manager import StudyManager
from sostrades_optimization_plugins.models.func_manager.func_manager import (
    FunctionManager,
)
from sostrades_optimization_plugins.models.func_manager.func_manager_disc import (
    FunctionManagerDisc,
)

from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.sos_processes.energy.MDA.energy_process_v0_mda.usecase import (
    Study as subStudy,
)
from energy_models.sos_processes.techno_dict.data.techno_dicts import techno_dict_midway

INVEST_DISC_NAME = "InvestmentDistribution"


class Study(StudyManager):
    coupling_name = "MDA"

    def __init__(
            self,
            file_path=__file__,
            year_start=GlossaryEnergy.YearStartDefault,
            year_end=GlossaryEnergy.YearEndDefault,
            main_study=True,
            bspline=True,
            execution_engine=None,
            use_utilisation_ratio: bool = False,
            techno_dict=techno_dict_midway
    ):
        super().__init__(
            file_path=file_path,
            run_usecase=True,
            execution_engine=execution_engine,
        )
        self.use_utilisation_ratio = use_utilisation_ratio
        self.substudy = subStudy(year_start=year_start, year_end=year_end)
        self.years = self.substudy.years

    def get_dvar_dscriptor(self):
        """Returns design variable descriptor based on techno list"""
        design_var_descriptor = {}
        for energy in self.substudy.energy_list:
            energy_wo_dot = energy.replace('.', '_')
            for technology in self.substudy.dict_technos[energy]:
                technology_wo_dot = technology.replace('.', '_')

                design_var_descriptor[f'{energy}.{technology}.{energy_wo_dot}_{technology_wo_dot}_array_mix'] = {
                    'out_name': GlossaryEnergy.invest_mix,
                    'out_type': 'dataframe',
                    'key': f'{energy}.{technology}',
                    'index': self.substudy.years,
                    'index_name': GlossaryEnergy.Years,
                    'namespace_in': GlossaryEnergy.NS_ENERGY_MIX,
                    'namespace_out': 'ns_invest'
                }
                if self.use_utilisation_ratio:
                    design_var_descriptor[f'EnergyMix.{energy}.{technology}.utilization_ratio_array'] = {
                        'out_name': f'EnergyMix.{energy}.{technology}.{GlossaryEnergy.UtilisationRatioValue}',
                        'out_type': 'dataframe',
                        'key': GlossaryEnergy.UtilisationRatioValue,
                        'index': self.substudy.years,
                        'index_name': GlossaryEnergy.Years,
                        'namespace_in': GlossaryEnergy.NS_WITNESS,
                        'namespace_out': GlossaryEnergy.NS_WITNESS
                    }

        for ccs in self.substudy.ccs_list:
            ccs_wo_dot = ccs.replace('.', '_')
            for technology in self.substudy.dict_technos[ccs]:
                technology_wo_dot = technology.replace('.', '_')

                design_var_descriptor[f'{ccs}.{technology}.{ccs_wo_dot}_{technology_wo_dot}_array_mix'] = {
                    'out_name': GlossaryEnergy.invest_mix,
                    'out_type': 'dataframe',
                    'key': f'{ccs}.{technology}',
                    'index': self.substudy.years,
                    'index_name': GlossaryEnergy.Years,
                    'namespace_in': GlossaryEnergy.NS_CCS,
                    'namespace_out': 'ns_invest'
                }

                if self.use_utilisation_ratio:
                    # add design variable for utilization ratio per technology
                    design_var_descriptor[f'{GlossaryEnergy.CCUS}.{ccs}.{technology}.utilization_ratio_array'] = {
                        'out_name': f'{GlossaryEnergy.CCUS}.{ccs}.{technology}.{GlossaryEnergy.UtilisationRatioValue}',
                        'out_type': 'dataframe',
                        'key': GlossaryEnergy.UtilisationRatioValue,
                        'index': self.substudy.years,
                        'index_name': GlossaryEnergy.Years,
                        'namespace_in': GlossaryEnergy.NS_WITNESS,
                        'namespace_out': GlossaryEnergy.NS_WITNESS
                    }

        return design_var_descriptor



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
        for energy_or_ccs in self.substudy.energy_list:
            for techno in self.substudy.dict_technos[energy_or_ccs]:
                variables.append(
                    f"EnergyMix.{energy_or_ccs}.{techno}.utilization_ratio_array"
                )

        for energy_or_ccs in self.substudy.ccs_list:
            for techno in self.substudy.dict_technos[energy_or_ccs]:
                variables.append(
                    f"{GlossaryEnergy.CCUS}.{energy_or_ccs}.{techno}.utilization_ratio_array"
                )
        low_bound = [1.] * GlossaryEnergy.NB_POLE_ENERGY_MIX_PROCESS
        upper_bound = [100.] * GlossaryEnergy.NB_POLE_ENERGY_MIX_PROCESS
        value = [100.] * GlossaryEnergy.NB_POLE_ENERGY_MIX_PROCESS
        n_dvar_ur = len(variables)
        dspace_ur = {
            'variable': variables,
            'value': [value] * n_dvar_ur,
            'activated_elem': [[True] * GlossaryEnergy.NB_POLE_ENERGY_MIX_PROCESS] * n_dvar_ur,
            'lower_bnd': [low_bound] * n_dvar_ur,
            'upper_bnd': [upper_bound] * n_dvar_ur,
            'enable_variable': [True] * n_dvar_ur
        }

        dspace_ur = pd.DataFrame(dspace_ur)
        return dspace_ur

    def make_func_df(self):
        func_df = pd.DataFrame({
            "variable": [GlossaryEnergy.CO2EmissionsObjectiveValue,
                         GlossaryEnergy.TargetProductionConstraintValue, GlossaryEnergy.MaxBudgetConstraintValue, ],
            "parent": ["objectives", "constraints", "constraints"],
            "ftype": [FunctionManagerDisc.OBJECTIVE,
                      FunctionManagerDisc.INEQ_CONSTRAINT, FunctionManagerDisc.INEQ_CONSTRAINT],
            "weight": [1.0, 10.0, 10.0, ],
            FunctionManagerDisc.AGGR_TYPE: [FunctionManager.AGGR_TYPE_SUM,
                                            FunctionManager.INEQ_NEGATIVE_WHEN_SATIFIED_AND_SQUARE_IT,
                                            FunctionManager.INEQ_NEGATIVE_WHEN_SATIFIED_AND_SQUARE_IT, ],
            "namespace": [GlossaryEnergy.NS_FUNCTIONS] * 3
        })
        return func_df

    def get_dvar_values(self, dspace):
        out_dict = {}

        for ccs in self.substudy.ccs_list:
            ccs_wo_dot = ccs.replace('.', '_')
            for technology in self.substudy.dict_technos[ccs]:
                technology_wo_dot = technology.replace('.', '_')
                array_invest_var_name = f"{ccs}.{technology}.{ccs_wo_dot}_{technology_wo_dot}_array_mix"
                value = dspace.loc[dspace['variable'] == array_invest_var_name, 'value'].values[0]
                out_dict.update({
                    f"{self.study_name}.{self.coupling_name}.{GlossaryEnergy.CCUS}.{array_invest_var_name}": np.array(
                        value)
                })

                if self.use_utilisation_ratio:
                    array_utilization_ratio_var_name = f"{GlossaryEnergy.CCUS}.{ccs}.{technology}.utilization_ratio_array"
                    value = dspace.loc[dspace['variable'] == array_utilization_ratio_var_name, 'value'].values[0]
                    out_dict.update({
                        f"{self.study_name}.{self.coupling_name}.{array_utilization_ratio_var_name}": np.array(value)
                    })

        for energy in self.substudy.energy_list:
            energy_wo_dot = energy.replace('.', '_')
            for technology in self.substudy.dict_technos[energy]:
                technology_wo_dot = technology.replace('.', '_')

                array_invest_var_name = f"{energy}.{technology}.{energy_wo_dot}_{technology_wo_dot}_array_mix"
                value = dspace.loc[dspace['variable'] == array_invest_var_name, 'value'].values[0]
                out_dict.update({
                    f"{self.study_name}.{self.coupling_name}.EnergyMix.{array_invest_var_name}": np.array(value)
                })

                if self.use_utilisation_ratio:
                    array_utilization_ratio_var_name = f"EnergyMix.{energy}.{technology}.utilization_ratio_array"
                    value = dspace.loc[dspace['variable'] == array_utilization_ratio_var_name, 'value'].values[0]
                    out_dict.update({
                        f"{self.study_name}.{self.coupling_name}.{array_utilization_ratio_var_name}": np.array(
                            value)
                    })

        return out_dict

    def make_dspace(self, ):
        self.substudy.dspace.pop("dspace_size")
        dspace_out = pd.DataFrame({'variable':self.substudy.dspace.keys() })
        dspace_out["value"] = [ds["value"] for ds in self.substudy.dspace.values()]
        dspace_out["lower_bnd"] = [ds["lower_bnd"] for ds in self.substudy.dspace.values()]
        dspace_out["upper_bnd"] = [ds["upper_bnd"] for ds in self.substudy.dspace.values()]
        dspace_out["activated_elem"] = [ds["activated_elem"] for ds in self.substudy.dspace.values()]
        dspace_out["activated_elem"] = [ds["activated_elem"] for ds in self.substudy.dspace.values()]
        dspace_out["enable_variable"] = [ds["enable_variable"] for ds in self.substudy.dspace.values()]

        if not self.use_utilisation_ratio:
            dspace_out = dspace_out[~dspace_out["variable"].str.contains("utilization_ratio_array", na=False)]

        return dspace_out



    def setup_usecase(self, study_folder_path=None):
        self.substudy.study_name = f'{self.study_name}.MDA'
        values_dict = self.substudy.setup_usecase()

        dspace = self.make_dspace()
        design_var_descriptor = self.get_dvar_dscriptor()
        func_df = self.make_func_df()
        dvar_values = self.get_dvar_values(dspace)
        values_dict.update({
            f"{self.study_name}.{self.coupling_name}.DesignVariables.design_var_descriptor": design_var_descriptor,
            f"{self.study_name}.design_space": dspace,
            f"{self.study_name}.{self.coupling_name}.FunctionsManager.function_df": func_df,
            **dvar_values
        })


        agriculture_land_use_emissions = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.Crop: 0.,
            GlossaryEnergy.Forestry: 0.,
            "Total": 0.,
        })
        df_zeros_sections = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            **{section: 0 for section in GlossaryEnergy.SectionsPossibleValues}
        })
        # ghg emission inputs
        values_dict.update({
            f"{self.study_name}.{self.coupling_name}.{GlossaryEnergy.insertGHGAgriLandEmissions.format(GlossaryEnergy.CO2)}": agriculture_land_use_emissions,
            f"{self.study_name}.{self.coupling_name}.{GlossaryEnergy.insertGHGAgriLandEmissions.format(GlossaryEnergy.CH4)}": agriculture_land_use_emissions,
            f"{self.study_name}.{self.coupling_name}.{GlossaryEnergy.insertGHGAgriLandEmissions.format(GlossaryEnergy.N2O)}": agriculture_land_use_emissions,
            f"{self.study_name}.{self.coupling_name}.{GlossaryEnergy.ResidentialEnergyConsumptionDfValue}": agriculture_land_use_emissions,

            f"{self.study_name}.{self.coupling_name}.{GlossaryEnergy.SectorServices}.{GlossaryEnergy.SectionEnergyConsumptionDfValue}": df_zeros_sections,
            f"{self.study_name}.{self.coupling_name}.{GlossaryEnergy.SectorServices}.{GlossaryEnergy.SectionNonEnergyEmissionGdpDfValue}": df_zeros_sections,
            f"{self.study_name}.{self.coupling_name}.{GlossaryEnergy.SectorServices}.{GlossaryEnergy.SectionGdpDfValue}": df_zeros_sections,

            f"{self.study_name}.{self.coupling_name}.{GlossaryEnergy.SectorIndustry}.{GlossaryEnergy.SectionEnergyConsumptionDfValue}": df_zeros_sections,
            f"{self.study_name}.{self.coupling_name}.{GlossaryEnergy.SectorIndustry}.{GlossaryEnergy.SectionNonEnergyEmissionGdpDfValue}": df_zeros_sections,
            f"{self.study_name}.{self.coupling_name}.{GlossaryEnergy.SectorIndustry}.{GlossaryEnergy.SectionGdpDfValue}": df_zeros_sections,
        })
        return values_dict




if '__main__' == __name__:
    uc_cls = Study()
    uc_cls.load_data()
    uc_cls.run()
