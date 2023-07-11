import pandas as pd
from sostrades_core.tools.post_processing.tables.instanciated_table import InstanciatedTable

def get_comparision_data(execution_engine, namespace, year):

    '''
    Extracting Capex, Opex, CO2_Tax and total price from data manager for all technologies in the techno list
    '''

    var_f_name = f"{namespace}.technologies_list"
    techno_list = execution_engine.dm.get_value(var_f_name)

    capex_list = []
    opex_list = []
    energy_costs_List = []
    for techno in techno_list:
        techno_prices_f_name = f"{namespace}.{techno}.techno_detailed_prices" #	"energy_detailed_techno_prices" for Hydrogen and Fuel
        price_details = execution_engine.dm.get_value(techno_prices_f_name)

        filtereddata = price_details[price_details['years']] # Filtering data for a year of 2023
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










































































