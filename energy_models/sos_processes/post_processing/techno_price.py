import pandas as pd
from sostrades_core.tools.post_processing.tables.instanciated_table import InstanciatedTable
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from plotly import figure_factory as ff
from sostrades_core.tools.post_processing.plotly_native_charts.instantiated_plotly_native_chart import \
    InstantiatedPlotlyNativeChart
import numpy as np
from plotly import graph_objects as go



YEAR_COMPARISON = [2023, 2050]
DECIMAL = 2
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
def post_processing_filters(execution_engine, namespace):
    '''
    WARNING : the execution_engine and namespace arguments are necessary to retrieve the filters
    '''
    filters = []

    chart_list = []
    energy = execution_engine.dm.get_disciplines_with_name(namespace)[
        0].mdo_discipline_wrapp.wrapper.energy_name

    filters.append(ChartFilter('Charts', chart_list, chart_list, 'Charts'))

    return filters
def get_figures_table(table, title):
    '''
    Table chart where Capex, Opex, CO2_Tax and total price comparison
    '''
    fig = ff.create_table(table)
    new_chart = InstantiatedPlotlyNativeChart(fig, chart_name=title)

    return new_chart
def get_comparison_data(execution_engine, namespace, years):
    var_f_name = f"{namespace}.technologies_list"
    techno_list = execution_engine.dm.get_value(var_f_name)

    if techno_list is None:
        raise ValueError("La liste des technologies est manquante ou vide.")

    headers = ['Technology', 'Year', 'CAPEX ($/MWh)', 'OPEX ($/MWh)', 'Price ($/MWh)']
    data = []

    if isinstance(years, int):
        years = [years]  #Convert to list if years is a single integer

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
def post_processings(execution_engine, namespace, filters):
    '''
    WARNING : the execution_engine and namespace arguments are necessary to retrieve the post_processings
    '''
    instanciated_charts = []

    # Overload default value with chart filter
    graphs_list = []
    if filters is not None:
        for chart_filter in filters:
            if chart_filter.filter_key == 'Charts':
                graphs_list.extend(chart_filter.selected_values)
    # ----

    energy = execution_engine.dm.get_disciplines_with_name(namespace)[0].mdo_discipline_wrapp.wrapper.energy_name
    if f'{energy} Figures table' in graphs_list:
        for year in YEAR_COMPARISON:
            new_table = get_comparison_data(execution_engine, namespace, year)
            #new_table = get_figures_table(price_comparision_table_data, str(year))
            instanciated_charts.append(new_table)

    if f'{energy} Capex value' in graphs_list:
        chart_name = f'{energy} Capex value'
        new_chart = get_chart_all_technologies(
            execution_engine, namespace, energy_name=energy, chart_name=chart_name)
        if new_chart is not None:
            instanciated_charts.append(new_chart)

    return instanciated_charts

