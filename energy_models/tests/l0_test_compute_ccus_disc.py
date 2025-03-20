'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/01-2024/06/24 Copyright 2023 Capgemini

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
import unittest
from os.path import dirname, join

import numpy as np
import pandas as pd
from sostrades_core.execution_engine.execution_engine import ExecutionEngine

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.glossaryenergy import GlossaryEnergy


class CCUSDiscTestCase(unittest.TestCase):
    """
    CO2EmissionsDisc  test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.year_start = GlossaryEnergy.YearStartDefault
        self.year_end = GlossaryEnergy.YearEndDefaultValueGradientTest
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.energy_list = [energy for energy in EnergyMix.energy_list if energy not in [
            GlossaryEnergy.fossil, GlossaryEnergy.clean_energy, f'{GlossaryEnergy.fuel}.{GlossaryEnergy.ethanol}',
            GlossaryEnergy.carbon_capture, GlossaryEnergy.carbon_storage, f'{GlossaryEnergy.heat}.lowtemperatureheat',
            f'{GlossaryEnergy.heat}.mediumtemperatureheat', f'{GlossaryEnergy.heat}.hightemperatureheat',
            GlossaryEnergy.biomass_dry]]
        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_streams_output_dict.pkl'), 'rb')
        streams_outputs_dict = pickle.load(pkl_file)
        pkl_file.close()

        self.CO2_per_use = {}
        self.stream_prices = {}
        self.energy_consumption_woratio = {}
        self.energy_production, self.energy_consumption, self.land_use_required = {}, {}, {}
        for i, energy in enumerate(self.energy_list):
            self.CO2_per_use[f'{energy}'] = streams_outputs_dict[f'{energy}'][GlossaryEnergy.CO2PerUse]['value']
            self.energy_production[f'{energy}'] = \
                streams_outputs_dict[f'{energy}'][GlossaryEnergy.EnergyProductionValue]['value']
            self.energy_consumption[f'{energy}'] = \
                streams_outputs_dict[f'{energy}'][GlossaryEnergy.StreamConsumptionValue]['value']
        for energy in [GlossaryEnergy.carbon_capture, GlossaryEnergy.carbon_storage]:
            self.land_use_required[f'{energy}'] = \
                streams_outputs_dict[f'{energy}'][GlossaryEnergy.LandUseRequiredValue]['value']
            self.energy_production[f'{energy}'] = \
                streams_outputs_dict[f'{energy}'][GlossaryEnergy.EnergyProductionValue]['value']
            self.energy_consumption[f'{energy}'] = \
                streams_outputs_dict[f'{energy}'][GlossaryEnergy.StreamConsumptionValue]['value']
            self.stream_prices[f'{energy}'] = streams_outputs_dict[f'{energy}'][GlossaryEnergy.StreamPricesValue][
                'value']
            self.energy_consumption_woratio[f'{energy}'] = streams_outputs_dict[
                f'{energy}'][GlossaryEnergy.StreamConsumptionWithoutRatioValue]['value']

        self.scaling_factor_energy_production = 1000.0
        self.scaling_factor_energy_consumption = 1000.0
        self.energy_production_detailed = streams_outputs_dict[GlossaryEnergy.StreamProductionDetailedValue]
        years = streams_outputs_dict[f'{energy}'][GlossaryEnergy.StreamConsumptionValue]['value'][GlossaryEnergy.Years]
        self.CO2_taxes = pd.DataFrame(data={GlossaryEnergy.Years: years, GlossaryEnergy.CO2Tax: 150.})
        self.co2_emissions = pd.DataFrame(
            data={GlossaryEnergy.Years: years, 'carbon_capture needed by energy mix (Mt)': 0.005})
        self.co2_emissions = pd.DataFrame(
            data={GlossaryEnergy.Years: years, 'carbon_capture needed by energy mix (Mt)': 0.005})
        self.co2_emissions_needed_by_energy_mix = pd.DataFrame(
            data={GlossaryEnergy.Years: years, 'carbon_capture needed by energy mix (Gt)': 0.005})
        self.carbon_capture_from_energy_mix = pd.DataFrame(
            data={GlossaryEnergy.Years: years, 'carbon_capture from energy mix (Gt)': 1e-15})

    def tearDown(self):
        pass

    def test_01_CCUS_discipline(self):

        self.name = 'Test'
        self.model_name = 'ConsumptionCO2Emissions'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name,
                   'ns_energy': self.name,
                   GlossaryEnergy.NS_CCS: self.name,
                   'ns_energy_study': self.name,
                   GlossaryEnergy.NS_FUNCTIONS: self.name,
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
            f'{self.name}.{GlossaryEnergy.YearStart}': self.year_start,
            f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
            f'{self.name}.{GlossaryEnergy.energy_list}': self.energy_list,
            f'{self.name}.{GlossaryEnergy.StreamProductionDetailedValue}': self.energy_production_detailed,
        }
        for energy in self.energy_list:
            inputs_dict[f'{self.name}.{energy}.{GlossaryEnergy.CO2PerUse}'] = self.CO2_per_use[energy]
            inputs_dict[f'{self.name}.{energy}.{GlossaryEnergy.EnergyProductionValue}'] = self.energy_production[energy]
            inputs_dict[f'{self.name}.{energy}.{GlossaryEnergy.StreamConsumptionValue}'] = self.energy_consumption[
                energy]

        for energy in [GlossaryEnergy.carbon_capture, GlossaryEnergy.carbon_storage]:
            inputs_dict[f'{self.name}.{energy}.{GlossaryEnergy.EnergyProductionValue}'] = self.energy_production[energy]
            inputs_dict[f'{self.name}.{energy}.{GlossaryEnergy.StreamConsumptionValue}'] = self.energy_consumption[
                energy]
            inputs_dict[f'{self.name}.{energy}.{GlossaryEnergy.StreamPricesValue}'] = self.stream_prices[energy]
            inputs_dict[f'{self.name}.{energy}.{GlossaryEnergy.LandUseRequiredValue}'] = self.land_use_required[energy]
            inputs_dict[f'{self.name}.{energy}.{GlossaryEnergy.StreamConsumptionWithoutRatioValue}'] = \
                self.energy_consumption_woratio[energy]
            inputs_dict[f'{self.name}.{energy}.co2_emissions'] = self.co2_emissions
        inputs_dict[f'{self.name}.{GlossaryEnergy.CO2TaxesValue}'] = self.CO2_taxes
        inputs_dict[f'{self.name}.carbon_capture_from_energy_mix'] = self.carbon_capture_from_energy_mix
        inputs_dict[f'{self.name}.co2_emissions_needed_by_energy_mix'] = self.co2_emissions_needed_by_energy_mix

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)
        for graph in graph_list:
            # graph.to_plotly().show()
            pass


if '__main__' == __name__:
    cls = CCUSDiscTestCase()
    cls.setUp()
    cls.test_01_CCUS_discipline()
