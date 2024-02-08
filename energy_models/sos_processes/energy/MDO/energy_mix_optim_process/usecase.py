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

from energy_models.core.energy_study_manager import DEFAULT_TECHNO_DICT
from energy_models.sos_processes.energy.MDA.energy_mix_optim_sub_process.usecase import Study as subStudy
from energy_models.glossaryenergy import GlossaryEnergy
from sostrades_core.execution_engine.func_manager.func_manager import FunctionManager
from sostrades_core.execution_engine.func_manager.func_manager_disc import FunctionManagerDisc

INVEST_DISC_NAME = "InvestmentDistribution"


class Study(subStudy):
    def __init__(
            self,
            file_path=__file__,
            year_start=GlossaryEnergy.YeartStartDefault,
            year_end=2050,
            main_study=True,
            bspline=True,
            execution_engine=None,
            techno_dict=DEFAULT_TECHNO_DICT
    ):
        super().__init__(
            file_path=file_path,
            main_study=main_study,
            execution_engine=execution_engine,
            bspline=bspline,
            year_start=year_start,
            year_end=year_end,
            techno_dict=techno_dict
        )

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

    def make_dspace_utilisation_ratio(self, d_space_invest: pd.DataFrame) -> pd.DataFrame:
        variables = d_space_invest['variable']
        var_ur = [var.replace('array_mix', 'utilization_ratio_array') for var in variables]
        low_bound = [1e-6] * 20
        upper_bound = [100.] * 20
        value = [100.] * 20
        n_dvar_ur = len(variables)
        dspace_ur = {
            'variable': var_ur,
            'value': [value] * n_dvar_ur,
            'activated_elem': [[True] * 20] * n_dvar_ur,
            'lower_bnd': [low_bound] * n_dvar_ur,
            'upper_bnd': [upper_bound] * n_dvar_ur,
            'enable_variable': [True] * n_dvar_ur
        }

        dspace_ur = pd.DataFrame(dspace_ur)
        return dspace_ur

    def make_func_df(self):
        func_df = pd.DataFrame({
            "variable": ["energy_production_objective", "syngas_prod_objective"],
            "parent": ["objectives", "objectives"],
            "ftype": [FunctionManagerDisc.OBJECTIVE, FunctionManagerDisc.OBJECTIVE],
            "weight": [1.0, 0.0],
            FunctionManagerDisc.AGGR_TYPE: [FunctionManager.AGGR_TYPE_SUM, FunctionManager.AGGR_TYPE_SUM],
            "namespace": [GlossaryEnergy.NS_FUNCTIONS, GlossaryEnergy.NS_FUNCTIONS]
        })
        return func_df

    def get_dvar_values(self, dspace):
        out_dict = {}

        for ccs in self.ccs_list:
            ccs_wo_dot = ccs.replace('.', '_')
            for technology in self.dict_technos[ccs]:
                technology_wo_dot = technology.replace('.', '_')
                array_var_name = f"{ccs}.{technology}.{ccs_wo_dot}_{technology_wo_dot}_array_mix"
                value = dspace.loc[dspace['variable'] == array_var_name, 'value'].values[0]
                out_dict.update({
                    f"{self.study_name}.{GlossaryEnergy.CCUS}.{array_var_name}": np.array(value)
                })

        for energy in self.energy_list:
            ccs_wo_dot = energy.replace('.', '_')
            for technology in self.dict_technos[energy]:
                technology_wo_dot = technology.replace('.', '_')
                array_var_name = f"{energy}.{technology}.{ccs_wo_dot}_{technology_wo_dot}_array_mix"
                value = dspace.loc[dspace['variable'] == array_var_name, 'value'].values[0]
                out_dict.update({
                    f"{self.study_name}.EnergyMix.{array_var_name}": np.array(value)
                })

        return out_dict

    def make_dspace(self, dspace_list: list):
        dspace_invests = self.make_dspace_invests(dspace_list)
        dspace_utilisation_ratio = self.make_dspace_utilisation_ratio(dspace_invests)
        dspace = pd.concat([dspace_invests, dspace_utilisation_ratio])
        dspace.reset_index(drop=True, inplace=True)
        return dspace

    def setup_usecase(self, study_folder_path=None):
        values = super().setup_usecase()

        design_var_descriptor = self.get_dvar_dscriptor()
        #self.get_dspace()

        values_dict_list, dspace_list, instanced_sub_studies = self.setup_usecase_sub_study_list()
        func_df = self.make_func_df()
        dspace = self.make_dspace(dspace_list)
        values_mdo = {
            f"{self.study_name}.DesignVariables.design_var_descriptor" : design_var_descriptor,
            f"{self.study_name}.design_space": dspace,
            f"{self.study_name}.FunctionsManager.function_df": func_df,
        }

        dvar_values = self.get_dvar_values(dspace)
        values_mdo.update(dvar_values)
        values.append(values_mdo)
        return values


if "__main__" == __name__:
    uc_cls = Study()
    uc_cls.load_data()
    uc_cls.run()
