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
from energy_models.models.clean_energy.clean_energy_simple_techno.clean_energy_simple_techno_disc import (
    CleanEnergySimpleTechnoDiscipline,
)

df_invest_historic = DatabaseWitnessEnergy.get_techno_invest_df(techno_name=GlossaryEnergy.CleanEnergySimpleTechno)
df_prod_historic = DatabaseWitnessEnergy.get_techno_prod(techno_name=GlossaryEnergy.CleanEnergySimpleTechno, year=2020)[1].value
ref_price_2023 = 70.76 # $/MWh
# data to run techno
construction_delay = GlossaryEnergy.TechnoConstructionDelayDict[GlossaryEnergy.CleanEnergySimpleTechno]
year_start_fitting = int(max(df_invest_historic['years'].min() + construction_delay, df_prod_historic['years'].min(), 2020))
year_end_fitting = int(min(df_invest_historic['years'].max(), df_prod_historic['years'].max()))

prod_values_historic = df_prod_historic.loc[(df_prod_historic['years'] >= year_start_fitting) & (df_prod_historic['years'] <= year_end_fitting)]['production'].values
years_fitting = list(np.arange(year_start_fitting, year_end_fitting + 1))
invest_df = df_invest_historic.loc[(df_invest_historic['years'] >= year_start_fitting) & (df_invest_historic['years'] <= year_end_fitting)]
margin = pd.DataFrame({GlossaryEnergy.Years: years_fitting, GlossaryEnergy.MarginValue: 110})
transport = pd.DataFrame({GlossaryEnergy.Years: years_fitting, 'transport': np.zeros(len(years_fitting))})
co2_taxes = pd.DataFrame({GlossaryEnergy.Years: years_fitting, GlossaryEnergy.CO2Tax: np.linspace(14., 40., len(years_fitting))})
stream_prices = pd.DataFrame({GlossaryEnergy.Years: years_fitting})
resources_price = pd.DataFrame({GlossaryEnergy.Years: years_fitting})
techno_dict_default = CleanEnergySimpleTechnoDiscipline.techno_infos_dict_default

name = 'Test'
model_name = GlossaryEnergy.CleanEnergySimpleTechno
ee = ExecutionEngine(name)
ns_dict = {'ns_public': name,
           'ns_energy': name,
           'ns_energy_study': f'{name}',
           'ns_clean_energy': name,
           'ns_resource': name}
ee.ns_manager.add_ns_def(ns_dict)

mod_path = 'energy_models.models.clean_energy.clean_energy_simple_techno.clean_energy_simple_techno_disc.CleanEnergySimpleTechnoDiscipline'
builder = ee.factory.get_builder_from_module(
    model_name, mod_path)

ee.factory.set_builders_to_coupling_builder(builder)

ee.configure()
ee.display_treeview_nodes()



def run_model(x: list, year_end: int = year_end_fitting):
    techno_dict_default["Capex_init"] = x[0]
    init_age_distrib_factor = x[1]
    #techno_dict_default["learning_rate"] = x[2]
    techno_dict_default["Opex_percentage"] = x[3]
    techno_dict_default["WACC"] = x[4]

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
    }

    ee.load_study_from_input_dict(inputs_dict)

    ee.execute()

    prod_df = ee.dm.get_value(ee.dm.get_all_namespaces_from_var_name(GlossaryEnergy.TechnoProductionValue)[0])
    prod_values_model = prod_df[f"{GlossaryEnergy.clean_energy} (TWh)"].values * 1000

    price_df = ee.dm.get_value(ee.dm.get_all_namespaces_from_var_name(GlossaryEnergy.TechnoPricesValue)[0])

    price_model_values = float((price_df.loc[price_df[GlossaryEnergy.Years] == 2023, f"{GlossaryEnergy.CleanEnergySimpleTechno}_wotaxes"]).values)
    return prod_values_model, price_model_values


def fitting_renewable(x: list):
    prod_values_model, price_model_values = run_model(x)
    return (((prod_values_model - prod_values_historic)) ** 2).mean() + (price_model_values - ref_price_2023) ** 2


# Initial guess for the variables
x0 = np.array([250., 1., 0.0, 0.2, 0.1])
#x0 = np.array([743.8, 1.3, 0.06, 0.0, 0.06])

bounds = [(0, 10000), (0, 3.0), (0.01, 0.95), (0.001, 0.99), (0.0001, 0.3)]

# Use minimize to find the minimum of the function
result = minimize(fitting_renewable, x0, bounds=bounds)

prod_values_model, price_model_values = run_model(result.x)

# Print the result
#print("Optimal solution:", result.x)
print("Function value at the optimum:", result.fun)


new_chart = TwoAxesInstanciatedChart('years', 'production (TWh)',
                                     chart_name='Production : model vs historic')


serie = InstanciatedSeries(years_fitting, prod_values_model, 'model', 'lines')
new_chart.series.append(serie)

serie = InstanciatedSeries(years_fitting, prod_values_historic, 'historic', 'lines')
new_chart.series.append(serie)

new_chart.to_plotly().show()

parameters = ["capex_init", "init_age_distrib_factor", "learning_rate", "opex_percentage", "wacc"]
opt_values = dict(zip(parameters, np.round(result.x, 2)))
for key, val in opt_values.items():
    print("Optimal", key, ":", val)

capex_init, init_age_distrib_factor, learning_rate, opex_percentage, wacc = result.x

disc = ee.dm.get_disciplines_with_name(
            f'{name}.{model_name}')[0]
filters = disc.get_chart_filter_list()
graph_list = disc.get_post_processing_list(filters)
for graph in graph_list:
    graph.to_plotly().show()
    pass