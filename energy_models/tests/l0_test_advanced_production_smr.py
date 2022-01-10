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


from energy_models.models.gaseous_hydrogen.smr.smr_disc import SMRDiscipline
from energy_models.models.gaseous_hydrogen.smr.smr import SMR
from energy_models.core.stream_type.ressources_data_disc import get_static_CO2_emissions
from climateeconomics.core.core_resources.all_resources_model import AllResourceModel
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import GaseousHydrogen


class AdvancedProductionSMRTestCase(unittest.TestCase):
    """
    Advanced Production SMR test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        years = np.arange(2020, 2051)
        self.resource_list = [
            'oil_resource', 'natural_gas_resource', 'uranium_resource', 'coal_resource']
        self.ratio_available_resource = pd.DataFrame(
            {'years': np.arange(2020, 2050 + 1)})
        for types in self.resource_list:
            self.ratio_available_resource[types] = np.linspace(
                1, 1, len(self.ratio_available_resource.index))
        self.energy_prices = pd.DataFrame({'years': years, 'electricity': np.array([0.09, 0.08974117039450046, 0.08948672733558984,
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
                                           'methane': np.array([0.06363, 0.0612408613576689, 0.059181808246196024, 0.05738028027202377,
                                                                0.0557845721244601, 0.05435665353332419, 0.05225877624361548,
                                                                0.05045797192512811, 0.04888746457113824, 0.04750006564084081,
                                                                0.04626130284326101, 0.044848110567750024, 0.043596892851567724,
                                                                0.04247763196812953, 0.04146768302263715, 0.04054957955940597,
                                                                0.03970959176775726, 0.03893674917609171, 0.038222160192931814,
                                                                0.03755852715493717, 0.03693979356326306, 0.03636088278590117,
                                                                0.03581750135963429, 0.03530598876014997, 0.03482320115289285,
                                                                0.03436642036567466, 0.03393328183670935, 0.033521717015978045,
                                                                0.03312990690071806, 0.032756244237772174, 0.03239930253734476]) * 1000.0
                                           })

        self.energy_carbon_emissions = pd.DataFrame(
            {'years': years, 'methane': 0.123 / 15.4, 'electricity': 0.0})
        # We use the IEA H2 demand to fake the invest level through years
        self.scaling_factor_invest_level = 1e3
        self.scaling_factor_techno_consumption = 1e3
        self.scaling_factor_techno_production = 1e3
        self.invest_level = pd.DataFrame({'years': years,
                                          'invest': np.array([4435750000.0, 4522000000.0, 4608250000.0,
                                                              4694500000.0, 4780750000.0, 4867000000.0,
                                                              4969400000.0, 5071800000.0, 5174200000.0,
                                                              5276600000.0, 5379000000.0, 5364700000.0,
                                                              5350400000.0, 5336100000.0, 5321800000.0,
                                                              5307500000.0, 5293200000.0, 5278900000.0,
                                                              5264600000.0, 5250300000.0, 5236000000.0,
                                                              5221700000.0, 5207400000.0, 5193100000.0,
                                                              5178800000.0, 5164500000.0, 5150200000.0,
                                                              5135900000.0, 5121600000.0, 5107300000.0,
                                                              5093000000.0]) * 1.0e-9})
        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [14.86, 17.22, 20.27,
                     29.01,  34.05,   39.08,  44.69,   50.29]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {'years': years, 'CO2_tax': func(years)})
        self.margin = pd.DataFrame(
            {'years': years, 'margin': np.ones(len(years)) * 110.0})
        self.transport = pd.DataFrame(
            {'years': years, 'transport': np.ones(len(years)) * 500.0})

        self.ressources_price = pd.DataFrame(
            columns=['years', 'water'])
        self.ressources_price['years'] = years
        self.ressources_price['water'] = 1.4
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.ones((len(years), len(years)))))
        demand_ratio_dict['years'] = years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)
        self.is_stream_demand = True
        self.is_apply_resource_ratio = True

    def tearDown(self):
        pass

    def test_02_compute_prod_from_invest(self):
        year_start = 2020
        year_end = 2050
        inputs_dict = {'year_start': year_start,
                       'year_end': year_end,
                       'techno_infos_dict': SMRDiscipline.techno_infos_dict_default,
                       'energy_prices': self.energy_prices,
                       'invest_level': self.invest_level,
                       'CO2_taxes': self.co2_taxes,
                       'margin':  self.margin,
                       'transport_cost': self.transport,
                       'transport_margin': self.margin,
                       'initial_production': SMRDiscipline.initial_production,
                       'initial_age_distrib': SMRDiscipline.initial_age_distribution,
                       'invest_before_ystart': SMRDiscipline.invest_before_year_start,
                       'ressources_price': self.ressources_price,
                       'ressources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       'energy_CO2_emissions': self.energy_carbon_emissions,
                       'scaling_factor_invest_level': self.scaling_factor_invest_level,
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production,
                       AllResourceModel.RATIO_USABLE_DEMAND: self.ratio_available_resource,
                       'all_streams_demand_ratio': self.all_streams_demand_ratio,
                       'is_stream_demand': self.is_stream_demand,
                       'is_apply_resource_ratio': self.is_apply_resource_ratio,
                       'data_fuel_dict': GaseousHydrogen.data_energy_dict,
                       }

        smr_model = SMR('SMR')
        smr_model.configure_parameters(inputs_dict)
        smr_model.configure_parameters_update(inputs_dict)
        price_details = smr_model.compute_price()
        # smr_model.compute_initial_aging_distribution()
        smr_model.production['invest'] = smr_model.cost_details['invest']
        construction_delay = 3

        prod = smr_model.compute_prod_from_invest(construction_delay)

        invest = self.invest_level['invest'].values
        price = price_details['Capex_SMR'].values

        # check price and invest after 2023
        self.assertListEqual(list(prod[
            'prod_from_invest'].values[construction_delay:]), list(
            invest[:-construction_delay] * self.scaling_factor_invest_level / price[:-construction_delay]))

        invest_before = SMRDiscipline.invest_before_year_start
        self.assertAlmostEqual(prod.loc[prod['years'] == 2020, 'prod_from_invest'].values[0],
                               invest_before.loc[invest_before['past years'] == -construction_delay, 'invest'].values[0] * self.scaling_factor_invest_level / price_details.loc[price_details['years'] == 2020, 'Capex_SMR'].values[0])

    def test_03_compute_aging_distribution_production(self):

        year_start = 2020
        year_end = 2050
        inputs_dict = {'year_start': year_start,
                       'year_end': year_end,
                       'techno_infos_dict': SMRDiscipline.techno_infos_dict_default,
                       'energy_prices': self.energy_prices,
                       'invest_level': self.invest_level,
                       'CO2_taxes': self.co2_taxes,
                       'margin':  self.margin,
                       'transport_cost': self.transport,
                       'transport_margin': self.margin,
                       'initial_production': SMRDiscipline.initial_production,
                       'initial_age_distrib': SMRDiscipline.initial_age_distribution,
                       'invest_before_ystart': SMRDiscipline.invest_before_year_start,
                       'ressources_price': self.ressources_price,
                       'ressources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       'energy_CO2_emissions': self.energy_carbon_emissions,
                       'scaling_factor_invest_level': self.scaling_factor_invest_level,
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production,
                       AllResourceModel.RATIO_USABLE_DEMAND: self.ratio_available_resource,
                       'all_streams_demand_ratio': self.all_streams_demand_ratio,
                       'is_stream_demand': self.is_stream_demand,
                       'is_apply_resource_ratio': self.is_apply_resource_ratio,
                       'data_fuel_dict': GaseousHydrogen.data_energy_dict,
                       }


        smr_model = SMR('SMR')
        smr_model.configure_parameters(inputs_dict)
        smr_model.configure_parameters_update(inputs_dict)
        price_details = smr_model.compute_price()
        # smr_model.compute_initial_aging_distribution()

        smr_model.compute_aging_distribution_production()

        age_distribution = smr_model.age_distrib_prod_df
#np.arange(year_start, year_end + 1)

        max_age = age_distribution['age'].max()
        # Check if an age is higher than lifetime
        self.assertLessEqual(
            max_age, SMRDiscipline.techno_infos_dict_default['lifetime'])

        prod = smr_model.compute_prod_from_invest(3)

        aging_distrib_year_df = smr_model.initial_age_distrib.copy(deep=True)
        aging_distrib_year_df[f'distrib_prod (TWh)'] = aging_distrib_year_df['distrib'] * \
            smr_model.initial_production / 100.0
        aging_distrib_year_df = aging_distrib_year_df[[
            'age', f'distrib_prod (TWh)']]

        age_distribution_2030 = age_distribution.loc[age_distribution['years'] == 2030]
        # 10 years of production since 2020 + 15 years of old age distribution
        # (25-11) but possibility to have zero distrib and a line suppressed

        self.assertLessEqual(len(age_distribution_2030), 10 + 15)

        prod_before2030 = prod.loc[prod['years'] <=
                                   2030, 'prod_from_invest'].values[::-1]
        prod_from_old = aging_distrib_year_df[f'distrib_prod (TWh)'].values[:14]

        th_age_distrib_2030 = pd.DataFrame({'age': np.arange(
            0, 25), 'years': 2030, 'distrib_prod (TWh)': np.concatenate((prod_before2030, prod_from_old))})

        th_age_distrib_2030 = th_age_distrib_2030[
            th_age_distrib_2030['distrib_prod (TWh)'] != 0.0]

        for column in th_age_distrib_2030:
            self.assertListEqual(list(th_age_distrib_2030[column].values), list(
                age_distribution_2030[column].values))

    def test_04_get_functions(self):

        year_start = 2020
        year_end = 2050
        inputs_dict = {'year_start': year_start,
                       'year_end': year_end,
                       'techno_infos_dict': SMRDiscipline.techno_infos_dict_default,
                       'energy_prices': self.energy_prices,
                       'invest_level': self.invest_level,
                       'CO2_taxes': self.co2_taxes,
                       'margin':  self.margin,
                       'transport_cost': self.transport,
                       'transport_margin': self.margin,
                       'initial_production': SMRDiscipline.initial_production,
                       'initial_age_distrib': SMRDiscipline.initial_age_distribution,
                       'invest_before_ystart': SMRDiscipline.invest_before_year_start,
                       'ressources_price': self.ressources_price,
                       'ressources_CO2_emissions': get_static_CO2_emissions(np.arange(2020, 2051)),
                       'energy_CO2_emissions': self.energy_carbon_emissions,
                       'scaling_factor_invest_level': self.scaling_factor_invest_level,
                       'scaling_factor_techno_consumption': self.scaling_factor_techno_consumption,
                       'scaling_factor_techno_production': self.scaling_factor_techno_production,
                       AllResourceModel.RATIO_USABLE_DEMAND: self.ratio_available_resource,
                       'all_streams_demand_ratio': self.all_streams_demand_ratio,
                       'is_stream_demand': self.is_stream_demand,
                       'is_apply_resource_ratio': self.is_apply_resource_ratio,
                       'data_fuel_dict': GaseousHydrogen.data_energy_dict,
                       }

        smr_model = SMR('SMR')
        smr_model.configure_parameters(inputs_dict)
        smr_model.configure_parameters_update(inputs_dict)
        price_details = smr_model.compute_price()
        smr_model.compute_primary_energy_production()
        age_distribution = smr_model.get_all_age_distribution()

        mean_age = smr_model.get_mean_age_over_years()

        # Check if an age is higher than lifetime
        self.assertLessEqual(
            mean_age['mean age'].max(), SMRDiscipline.techno_infos_dict_default['lifetime'])