def get_chart_all_technologies(execution_engine, namespace, energy_name, chart_name='Technologies Capex Value',
                                 summary=True):
    '''! Function to create the green_techno/_energy scatter chart
    @param execution_engine: Execution engine object from which the data is gathered
    @param namespace: String containing the namespace to access the data
    @param chart_name:String, title of the post_proc
    @param energy_name:String, name of the energy that the technologies produce
    @param summary:Boolean, switch from summary (True) to detailed by years via sliders (False)

    @return new_chart: InstantiatedPlotlyNativeChart Scatter plot
    '''

    # Prepare data
    multilevel_df, years = get_multilevel_df(
        execution_engine, namespace, columns=['price_per_kWh', 'years',
                                              'Capex', 'production', 'invest'])
    energy_list = list(set(multilevel_df.index.droplevel(1)))
    # Create Figure
    fig = go.Figure()
    # Get min and max CO2 emissions for colorscale and max of production for
    # marker size
    array_of_cmin, array_of_cmax, array_of_pmax, array_of_pintmax = [], [], [], []
    for (array_c, array_p) in multilevel_df[['Capex', 'production']].values:
        array_of_cmin += [array_c.min()]
        array_of_cmax += [array_c.max()]
        array_of_pmax += [array_p.max()]
        array_of_pintmax += [array_p.sum()]
    cmin, cmax = np.min(array_of_cmin), np.max(array_of_cmax)
    pmax, pintmax = np.max(array_of_pmax), np.max(array_of_pintmax)
    if summary:
        # Create a graph to aggregate the informations on all years
        price_per_kWh, years, Capex, label, production, invest, total_CO2 = [
        ], [], [], [], [], [], []
        energy_disc = execution_engine.dm.get_disciplines_with_name(namespace)[
            0]
        CO2_taxes, CO2_taxes_array = energy_disc.get_sosdisc_inputs('CO2_taxes')[
            'CO2_tax'].values, []
        for i, row in multilevel_df.iterrows():
            # skip techno that do not produce the selected energy
            if i[0] != energy_name:
                continue
            price_per_kWh += [np.mean(row['price_per_kWh']), ]
            years += [np.mean(row['years']), ]
            Capex += [np.mean(row['Capex']), ]
            label += [i, ]
            production += [np.sum(row['production']), ]
            invest += [np.sum(row['invest']), ]
            total_CO2 += [np.sum(row['Capex'] *
                                 row['production']), ]
            CO2_taxes_array += [np.mean(CO2_taxes), ]
        customdata = [label, price_per_kWh, Capex,
                      production, invest, total_CO2, CO2_taxes_array,
                      years]
        hovertemplate = ''
        marker_sizes = np.multiply(production, 20.0) / \
                       pintmax + 10.0
        scatter = go.Scatter(x=list(years), y=list(Capex),
                             customdata=list(np.asarray(customdata, dtype='object').T),
                             hovertemplate=hovertemplate,
                             text=label,
                             textposition="top center",
                             mode='markers+text',
                             marker=dict(color=Capex,
                                         cmin=cmin, cmax=cmax,
                                         colorscale='RdYlGn_r', size=list(marker_sizes),
                                         colorbar=dict(title='Capex', thickness=20)),
                             visible=True)
        fig.add_trace(scatter)
    else:
        # Fill figure with data by year
        for i_year in range(len(years)):
            ################
            # -technology level-#
            ################
            price_per_kWh, years, Capex, label, production, invest, total_CO2 = [
            ], [], [], [], [], [], []
            energy_disc = execution_engine.dm.get_disciplines_with_name(namespace)[
                0]
            CO2_taxes, CO2_taxes_array = energy_disc.get_sosdisc_inputs('CO2_taxes')[
                'CO2_tax'].values, []
            for i, row in multilevel_df.iterrows():
                # skip techno that do not produce the selected energy
                if i[0] != energy_name:
                    continue
                price_per_kWh += [row['price_per_kWh'][i_year], ]
                years += [row['years'][i_year], ]
                Capex += [row['Capex'][i_year], ]
                label += [i, ]
                production += [row['production'][i_year], ]
                invest += [row['invest'][i_year], ]
                total_CO2 += [row['Capex'][i_year] *
                              row['production'][i_year], ]
                CO2_taxes_array += [CO2_taxes[i_year], ]
            customdata = [label, price_per_kWh, Capex,
                          production, invest, total_CO2, CO2_taxes_array,
                          years]
            hovertemplate = ''
            marker_sizes = np.multiply(production, 20.0) / \
                           pmax + 10.0
            scatter = go.Scatter(x=list(years), y=list(Capex),
                                 customdata=list(np.asarray(customdata, dtype='object').T),
                                 hovertemplate=hovertemplate,
                                 text=label,
                                 textposition="top center",
                                 mode='markers+text',
                                 marker=dict(color=Capex,
                                             cmin=cmin, cmax=cmax,
                                             colorscale='RdYlGn_r', size=list(marker_sizes),
                                             colorbar=dict(title='Capex', thickness=20)),
                                 visible=False)
            fig.add_trace(scatter)
        # Prepare year slider and layout updates
        steps = []
        for i in range(int(len(fig.data)) - 1):
            step = dict(
                method="update",
                args=[{"visible": [False] * len(fig.data)}, ],
                label=str(2020 + i)
            )
            step["args"][0]["visible"][i] = True
            steps.append(step)
        sliders = [dict(
            active=0,
            currentvalue={"prefix": "Year: "},
            steps=steps), ]

        fig.update_layout(
            sliders=sliders
        )

    fig.update_xaxes(title_text='Years')
    fig.update_yaxes(title_text='Capex [$/MWh]')
    fig.data[0].visible = True

    new_chart = InstantiatedPlotlyNativeChart(
        fig, chart_name=chart_name, default_title=True)
    return new_chart

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