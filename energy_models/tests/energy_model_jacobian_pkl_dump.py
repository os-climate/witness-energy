'''
Created on 10 May 2021

'''

import energy_models.tests as jacobian_target

from sos_trades_core.tests.core.abstract_jacobian_unit_test import AbstractJacobianUnittest
from os import listdir

if __name__ == '__main__':
    
    AbstractJacobianUnittest.launch_all_pickle_generation(
       jacobian_target, 'l1_test_gradient*.py')

    #AbstractJacobianUnittest.launch_all_pickle_generation(
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
