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
from sostrades_core.execution_engine.execution_engine import ExecutionEngine
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import (
    InstanciatedSeries,
    TwoAxesInstanciatedChart,
)

from energy_models.database_witness_energy import DatabaseWitnessEnergy
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.fossil.fossil_simple_techno.fossil_simple_techno_disc import (
    FossilSimpleTechnoDiscipline,
)

year_calibration = 2015

df_invest_historic = DatabaseWitnessEnergy.get_techno_invest_df(techno_name=GlossaryEnergy.FossilSimpleTechno)
df_prod_historic = DatabaseWitnessEnergy.get_techno_prod(techno_name=GlossaryEnergy.FossilSimpleTechno, year=2020)[1].value
ref_price_2023 = 121.5 # $/MWh Source: chatgpt LCOE without tax
# data to run techno
construction_delay = GlossaryEnergy.TechnoConstructionDelayDict[GlossaryEnergy.FossilSimpleTechno]
year_start_fitting = int(max(df_invest_historic['years'].min() + construction_delay, df_prod_historic['years'].min(), year_calibration))
year_end_fitting = int(min(df_invest_historic['years'].max(), df_prod_historic['years'].max()))

prod_values_historic = df_prod_historic.loc[(df_prod_historic['years'] >= year_start_fitting) & (df_prod_historic['years'] <= year_end_fitting)]['production'].values
years_fitting = list(np.arange(year_start_fitting, year_end_fitting + 1))
invest_df = df_invest_historic.loc[(df_invest_historic['years'] >= year_start_fitting) & (df_invest_historic['years'] <= year_end_fitting)]
margin = pd.DataFrame({GlossaryEnergy.Years: years_fitting, GlossaryEnergy.MarginValue: 110})
transport = pd.DataFrame({GlossaryEnergy.Years: years_fitting, 'transport': np.zeros(len(years_fitting))})
co2_taxes = pd.DataFrame({GlossaryEnergy.Years: years_fitting, GlossaryEnergy.CO2Tax: np.linspace(0., 0., len(years_fitting))})
stream_prices = pd.DataFrame({GlossaryEnergy.Years: years_fitting})
resources_price = pd.DataFrame({GlossaryEnergy.Years: years_fitting})
techno_dict_default = FossilSimpleTechnoDiscipline.techno_infos_dict_default

name = 'Test'
model_name = GlossaryEnergy.FossilSimpleTechno
ee = ExecutionEngine(name)
ns_dict = {'ns_public': name,
           'ns_energy': name,
           'ns_energy_study': f'{name}',
           'ns_fossil': name,
           'ns_resource': name}
ee.ns_manager.add_ns_def(ns_dict)

mod_path = 'energy_models.models.fossil.fossil_simple_techno.fossil_simple_techno_disc.FossilSimpleTechnoDiscipline'
builder = ee.factory.get_builder_from_module(
    model_name, mod_path)

ee.factory.set_builders_to_coupling_builder(builder)

ee.configure()
ee.display_treeview_nodes()



