'''
Copyright 2022 Airbus SAS
Modifications on 2023/05/02-2024/06/24 Copyright 2023 Capgemini

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
from os.path import dirname, join

import numpy as np
import pandas as pd
from climateeconomics.core.core_resources.resource_mix.resource_mix import (
    ResourceMixModel,
)
from sostrades_core.execution_engine.execution_engine import ExecutionEngine

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.resources_data_disc import (
    get_default_resources_CO2_emissions,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.electricity.solar_thermal.solar_thermal_disc import (
    SolarThermalDiscipline,
)


class SolarThermalPriceTestCase(unittest.TestCase):
    """
    Solar Thermal prices test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.years = np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)
        self.resource_list = [
            'oil_resource', 'natural_gas_resource', 'uranium_resource', 'coal_resource']
        self.ratio_available_resource = pd.DataFrame(
            {GlossaryEnergy.Years: np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)})
        for types in self.resource_list:
            self.ratio_available_resource[types] = np.linspace(
                1, 1, len(self.ratio_available_resource.index))

        self.invest_level_2 = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.InvestValue: 15.0})

        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.CO2Tax: np.linspace(14., 40., len(self.years))})
        self.margin = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, GlossaryEnergy.MarginValue: 110.0})

        transport_cost = 11
        # It is noteworthy that the cost of transmission has generally been held (and can
        # continue to be held)    within the 10-12/MWhr range despite transmission distances
        # increasing by almost an order of magnitude from an average of 20km for the
        # leftmost bar to 170km for the 2020 scenarios / OWPB 2016

        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: self.years, 'transport': transport_cost})
        self.resources_price = pd.DataFrame({GlossaryEnergy.Years: self.years})
        self.stream_prices = pd.DataFrame({GlossaryEnergy.Years: self.years})

        biblio_data_path = join(
            dirname(__file__), 'output_values_check', 'biblio_data.csv')
        self.biblio_data = pd.read_csv(biblio_data_path)
        self.biblio_data = self.biblio_data.loc[self.biblio_data['sos_name']
                                                == f'{GlossaryEnergy.electricity}.{GlossaryEnergy.SolarThermal}']
        self.scaling_factor_techno_consumption = 1e3
        self.scaling_factor_techno_production = 1e3
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.ones((len(self.years), len(self.years)))))
        demand_ratio_dict[GlossaryEnergy.Years] = self.years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)
        self.is_stream_demand = True
        self.is_apply_resource_ratio = True

        self.years = np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)
        utilisation_ratio = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.UtilisationRatioValue: 100.
        })
        self.inputs_dict = {GlossaryEnergy.YearStart: GlossaryEnergy.YearStartDefault,
                            GlossaryEnergy.YearEnd: GlossaryEnergy.YearEndDefault,
                            GlossaryEnergy.UtilisationRatioValue: utilisation_ratio,
                            'techno_infos_dict': SolarThermalDiscipline.techno_infos_dict_default,
                            GlossaryEnergy.InvestLevelValue: self.invest_level_2,
                            GlossaryEnergy.CO2TaxesValue: self.co2_taxes,
                            GlossaryEnergy.MarginValue: self.margin,
                            GlossaryEnergy.TransportCostValue: self.transport,
                            GlossaryEnergy.TransportMarginValue: self.margin,
                            GlossaryEnergy.ResourcesPriceValue: self.resources_price,
                            GlossaryEnergy.StreamPricesValue: self.stream_prices,
                            'initial_production': SolarThermalDiscipline.initial_production,
                            GlossaryEnergy.RessourcesCO2EmissionsValue: get_default_resources_CO2_emissions(
                                np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)),
                            GlossaryEnergy.StreamsCO2EmissionsValue: pd.DataFrame(),
                            'scaling_factor_invest_level': 1e3,
                            'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                            'scaling_factor_techno_production': self.scaling_factor_techno_production,
                            ResourceMixModel.RATIO_USABLE_DEMAND: self.ratio_available_resource,
                            GlossaryEnergy.AllStreamsDemandRatioValue: self.all_streams_demand_ratio,
                            GlossaryEnergy.BoolApplyStreamRatio: self.is_stream_demand,
                            GlossaryEnergy.BoolApplyResourceRatio: self.is_apply_resource_ratio,
                            'smooth_type': 'smooth_max',
                            'data_fuel_dict': Electricity.data_energy_dict,
                            }

    def tearDown(self):
        pass

    def test_03_solar_Thermal_discipline(self):
        self.name = 'Test'
        self.model_name = 'Solar_Electricity'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name,
                   'ns_energy': self.name,
                   'ns_energy_study': self.name,
                   'ns_electricity': self.name,
                   'ns_resource': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.electricity.solar_thermal.solar_thermal_disc.SolarThermalDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)
        self.ee.configure()

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearEnd}': GlossaryEnergy.YearEndDefault,
                       f'{self.name}.{GlossaryEnergy.StreamPricesValue}': self.stream_prices,
                       f'{self.name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': pd.DataFrame({GlossaryEnergy.Years: self.years}),
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.InvestLevelValue}': self.invest_level_2,
                       f'{self.name}.{GlossaryEnergy.CO2TaxesValue}': self.co2_taxes,
                       f'{self.name}.{GlossaryEnergy.TransportMarginValue}': self.margin,
                       f'{self.name}.{GlossaryEnergy.TransportCostValue}': self.transport,
                       f'{self.name}.{GlossaryEnergy.ResourcesPriceValue}': self.resources_price,
                       f'{self.name}.{self.model_name}.{GlossaryEnergy.MarginValue}': self.margin}

        self.ee.load_study_from_input_dict(inputs_dict)

        self.ee.execute()

        disc = self.ee.dm.get_disciplines_with_name(
            f'{self.name}.{self.model_name}')[0]

        production_detailed = disc.get_sosdisc_outputs(GlossaryEnergy.TechnoDetailedProductionValue)
        power_production = disc.get_sosdisc_outputs(GlossaryEnergy.InstalledPower)
        techno_infos_dict = disc.get_sosdisc_inputs('techno_infos_dict')

        self.assertLessEqual(list(production_detailed[f'{GlossaryEnergy.electricity} ({GlossaryEnergy.energy_unit})'].values),
                             list(power_production['total_installed_power'] * techno_infos_dict[
                                 'full_load_hours'] / 1000 * 1.001))
        self.assertGreaterEqual(list(production_detailed[f'{GlossaryEnergy.electricity} ({GlossaryEnergy.energy_unit})'].values),
                                list(power_production['total_installed_power'] * techno_infos_dict[
                                    'full_load_hours'] / 1000 * 0.999))
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)

        # for graph in graph_list:
        #     graph.to_plotly().show()

# if __name__ == "__main__":
#     unittest.main()
