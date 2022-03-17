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
import pandas as pd
from os.path import join, dirname

from sos_trades_core.execution_engine.execution_engine import ExecutionEngine
from sos_trades_core.tests.core.abstract_jacobian_unit_test import AbstractJacobianUnittest
from energy_models.core.energy_mix.energy_mix import EnergyMix
import pickle
from energy_models.sos_processes.energy.MDA.energy_process_v0.usecase import Study
from climateeconomics.sos_processes.iam.witness.witness_optim_sub_process.usecase_witness_optim_sub import Study as WITNESSFull_subprocess
from energy_models.tests.data_tests.mda_energy_data_generator import launch_data_pickle_generation


class ConsumptionCO2EmissionsDiscJacobianTestCase(AbstractJacobianUnittest):
    """
    Consumption CO2 Emissions Discipline jacobian test class
    """
    #AbstractJacobianUnittest.DUMP_JACOBIAN = True

    def analytic_grad_entry(self):
        return [
            self.test_01_Consumption_CO2_emissions_discipline_CO2_per_use_jacobian,

        ]

    def launch_data_pickle_generation(self):
        '''
        If the energy_process_v0 usecase changed, launch this function to update the data pickle
        '''
        launch_data_pickle_generation()

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.year_start = 2020
        self.year_end = 2050
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.energy_list = [energy for energy in EnergyMix.energy_list if energy not in [
            'fossil', 'renewable', 'hydrotreated_oil_fuel', 'carbon_capture', 'carbon_storage']]
        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_streams_output_dict.pkl'), 'rb')
        streams_outputs_dict = pickle.load(pkl_file)
        pkl_file.close()

        self.CO2_per_use = {}
        self.energy_prices = {}
        self.energy_demand = {}
        self.energy_consumption_woratio = {}
        self.energy_production, self.energy_consumption, self.land_use_required = {}, {}, {}
        for i, energy in enumerate(self.energy_list):
            self.CO2_per_use[f'{energy}'] = streams_outputs_dict[f'{energy}']['CO2_per_use']['value']
            self.energy_production[f'{energy}'] = streams_outputs_dict[f'{energy}']['energy_production']['value']
            self.energy_consumption[f'{energy}'] = streams_outputs_dict[f'{energy}']['energy_consumption']['value']
        for energy in ['carbon_capture', 'carbon_storage']:
            self.land_use_required[f'{energy}'] = streams_outputs_dict[f'{energy}']['land_use_required']['value']
            self.energy_production[f'{energy}'] = streams_outputs_dict[f'{energy}']['energy_production']['value']
            self.energy_consumption[f'{energy}'] = streams_outputs_dict[f'{energy}']['energy_consumption']['value']
            self.energy_prices[f'{energy}'] = streams_outputs_dict[f'{energy}']['energy_prices']['value']
            self.energy_consumption_woratio[f'{energy}'] = streams_outputs_dict[f'{energy}']['energy_consumption_woratio']['value']

            #self.energy_demand[f'{energy}'] = streams_outputs_dict[f'{energy}']['energy_demand']['value']
        self.scaling_factor_energy_production = 1000.0
        self.scaling_factor_energy_consumption = 1000.0
        self.energy_production_detailed = streams_outputs_dict['energy_production_detailed']
        years = streams_outputs_dict[f'{energy}']['energy_consumption']['value']['years']
        self.CO2_taxes = pd.DataFrame(data={'years': years, 'CO2_tax': 150.})
        self.energy_demand_unit = pd.DataFrame(data={'years': years, 'CO2_tax': 0.})
        self.co2_emissions = pd.DataFrame(data={'years': years, 'carbon_capture needed by energy mix (Mt)':0.005})
        self.co2_emissions = pd.DataFrame(data={'years': years, 'carbon_capture needed by energy mix (Mt)':0.005})
        self.co2_emissions_needed_by_energy_mix = pd.DataFrame(data={'years': years, 'carbon_capture needed by energy mix (Gt)':0.005})
        self.CO2_emissions_by_use_sources = pd.DataFrame(data={'years': years, 'CO2_resource from energy mix (Gt)':1.2, 'carbon_capture from energy mix (Gt)': 1e-15,
                                                               'Total CO2 by use (Gt)': 6.5, 'Total CO2 from Flue Gas (Gt)': 1e-3})


    def tearDown(self):
        pass

    def test_01_Consumption_ccus_disciplinejacobian(self):
        '''
        Test the gradients of the Consumption CO2 emissions discipline
        for inputs CO2_per_use
        '''

        self.name = 'Test'
        self.model_name = 'CCUS_disc'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name,
                   'ns_energy': self.name,
                   'ns_ccs': self.name,
                   'ns_energy_study': self.name,
                   'ns_ref': self.name,
                   'ns_functions': self.name,
                   'ns_demand': self.name,
                   'ns_carbon_capture': self.name,
                   'ns_carbon_storage': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.ccus.ccus_disc.CCUS_Discipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {
            f'{self.name}.year_start': self.year_start,
            f'{self.name}.year_end': self.year_end,
            f'{self.name}.energy_list': self.energy_list,
            f'{self.name}.scaling_factor_energy_production': self.scaling_factor_energy_production,
            f'{self.name}.scaling_factor_energy_consumption': self.scaling_factor_energy_consumption,
            f'{self.name}.energy_production_detailed': self.energy_production_detailed,
        }
        for energy in self.energy_list :
            inputs_dict[f'{self.name}.{energy}.CO2_per_use'] = self.CO2_per_use[energy]
            inputs_dict[f'{self.name}.{energy}.energy_production'] = self.energy_production[energy]
            inputs_dict[f'{self.name}.{energy}.energy_consumption'] = self.energy_consumption[energy]

        for energy in ['carbon_capture', 'carbon_storage']:
            inputs_dict[f'{self.name}.{energy}.energy_production'] = self.energy_production[energy]
            inputs_dict[f'{self.name}.{energy}.energy_consumption'] = self.energy_consumption[energy]
            inputs_dict[f'{self.name}.{energy}.energy_prices'] = self.energy_prices[energy]
            inputs_dict[f'{self.name}.{energy}.land_use_required'] = self.land_use_required[energy]
            inputs_dict[f'{self.name}.{energy}.energy_consumption_woratio'] = self.energy_consumption_woratio[energy]
            inputs_dict[f'{self.name}.{energy}.energy_demand'] = self.energy_demand_unit
            inputs_dict[f'{self.name}.{energy}.co2_emissions'] = self.co2_emissions
        inputs_dict[f'{self.name}.CO2_taxes'] = self.CO2_taxes
        inputs_dict[f'{self.name}.CO2_emissions_by_use_sources'] = self.CO2_emissions_by_use_sources
        inputs_dict[f'{self.name}.co2_emissions_needed_by_energy_mix'] = self.co2_emissions_needed_by_energy_mix

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]

        coupled_inputs = [
            f'{self.name}.CO2_emissions_by_use_sources',
            f'{self.name}.co2_emissions_needed_by_energy_mix',
            f'{self.name}.carbon_capture.energy_production',
            f'{self.name}.carbon_capture.energy_consumption',
            f'{self.name}.carbon_capture.energy_prices',
            f'{self.name}.carbon_capture.land_use_required',
            f'{self.name}.carbon_storage.energy_production',
            f'{self.name}.carbon_storage.energy_consumption',
            f'{self.name}.carbon_storage.energy_prices',
            f'{self.name}.carbon_storage.land_use_required',
        ]
        coupled_outputs = [f'{self.name}.co2_emissions_ccus_Gt',
                           f'{self.name}.ratio_available_carbon_capture',
                           f'{self.name}.CCS_price',
                           f'{self.name}.carbon_storage_constraint']

        # AbstractJacobianUnittest.DUMP_JACOBIAN = True

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.model_name}.pkl',
                            discipline=disc, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,
                            inputs=coupled_inputs,
                            outputs=coupled_outputs,)


if '__main__' == __name__:
    AbstractJacobianUnittest.DUMP_JACOBIAN = True
    cls = ConsumptionCO2EmissionsDiscJacobianTestCase()
    cls.setUp()
    # cls.launch_data_pickle_generation()
    cls.test_01_Consumption_ccus_disciplinejacobian()
