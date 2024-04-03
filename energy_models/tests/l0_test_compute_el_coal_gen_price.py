'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2024/03/27 Copyright 2023 Capgemini

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

import numpy as np
import pandas as pd
import scipy.interpolate as sc

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
from energy_models.core.stream_type.resources_models.water import Water
from energy_models.glossaryenergy import GlossaryEnergy
from sostrades_core.execution_engine.execution_engine import ExecutionEngine


class CoalGenPriceTestCase(unittest.TestCase):
    """
    Coal prices test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        solid_fuel_price = np.array(
            [5.7] * 31)
        years = np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)
        self.resource_list = [
            'oil_resource', 'natural_gas_resource', 'uranium_resource', 'coal_resource']
        self.ratio_available_resource = pd.DataFrame(
            {GlossaryEnergy.Years: np.arange(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1)})
        for types in self.resource_list:
            self.ratio_available_resource[types] = np.linspace(
                1, 1, len(self.ratio_available_resource.index))
        self.energy_prices = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.electricity: np.array([0.09, 0.08974117039450046, 0.08948672733558984,
                                                                   0.089236536471781, 0.08899046935409588,
                                                                   0.08874840310033885,
                                                                   0.08875044941298937, 0.08875249600769718,
                                                                   0.08875454288453355,
                                                                   0.08875659004356974, 0.0887586374848771,
                                                                   0.08893789675406477,
                                                                   0.08911934200930778, 0.08930302260662477,
                                                                   0.08948898953954933,
                                                                   0.08967729551117891, 0.08986799501019029,
                                                                   0.09006114439108429,
                                                                   0.09025680195894345, 0.09045502805900876,
                                                                   0.09065588517140537,
                                                                   0.0908594380113745, 0.09106575363539733,
                                                                   0.09127490155362818,
                                                                   0.09148695384909017, 0.0917019853041231,
                                                                   0.0919200735346165,
                                                                   0.09214129913260598, 0.09236574581786147,
                                                                   0.09259350059915213,
                                                                   0.0928246539459331]) * 1000.0,
             GlossaryEnergy.solid_fuel: solid_fuel_price
             })

        self.energy_carbon_emissions = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.solid_fuel: 0.64 / 4.86, GlossaryEnergy.electricity: 0.0})
        self.invest_level = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.InvestValue: np.ones(len(years)) * 50.0})

        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [14.86, 17.22, 20.27,
                     29.01, 34.05, 39.08, 44.69, 50.29]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.CO2Tax: func(years)})
        self.margin = pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.MarginValue: np.ones(len(years)) * 110.0})

        transport_cost = 0
        # It is noteworthy that the cost of transmission has generally been held (and can
        # continue to be held)    within the 10-12/MWhr range despite transmission distances
        # increasing by almost an order of magnitude from an average of 20km for the
        # leftmost bar to 170km for the 2020 scenarios / OWPB 2016

        self.transport = pd.DataFrame(
            {GlossaryEnergy.Years: years, 'transport': np.ones(len(years)) * transport_cost})
        self.resources_price = pd.DataFrame()

        self.resources_price = pd.DataFrame(
            columns=[GlossaryEnergy.Years, ResourceGlossary.WaterResource])
        self.resources_price[GlossaryEnergy.Years] = years
        self.resources_price[ResourceGlossary.WaterResource
        ] = Water.data_energy_dict['cost_now']

        biblio_data_path = join(
            dirname(__file__), 'output_values_check', 'biblio_data.csv')
        self.biblio_data = pd.read_csv(biblio_data_path)
        self.biblio_data = self.biblio_data.loc[self.biblio_data['sos_name']
                                                == f'{GlossaryEnergy.electricity}.CoalGen']
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

    def test_03_coal_gen_discipline(self):

        self.name = 'Test'
        self.model_name = 'Coal_Electricity'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name,
                   'ns_energy': self.name,
                   'ns_energy_study': self.name,
                   'ns_electricity': self.name,
                   'ns_solid_fuel': self.name,
                   'ns_resource': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.electricity.coal_gen.coal_gen_disc.CoalGenDiscipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        import traceback
        try:
            self.ee.configure()
        except:
            traceback.print_exc()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.{GlossaryEnergy.YearEnd}': GlossaryEnergy.YearEndDefault,
                       f'{self.name}.{GlossaryEnergy.EnergyPricesValue}': self.energy_prices,
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

        production_detailed = disc.get_sosdisc_outputs(GlossaryEnergy.TechnoDetailedProductionValue)
        power_production = disc.get_sosdisc_outputs(GlossaryEnergy.InstalledPower)
        techno_infos_dict = disc.get_sosdisc_inputs('techno_infos_dict')

        self.assertLessEqual(list(production_detailed[f'{GlossaryEnergy.electricity} (TWh)'].values),
                             list(power_production['total_installed_power'] * techno_infos_dict[
                                 'full_load_hours'] / 1000 * 1.001))
        self.assertGreaterEqual(list(production_detailed[f'{GlossaryEnergy.electricity} (TWh)'].values),
                                list(power_production['total_installed_power'] * techno_infos_dict[
                                    'full_load_hours'] / 1000 * 0.999))
        filters = disc.get_chart_filter_list()
        graph_list = disc.get_post_processing_list(filters)

        # for graph in graph_list:
        #     graph.to_plotly().show()


if __name__ == "__main__":
    unittest.main()
