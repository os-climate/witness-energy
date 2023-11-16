'''
Copyright 2022 Airbus SAS
Modifications on 2023/10/23-2023/11/09 Copyright 2023 Capgemini

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
from climateeconomics.glossarycore import GlossaryCore
from energy_models.glossaryenergy import GlossaryEnergy
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
from energy_models.core.stream_type.energy_models.biogas import BioGas
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary


class BiogasJacobianTestCase(AbstractJacobianUnittest):
    """
    Anaerobic Digestion prices test class
    """

    #AbstractJacobianUnittest.DUMP_JACOBIAN = True

    def analytic_grad_entry(self):
        return [
            self.test_01_biomass_gas_discipline_analytic_grad,
        ]

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.energy_name = 'biogas'
        years = np.arange(2020, 2051)
        
        self.resource_list = [
            'oil_resource', 'natural_gas_resource', 'uranium_resource', 'coal_resource']
        self.ratio_available_resource = pd.DataFrame(
            {GlossaryCore.Years: np.arange(2020, 2050 + 1)})
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
        self.energy_prices = pd.DataFrame({GlossaryCore.Years: years, 'electricity': electricity_price
                                           })
        self.resources_prices = pd.DataFrame({GlossaryCore.Years: years, ResourceGlossary.WetBiomass['name']: electricity_price / 100.0
                                              })

        self.energy_carbon_emissions = pd.DataFrame(
            {GlossaryCore.Years: years, 'electricity': 0.0})

        self.invest_level = pd.DataFrame(
            {GlossaryCore.Years: years, GlossaryCore.InvestValue: np.array([4435750000.0, 4522000000.0, 4608250000.0,
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
            {GlossaryCore.Years: years, GlossaryCore.CO2Tax: func(years)})
        self.margin = pd.DataFrame(
            {GlossaryCore.Years: years, GlossaryCore.MarginValue: np.ones(len(years)) * 110.0})
        # From future of hydrogen
        self.transport = pd.DataFrame(
            {GlossaryCore.Years: years, 'transport': np.ones(len(years)) * 0.0})
        self.scaling_factor_techno_consumption = 1e3
        self.scaling_factor_techno_production = 1e3
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.ones((len(years), len(years)))))
        demand_ratio_dict[GlossaryCore.Years] = years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)
        self.is_stream_demand = True
        self.is_apply_resource_ratio = True

    def tearDown(self):
        pass

    def test_01_biomass_gas_discipline_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'AnaerobicDigestion'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_biogas': f'{self.name}',
                   'ns_resource': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.biogas.anaerobic_digestion.anaerobic_digestion_disc.AnaerobicDigestionDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryCore.YearEnd}': 2050,
                       f'{self.name}.{GlossaryCore.EnergyPricesValue}': self.energy_prices,
                       f'{self.name}.{GlossaryCore.EnergyCO2EmissionsValue}': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryCore.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{GlossaryCore.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryCore.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryCore.TransportCostValue}': self.transport,
                       f'{self.name}.{self.model_name}.{GlossaryCore.MarginValue}':  self.margin,
                       f'{self.name}.{GlossaryCore.RessourcesCO2EmissionsValue}': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.{GlossaryCore.ResourcesPriceValue}': get_static_prices(np.arange(2020, 2051))
                       }

        self.ee.load_study_from_input_dict(inputs_dict)
        self.ee.execute()
        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-18, derr_approx='complex_step', local_data=disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryCore.InvestLevelValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryCore.UtilisationRatioValue}',
                                    f'{self.name}.{GlossaryCore.EnergyPricesValue}',
                                    f'{self.name}.{GlossaryCore.EnergyCO2EmissionsValue}',
                                    f'{self.name}.{GlossaryCore.CO2TaxesValue}',
                                    f'{self.name}.{GlossaryCore.ResourcesPriceValue}',
                                    f'{self.name}.{GlossaryCore.RessourcesCO2EmissionsValue}',
                                    ],
                            outputs=[f'{self.name}.{self.model_name}.{GlossaryCore.TechnoPricesValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.CO2EmissionsValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.TechnoConsumptionValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.TechnoConsumptionWithoutRatioValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.TechnoProductionValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoCapitalValue}',
                                     ], )
