'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2023/11/16 Copyright 2023 Capgemini

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

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.interpolate as sc

from climateeconomics.core.core_resources.resource_mix.resource_mix import ResourceMixModel
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.resources_data_disc import get_static_CO2_emissions
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.carbon_capture.flue_gas_capture.chilled_ammonia_process.chilled_ammonia_process \
    import ChilledAmmoniaProcess
from energy_models.models.carbon_capture.flue_gas_capture.chilled_ammonia_process.chilled_ammonia_process_disc \
    import ChilledAmmoniaProcessDiscipline
from sostrades_core.execution_engine.execution_engine import ExecutionEngine


class FGChilledAmmoniaProcessTestCase(unittest.TestCase):
    """
    ChilledAmmonia prices test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        years = np.arange(GlossaryEnergy.YeartStartDefault, 2050 + 1)
        self.resource_list = [
            'oil_resource', 'natural_gas_resource', 'uranium_resource', 'coal_resource']
        self.ratio_available_resource = pd.DataFrame(
            {GlossaryEnergy.Years: np.arange(GlossaryEnergy.YeartStartDefault, 2050 + 1)})
        for types in self.resource_list:
            self.ratio_available_resource[types] = np.linspace(
                1, 1, len(self.ratio_available_resource.index))
        self.flue_gas_mean = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.FlueGasMean: 0.3})

        self.energy_prices = pd.DataFrame(
            {GlossaryEnergy.Years: years,
             'electricity': np.ones(len(np.arange(GlossaryEnergy.YeartStartDefault, 2050 + 1))) * 80.0,
             'methane': np.ones(len(np.arange(GlossaryEnergy.YeartStartDefault, 2050 + 1))) * 80.0})

        self.invest_level = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.InvestValue: np.array([22000.00, 22000.00, 22000.00, 22000.00,
                                                                                22000.00, 22000.00, 22000.00, 22000.00,
                                                                                22000.00, 22000.00, 31000.00, 31000.00,
                                                                                31000.00, 31000.00, 31000.00, 31000.00,
                                                                                31000.00, 31000.00, 31000.00, 31000.00,
                                                                                31000.00, 31000.00, 31000.00, 31000.00,
                                                                                31000.00, 31000.00, 31000.00, 31000.00,
                                                                                31000.00, 31000.00, 31000.00]) * 1e-3})

        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [14.86, 17.22, 20.27,
                     29.01, 34.05, 39.08, 44.69, 50.29]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')
        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.CO2Tax: func(years)})

        self.margin = pd.DataFrame(
            {GlossaryEnergy.Years: np.arange(GlossaryEnergy.YeartStartDefault, 2050 + 1),
             GlossaryEnergy.MarginValue: np.ones(len(np.arange(GlossaryEnergy.YeartStartDefault, 2050 + 1))) * 100})

        self.energy_carbon_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'electricity': 0.0})

        transport_cost = 0,

        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'transport': np.ones(len(years)) * transport_cost})

        self.resources_price = pd.DataFrame({GlossaryEnergy.Years: years})
        self.scaling_factor_techno_consumption = 1e3
        self.scaling_factor_techno_production = 1e3
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.ones((len(years), len(years)))))
        demand_ratio_dict[GlossaryEnergy.Years] = years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)
        self.is_stream_demand = True
        self.is_apply_resource_ratio = True

    def tearDown(self):
        pass

    def test_01_compute_chilled_ammonia_process_price(self):
        years = np.arange(GlossaryEnergy.YeartStartDefault, 2050 + 1)
        utilisation_ratio = pd.DataFrame({
            GlossaryEnergy.Years: years,
            GlossaryEnergy.UtilisationRatioValue: np.ones_like(years) * 100.
        })

        inputs_dict = {GlossaryEnergy.YearStart: GlossaryEnergy.YeartStartDefault,
                       GlossaryEnergy.YearEnd: 2050,
                       GlossaryEnergy.UtilisationRatioValue: utilisation_ratio,
                       'techno_infos_dict': ChilledAmmoniaProcessDiscipline.techno_infos_dict_default,
                       GlossaryEnergy.InvestLevelValue: self.invest_level,
                       GlossaryEnergy.InvestmentBeforeYearStartValue: ChilledAmmoniaProcessDiscipline.invest_before_year_start,
                       GlossaryEnergy.MarginValue: self.margin,
                       GlossaryEnergy.TransportCostValue: self.transport,
                       GlossaryEnergy.ResourcesPriceValue: self.resources_price,
                       GlossaryEnergy.EnergyCO2EmissionsValue: self.energy_carbon_emissions,
                       GlossaryEnergy.RessourcesCO2EmissionsValue: get_static_CO2_emissions(
                           np.arange(GlossaryEnergy.YeartStartDefault, 2050 + 1)),
                       GlossaryEnergy.EnergyPricesValue: self.energy_prices,
                       GlossaryEnergy.FlueGasMean: self.flue_gas_mean,
                       GlossaryEnergy.CO2TaxesValue: self.co2_taxes,
                       GlossaryEnergy.TransportMarginValue: self.margin,
                       'initial_production': ChilledAmmoniaProcessDiscipline.initial_capture,
                       'initial_age_distrib': ChilledAmmoniaProcessDiscipline.initial_age_distribution,
                       'scaling_factor_invest_level': 1e3,
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production,
                       ResourceMixModel.RATIO_USABLE_DEMAND: self.ratio_available_resource,
                       GlossaryEnergy.AllStreamsDemandRatioValue: self.all_streams_demand_ratio,
                       'is_stream_demand': self.is_stream_demand,
                       'is_apply_resource_ratio': self.is_apply_resource_ratio,
                       'smooth_type': 'smooth_max',
                       'data_fuel_dict': CarbonCapture.data_energy_dict}

        cap_model = ChilledAmmoniaProcess(
            'Flue_gas_capture.ChilledAmmoniaProcess')
        cap_model.configure_parameters(inputs_dict)
        cap_model.configure_parameters_update(inputs_dict)
        price_details = cap_model.compute_price()

        # Comparison in $/kWH
        plt.figure()
        plt.xlabel(GlossaryEnergy.Years)

        plt.plot(price_details[GlossaryEnergy.Years],
                 price_details['Flue_gas_capture.ChilledAmmoniaProcess'], label='SoSTrades Total')

        plt.plot(price_details[GlossaryEnergy.Years], price_details['transport'],
                 label='SoSTrades Transport')

        plt.plot(price_details[GlossaryEnergy.Years], price_details['Flue_gas_capture.ChilledAmmoniaProcess_factory'],
                 label='SoSTrades Factory')
        plt.legend()
        plt.ylabel('Price ($/kWh)')

    def test_03_chilled_ammonia_process_discipline(self):
        self.name = 'Test'
        self.model_name = 'Flue_gas_capture.ChilledAmmoniaProcess'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name,
                   'ns_energy': self.name,
                   'ns_flue_gas': f'{self.name}',
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_carbon_capture': self.name,
                   'ns_resource': self.name}

        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.carbon_capture.flue_gas_capture.chilled_ammonia_process' \
                   '.chilled_ammonia_process_disc.ChilledAmmoniaProcessDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearEnd}': 2050,
                       f'{self.name}.{GlossaryEnergy.EnergyPricesValue}': self.energy_prices,
                       f'{self.name}.{GlossaryEnergy.FlueGasMean}': self.flue_gas_mean,
                       f'{self.name}.{GlossaryEnergy.EnergyCO2EmissionsValue}': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': self.resources_price,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)
        # for graph in graph_list:
        #     graph.to_plotly().show()
