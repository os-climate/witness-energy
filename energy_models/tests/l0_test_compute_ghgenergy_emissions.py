'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/01-2023/11/03 Copyright 2023 Capgemini

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
from climateeconomics.sos_wrapping.sos_wrapping_agriculture.agriculture.agriculture_mix_disc import AgricultureMixDiscipline


class GHGEnergyEmissionsDiscTestCase(unittest.TestCase):
    """
    GHGEnergyEmissionsDisc  test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.year_start = 2020
        self.year_end = 2050
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.energy_list = [energy for energy in EnergyMix.energy_list if energy not in [
            'fossil', 'renewable', 'fuel.ethanol', 'carbon_capture', 'carbon_storage', 'heat.lowtemperatureheat',
            'heat.mediumtemperatureheat', 'heat.hightemperatureheat', 'biomass_dry']]
        #print('energy_list', self.energy_list)
        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_streams_output_dict.pkl'), 'rb')
        streams_outputs_dict = pickle.load(pkl_file)
        #print('streams_outputs_dict', streams_outputs_dict.keys())
        #print('pkl_file', pkl_file)
        pkl_file.close()
        self.ccs_list = ['carbon_capture', 'carbon_storage']

        self.CO2_per_use = {}
        self.CH4_per_use = {}
        self.N2O_per_use = {}
        self.energy_production, self.energy_consumption = {}, {}
        for i, energy in enumerate(self.energy_list):
            #print('energy', energy)
            self.CO2_per_use[f'{energy}'] = streams_outputs_dict[f'{energy}']['CO2_per_use']['value']
            self.CH4_per_use[f'{energy}'] = streams_outputs_dict[f'{energy}']['CH4_per_use']['value']
            self.N2O_per_use[f'{energy}'] = streams_outputs_dict[f'{energy}']['N2O_per_use']['value']
            self.energy_production[f'{energy}'] = streams_outputs_dict[f'{energy}'][GlossaryCore.EnergyProductionValue]['value']
            self.energy_consumption[f'{energy}'] = streams_outputs_dict[f'{energy}']['energy_consumption']['value']

        for i, energy in enumerate(self.ccs_list):
            self.energy_production[f'{energy}'] = streams_outputs_dict[f'{energy}'][GlossaryCore.EnergyProductionValue]['value']

        self.scaling_factor_energy_production = 1000.0
        self.scaling_factor_energy_consumption = 1000.0
        self.energy_production_detailed = streams_outputs_dict['energy_production_detailed']

        self.co2_emissions_ccus_Gt = pd.DataFrame({'years': self.years,
                                                   'carbon_storage Limited by capture (Gt)': np.linspace(1, 6, len(self.years))
                                                   })
        self.co2_emissions_needed_by_energy_mix = pd.DataFrame({'years': self.years,
                                                                'carbon_capture needed by energy mix (Gt)': np.linspace(0.001, 0.3, len(self.years))
                                                                })

    def tearDown(self):
        pass

    def test_01_ghgenergy_discipline(self):

        self.name = 'Test'
        self.model_name = 'GHGEnergyEmissions'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name,
                   'ns_energy': self.name,
                   'ns_ccs': self.name,
                   'ns_energy_study': self.name,
                   'ns_witness': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.energy_ghg_emissions.energy_ghg_emissions_disc.EnergyGHGEmissionsDiscipline'
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
            f'{self.name}.co2_emissions_ccus_Gt': self.co2_emissions_ccus_Gt,
            f'{self.name}.co2_emissions_needed_by_energy_mix': self.co2_emissions_needed_by_energy_mix,
            f'{self.name}.ccs_list': self.ccs_list

        }

        for energy in self.energy_list:
            if energy == 'biomass_dry':
                inputs_dict[f'{self.name}.{AgricultureMixDiscipline.name}.CO2_per_use'] = self.CO2_per_use[energy]
                inputs_dict[f'{self.name}.{AgricultureMixDiscipline.name}.CH4_per_use'] = self.CH4_per_use[energy]
                inputs_dict[f'{self.name}.{AgricultureMixDiscipline.name}.N2O_per_use'] = self.N2O_per_use[energy]
                inputs_dict[f'{self.name}.{AgricultureMixDiscipline.name}.energy_production'] = self.energy_production[energy]
                inputs_dict[f'{self.name}.{AgricultureMixDiscipline.name}.energy_consumption'] = self.energy_consumption[energy]
            else:

                inputs_dict[f'{self.name}.{energy}.CO2_per_use'] = self.CO2_per_use[energy]
                inputs_dict[f'{self.name}.{energy}.CH4_per_use'] = self.CH4_per_use[energy]
                inputs_dict[f'{self.name}.{energy}.N2O_per_use'] = self.N2O_per_use[energy]
                inputs_dict[f'{self.name}.{energy}.energy_production'] = self.energy_production[energy]
                inputs_dict[f'{self.name}.{energy}.energy_consumption'] = self.energy_consumption[energy]

        for energy in self.ccs_list:
            inputs_dict[f'{self.name}.{energy}.energy_production'] = self.energy_production[
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
