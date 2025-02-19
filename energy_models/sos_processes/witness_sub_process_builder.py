'''
Copyright 2022 Airbus SAS
Modifications on 2023/05/12-2024/06/24 Copyright 2023 Capgemini
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

from sostrades_core.sos_processes.base_process_builder import BaseProcessBuilder

from energy_models.core.energy_process_builder import INVEST_DISCIPLINE_DEFAULT
from energy_models.glossaryenergy import GlossaryEnergy


class WITNESSSubProcessBuilder(BaseProcessBuilder):
    def __init__(self, ee):
        super(WITNESSSubProcessBuilder, self).__init__(ee)
        self._techno_dict = {}
        self.energy_list = []
        self.ccs_list = []
        self.techno_dict = GlossaryEnergy.DEFAULT_TECHNO_DICT
        self.invest_discipline = INVEST_DISCIPLINE_DEFAULT
        self.process_level = 'val'
        # If true, inputs for energy invesments are in Gdollars. If False, they are in percentage
        # and an the discipline Investment_redistribution_disc is introduced to translate invest in Gdollars
        self.energy_invest_input_in_abs_value = True
        self.use_resources_bool = False
        self.associate_namespace = None
    @property
    def techno_dict(self):
        return self._techno_dict

    @techno_dict.setter
    def techno_dict(self, value: dict):
        self._techno_dict = value
        self.energy_list, self.ccs_list = self.build_energy_and_ccs_list()

    def build_energy_and_ccs_list(self):
        energy_list = [key for key, value in self._techno_dict.items() if value['type'] == 'energy']
        ccs_list = [key for key, value in self._techno_dict.items() if value['type'] == GlossaryEnergy.CCUS]
        return energy_list, ccs_list

    def setup_process(
            self,
            techno_dict,
            invest_discipline=INVEST_DISCIPLINE_DEFAULT,
            process_level='val',
            energy_invest_input_in_abs_value=True,
            associate_namespace=False,
            use_resources_bool=True,
    ):
        '''
        Setup process function which will be called if the builder is retrieved with get_builder_from_process with args
        This allows to define instance variables inside the class as energy_list or one invest discipline
        '''

        self.techno_dict = techno_dict
        self.invest_discipline = invest_discipline
        self.process_level = process_level
        self.associate_namespace = associate_namespace
        self.energy_invest_input_in_abs_value = energy_invest_input_in_abs_value
        self.use_resources_bool = use_resources_bool
