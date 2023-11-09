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
import scipy.interpolate as sc
from os.path import join, dirname

from climateeconomics.glossarycore import GlossaryCore
from energy_models.models.electricity.oil_gen.oil_gen_disc import OilGenDiscipline
from energy_models.models.electricity.oil_gen.oil_gen import OilGen
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from energy_models.core.stream_type.resources_models.water import Water
from energy_models.core.stream_type.resources_data_disc import get_static_CO2_emissions
from climateeconomics.core.core_resources.resource_mix.resource_mix import ResourceMixModel
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.energy_models.solid_fuel import SolidFuel
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary


class OilGenPriceTestCase(unittest.TestCase):
    """
    Oil prices test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        liquid_fuel_price = np.array(
            [40] * 31)
        years = np.arange(2020, 2051)
        self.resource_list = [
            'oil_resource', 'natural_gas_resource', 'uranium_resource', 'coal_resource']
        self.ratio_available_resource = pd.DataFrame(
            {GlossaryCore.Years: np.arange(2020, 2050 + 1)})
        for types in self.resource_list:
            self.ratio_available_resource[types] = np.linspace(
                1, 1, len(self.ratio_available_resource.index))
        self.energy_prices = pd.DataFrame({GlossaryCore.Years: years, 'electricity': np.array([0.09, 0.08974117039450046, 0.08948672733558984,
                                                                                    0.089236536471781, 0.08899046935409588, 0.08874840310033885,
                                                                                    0.08875044941298937, 0.08875249600769718, 0.08875454288453355,
                                                                                    0.08875659004356974, 0.0887586374848771, 0.08893789675406477,
                                                                                    0.08911934200930778, 0.08930302260662477, 0.08948898953954933,
                                                                                    0.08967729551117891, 0.08986799501019029, 0.09006114439108429,
                                                                                    0.09025680195894345, 0.09045502805900876, 0.09065588517140537,
                                                                                    0.0908594380113745, 0.09106575363539733, 0.09127490155362818,
                                                                                    0.09148695384909017, 0.0917019853041231, 0.0919200735346165,
                                                                                    0.09214129913260598, 0.09236574581786147, 0.09259350059915213,
                                                                                    0.0928246539459331]) * 1000.0,
                                           'fuel.liquid_fuel': liquid_fuel_price
                                           })

        self.energy_carbon_emissions = pd.DataFrame(
            {GlossaryCore.Years: years, 'fuel.liquid_fuel': 0.64 / 4.86, 'electricity': 0.0})
        #  IEA invest data NPS Scenario 22bn to 2030 and 31bn after 2030

        self.invest_level = pd.DataFrame(
            {GlossaryCore.Years: years, GlossaryCore.InvestValue: np.ones(len(years)) * 50.0})

        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [14.86, 17.22, 20.27,
                     29.01,  34.05,   39.08,  44.69,   50.29]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {GlossaryCore.Years: years, GlossaryCore.CO2Tax: 0.0})
        self.margin = pd.DataFrame(
            {GlossaryCore.Years: years, GlossaryCore.MarginValue: np.ones(len(years)) * 110.0})

        transport_cost = 0
        # It is noteworthy that the cost of transmission has generally been held (and can
        # continue to be held)    within the �10-12/MWhr range despite transmission distances
        # increasing by almost an order of magnitude from an average of 20km for the
        # leftmost bar to 170km for the 2020 scenarios / OWPB 2016

        self.transport = pd.DataFrame(
            {GlossaryCore.Years: years, 'transport': np.ones(len(years)) * transport_cost})
        self.resources_price = pd.DataFrame()

        self.resources_price = pd.DataFrame(
            columns=[GlossaryCore.Years, ResourceGlossary.Water['name']])
        self.resources_price[GlossaryCore.Years] = years
        self.resources_price[ResourceGlossary.Water['name']
                             ] = Water.data_energy_dict['cost_now']

        biblio_data_path = join(
            dirname(__file__), 'output_values_check', 'biblio_data.csv')
        self.biblio_data = pd.read_csv(biblio_data_path)
        self.biblio_data = self.biblio_data.loc[self.biblio_data['sos_name']
                                                == 'electricity.OilGen']
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

    def test_01_compute_oil_gen_price(self):

        inputs_dict = {GlossaryCore.YearStart: 2020,
                       GlossaryCore.YearEnd: 2050,
                       'techno_infos_dict': OilGenDiscipline.techno_infos_dict_default,
                       GlossaryCore.InvestLevelValue: self.invest_level,
                       GlossaryCore.InvestmentBeforeYearStartValue: OilGenDiscipline.invest_before_year_start,
                       GlossaryCore.CO2TaxesValue: self.co2_taxes,
                       GlossaryCore.MarginValue:  self.margin,
                       GlossaryCore.TransportCostValue: self.transport,
                       GlossaryCore.TransportMarginValue: self.margin,
                       'initial_production': OilGenDiscipline.initial_production,
                       'initial_age_distrib': OilGenDiscipline.initial_age_distribution,
                       GlossaryCore.ResourcesPriceValue: self.resources_price,
                       GlossaryCore.EnergyPricesValue: self.energy_prices,
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
                       'data_fuel_dict': SolidFuel.data_energy_dict,
                       }

        oilgen_model = OilGen('CoalGen')
        oilgen_model.configure_parameters(inputs_dict)
        oilgen_model.configure_parameters_update(inputs_dict)
        price_details = oilgen_model.compute_price()

    def test_02_compute_oil_gen_price_prod_consumption(self):

        inputs_dict = {GlossaryCore.YearStart: 2020,
                       GlossaryCore.YearEnd: 2050,
                       'techno_infos_dict': OilGenDiscipline.techno_infos_dict_default,
                       GlossaryCore.EnergyPricesValue: self.energy_prices,
                       GlossaryCore.InvestLevelValue: self.invest_level,
                       GlossaryCore.InvestmentBeforeYearStartValue: OilGenDiscipline.invest_before_year_start,
                       GlossaryCore.CO2TaxesValue: self.co2_taxes,
                       GlossaryCore.MarginValue:  self.margin,
                       GlossaryCore.TransportCostValue: self.transport,
                       GlossaryCore.ResourcesPriceValue: self.resources_price,
                       GlossaryCore.TransportMarginValue: self.margin,
                       'initial_production': OilGenDiscipline.initial_production,
                       'initial_age_distrib': OilGenDiscipline.initial_age_distribution,
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
                       'data_fuel_dict': SolidFuel.data_energy_dict,
                       }

        oilgen_model = OilGen('CoalGen')
        oilgen_model.configure_parameters(inputs_dict)
        oilgen_model.configure_parameters_update(inputs_dict)
        price_details = oilgen_model.compute_price()
        oilgen_model.compute_consumption_and_production()

        oilgen_model.check_outputs_dict(self.biblio_data)

    def test_04_compute_oil_gen_power(self):

        inputs_dict = {GlossaryCore.YearStart: 2020,
                       GlossaryCore.YearEnd: 2050,
                       'techno_infos_dict': OilGenDiscipline.techno_infos_dict_default,
                       GlossaryCore.EnergyPricesValue: self.energy_prices,
                       GlossaryCore.InvestLevelValue: self.invest_level,
                       GlossaryCore.InvestmentBeforeYearStartValue: OilGenDiscipline.invest_before_year_start,
                       GlossaryCore.CO2TaxesValue: self.co2_taxes,
                       GlossaryCore.MarginValue:  self.margin,
                       GlossaryCore.TransportCostValue: self.transport,
                       GlossaryCore.ResourcesPriceValue: self.resources_price,
                       GlossaryCore.TransportMarginValue: self.margin,
                       'initial_production': OilGenDiscipline.initial_production,
                       'initial_age_distrib': OilGenDiscipline.initial_age_distribution,
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
                       'data_fuel_dict': SolidFuel.data_energy_dict,
                       }

        oilgen_model = OilGen('CoalGen')
        oilgen_model.configure_parameters(inputs_dict)
        oilgen_model.configure_parameters_update(inputs_dict)
        price_details = oilgen_model.compute_price()
        oilgen_model.compute_consumption_and_production()
        oilgen_model.compute_consumption_and_power_production()

        print(oilgen_model.power_production)

        print(oilgen_model.power_production * oilgen_model.techno_infos_dict['full_load_hours'] / 1000)

        print(oilgen_model.production_detailed[f'electricity ({oilgen_model.product_energy_unit})'])

        self.assertLessEqual(list(oilgen_model.production_detailed[f'electricity ({oilgen_model.product_energy_unit})'].values),
                             list(oilgen_model.power_production['total_installed_power'] * oilgen_model.techno_infos_dict['full_load_hours'] / 1000 * 1.001))
        self.assertGreaterEqual(list(oilgen_model.production_detailed[f'electricity ({oilgen_model.product_energy_unit})'].values),
                                list(oilgen_model.power_production['total_installed_power'] * oilgen_model.techno_infos_dict['full_load_hours'] / 1000 * 0.999))

    def test_03_oil_gen_discipline(self):

        self.name = 'Test'
        self.model_name = 'Oil_Electricity'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name,
                   'ns_energy': self.name,
                   'ns_energy_study': self.name,
                   'ns_electricity': self.name,
                   'ns_solid_fuel': self.name,
                   'ns_resource': self.name}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.models.electricity.oil_gen.oil_gen_disc.OilGenDiscipline'
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
                       f'{self.name}.{self.model_name}.{GlossaryCore.InvestLevelValue}': self.invest_level,
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

#         for graph in graph_list:
#             graph.to_plotly().show()
# if __name__ == "__main__":
#     unittest.main()
