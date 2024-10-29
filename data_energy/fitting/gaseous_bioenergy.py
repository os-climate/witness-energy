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
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.interpolate import interp1d
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import (
    InstanciatedSeries,
    TwoAxesInstanciatedChart,
)

from energy_models.glossaryenergy import GlossaryEnergy
from climateeconomics.glossarycore import GlossaryCore

"""
This script is used to calibrate the gaseous bioenergy invest so that the energy production matches the IEA NZE scenario
production values between 2020 and 2050
"""

year_start = 2020
year_end = 2100
years_IEA = [2020, 2025, 2030, 2035, 2040, 2045, 2050, 2100]
# increase discretization in order to smooth production between 2020 and 2030
years_optim = sorted(list(set(years_IEA + list(np.arange(year_start, max(year_start, 2030) + 1)))))
years = np.arange(year_start, year_end + 1)

# source: IEA report NZE2021Ch02
# energy(2100) = max worldwide potential = between 5000 to 15000 TWh if dedicated short rotation wood are considered (chatgpt). 5000 TWh is arbitrarily chosen
models_path_abs = os.path.dirname(os.path.abspath(__file__)).split(os.sep + "models")[0]
df_prod_iea = pd.read_csv(
    os.path.join(models_path_abs, 'models', 'witness-core', 'climateeconomics', 'data', 'IEA_NZE_EnergyMix.biogas.energy_production_detailed.csv'))
new_row = pd.DataFrame({'years': [2100], "biogas AnaerobicDigestion (TWh)": [5000.]})
df_prod_iea = pd.concat([df_prod_iea, new_row], ignore_index=True)
invest_year_start = 3.432 #G$

name = 'Test'
model_name = GlossaryEnergy.AnaerobicDigestion
ns_dict = {'ns_public': name,
           'ns_energy': name,
           'ns_energy_study': f'{name}',
           'ns_biogas': f'{name}',
           'ns_resource': name}
mod_path = 'energy_models.models.biogas.anaerobic_digestion.anaerobic_digestion_disc.AnaerobicDigestionDiscipline'
ee = ExecutionEngine(name)
ee.ns_manager.add_ns_def(ns_dict)
builder = ee.factory.get_builder_from_module(
    model_name, mod_path)

ee.factory.set_builders_to_coupling_builder(builder)

ee.configure()
ee.display_treeview_nodes()


def run_model(x: list, year_end: int = year_end):
    init_age_distrib_factor = x[0]
    invest_years_optim = x[1:]
    # interpolate on missing years
    f = interp1d(years_optim, invest_years_optim, kind='linear')
    invests = f(years)
    invest_df = pd.DataFrame({GlossaryEnergy.Years: years,
                                                          GlossaryCore.InvestValue: list(invests)})

    inputs_dict = {
        f'{name}.{GlossaryEnergy.YearStart}': year_start,
        f'{name}.{GlossaryEnergy.YearEnd}': year_end,
        f'{name}.{model_name}.{GlossaryEnergy.InvestLevelValue}': invest_df,
        f'{name}.{GlossaryEnergy.CO2TaxesValue}': pd.DataFrame(
            {GlossaryEnergy.Years: years, GlossaryEnergy.CO2Tax: np.linspace(0., 0., len(years))}),
        f'{name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': pd.DataFrame({GlossaryEnergy.Years: years, GlossaryEnergy.electricity: np.zeros_like(years), GlossaryEnergy.WetBiomassResource: np.zeros_like(years)}),
        f'{name}.{GlossaryEnergy.StreamPricesValue}': pd.DataFrame({GlossaryEnergy.Years: years, GlossaryEnergy.electricity: np.zeros_like(years), GlossaryEnergy.WetBiomassResource: np.zeros_like(years)}),
        f'{name}.{GlossaryEnergy.ResourcesPriceValue}': pd.DataFrame({GlossaryEnergy.Years: years, GlossaryEnergy.electricity: np.zeros_like(years), GlossaryEnergy.WetBiomassResource: np.zeros_like(years)}),
        f'{name}.{GlossaryEnergy.TransportCostValue}': pd.DataFrame({GlossaryEnergy.Years: years, 'transport': np.zeros(len(years))}),
        f'{name}.{model_name}.{GlossaryEnergy.InitialPlantsAgeDistribFactor}': init_age_distrib_factor,
        f'{name}.{model_name}.initial_production': df_prod_iea.loc[df_prod_iea[GlossaryEnergy.Years] == year_start]["biogas AnaerobicDigestion (TWh)"].values[0]
    }

    # must load the dict twice, otherwise values are not taken into account
    ee.load_study_from_input_dict(inputs_dict)
    ee.load_study_from_input_dict(inputs_dict)

    ee.execute()

    prod_df = ee.dm.get_value(ee.dm.get_all_namespaces_from_var_name(GlossaryEnergy.TechnoProductionValue)[0]) #PWh
    prod_values_model = prod_df.loc[prod_df[GlossaryEnergy.Years].isin(years_IEA), "biogas (TWh)"].values * 1000. #TWh

    return prod_values_model, prod_df[[GlossaryEnergy.Years, "biogas (TWh)"]], invest_df


def fitting_renewable(x: list):
    prod_values_model, prod_df, invest_df = run_model(x)
    return (((prod_values_model - df_prod_iea["biogas AnaerobicDigestion (TWh)"].values)) ** 2).mean()


# Initial guess for the variables invest from year 2025 to 2100.
x0 = np.concatenate((np.array([1.0]), invest_year_start * np.ones(len(years_optim))))
bounds = [(1., 2.)] + (len(years_optim)) * [(invest_year_start/10., 10.0 * invest_year_start)]

# Use minimize to find the minimum of the function
result = minimize(fitting_renewable, x0, bounds=bounds)

prod_values_model, prod_df, invest_df = run_model(result.x)

# Print the result
print("Function value at the optimum:", result.fun)
print("init age distrib at the optimum", result.x[0])
print("invest at the optimum", result.x[1:])
print("prod at the optimum", prod_values_model)


new_chart = TwoAxesInstanciatedChart('years', 'production (TWh)',
                                     chart_name='Production : model vs historic')


serie = InstanciatedSeries(years_IEA, prod_values_model, 'model', 'lines')
new_chart.series.append(serie)

serie = InstanciatedSeries(years_IEA, df_prod_iea["biogas AnaerobicDigestion (TWh)"].values, 'historic', 'lines')
new_chart.series.append(serie)

new_chart.to_plotly().show()

new_chart = TwoAxesInstanciatedChart('years', 'invest (G$)',
                                     chart_name='investments')
serie = InstanciatedSeries(years_IEA, list(result.x)[1:], 'invests', 'lines')
new_chart.series.append(serie)

new_chart.to_plotly().show()

disc = ee.dm.get_disciplines_with_name(
            f'{name}.{model_name}')[0]
filters = disc.get_chart_filter_list()
graph_list = disc.get_post_processing_list(filters)
for graph in graph_list:
    #graph.to_plotly().show()
    pass

# update the invest_mix values with correct unit, ie divide by 1000
invest_mix_csv = os.path.join(models_path_abs, 'models', 'witness-core', 'climateeconomics', 'sos_processes', 'iam', 'witness', 'witness_optim_process', 'data', 'investment_mix.csv')
df_invest_mix = pd.read_csv(invest_mix_csv)
df_invest_mix['biogas.AnaerobicDigestion'] = invest_df[GlossaryCore.InvestValue]
df_invest_mix.to_csv(invest_mix_csv, index=False, sep=',')