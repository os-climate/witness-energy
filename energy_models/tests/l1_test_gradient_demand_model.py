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

import numpy as np
import pandas as pd
from os.path import join, dirname
import scipy.interpolate as sc

from sos_trades_core.execution_engine.execution_engine import ExecutionEngine
from energy_models.core.stream_type.resources_data_disc import get_static_CO2_emissions,\
    get_static_prices
from sos_trades_core.tests.core.abstract_jacobian_unit_test import AbstractJacobianUnittest
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
from energy_models.core.energy_mix.energy_mix import EnergyMix
import pickle
from energy_models.core.demand.energy_demand import EnergyDemand


class DemandModelJacobianTestCase(AbstractJacobianUnittest):
    """
    DemandModel jacobian test class
    """
    #AbstractJacobianUnittest.DUMP_JACOBIAN = True

    def analytic_grad_entry(self):
        return [
            self.test_01_demand_model_discipline_jacobian
        ]

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.year_start = 2020
        self.year_end = 2100
        self.years = np.arange(self.year_start, self.year_end + 1)

        self.energy_production_detailed = pd.DataFrame({'years': self.years,
                                                        EnergyDemand.elec_prod_column: np.linspace(20000, 19000, len(self.years)),
                                                        'production hydrogen.liquid_hydrogen (TWh)' : np.linspace(20000, 19000, len(self.years)),
                                                        'production fuel.liquid_fuel (TWh)': np.linspace(10000, 12000, len(self.years)),
                                                        'production fuel.biodiesel (TWh)': np.linspace(11000, 12000, len(self.years)),
                                                        'production methane (TWh)': np.linspace(5000., 6000., len(self.years)),
                                                        'production biogas (TWh)': np.linspace(1000., 1500., len(self.years)),
                                                        'production fuel.hydrotreated_oil_fuel (TWh)': np.linspace(2000., 3000., len(self.years)),
                                                        })
        self.population = pd.DataFrame({'years': self.years,
                                        'population': np.linspace(7794.79, 9000., len(self.years))})
        self.transport_demand=pd.DataFrame({'years': self.years,
                                'transport_demand': np.linspace(33600., 30000., len(self.years))})

    def tearDown(self):
        pass

    def test_01_demand_model_discipline_jacobian(self):

        self.name = 'Test'
        self.model_name = 'demand_model'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': f'{self.name}',
                   'ns_ref': f'{self.name}',
                   'ns_functions': f'{self.name}.{self.model_name}',
                   'ns_energy_mix': f'{self.name}',
                   'ns_witness': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.demand.energy_demand_disc.EnergyDemandDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.year_start': self.year_start,
                       f'{self.name}.year_end': self.year_end,
                       f'{self.name}.energy_production_detailed': self.energy_production_detailed,
                       f'{self.name}.population_df': self.population,
                       f'{self.name}.{self.model_name}.transport_demand': self.transport_demand
                       }
        self.ee.load_study_from_input_dict(inputs_dict)

        disc_techno = self.ee.root_process.sos_disciplines[0]

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            inputs=[f'{self.name}.energy_production_detailed',
                                    f'{self.name}.population_df'],
                            outputs=[f'{self.name}.{self.model_name}.electricity_demand_constraint',
                                     f'{self.name}.{self.model_name}.transport_demand_constraint'
                                     ],)


if '__main__' == __name__:
    AbstractJacobianUnittest.DUMP_JACOBIAN = True
    cls = DemandModelJacobianTestCase()
    cls.setUp()
    cls.test_01_demand_model_discipline_jacobian()
