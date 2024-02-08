'''
Copyright 2022 Airbus SAS
Modifications on 2023/09/06-2023/11/03 Copyright 2023 Capgemini

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

from os.path import join, dirname

import numpy as np
import pandas as pd
from pandas import read_csv

from climateeconomics.glossarycore import GlossaryCore
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tests.core.abstract_jacobian_unit_test import AbstractJacobianUnittest
from energy_models.glossaryenergy import GlossaryEnergy

class HeatMixJacobianTestCase(AbstractJacobianUnittest):
    # AbstractJacobianUnittest.DUMP_JACOBIAN = True

    def setUp(self):
        self.name = 'Test'
        self.model_name = 'HeatMix'
        self.year_start =GlossaryCore.YeartStartDefault
        self.year_end = GlossaryCore.YeartEndDefault
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.year_range = self.year_end - self.year_start

        ns_dict = {GlossaryCore.NS_WITNESS: f'{self.name}',
                   'ns_public': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_energy': f'{self.name}.{self.model_name}',
                   GlossaryCore.NS_ENERGY_MIX: f'{self.name}',
                   GlossaryCore.NS_REFERENCE: f'{self.name}',
                   GlossaryCore.NS_FUNCTIONS: f'{self.name}'}
        self.ee = ExecutionEngine(self.name)
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.heat_mix.heat_mix_disc.Heat_Mix_Discipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)
        self.ee.configure()
        self.ee.display_treeview_nodes()

        heat_energy_list= ['heat.hightemperatureheat', 'heat.lowtemperatureheat', 'heat.mediumtemperatureheat']
        high_heat_techno_list =  ['NaturalGasBoilerHighHeat', 'ElectricBoilerHighHeat',
                           'HeatPumpHighHeat', 'GeothermalHighHeat', 'CHPHighHeat', 'HydrogenBoilerHighHeat']
        medium_heat_techno_list = ['NaturalGasBoilerMediumHeat', 'ElectricBoilerMediumHeat',
                           'HeatPumpMediumHeat', 'GeothermalMediumHeat', 'CHPMediumHeat', 'HydrogenBoilerMediumHeat']

        low_heat_techno_list = ['NaturalGasBoilerLowHeat', 'ElectricBoilerLowHeat',
                           'HeatPumpLowHeat', 'GeothermalLowHeat', 'CHPLowHeat', 'HydrogenBoilerLowHeat'],

        energy_mix_emission_dic = {}
        energy_mix_emission_dic[GlossaryEnergy.Years] = self.years
        energy_mix_emission_dic['heat.hightemperatureheat.NaturalGasBoilerHighHeat'] = np.ones(len(self.years)) * 10.0
        energy_mix_emission_dic['heat.hightemperatureheat.ElectricBoilerHighHeat'] = np.ones(len(self.years)) * 20.0
        energy_mix_emission_dic['heat.hightemperatureheat.HeatPumpHighHeat'] = np.ones(len(self.years)) * 30.0
        energy_mix_emission_dic['heat.hightemperatureheat.GeothermalHighHeat'] = np.ones(len(self.years)) * 40.0
        energy_mix_emission_dic['heat.hightemperatureheat.CHPHighHeat'] = np.ones(len(self.years)) * 50.0
        energy_mix_emission_dic['heat.hightemperatureheat.HydrogenBoilerHighHeat'] = np.ones(len(self.years)) * 60.0

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

        energy_mix_emission = pd.DataFrame(energy_mix_emission_dic)

        energy_mix_target_production_dic = {}
        energy_mix_target_production_dic[GlossaryEnergy.Years] = self.years
        energy_mix_target_production_dic['target production'] = 260

        self.traget_production = pd.DataFrame(energy_mix_target_production_dic)


        ############
        energy_mix_high_heat_production_dic = {}
        energy_mix_high_heat_production_dic[GlossaryEnergy.Years] = self.years
        energy_mix_high_heat_production_dic['NaturalGasBoilerHighHeat'] = np.ones(len(self.years)) * 2
        energy_mix_high_heat_production_dic['ElectricBoilerHighHeat'] = np.ones(len(self.years)) * 3
        energy_mix_high_heat_production_dic['HeatPumpHighHeat'] = np.ones(len(self.years)) * 4
        energy_mix_high_heat_production_dic['GeothermalHighHeat'] = np.ones(len(self.years)) * 5
        energy_mix_high_heat_production_dic['CHPHighHeat'] = np.ones(len(self.years)) * 6
        energy_mix_high_heat_production_dic['HydrogenBoilerHighHeat'] = np.ones(len(self.years)) * 7
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

        self.values_dict = {
                            f'{self.name}.{GlossaryEnergy.YearStart}': self.year_start,
                            f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                            f'{self.name}.{GlossaryEnergy.energy_list}': heat_energy_list,
                            'heat.hightemperatureheat.technologies_list': high_heat_techno_list,
                            'heat.lowtemperatureheat.technologies_list': low_heat_techno_list,
                            'heat.mediumtemperatureheat.technologies_list': medium_heat_techno_list,
                            f'{self.name}.{self.model_name}.CO2_emission_mix': energy_mix_emission,
                            f'{self.name}.{self.model_name}.target_heat_production': self.traget_production,
                            f'{self.name}.{self.model_name}.heat.hightemperatureheat.{GlossaryEnergy.EnergyProductionValue}': self.high_heat_production,
                            f'{self.name}.{self.model_name}.heat.lowtemperatureheat.{GlossaryEnergy.EnergyProductionValue}': self.low_heat_production,
                            f'{self.name}.{self.model_name}.heat.mediumtemperatureheat.{GlossaryEnergy.EnergyProductionValue}': self.medium_heat_production,

                            }

        self.ee.load_study_from_input_dict(self.values_dict)

    def analytic_grad_entry(self):
        return [
            self.test_01_heat_mix_analytic_grad,
        ]

    def test_01_heat_mix_analytic_grad(self):
        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_heat_mix_discipline.pkl', discipline=disc_techno, step=1e-15,local_data = disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.CO2_emission_mix',
                                    f'{self.name}.{self.model_name}.target_heat_production',
                                    ],
                            outputs=[f'{self.name}.CO2MinimizationObjective',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.EnergyCO2EmissionsValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.EnergyProductionValue}',
                            ],
                            derr_approx='complex_step')
