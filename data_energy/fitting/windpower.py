'''
Copyright 2024 Capgemini

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
import os
import pickle
from copy import deepcopy
from functools import reduce

import numpy as np
import pandas as pd
from climateeconomics.glossarycore import GlossaryCore
from scipy.interpolate import interp1d
from scipy.optimize import minimize
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tools.bspline.bspline import BSpline
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import (
    InstanciatedSeries,
    TwoAxesInstanciatedChart,
)

from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.electricity.wind_onshore.wind_onshore_disc import (
    WindOnshoreDiscipline,
)

"""
This script is used to calibrate the windpower invest so that the electricity production matches the IEA NZE scenario
production values between 2020 and 2050
"""

year_start = 2020
year_end = 2100
years_IEA = [2020, 2025, 2030, 2035, 2040, 2045, 2050, 2100]
years = np.arange(year_start, year_end + 1)


# source: IEA report NZE2021Ch02
models_path_abs = os.path.dirname(os.path.abspath(__file__)).split(os.sep + "models")[0]
df_prod_iea = pd.read_csv(
    os.path.join(models_path_abs, 'models', 'witness-core', 'climateeconomics', 'data', 'IEA_NZE_EnergyMix.electricity.WindXXshore.techno_production.csv'))
new_row = pd.DataFrame({'years': [2100], 'electricity (TWh)': [35000.]})
df_prod_iea = pd.concat([df_prod_iea, new_row], ignore_index=True)

df_price_iea = pd.read_csv(
    os.path.join(models_path_abs, 'models', 'witness-core', 'climateeconomics', 'data', 'IEA_NZE_electricity_Technologies_Mix_prices.csv'))

# interpolate data between 2050 and 2100
years_IEA_interpolated = years
f = interp1d(years_IEA, df_prod_iea['electricity (TWh)'].values, kind='linear')
prod_IEA_interpolated = f(years_IEA_interpolated)

# optimization at the poles just like in witness-full study
years_optim = np.linspace(year_start, year_end, 8)  # years_IEA_interpolated #sorted(list(set(years_IEA + list(np.arange(year_start, max(year_start, 2030) + 1)))))

invest_year_start = 80.  # G$
construction_delay = GlossaryEnergy.TechnoConstructionDelayDict['WindOffshore']  # same construction delay for windonshore and windoffshore
if construction_delay != GlossaryEnergy.TechnoConstructionDelayDict['WindOnshore']:
    raise ValueError("must adapt script as construction delay for windOnshore and windOffshore differ")

name = 'usecase_witness_optim_nze_eval'
model_name_onshore = f"WITNESS_MDO.WITNESS_Eval.WITNESS.EnergyMix.electricity.{GlossaryEnergy.WindOnshore}"
model_name_offshore = f"WITNESS_MDO.WITNESS_Eval.WITNESS.EnergyMix.electricity.{GlossaryEnergy.WindOffshore}"
ns_dict = {'ns_public': name,
           'ns_energy': name,
           'ns_energy_study': f'{name}',
           'ns_electricity': name,
           'ns_resource': name}

mod_path_onshore = 'energy_models.models.electricity.wind_onshore.wind_onshore_disc.WindOnshoreDiscipline'
mod_path_offshore = 'energy_models.models.electricity.wind_offshore.wind_offshore_disc.WindOffshoreDiscipline'

# if want to modify the capex of both onshore and offshore
# dict_techno_dict_default = {model_name_onshore: WindOnshoreDiscipline.techno_infos_dict_default,
#                            model_name_offshore: WindOffshoreDiscipline.techno_infos_dict_default}
techno_info_dict_default = WindOnshoreDiscipline.techno_infos_dict_default
Capex_init0 = WindOnshoreDiscipline.techno_infos_dict_default['Capex_init']

# recover the input data of the discipline from the iea nze scenario
with open('dm_iea_nze.pkl', 'rb') as f:
            dm = pickle.load(f)
f.close()
inputs_dict = deepcopy(dm)
inputs_dict.update({f'{name}.{GlossaryEnergy.CO2TaxesValue}': inputs_dict.pop(f'usecase_witness_optim_nze_eval.WITNESS_MDO.WITNESS_Eval.WITNESS.{GlossaryEnergy.CO2TaxesValue}')})
inputs_dict.update({f'{name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': inputs_dict.pop(f'usecase_witness_optim_nze_eval.WITNESS_MDO.WITNESS_Eval.WITNESS.EnergyMix.{GlossaryEnergy.StreamsCO2EmissionsValue}')})
inputs_dict.update({f'{name}.{GlossaryEnergy.StreamPricesValue}': inputs_dict.pop(f'usecase_witness_optim_nze_eval.WITNESS_MDO.WITNESS_Eval.WITNESS.EnergyMix.{GlossaryEnergy.StreamPricesValue}')})
inputs_dict.update({f'{name}.{GlossaryEnergy.ResourcesPriceValue}': inputs_dict.pop(f'usecase_witness_optim_nze_eval.WITNESS_MDO.WITNESS_Eval.WITNESS.EnergyMix.{GlossaryEnergy.ResourcesPriceValue}')})
inputs_dict.update({f'{name}.{GlossaryEnergy.TransportCostValue}': inputs_dict.pop(f'usecase_witness_optim_nze_eval.WITNESS_MDO.WITNESS_Eval.WITNESS.EnergyMix.electricity.{GlossaryEnergy.TransportCostValue}')})

# initial_production from IEA is split between windonshore and windoffshore following arbitrary ratio
init_prod_onshore_over_offshore = 1508. / 107.69  # taken from initial witness results
initial_prod = df_prod_iea.loc[df_prod_iea[GlossaryEnergy.Years] == year_start]['electricity (TWh)'].values[0]
init_prod_dict = {
    model_name_onshore: initial_prod * init_prod_onshore_over_offshore / (1. + init_prod_onshore_over_offshore),
    model_name_offshore: initial_prod / (1. + init_prod_onshore_over_offshore)}
ratio_invest_onshore_offshore = 3.6689  # taken from initial witness results


def run_model(x: list, year_end: int = year_end):
    techno_info_dict_default['Capex_init'] = Capex_init0 * x[0]
    invest_before_year_start = x[1:construction_delay + 1] * invest_year_start
    invest_years_optim = x[construction_delay + 1:] * invest_year_start
    # interpolate on missing years using bspline as in sostrades-core
    list_t = np.linspace(0.0, 1.0, len(years))
    bspline = BSpline(n_poles=len(years_optim))
    bspline.set_ctrl_pts(invest_years_optim)
    invests, b_array = bspline.eval_list_t(list_t)
    invest_df = pd.DataFrame({GlossaryEnergy.Years: years,
                                                          GlossaryCore.InvestValue: list(invests)})
    invest_before_year_start_df = pd.DataFrame({GlossaryEnergy.Years: np.arange(year_start - construction_delay, year_start),
                  GlossaryEnergy.InvestValue: invest_before_year_start})
    # split investment between onshore and offshore
    for df in [invest_df, invest_before_year_start_df]:
        df[model_name_onshore] = df[GlossaryCore.InvestValue] * ratio_invest_onshore_offshore / (1. + ratio_invest_onshore_offshore)
        df[model_name_offshore] = df[GlossaryCore.InvestValue] / (1. + ratio_invest_onshore_offshore)

    ee = ExecutionEngine(name)
    ee.ns_manager.add_ns_def(ns_dict)
    builder = []
    builder.append(ee.factory.get_builder_from_module(
        model_name_onshore, mod_path_onshore))
    builder.append(ee.factory.get_builder_from_module(
        model_name_offshore, mod_path_offshore))
    ee.factory.set_builders_to_coupling_builder(builder)

    ee.configure()
    # ee.display_treeview_nodes()

    inputs_dict.update({
        f'{name}.{GlossaryEnergy.YearStart}': year_start,
        f'{name}.{GlossaryEnergy.YearEnd}': year_end,
        f'{name}.{model_name_onshore}.techno_infos_dict': techno_info_dict_default,
    })
    for model_name in [model_name_offshore, model_name_onshore]:
        inputs_dict.update({
        # f'{name}.{model_name}.{GlossaryEnergy.InitialPlantsAgeDistribFactor}': init_age_distrib_factor,
        f'{name}.{model_name}.initial_production': init_prod_dict[model_name],
        f'{name}.{model_name}.{GlossaryEnergy.InvestLevelValue}': pd.DataFrame({GlossaryEnergy.Years: years, GlossaryCore.InvestValue: invest_df[model_name].values}),
        f'{name}.{model_name}.{GlossaryEnergy.InvestmentBeforeYearStartValue}': pd.DataFrame({GlossaryEnergy.Years: np.arange(year_start - construction_delay, year_start),
                  GlossaryEnergy.InvestValue: invest_before_year_start_df[model_name].values}),
        })

    ee.load_study_from_input_dict(inputs_dict)

    ee.execute()

    # put electricity production for both wind techno energies in a single dataframe
    df_prod_names = ee.dm.get_all_namespaces_from_var_name(GlossaryEnergy.TechnoProductionValue)
    df_prod_list = [ee.dm.get_value(df_prod_names[i]).rename(columns={"electricity (TWh)": df_prod_names[i]}) for i in range(len(df_prod_names))]  # PWh
    df_prod = reduce(lambda left, right: pd.merge(left, right, on=GlossaryEnergy.Years), df_prod_list)
    # compute the sum of onshore and offshore technos:
    df_prod['electricity (TWh)'] = df_prod.drop(GlossaryEnergy.Years, axis=1).sum(axis=1) * 1000.  # PWh
    df_prod_model = df_prod.loc[df_prod[GlossaryEnergy.Years].isin(years_IEA_interpolated)]

    price_df = ee.dm.get_value(f"{name}.{model_name}.{GlossaryEnergy.TechnoPricesValue}")

    return df_prod, price_df, df_prod_model, invest_df, ee


def fitting_renewable(x: list):
    df_prod, price_df, df_prod_model, invest_df, ee = run_model(x)
    price_iea_values = df_price_iea['WindOnshore'].values
    years_price_iea = df_price_iea['years'].values
    price_model_values = (price_df.loc[price_df[GlossaryEnergy.Years].isin(years_price_iea), f"{GlossaryEnergy.WindOnshore}_wotaxes"]).values

    return ((((df_prod_model['electricity (TWh)'].values - prod_IEA_interpolated) / prod_IEA_interpolated.mean()) ** 2).mean() + (((price_model_values - price_iea_values) / price_iea_values.mean()) ** 2).mean())


# Initial guess for the variables invest from year 2025 to 2100.
x0 = np.concatenate((np.array([1.]), np.array([0.]), 80. / invest_year_start * np.ones(construction_delay - 1), np.ones(len(years_optim))))
bounds = [(0.5, 1.5)] + [(0., 0.)] + [(80. / invest_year_start / 2., 80. / invest_year_start * 2.)] * (construction_delay - 1) + (len(years_optim)) * [(1. / 10., 10.)]

# Use minimize to find the minimum of the function
result = minimize(fitting_renewable, x0, bounds=bounds)

df_prod, price_df, df_prod_model, invest_df, ee = run_model(result.x)

# Print the result
print("Function value at the optimum:", result.fun)
print('Capex_init wind onshore:', result.x[0] * Capex_init0)
print("invest before year start", result.x[1:construction_delay + 1] * invest_year_start)
print("invest at the poles at the optimum", result.x[construction_delay + 1:] * invest_year_start)


new_chart = TwoAxesInstanciatedChart('years', 'production (TWh)',
                                     chart_name='Windpower Production : witness vs IEA')


serie = InstanciatedSeries(list(years_IEA_interpolated), df_prod_model['electricity (TWh)'].values, 'model', 'lines')
new_chart.series.append(serie)

serie = InstanciatedSeries(years_IEA, df_prod_iea['electricity (TWh)'].values, 'IEA', 'scatter')
new_chart.series.append(serie)
serie = InstanciatedSeries(list(years_IEA_interpolated), list(prod_IEA_interpolated), 'IEA_interpolated', 'lines+markers')
new_chart.series.append(serie)

new_chart.to_plotly().show()

new_chart = TwoAxesInstanciatedChart('years', 'invest (G$)',
                                     chart_name='Windpower investments')
serie = InstanciatedSeries(list(years_optim), list(result.x[construction_delay + 1:] * invest_year_start), 'invests_at_poles', 'scatter')
new_chart.series.append(serie)
serie = InstanciatedSeries(list(years), list(invest_df[GlossaryEnergy.InvestValue]), 'invests', 'lines')
new_chart.series.append(serie)

new_chart.to_plotly().show()

new_chart = TwoAxesInstanciatedChart('years', 'Price ($/MWh)',
                                     chart_name='Wind Onshore price')
serie = InstanciatedSeries(list(df_price_iea['years'].values), list(df_price_iea['WindOnshore'].values), 'IEA', 'scatter')
new_chart.series.append(serie)
# in witness vs iea post -processing, take f"{GlossaryEnergy.WindOnshore}" but same value
serie = InstanciatedSeries(list(years), list(price_df[f"{GlossaryEnergy.WindOnshore}_wotaxes"].values), 'Witness', 'lines')
new_chart.series.append(serie)

new_chart.to_plotly().show()

for model_name in [model_name_offshore, model_name_onshore]:
    disc = ee.dm.get_disciplines_with_name(
                f'{name}.{model_name}')[0]
    filters = disc.get_chart_filter_list()
    graph_list = disc.get_post_processing_list(filters)
    for graph in graph_list:
        graph.to_plotly().show()
        pass

# export csv with correct unit, ie multiply by 1000
models_path_abs = os.path.dirname(os.path.abspath(__file__)).split(os.sep + "models")[0]
invest_mix_csv = os.path.join(models_path_abs, 'models', 'witness-core', 'climateeconomics', 'sos_processes', 'iam', 'witness', 'witness_optim_process', 'data', 'investment_mix.csv')
df_invest_mix = pd.read_csv(invest_mix_csv)
df_prod_names = ee.dm.get_all_namespaces_from_var_name(GlossaryEnergy.TechnoProductionValue)
for name in df_prod_names:
    if 'WindOffshore' in name:
        df_invest_mix['electricity.WindOffshore'] = invest_df['WindOffshore']
    elif 'WindOnshore' in name:
        df_invest_mix['electricity.WindOnshore'] = invest_df['WindOnshore']
df_invest_mix.to_csv(invest_mix_csv, index=False, sep=',')
# values to set in the invest_design_space_NZE.csv
print(f"invest at poles for WindOnshore={result.x[construction_delay + 1:] * invest_year_start * ratio_invest_onshore_offshore / (1. + ratio_invest_onshore_offshore)}")
print(f"invest at poles for WindOffshore={result.x[construction_delay + 1:] * invest_year_start / (1. + ratio_invest_onshore_offshore)}")
print(f"invest before year start for WindOnshore={result.x[1:construction_delay + 1] * invest_year_start * ratio_invest_onshore_offshore / (1. + ratio_invest_onshore_offshore)}")
print(f"invest before year start for WindOffshore={result.x[1:construction_delay + 1] * invest_year_start / (1. + ratio_invest_onshore_offshore)}")
