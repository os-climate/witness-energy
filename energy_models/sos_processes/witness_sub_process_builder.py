'''
Copyright 2022 Airbus SAS
Modifications on 2023/05/12-2023/11/21 Copyright 2023 Capgemini
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

from energy_models.core.energy_process_builder import INVEST_DISCIPLINE_DEFAULT
from energy_models.core.energy_study_manager import DEFAULT_ENERGY_LIST, DEFAULT_CCS_LIST, DEFAULT_TECHNO_DICT
from sostrades_core.sos_processes.base_process_builder import BaseProcessBuilder


class WITNESSSubProcessBuilder(BaseProcessBuilder):

    def __init__(self, ee):
        super(WITNESSSubProcessBuilder, self).__init__(ee)
        self.energy_list = DEFAULT_ENERGY_LIST
        self.ccs_list = DEFAULT_CCS_LIST
        self.techno_dict = DEFAULT_TECHNO_DICT
        self.invest_discipline = INVEST_DISCIPLINE_DEFAULT
        self.process_level = 'val'
        # If true, inputs for energy invesments are in Gdollars. If False, they are in percentage
        # and an the discipline Investment_redistribution_disc is introduced to translate invest in Gdollars
        self.energy_invest_input_in_abs_value = True

    def setup_process(self, techno_dict, invest_discipline=INVEST_DISCIPLINE_DEFAULT, process_level='val',
                      energy_invest_input_in_abs_value=True, associate_namespace=False):
        '''
        Setup process function which will be called if the builder is retrieved with get_builder_from_process with args
        This allows to define instance variables inside the class as energy_list or one invest discipline
        '''

        self.energy_list = [key for key,
                            value in techno_dict.items() if value['type'] == 'energy']
        self.ccs_list = [key for key,
                         value in techno_dict.items() if value['type'] == 'CCUS']
        self.techno_dict = techno_dict
        self.invest_discipline = invest_discipline
        self.process_level = process_level
        self.associate_namespace = associate_namespace
        self.energy_invest_input_in_abs_value = energy_invest_input_in_abs_value
