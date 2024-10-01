'''
Copyright 2022 Airbus SAS
Modifications on 23/11/2023-2024/06/24 Copyright 2023 Capgemini
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

from sostrades_core.tests.core.abstract_jacobian_unit_test import (
    AbstractJacobianUnittest,
)

import energy_models.tests as jacobian_target

if __name__ == '__main__':
    AbstractJacobianUnittest.launch_all_pickle_generation(
        jacobian_target, 'l1_test_gradient*.py')

    # AbstractJacobianUnittest.launch_all_pickle_generation(
    #    jacobian_target, '_l1_test_gradient_energy_mix.py')

    # AbstractJacobianUnittest.launch_all_pickle_generation(
    # jacobian_target, '_l2_test_gradient_energy_model_mda.py')

# #
#     AbstractJacobianUnittest.launch_all_pickle_generation(
#         jacobian_target, 'l2_test_gradient_design_var_openloop.py')
#
#     AbstractJacobianUnittest.launch_all_pickle_generation(
#         jacobian_target, '_l2_test_gradient_design_var_openloop.py')
#
#     AbstractJacobianUnittest.launch_all_pickle_generation(
#         jacobian_target, 'l2_test_check_jacobian_dv_closed_loop.py')
