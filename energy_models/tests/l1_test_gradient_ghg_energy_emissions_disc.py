'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/07-2024/06/24 Copyright 2023 Capgemini

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
from os.path import dirname, join

import numpy as np
import pandas as pd
from climateeconomics.sos_wrapping.sos_wrapping_agriculture.agriculture.agriculture_mix_disc import (
    AgricultureMixDiscipline,
)
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tests.core.abstract_jacobian_unit_test import (
    AbstractJacobianUnittest,
)

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.tests.data_tests.mda_energy_data_generator import (
    launch_data_pickle_generation,
)


class GHGEnergyEmissionsDiscJacobianTestCase(AbstractJacobianUnittest):
    """
    GHGEnergy Emissions Discipline jacobian test class
    """

    def analytic_grad_entry(self):
        return [
            self.test_01_GHGEnergy_emissions_discipline_CO2_per_use_jacobian,
            self.test_02_GHGEnergy_emissions_discipline_energy_prod_cons_jacobian,
            self.test_03_GHGENergy_from_energy_mix_jacobian

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
        self.year_start = GlossaryEnergy.YearStartDefault
        self.year_end = GlossaryEnergy.YearEndDefaultValueGradientTest
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.energy_list = [energy for energy in EnergyMix.energy_list if energy not in [
            GlossaryEnergy.fossil, GlossaryEnergy.clean_energy, f'{GlossaryEnergy.fuel}.{GlossaryEnergy.ethanol}',
            GlossaryEnergy.carbon_capture, GlossaryEnergy.carbon_storage,
            f'{GlossaryEnergy.heat}.lowtemperatureheat', f'{GlossaryEnergy.heat}.mediumtemperatureheat',
            f'{GlossaryEnergy.heat}.hightemperatureheat']]
        self.ccs_list = [GlossaryEnergy.carbon_capture, GlossaryEnergy.carbon_storage]
        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_streams_output_dict.pkl'), 'rb')
        streams_outputs_dict = pickle.load(pkl_file)
        pkl_file.close()

        self.CO2_per_use = {}
        self.CH4_per_use = {}
        self.N2O_per_use = {}
        self.energy_production, self.energy_consumption = {}, {}
        for i, energy in enumerate(self.energy_list):
            if energy == GlossaryEnergy.biomass_dry:
                # not to delete the test, we do not care about the biomass dry values (they are not anymore in the generator data dict
                self.CO2_per_use[f'{energy}'] = streams_outputs_dict[GlossaryEnergy.biogas][GlossaryEnergy.CO2PerUse]['value']
                self.CH4_per_use[f'{energy}'] = streams_outputs_dict[GlossaryEnergy.biogas][GlossaryEnergy.CH4PerUse]['value']
                self.N2O_per_use[f'{energy}'] = streams_outputs_dict[GlossaryEnergy.biogas][GlossaryEnergy.N2OPerUse]['value']
                biomass_energy_prod = streams_outputs_dict[GlossaryEnergy.biogas][GlossaryEnergy.EnergyProductionValue][
                    'value'].copy()
                biomass_energy_prod = biomass_energy_prod.rename(
                    columns={GlossaryEnergy.biogas: GlossaryEnergy.biomass_dry})
                self.energy_production[f'{energy}'] = biomass_energy_prod
                biomass_cons_prod = streams_outputs_dict[GlossaryEnergy.biogas][GlossaryEnergy.StreamConsumptionValue][
                    'value'].copy()
                biomass_cons_prod = biomass_cons_prod.drop(columns=[f'{GlossaryEnergy.WetBiomassResource} ({GlossaryEnergy.mass_unit})'])

                self.energy_consumption[f'{energy}'] = biomass_cons_prod

            else:
                self.CO2_per_use[f'{energy}'] = streams_outputs_dict[f'{energy}'][GlossaryEnergy.CO2PerUse]['value']
                self.CH4_per_use[f'{energy}'] = streams_outputs_dict[f'{energy}'][GlossaryEnergy.CH4PerUse]['value']
                self.N2O_per_use[f'{energy}'] = streams_outputs_dict[f'{energy}'][GlossaryEnergy.N2OPerUse]['value']
                self.energy_production[f'{energy}'] = \
                    streams_outputs_dict[f'{energy}'][GlossaryEnergy.EnergyProductionValue][
                        'value']
                self.energy_consumption[f'{energy}'] = \
                    streams_outputs_dict[f'{energy}'][GlossaryEnergy.StreamConsumptionValue]['value']

        for i, ccs_name in enumerate(self.ccs_list):
            self.energy_production[f'{ccs_name}'] = \
                streams_outputs_dict[f'{ccs_name}'][GlossaryEnergy.EnergyProductionValue]['value']

        self.scaling_factor_energy_production = 1000.0
        self.scaling_factor_energy_consumption = 1000.0
        self.energy_production_detailed = streams_outputs_dict[GlossaryEnergy.StreamProductionDetailedValue]

        self.co2_emissions_ccus_Gt = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                                   'carbon_storage Limited by capture (Gt)': np.linspace(1, 6,
                                                                                                         len(self.years))
                                                   })
        self.co2_emissions_needed_by_energy_mix = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                                                'carbon_capture needed by energy mix (Gt)': np.linspace(
                                                                    0.001, 0.3, len(self.years))
                                                                })
        self.name = 'Test'
        self.model_name = 'EnergyGHGEmissions'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_emissions': self.name,
                   'ns_energy': self.name,
                   GlossaryEnergy.NS_CCS: self.name,
                   'ns_public': self.name,
                   'ns_energy_study': self.name,
                   GlossaryEnergy.NS_WITNESS: self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.energy_ghg_emissions.energy_ghg_emissions_disc.EnergyGHGEmissionsDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {
            f'{self.name}.{GlossaryEnergy.YearStart}': self.year_start,
            f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
            f'{self.name}.{GlossaryEnergy.energy_list}': self.energy_list,
            f'{self.name}.scaling_factor_energy_production': self.scaling_factor_energy_production,
            f'{self.name}.scaling_factor_energy_consumption': self.scaling_factor_energy_consumption,
            f'{self.name}.{GlossaryEnergy.StreamProductionDetailedValue}': self.energy_production_detailed,
            f'{self.name}.co2_emissions_ccus_Gt': self.co2_emissions_ccus_Gt,
            f'{self.name}.co2_emissions_needed_by_energy_mix': self.co2_emissions_needed_by_energy_mix,
            f'{self.name}.{GlossaryEnergy.ccs_list}': self.ccs_list
        }
        for energy in self.energy_list:
            if energy == GlossaryEnergy.biomass_dry:
                inputs_dict[f'{self.name}.{AgricultureMixDiscipline.name}.{GlossaryEnergy.CO2PerUse}'] = self.CO2_per_use[energy]
                inputs_dict[f'{self.name}.{AgricultureMixDiscipline.name}.{GlossaryEnergy.CH4PerUse}'] = self.CH4_per_use[energy]
                inputs_dict[f'{self.name}.{AgricultureMixDiscipline.name}.{GlossaryEnergy.N2OPerUse}'] = self.N2O_per_use[energy]
                inputs_dict[f'{self.name}.{AgricultureMixDiscipline.name}.{GlossaryEnergy.EnergyProductionValue}'] = \
                    self.energy_production[
                        energy]
                inputs_dict[f'{self.name}.{AgricultureMixDiscipline.name}.{GlossaryEnergy.StreamConsumptionValue}'] = \
                    self.energy_consumption[energy]
            else:

                inputs_dict[f'{self.name}.{energy}.{GlossaryEnergy.CO2PerUse}'] = self.CO2_per_use[energy]
                inputs_dict[f'{self.name}.{energy}.{GlossaryEnergy.CH4PerUse}'] = self.CH4_per_use[energy]
                inputs_dict[f'{self.name}.{energy}.{GlossaryEnergy.N2OPerUse}'] = self.N2O_per_use[energy]
                inputs_dict[f'{self.name}.{energy}.{GlossaryEnergy.EnergyProductionValue}'] = self.energy_production[
                    energy]
                inputs_dict[f'{self.name}.{energy}.{GlossaryEnergy.StreamConsumptionValue}'] = self.energy_consumption[
                    energy]

        for energy in self.ccs_list:
            inputs_dict[f'{self.name}.{energy}.{GlossaryEnergy.EnergyProductionValue}'] = self.energy_production[energy]

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

    def tearDown(self):
        pass

    def test_01_GHGEnergy_emissions_discipline_CO2_per_use_jacobian(self):
        '''
        Test the gradients of the Consumption CO2 emissions discipline
        for inputs CO2_per_use
        '''

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0].discipline_wrapp.discipline

        energy_list_wobiomass_dry = [
            energy for energy in self.energy_list if energy != GlossaryEnergy.biomass_dry]
        coupled_inputs = [
            f'{self.name}.{energy}.{GlossaryEnergy.CO2PerUse}' for energy in energy_list_wobiomass_dry]
        coupled_inputs.extend([
            f'{self.name}.{energy}.{GlossaryEnergy.CH4PerUse}' for energy in energy_list_wobiomass_dry])
        coupled_inputs.extend([
            f'{self.name}.{energy}.{GlossaryEnergy.N2OPerUse}' for energy in energy_list_wobiomass_dry])

        coupled_inputs.extend([f'{self.name}.{AgricultureMixDiscipline.name}.{GlossaryEnergy.CO2PerUse}',
                               f'{self.name}.{AgricultureMixDiscipline.name}.{GlossaryEnergy.CH4PerUse}',
                               f'{self.name}.{AgricultureMixDiscipline.name}.{GlossaryEnergy.N2OPerUse}'])
        coupled_outputs = [
            f'{self.name}.GHG_total_energy_emissions']

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.model_name}.pkl',
                            discipline=disc, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc.local_data,
                            inputs=coupled_inputs,
                            outputs=coupled_outputs, )

    def test_02_GHGEnergy_emissions_discipline_energy_prod_cons_jacobian(self):
        '''
        Test the gradients of the Consumption CO2 emissions discipline
        for inputs energy production and consumption
        '''

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0].discipline_wrapp.discipline

        energy_list_wobiomass_dry = [
            energy for energy in self.energy_list if energy != GlossaryEnergy.biomass_dry]
        coupled_inputs = [
            f'{self.name}.{energy}.{GlossaryEnergy.EnergyProductionValue}' for energy in energy_list_wobiomass_dry]
        coupled_inputs.extend([
            f'{self.name}.{energy}.{GlossaryEnergy.EnergyProductionValue}' for energy in self.ccs_list])
        coupled_inputs.extend(
            [f'{self.name}.{energy}.{GlossaryEnergy.StreamConsumptionValue}' for energy in energy_list_wobiomass_dry])

        coupled_inputs.extend([f'{self.name}.{AgricultureMixDiscipline.name}.{GlossaryEnergy.EnergyProductionValue}',
                               f'{self.name}.{AgricultureMixDiscipline.name}.{GlossaryEnergy.StreamConsumptionValue}'])
        coupled_outputs = [f'{self.name}.GHG_total_energy_emissions']

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.model_name}_prodcons.pkl',
                            discipline=disc, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc.local_data,
                            inputs=coupled_inputs,
                            outputs=coupled_outputs, )

    def test_03_GHGENergy_from_energy_mix_jacobian(self):
        '''
        Test the gradients of the Consumption CO2 emissions discipline
        for inputs energy production and consumption
        '''

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0].discipline_wrapp.discipline

        coupled_inputs = [
            f'{self.name}.co2_emissions_ccus_Gt',
            f'{self.name}.co2_emissions_needed_by_energy_mix']

        coupled_outputs = [f'{self.name}.GHG_total_energy_emissions']

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.model_name}_emission_energy_mix.pkl',
                            discipline=disc, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc.local_data,
                            inputs=coupled_inputs,
                            outputs=coupled_outputs, )

    def test_04_GHGENergy_energy_production_detailed_jacobian(self):
        '''
        Test the gradients of the Consumption CO2 emissions discipline
        for inputs energy production and consumption
        '''

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0].discipline_wrapp.discipline

        coupled_inputs = [
            f'{self.name}.{GlossaryEnergy.StreamProductionDetailedValue}']

        coupled_outputs = [f'{self.name}.GHG_total_energy_emissions']

        self.check_jacobian(location=dirname(__file__),
                            filename=f'jacobian_{self.model_name}_energy_production_detailed.pkl',
                            discipline=disc, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc.local_data,
                            inputs=coupled_inputs,
                            outputs=coupled_outputs, )


if '__main__' == __name__:
    cls = GHGEnergyEmissionsDiscJacobianTestCase()
    cls.setUp()
    # cls.launch_data_pickle_generation()
    cls.test_01_GHGEnergy_emissions_discipline_CO2_per_use_jacobian()
    # cls.test_02_GHGEnergy_emissions_discipline_energy_prod_cons_jacobian()
    # cls.test_03_GHGENergy_from_energy_mix_jacobian()
    # cls.test_04_GHGENergy_energy_production_detailed_jacobian()
