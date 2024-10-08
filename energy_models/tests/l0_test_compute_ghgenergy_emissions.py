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
from climateeconomics.sos_wrapping.sos_wrapping_agriculture.agriculture.agriculture_mix_disc import (
    AgricultureMixDiscipline,
)
from sostrades_core.execution_engine.execution_engine import ExecutionEngine

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.glossaryenergy import GlossaryEnergy


class GHGEnergyEmissionsDiscTestCase(unittest.TestCase):
    """
    GHGEnergyEmissionsDisc  test class
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
        # print(GlossaryEnergy.energy_list, self.energy_list)
        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_streams_output_dict.pkl'), 'rb')
        streams_outputs_dict = pickle.load(pkl_file)
        # print('streams_outputs_dict', streams_outputs_dict.keys())
        # print('pkl_file', pkl_file)
        pkl_file.close()
        self.ccs_list = [GlossaryEnergy.carbon_capture, GlossaryEnergy.carbon_storage]

        self.CO2_per_use = {}
        self.CH4_per_use = {}
        self.N2O_per_use = {}
        self.energy_production, self.energy_consumption = {}, {}
        for i, energy in enumerate(self.energy_list):
            # print('energy', energy)
            self.CO2_per_use[f'{energy}'] = streams_outputs_dict[f'{energy}'][GlossaryEnergy.CO2PerUse]['value']
            self.CH4_per_use[f'{energy}'] = streams_outputs_dict[f'{energy}'][GlossaryEnergy.CH4PerUse]['value']
            self.N2O_per_use[f'{energy}'] = streams_outputs_dict[f'{energy}'][GlossaryEnergy.N2OPerUse]['value']
            self.energy_production[f'{energy}'] = \
                streams_outputs_dict[f'{energy}'][GlossaryEnergy.EnergyProductionValue]['value']
            self.energy_consumption[f'{energy}'] = \
                streams_outputs_dict[f'{energy}'][GlossaryEnergy.StreamConsumptionValue]['value']

        for i, energy in enumerate(self.ccs_list):
            self.energy_production[f'{energy}'] = \
                streams_outputs_dict[f'{energy}'][GlossaryEnergy.EnergyProductionValue]['value']

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

    def tearDown(self):
        pass

    def test_01_ghgenergy_discipline(self):

        self.name = 'Test'
        self.model_name = 'GHGEnergyEmissions'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name,
                   'ns_energy': self.name,
                   GlossaryEnergy.NS_CCS: self.name,
                   GlossaryEnergy.NS_FUNCTIONS: self.name,
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
                    self.energy_production[energy]
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
            inputs_dict[f'{self.name}.{energy}.{GlossaryEnergy.EnergyProductionValue}'] = self.energy_production[
                energy]

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)


#         for graph in graph_list:
#             graph.to_plotly().show()


if '__main__' == __name__:
    cls = GHGEnergyEmissionsDiscTestCase()
    cls.setUp()
    cls.test_01_ghgenergy_discipline()
