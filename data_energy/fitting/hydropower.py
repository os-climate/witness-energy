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

"""
This script is used to calibrate the hydropower invest so that the electricity production matches the IEA NZE scenario
production values between 2020 and 2050
"""

year_start = 2020
year_end = 2100
years_IEA = [2020, 2025, 2030, 2035, 2040, 2045, 2050, 2100]
years = np.arange(year_start, year_end + 1)
construction_delay = GlossaryEnergy.TechnoConstructionDelayDict['Hydropower']

# source: IEA report NZE2021Ch02
# energy(2100) = energy(2050) = physical limit of available hydroenergy if all basins, rivers, etc. are used
df_prod_iea = pd.DataFrame({GlossaryEnergy.Years: years_IEA,
                            'electricity (TWh)': [4444.3, 4999.9, 5833.2, 6666.5, 7499.8, 8055.3, 8610.9, 8610.9]})
initial_production = df_prod_iea.loc[df_prod_iea[GlossaryEnergy.Years] == year_start]['electricity (TWh)'].values[0]
# interpolate data between 2050 and 2100
years_IEA_interpolated = years
f = interp1d(years_IEA, df_prod_iea['electricity (TWh)'].values, kind='linear')
prod_IEA_interpolated = f(years_IEA_interpolated)

# increase discretization in order to smooth production between 2020 and 2030
years_optim = np.linspace(year_start, year_end, 8)  # np.arange(years_IEA[0], years_IEA[-1] + 1, 5) #years_IEA_interpolated #sorted(list(set(years_IEA_interpolated + list(np.arange(year_start, max(year_start, 2030) + 1)))))
invest_year_start = 18.957  # G$

name = 'usecase_witness_optim_nze_eval'
model_name = f"MDO.WITNESS_Eval.WITNESS.EnergyMix.electricity.{GlossaryEnergy.Hydropower}"

# recover the input data of the discipline from the iea nze scenario
with open('dm_iea_nze.pkl', 'rb') as f:
            dm = pickle.load(f)
f.close()
inputs_dict = deepcopy(dm)
inputs_dict.update({f'{name}.{GlossaryEnergy.CO2TaxesValue}': inputs_dict.pop(f'usecase_witness_optim_nze_eval.MDO.WITNESS_Eval.WITNESS.{GlossaryEnergy.CO2TaxesValue}')})
inputs_dict.update({f'{name}.{GlossaryEnergy.StreamsGHGEmissionsValue}': inputs_dict.pop(f'usecase_witness_optim_nze_eval.MDO.WITNESS_Eval.WITNESS.EnergyMix.{GlossaryEnergy.StreamsGHGEmissionsValue}')})
inputs_dict.update({f'{name}.{GlossaryEnergy.StreamPricesValue}': inputs_dict.pop(f'usecase_witness_optim_nze_eval.MDO.WITNESS_Eval.WITNESS.EnergyMix.{GlossaryEnergy.StreamPricesValue}')})
inputs_dict.update({f'{name}.{GlossaryEnergy.ResourcesPriceValue}': inputs_dict.pop(f'usecase_witness_optim_nze_eval.MDO.WITNESS_Eval.WITNESS.EnergyMix.{GlossaryEnergy.ResourcesPriceValue}')})
inputs_dict.update({f'{name}.{GlossaryEnergy.TransportCostValue}': inputs_dict.pop(f'usecase_witness_optim_nze_eval.MDO.WITNESS_Eval.WITNESS.EnergyMix.biogas.{GlossaryEnergy.TransportCostValue}')})


def run_model(x: list, year_end: int = year_end):
    init_prod = x[0] * initial_production
    invest_before_year_start = x[1:1 + construction_delay] * invest_year_start
    invest_years_optim = x[1 + construction_delay:] * invest_year_start
    # interpolate on missing years using bspline as in sostrades-core
    list_t = np.linspace(0.0, 1.0, len(years))
    bspline = BSpline(n_poles=len(years_optim))
    bspline.set_ctrl_pts(invest_years_optim)
    invests, b_array = bspline.eval_list_t(list_t)
    invest_df = pd.DataFrame({GlossaryEnergy.Years: years,
                                                          GlossaryCore.InvestValue: list(invests)})

    ee = ExecutionEngine(name)
    ns_dict = {'ns_public': name,
               'ns_energy': name,
               'ns_energy_study': f'{name}',
               'ns_electricity': name,
               'ns_resource': name}
    ee.ns_manager.add_ns_def(ns_dict)

    mod_path = 'energy_models.models.electricity.hydropower.hydropower_disc.HydropowerDiscipline'
    builder = ee.factory.get_builder_from_module(
        model_name, mod_path)

    ee.factory.set_builders_to_coupling_builder(builder)

    ee.configure()
    # ee.display_treeview_nodes()

    inputs_dict.update({
        f'{name}.{GlossaryEnergy.YearStart}': year_start,
        f'{name}.{GlossaryEnergy.YearEnd}': year_end,
        f'{name}.{model_name}.{GlossaryEnergy.InvestLevelValue}': invest_df,
        # f'{name}.{model_name}.{GlossaryEnergy.InitialPlantsAgeDistribFactor}': init_age_distrib_factor,
        f'{name}.{model_name}.initial_production': init_prod,
        f'{name}.{model_name}.{GlossaryEnergy.InvestmentBeforeYearStartValue}': pd.DataFrame(
            {GlossaryEnergy.Years: np.arange(year_start - construction_delay, year_start),
             GlossaryEnergy.InvestValue: invest_before_year_start}),
    })
    ee.load_study_from_input_dict(inputs_dict)

    ee.execute()

    prod_df = ee.dm.get_value(ee.dm.get_all_namespaces_from_var_name(GlossaryEnergy.TechnoProductionValue)[0])  # PWh

    return prod_df[[GlossaryEnergy.Years, "electricity (TWh)"]], invest_df, ee


