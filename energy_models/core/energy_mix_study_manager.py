'''
Copyright 2022 Airbus SAS

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
from sos_trades_core.study_manager.study_manager import StudyManager
from sos_trades_core.tools.bspline.bspline_methods import bspline_method


class EnergyMixStudyManager(StudyManager):
    '''
    classdocs
    '''

    def __init__(self, file_path, technologies_list, run_usecase=True, main_study=True, execution_engine=None, one_invest_discipline=False):
        '''
        Constructor
        '''
        self.technologies_list = technologies_list
        self.lower_bound_techno = None
        self.upper_bound_techno = None
        self.energy_name = None
        super().__init__(file_path, run_usecase=run_usecase, execution_engine=execution_engine)
        self.configure_ds_boundaries()
        self.one_invest_discipline = one_invest_discipline
        self.main_study = main_study
    #--Overwrite method for technology selection

    def setup_process(self):
        StudyManager.setup_process(self)
        self.ee.root_builder_ist.setup_process(
            self.technologies_list, self.one_invest_discipline)

    def configure_ds_boundaries(self, lower_bound_techno=1.0, upper_bound_techno=100.):
        """
        Configure design space boundaries 
        """
        self.lower_bound_techno = lower_bound_techno
        self.upper_bound_techno = upper_bound_techno

    def update_dv_arrays(self):
        """
        Update design variable arrays
        """
        invest_mix_dict = self.get_investments()
        energy_wodot = self.energy_name.replace('.', '_')

        if len(self.technologies_list) > 1:
            enable_variable = True
        else:
            enable_variable = False

        for techno in self.technologies_list:
            techno_wo_dot = techno.replace('.', '_')
            self.update_dspace_dict_with(
                f'{energy_wodot}_{techno_wo_dot}_array_mix', np.maximum(
                    self.lower_bound_techno, invest_mix_dict[techno].values),
                self.lower_bound_techno, self.upper_bound_techno, enable_variable=enable_variable)

    def get_investments(self):
        ''' To be overloaded by sublcasses
        '''
        raise NotImplementedError()

    def invest_bspline(self, ctrl_pts, len_years):
        '''
        Method to evaluate investment per year from control points
        '''

        return bspline_method(ctrl_pts, len_years)
