'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/14-2023/11/16 Copyright 2023 Capgemini

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

from os.path import dirname

import numpy as np
import pandas as pd

from energy_models.core.demand.energy_demand import EnergyDemand
from energy_models.glossaryenergy import GlossaryEnergy
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tests.core.abstract_jacobian_unit_test import AbstractJacobianUnittest


class DemandModelJacobianTestCase(AbstractJacobianUnittest):
    """
    DemandModel jacobian test class
    """

    # AbstractJacobianUnittest.DUMP_JACOBIAN = True

    def analytic_grad_entry(self):
        return [
            self.test_01_demand_model_discipline_jacobian
        ]

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.year_start = GlossaryEnergy.YeartStartDefault
        self.year_end = GlossaryEnergy.YeartEndDefault
        self.years = np.arange(self.year_start, self.year_end + 1)

        self.energy_production_detailed = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                                        EnergyDemand.elec_prod_column: np.linspace(20000, 19000,
                                                                                                   len(self.years)),
                                                        f'production {GlossaryEnergy.hydrogen}.{GlossaryEnergy.liquid_hydrogen} (TWh)': np.linspace(20000,
                                                                                                                 19000,
                                                                                                                 len(self.years)),
                                                        f'production {GlossaryEnergy.fuel}.{GlossaryEnergy.liquid_fuel} (TWh)': np.linspace(10000, 12000,
                                                                                                         len(self.years)),
                                                        f'production {GlossaryEnergy.fuel}.{GlossaryEnergy.biodiesel} (TWh)': np.linspace(11000, 12000,
                                                                                                       len(self.years)),
                                                        f'production {GlossaryEnergy.methane} (TWh)': np.linspace(5000., 6000.,
                                                                                                len(self.years)),
                                                        f'production {GlossaryEnergy.biogas} (TWh)': np.linspace(1000., 1500.,
                                                                                               len(self.years)),
                                                        f'production {GlossaryEnergy.fuel}.{GlossaryEnergy.hydrotreated_oil_fuel} (TWh)': np.linspace(
                                                            2000., 3000., len(self.years)),
                                                        })
        self.population = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                        GlossaryEnergy.PopulationValue: np.linspace(7794.79, 9000., len(self.years))})
        self.transport_demand = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                              GlossaryEnergy.TransportDemandValue: np.linspace(33600., 30000.,
                                                                                               len(self.years))})

    def tearDown(self):
        pass

    def test_01_demand_model_discipline_jacobian(self):
        self.name = 'Test'
        self.model_name = 'demand_model'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': f'{self.name}',
                   GlossaryEnergy.NS_REFERENCE: f'{self.name}',
                   GlossaryEnergy.NS_FUNCTIONS: f'{self.name}.{self.model_name}',
                   GlossaryEnergy.NS_ENERGY_MIX: f'{self.name}',
                   GlossaryEnergy.NS_WITNESS: f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.demand.energy_demand_disc.EnergyDemandDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearStart}': self.year_start,
                       f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.EnergyProductionDetailedValue}': self.energy_production_detailed,
                       f'{self.name}.{GlossaryEnergy.PopulationDfValue}': self.population,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.TransportDemandValue}': self.transport_demand
                       }
        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()
        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc_techno.local_data,
                            inputs=[f'{self.name}.{GlossaryEnergy.EnergyProductionDetailedValue}',
                                    f'{self.name}.{GlossaryEnergy.PopulationDfValue}'],
                            outputs=[f'{self.name}.{self.model_name}.electricity_demand_constraint',
                                     f'{self.name}.{self.model_name}.transport_demand_constraint'
                                     ], )


if '__main__' == __name__:
    # AbstractJacobianUnittest.DUMP_JACOBIAN = True
    cls = DemandModelJacobianTestCase()
    cls.setUp()
    cls.test_01_demand_model_discipline_jacobian()
