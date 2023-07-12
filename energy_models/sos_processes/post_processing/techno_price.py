import pandas as pd
from sostrades_core.tools.post_processing.tables.instanciated_table import InstanciatedTable
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
class InstanciatedTable:
    '''
        Extracting Capex, Opex, and total price
        '''
    def __init__(self, title, headers, data):
        self.title = title
        self.headers = headers
        self.data = data

    def print_table(self):
        print(self.title)
        df = pd.DataFrame(self.data, columns=self.headers)
        print(df)

def get_comparison_data(execution_engine, namespace, years):
    var_f_name = f"{namespace}.technologies_list"
    techno_list = execution_engine.dm.get_value(var_f_name)

    if techno_list is None:
        raise ValueError("La liste des technologies est manquante ou vide.")

    headers = ['Technology', 'Year', 'CAPEX ($/MWh)', 'OPEX ($/MWh)', 'Price ($/MWh)']
    data = []

    if isinstance(years, int):
        years = [years]  # Convertir en liste si years est un entier unique

    for techno in techno_list:
        for year in years:
            techno_prices_f_name = f"{namespace}.{techno}.techno_detailed_prices"
            price_details = execution_engine.dm.get_value(techno_prices_f_name)

            if price_details is not None:
                filtered_data = price_details[price_details['years'] == year]
                if not filtered_data.empty:
                    capex_price = filtered_data['CAPEX_Part'].iloc[0]
                    opex_price = filtered_data['OPEX_Part'].iloc[0]
                    price = filtered_data[techno].iloc[0]

                    row = [techno, year, capex_price, opex_price, price]
                    data.append(row)

    table = InstanciatedTable('Data Comparison', headers, data)
    return table

#"------------------------------------------------------"
'''
    Example of test 
    '''
class DummyExecutionEngine:
    def __init__(self):
        self.dm = DummyDataManager()

class DummyDataManager:
    def get_value(self, var_name):
        # Renvoie des données factices pour les tests
        if var_name == 'dummy_namespace.technologies_list':
            return ['Tech1', 'Tech2', 'Tech3']
        elif var_name == 'dummy_namespace.Tech1.techno_detailed_prices':
            return dummy_price_data('Tech1')
        elif var_name == 'dummy_namespace.Tech2.techno_detailed_prices':
            return dummy_price_data('Tech2')
        elif var_name == 'dummy_namespace.Tech3.techno_detailed_prices':
            return dummy_price_data('Tech3')

def dummy_price_data(techno):
    # Renvoie des données factices pour les prix détaillés d'une technologie
    return pd.DataFrame({
        'years': [2020, 2021, 2022],
        'CAPEX_Part': [100, 200, 300],
        'OPEX_Part': [10, 20, 30],
        techno: [50, 100, 150]
    })

# Crée une instance du moteur d'exécution fictif
execution_engine = DummyExecutionEngine()

# Définit le namespace et la liste des années
namespace = 'dummy_namespace'
years = [2020, 2021, 2022]

# Appelle la fonction get_comparison_data
table = get_comparison_data(execution_engine, namespace, years)

# Affiche la table
table.print_table()