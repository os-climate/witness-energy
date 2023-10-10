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
import unittest
import pandas as pd
import numpy as np

from climateeconomics.glossarycore import GlossaryCore
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from energy_models.core.energy_mix.energy_mix import EnergyMix

from os.path import join, dirname
import pickle


class CCUSDiscTestCase(unittest.TestCase):
    """
    CO2EmissionsDisc  test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.year_start = 2020
        self.year_end = 2050
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.energy_list = [energy for energy in EnergyMix.energy_list if energy not in [
            'fossil', 'renewable', 'fuel.ethanol', 'carbon_capture', 'carbon_storage', 'heat.lowtemperatureheat', \
            'heat.mediumtemperatureheat', 'heat.hightemperatureheat']]
        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_streams_output_dict.pkl'), 'rb')
        streams_outputs_dict = pickle.load(pkl_file)
        pkl_file.close()

        self.CO2_per_use = {}
        self.energy_prices = {}
        self.energy_consumption_woratio = {}
        self.energy_production, self.energy_consumption, self.land_use_required = {}, {}, {}
        for i, energy in enumerate(self.energy_list):
            self.CO2_per_use[f'{energy}'] = streams_outputs_dict[f'{energy}']['CO2_per_use']['value']
            self.energy_production[f'{energy}'] = streams_outputs_dict[f'{energy}'][GlossaryCore.EnergyProductionValue]['value']
            self.energy_consumption[f'{energy}'] = streams_outputs_dict[f'{energy}']['energy_consumption']['value']
        for energy in ['carbon_capture', 'carbon_storage']:
            self.land_use_required[f'{energy}'] = streams_outputs_dict[f'{energy}']['land_use_required']['value']
            self.energy_production[f'{energy}'] = streams_outputs_dict[f'{energy}'][GlossaryCore.EnergyProductionValue]['value']
            self.energy_consumption[f'{energy}'] = streams_outputs_dict[f'{energy}']['energy_consumption']['value']
            self.energy_prices[f'{energy}'] = streams_outputs_dict[f'{energy}']['energy_prices']['value']
            self.energy_consumption_woratio[f'{energy}'] = streams_outputs_dict[
                f'{energy}']['energy_consumption_woratio']['value']

        self.scaling_factor_energy_production = 1000.0
        self.scaling_factor_energy_consumption = 1000.0
        self.energy_production_detailed = streams_outputs_dict['energy_production_detailed']
        years = streams_outputs_dict[f'{energy}']['energy_consumption']['value']['years']
        self.CO2_taxes = pd.DataFrame(data={'years': years, 'CO2_tax': 150.})
        self.co2_emissions = pd.DataFrame(
            data={'years': years, 'carbon_capture needed by energy mix (Mt)': 0.005})
        self.co2_emissions = pd.DataFrame(
            data={'years': years, 'carbon_capture needed by energy mix (Mt)': 0.005})
        self.co2_emissions_needed_by_energy_mix = pd.DataFrame(
            data={'years': years, 'carbon_capture needed by energy mix (Gt)': 0.005})
        self.carbon_capture_from_energy_mix = pd.DataFrame(
            data={'years': years, 'carbon_capture from energy mix (Gt)': 1e-15})

    def tearDown(self):
        pass

    def test_01_CCUS_discipline(self):

        self.name = 'Test'
        self.model_name = 'ConsumptionCO2Emissions'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name,
                   'ns_energy': self.name,
                   'ns_ccs': self.name,
                   'ns_energy_study': self.name,
                   'ns_ref': self.name,
                   'ns_functions': self.name,
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
            f'{self.name}.ccs_list': ['carbon_capture', 'carbon_storage'],
            f'{self.name}.scaling_factor_energy_production': self.scaling_factor_energy_production,
            f'{self.name}.scaling_factor_energy_consumption': self.scaling_factor_energy_consumption,
            f'{self.name}.energy_production_detailed': self.energy_production_detailed,
        }
        for energy in self.energy_list:
            inputs_dict[f'{self.name}.{energy}.CO2_per_use'] = self.CO2_per_use[energy]
            inputs_dict[f'{self.name}.{energy}.energy_production'] = self.energy_production[energy]
            inputs_dict[f'{self.name}.{energy}.energy_consumption'] = self.energy_consumption[energy]

        for energy in ['carbon_capture', 'carbon_storage']:
            inputs_dict[f'{self.name}.{energy}.energy_production'] = self.energy_production[energy]
            inputs_dict[f'{self.name}.{energy}.energy_consumption'] = self.energy_consumption[energy]
            inputs_dict[f'{self.name}.{energy}.energy_prices'] = self.energy_prices[energy]
            inputs_dict[f'{self.name}.{energy}.land_use_required'] = self.land_use_required[energy]
            inputs_dict[f'{self.name}.{energy}.energy_consumption_woratio'] = self.energy_consumption_woratio[energy]
            inputs_dict[f'{self.name}.{energy}.co2_emissions'] = self.co2_emissions
        inputs_dict[f'{self.name}.CO2_taxes'] = self.CO2_taxes
        inputs_dict[f'{self.name}.carbon_capture_from_energy_mix'] = self.carbon_capture_from_energy_mix
        inputs_dict[f'{self.name}.co2_emissions_needed_by_energy_mix'] = self.co2_emissions_needed_by_energy_mix

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)
#        for graph in graph_list:
#            graph.to_plotly().show()


if '__main__' == __name__:
    cls = CCUSDiscTestCase()
    cls.setUp()
    cls.test_01_CCUS_discipline()
