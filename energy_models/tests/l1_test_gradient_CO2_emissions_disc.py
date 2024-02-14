'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/07-2023/11/16 Copyright 2023 Capgemini

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

import pickle
from os.path import join, dirname

import numpy as np

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.tests.data_tests.mda_energy_data_generator import launch_data_pickle_generation
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tests.core.abstract_jacobian_unit_test import AbstractJacobianUnittest


class ConsumptionCO2EmissionsDiscJacobianTestCase(AbstractJacobianUnittest):
    """
    Consumption CO2 Emissions Discipline jacobian test class
    """

    # AbstractJacobianUnittest.DUMP_JACOBIAN = True

    def analytic_grad_entry(self):
        return [
            self.test_01_Consumption_CO2_emissions_discipline_CO2_per_use_jacobian,
            self.test_02_Consumption_CO2_emissions_discipline_energy_prod_cons_jacobian,

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
        self.year_start = GlossaryEnergy.YeartStartDefault
        self.year_end = 2050
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.energy_list = [energy for energy in EnergyMix.energy_list if energy not in [
            GlossaryEnergy.fossil, GlossaryEnergy.renewable, f'{GlossaryEnergy.fuel}.{GlossaryEnergy.ethanol}', GlossaryEnergy.carbon_capture, GlossaryEnergy.carbon_storage,
            f'{GlossaryEnergy.heat}.lowtemperatureheat', f'{GlossaryEnergy.heat}.mediumtemperatureheat', f'{GlossaryEnergy.heat}.hightemperatureheat']]
        self.ccs_list = [GlossaryEnergy.carbon_capture, GlossaryEnergy.carbon_storage]
        self.agriculture_mix_name = 'AgricultureMix'
        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_streams_output_dict.pkl'), 'rb')
        streams_outputs_dict = pickle.load(pkl_file)
        pkl_file.close()

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_streams_output_dict_old.pkl'), 'rb')
        streams_outputs_dict_old = pickle.load(pkl_file)
        pkl_file.close()

        self.CO2_per_use = {}
        self.energy_production, self.energy_consumption = {}, {}
        for i, energy in enumerate(self.energy_list):
            self.CO2_per_use[f'{energy}'] = streams_outputs_dict[f'{energy}']['CO2_per_use']['value']
            self.energy_production[f'{energy}'] = \
            streams_outputs_dict[f'{energy}'][GlossaryEnergy.EnergyProductionValue][
                'value']
            self.energy_consumption[f'{energy}'] = \
            streams_outputs_dict[f'{energy}'][GlossaryEnergy.EnergyConsumptionValue]['value']

        for i, ccs_name in enumerate(self.ccs_list):
            self.energy_production[f'{ccs_name}'] = \
                streams_outputs_dict[f'{ccs_name}'][GlossaryEnergy.EnergyProductionValue]['value']
        self.scaling_factor_energy_production = 1000.0
        self.scaling_factor_energy_consumption = 1000.0
        self.energy_production_detailed = streams_outputs_dict[GlossaryEnergy.EnergyProductionDetailedValue]

    def tearDown(self):
        pass

    def test_01_Consumption_CO2_emissions_discipline_CO2_per_use_jacobian(self):
        '''
        Test the gradients of the Consumption CO2 emissions discipline
        for inputs CO2_per_use
        '''
        self.name = 'Test'
        self.model_name = 'ConsumptionCO2Emissions'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_emissions': self.name,
                   'ns_energy': self.name + f'.{self.model_name}',
                   GlossaryEnergy.NS_WITNESS: self.name,
                   GlossaryEnergy.NS_CCS: self.name,
                   'ns_public': self.name,
                   'ns_energy_study': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.consumption_CO2_emissions.consumption_CO2_emissions_disc.ConsumptionCO2EmissionsDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {
            f'{self.name}.{GlossaryEnergy.YearStart}': self.year_start,
            f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
            f'{self.name}.{GlossaryEnergy.energy_list}': self.energy_list,
            f'{self.name}.{GlossaryEnergy.ccs_list}': self.ccs_list,

            f'{self.name}.scaling_factor_energy_production': self.scaling_factor_energy_production,
            f'{self.name}.scaling_factor_energy_consumption': self.scaling_factor_energy_consumption,
            f'{self.name}.{self.model_name}.{GlossaryEnergy.EnergyProductionDetailedValue}': self.energy_production_detailed,
        }

        for energy in self.energy_list:
            if energy == GlossaryEnergy.biomass_dry:
                inputs_dict[f'{self.name}.{self.agriculture_mix_name}.CO2_per_use'] = self.CO2_per_use[energy]
                inputs_dict[f'{self.name}.{self.agriculture_mix_name}.{GlossaryEnergy.EnergyProductionValue}'] = \
                self.energy_production[
                    energy]
                inputs_dict[f'{self.name}.{self.agriculture_mix_name}.{GlossaryEnergy.EnergyConsumptionValue}'] = \
                self.energy_consumption[
                    energy]

            else:
                inputs_dict[f'{self.name}.{self.model_name}.{energy}.CO2_per_use'] = self.CO2_per_use[energy]
                inputs_dict[f'{self.name}.{self.model_name}.{energy}.{GlossaryEnergy.EnergyProductionValue}'] = \
                self.energy_production[
                    energy]
                inputs_dict[f'{self.name}.{self.model_name}.{energy}.{GlossaryEnergy.EnergyConsumptionValue}'] = \
                self.energy_consumption[
                    energy]

        for energy in self.ccs_list:
            inputs_dict[f'{self.name}.{energy}.{GlossaryEnergy.EnergyProductionValue}'] = self.energy_production[energy]

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0].mdo_discipline_wrapp.mdo_discipline

        coupled_inputs = [
            f'{self.name}.{self.model_name}.{energy}.CO2_per_use' for energy in self.energy_list if
            energy != GlossaryEnergy.biomass_dry]
        coupled_inputs.append(f'{self.name}.{self.agriculture_mix_name}.CO2_per_use')
        coupled_outputs = [f'{self.name}.CO2_emissions_by_use_sources',
                           f'{self.name}.CO2_emissions_by_use_sinks']

        # AbstractJacobianUnittest.DUMP_JACOBIAN = True

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.model_name}.pkl',
                            discipline=disc, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc.local_data,
                            inputs=coupled_inputs,
                            outputs=coupled_outputs, )

    def test_02_Consumption_CO2_emissions_discipline_energy_prod_cons_jacobian(self):
        '''
        Test the gradients of the Consumption CO2 emissions discipline
        for inputs energy production and consumption
        '''
        self.name = 'Test'
        self.model_name = 'ConsumptionCO2Emissions'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_emissions': self.name,
                   'ns_energy': self.name + f'.{self.model_name}',
                   GlossaryEnergy.NS_WITNESS: self.name,
                   GlossaryEnergy.NS_CCS: self.name,
                   'ns_public': self.name,
                   'ns_energy_study': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.consumption_CO2_emissions.consumption_CO2_emissions_disc.ConsumptionCO2EmissionsDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {
            f'{self.name}.{GlossaryEnergy.YearStart}': self.year_start,
            f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
            f'{self.name}.{GlossaryEnergy.energy_list}': self.energy_list,
            f'{self.name}.{GlossaryEnergy.ccs_list}': self.ccs_list,

            f'{self.name}.scaling_factor_energy_production': self.scaling_factor_energy_production,
            f'{self.name}.scaling_factor_energy_consumption': self.scaling_factor_energy_consumption,
            f'{self.name}.{self.model_name}.{GlossaryEnergy.EnergyProductionDetailedValue}': self.energy_production_detailed,
        }
        for energy in self.energy_list:
            if energy == GlossaryEnergy.biomass_dry:
                inputs_dict[f'{self.name}.{self.agriculture_mix_name}.CO2_per_use'] = self.CO2_per_use[energy]
                inputs_dict[f'{self.name}.{self.agriculture_mix_name}.{GlossaryEnergy.EnergyProductionValue}'] = \
                self.energy_production[
                    energy]
                inputs_dict[f'{self.name}.{self.agriculture_mix_name}.{GlossaryEnergy.EnergyConsumptionValue}'] = \
                self.energy_consumption[
                    energy]

            else:
                inputs_dict[f'{self.name}.{self.model_name}.{energy}.CO2_per_use'] = self.CO2_per_use[energy]
                inputs_dict[f'{self.name}.{self.model_name}.{energy}.{GlossaryEnergy.EnergyProductionValue}'] = \
                self.energy_production[
                    energy]
                inputs_dict[f'{self.name}.{self.model_name}.{energy}.{GlossaryEnergy.EnergyConsumptionValue}'] = \
                self.energy_consumption[
                    energy]

        for energy in self.ccs_list:
            inputs_dict[f'{self.name}.{energy}.{GlossaryEnergy.EnergyProductionValue}'] = self.energy_production[energy]
        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0].mdo_discipline_wrapp.mdo_discipline

        coupled_inputs = [
            f'{self.name}.{energy}.{GlossaryEnergy.EnergyProductionValue}' for energy in self.ccs_list]
        coupled_inputs.extend(
            [f'{self.name}.{self.model_name}.{energy}.{GlossaryEnergy.EnergyProductionValue}' for energy in
             self.energy_list if
             energy != GlossaryEnergy.biomass_dry])
        coupled_inputs.extend(
            [f'{self.name}.{self.model_name}.{energy}.{GlossaryEnergy.EnergyConsumptionValue}' for energy in
             self.energy_list if
             energy != GlossaryEnergy.biomass_dry])

        coupled_inputs.append(f'{self.name}.{self.agriculture_mix_name}.{GlossaryEnergy.EnergyProductionValue}')
        coupled_inputs.append(f'{self.name}.{self.agriculture_mix_name}.{GlossaryEnergy.EnergyConsumptionValue}')
        coupled_outputs = [f'{self.name}.CO2_emissions_by_use_sources',
                           f'{self.name}.CO2_emissions_by_use_sinks']

        # AbstractJacobianUnittest.DUMP_JACOBIAN = True

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.model_name}_prodcons.pkl',
                            discipline=disc, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,
                            inputs=coupled_inputs,
                            outputs=coupled_outputs,
                            local_data=disc.local_data)


if '__main__' == __name__:
    # AbstractJacobianUnittest.DUMP_JACOBIAN = True
    cls = ConsumptionCO2EmissionsDiscJacobianTestCase()
    cls.setUp()
    # cls.launch_data_pickle_generation()
    cls.test_02_Consumption_CO2_emissions_discipline_energy_prod_cons_jacobian()
