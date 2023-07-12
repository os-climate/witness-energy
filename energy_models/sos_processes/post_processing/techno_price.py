import pandas as pd
from sostrades_core.tools.post_processing.tables.instanciated_table import InstanciatedTable
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
def get_comparision_data(execution_engine, namespace, year):

    '''
    Extracting Capex, Opex, CO2_Tax and total price from data manager for all technologies in the techno list
    '''

    var_f_name = f"{namespace}.technologies_list"
    techno_list = execution_engine.dm.get_value(var_f_name)

    if techno_list is None:
        # Managing the case where the list of technologies is None
        raise ValueError("La liste des technologies est manquante ou vide.")

    capex_list = []
    opex_list = []
    energy_costs_List = []
    for techno in techno_list:
        techno_prices_f_name = f"{namespace}.{techno}.techno_detailed_prices" #	"energy_detailed_techno_prices" for Hydrogen and Fuel
        price_details = execution_engine.dm.get_value(techno_prices_f_name)

        filtereddata = price_details
        capex_price = filtereddata['CAPEX_Part']
        opex_price = filtereddata['OPEX_Part']
        price = filtereddata[techno]


    headers = ['Technology', 'CAPEX ($/MWh)', 'OPEX ($/MWh)', 'Price ($/MWh)']
    cells = []
    cells.append(techno_list)
    cells.append(capex_list)
    cells.append(opex_list)
    cells.append(energy_costs_List)

    table = InstanciatedTable('Data Comparison for Year ' , headers, cells)
    return table

#def get_graphs(table, title):
#     '''
#     Table chart where Capex, Opex and total price
#     '''
#
#
#     return new_chart





# def dummy_price_data(techno):
#     # Ici, tu peux renvoyer des données factices pour les prix détaillés d'une technologie
#     return {
#         'CAPEX_Part': [100, 200, 300],
#         'OPEX_Part': [10, 20, 30],
#         techno: ['a', 'b', 'c']
#     }
#
# execution_engine = ['Tech1', 'Tech2', 'Tech3']
# namespace =['a','b','c']
# year = 2023
#
# # Étape 3 : Appel de la fonction get_comparision_data
# result = get_comparision_data(execution_engine, namespace, year)
#
# # Étape 4 : Affichage de la table
# table_data = result.get_table_data()  # Obtention des données de la table
# df = pd.DataFrame(table_data[1:], columns=table_data[0])  # Conversion en DataFrame pandas
# print(df)
