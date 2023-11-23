'''
Copyright 2022 Airbus SAS
Modifications on 2023/07/03-2023/11/03 Copyright 2023 Capgemini

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
from os.path import join, dirname

from climateeconomics.glossarycore import GlossaryCore
from energy_models.glossaryenergy import GlossaryEnergy
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tests.core.abstract_jacobian_unit_test import AbstractJacobianUnittest
from energy_models.core.energy_mix.energy_mix import EnergyMix
import pickle
from energy_models.sos_processes.energy.MDA.energy_process_v0.usecase import Study
from climateeconomics.sos_processes.iam.witness.witness_optim_sub_process.usecase_witness_optim_sub import Study as WITNESSFull_subprocess
from energy_models.tests.data_tests.mda_energy_data_generator import launch_data_pickle_generation


class RatioJacobianTestCase(AbstractJacobianUnittest):
    """
    Ratio jacobian test class
    """
    # AbstractJacobianUnittest.DUMP_JACOBIAN = True

    def analytic_grad_entry(self):
        return [
            self.test_01_ratio_hydrogen_liquefaction_discipline_jacobian,
            self.test_02_ratio_SMR_discipline_jacobian,
            self.test_03_ratio_CropEnergy_discipline_jacobian,
            self.test_04_ratio_UnmanagedWood_discipline_jacobian,
            self.test_05_ratio_WaterGasShift_discipline_jacobian,
            self.test_06_ratio_FischerTropsch_discipline_jacobian,
            self.test_07_ratio_CalciumLooping_discipline_jacobian,
            self.test_08_gaseous_hydrogen_discipline_jacobian,
            #self.test_09_carbon_capture_discipline_jacobian,
            self.test_12_energy_mix_all_stream_demand_ratio_discipline_jacobian,
            self.test_01b_ratio_FossilGas_discipline_jacobian(),
            self.test_02b_ratio_Nuclear_discipline_jacobian(),
            self.test_03b_ratio_CoalExtraction_discipline_jacobian(),
            self.test_04b_ratio_Refinery_discipline_jacobian(),
            self.test_05b_ratio_PEM_discipline_jacobian(),
            # self.test_10_energy_mix_discipline_jacobian,
        ]

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.name = 'Test_Ratio'
        years = np.arange(2020, 2051)
        self.years = years
        #---Ratios---
        self.is_apply_ratio = True
        self.is_stream_demand = True
        self.is_apply_resource_ratio = True

        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, 100.0 * np.linspace(0.2, 0.9, len(self.years))))
        demand_ratio_dict[GlossaryCore.Years] = self.years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)

        resource_ratio_dict = dict(
            zip(EnergyMix.RESOURCE_LIST, 100.0 * np.linspace(0.8, 1.0, len(self.years))))
        resource_ratio_dict[GlossaryCore.Years] = self.years
        self.all_resource_ratio_usable_demand = pd.DataFrame(
            resource_ratio_dict)

    def tearDown(self):
        pass

    def test_01_ratio_hydrogen_liquefaction_discipline_jacobian(self):
        '''
        Test the gradients of the ratios on a simple techno which uses a single ratio (hydrogen consumption)
        '''
        self.setUp()
        self.techno_name = 'HydrogenLiquefaction'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_hydrogen': f'{self.name}',
                   'ns_liquid_hydrogen': f'{self.name}',
                   'ns_resource': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.liquid_hydrogen.hydrogen_liquefaction.hydrogen_liquefaction_disc.HydrogenLiquefactionDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.techno_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_technologies_input_dict.pkl'), 'rb')
        mda_data_input_dict = pickle.load(pkl_file)
        pkl_file.close()

        namespace = f'{self.name}'
        inputs_dict = {}
        coupled_inputs = []
        for key in mda_data_input_dict[self.techno_name].keys():
            # Modify namespace of input 'key' if needed
            if key in ['linearization_mode', 'cache_type', 'cache_file_path', 'sub_mda_class',
                       'max_mda_iter', 'n_processes', 'chain_linearize', 'tolerance', 'use_lu_fact',
                       'warm_start', 'acceleration', 'warm_start_threshold', 'n_subcouplings_parallel',
                       'max_mda_iter_gs', 'relax_factor', 'epsilon0',
                       'linear_solver_MDO', 'linear_solver_MDO_preconditioner', 'linear_solver_MDA', 'linear_solver_MDA_preconditioner',  'linear_solver_MDA_options',
                       'linear_solver_MDO_options', 'tolerance_linear_solver_MDO', 'group_mda_disciplines',
                       GlossaryCore.TransportCostValue, GlossaryCore.TransportMarginValue, GlossaryCore.YearStart, GlossaryCore.YearEnd,
                       GlossaryCore.EnergyPricesValue, GlossaryCore.EnergyCO2EmissionsValue, GlossaryCore.CO2TaxesValue, GlossaryCore.ResourcesPriceValue,
                       GlossaryCore.RessourcesCO2EmissionsValue, 'scaling_factor_techno_consumption',
                       'scaling_factor_techno_production', 'is_apply_ratio',
                       'is_stream_demand', 'is_apply_resource_ratio',
                       'residuals_history', GlossaryCore.AllStreamsDemandRatioValue, 'all_resource_ratio_usable_demand']:
                inputs_dict[f'{namespace}.{key}'] = mda_data_input_dict[self.techno_name][key]['value']
                if mda_data_input_dict[self.techno_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{key}']
            else:
                inputs_dict[f'{namespace}.{self.techno_name}.{key}'] = mda_data_input_dict[self.techno_name][key]['value']
                if mda_data_input_dict[self.techno_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{self.techno_name}.{key}']

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_technologies_output_dict.pkl'), 'rb')
        mda_data_output_dict = pickle.load(pkl_file)
        pkl_file.close()

        coupled_outputs = []
        for key in mda_data_output_dict[self.techno_name].keys():
            # Modify namespace of output 'key' if needed
            if key in []:
                if mda_data_output_dict[self.techno_name][key]['is_coupling']:
                    coupled_outputs += [f'{namespace}.{key}']
            else:
                if mda_data_output_dict[self.techno_name][key]['is_coupling']:
                    coupled_outputs += [f'{namespace}.{self.techno_name}.{key}']

        # Overwrite values for ratios with values from setup
        inputs_dict[f'{namespace}.{GlossaryCore.YearEnd}'] = 2050
        inputs_dict[f'{namespace}.is_apply_ratio'] = self.is_apply_ratio
        inputs_dict[f'{namespace}.is_stream_demand'] = self.is_stream_demand
        inputs_dict[f'{namespace}.is_apply_resource_ratio'] = self.is_apply_resource_ratio
        inputs_dict[f'{namespace}.{GlossaryCore.AllStreamsDemandRatioValue}'] = self.all_streams_demand_ratio
        inputs_dict[f'{namespace}.all_resource_ratio_usable_demand'] = self.all_resource_ratio_usable_demand

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.techno_name}')[0].mdo_discipline_wrapp.mdo_discipline
        # AbstractJacobianUnittest.DUMP_JACOBIAN = True
        coupled_outputs.append(
            f'{namespace}.{self.techno_name}.non_use_capital')
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_ratio_{self.techno_name}.pkl',
                            discipline=disc, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,local_data = disc.local_data,
                            inputs=coupled_inputs,
                            outputs=coupled_outputs,)

    def test_02_ratio_SMR_discipline_jacobian(self):
        '''
        Test the gradients of the ratios on a simple techno which uses several ratios (electricity and methane consumption)
        '''
        self.setUp()
        self.techno_name = 'SMR'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_syngas': f'{self.name}',
                   'ns_resource': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.syngas.smr.smr_disc.SMRDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.techno_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_technologies_input_dict.pkl'), 'rb')
        mda_data_input_dict = pickle.load(pkl_file)
        pkl_file.close()

        namespace = f'{self.name}'
        inputs_dict = {}
        coupled_inputs = []
        for key in mda_data_input_dict[self.techno_name].keys():
            # Modify namespace of input 'key' if needed
            if key in ['linearization_mode', 'cache_type', 'cache_file_path', 'sub_mda_class',
                       'max_mda_iter', 'n_processes', 'chain_linearize', 'tolerance', 'use_lu_fact',
                       'warm_start', 'acceleration', 'warm_start_threshold', 'n_subcouplings_parallel',
                       'max_mda_iter_gs', 'relax_factor', 'epsilon0',
                       'linear_solver_MDO', 'linear_solver_MDO_preconditioner', 'linear_solver_MDA', 'linear_solver_MDA_preconditioner', 'linear_solver_MDA_options',
                       'linear_solver_MDO_options', 'group_mda_disciplines',
                       GlossaryCore.TransportCostValue, GlossaryCore.TransportMarginValue, GlossaryCore.YearStart, GlossaryCore.YearEnd,
                       GlossaryCore.EnergyPricesValue, GlossaryCore.EnergyCO2EmissionsValue, GlossaryCore.CO2TaxesValue, GlossaryCore.ResourcesPriceValue,
                       GlossaryCore.RessourcesCO2EmissionsValue, 'scaling_factor_techno_consumption',
                       'scaling_factor_techno_production', 'is_apply_ratio',
                       'is_stream_demand', 'is_apply_resource_ratio',
                       'residuals_history', GlossaryCore.AllStreamsDemandRatioValue, 'all_resource_ratio_usable_demand']:
                inputs_dict[f'{namespace}.{key}'] = mda_data_input_dict[self.techno_name][key]['value']
                if mda_data_input_dict[self.techno_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{key}']
            else:
                inputs_dict[f'{namespace}.{self.techno_name}.{key}'] = mda_data_input_dict[self.techno_name][key]['value']
                if mda_data_input_dict[self.techno_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{self.techno_name}.{key}']

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_technologies_output_dict.pkl'), 'rb')
        mda_data_output_dict = pickle.load(pkl_file)
        pkl_file.close()

        coupled_outputs = []
        for key in mda_data_output_dict[self.techno_name].keys():
            # Modify namespace of output 'key' if needed
            if key in []:
                if mda_data_output_dict[self.techno_name][key]['is_coupling']:
                    coupled_outputs += [f'{namespace}.{key}']
            else:
                if mda_data_output_dict[self.techno_name][key]['is_coupling']:
                    coupled_outputs += [f'{namespace}.{self.techno_name}.{key}']

        coupled_outputs.append(
            f'{namespace}.{self.techno_name}.non_use_capital')
        # Overwrite values for ratios with values from setup
        inputs_dict[f'{namespace}.{GlossaryCore.YearEnd}'] = 2050
        inputs_dict[f'{namespace}.is_apply_ratio'] = self.is_apply_ratio
        inputs_dict[f'{namespace}.is_stream_demand'] = self.is_stream_demand
        inputs_dict[f'{namespace}.is_apply_resource_ratio'] = self.is_apply_resource_ratio
        inputs_dict[f'{namespace}.{GlossaryCore.AllStreamsDemandRatioValue}'] = self.all_streams_demand_ratio
        inputs_dict[f'{namespace}.all_resource_ratio_usable_demand'] = self.all_resource_ratio_usable_demand

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.techno_name}')[0].mdo_discipline_wrapp.mdo_discipline
        # AbstractJacobianUnittest.DUMP_JACOBIAN = True

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_ratio_{self.techno_name}.pkl',
                            discipline=disc, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,local_data = disc.local_data,
                            inputs=coupled_inputs,
                            outputs=coupled_outputs,)

    def test_03_ratio_CropEnergy_discipline_jacobian(self):
        '''
        Test the gradients of the ratios on CropEnergy techno since it has special gradients
        '''
        self.setUp()
        self.techno_name = 'CropEnergy'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_biomass_dry': f'{self.name}',
                   'ns_witness': f'{self.name}',
                   'ns_resource': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.biomass_dry.crop_energy.crop_energy_disc.CropEnergyDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.techno_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_technologies_input_dict.pkl'), 'rb')
        mda_data_input_dict = pickle.load(pkl_file)
        pkl_file.close()

        namespace = f'{self.name}'
        inputs_dict = {}
        coupled_inputs = []
        for key in mda_data_input_dict[self.techno_name].keys():
            # Modify namespace of input 'key' if needed
            if key in ['linearization_mode', 'cache_type', 'cache_file_path', 'sub_mda_class',
                       'max_mda_iter', 'n_processes', 'chain_linearize', 'tolerance', 'use_lu_fact',
                       'warm_start', 'acceleration', 'warm_start_threshold', 'n_subcouplings_parallel',
                       'max_mda_iter_gs', 'relax_factor', 'epsilon0',
                       'linear_solver_MDO', 'linear_solver_MDO_preconditioner', 'linear_solver_MDA', 'linear_solver_MDA_preconditioner',  'linear_solver_MDA_options',
                       'linear_solver_MDO_options', 'group_mda_disciplines',
                       GlossaryCore.TransportCostValue, GlossaryCore.TransportMarginValue, GlossaryCore.YearStart, GlossaryCore.YearEnd,
                       GlossaryCore.EnergyPricesValue, GlossaryCore.EnergyCO2EmissionsValue, GlossaryCore.CO2TaxesValue, GlossaryCore.ResourcesPriceValue,
                       GlossaryCore.RessourcesCO2EmissionsValue, 'scaling_factor_techno_consumption',
                       'scaling_factor_techno_production', 'is_apply_ratio',
                       'is_stream_demand', 'is_apply_resource_ratio',
                       'residuals_history', GlossaryCore.AllStreamsDemandRatioValue, 'all_resource_ratio_usable_demand']:
                inputs_dict[f'{namespace}.{key}'] = mda_data_input_dict[self.techno_name][key]['value']
                if mda_data_input_dict[self.techno_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{key}']
            else:
                inputs_dict[f'{namespace}.{self.techno_name}.{key}'] = mda_data_input_dict[self.techno_name][key]['value']
                if mda_data_input_dict[self.techno_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{self.techno_name}.{key}']

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_technologies_output_dict.pkl'), 'rb')
        mda_data_output_dict = pickle.load(pkl_file)
        pkl_file.close()

        coupled_outputs = []
        for key in mda_data_output_dict[self.techno_name].keys():
            # Modify namespace of output 'key' if needed
            if key in []:
                if mda_data_output_dict[self.techno_name][key]['is_coupling']:
                    coupled_outputs += [f'{namespace}.{key}']
            else:
                if mda_data_output_dict[self.techno_name][key]['is_coupling']:
                    coupled_outputs += [f'{namespace}.{self.techno_name}.{key}']
        coupled_outputs.append(
            f'{namespace}.{self.techno_name}.non_use_capital')
        # Overwrite values for ratios with values from setup
        inputs_dict[f'{namespace}.{GlossaryCore.YearEnd}'] = 2050
        inputs_dict[f'{namespace}.is_apply_ratio'] = self.is_apply_ratio
        inputs_dict[f'{namespace}.is_stream_demand'] = self.is_stream_demand
        inputs_dict[f'{namespace}.is_apply_resource_ratio'] = self.is_apply_resource_ratio
        inputs_dict[f'{namespace}.{GlossaryCore.AllStreamsDemandRatioValue}'] = self.all_streams_demand_ratio
        inputs_dict[f'{namespace}.all_resource_ratio_usable_demand'] = self.all_resource_ratio_usable_demand
        inputs_dict[f'{namespace}.land_surface_for_food_df'] = pd.DataFrame({GlossaryCore.Years: np.arange(2020, 2051),
                                              'Agriculture total (Gha)': np.ones(31) * 4.8})

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.techno_name}')[0].mdo_discipline_wrapp.mdo_discipline
        #AbstractJacobianUnittest.DUMP_JACOBIAN = True

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_ratio_{self.techno_name}.pkl',
                            discipline=disc, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,local_data = disc.local_data,
                            inputs=coupled_inputs,
                            outputs=coupled_outputs,)

    def test_04_ratio_UnmanagedWood_discipline_jacobian(self):
        '''
        Test the gradients of the ratios on UnmanagedWood techno since it has special gradients
        '''
        self.setUp()
        self.techno_name = 'UnmanagedWood'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_biomass_dry': f'{self.name}',
                   'ns_witness': f'{self.name}',
                   'ns_resource': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.biomass_dry.unmanaged_wood.unmanaged_wood_disc.UnmanagedWoodDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.techno_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_technologies_input_dict.pkl'), 'rb')
        mda_data_input_dict = pickle.load(pkl_file)
        pkl_file.close()

        namespace = f'{self.name}'
        inputs_dict = {}
        coupled_inputs = []
        for key in mda_data_input_dict[self.techno_name].keys():
            # Modify namespace of input 'key' if needed
            if key in ['linearization_mode', 'cache_type', 'cache_file_path', 'sub_mda_class',
                       'max_mda_iter', 'n_processes', 'chain_linearize', 'tolerance', 'use_lu_fact',
                       'warm_start', 'acceleration', 'warm_start_threshold', 'n_subcouplings_parallel',
                       'max_mda_iter_gs', 'relax_factor', 'epsilon0',
                       'linear_solver_MDO', 'linear_solver_MDO_preconditioner', 'linear_solver_MDA', 'linear_solver_MDA_preconditioner', 'linear_solver_MDA_options',
                       'linear_solver_MDO_options', 'group_mda_disciplines',
                       GlossaryCore.TransportCostValue, GlossaryCore.TransportMarginValue, GlossaryCore.YearStart, GlossaryCore.YearEnd,
                       GlossaryCore.EnergyPricesValue, GlossaryCore.EnergyCO2EmissionsValue, GlossaryCore.CO2TaxesValue, GlossaryCore.ResourcesPriceValue,
                       GlossaryCore.RessourcesCO2EmissionsValue, 'scaling_factor_techno_consumption',
                       'scaling_factor_techno_production', 'is_apply_ratio',
                       'is_stream_demand', 'is_apply_resource_ratio',
                       'residuals_history', GlossaryCore.AllStreamsDemandRatioValue, 'all_resource_ratio_usable_demand']:
                inputs_dict[f'{namespace}.{key}'] = mda_data_input_dict[self.techno_name][key]['value']
                if mda_data_input_dict[self.techno_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{key}']
            else:
                inputs_dict[f'{namespace}.{self.techno_name}.{key}'] = mda_data_input_dict[self.techno_name][key]['value']
                if mda_data_input_dict[self.techno_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{self.techno_name}.{key}']

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_technologies_output_dict.pkl'), 'rb')
        mda_data_output_dict = pickle.load(pkl_file)
        pkl_file.close()

        coupled_outputs = []
        for key in mda_data_output_dict[self.techno_name].keys():
            # Modify namespace of output 'key' if needed
            if key in []:
                if mda_data_output_dict[self.techno_name][key]['is_coupling']:
                    coupled_outputs += [f'{namespace}.{key}']
            else:
                if mda_data_output_dict[self.techno_name][key]['is_coupling']:
                    coupled_outputs += [f'{namespace}.{self.techno_name}.{key}']
        coupled_outputs.append(
            f'{namespace}.{self.techno_name}.non_use_capital')
        # Overwrite values for ratios with values from setup
        inputs_dict[f'{namespace}.{GlossaryCore.YearEnd}'] = 2050
        inputs_dict[f'{namespace}.is_apply_ratio'] = self.is_apply_ratio
        inputs_dict[f'{namespace}.is_stream_demand'] = self.is_stream_demand
        inputs_dict[f'{namespace}.is_apply_resource_ratio'] = self.is_apply_resource_ratio
        inputs_dict[f'{namespace}.{GlossaryCore.AllStreamsDemandRatioValue}'] = self.all_streams_demand_ratio
        inputs_dict[f'{namespace}.all_resource_ratio_usable_demand'] = self.all_resource_ratio_usable_demand

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.techno_name}')[0].mdo_discipline_wrapp.mdo_discipline
        #AbstractJacobianUnittest.DUMP_JACOBIAN = True

        # self.check_jacobian(location=dirname(__file__), filename=f'jacobian_ratio_{self.techno_name}.pkl',
        # discipline=disc, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,
        # inputs=coupled_inputs,
        # outputs=coupled_outputs,)

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_ratio_{self.techno_name}.pkl',
                            discipline=disc, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,local_data = disc.local_data,
                            inputs=coupled_inputs,
                            outputs=coupled_outputs,)

    def test_05_ratio_WaterGasShift_discipline_jacobian(self):
        '''
        Test the gradients of the ratios on WaterGasShift techno since it has special gradients
        '''
        self.setUp()
        self.techno_name = 'WaterGasShift'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_hydrogen': f'{self.name}',
                   'ns_syngas': f'{self.name}',
                   'ns_energy_mix': f'{self.name}',
                   'ns_resource': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.gaseous_hydrogen.water_gas_shift.water_gas_shift_disc.WaterGasShiftDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.techno_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_technologies_input_dict.pkl'), 'rb')
        mda_data_input_dict = pickle.load(pkl_file)
        pkl_file.close()

        namespace = f'{self.name}'
        inputs_dict = {}
        coupled_inputs = []
        for key in mda_data_input_dict[self.techno_name].keys():
            # Modify namespace of input 'key' if needed
            if key in ['linearization_mode', 'cache_type', 'cache_file_path', 'sub_mda_class',
                       'max_mda_iter', 'n_processes', 'chain_linearize', 'tolerance', 'use_lu_fact',
                       'warm_start', 'acceleration', 'warm_start_threshold', 'n_subcouplings_parallel',
                       'max_mda_iter_gs', 'relax_factor', 'epsilon0',
                       'linear_solver_MDO', 'linear_solver_MDO_preconditioner', 'linear_solver_MDA', 'linear_solver_MDA_preconditioner',  'linear_solver_MDA_options',
                       'linear_solver_MDO_options', 'group_mda_disciplines',
                       GlossaryCore.TransportCostValue, GlossaryCore.TransportMarginValue, GlossaryCore.YearStart, GlossaryCore.YearEnd,
                       GlossaryCore.EnergyPricesValue, GlossaryCore.EnergyCO2EmissionsValue, GlossaryCore.CO2TaxesValue, GlossaryCore.ResourcesPriceValue,
                       GlossaryCore.RessourcesCO2EmissionsValue, 'scaling_factor_techno_consumption',
                       'scaling_factor_techno_production', 'is_apply_ratio',
                       'is_stream_demand', 'is_apply_resource_ratio', 'syngas_ratio',
                       'residuals_history', GlossaryCore.AllStreamsDemandRatioValue, 'all_resource_ratio_usable_demand']:
                inputs_dict[f'{namespace}.{key}'] = mda_data_input_dict[self.techno_name][key]['value']
                if mda_data_input_dict[self.techno_name][key]['is_coupling'] and 'resources' not in key:
                    coupled_inputs += [f'{namespace}.{key}']
            else:
                inputs_dict[f'{namespace}.{self.techno_name}.{key}'] = mda_data_input_dict[self.techno_name][key]['value']
                if mda_data_input_dict[self.techno_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{self.techno_name}.{key}']

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_technologies_output_dict.pkl'), 'rb')
        mda_data_output_dict = pickle.load(pkl_file)
        pkl_file.close()

        coupled_outputs = []
        for key in mda_data_output_dict[self.techno_name].keys():
            # Modify namespace of output 'key' if needed
            if key in []:
                if mda_data_output_dict[self.techno_name][key]['is_coupling']:
                    coupled_outputs += [f'{namespace}.{key}']
            elif key in ['flue_gas_co2_ratio', ]:
                pass
            else:
                if mda_data_output_dict[self.techno_name][key]['is_coupling']:
                    coupled_outputs += [f'{namespace}.{self.techno_name}.{key}']
        coupled_outputs.append(
            f'{namespace}.{self.techno_name}.non_use_capital')
        # Overwrite values for ratios with values from setup
        inputs_dict[f'{namespace}.{GlossaryCore.YearEnd}'] = 2050
        inputs_dict[f'{namespace}.is_apply_ratio'] = self.is_apply_ratio
        inputs_dict[f'{namespace}.is_stream_demand'] = self.is_stream_demand
        inputs_dict[f'{namespace}.is_apply_resource_ratio'] = self.is_apply_resource_ratio
        inputs_dict[f'{namespace}.{GlossaryCore.AllStreamsDemandRatioValue}'] = self.all_streams_demand_ratio
        inputs_dict[f'{namespace}.all_resource_ratio_usable_demand'] = self.all_resource_ratio_usable_demand

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.techno_name}')[0].mdo_discipline_wrapp.mdo_discipline
        # AbstractJacobianUnittest.DUMP_JACOBIAN = True

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_ratio_{self.techno_name}.pkl',
                            discipline=disc, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,local_data = disc.local_data,
                            inputs=coupled_inputs,
                            outputs=coupled_outputs,)

    def test_06_ratio_FischerTropsch_discipline_jacobian(self):
        '''
        Test the gradients of the ratios on FischerTropsch techno since it has special gradients
        '''
        self.setUp()
        self.techno_name = 'FischerTropsch'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_liquid_fuel': self.name,
                   'ns_syngas': self.name,
                   'ns_resource': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.liquid_fuel.fischer_tropsch.fischer_tropsch_disc.FischerTropschDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.techno_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_technologies_input_dict.pkl'), 'rb')
        mda_data_input_dict = pickle.load(pkl_file)
        pkl_file.close()

        namespace = f'{self.name}'
        inputs_dict = {}
        coupled_inputs = []
        for key in mda_data_input_dict[self.techno_name].keys():
            # Modify namespace of input 'key' if needed
            if key in ['linearization_mode', 'cache_type', 'cache_file_path', 'sub_mda_class',
                       'max_mda_iter', 'n_processes', 'chain_linearize', 'tolerance', 'use_lu_fact',
                       'warm_start', 'acceleration', 'warm_start_threshold', 'n_subcouplings_parallel',
                       'max_mda_iter_gs', 'relax_factor', 'epsilon0',
                       'linear_solver_MDO', 'linear_solver_MDO_preconditioner', 'linear_solver_MDA', 'linear_solver_MDA_preconditioner',  'linear_solver_MDA_options',
                       'linear_solver_MDO_options', 'group_mda_disciplines',
                       GlossaryCore.TransportCostValue, GlossaryCore.TransportMarginValue, GlossaryCore.YearStart, GlossaryCore.YearEnd,
                       GlossaryCore.EnergyPricesValue, GlossaryCore.EnergyCO2EmissionsValue, GlossaryCore.CO2TaxesValue, GlossaryCore.ResourcesPriceValue,
                       GlossaryCore.RessourcesCO2EmissionsValue, 'scaling_factor_techno_consumption',
                       'scaling_factor_techno_production', 'is_apply_ratio',
                       'is_stream_demand', 'is_apply_resource_ratio', 'syngas_ratio',
                       'residuals_history', GlossaryCore.AllStreamsDemandRatioValue, 'all_resource_ratio_usable_demand']:
                inputs_dict[f'{namespace}.{key}'] = mda_data_input_dict[self.techno_name][key]['value']
                if mda_data_input_dict[self.techno_name][key]['is_coupling'] and 'resources' not in key:
                    coupled_inputs += [f'{namespace}.{key}']
            else:
                inputs_dict[f'{namespace}.{self.techno_name}.{key}'] = mda_data_input_dict[self.techno_name][key]['value']
                if mda_data_input_dict[self.techno_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{self.techno_name}.{key}']

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_technologies_output_dict.pkl'), 'rb')
        mda_data_output_dict = pickle.load(pkl_file)
        pkl_file.close()

        coupled_outputs = []
        for key in mda_data_output_dict[self.techno_name].keys():
            # Modify namespace of output 'key' if needed
            if key in []:
                if mda_data_output_dict[self.techno_name][key]['is_coupling']:
                    coupled_outputs += [f'{namespace}.{key}']
            elif key in ['flue_gas_co2_ratio', ]:
                pass
            else:
                if mda_data_output_dict[self.techno_name][key]['is_coupling']:
                    coupled_outputs += [f'{namespace}.{self.techno_name}.{key}']
        coupled_outputs.append(
            f'{namespace}.{self.techno_name}.non_use_capital')
        # Overwrite values for ratios with values from setup
        inputs_dict[f'{namespace}.{GlossaryCore.YearEnd}'] = 2050
        inputs_dict[f'{namespace}.is_apply_ratio'] = self.is_apply_ratio
        inputs_dict[f'{namespace}.is_stream_demand'] = self.is_stream_demand
        inputs_dict[f'{namespace}.is_apply_resource_ratio'] = self.is_apply_resource_ratio
        inputs_dict[f'{namespace}.{GlossaryCore.AllStreamsDemandRatioValue}'] = self.all_streams_demand_ratio
        inputs_dict[f'{namespace}.all_resource_ratio_usable_demand'] = self.all_resource_ratio_usable_demand

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.techno_name}')[0].mdo_discipline_wrapp.mdo_discipline
        # AbstractJacobianUnittest.DUMP_JACOBIAN = True
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_ratio_{self.techno_name}.pkl',
                            discipline=disc, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,local_data = disc.local_data,
                            inputs=coupled_inputs,
                            outputs=coupled_outputs,)

    def test_07_ratio_CalciumLooping_discipline_jacobian(self):
        '''
        Test the gradients of the ratios on CalciumLooping techno since CarbonCapture technos have special gradients
        '''
        self.setUp()
        self.techno_name = 'flue_gas_capture.CalciumLooping'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_carbon_capture': self.name,
                   'ns_flue_gas': f'{self.name}',
                   'ns_resource': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.carbon_capture.flue_gas_capture.calcium_looping.calcium_looping_disc.CalciumLoopingDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.techno_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_technologies_input_dict.pkl'), 'rb')
        mda_data_input_dict = pickle.load(pkl_file)
        pkl_file.close()

        namespace = f'{self.name}'
        inputs_dict = {}
        coupled_inputs = []
        for key in mda_data_input_dict[self.techno_name].keys():
            # Modify namespace of input 'key' if needed
            if key in ['linearization_mode', 'cache_type', 'cache_file_path', 'sub_mda_class',
                       'max_mda_iter', 'n_processes', 'chain_linearize', 'tolerance', 'use_lu_fact',
                       'warm_start', 'acceleration', 'warm_start_threshold', 'n_subcouplings_parallel',
                       'max_mda_iter_gs', 'relax_factor', 'epsilon0',
                       'linear_solver_MDO', 'linear_solver_MDO_preconditioner', 'linear_solver_MDA', 'linear_solver_MDA_preconditioner',  'linear_solver_MDA_options',
                       'linear_solver_MDO_options', 'group_mda_disciplines',
                       GlossaryCore.TransportCostValue, GlossaryCore.TransportMarginValue, GlossaryCore.YearStart, GlossaryCore.YearEnd,
                       GlossaryCore.EnergyPricesValue, GlossaryCore.EnergyCO2EmissionsValue, GlossaryCore.CO2TaxesValue, GlossaryCore.ResourcesPriceValue,
                       GlossaryCore.RessourcesCO2EmissionsValue, 'scaling_factor_techno_consumption',
                       'scaling_factor_techno_production', 'is_apply_ratio',
                       'is_stream_demand', 'is_apply_resource_ratio', GlossaryCore.FlueGasMean,
                       'residuals_history', GlossaryCore.AllStreamsDemandRatioValue, 'all_resource_ratio_usable_demand']:
                inputs_dict[f'{namespace}.{key}'] = mda_data_input_dict[self.techno_name][key]['value']
                if mda_data_input_dict[self.techno_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{key}']
            else:
                inputs_dict[f'{namespace}.{self.techno_name}.{key}'] = mda_data_input_dict[self.techno_name][key]['value']
                if mda_data_input_dict[self.techno_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{self.techno_name}.{key}']

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_technologies_output_dict.pkl'), 'rb')
        mda_data_output_dict = pickle.load(pkl_file)
        pkl_file.close()

        coupled_outputs = []
        for key in mda_data_output_dict[self.techno_name].keys():
            # Modify namespace of output 'key' if needed
            if key in []:
                if mda_data_output_dict[self.techno_name][key]['is_coupling']:
                    coupled_outputs += [f'{namespace}.{key}']
            else:
                if mda_data_output_dict[self.techno_name][key]['is_coupling']:
                    coupled_outputs += [f'{namespace}.{self.techno_name}.{key}']
        coupled_outputs.append(
            f'{namespace}.{self.techno_name}.non_use_capital')
        # Overwrite values for ratios with values from setup
        inputs_dict[f'{namespace}.{GlossaryCore.YearEnd}'] = 2050
        inputs_dict[f'{namespace}.is_apply_ratio'] = self.is_apply_ratio
        inputs_dict[f'{namespace}.is_stream_demand'] = self.is_stream_demand
        inputs_dict[f'{namespace}.is_apply_resource_ratio'] = self.is_apply_resource_ratio
        inputs_dict[f'{namespace}.{GlossaryCore.AllStreamsDemandRatioValue}'] = self.all_streams_demand_ratio
        inputs_dict[f'{namespace}.all_resource_ratio_usable_demand'] = self.all_resource_ratio_usable_demand

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.techno_name}')[0].mdo_discipline_wrapp.mdo_discipline
        # AbstractJacobianUnittest.DUMP_JACOBIAN = True

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_ratio_{self.techno_name}.pkl',
                            discipline=disc, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,local_data = disc.local_data,
                            inputs=coupled_inputs,
                            outputs=coupled_outputs,)

    def test_08_gaseous_hydrogen_discipline_jacobian(self):
        '''
        Test the gradients of the ratios on Gaseous Hydrogen energy to test the gradients on a stream
        '''
        self.setUp()
        self.energy_name = 'hydrogen.gaseous_hydrogen'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': f'{self.name}',
                   'ns_hydrogen': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_resource': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.stream_type.energy_disciplines.gaseous_hydrogen_disc.GaseousHydrogenDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.energy_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_streams_input_dict.pkl'), 'rb')
        mda_data_input_dict = pickle.load(pkl_file)
        pkl_file.close()

        namespace = f'{self.name}'
        inputs_dict = {}
        coupled_inputs = []
        for key in mda_data_input_dict[self.energy_name].keys():
            if key in [GlossaryCore.techno_list, GlossaryCore.CO2TaxesValue, GlossaryCore.YearStart, GlossaryCore.YearEnd,
                       'scaling_factor_energy_production', 'scaling_factor_energy_consumption',
                       'scaling_factor_techno_consumption', 'scaling_factor_techno_production',]:
                inputs_dict[f'{namespace}.{key}'] = mda_data_input_dict[self.energy_name][key]['value']
                if mda_data_input_dict[self.energy_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{key}']
            else:
                inputs_dict[f'{namespace}.{self.energy_name}.{key}'] = mda_data_input_dict[self.energy_name][key]['value']
                if mda_data_input_dict[self.energy_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{self.energy_name}.{key}']

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_streams_output_dict.pkl'), 'rb')
        mda_data_output_dict = pickle.load(pkl_file)
        pkl_file.close()

        coupled_outputs = []
        for key in mda_data_output_dict[self.energy_name].keys():
            if mda_data_output_dict[self.energy_name][key]['is_coupling']:
                coupled_outputs += [f'{namespace}.{self.energy_name}.{key}']

        technos = inputs_dict[f"{self.name}.technologies_list"]
        techno_capital = pd.DataFrame({
            GlossaryCore.Years: self.years,
            GlossaryCore.Capital: 20000 * np.ones_like(self.years)
        })
        for techno in technos:
            inputs_dict[
                f"{self.name}.{self.energy_name}.{techno}.{GlossaryEnergy.TechnoCapitalDfValue}"] = techno_capital
            coupled_inputs.append(f"{self.name}.{self.energy_name}.{techno}.{GlossaryEnergy.TechnoCapitalDfValue}")

        coupled_outputs.append(f"{self.name}.{self.energy_name}.{GlossaryEnergy.EnergyTypeCapitalDfValue}")

        # Overwrite values for ratios with values from setup
        inputs_dict[f'{namespace}.{GlossaryCore.YearEnd}'] = 2050
        inputs_dict[f'{namespace}.is_apply_ratio'] = self.is_apply_ratio
        inputs_dict[f'{namespace}.is_stream_demand'] = self.is_stream_demand
        inputs_dict[f'{namespace}.is_apply_resource_ratio'] = self.is_apply_resource_ratio
        inputs_dict[f'{namespace}.{GlossaryCore.AllStreamsDemandRatioValue}'] = self.all_streams_demand_ratio
        inputs_dict[f'{namespace}.all_resource_ratio_usable_demand'] = self.all_resource_ratio_usable_demand

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.energy_name}')[0].mdo_discipline_wrapp.mdo_discipline
        # AbstractJacobianUnittest.DUMP_JACOBIAN = True

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_ratio_{self.energy_name}.pkl',
                            discipline=disc, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,local_data = disc.local_data,
                            inputs=coupled_inputs,
                            outputs=coupled_outputs,)

    def _test_09_carbon_capture_discipline_jacobian(self):
        '''
        Test the gradients of the ratios on Carbon Capture stream since it has special gradients.
        Also, set the inputs so that the limited flue gas case is tested.
        '''
        self.setUp()
        self.energy_name = 'carbon_capture'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_energy_mix': f'{self.name}',
                   'ns_flue_gas': f'{self.name}',
                   'ns_carbon_capture': f'{self.name}',
                   'ns_public': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.stream_type.carbon_disciplines.carbon_capture_disc.CarbonCaptureDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.energy_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_streams_input_dict.pkl'), 'rb')
        mda_data_input_dict = pickle.load(pkl_file)
        pkl_file.close()

        namespace = f'{self.name}'
        inputs_dict = {}
        coupled_inputs = []
        for key in mda_data_input_dict[self.energy_name].keys():
            if key in [GlossaryCore.techno_list, GlossaryCore.CO2TaxesValue, GlossaryCore.YearStart, GlossaryCore.YearEnd,
                       'scaling_factor_energy_production', 'scaling_factor_energy_consumption',
                       'scaling_factor_techno_consumption', 'scaling_factor_techno_production',
                       'flue_gas_prod_ratio', 'flue_gas_production',  'ratio_objective' ]:
                inputs_dict[f'{namespace}.{key}'] = mda_data_input_dict[self.energy_name][key]['value']
                if mda_data_input_dict[self.energy_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{key}']
            else:
                inputs_dict[f'{namespace}.{self.energy_name}.{key}'] = mda_data_input_dict[self.energy_name][key]['value']
                if mda_data_input_dict[self.energy_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{self.energy_name}.{key}']

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_streams_output_dict.pkl'), 'rb')
        mda_data_output_dict = pickle.load(pkl_file)
        pkl_file.close()

        coupled_outputs = []
        for key in mda_data_output_dict[self.energy_name].keys():
            if mda_data_output_dict[self.energy_name][key]['is_coupling']:
                coupled_outputs += [f'{namespace}.{self.energy_name}.{key}']

        # Overwrite values for ratios with values from setup
        inputs_dict[f'{namespace}.{GlossaryCore.YearEnd}'] = 2050
        inputs_dict[f'{namespace}.is_apply_ratio'] = self.is_apply_ratio
        inputs_dict[f'{namespace}.is_stream_demand'] = self.is_stream_demand
        inputs_dict[f'{namespace}.is_apply_resource_ratio'] = self.is_apply_resource_ratio
        inputs_dict[f'{namespace}.{GlossaryCore.AllStreamsDemandRatioValue}'] = self.all_streams_demand_ratio
        inputs_dict[f'{namespace}.all_resource_ratio_usable_demand'] = self.all_resource_ratio_usable_demand
        # Overwrite CalciumLooping techno production to test the flue_gas
        # limited case
        inputs_dict[f'{namespace}.{self.energy_name}.flue_gas_capture.CalciumLooping.techno_production'][
            'carbon_capture (Mt)'] *= np.linspace(1.0, 5.0, len(self.years))
        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.energy_name}')[0].mdo_discipline_wrapp.mdo_discipline
        # AbstractJacobianUnittest.DUMP_JACOBIAN = True

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_ratio_cc{self.energy_name}.pkl',
                            discipline=disc, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,local_data = disc.local_data,
                            inputs=coupled_inputs,
                            outputs=coupled_outputs,)

    def _test_10_energy_mix_discipline_jacobian(self):
        '''
        Test the gradients of the ratios on EnergyMix discipline.
        For now do not include it to the test routine (not sure how volatile this test it)
        '''
        self.setUp()
        self.model_name = 'EnergyMix'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_energy_mix': f'{self.name}',
                   'ns_public': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        repo = 'energy_models.sos_processes.energy.MDA'
        builder = self.ee.factory.get_builder_from_process(
            repo, 'energy_process_v0')

        self.ee.factory.set_builders_to_coupling_builder(builder)
        self.ee.configure()
        usecase = Study(execution_engine=self.ee)
        usecase.study_name = self.name
        values_dict = usecase.setup_usecase()

        self.ee.display_treeview_nodes()
        full_values_dict = {}
        for dict_v in values_dict:
            full_values_dict.update(dict_v)

        full_values_dict[f'{self.name}.{GlossaryCore.YearEnd}'] = 2050
        full_values_dict[f'{self.name}.epsilon0'] = 1.0
        full_values_dict[f'{self.name}.tolerance'] = 1.0e-8
        full_values_dict[f'{self.name}.max_mda_iter'] = 1
        full_values_dict[f'{self.name}.sub_mda_class'] = 'MDAGaussSeidel'
        # Overwrite values for ratios with values from setup
        full_values_dict[f'{self.name}.is_apply_ratio'] = self.is_apply_ratio
        full_values_dict[f'{self.name}.is_stream_demand'] = self.is_stream_demand
        full_values_dict[f'{self.name}.is_apply_resource_ratio'] = self.is_apply_resource_ratio
        full_values_dict[f'{self.name}.{GlossaryCore.AllStreamsDemandRatioValue}'] = self.all_streams_demand_ratio
        full_values_dict[f'{self.name}.all_resource_ratio_usable_demand'] = self.all_resource_ratio_usable_demand

        self.ee.load_study_from_input_dict(full_values_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0].mdo_discipline_wrapp.mdo_discipline

        # Get coupled inputs and outputs
        full_inputs = disc.get_input_data_names()
        full_outputs = disc.get_output_data_names()
        # For the coupled inputs and outputs, test inputs/outputs on all
        # namespaces
        coupled_inputs, coupled_outputs = [], []
        namespaces = [f'{self.name}.', f'{self.name}.{self.model_name}.', ]
        for namespace in namespaces:
            coupled_inputs += [input for input in full_inputs if self.ee.dm.get_data(
                input, 'coupling')]
            coupled_outputs += [output for output in full_outputs if self.ee.dm.get_data(
                output, 'coupling')]

        #AbstractJacobianUnittest.DUMP_JACOBIAN = True

        coupled_inputs = [
            'Test_Ratio.EnergyMix.liquid_fuel.{GlossaryCore.EnergyConsumptionWithoutRatioValue}', ]
        #'Test_Ratio.EnergyMix.methane.{GlossaryCore.EnergyProcductionWithoutRatioValue}']
        coupled_outputs = ['Test_Ratio.EnergyMix.{GlossaryCore.AllStreamsDemandRatioValue}']

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_ratio_{self.model_name}.pkl',
                            discipline=disc, step=1.0e-16, derr_approx='complex_step',local_data = disc.local_data,
                            inputs=coupled_inputs,  outputs=coupled_outputs,)

    def _test_11_energy_mix_discipline_in_WITNESSFull_jacobian(self):
        '''
        Test the gradients of the ratios on EnergyMix discipline in WITNESS Full process.
        For now do not include it to the test routine (not sure how volatile this test it)
        '''
        self.setUp()
        self.model_name = 'EnergyMix'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_energy_mix': f'{self.name}',
                   'ns_public': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        repo = 'climateeconomics.sos_processes.iam.witness'
        builder = self.ee.factory.get_builder_from_process(
            repo, 'witness_optim_sub_process')

        self.ee.factory.set_builders_to_coupling_builder(builder)
        self.ee.configure()
        usecase = WITNESSFull_subprocess(execution_engine=self.ee)
        usecase.study_name = self.name
        values_dict = usecase.setup_usecase()

        self.ee.display_treeview_nodes()
        full_values_dict = {}
        for dict_v in values_dict:
            full_values_dict.update(dict_v)

        full_values_dict[f'{self.name}.{GlossaryCore.YearEnd}'] = 2050
        full_values_dict[f'{self.name}.{usecase.coupling_name}.epsilon0'] = 1.0
        full_values_dict[f'{self.name}.{usecase.coupling_name}.tolerance'] = 1.0e-8
        full_values_dict[f'{self.name}.{usecase.coupling_name}.sub_mda_class'] = 'MDANewtonRaphson'
        full_values_dict[f'{self.name}.{usecase.coupling_name}.max_mda_iter'] = 1
        # Overwrite values for ratios with values from setup
        full_values_dict[f'{self.name}.{usecase.coupling_name}.{usecase.extra_name}.is_apply_ratio'] = self.is_apply_ratio
        full_values_dict[f'{self.name}.{usecase.coupling_name}.{usecase.extra_name}.is_stream_demand'] = self.is_stream_demand
        full_values_dict[f'{self.name}.{usecase.coupling_name}.{usecase.extra_name}.is_apply_resource_ratio'] = self.is_apply_resource_ratio
        full_values_dict[f'{self.name}.{usecase.coupling_name}.{usecase.extra_name}.{GlossaryCore.AllStreamsDemandRatioValue}'] = self.all_streams_demand_ratio
        full_values_dict[f'{self.name}.{usecase.coupling_name}.{usecase.extra_name}.all_resource_ratio_usable_demand'] = self.all_resource_ratio_usable_demand

        # Load design_var crash
        ds_crash = pd.read_csv('data_tests/design_space_last_ite_crash.csv')
        full_values_dict[f'{self.name}.design_space'] = ds_crash
        self.ee.load_study_from_input_dict(full_values_dict)

        self.ee.execute()

        # EnergyMix
        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{usecase.coupling_name}.{usecase.extra_name}.{self.model_name}')[0].mdo_discipline_wrapp.mdo_discipline

        # Get coupled inputs and outputs
        full_inputs = disc.get_input_data_names()
        full_outputs = disc.get_output_data_names()
        # For the coupled inputs and outputs, test inputs/outputs on all
        # namespaces
        coupled_inputs, coupled_outputs = [], []
        namespaces = [f'{self.name}.', f'{self.name}.{usecase.coupling_name}.',
                      f'{self.name}.{usecase.coupling_name}.{usecase.extra_name}.',
                      f'{self.name}.{usecase.coupling_name}.{usecase.extra_name}.{self.model_name}.']
        for namespace in namespaces:
            coupled_inputs += [input for input in full_inputs if self.ee.dm.get_data(
                input, 'coupling')]
            coupled_outputs += [output for output in full_outputs if self.ee.dm.get_data(
                output, 'coupling')]

        energy_list = full_values_dict[f'{self.name}.{usecase.coupling_name}.{usecase.extra_name}.{GlossaryCore.energy_list}']
        coupled_inputs = []
        for energy in energy_list:
            coupled_inputs += [
                f'{self.name}.{usecase.coupling_name}.{usecase.extra_name}.{self.model_name}.{energy}.{GlossaryCore.EnergyProcductionWithoutRatioValue}', ]
            coupled_inputs += [
                f'{self.name}.{usecase.coupling_name}.{usecase.extra_name}.{self.model_name}.{energy}.{GlossaryCore.EnergyConsumptionWithoutRatioValue}', ]
        # coupled_inputs = [
            # f'{self.name}.{usecase.coupling_name}.{usecase.extra_name}.{self.model_name}.liquid_fuel.{GlossaryCore.EnergyConsumptionWithoutRatioValue}', ]
        # #'Test_Ratio.EnergyMix.methane.{GlossaryCore.EnergyProcductionWithoutRatioValue}']
        coupled_outputs = [
            f'{self.name}.{usecase.coupling_name}.{usecase.extra_name}.{self.model_name}.{GlossaryCore.AllStreamsDemandRatioValue}']

        # Techno
        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{usecase.coupling_name}.{usecase.extra_name}.{self.model_name}.liquid_fuel.FischerTropsch')[0]

        # Get coupled inputs and outputs
        full_inputs = disc.get_input_data_names()
        full_outputs = disc.get_output_data_names()
        # For the coupled inputs and outputs, test inputs/outputs on all
        # namespaces
        coupled_inputs, coupled_outputs = [], []
        namespaces = [f'{self.name}.', f'{self.name}.{usecase.coupling_name}.',
                      f'{self.name}.{usecase.coupling_name}.{usecase.extra_name}.',
                      f'{self.name}.{usecase.coupling_name}.{usecase.extra_name}.{self.model_name}.']
        for namespace in namespaces:
            coupled_inputs += [input for input in full_inputs if self.ee.dm.get_data(
                input, 'coupling')]
            coupled_outputs += [output for output in full_outputs if self.ee.dm.get_data(
                output, 'coupling')]

        coupled_inputs = [
            f'{self.name}.{usecase.coupling_name}.{usecase.extra_name}.{GlossaryCore.AllStreamsDemandRatioValue}']
        #AbstractJacobianUnittest.DUMP_JACOBIAN = True

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_ratio_{self.model_name}_WITNESSFull.pkl',
                            discipline=disc, step=1.0e-16, derr_approx='complex_step',local_data = disc.local_data,
                            inputs=coupled_inputs,  outputs=coupled_outputs,)

    def test_12_energy_mix_all_stream_demand_ratio_discipline_jacobian(self):
        '''
        Test the gradients of the ratios on EnergyMix discipline.
        For now do not include it to the test routine (not sure how volatile this test it)
        '''
        self.setUp()
        self.model_name = 'EnergyMix'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_energy_mix': f'{self.name}',
                   'ns_public': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        repo = 'energy_models.sos_processes.energy.MDA'
        builder = self.ee.factory.get_builder_from_process(
            repo, 'energy_process_v0')

        self.ee.factory.set_builders_to_coupling_builder(builder)
        self.ee.configure()
        usecase = Study(execution_engine=self.ee)
        usecase.study_name = self.name
        values_dict = usecase.setup_usecase()

        self.ee.display_treeview_nodes()
        full_values_dict = {}
        for dict_v in values_dict:
            full_values_dict.update(dict_v)

        full_values_dict[f'{self.name}.{GlossaryCore.YearEnd}'] = 2050
        full_values_dict[f'{self.name}.epsilon0'] = 1.0
        full_values_dict[f'{self.name}.tolerance'] = 1.0e-8
        full_values_dict[f'{self.name}.max_mda_iter'] = 50
        full_values_dict[f'{self.name}.sub_mda_class'] = 'MDAGaussSeidel'
        # Overwrite values for ratios with values from setup
        full_values_dict[f'{self.name}.is_apply_ratio'] = self.is_apply_ratio
        full_values_dict[f'{self.name}.is_stream_demand'] = self.is_stream_demand
        full_values_dict[f'{self.name}.is_apply_resource_ratio'] = self.is_apply_resource_ratio
        full_values_dict[f'{self.name}.{GlossaryCore.AllStreamsDemandRatioValue}'] = self.all_streams_demand_ratio
        full_values_dict[f'{self.name}.all_resource_ratio_usable_demand'] = self.all_resource_ratio_usable_demand
        self.ee.load_study_from_input_dict(full_values_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0].mdo_discipline_wrapp.mdo_discipline

        # Get coupled inputs and outputs
        full_inputs = disc.get_input_data_names()
        full_outputs = disc.get_output_data_names()

        # coupled_inputs = [input for input in full_inputs if self.ee.dm.get_data(
        #     input, 'coupling')]
        # coupled_outputs = [output for output in full_outputs if self.ee.dm.get_data(
        #     output, 'coupling')]
        # coupled_outputs.extend(['Test_Ratio.EnergyMix.{GlossaryCore.AllStreamsDemandRatioValue}'
        #                         ])

        #AbstractJacobianUnittest.DUMP_JACOBIAN = True

        coupled_inputs = [
            # 'Test_Ratio.EnergyMix.fuel.liquid_fuel.{GlossaryCore.EnergyConsumptionWithoutRatioValue}',
            # 'Test_Ratio.EnergyMix.methane.{GlossaryCore.EnergyProductionValue}',
            f'Test_Ratio.EnergyMix.electricity.{GlossaryCore.EnergyConsumptionValue}']
        coupled_outputs = [f'Test_Ratio.EnergyMix.{GlossaryCore.AllStreamsDemandRatioValue}',]

        #coupled_inputs = ['Test_Ratio.EnergyMix.hydrogen.gaseous_hydrogen.{GlossaryCore.EnergyProductionValue}',]
        #coupled_outputs = ['Test_Ratio.EnergyMix.output_test']

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_ratio_false_true_{self.model_name}.pkl',
                            discipline=disc, step=1.0e-16, derr_approx='complex_step',local_data = disc.local_data,
                            inputs=coupled_inputs,  outputs=coupled_outputs,)

    def test_01b_ratio_FossilGas_discipline_jacobian(self):
        '''
        Test the gradients of the ratios on a simple techno which uses a single resource ratio (natural_gas_resource consumption)
        '''
        self.setUp()
        self.techno_name = 'FossilGas'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_methane': f'{self.name}',
                   'ns_resource': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.methane.fossil_gas.fossil_gas_disc.FossilGasDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.techno_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_technologies_input_dict.pkl'), 'rb')
        mda_data_input_dict = pickle.load(pkl_file)
        pkl_file.close()

        namespace = f'{self.name}'
        inputs_dict = {}
        coupled_inputs = []
        for key in mda_data_input_dict[self.techno_name].keys():
            # Modify namespace of input 'key' if needed
            if key in ['linearization_mode', 'cache_type', 'cache_file_path', 'sub_mda_class',
                       'max_mda_iter', 'n_processes', 'chain_linearize', 'tolerance', 'use_lu_fact',
                       'warm_start', 'acceleration', 'warm_start_threshold', 'n_subcouplings_parallel',
                       'max_mda_iter_gs', 'relax_factor', 'epsilon0',
                       'linear_solver_MDO', 'linear_solver_MDO_preconditioner', 'linear_solver_MDA', 'linear_solver_MDA_preconditioner',  'linear_solver_MDA_options',
                       'linear_solver_MDO_options', 'tolerance_linear_solver_MDO', 'group_mda_disciplines',
                       GlossaryCore.TransportCostValue, GlossaryCore.TransportMarginValue, GlossaryCore.YearStart, GlossaryCore.YearEnd,
                       GlossaryCore.EnergyPricesValue, GlossaryCore.EnergyCO2EmissionsValue, GlossaryCore.CO2TaxesValue, GlossaryCore.ResourcesPriceValue,
                       GlossaryCore.RessourcesCO2EmissionsValue, 'scaling_factor_techno_consumption',
                       'scaling_factor_techno_production', 'is_apply_ratio',
                       'is_stream_demand', 'is_apply_resource_ratio',
                       'residuals_history', GlossaryCore.AllStreamsDemandRatioValue, 'all_resource_ratio_usable_demand', 'ratio_objective']:
                inputs_dict[f'{namespace}.{key}'] = mda_data_input_dict[self.techno_name][key]['value']
                if mda_data_input_dict[self.techno_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{key}']
            else:
                inputs_dict[f'{namespace}.{self.techno_name}.{key}'] = mda_data_input_dict[self.techno_name][key]['value']
                if mda_data_input_dict[self.techno_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{self.techno_name}.{key}']

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_technologies_output_dict.pkl'), 'rb')
        mda_data_output_dict = pickle.load(pkl_file)
        pkl_file.close()

        coupled_outputs = []
        for key in mda_data_output_dict[self.techno_name].keys():
            # Modify namespace of output 'key' if needed
            if key in []:
                if mda_data_output_dict[self.techno_name][key]['is_coupling']:
                    coupled_outputs += [f'{namespace}.{key}']
            else:
                if mda_data_output_dict[self.techno_name][key]['is_coupling']:
                    coupled_outputs += [f'{namespace}.{self.techno_name}.{key}']

        # Overwrite values for ratios with values from setup
        inputs_dict[f'{namespace}.{GlossaryCore.YearEnd}'] = 2050
        inputs_dict[f'{namespace}.is_apply_ratio'] = self.is_apply_ratio
        inputs_dict[f'{namespace}.is_stream_demand'] = self.is_stream_demand
        inputs_dict[f'{namespace}.is_apply_resource_ratio'] = self.is_apply_resource_ratio
        inputs_dict[f'{namespace}.{GlossaryCore.AllStreamsDemandRatioValue}'] = self.all_streams_demand_ratio
        inputs_dict[f'{namespace}.all_resource_ratio_usable_demand'] = self.all_resource_ratio_usable_demand

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.techno_name}')[0].mdo_discipline_wrapp.mdo_discipline
        coupled_outputs.append(
            f'{namespace}.{self.techno_name}.non_use_capital')
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_ratio_{self.techno_name}.pkl',
                            discipline=disc, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,local_data = disc.local_data,
                            inputs=coupled_inputs,
                            outputs=coupled_outputs,)

    def test_02b_ratio_Nuclear_discipline_jacobian(self):
        '''
        Test the gradients of the ratios on a simple techno which uses a single resource ratio (uranium_resource consumption)
        '''
        self.setUp()
        self.techno_name = 'Nuclear'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': f'{self.name}',
                   'ns_resource': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.electricity.nuclear.nuclear_disc.NuclearDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.techno_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_technologies_input_dict.pkl'), 'rb')
        mda_data_input_dict = pickle.load(pkl_file)
        pkl_file.close()

        namespace = f'{self.name}'
        inputs_dict = {}
        coupled_inputs = []
        for key in mda_data_input_dict[self.techno_name].keys():
            # Modify namespace of input 'key' if needed
            if key in ['linearization_mode', 'cache_type', 'cache_file_path', 'sub_mda_class',
                       'max_mda_iter', 'n_processes', 'chain_linearize', 'tolerance', 'use_lu_fact',
                       'warm_start', 'acceleration', 'warm_start_threshold', 'n_subcouplings_parallel',
                       'max_mda_iter_gs', 'relax_factor', 'epsilon0',
                       'linear_solver_MDO', 'linear_solver_MDO_preconditioner', 'linear_solver_MDA', 'linear_solver_MDA_preconditioner',  'linear_solver_MDA_options',
                       'linear_solver_MDO_options', 'tolerance_linear_solver_MDO', 'group_mda_disciplines',
                       GlossaryCore.TransportCostValue, GlossaryCore.TransportMarginValue, GlossaryCore.YearStart, GlossaryCore.YearEnd,
                       GlossaryCore.EnergyPricesValue, GlossaryCore.EnergyCO2EmissionsValue, GlossaryCore.CO2TaxesValue, GlossaryCore.ResourcesPriceValue,
                       GlossaryCore.RessourcesCO2EmissionsValue, 'scaling_factor_techno_consumption',
                       'scaling_factor_techno_production', 'is_apply_ratio',
                       'is_stream_demand', 'is_apply_resource_ratio',
                       'residuals_history', GlossaryCore.AllStreamsDemandRatioValue, 'all_resource_ratio_usable_demand']:
                inputs_dict[f'{namespace}.{key}'] = mda_data_input_dict[self.techno_name][key]['value']
                if mda_data_input_dict[self.techno_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{key}']
            else:
                inputs_dict[f'{namespace}.{self.techno_name}.{key}'] = mda_data_input_dict[self.techno_name][key]['value']
                if mda_data_input_dict[self.techno_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{self.techno_name}.{key}']

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_technologies_output_dict.pkl'), 'rb')
        mda_data_output_dict = pickle.load(pkl_file)
        pkl_file.close()

        coupled_outputs = []
        for key in mda_data_output_dict[self.techno_name].keys():
            # Modify namespace of output 'key' if needed
            if key in []:
                if mda_data_output_dict[self.techno_name][key]['is_coupling']:
                    coupled_outputs += [f'{namespace}.{key}']
            else:
                if mda_data_output_dict[self.techno_name][key]['is_coupling']:
                    coupled_outputs += [f'{namespace}.{self.techno_name}.{key}']

        # Overwrite values for ratios with values from setup
        inputs_dict[f'{namespace}.{GlossaryCore.YearEnd}'] = 2050
        inputs_dict[f'{namespace}.is_apply_ratio'] = self.is_apply_ratio
        inputs_dict[f'{namespace}.is_stream_demand'] = self.is_stream_demand
        inputs_dict[f'{namespace}.is_apply_resource_ratio'] = self.is_apply_resource_ratio
        inputs_dict[f'{namespace}.{GlossaryCore.AllStreamsDemandRatioValue}'] = self.all_streams_demand_ratio
        inputs_dict[f'{namespace}.all_resource_ratio_usable_demand'] = self.all_resource_ratio_usable_demand

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.techno_name}')[0].mdo_discipline_wrapp.mdo_discipline
        coupled_inputs.append(
            f'{namespace}.all_resource_ratio_usable_demand'
        )
        coupled_outputs.append(
            f'{namespace}.{self.techno_name}.non_use_capital')
        #AbstractJacobianUnittest.DUMP_JACOBIAN = True
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_ratio_{self.techno_name}.pkl',
                            discipline=disc, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,local_data = disc.local_data,
                            inputs=coupled_inputs,
                            outputs=coupled_outputs,)

    def test_03b_ratio_CoalExtraction_discipline_jacobian(self):
        '''
        Test the gradients of the ratios on a simple techno which uses a single resource ratio (coal_resource consumption)
        '''
        self.setUp()
        self.techno_name = 'CoalExtraction'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_solid_fuel': f'{self.name}',
                   'ns_resource': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.solid_fuel.coal_extraction.coal_extraction_disc.CoalExtractionDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.techno_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_technologies_input_dict.pkl'), 'rb')
        mda_data_input_dict = pickle.load(pkl_file)
        pkl_file.close()

        namespace = f'{self.name}'
        inputs_dict = {}
        coupled_inputs = []
        for key in mda_data_input_dict[self.techno_name].keys():
            # Modify namespace of input 'key' if needed
            if key in ['linearization_mode', 'cache_type', 'cache_file_path', 'sub_mda_class',
                       'max_mda_iter', 'n_processes', 'chain_linearize', 'tolerance', 'use_lu_fact',
                       'warm_start', 'acceleration', 'warm_start_threshold', 'n_subcouplings_parallel',
                       'max_mda_iter_gs', 'relax_factor', 'epsilon0',
                       'linear_solver_MDO', 'linear_solver_MDO_preconditioner', 'linear_solver_MDA', 'linear_solver_MDA_preconditioner',  'linear_solver_MDA_options',
                       'linear_solver_MDO_options', 'tolerance_linear_solver_MDO', 'group_mda_disciplines',
                       GlossaryCore.TransportCostValue, GlossaryCore.TransportMarginValue, GlossaryCore.YearStart, GlossaryCore.YearEnd,
                       GlossaryCore.EnergyPricesValue, GlossaryCore.EnergyCO2EmissionsValue, GlossaryCore.CO2TaxesValue, GlossaryCore.ResourcesPriceValue,
                       GlossaryCore.RessourcesCO2EmissionsValue, 'scaling_factor_techno_consumption',
                       'scaling_factor_techno_production', 'is_apply_ratio',
                       'is_stream_demand', 'is_apply_resource_ratio',
                       'residuals_history', GlossaryCore.AllStreamsDemandRatioValue, 'all_resource_ratio_usable_demand']:
                inputs_dict[f'{namespace}.{key}'] = mda_data_input_dict[self.techno_name][key]['value']
                if mda_data_input_dict[self.techno_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{key}']
            else:
                inputs_dict[f'{namespace}.{self.techno_name}.{key}'] = mda_data_input_dict[self.techno_name][key]['value']
                if mda_data_input_dict[self.techno_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{self.techno_name}.{key}']

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_technologies_output_dict.pkl'), 'rb')
        mda_data_output_dict = pickle.load(pkl_file)
        pkl_file.close()

        coupled_outputs = []
        for key in mda_data_output_dict[self.techno_name].keys():
            # Modify namespace of output 'key' if needed
            if key in []:
                if mda_data_output_dict[self.techno_name][key]['is_coupling']:
                    coupled_outputs += [f'{namespace}.{key}']
            else:
                if mda_data_output_dict[self.techno_name][key]['is_coupling']:
                    coupled_outputs += [f'{namespace}.{self.techno_name}.{key}']

        # Overwrite values for ratios with values from setup
        inputs_dict[f'{namespace}.{GlossaryCore.YearEnd}'] = 2050
        inputs_dict[f'{namespace}.is_apply_ratio'] = self.is_apply_ratio
        inputs_dict[f'{namespace}.is_stream_demand'] = self.is_stream_demand
        inputs_dict[f'{namespace}.is_apply_resource_ratio'] = self.is_apply_resource_ratio
        inputs_dict[f'{namespace}.{GlossaryCore.AllStreamsDemandRatioValue}'] = self.all_streams_demand_ratio
        inputs_dict[f'{namespace}.all_resource_ratio_usable_demand'] = self.all_resource_ratio_usable_demand

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.techno_name}')[0].mdo_discipline_wrapp.mdo_discipline
        coupled_outputs.append(
            f'{namespace}.{self.techno_name}.non_use_capital')
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_ratio_{self.techno_name}.pkl',
                            discipline=disc, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,local_data = disc.local_data,
                            inputs=coupled_inputs,
                            outputs=coupled_outputs,)

    def test_04b_ratio_Refinery_discipline_jacobian(self):
        '''
        Test the gradients of the ratios on a simple techno which uses a single resource ratio (oil_resource consumption)
        '''
        self.setUp()
        self.techno_name = 'Refinery'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_liquid_fuel': f'{self.name}',
                   'ns_resource': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)
        mod_path = 'energy_models.models.liquid_fuel.refinery.refinery_disc.RefineryDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.techno_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_technologies_input_dict.pkl'), 'rb')
        mda_data_input_dict = pickle.load(pkl_file)
        pkl_file.close()

        namespace = f'{self.name}'
        inputs_dict = {}
        coupled_inputs = []
        for key in mda_data_input_dict[self.techno_name].keys():
            # Modify namespace of input 'key' if needed
            if key in ['linearization_mode', 'cache_type', 'cache_file_path', 'sub_mda_class',
                       'max_mda_iter', 'n_processes', 'chain_linearize', 'tolerance', 'use_lu_fact',
                       'warm_start', 'acceleration', 'warm_start_threshold', 'n_subcouplings_parallel',
                       'max_mda_iter_gs', 'relax_factor', 'epsilon0',
                       'linear_solver_MDO', 'linear_solver_MDO_preconditioner', 'linear_solver_MDA', 'linear_solver_MDA_preconditioner',  'linear_solver_MDA_options',
                       'linear_solver_MDO_options', 'tolerance_linear_solver_MDO', 'group_mda_disciplines',
                       GlossaryCore.TransportCostValue, GlossaryCore.TransportMarginValue, GlossaryCore.YearStart, GlossaryCore.YearEnd,
                       GlossaryCore.EnergyPricesValue, GlossaryCore.EnergyCO2EmissionsValue, GlossaryCore.CO2TaxesValue, GlossaryCore.ResourcesPriceValue,
                       GlossaryCore.RessourcesCO2EmissionsValue, 'scaling_factor_techno_consumption',
                       'scaling_factor_techno_production', 'is_apply_ratio',
                       'is_stream_demand', 'is_apply_resource_ratio',
                       'residuals_history', GlossaryCore.AllStreamsDemandRatioValue, 'all_resource_ratio_usable_demand']:
                inputs_dict[f'{namespace}.{key}'] = mda_data_input_dict[self.techno_name][key]['value']
                if mda_data_input_dict[self.techno_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{key}']
            else:
                inputs_dict[f'{namespace}.{self.techno_name}.{key}'] = mda_data_input_dict[self.techno_name][key]['value']
                if mda_data_input_dict[self.techno_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{self.techno_name}.{key}']

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_technologies_output_dict.pkl'), 'rb')
        mda_data_output_dict = pickle.load(pkl_file)
        pkl_file.close()

        coupled_outputs = []
        for key in mda_data_output_dict[self.techno_name].keys():
            # Modify namespace of output 'key' if needed
            if key in []:
                if mda_data_output_dict[self.techno_name][key]['is_coupling']:
                    coupled_outputs += [f'{namespace}.{key}']
            else:
                if mda_data_output_dict[self.techno_name][key]['is_coupling']:
                    coupled_outputs += [f'{namespace}.{self.techno_name}.{key}']

        # Overwrite values for ratios with values from setup
        inputs_dict[f'{namespace}.{GlossaryCore.YearEnd}'] = 2050
        inputs_dict[f'{namespace}.is_apply_ratio'] = self.is_apply_ratio
        inputs_dict[f'{namespace}.is_stream_demand'] = self.is_stream_demand
        inputs_dict[f'{namespace}.is_apply_resource_ratio'] = self.is_apply_resource_ratio
        inputs_dict[f'{namespace}.{GlossaryCore.AllStreamsDemandRatioValue}'] = self.all_streams_demand_ratio
        inputs_dict[f'{namespace}.all_resource_ratio_usable_demand'] = self.all_resource_ratio_usable_demand

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.techno_name}')[0].mdo_discipline_wrapp.mdo_discipline
        coupled_outputs.append(
            f'{namespace}.{self.techno_name}.non_use_capital')
        # AbstractJacobianUnittest.DUMP_JACOBIAN = True
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_ratio_{self.techno_name}.pkl',
                            discipline=disc, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,local_data = disc.local_data,
                            inputs=coupled_inputs,
                            outputs=coupled_outputs,)
        
    def test_05b_ratio_PEM_discipline_jacobian(self):
        '''
        Test the gradients of the ratios on a simple techno which uses a single resource ratio (platinum_resource consumption)
        '''
        self.setUp()
        self.techno_name = 'Electrolysis.PEM'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_hydrogen': f'{self.name}',
                   'ns_resource': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.gaseous_hydrogen.electrolysis.pem.electrolysis_pem_disc.ElectrolysisPEMDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.techno_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_technologies_input_dict.pkl'), 'rb')
        mda_data_input_dict = pickle.load(pkl_file)
        pkl_file.close()

        namespace = f'{self.name}'
        inputs_dict = {}
        coupled_inputs = []
        for key in mda_data_input_dict[self.techno_name].keys():
            # Modify namespace of input 'key' if needed
            if key in ['linearization_mode', 'cache_type', 'cache_file_path', 'sub_mda_class',
                       'max_mda_iter', 'n_processes', 'chain_linearize', 'tolerance', 'use_lu_fact',
                       'warm_start', 'acceleration', 'warm_start_threshold', 'n_subcouplings_parallel',
                       'max_mda_iter_gs', 'relax_factor', 'epsilon0',
                       'linear_solver_MDO', 'linear_solver_MDO_preconditioner', 'linear_solver_MDA', 'linear_solver_MDA_preconditioner',  'linear_solver_MDA_options',
                       'linear_solver_MDO_options', 'tolerance_linear_solver_MDO', 'group_mda_disciplines',
                       GlossaryCore.TransportCostValue, GlossaryCore.TransportMarginValue, GlossaryCore.YearStart, GlossaryCore.YearEnd,
                       GlossaryCore.EnergyPricesValue, GlossaryCore.EnergyCO2EmissionsValue, GlossaryCore.CO2TaxesValue, GlossaryCore.ResourcesPriceValue,
                       GlossaryCore.RessourcesCO2EmissionsValue, 'scaling_factor_techno_consumption',
                       'scaling_factor_techno_production', 'is_apply_ratio',
                       'is_stream_demand', 'is_apply_resource_ratio',
                       'residuals_history', GlossaryCore.AllStreamsDemandRatioValue, 'all_resource_ratio_usable_demand']:
                inputs_dict[f'{namespace}.{key}'] = mda_data_input_dict[self.techno_name][key]['value']
                if mda_data_input_dict[self.techno_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{key}']
            else:
                inputs_dict[f'{namespace}.{self.techno_name}.{key}'] = mda_data_input_dict[self.techno_name][key]['value']
                if mda_data_input_dict[self.techno_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{self.techno_name}.{key}']

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_technologies_output_dict.pkl'), 'rb')
        mda_data_output_dict = pickle.load(pkl_file)
        pkl_file.close()

        coupled_outputs = []
        for key in mda_data_output_dict[self.techno_name].keys():
            # Modify namespace of output 'key' if needed
            if key in []:
                if mda_data_output_dict[self.techno_name][key]['is_coupling']:
                    coupled_outputs += [f'{namespace}.{key}']
            else:
                if mda_data_output_dict[self.techno_name][key]['is_coupling']:
                    coupled_outputs += [f'{namespace}.{self.techno_name}.{key}']

        # Overwrite values for ratios with values from setup


        inputs_dict[f'{namespace}.{GlossaryCore.YearEnd}'] = 2050
        inputs_dict[f'{namespace}.is_apply_ratio'] = self.is_apply_ratio
        inputs_dict[f'{namespace}.is_stream_demand'] = self.is_stream_demand
        inputs_dict[f'{namespace}.is_apply_resource_ratio'] = self.is_apply_resource_ratio
        inputs_dict[f'{namespace}.{GlossaryCore.AllStreamsDemandRatioValue}'] = self.all_streams_demand_ratio
        inputs_dict[f'{namespace}.all_resource_ratio_usable_demand'] = self.all_resource_ratio_usable_demand

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.techno_name}')[0].mdo_discipline_wrapp.mdo_discipline
        coupled_inputs.append(
            f'{namespace}.all_resource_ratio_usable_demand'
        )
        coupled_outputs.append(
            f'{namespace}.{self.techno_name}.non_use_capital')
        coupled_outputs.remove('Test_Ratio.Electrolysis.PEM.techno_prices')
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_ratio_{self.techno_name}.pkl',
                            discipline=disc, step=1.0e-18, derr_approx='complex_step', threshold=2e-5,local_data = disc.local_data,
                            inputs=coupled_inputs,
                            outputs=coupled_outputs,)

if '__main__' == __name__:
    #AbstractJacobianUnittest.DUMP_JACOBIAN = True
    cls = RatioJacobianTestCase()
    cls.setUp()
    np.set_printoptions(threshold = 10000)
    #cls.test_07_ratio_CalciumLooping_discipline_jacobian()
    cls.test_05b_ratio_PEM_discipline_jacobian()
