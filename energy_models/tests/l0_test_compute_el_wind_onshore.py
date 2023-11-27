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
from os.path import join, dirname

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.interpolate as sc

from climateeconomics.core.core_resources.resource_mix.resource_mix import ResourceMixModel
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.resources_data_disc import get_static_CO2_emissions
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.electricity.wind_onshore.wind_onshore import WindOnshore
from energy_models.models.electricity.wind_onshore.wind_onshore_disc import WindOnshoreDiscipline
from sostrades_core.execution_engine.execution_engine import ExecutionEngine


class WindOnshoreTestCase(unittest.TestCase):
    """
    WindOnshore prices test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        years = np.arange(2020, 2051)
        self.resource_list = [
            'oil_resource', 'natural_gas_resource', 'uranium_resource', 'coal_resource']
        self.ratio_available_resource = pd.DataFrame(
            {GlossaryEnergy.Years: np.arange(2020, 2050 + 1)})
        for types in self.resource_list:
            self.ratio_available_resource[types] = np.linspace(
                1, 1, len(self.ratio_available_resource.index))

        self.invest_level = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.InvestValue: np.array([22.0, 22.0, 22.0, 22.0,
                                                 22.0, 22.0, 22.0, 22.0,
                                                 22.0, 22.0, 31.0, 31.0,
                                                 31.0, 31.0, 31.0, 31.0,
                                                 31.0, 31.0, 31.0, 31.0,
                                                 31.0, 31.0, 31.0, 31.0,
                                                 31.0, 31.0, 31.0, 31.0,
                                                 31.0, 31.0, 31.0]) * 1e-3})

        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [14.86, 17.22, 20.27,
                     29.01,  34.05,   39.08,  44.69,   50.29]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')
        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.CO2Tax: func(years)})

        self.margin = pd.DataFrame(
            {GlossaryEnergy.Years: np.arange(2020, 2051), GlossaryEnergy.MarginValue: np.ones(len(np.arange(2020, 2051))) * 110})

        transport_cost = 11,
        # It is noteworthy that the cost of transmission has generally been held (and can
        # continue to be held)	within the £10-12/MWhr range despite transmission distances
        # increasing by almost an order of magnitude from an average of 20km for the
        # leftmost bar to 170km for the 2020 scenarios / OWPB 2016

        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'transport': np.ones(len(years)) * transport_cost})

        self.resources_price = pd.DataFrame({GlossaryEnergy.Years: years})

        self.energy_prices = pd.DataFrame({GlossaryEnergy.Years: years})

        biblio_data_path = join(
            dirname(__file__), 'output_values_check', 'biblio_data.csv')
        self.biblio_data = pd.read_csv(biblio_data_path)
        self.biblio_data = self.biblio_data.loc[self.biblio_data['sos_name']
                                                == 'electricity.Wind_Onshore']
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

    def test_01_compute_wind_onshore_price(self):

        years = np.arange(2020, 2051)
        utilisation_ratio = pd.DataFrame({
            GlossaryEnergy.Years: years,
            GlossaryEnergy.UtilisationRatioValue: np.ones_like(years) * 100.
        })
        
        inputs_dict = {GlossaryEnergy.YearStart: 2020,
                       GlossaryEnergy.YearEnd: 2050,
                       GlossaryEnergy.UtilisationRatioValue: utilisation_ratio,
                       'techno_infos_dict': WindOnshoreDiscipline.techno_infos_dict_default,
                       GlossaryEnergy.InvestLevelValue: self.invest_level,
                       GlossaryEnergy.InvestmentBeforeYearStartValue: WindOnshoreDiscipline.invest_before_year_start,
                       GlossaryEnergy.MarginValue:  self.margin,
                       GlossaryEnergy.TransportCostValue: self.transport,
                       GlossaryEnergy.ResourcesPriceValue: self.resources_price,
                       GlossaryEnergy.EnergyCO2EmissionsValue: pd.DataFrame(),
                       GlossaryEnergy.RessourcesCO2EmissionsValue: get_static_CO2_emissions(np.arange(2020, 2051)),
                       GlossaryEnergy.EnergyPricesValue: self.energy_prices,
                       GlossaryEnergy.CO2TaxesValue: self.co2_taxes,
                       GlossaryEnergy.TransportMarginValue: self.margin,
                       'initial_production': WindOnshoreDiscipline.initial_production,
                       'initial_age_distrib': WindOnshoreDiscipline.initial_age_distribution,
                       'scaling_factor_invest_level': 1e3,
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production,
                       ResourceMixModel.RATIO_USABLE_DEMAND: self.ratio_available_resource,
                       GlossaryEnergy.AllStreamsDemandRatioValue: self.all_streams_demand_ratio,
                       'is_stream_demand': self.is_stream_demand,
                       'is_apply_resource_ratio': self.is_apply_resource_ratio,
                       'smooth_type': 'smooth_max',
                       'data_fuel_dict': Electricity.data_energy_dict,
                       }

        model = WindOnshore('WindOnShore')
        model.configure_parameters(inputs_dict)
        model.configure_parameters_update(inputs_dict)
        price_details = model.compute_price()

        # Comparison in $/kWH
        plt.figure()
        plt.xlabel(GlossaryEnergy.Years)

        plt.plot(price_details[GlossaryEnergy.Years],
                 price_details['WindOnShore'], label='SoSTrades Total')

        plt.plot(price_details[GlossaryEnergy.Years], price_details['transport'],
                 label='SoSTrades Transport')

        plt.plot(price_details[GlossaryEnergy.Years], price_details['WindOnShore_factory'],
                 label='SoSTrades Factory')
        plt.legend()
        plt.ylabel('Price ($/kWh)')
        # plt.show()
        # plt.savefig('WindOnshore_COMP.png')

    def test_03_wind_on_shore_discipline(self):

        self.name = 'Test'
        self.model_name = 'Wind_Electricity'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name,
                   'ns_energy': self.name,
                   'ns_energy_study': f'{self.name}',
                   'ns_electricity': self.name,
                   'ns_resource': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.electricity.wind_onshore.wind_onshore_disc.WindOnshoreDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearEnd}': 2050,
                       f'{self.name}.{GlossaryEnergy.EnergyPricesValue}': self.energy_prices,
                       f'{self.name}.{GlossaryEnergy.EnergyCO2EmissionsValue}': pd.DataFrame(),
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': self.resources_price,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}':  self.margin}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]

        production_detailed = disc.get_sosdisc_outputs(GlossaryEnergy.TechnoDetailedProductionValue)
        power_production = disc.get_sosdisc_outputs(GlossaryEnergy.InstalledPower)
        techno_infos_dict = disc.get_sosdisc_inputs('techno_infos_dict')

        self.assertLessEqual(list(production_detailed['electricity (TWh)'].values),
                             list(power_production['total_installed_power'] * techno_infos_dict[
                                 'full_load_hours'] / 1000 * 1.001))
        self.assertGreaterEqual(list(production_detailed[f'electricity (TWh)'].values),
                                list(power_production['total_installed_power'] * techno_infos_dict[
                                    'full_load_hours'] / 1000 * 0.999))
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)
#         for graph in graph_list:
#             graph.to_plotly().show()
# if __name__ == "__main__":
#     unittest.main()