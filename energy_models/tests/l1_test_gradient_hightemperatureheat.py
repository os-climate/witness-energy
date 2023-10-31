'''
Copyright (c) 2023 Capgemini

All rights reserved

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer
in the documentation and/or mother materials provided with the distribution.
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
INCLUDING BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND OR ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''
from sostrades_core.tests.core.abstract_jacobian_unit_test import AbstractJacobianUnittest
import pandas as pd
import numpy as np
import scipy.interpolate as sc
from os.path import join, dirname
from energy_models.models.biogas.anaerobic_digestion.anaerobic_digestion_disc import AnaerobicDigestionDiscipline
from energy_models.models.biogas.anaerobic_digestion.anaerobic_digestion import AnaerobicDigestion
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from energy_models.core.stream_type.resources_data_disc import get_static_CO2_emissions,\
    get_static_prices

from climateeconomics.core.core_resources.resource_mix.resource_mix import ResourceMixModel
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary


class HighTemperatureHeatJacobianTestCase(AbstractJacobianUnittest):
    """
    Anaerobic Digestion prices test class
    """

    # AbstractJacobianUnittest.DUMP_JACOBIAN = True

    def analytic_grad_entry(self):
        return [
            self.test_01_hydrogen_boiler_discipline_analytic_grad,
        ]

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.energy_name = 'hightemperatureheat'
        years = np.arange(2020, 2051)
        self.resource_list = [
            'oil_resource', 'natural_gas_resource', 'uranium_resource', 'coal_resource']
        self.ratio_available_resource = pd.DataFrame(
            {'years': np.arange(2020, 2050 + 1)})
        for types in self.resource_list:
            self.ratio_available_resource[types] = np.linspace(
                1, 1, len(self.ratio_available_resource.index))
        electricity_price = np.array([0.09, 0.08974117039450046, 0.08948672733558984,
                                      0.089236536471781, 0.08899046935409588, 0.08874840310033885,
                                      0.08875044941298937, 0.08875249600769718, 0.08875454288453355,
                                      0.08875659004356974, 0.0887586374848771, 0.08893789675406477,
                                      0.08911934200930778, 0.08930302260662477, 0.08948898953954933,
                                      0.08967729551117891, 0.08986799501019029, 0.09006114439108429,
                                      0.09025680195894345, 0.09045502805900876, 0.09065588517140537,
                                      0.0908594380113745, 0.09106575363539733, 0.09127490155362818,
                                      0.09148695384909017, 0.0917019853041231, 0.0919200735346165,
                                      0.09214129913260598, 0.09236574581786147, 0.09259350059915213,
                                      0.0928246539459331]) * 1000.0
        # We take biomass price of methane/5.0
        self.energy_prices = pd.DataFrame({'years': years, 'electricity': electricity_price, 'hydrogen.gaseous_hydrogen': 0.0
                                           })
        self.resources_prices = pd.DataFrame({'years': years, ResourceGlossary.WetBiomass['name']: electricity_price / 100.0, 'hydrogen.gaseous_hydrogen': 0.0
                                              })

        self.energy_carbon_emissions = pd.DataFrame(
            {'years': years, 'electricity': 0.0, 'hydrogen.gaseous_hydrogen': 0.0})

        self.invest_level = pd.DataFrame(
            {'years': years, 'invest': np.array([4435750000.0, 4522000000.0, 4608250000.0,
                                                 4694500000.0, 4780750000.0, 4867000000.0,
                                                 4969400000.0, 5071800000.0, 5174200000.0,
                                                 5276600000.0, 5379000000.0, 5364700000.0,
                                                 5350400000.0, 5336100000.0, 5321800000.0,
                                                 5307500000.0, 5293200000.0, 5278900000.0,
                                                 5264600000.0, 5250300000.0, 5236000000.0,
                                                 5221700000.0, 5207400000.0, 5193100000.0,
                                                 5178800000.0, 5164500000.0, 5150200000.0,
                                                 5135900000.0, 5121600000.0, 5107300000.0,
                                                 5093000000.0]) / 5.0 * 1e-9})
        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [14.86, 17.22, 20.27,
                     29.01,  34.05,   39.08,  44.69,   50.29]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {'years': years, 'CO2_tax': func(years)})
        self.margin = pd.DataFrame(
            {'years': years, 'margin': np.ones(len(years)) * 110.0})
        # From future of hydrogen
        self.transport = pd.DataFrame(
            {'years': years, 'transport': np.ones(len(years)) * 0.0})
        self.scaling_factor_techno_consumption = 1e3
        self.scaling_factor_techno_production = 1e3
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.ones((len(years), len(years)))))
        demand_ratio_dict['years'] = years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)
        self.is_stream_demand = True
        self.is_apply_resource_ratio = True

    def tearDown(self):
        pass

    def test_01_hydrogen_boiler_discipline_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'HydrogenBoilerHighHeat'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_heat_high': f'{self.name}',
                   'ns_resource': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.heat.high.hydrogen_boiler_high_heat.hydrogen_boiler_high_heat_disc.HydrogenBoilerHighHeatDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.year_end': 2050,
                       f'{self.name}.energy_prices': self.energy_prices,
                       f'{self.name}.energy_CO2_emissions': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.invest_level': self.invest_level,
                       f'{self.name}.CO2_taxes': self.co2_taxes,
                       f'{self.name}.transport_margin': self.margin,
                       f'{self.name}.transport_cost': self.transport,
                       f'{self.name}.{self.model_name}.margin':  self.margin,
                       f'{self.name}.resources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.resources_price': get_static_prices(np.arange(2020, 2051))
                       }

        self.ee.load_study_from_input_dict(inputs_dict)
        self.ee.execute()
        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-18, derr_approx='complex_step', local_data=disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.invest_level',
                                    f'{self.name}.energy_prices',
                                    f'{self.name}.energy_CO2_emissions',
                                    f'{self.name}.CO2_taxes',
                                    f'{self.name}.resources_price',
                                    f'{self.name}.resources_CO2_emissions',
                                    ],
                            outputs=[f'{self.name}.{self.model_name}.techno_prices',
                                     f'{self.name}.{self.model_name}.CO2_emissions',
                                     f'{self.name}.{self.model_name}.techno_consumption',
                                     f'{self.name}.{self.model_name}.techno_consumption_woratio',
                                     f'{self.name}.{self.model_name}.techno_production',
                                     ], )