def fitting_renewable(x: list):
    prod_df, invest_df, ee = run_model(x)
    prod_values_model = prod_df.loc[prod_df[GlossaryEnergy.Years].isin(
        years_IEA_interpolated), "electricity (TWh)"].values * 1000.  # TWh
    return (((prod_values_model - prod_IEA_interpolated) / (initial_production * np.ones_like(prod_values_model))) ** 2).mean()


# Initial guess for the variables invest from year 2025 to 2100.
# there is a bug with the invest before year start => first value must be set to 0
# otherwise initial production at year start is not as expected
x0 = np.concatenate((np.array([1.]), np.array([0.]), 80. / invest_year_start * np.ones(construction_delay - 1), np.ones(len(years_optim))))
bounds = [(1., 1.)] + [(0., 0.)] + [(80. / invest_year_start / 2., 80. / invest_year_start * 2.)] * (construction_delay - 1) + (len(years_optim)) * [(1. / 10., 10.)]

# Use minimize to find the minimum of the function
result = minimize(fitting_renewable, x0, bounds=bounds,  # method='trust-constr',
                  options={'disp': True, 'maxiter': 2000, 'xtol': 1e-20})

prod_df, invest_df, ee = run_model(result.x)

# Print the result
print("Function value at the optimum:", result.fun)
print("initial production", result.x[0] * initial_production)
print("invest before year start", result.x[1:1 + construction_delay] * invest_year_start)
print("invest at the poles at the optimum", result.x[1 + construction_delay:] * invest_year_start)


new_chart = TwoAxesInstanciatedChart('years', 'hydropower production (TWh)',
                                     chart_name='witness vs IEA')


serie = InstanciatedSeries(list(prod_df[GlossaryEnergy.Years].values), list(prod_df["electricity (TWh)"].values * 1000.), 'model', 'lines')
new_chart.series.append(serie)

serie = InstanciatedSeries(years_IEA, df_prod_iea['electricity (TWh)'].values, 'IEA', 'scatter')
new_chart.series.append(serie)
serie = InstanciatedSeries(list(years_IEA_interpolated), list(prod_IEA_interpolated), 'IEA_interpolated', 'lines+markers')
new_chart.series.append(serie)

new_chart.to_plotly().show()

new_chart = TwoAxesInstanciatedChart('years', 'hydropower invest (G$)',
                                     chart_name='investments')
serie = InstanciatedSeries(list(years_optim), list(result.x[1 + construction_delay:] * invest_year_start), 'invests_at_poles', 'scatter')
new_chart.series.append(serie)
serie = InstanciatedSeries(list(years), list(invest_df[GlossaryEnergy.InvestValue]), 'invests_bspline', 'lines')
new_chart.series.append(serie)

new_chart.to_plotly().show()

disc = ee.dm.get_disciplines_with_name(
            f'{name}.{model_name}')[0]
filters = disc.get_chart_filter_list()
graph_list = disc.get_post_processing_list(filters)
for graph in graph_list:
    graph.to_plotly().show()
    pass

# export csv with correct unit, ie multiply by 1000
# update the invest_mix values with correct unit, ie multiply by 1000
models_path_abs = os.path.dirname(os.path.abspath(__file__)).split(os.sep + "models")[0]
invest_mix_csv = os.path.join(models_path_abs, 'models', 'witness-core', 'climateeconomics', 'sos_processes', 'iam', 'witness', 'witness_optim_process', 'data', 'investment_mix.csv')
df_invest_mix = pd.read_csv(invest_mix_csv)
df_invest_mix['electricity.Hydropower'] = invest_df[GlossaryCore.InvestValue]
df_invest_mix.to_csv(invest_mix_csv, index=False, sep=',')

# values to set in the invest_design_space_NZE.csv
print(f"invest at poles={result.x[1 + construction_delay:] * invest_year_start}")
