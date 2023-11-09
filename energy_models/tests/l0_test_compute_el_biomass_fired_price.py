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
import pandas as pd
import numpy as np
from os.path import join, dirname

import scipy.interpolate as sc
import matplotlib.pyplot as plt

from climateeconomics.glossarycore import GlossaryCore
from energy_models.models.electricity.biomass_fired.biomass_fired_disc import BiomassFiredDiscipline
from energy_models.models.electricity.biomass_fired.biomass_fired import BiomassFired
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from energy_models.core.stream_type.resources_data_disc import get_static_CO2_emissions
from climateeconomics.core.core_resources.resource_mix.resource_mix import ResourceMixModel
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.energy_models.electricity import Electricity


class GasTurbinePriceTestCase(unittest.TestCase):
    """
    GT prices test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        years = np.arange(2020, 2051)
        self.resource_list = [
            'oil_resource', 'natural_gas_resource', 'uranium_resource', 'coal_resource']
        self.ratio_available_resource = pd.DataFrame(
            {GlossaryCore.Years: np.arange(2020, 2050 + 1)})
        for types in self.resource_list:
            self.ratio_available_resource[types] = np.linspace(
                1, 1, len(self.ratio_available_resource.index))
        self.energy_prices = pd.DataFrame(
            {GlossaryCore.Years: years, 'biomass_dry': np.ones(len(years)) * 11.0})
        # From CO2 prod of methane fossil
        self.energy_carbon_emissions = pd.DataFrame(
            {GlossaryCore.Years: years, 'methane': 0.123 / 15.4, 'biomass_dry': - 0.64 / 4.86})
        #  IEA invest data NPS Scenario 22bn to 2030 and 31bn after 2030

        self.invest_level_2 = pd.DataFrame(
            {GlossaryCore.Years: years, GlossaryCore.InvestValue: np.ones(len(years)) * 21.0})

        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
#         co2_taxes = [0.01486, 0.01722, 0.02027,
#                      0.02901,  0.03405,   0.03908,  0.04469,   0.05029]
        co2_taxes = [0, 0, 0, 0,  0,   0,  0,   0]

        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {GlossaryCore.Years: years, GlossaryCore.CO2Tax: func(years)})
        self.margin = pd.DataFrame(
            {GlossaryCore.Years: years, GlossaryCore.MarginValue: np.ones(len(years)) * 110.0})

        transport_cost = 11
        # It is noteworthy that the cost of transmission has generally been held (and can
        # continue to be held)    within the �10-12/MWhr range despite transmission distances
        # increasing by almost an order of magnitude from an average of 20km for the
        # leftmost bar to 170km for the 2020 scenarios / OWPB 2016

        self.transport = pd.DataFrame(
            {GlossaryCore.Years: years, 'transport': np.ones(len(years)) * transport_cost})
        self.resources_price = pd.DataFrame({GlossaryCore.Years: years})

        biblio_data_path = join(
            dirname(__file__), 'output_values_check', 'biblio_data.csv')
        self.biblio_data = pd.read_csv(biblio_data_path)
        self.biblio_data = self.biblio_data.loc[self.biblio_data['sos_name']
                                                == 'electricity.BiomassFired']
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

    def test_01_compute_gas_turbine_price(self):

        inputs_dict = {GlossaryCore.YearStart: 2020,
                       GlossaryCore.YearEnd: 2050,
                       'techno_infos_dict': BiomassFiredDiscipline.techno_infos_dict_default,
                       GlossaryCore.InvestLevelValue: self.invest_level_2,
                       GlossaryCore.InvestmentBeforeYearStartValue: BiomassFiredDiscipline.invest_before_year_start,
                       GlossaryCore.CO2TaxesValue: self.co2_taxes,
                       GlossaryCore.MarginValue:  self.margin,
                       GlossaryCore.TransportCostValue: self.transport,
                       GlossaryCore.TransportMarginValue: self.margin,
                       GlossaryCore.ResourcesPriceValue: self.resources_price,
                       GlossaryCore.EnergyPricesValue: self.energy_prices,
                       'initial_production': BiomassFiredDiscipline.initial_production,
                       'initial_age_distrib': BiomassFiredDiscipline.initial_age_distribution,
                       GlossaryCore.EnergyCO2EmissionsValue: self.energy_carbon_emissions,
                       GlossaryCore.RessourcesCO2EmissionsValue: get_static_CO2_emissions(np.arange(2020, 2051)),
                       'scaling_factor_invest_level': 1e3,
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production,
                       ResourceMixModel.RATIO_USABLE_DEMAND: self.ratio_available_resource,
                       GlossaryCore.AllStreamsDemandRatioValue: self.all_streams_demand_ratio,
                       'is_stream_demand': self.is_stream_demand,
                       'is_apply_resource_ratio': self.is_apply_resource_ratio,
                       'smooth_type': 'smooth_max',
                       'data_fuel_dict': Electricity.data_energy_dict,
                       }

        bf_model = BiomassFired('BiomassFired')
        bf_model.configure_parameters(inputs_dict)
        bf_model.configure_parameters_update(inputs_dict)
        price_details = bf_model.compute_price()

        # Comparison in $/kWH
        plt.figure()
        plt.xlabel(GlossaryCore.Years)

        plt.plot(price_details[GlossaryCore.Years],
                 price_details['BiomassFired'], label='SoSTrades Total')

        plt.plot(price_details[GlossaryCore.Years], price_details['transport'],
                 label='SoSTrades Transport')

        plt.plot(price_details[GlossaryCore.Years], price_details['BiomassFired_factory'],
                 label='SoSTrades Factory')
        plt.legend()
        plt.ylabel('Price ($/kWh)')

    def test_02_compute_gasturbine_price_prod_consumption(self):

        inputs_dict = {GlossaryCore.YearStart: 2020,
                       GlossaryCore.YearEnd: 2050,
                       'techno_infos_dict': BiomassFiredDiscipline.techno_infos_dict_default,
                       GlossaryCore.EnergyPricesValue: self.energy_prices,
                       GlossaryCore.InvestLevelValue: self.invest_level_2,
                       GlossaryCore.InvestmentBeforeYearStartValue: BiomassFiredDiscipline.invest_before_year_start,
                       GlossaryCore.CO2TaxesValue: self.co2_taxes,
                       GlossaryCore.MarginValue:  self.margin,
                       GlossaryCore.TransportCostValue: self.transport,
                       GlossaryCore.ResourcesPriceValue: self.resources_price,
                       GlossaryCore.TransportMarginValue: self.margin,
                       'initial_production': BiomassFiredDiscipline.initial_production,
                       'initial_age_distrib': BiomassFiredDiscipline.initial_age_distribution,
                       GlossaryCore.EnergyCO2EmissionsValue: self.energy_carbon_emissions,
                       GlossaryCore.RessourcesCO2EmissionsValue: get_static_CO2_emissions(np.arange(2020, 2051)),
                       'scaling_factor_invest_level': 1e3,
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production,
                       ResourceMixModel.RATIO_USABLE_DEMAND: self.ratio_available_resource,
                       GlossaryCore.AllStreamsDemandRatioValue: self.all_streams_demand_ratio,
                       'is_stream_demand': self.is_stream_demand,
                       'is_apply_resource_ratio': self.is_apply_resource_ratio,
                       'smooth_type': 'smooth_max',
                       'data_fuel_dict': Electricity.data_energy_dict,
                       }

        bf_model = BiomassFired('BiomassFired')
        bf_model.configure_parameters(inputs_dict)
        bf_model.configure_parameters_update(inputs_dict)
        price_details = bf_model.compute_price()
        # print(price_details)
        bf_model.compute_consumption_and_production()
        bf_model.check_outputs_dict(self.biblio_data)
        # print(production)
        # print(consumption)

    def test_04_compute_gasturbine_power(self):

        inputs_dict = {GlossaryCore.YearStart: 2020,
                       GlossaryCore.YearEnd: 2050,
                       'techno_infos_dict': BiomassFiredDiscipline.techno_infos_dict_default,
                       GlossaryCore.EnergyPricesValue: self.energy_prices,
                       GlossaryCore.InvestLevelValue: self.invest_level_2,
                       GlossaryCore.InvestmentBeforeYearStartValue: BiomassFiredDiscipline.invest_before_year_start,
                       GlossaryCore.CO2TaxesValue: self.co2_taxes,
                       GlossaryCore.MarginValue:  self.margin,
                       GlossaryCore.TransportCostValue: self.transport,
                       GlossaryCore.ResourcesPriceValue: self.resources_price,
                       GlossaryCore.TransportMarginValue: self.margin,
                       'initial_production': BiomassFiredDiscipline.initial_production,
                       'initial_age_distrib': BiomassFiredDiscipline.initial_age_distribution,
                       GlossaryCore.EnergyCO2EmissionsValue: self.energy_carbon_emissions,
                       GlossaryCore.RessourcesCO2EmissionsValue: get_static_CO2_emissions(np.arange(2020, 2051)),
                       'scaling_factor_invest_level': 1e3,
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production,
                       ResourceMixModel.RATIO_USABLE_DEMAND: self.ratio_available_resource,
                       GlossaryCore.AllStreamsDemandRatioValue: self.all_streams_demand_ratio,
                       'is_stream_demand': self.is_stream_demand,
                       'is_apply_resource_ratio': self.is_apply_resource_ratio,
                       'smooth_type': 'smooth_max',
                       'data_fuel_dict': Electricity.data_energy_dict,
                       }

        bf_model = BiomassFired('BiomassFired')
        bf_model.configure_parameters(inputs_dict)
        bf_model.configure_parameters_update(inputs_dict)
        price_details = bf_model.compute_price()
        bf_model.compute_consumption_and_production()
        bf_model.compute_consumption_and_power_production()

        print(bf_model.power_production)

        print(bf_model.power_production * bf_model.techno_infos_dict['full_load_hours'] / 1000)

        print(bf_model.production_detailed[f'electricity ({bf_model.product_energy_unit})'])

        self.assertLessEqual(list(bf_model.production_detailed[f'electricity ({bf_model.product_energy_unit})'].values),
                             list(bf_model.power_production['total_installed_power'] * bf_model.techno_infos_dict['full_load_hours'] / 1000 * 1.001))
        self.assertGreaterEqual(list(bf_model.production_detailed[f'electricity ({bf_model.product_energy_unit})'].values),
                                list(bf_model.power_production['total_installed_power'] * bf_model.techno_infos_dict['full_load_hours'] / 1000 * 0.999))

    def test_03_gas_turbine_discipline(self):

        self.name = 'Test'
        self.model_name = 'BiomassFired'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name,
                   'ns_energy': self.name,
                   'ns_energy_study': self.name,
                   'ns_electricity': self.name,
                   'ns_resource': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.electricity.biomass_fired.biomass_fired_disc.BiomassFiredDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        import traceback
        try:
            self.ee.configure()
        except:
            traceback.print_exc()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryCore.YearEnd}': 2050,
                       f'{self.name}.{GlossaryCore.EnergyPricesValue}': self.energy_prices,
                       f'{self.name}.{GlossaryCore.EnergyCO2EmissionsValue}': self.energy_carbon_emissions,
                       f'{self.name}.{self.model_name}.{GlossaryCore.InvestLevelValue}': self.invest_level_2,
                       f'{self.name}.{GlossaryCore.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryCore.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryCore.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryCore.ResourcesPriceValue}': self.resources_price,
                       f'{self.name}.{self.model_name}.{GlossaryCore.MarginValue}':  self.margin}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)
        for graph in graph_list:
            graph.to_plotly()#.show()
if __name__ == "__main__":
    unittest.main()