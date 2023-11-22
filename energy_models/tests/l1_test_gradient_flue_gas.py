'''
Copyright 2022 Airbus SAS
Modifications on 2023/08/23-2023/11/16 Copyright 2023 Capgemini

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
import scipy.interpolate as sc

from climateeconomics.glossarycore import GlossaryCore
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.resources_data_disc import get_static_CO2_emissions, \
    get_static_prices
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tests.core.abstract_jacobian_unit_test import AbstractJacobianUnittest


class GradientFlueGasTestCase(AbstractJacobianUnittest):
    """
    Flue gas gradients test class
    """
    #AbstractJacobianUnittest.DUMP_JACOBIAN = True

    def analytic_grad_entry(self):
        return [
            self.test_01_calcium_looping_discipline_analytic_grad,
            self.test_02_pressure_swing_adsorption_analytic_grad,
            self.test_03_piperazine_process_analytic_grad,
            self.test_04_monoethanolamine_analytic_grad,
            self.test_05_co2_membranes_analytic_grad,
            self.test_06_chilled_ammonia_process_discipline_analytic_grad,
        ]

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        years = np.arange(2020, 2051)

        self.energy_name = 'flue_gas'

        
        self.flue_gas_mean = pd.DataFrame(
            {GlossaryCore.Years: years, GlossaryCore.FlueGasMean: 0.3})

        self.flue_gas_mean_swing = pd.DataFrame(
            {GlossaryCore.Years: years, GlossaryCore.FlueGasMean: 0.1})

        self.flue_gas_mean_piperazine = pd.DataFrame(
            {GlossaryCore.Years: years, GlossaryCore.FlueGasMean: 0.2})

        self.energy_prices = pd.DataFrame(
            {GlossaryCore.Years: years, 'electricity': np.ones(len(np.arange(2020, 2051))) * 80.0, 'methane':np.ones(len(np.arange(2020, 2051))) * 80.0})

        self.invest_level = pd.DataFrame(
            {GlossaryCore.Years: years, GlossaryCore.InvestValue: np.array([22000.00, 22000.00, 22000.00, 22000.00,
                                                 22000.00, 22000.00, 22000.00, 22000.00,
                                                 22000.00, 22000.00, 31000.00, 31000.00,
                                                 31000.00, 31000.00, 31000.00, 31000.00,
                                                 31000.00, 31000.00, 31000.00, 31000.00,
                                                 31000.00, 31000.00, 31000.00, 31000.00,
                                                 31000.00, 31000.00, 31000.00, 31000.00,
                                                 31000.00, 31000.00, 31000.00]) * 1e-3})

        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [14.86, 17.22, 20.27,
                     29.01,  34.05,   39.08,  44.69,   50.29]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')
        self.co2_taxes = pd.DataFrame(
            {GlossaryCore.Years: years, GlossaryCore.CO2Tax: func(years)})

        self.margin = pd.DataFrame(
            {GlossaryCore.Years: np.arange(2020, 2051), GlossaryCore.MarginValue: np.ones(len(np.arange(2020, 2051))) * 100})

        self.energy_carbon_emissions = pd.DataFrame(
            {GlossaryCore.Years: years, 'electricity': 0.0, 'methane': 0.2})

        transport_cost = 0,

        self.transport = pd.DataFrame(
            {GlossaryCore.Years: years, 'transport': np.ones(len(years)) * transport_cost})

        self.resources_price = pd.DataFrame({GlossaryCore.Years: years})
        #---Ratios---
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.linspace(1.0, 1.0, len(years))))
        demand_ratio_dict[GlossaryCore.Years] = years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)

        resource_ratio_dict = dict(
            zip(EnergyMix.RESOURCE_LIST, np.linspace(1.0, 1.0, len(years))))
        resource_ratio_dict[GlossaryCore.Years] = years
        self.all_resource_ratio_usable_demand = pd.DataFrame(
            resource_ratio_dict)

    def tearDown(self):
        pass

    def test_01_calcium_looping_discipline_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'CalciumLooping'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name,
                   'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_flue_gas': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_carbon_capture': self.name,
                   'ns_resource': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.carbon_capture.flue_gas_capture.calcium_looping.calcium_looping_disc.CalciumLoopingDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryCore.YearEnd}': 2050,
                       f'{self.name}.{GlossaryCore.RessourcesCO2EmissionsValue}': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.{GlossaryCore.EnergyPricesValue}': self.energy_prices,
                       f'{self.name}.{GlossaryCore.FlueGasMean}': self.flue_gas_mean,
                       f'{self.name}.{GlossaryCore.EnergyCO2EmissionsValue}': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryCore.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{GlossaryCore.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryCore.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryCore.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryCore.ResourcesPriceValue}': self.resources_price,
                       
                       f'{self.name}.{self.model_name}.{GlossaryCore.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryCore.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)
        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,local_data = disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryCore.InvestLevelValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryCore.UtilisationRatioValue}',
                                    f'{self.name}.{GlossaryCore.FlueGasMean}',
                                    f'{self.name}.{GlossaryCore.EnergyPricesValue}',
                                    f'{self.name}.{GlossaryCore.EnergyCO2EmissionsValue}',
                                    f'{self.name}.{GlossaryCore.CO2TaxesValue}'],
                            outputs=[f'{self.name}.{self.model_name}.{GlossaryCore.TechnoPricesValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.CO2EmissionsValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.TechnoConsumptionValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.TechnoConsumptionWithoutRatioValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.TechnoProductionValue}',
                                     ],)

    def test_02_pressure_swing_adsorption_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'pressure_swing_adsorption'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name,
                   'ns_energy': self.name,
                   'ns_flue_gas': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_carbon_capture': self.name,
                   'ns_resource': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.carbon_capture.flue_gas_capture.pressure_swing_adsorption.pressure_swing_adsorption_disc' \
                   '.PressureSwingAdsorptionDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryCore.YearEnd}': 2050,
                       f'{self.name}.{GlossaryCore.RessourcesCO2EmissionsValue}': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.{GlossaryCore.ResourcesPriceValue}': get_static_prices(np.arange(2020, 2051)),
                       f'{self.name}.{GlossaryCore.EnergyPricesValue}': self.energy_prices,
                       f'{self.name}.{GlossaryCore.FlueGasMean}': self.flue_gas_mean_swing,
                       f'{self.name}.{GlossaryCore.EnergyCO2EmissionsValue}': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryCore.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{GlossaryCore.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryCore.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryCore.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryCore.ResourcesPriceValue}': self.resources_price,
                       f'{self.name}.{self.model_name}.{GlossaryCore.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryCore.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,local_data = disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryCore.InvestLevelValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryCore.UtilisationRatioValue}',
                                    f'{self.name}.{GlossaryCore.EnergyPricesValue}',
                                    f'{self.name}.{GlossaryCore.FlueGasMean}',
                                    f'{self.name}.{GlossaryCore.EnergyCO2EmissionsValue}',
                                    f'{self.name}.{GlossaryCore.CO2TaxesValue}'],
                            outputs=[f'{self.name}.{self.model_name}.{GlossaryCore.TechnoPricesValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.CO2EmissionsValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.TechnoConsumptionValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.TechnoConsumptionWithoutRatioValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.TechnoProductionValue}',
                                     ],)

    def test_03_piperazine_process_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'piperazine_process'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name,
                   'ns_energy': self.name,
                   'ns_flue_gas': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_carbon_capture': self.name,
                   'ns_resource': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.carbon_capture.flue_gas_capture.piperazine_process' \
                   '.piperazine_process_disc.PiperazineProcessDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryCore.YearEnd}': 2050,
                       f'{self.name}.{GlossaryCore.RessourcesCO2EmissionsValue}': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.{GlossaryCore.ResourcesPriceValue}': get_static_prices(np.arange(2020, 2051)),
                       f'{self.name}.{GlossaryCore.EnergyPricesValue}': self.energy_prices,
                       f'{self.name}.{GlossaryCore.FlueGasMean}': self.flue_gas_mean_piperazine,
                       f'{self.name}.{GlossaryCore.EnergyCO2EmissionsValue}': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryCore.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{GlossaryCore.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryCore.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryCore.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryCore.ResourcesPriceValue}': self.resources_price,
                       f'{self.name}.{self.model_name}.{GlossaryCore.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryCore.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)
        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,local_data = disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryCore.InvestLevelValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryCore.UtilisationRatioValue}',
                                    f'{self.name}.{GlossaryCore.EnergyPricesValue}',
                                    f'{self.name}.{GlossaryCore.FlueGasMean}',
                                    f'{self.name}.{GlossaryCore.EnergyCO2EmissionsValue}',
                                    f'{self.name}.{GlossaryCore.CO2TaxesValue}'],
                            outputs=[f'{self.name}.{self.model_name}.{GlossaryCore.TechnoPricesValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.CO2EmissionsValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.TechnoConsumptionValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.TechnoConsumptionWithoutRatioValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.TechnoProductionValue}',
                                     ],)

    def test_04_monoethanolamine_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'mono_ethanol_amine'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name,
                   'ns_energy': self.name,
                   'ns_flue_gas': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_carbon_capture': self.name,
                   'ns_resource': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.carbon_capture.flue_gas_capture.mono_ethanol_amine.mono_ethanol_amine_disc.MonoEthanolAmineDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryCore.YearEnd}': 2050,
                       f'{self.name}.{GlossaryCore.RessourcesCO2EmissionsValue}': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.{GlossaryCore.ResourcesPriceValue}': get_static_prices(np.arange(2020, 2051)),
                       f'{self.name}.{GlossaryCore.EnergyPricesValue}': self.energy_prices,
                       f'{self.name}.{GlossaryCore.FlueGasMean}': self.flue_gas_mean_piperazine,
                       f'{self.name}.{GlossaryCore.EnergyCO2EmissionsValue}': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryCore.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{GlossaryCore.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryCore.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryCore.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryCore.ResourcesPriceValue}': self.resources_price,
                       f'{self.name}.{self.model_name}.{GlossaryCore.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryCore.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)
        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,local_data = disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryCore.InvestLevelValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryCore.UtilisationRatioValue}',
                                    f'{self.name}.{GlossaryCore.EnergyPricesValue}',
                                    f'{self.name}.{GlossaryCore.FlueGasMean}',
                                    f'{self.name}.{GlossaryCore.EnergyCO2EmissionsValue}',
                                    f'{self.name}.{GlossaryCore.CO2TaxesValue}'],
                            outputs=[f'{self.name}.{self.model_name}.{GlossaryCore.TechnoPricesValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.CO2EmissionsValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.TechnoConsumptionValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.TechnoConsumptionWithoutRatioValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.TechnoProductionValue}',
                                     ],)

    def test_05_co2_membranes_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'CO2_membranes'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name,
                   'ns_energy': self.name,
                   'ns_flue_gas': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_carbon_capture': self.name,
                   'ns_resource': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.carbon_capture.flue_gas_capture.co2_membranes' \
                   '.co2_membranes_disc.CO2MembranesDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryCore.YearEnd}': 2050,
                       f'{self.name}.{GlossaryCore.RessourcesCO2EmissionsValue}': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.{GlossaryCore.ResourcesPriceValue}': get_static_prices(np.arange(2020, 2051)),
                       f'{self.name}.{GlossaryCore.EnergyPricesValue}': self.energy_prices,
                       f'{self.name}.{GlossaryCore.FlueGasMean}': self.flue_gas_mean_piperazine,
                       f'{self.name}.{GlossaryCore.EnergyCO2EmissionsValue}': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryCore.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{GlossaryCore.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryCore.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryCore.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryCore.ResourcesPriceValue}': self.resources_price,
                       f'{self.name}.{self.model_name}.{GlossaryCore.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryCore.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,local_data = disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryCore.InvestLevelValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryCore.UtilisationRatioValue}',
                                    f'{self.name}.{GlossaryCore.FlueGasMean}',
                                    f'{self.name}.{GlossaryCore.EnergyPricesValue}',
                                    f'{self.name}.{GlossaryCore.EnergyCO2EmissionsValue}',
                                    f'{self.name}.{GlossaryCore.CO2TaxesValue}'],
                            outputs=[f'{self.name}.{self.model_name}.{GlossaryCore.TechnoPricesValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.CO2EmissionsValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.TechnoConsumptionValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.TechnoConsumptionWithoutRatioValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.TechnoProductionValue}',
                                     ],)

    def test_06_chilled_ammonia_process_discipline_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'chilled_ammonia_process'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name,
                   'ns_energy': self.name,
                   'ns_flue_gas': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_carbon_capture': self.name,
                   'ns_resource': f'{self.name}'}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.carbon_capture.flue_gas_capture.chilled_ammonia_process' \
                   '.chilled_ammonia_process_disc.ChilledAmmoniaProcessDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryCore.YearEnd}': 2050,
                       f'{self.name}.{GlossaryCore.RessourcesCO2EmissionsValue}': get_static_CO2_emissions(np.arange(2020, 2051)),
                       f'{self.name}.{GlossaryCore.ResourcesPriceValue}': get_static_prices(np.arange(2020, 2051)),
                       f'{self.name}.{GlossaryCore.EnergyPricesValue}': self.energy_prices,
                       f'{self.name}.{GlossaryCore.FlueGasMean}': self.flue_gas_mean_swing,
                       f'{self.name}.{GlossaryCore.EnergyCO2EmissionsValue}': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryCore.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{GlossaryCore.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryCore.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryCore.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryCore.ResourcesPriceValue}': self.resources_price,
                       f'{self.name}.{self.model_name}.{GlossaryCore.MarginValue}': self.margin,
                       f'{self.name}.{GlossaryCore.AllStreamsDemandRatioValue}': self.all_streams_demand_ratio,
                       f'{self.name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc_techno = self.ee.root_process.proxy_disciplines[0].mdo_discipline_wrapp.mdo_discipline
        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.energy_name}_{self.model_name}.pkl',
                            discipline=disc_techno, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,local_data = disc_techno.local_data,
                            inputs=[f'{self.name}.{self.model_name}.{GlossaryCore.InvestLevelValue}',
                                    f'{self.name}.{self.model_name}.{GlossaryCore.UtilisationRatioValue}',
                                    f'{self.name}.{GlossaryCore.FlueGasMean}',
                                    f'{self.name}.{GlossaryCore.EnergyPricesValue}',
                                    f'{self.name}.{GlossaryCore.EnergyCO2EmissionsValue}',
                                    f'{self.name}.{GlossaryCore.CO2TaxesValue}'],
                            outputs=[f'{self.name}.{self.model_name}.{GlossaryCore.TechnoPricesValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.CO2EmissionsValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.TechnoConsumptionValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.TechnoConsumptionWithoutRatioValue}',
                                     f'{self.name}.{self.model_name}.{GlossaryCore.TechnoProductionValue}',
                                     ],)
