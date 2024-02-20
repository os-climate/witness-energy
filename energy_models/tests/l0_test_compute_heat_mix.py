'''
Copyright 2024 Capgemini

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

import numpy as np
import pandas as pd
import scipy.interpolate as sc

# from energy_models.core.energy_mix.energy_mix import HeatMix
from energy_models.core.heat_mix.heat_mix import HeatMix
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import GaseousHydrogen
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.glossaryenergy import GlossaryEnergy
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tools.post_processing.post_processing_factory import PostProcessingFactory


class HeatMixTestCase(unittest.TestCase):
    """
    HeatMix test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.year_start = 2020
        self.year_end = 2050
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.year_range = self.year_end - self.year_start + 1
        self.energy_list = ['heat.hightemperatureheat', 'heat.lowtemperatureheat', 'heat.mediumtemperatureheat']


        ############################################################################
        energy_mix_emission_dic = {}
        energy_mix_emission_dic[GlossaryEnergy.Years] = self.years
        energy_mix_emission_dic['heat.hightemperatureheat.NaturalGasBoilerHighHeat'] = np.ones(len(self.years)) * 10.0
        energy_mix_emission_dic['heat.hightemperatureheat.ElectricBoilerHighHeat'] = np.ones(len(self.years)) * 20.0
        energy_mix_emission_dic['heat.hightemperatureheat.HeatPumpHighHeat'] = np.ones(len(self.years)) * 30.0
        energy_mix_emission_dic['heat.hightemperatureheat.GeothermalHighHeat'] = np.ones(len(self.years)) * 40.0
        energy_mix_emission_dic['heat.hightemperatureheat.CHPHighHeat'] = np.ones(len(self.years)) * 50.0
        energy_mix_emission_dic['heat.hightemperatureheat.HydrogenBoilerHighHeat'] = np.ones(len(self.years)) * 60.0
        energy_mix_emission_dic['heat.hightemperatureheat.SofcgtHighHeat'] = np.ones(len(self.years)) * 60.0

        energy_mix_emission_dic['heat.lowtemperatureheat.NaturalGasBoilerLowHeat'] = np.ones(len(self.years)) * 10.0
        energy_mix_emission_dic['heat.lowtemperatureheat.ElectricBoilerLowHeat'] = np.ones(len(self.years)) * 20.0
        energy_mix_emission_dic['heat.lowtemperatureheat.HeatPumpLowHeat'] = np.ones(len(self.years)) * 30.0
        energy_mix_emission_dic['heat.lowtemperatureheat.GeothermalLowHeat'] = np.ones(len(self.years)) * 40.0
        energy_mix_emission_dic['heat.lowtemperatureheat.CHPLowHeat'] = np.ones(len(self.years)) * 50.0
        energy_mix_emission_dic['heat.lowtemperatureheat.HydrogenBoilerLowHeat'] = np.ones(len(self.years)) * 60.0

        energy_mix_emission_dic['heat.mediumtemperatureheat.NaturalGasBoilerMediumHeat'] = np.ones(
            len(self.years)) * 10.0
        energy_mix_emission_dic['heat.mediumtemperatureheat.ElectricBoilerMediumHeat'] = np.ones(len(self.years)) * 20.0
        energy_mix_emission_dic['heat.mediumtemperatureheat.HeatPumpMediumHeat'] = np.ones(len(self.years)) * 30.0
        energy_mix_emission_dic['heat.mediumtemperatureheat.GeothermalMediumHeat'] = np.ones(len(self.years)) * 40.0
        energy_mix_emission_dic['heat.mediumtemperatureheat.CHPMediumHeat'] = np.ones(len(self.years)) * 50.0
        energy_mix_emission_dic['heat.mediumtemperatureheat.HydrogenBoilerMediumHeat'] = np.ones(len(self.years)) * 60.0

        self.energy_mix = pd.DataFrame(energy_mix_emission_dic)

        self.target_production = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.TargetHeatProductionValue: 260.
        })

        ############
        energy_mix_high_heat_production_dic = {}
        energy_mix_high_heat_production_dic[GlossaryEnergy.Years] = self.years
        energy_mix_high_heat_production_dic['NaturalGasBoilerHighHeat'] = np.ones(len(self.years)) * 2
        energy_mix_high_heat_production_dic['ElectricBoilerHighHeat'] = np.ones(len(self.years)) * 3
        energy_mix_high_heat_production_dic['HeatPumpHighHeat'] = np.ones(len(self.years)) * 4
        energy_mix_high_heat_production_dic['GeothermalHighHeat'] = np.ones(len(self.years)) * 5
        energy_mix_high_heat_production_dic['CHPHighHeat'] = np.ones(len(self.years)) * 6
        energy_mix_high_heat_production_dic['HydrogenBoilerHighHeat'] = np.ones(len(self.years)) * 7
        energy_mix_high_heat_production_dic['SofcgtHighHeat'] = np.ones(len(self.years)) * 8
        self.high_heat_production = pd.DataFrame(energy_mix_high_heat_production_dic)

        energy_mix_low_heat_production_dic = {}
        energy_mix_low_heat_production_dic[GlossaryEnergy.Years] = self.years
        energy_mix_low_heat_production_dic['NaturalGasBoilerLowHeat'] = np.ones(len(self.years)) * 15.0
        energy_mix_low_heat_production_dic['ElectricBoilerLowHeat'] = np.ones(len(self.years)) * 16.0
        energy_mix_low_heat_production_dic['HeatPumpLowHeat'] = np.ones(len(self.years)) * 17.0
        energy_mix_low_heat_production_dic['GeothermalLowHeat'] = np.ones(len(self.years)) * 18.0
        energy_mix_low_heat_production_dic['CHPLowHeat'] = np.ones(len(self.years)) * 19.0
        energy_mix_low_heat_production_dic['HydrogenBoilerLowHeat'] = np.ones(len(self.years)) * 20.0
        self.low_heat_production = pd.DataFrame(energy_mix_low_heat_production_dic)

        energy_mix_mediun_heat_production_dic = {}
        energy_mix_mediun_heat_production_dic[GlossaryEnergy.Years] = self.years
        energy_mix_mediun_heat_production_dic['NaturalGasBoilerMediumHeat'] = np.ones(len(self.years)) * 22.0
        energy_mix_mediun_heat_production_dic['ElectricBoilerMediumHeat'] = np.ones(len(self.years)) * 23.0
        energy_mix_mediun_heat_production_dic['HeatPumpMediumHeat'] = np.ones(len(self.years)) * 24.0
        energy_mix_mediun_heat_production_dic['GeothermalMediumHeat'] = np.ones(len(self.years)) * 25.0
        energy_mix_mediun_heat_production_dic['CHPMediumHeat'] = np.ones(len(self.years)) * 13.0
        energy_mix_mediun_heat_production_dic['HydrogenBoilerMediumHeat'] = np.ones(len(self.years)) * 18.0
        self.medium_heat_production = pd.DataFrame(energy_mix_mediun_heat_production_dic)

    def test_01_energy_mix(self):
        """
        Test heat mix class

        Returns
        -------
        None.

        """

        inputs_dict = {GlossaryEnergy.YearStart: self.year_start,
                       GlossaryEnergy.YearEnd: self.year_end,
                       GlossaryEnergy.energy_list: self.energy_list, #['heat.hightemperatureheat', 'heat.lowtemperatureheat', 'heat.mediumtemperatureheat'], #'heat.mediumtemperatureheat',
                       'heat.hightemperatureheat.technologies_list': ['NaturalGasBoilerHighHeat', 'ElectricBoilerHighHeat',
                           'HeatPumpHighHeat', 'GeothermalHighHeat', 'CHPHighHeat', 'HydrogenBoilerHighHeat','SofcgtHighHeat'],
                       'heat.lowtemperatureheat.technologies_list': ['NaturalGasBoilerLowHeat', 'ElectricBoilerLowHeat',
                           'HeatPumpLowHeat', 'GeothermalLowHeat', 'CHPLowHeat', 'HydrogenBoilerLowHeat'],
                       'heat.mediumtemperatureheat.technologies_list': ['NaturalGasBoilerMediumHeat', 'ElectricBoilerMediumHeat',
                           'HeatPumpMediumHeat', 'GeothermalMediumHeat', 'CHPMediumHeat', 'HydrogenBoilerMediumHeat'],
                       'CO2_emission_mix': self.energy_mix,
                       GlossaryEnergy.TargetHeatProductionValue: self.target_production,
                       f'heat.hightemperatureheat.{GlossaryEnergy.EnergyProductionValue}': self.high_heat_production,
                       f'heat.lowtemperatureheat.{GlossaryEnergy.EnergyProductionValue}': self.low_heat_production,
                       f'heat.mediumtemperatureheat.{GlossaryEnergy.EnergyProductionValue}': self.medium_heat_production,
                       }

        EM = HeatMix('HeatMix')
        EM.configure(inputs_dict)
        EM.compute(inputs_dict)
        EM.compute_CO2_emissions(inputs_dict)


    def test_02_heat_mix_discipline(self):
        """
        Test heat mix discipline
        """

        name = 'Test'
        model_name = 'HeatMix'
        ee = ExecutionEngine(name)
        ns_dict = {'ns_public': f'{name}',
                   'ns_energy_study': f'{name}',
                   GlossaryEnergy.NS_ENERGY_MIX: f'{name}.{model_name}',
                   GlossaryEnergy.NS_FUNCTIONS: f'{name}.{model_name}',
                   GlossaryEnergy.NS_REFERENCE: f'{name}.{model_name}',
                   'ns_energy': f'{name}.{model_name}',
                   GlossaryEnergy.NS_WITNESS: f'{name}'}
        ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.heat_mix.heat_mix_disc.Heat_Mix_Discipline'
        builder = ee.factory.get_builder_from_module(model_name, mod_path)

        ee.factory.set_builders_to_coupling_builder(builder)

        ee.configure()
        ee.display_treeview_nodes()

        inputs_dict = {f'{name}.{GlossaryEnergy.YearStart}': self.year_start,
                       f'{name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       #GlossaryEnergy.energy_list: ['heat.hightemperatureheat', 'heat.lowtemperatureheat'],
                       f'{name}.{GlossaryEnergy.energy_list}': ['heat.hightemperatureheat', 'heat.lowtemperatureheat', 'heat.mediumtemperatureheat'],
                       # 'heat.mediumtemperatureheat',
                       'heat.hightemperatureheat.technologies_list': ['NaturalGasBoilerHighHeat',
                                                                      'ElectricBoilerHighHeat',
                                                                      'HeatPumpHighHeat', 'GeothermalHighHeat',
                                                                      'CHPHighHeat', 'HydrogenBoilerHighHeat','SofcgtHighHeat'],
                       'heat.lowtemperatureheat.technologies_list': ['NaturalGasBoilerLowHeat', 'ElectricBoilerLowHeat',
                                                                     'HeatPumpLowHeat', 'GeothermalLowHeat',
                                                                     'CHPLowHeat', 'HydrogenBoilerLowHeat'],
                       'heat.mediumtemperatureheat.technologies_list': ['NaturalGasBoilerMediumHeat',
                                                                        'ElectricBoilerMediumHeat',
                                                                        'HeatPumpMediumHeat', 'GeothermalMediumHeat',
                                                                        'CHPMediumHeat', 'HydrogenBoilerMediumHeat'],
                       f'{name}.{model_name}.CO2_emission_mix': self.energy_mix,
                       f'{name}.{model_name}.{GlossaryEnergy.TargetHeatProductionValue}': self.target_production,
                       f'{name}.{model_name}.heat.hightemperatureheat.{GlossaryEnergy.EnergyProductionValue}': self.high_heat_production,
                       f'{name}.{model_name}.heat.lowtemperatureheat.{GlossaryEnergy.EnergyProductionValue}': self.low_heat_production,
                       f'{name}.{model_name}.heat.mediumtemperatureheat.{GlossaryEnergy.EnergyProductionValue}': self.medium_heat_production,

                       }

        # self.high_heat_production
        ee.load_study_from_input_dict(inputs_dict)

        ee.execute()

        disc = ee.dm.get_disciplines_with_name(
            f'{name}.{model_name}')[0]
        ppf = PostProcessingFactory()
        filters = ppf.get_post_processing_filters_by_discipline(disc)
        graph_list = ppf.get_post_processing_by_discipline(
            disc, filters, as_json=False)

        # for graph in graph_list:
        #    graph.to_plotly().show()



if '__main__' == __name__:
    cls = HeatMixTestCase()
    cls.setUp()
    cls.test_02_heat_mix_discipline()