def run_model(x: list, year_end: int = year_end_fitting):
    techno_dict_default["Capex_init"] = x[0]
    init_age_distrib_factor = x[1]
    techno_dict_default["learning_rate"] = x[2]
    techno_dict_default["Opex_percentage"] = x[3]
    techno_dict_default["WACC"] = x[4]
    utilisation_ratio = pd.DataFrame({GlossaryEnergy.Years: years_fitting,
                                                          GlossaryEnergy.UtilisationRatioValue: x[5:]})

    inputs_dict = {
        f'{name}.{GlossaryEnergy.YearStart}': year_start_fitting,
        f'{name}.{GlossaryEnergy.YearEnd}': year_end,
        f'{name}.{GlossaryEnergy.StreamPricesValue}': stream_prices,
        f'{name}.{GlossaryEnergy.StreamsCO2EmissionsValue}': pd.DataFrame({GlossaryEnergy.Years: years_fitting}),
        f'{name}.{model_name}.{GlossaryEnergy.InvestLevelValue}': invest_df,
        f'{name}.{GlossaryEnergy.TransportMarginValue}': margin,
        f'{name}.{GlossaryEnergy.CO2TaxesValue}': co2_taxes,
        f'{name}.{GlossaryEnergy.TransportCostValue}': transport,
        f'{name}.{GlossaryEnergy.ResourcesPriceValue}': resources_price,
        f'{name}.{model_name}.{GlossaryEnergy.MarginValue}': margin,
        f'{name}.{model_name}.{GlossaryEnergy.InitialPlantsAgeDistribFactor}': init_age_distrib_factor,
        f'{name}.{model_name}.techno_infos_dict': techno_dict_default,
        f'{name}.{model_name}.{GlossaryEnergy.UtilisationRatioValue}': utilisation_ratio,
    }

    ee.load_study_from_input_dict(inputs_dict)

    ee.execute()

    prod_df = ee.dm.get_value(ee.dm.get_all_namespaces_from_var_name(GlossaryEnergy.TechnoProductionValue)[0])
    prod_values_model = prod_df["fossil (TWh)"].values * 1000

    price_df = ee.dm.get_value(ee.dm.get_all_namespaces_from_var_name(GlossaryEnergy.TechnoPricesValue)[0])

    price_model_values = float((price_df.loc[price_df[GlossaryEnergy.Years] == 2023, f"{GlossaryEnergy.FossilSimpleTechno}_wotaxes"]).values)
    return prod_values_model, price_model_values


def fitting_renewable(x: list):
    prod_values_model, price_model_values = run_model(x)
    return (((prod_values_model - prod_values_historic)) ** 2).mean() + (price_model_values - ref_price_2023) ** 2


# Initial guess for the variables
# [capex_init, init_age_distrib_factor, learnin_rate, Opex_fraction, WACC, utilization_ratio]
x0 = np.concatenate((np.array([200., 1., 0.0, 0.024, 0.058]), 100.0 * np.ones_like(years_fitting)))

# can put different lower and upper bounds for utilization ratio if want to activate it
bounds = [(0, 10000), (1.0, 1.0), (0.0, 0.0), (0.001, 0.99), (0.0001, 0.3)] + len(years_fitting) * [(100.0, 100.0)]

# Use minimize to find the minimum of the function
result = minimize(fitting_renewable, x0, bounds=bounds)

prod_values_model, price_model_values = run_model(result.x)

# Print the result
print("Function value at the optimum:", result.fun)


new_chart = TwoAxesInstanciatedChart('years', 'production (TWh)',
                                     chart_name='Production : model vs historic')


serie = InstanciatedSeries(years_fitting, prod_values_model, 'model', 'lines')
new_chart.series.append(serie)

serie = InstanciatedSeries(years_fitting, prod_values_historic, 'historic', 'lines')
new_chart.series.append(serie)

new_chart.to_plotly().show()

capex_init, init_age_distrib_factor, learning_rate, opex_percentage, wacc = result.x[0:5]
utilization_ratio = result.x[5:]
parameters = ["capex_init", "init_age_distrib_factor", "learning_rate", "opex_percentage", "wacc"]
opt_values = dict(zip(parameters, np.round(result.x, 3)))
for key, val in opt_values.items():
    print("Optimal", key, ":", val)
print("Optimal utilization_ratio", utilization_ratio)

disc = ee.dm.get_disciplines_with_name(
            f'{name}.{model_name}')[0]
filters = disc.get_chart_filter_list()
graph_list = disc.get_post_processing_list(filters)
for graph in graph_list:
    graph.to_plotly().show()
    pass

"""
Results obtained:
Function value at the optimum: 16826745.79920797 
=> less than 6% error at max between model and historic production between 2015 and 2023
=> no error on the price
Optimal capex_init : 222.638
Optimal init_age_distrib_factor : 1.0
Optimal learning_rate : 0.0
Optimal opex_percentage : 0.299
Optimal wacc : 0.0
Optimal utilization_ratio [100. 100. 100. 100. 100. 100.]
"""