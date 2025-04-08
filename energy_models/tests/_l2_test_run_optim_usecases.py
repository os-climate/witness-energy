'''
Copyright 2022 Airbus SAS
Modifications on 03/03/2025 Copyright 2025 Capgemini

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

import pprint
import unittest

from sostrades_core.sos_processes.run_all_usecases import run_optim_usecases


class TestUseCases(unittest.TestCase):
    """
    Usecases test class
    """

    def setUp(self):
        
        self.pp = pprint.PrettyPrinter(indent=4, compact=True)
        self.processes_repo = 'energy_models.sos_processes'

    def test_01_run_optim_usecases(self):
        '''
        Run all usecases in this repository.
        '''
        run_optim_usecases(self.processes_repo)
