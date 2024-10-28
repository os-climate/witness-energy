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
This script is used to calibrate the hydropower invest so that the electricity production matches the IEA NZE scenario
production values between 2020 and 2050
"""

year_start = 2020
year_end = 2100
years_IEA = [2020, 2025, 2030, 2035, 2040, 2045, 2050, 2100]
# increase discretization in order to smooth production between 2020 and 2030
years_optim = sorted(list(set(years_IEA + list(np.arange(year_start, max(year_start, 2030) + 1)))))
years = np.arange(year_start, year_end + 1)

# source: IEA report NZE2021Ch02
# energy(2100) = energy(2050) = physical limit of available hydroenergy if all basins, rivers, etc. are used
df_prod_iea = pd.DataFrame({GlossaryEnergy.Years: years_IEA,
                            'electricity (TWh)': [4444.3, 4999.9, 5833.2, 6666.5, 7499.8, 8055.3, 8610.9, 8610.9]})
invest_year_start = 18.957 #G$

name = 'Test'
model_name = GlossaryEnergy.Hydropower
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
        f'{name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': pd.DataFrame({GlossaryEnergy.Years: years}),
        f'{name}.{GlossaryEnergy.StreamPricesValue}': pd.DataFrame({GlossaryEnergy.Years: years}),
        f'{name}.{GlossaryEnergy.ResourcesPriceValue}': pd.DataFrame({GlossaryEnergy.Years: years}),
        f'{name}.{GlossaryEnergy.TransportCostValue}': pd.DataFrame({GlossaryEnergy.Years: years, 'transport': np.zeros(len(years))}),
        f'{name}.{model_name}.{GlossaryEnergy.InitialPlantsAgeDistribFactor}': init_age_distrib_factor,
        f'{name}.{model_name}.initial_production': df_prod_iea.loc[df_prod_iea[GlossaryEnergy.Years] == year_start]['electricity (TWh)'].values[0]
    }

    ee.load_study_from_input_dict(inputs_dict)

    ee.execute()

    prod_df = ee.dm.get_value(ee.dm.get_all_namespaces_from_var_name(GlossaryEnergy.TechnoProductionValue)[0]) #PWh
    prod_values_model = prod_df.loc[prod_df[GlossaryEnergy.Years].isin(years_IEA), "electricity (TWh)"].values * 1000. #TWh

    return prod_values_model, prod_df[[GlossaryEnergy.Years, "electricity (TWh)"]], invest_df


def fitting_renewable(x: list):
    prod_values_model, prod_df, invest_df = run_model(x)
    return (((prod_values_model - df_prod_iea['electricity (TWh)'].values)) ** 2).mean()


# Initial guess for the variables invest from year 2025 to 2100.
x0 = np.concatenate((np.array([1.6]), invest_year_start * np.ones(len(years_optim))))
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

serie = InstanciatedSeries(years_IEA, df_prod_iea['electricity (TWh)'].values, 'historic', 'lines')
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
    graph.to_plotly().show()
    pass

# export csv with correct unit, ie multiply by 1000

invest_df.to_csv('invest_hydropower_iea_nze_Gdollars.csv', index=False, sep=',', float_format='%.3f')