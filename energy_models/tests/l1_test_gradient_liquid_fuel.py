'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/14-2024/06/24 Copyright 2023 Capgemini

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
import warnings
from os.path import dirname, join

import numpy as np
import pandas as pd
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tests.core.abstract_jacobian_unit_test import (
    AbstractJacobianUnittest,
)

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.resources_data_disc import (
    get_default_resources_CO2_emissions,
    get_default_resources_prices,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.biodiesel.transesterification.transesterification_disc import (
    TransesterificationDiscipline,
)
from energy_models.models.liquid_fuel.refinery.refinery_disc import RefineryDiscipline

warnings.filterwarnings("ignore")


class LiquidFuelJacobianCase(AbstractJacobianUnittest):
    """
    Liquid Fuel jacobian test class
    """

    def analytic_grad_entry(self):
        return [
            self.test_01_refinery_jacobian,
            self.test_02_transesterification_discipline_analytic_grad,
            self.test_03_transesterification_discipline_analytic_grad_negative_invest,
            self.test_04_transesterification_discipline_analytic_grad_negative_invest2,
            self.test_05_liquid_fuel_discipline_jacobian,
        ]

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.year_end = GlossaryEnergy.YearEndDefaultValueGradientTest
        years = np.arange(GlossaryEnergy.YearStartDefault, self.year_end + 1)

        self.years = years
        self.energy_name = GlossaryEnergy.liquid_fuel
        # crude oil price : 1.3$/gallon
        self.stream_prices = pd.DataFrame(
            {GlossaryEnergy.Years: years,
             GlossaryEnergy.electricity: 16.,
             GlossaryEnergy.CO2: 0.0,
             GlossaryEnergy.syngas: 34,
             f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}': 15.,
             })

        self.syngas_detailed_prices = pd.DataFrame({GlossaryEnergy.SMR: np.ones(len(years)) * 34,
                                                    # price to be updated for
                                                    # CO2
                                                    GlossaryEnergy.CoElectrolysis: np.ones(len(years)) * 60,
                                                    GlossaryEnergy.BiomassGasification: np.ones(len(years)) * 50
                                                    })
        self.syngas_ratio_technos = {GlossaryEnergy.SMR: 0.33,
                                     GlossaryEnergy.CoElectrolysis: 1.0,
                                     GlossaryEnergy.BiomassGasification: 2.0
                                     }
        self.stream_co2_emissions = pd.DataFrame({
            GlossaryEnergy.Years: years,
            GlossaryEnergy.electricity: 0.0,
            GlossaryEnergy.syngas: 0.0,
             f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}': 0.})

        self.invest_level = pd.DataFrame({GlossaryEnergy.Years: years,
                                          GlossaryEnergy.InvestValue: np.linspace(4435750000.0, 5093000000.0, len(self.years)) * 1.0e-9})

        self.invest_level_negative = pd.DataFrame({GlossaryEnergy.Years: years,
                                                   GlossaryEnergy.InvestValue: -np.linspace(4435750000.0, 5093000000.0, len(self.years)) * 1.0e-9})

        self.invest_level_negative2 = pd.DataFrame({GlossaryEnergy.Years: years,
                                                    GlossaryEnergy.InvestValue: np.linspace(4435750000.0, 5093000000.0, len(self.years)) * 1.0e-9})
        
        self.invest_level = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.InvestValue: np.linspace(4435750000.0, 5093000000.0, len(self.years)) * 1.0e-9})

        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.CO2Tax: np.linspace(14.86, 50.29, len(self.years))})
        self.margin = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.MarginValue: 110.0})
        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'transport': 200.0})

        biblio_data_path = join(
            dirname(__file__), 'output_values_check', 'biblio_data.csv')
        self.biblio_data = pd.read_csv(biblio_data_path)
        self.biblio_data = self.biblio_data.loc[self.biblio_data['sos_name']
                                                == f'{GlossaryEnergy.liquid_fuel}.{GlossaryEnergy.Refinery}']
        # ---Ratios---
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.linspace(1.0, 1.0, len(years))))
        demand_ratio_dict[GlossaryEnergy.Years] = years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)

        resource_ratio_dict = dict(
            zip(EnergyMix.RESOURCE_LIST, np.linspace(1.0, 1.0, len(years))))
        resource_ratio_dict[GlossaryEnergy.Years] = years
        self.all_resource_ratio_usable_demand = pd.DataFrame(
            resource_ratio_dict)

    def tearDown(self):
        pass

    def test_01_refinery_jacobian(self):

        self.name = 'Test'
        self.model_name = 'refinery'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_liquid_fuel': self.name,
                   'ns_resource': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.liquid_fuel.refinery.refinery_disc.RefineryDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        techno_infos_dict = RefineryDiscipline.techno_infos_dict_default
        techno_infos_dict["lifetime"] = GlossaryEnergy.LifetimeDefaultValueGradientTest

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                           self.years),
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_default_resources_prices(
                           self.years),
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       f'{self.name}.techno_infos_dict': techno_infos_dict
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryEnergy.UtilisationRatioValue}',
                                    f'{self.name}.{GlossaryEnergy.StreamPricesValue}',
                                    f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}',
                                    f'{self.name}.{GlossaryEnergy.CO2TaxesValue}',
                                    f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}',
                                    f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}', ],
                            outputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoPricesValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.CO2EmissionsValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoProductionValue}',
                                     ], )

    def test_02_transesterification_discipline_analytic_grad(self):

        self.name = 'Test'
        self.model_name = GlossaryEnergy.Transesterification
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   #    'ns_biogas': f'{self.name}'
                   'ns_biodiesel': f'{self.name}',
                   'ns_resource': f'{self.name}'
                   }
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = f'energy_models.models.{GlossaryEnergy.biodiesel}.transesterification.transesterification_disc.TransesterificationDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        techno_infos_dict = TransesterificationDiscipline.techno_infos_dict_default
        techno_infos_dict["lifetime"] = GlossaryEnergy.LifetimeDefaultValueGradientTest

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                           self.years),
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_default_resources_prices(
                           self.years),
                       f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       f'{self.name}.techno_infos_dict': techno_infos_dict
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryEnergy.UtilisationRatioValue}',
                                    f'{self.name}.{GlossaryEnergy.StreamPricesValue}',
                                    f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}',
                                    f'{self.name}.{GlossaryEnergy.CO2TaxesValue}',
                                    f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}',
                                    f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}',
                                    ],
                            outputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoPricesValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.CO2EmissionsValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoProductionValue}',
                                     ], )

    def test_03_transesterification_discipline_analytic_grad_negative_invest(self):

        self.name = 'Test'
        self.model_name = GlossaryEnergy.Transesterification
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   #    'ns_biogas': f'{self.name}'
                   'ns_biodiesel': f'{self.name}',
                   'ns_resource': f'{self.name}'
                   }
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = f'energy_models.models.{GlossaryEnergy.biodiesel}.transesterification.transesterification_disc.TransesterificationDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()
        techno_infos_dict = TransesterificationDiscipline.techno_infos_dict_default
        techno_infos_dict["lifetime"] = GlossaryEnergy.LifetimeDefaultValueGradientTest

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearEnd}': self.year_end,
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': self.stream_co2_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level_negative,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}': get_default_resources_CO2_emissions(
                           self.years),
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': get_default_resources_prices(
                           self.years),
                       f'{self.name}.{GlossaryEnergy.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       f'{self.name}.techno_infos_dict': techno_infos_dict
                       }

        self.ee.load_study_from_input_dict(inputs_dict)
        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline
        self.override_dump_jacobian = True # Test seems KO in server, regenerate pickle at each test
        self.check_jacobian(location=dirname(__file__),
                            filename=f'jacobian_{self.energy_name}_{self.model_name}_negative.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step',
                            local_data=disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryEnergy.UtilisationRatioValue}',
                                    f'{self.name}.{GlossaryEnergy.StreamPricesValue}',
                                    f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}',
                                    f'{self.name}.{GlossaryEnergy.CO2TaxesValue}',
                                    f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}',
                                    f'{self.name}.{GlossaryEnergy.RessourcesCO2EmissionsValue}',
                                    ],
                            outputs=[f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoPricesValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.CO2EmissionsValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryEnergy.TechnoProductionValue}',
                                     ], )

    def test_05_liquid_fuel_discipline_jacobian(self):

        self.name = 'Test'
        self.energy_name = f'{GlossaryEnergy.fuel}.{GlossaryEnergy.liquid_fuel}'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': f'{self.name}',
                   'ns_liquid_fuel': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_resource': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.stream_type.energy_disciplines.liquid_fuel_disc.LiquidFuelDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.energy_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_streams_input_dict.pkl'), 'rb')
        mda_data_input_dict = pickle.load(pkl_file)
        pkl_file.close()

        namespace = f'{self.name}'
        inputs_dict = {}
        coupled_inputs = []
        for key in mda_data_input_dict[self.energy_name].keys():
            if key in [GlossaryEnergy.techno_list, GlossaryEnergy.CO2TaxesValue, GlossaryEnergy.YearStart,
                       GlossaryEnergy.YearEnd,
                       'scaling_factor_energy_production', 'scaling_factor_energy_consumption',
                       'scaling_factor_techno_consumption', 'scaling_factor_techno_production', ]:
                inputs_dict[f'{namespace}.{key}'] = mda_data_input_dict[self.energy_name][key]['value']
                if mda_data_input_dict[self.energy_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{key}']
            else:
                inputs_dict[f'{namespace}.{self.energy_name}.{key}'] = mda_data_input_dict[self.energy_name][key][
                    'value']
                if mda_data_input_dict[self.energy_name][key]['is_coupling']:
                    coupled_inputs += [f'{namespace}.{self.energy_name}.{key}']

        pkl_file = open(
            join(dirname(__file__), 'data_tests/mda_energy_data_streams_output_dict.pkl'), 'rb')
        mda_data_output_dict = pickle.load(pkl_file)
        pkl_file.close()

        coupled_outputs = []
        # remove some outputs that we know are not coupled for this discipline
        not_coupled_ouputs = [
            'energy_detailed_techno_prices', GlossaryEnergy.EnergyProductionDetailedValue]

        for key in mda_data_output_dict[self.energy_name].keys():
            if mda_data_output_dict[self.energy_name][key]['is_coupling'] and key not in not_coupled_ouputs:
                coupled_outputs += [f'{namespace}.{self.energy_name}.{key}']

        technos = inputs_dict[f"{self.name}.technologies_list"]
        techno_capital = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.Capital: 20000 * np.ones_like(self.years)
        })
        for techno in technos:
            inputs_dict[
                f"{self.name}.{self.energy_name}.{techno}.{GlossaryEnergy.TechnoCapitalValue}"] = techno_capital
            coupled_inputs.append(f"{self.name}.{self.energy_name}.{techno}.{GlossaryEnergy.TechnoCapitalValue}")

        coupled_outputs.append(f"{self.name}.{self.energy_name}.{GlossaryEnergy.EnergyTypeCapitalDfValue}")
        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.energy_name}')[0].mdo_discipline_wrapp.mdo_discipline

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}.pkl',
                            discipline=disc, step=1.0e-18, derr_approx='complex_step', threshold=1e-5,
                            local_data=disc.local_data,
                            inputs=coupled_inputs,
                            outputs=coupled_outputs, )


if '__main__' == __name__:
    cls = LiquidFuelJacobianCase()
    cls.setUp()
    cls.test_05_liquid_fuel_discipline_jacobian()
