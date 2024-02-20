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

from climateeconomics.core.tools.ClimateEconomicsStudyManager import ClimateEconomicsStudyManager
# mode: python; py-indent-offset: 4; tab-width: 8; coding:utf-8
from climateeconomics.glossarycore import GlossaryCore
from climateeconomics.sos_processes.iam.witness.agriculture_mix_process.usecase import \
    AGRI_MIX_TECHNOLOGIES_LIST_FOR_OPT
#from climateeconomics.sos_processes.iam.witness.witness.usecase_witness import Study as witness_usecase
from energy_models.sos_processes.energy.MDA.heat_process_v0.usecase import Study as witness_usecase
from energy_models.core.energy_process_builder import INVEST_DISCIPLINE_OPTIONS
from energy_models.core.energy_study_manager import DEFAULT_TECHNO_DICT
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
from energy_models.core.energy_study_manager import AGRI_TYPE, ENERGY_TYPE

DEFAULT_TECHNO_DICT = {
                       # Electricity.name: {'type': ENERGY_TYPE, 'value': Electricity_technos_dev},
                       # Methane.name: {'type': ENERGY_TYPE, 'value': Methane_technos_dev},
                       hightemperatureheat.name: {'type': ENERGY_TYPE, 'value': hightemperatureheat_technos_dev},
                       mediumtemperatureheat.name: {'type': ENERGY_TYPE, 'value': mediumtemperatureheat_technos_dev},
                       lowtemperatureheat.name: {'type': ENERGY_TYPE, 'value': lowtemperatureheat_technos_dev},
                       }

OBJECTIVE = FunctionManagerDisc.OBJECTIVE
INEQ_CONSTRAINT = FunctionManagerDisc.INEQ_CONSTRAINT
EQ_CONSTRAINT = FunctionManagerDisc.EQ_CONSTRAINT
OBJECTIVE_LAGR = FunctionManagerDisc.OBJECTIVE_LAGR
FUNC_DF = FunctionManagerDisc.FUNC_DF
OPTIM_NAME = "WITNESS_MDO"
COUPLING_NAME = "WITNESS_Eval"
EXTRA_NAME = "WITNESS"


