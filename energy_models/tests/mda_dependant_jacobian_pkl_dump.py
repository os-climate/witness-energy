'''
Created on 10 May 2021

'''

import os

import energy_models.tests as jacobian_target
from energy_models.tests.data_tests.mda_energy_data_generator import launch_data_pickle_generation
from sostrades_core.tests.core.abstract_jacobian_unit_test import AbstractJacobianUnittest

if __name__ == '__main__':

    directory = 'data_tests'
    launch_data_pickle_generation(directory)
    os.system(f'git add ./{directory}/*.pkl')
    os.system('git commit -m "regeneration of mda_energy data pickles"')
    os.system('git pull')
    os.system('git push')

    AbstractJacobianUnittest.launch_all_pickle_generation(
        jacobian_target, 'l1_test_gradient_biomass_dry.py', test_names=['test_04_biomass_dry_discipline_jacobian'])
    AbstractJacobianUnittest.launch_all_pickle_generation(
        jacobian_target, 'l1_test_gradient_carbon_capture.py', test_names=['test_04_carbon_capture_discipline_jacobian'])
    AbstractJacobianUnittest.launch_all_pickle_generation(
        jacobian_target, 'l1_test_gradient_carbon_storage.py', test_names=['test_09_carbon_storage_discipline_jacobian'])
    AbstractJacobianUnittest.launch_all_pickle_generation(
        jacobian_target, 'l1_test_gradient_electricity.py', test_names=['test_11_electricity_discipline_jacobian'])
    AbstractJacobianUnittest.launch_all_pickle_generation(
        jacobian_target, 'l1_test_gradient_hydrogen.py', test_names=['test_08_gaseous_hydrogen_discipline_jacobian'])
    AbstractJacobianUnittest.launch_all_pickle_generation(
        jacobian_target, 'l1_test_gradient_liquid_fuel.py', test_names=['test_05_liquid_fuel_discipline_jacobian'])
    AbstractJacobianUnittest.launch_all_pickle_generation(
        jacobian_target, 'l1_test_gradient_liquid_hydrogen.py', test_names=['test_02_liquid_hydrogen_discipline_jacobian'])
    AbstractJacobianUnittest.launch_all_pickle_generation(
        jacobian_target, 'l1_test_gradient_methane.py', test_names=['test_04_methane_discipline_jacobian'])
    AbstractJacobianUnittest.launch_all_pickle_generation(
        jacobian_target, 'l1_test_gradient_ratio.py', test_names=[
            'test_01_ratio_hydrogen_liquefaction_discipline_jacobian',
            'test_02_ratio_SMR_discipline_jacobian',
            'test_03_ratio_CropEnergy_discipline_jacobian',
            'test_04_ratio_UnmanagedWood_discipline_jacobian',
            'test_05_ratio_WaterGasShift_discipline_jacobian',
            'test_06_ratio_FischerTropsch_discipline_jacobian',
            'test_07_ratio_CalciumLooping_discipline_jacobian',
            'test_08_gaseous_hydrogen_discipline_jacobian',
            'test_09_carbon_capture_discipline_jacobian',
            'test_12_energy_mix_all_stream_demand_ratio_discipline_jacobian'])
    AbstractJacobianUnittest.launch_all_pickle_generation(
        jacobian_target, 'l1_test_gradient_solid_fuel.py', test_names=['test_03_solid_fuel_discipline_jacobian'])
    AbstractJacobianUnittest.launch_all_pickle_generation(
        jacobian_target, 'l1_test_gradient_syngas.py', test_names=['test_09_generic_syngas_discipline_jacobian'])