class Study(ClimateEconomicsStudyManager):

    def __init__(self, year_start=2020, year_end=2100, time_step=1, bspline=False, run_usecase=False,
                 execution_engine=None,
                 invest_discipline=INVEST_DISCIPLINE_OPTIONS[
                     2], techno_dict=DEFAULT_TECHNO_DICT, agri_techno_list=AGRI_MIX_TECHNOLOGIES_LIST_FOR_OPT,
                 process_level='val'):
        super().__init__(__file__, run_usecase=run_usecase, execution_engine=execution_engine)
        self.year_start = year_start
        self.year_end = year_end
        self.time_step = time_step

        self.coupling_name = COUPLING_NAME
        self.designvariable_name = "DesignVariables"
        self.func_manager_name = "FunctionsManager"
        self.extra_name = EXTRA_NAME
        self.energy_mix_name = 'HeatMix'
        self.ccs_mix_name = 'CCUS'
        self.bspline = bspline
        self.invest_discipline = invest_discipline
        self.techno_dict = techno_dict
        self.agri_techno_list = agri_techno_list
        self.process_level = process_level
        self.witness_uc = witness_usecase(
            self.year_start, self.year_end, self.time_step, bspline=self.bspline, execution_engine=execution_engine,
            invest_discipline=self.invest_discipline, techno_dict=techno_dict,
            ) # process_level=process_level, agri_techno_list=agri_techno_list
        self.sub_study_path_dict = self.witness_uc.sub_study_path_dict

    def setup_usecase(self):
        """ Overloaded method to initialize witness multiscenario optimization process

        @return list of dictionary: [{str: *}]
        """
        setup_data_list = []

        # -- retrieve energy input data

        self.witness_mda_usecase = self.witness_uc
        self.witness_uc.study_name = f'{self.study_name}.{self.coupling_name}.{self.extra_name}'
        self.witness_uc.study_name_wo_extra_name = f'{self.study_name}.{self.coupling_name}'
        witness_data_list = self.witness_uc.setup_usecase()
        setup_data_list = setup_data_list + witness_data_list

        dspace_df = self.witness_uc.dspace

        values_dict = {}

        values_dict[f'{self.study_name}.epsilon0'] = 1.0
        dv_arrays_dict = {}

        design_var_descriptor = {}
        years = np.arange(self.year_start, self.year_end + 1, self.time_step)
        for energy in self.witness_uc.energy_list:
            energy_wo_dot = energy.replace('.', '_')
            for technology in self.witness_uc.dict_technos[energy]:
                technology_wo_dot = technology.replace('.', '_')
                dvar_value = dspace_df[
                        f'{energy}.{technology}.{energy_wo_dot}_{technology_wo_dot}_array_mix']['value']
                activated_dvar = dspace_df[
                        f'{energy}.{technology}.{energy_wo_dot}_{technology_wo_dot}_array_mix']['activated_elem']
                activated_value = np.array([elem for i,elem in enumerate(dvar_value) if activated_dvar[i]])

                dv_arrays_dict[
                    f'{self.witness_uc.study_name}.{self.energy_mix_name}.{energy}.{technology}.{energy_wo_dot}_{technology_wo_dot}_array_mix'] = activated_value

                design_var_descriptor[f'{energy}.{technology}.{energy_wo_dot}_{technology_wo_dot}_array_mix'] = {
                    'out_name': GlossaryCore.invest_mix,
                    'out_type': 'dataframe',
                    'key': f'{energy}.{technology}',
                    'index': years,
                    'index_name': GlossaryCore.Years,
                    'namespace_in': GlossaryCore.NS_ENERGY_MIX,
                    'namespace_out': 'ns_invest'
                }

                design_var_utilization_ratio_value = dspace_df[f'{energy}_{technology}_utilization_ratio_array']['value']
                dv_arrays_dict[f'{self.witness_uc.study_name}.{self.energy_mix_name}.{energy}_{technology}_utilization_ratio_array'] = design_var_utilization_ratio_value
                dv_arrays_dict[f'{self.witness_uc.study_name}.{self.energy_mix_name}.{energy}.{technology}.{GlossaryCore.UtilisationRatioValue}'] = pd.DataFrame(data={GlossaryCore.Years : years,
                                                                                                                                                                       GlossaryCore.UtilisationRatioValue : 100.})
                # add design variable for utilization ratio per technology
                design_var_descriptor[f'{energy}_{technology}_utilization_ratio_array'] = {
                    'out_name':  f'{energy}.{technology}.{GlossaryCore.UtilisationRatioValue}',
                    'out_type': 'dataframe',
                    'key': GlossaryCore.UtilisationRatioValue,
                    'index': years,
                    'index_name': GlossaryCore.Years,
                    'namespace_in': GlossaryCore.NS_ENERGY_MIX,
                    'namespace_out': GlossaryCore.NS_ENERGY_MIX,
                }


        func_df = self.witness_uc.func_df

        # Display func_df after dropping rows

        self.func_df = func_df
        self.design_var_descriptor = design_var_descriptor
        values_dict[f'{self.study_name}.{self.coupling_name}.{self.func_manager_name}.{FUNC_DF}'] = func_df
        values_dict[
            f'{self.study_name}.{self.coupling_name}.{self.designvariable_name}.design_var_descriptor'] = design_var_descriptor

        values_dict[f'{self.study_name}.{self.coupling_name}.sub_mda_class'] = 'GSPureNewtonMDA'
        # values_dict[f'{self.study_name}.{self.coupling_name}.warm_start'] = True
        values_dict[f'{self.study_name}.{self.coupling_name}.max_mda_iter'] = 50
        values_dict[f'{self.study_name}.{self.coupling_name}.linearization_mode'] = 'adjoint'
        values_dict[f'{self.study_name}.{self.coupling_name}.epsilon0'] = 1.0
        # design space

        dspace = self.witness_uc.dspace
        self.dspace_size = dspace.pop('dspace_size')

        dspace_df_columns = ['variable', 'value', 'lower_bnd',
                             'upper_bnd', 'enable_variable']
        dspace_df = pd.DataFrame(columns=dspace_df_columns)
        for key, elem in dspace.items():
            dict_var = {'variable': key}
            dict_var.update(elem)
            dspace_df = dspace_df.append(dict_var, ignore_index=True)

        self.dspace = dspace_df
        """

        keys_to_update = ['carbon_storage.CarbonStorageTechno.carbon_storage_CarbonStorageTechno_array_mix',
                          'carbon_capture.flue_gas_capture.FlueGasTechno.carbon_capture_flue_gas_capture_FlueGasTechno_array_mix',
                          'carbon_capture.direct_air_capture.DirectAirCaptureTechno.carbon_capture_direct_air_capture_DirectAirCaptureTechno_array_mix']
        for key in keys_to_update:
            self.dspace.loc[self.dspace['variable'] == key, 'value'] = \
                np.array(self.dspace.loc[self.dspace['variable'] == key, 'lower_bnd'])
        """
        values_dict[f'{self.witness_uc.study_name}.{self.coupling_name}.{GlossaryCore.energy_list}'] = self.witness_uc.energy_list
        values_dict[f'{self.study_name}.design_space'] = self.dspace
        setup_data_list.append(values_dict)
        setup_data_list.append(dv_arrays_dict)
        return setup_data_list


if '__main__' == __name__:
    uc_cls = Study()
    uc_cls.ee.display_treeview_nodes()
    uc_cls.test()

