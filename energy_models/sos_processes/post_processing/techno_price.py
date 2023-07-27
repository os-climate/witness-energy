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
from collections import defaultdict


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

def post_processing_filters(execution_engine, namespace):
    '''
    WARNING : the execution_engine and namespace arguments are necessary to retrieve the filters
    '''
    filters = []


    chart_list = ['Capex','Opex','Prices']


    #energy = execution_engine.dm.get_disciplines_with_name(namespace)[
     #   0].mdo_discipline_wrapp.wrapper.energy_name

    filters.append(ChartFilter('Charts', chart_list, chart_list, 'Charts'))

    return filters

def get_figures_table(table, title):
    '''
    Table chart where Capex, Opex, CO2_Tax and total price comparison
    '''
    fig = ff.create_table(table)
    new_chart = InstantiatedPlotlyNativeChart(fig, chart_name=title)

    return new_chart

def get_comparison_data(execution_engine,price_name, namespace, years,title,y_label):
    var_f_name = f"{namespace}.technologies_list"
    techno_list = execution_engine.dm.get_value(var_f_name)
    year_list = []
    headers = ['Technology', 'Year', 'CAPEX ($/MWh)', 'OPEX ($/MWh)', 'Price ($/MWh)']
    data = []

    # if isinstance(years, int):
    #     years = [years]  #Convert to list if years is a single integer
    opex_list = []
    CO2tax_list = []
    energy_costs_List = []
    techno_price_data = {}
    for techno in techno_list:
        capex_list=[]
        techno_prices_f_name = f"{namespace}.{techno}.techno_detailed_prices" #	"energy_detailed_techno_prices" for Hydrogen and Fuel
        price_details = execution_engine.dm.get_value(techno_prices_f_name)
        year_list = price_details['years'].tolist()
        for year in year_list :
            filtereddata = price_details[price_details['years'] == year]  # Filtering data for a year of 2023
        price_details = execution_engine.dm.get_value(techno_prices_f_name)
        capex_price = price_details['CAPEX_Part'].iloc[0]
        opex_price = price_details['OPEX_Part'].iloc[0]
        CO2tax_price = price_details['CO2Tax_Part'].iloc[0]
        price = price_details[techno].iloc[0]
        capex_list.append(capex_price)
        opex_list.append(opex_price)
        CO2tax_list.append(CO2tax_price)
        energy_costs_List.append(price)
        if price_name == 'CAPEX_Part':
            techno_price_data[techno] = capex_list
        elif price_name == 'OPEX_Part':
            techno_price_data[techno] = opex_list
        elif price_name == 'CO2Tax_Part':
            techno_price_data[techno] = CO2tax_list
        else:
            techno_price_data[techno] = energy_costs_List

        trace_list = []
        for key in techno_price_data.keys():
            trace1 = go.Bar(
                x=[key],
                y=[techno_price_data[key][0]],
                name=key + ' (' + str(year_list[0]) + ')',
                # offset=-0.2
            )
            trace_list.append(trace1)

        steps = []
        for i in range(len(year_list)):
            initial_y_values = []
            for key in techno_price_data.keys():
                initial_y_values.append(techno_price_data[key][i])
            step = dict(
                method='update',
                args=[{
                    'x': [[i] for i in list(techno_price_data.keys())],
                    'y[0]': initial_y_values,
                    'name': [f'{x} ({year_list[i]}) ' for x in list(techno_price_data.keys())],
                    # list(techno_price_data.keys())
                }],
                label=str(year_list[i])
            )
            steps.append(step)
        # Create slider
        sliders = [dict(
            active=0,
            pad=dict(t=10),
            steps=steps
        )]

        # Set figure layout
        layout = go.Layout(
            title=title,
            xaxis=dict(title='Technology'),
            yaxis=dict(title=y_label + ' ($/MWh)'),
            sliders=sliders,
            barmode='group'
        )

        fig = go.Figure(data=trace_list, layout=layout)

        # fig.show()
        new_chart = InstantiatedPlotlyNativeChart(
            fig, chart_name=title, default_title=True)
        return new_chart

def get_techno_price_data(execution_engine, namespace, title, price_name, y_label):

    '''
    Extracting Capex, Opex, CO2_Tax and total price from data manager for all technologies in the techno list
    '''

    var_f_name = f"{namespace}.technologies_list"
    techno_list = execution_engine.dm.get_value(var_f_name)
    # print('techno_list', techno_list)

    year_list = []
    for techno in techno_list:
        techno_prices_f_name = f"{namespace}.{techno}.techno_detailed_prices" #	"energy_detailed_techno_prices" for Hydrogen and Fuel
        price_details = execution_engine.dm.get_value(techno_prices_f_name)
        year_list = price_details['years'].tolist()

    opex_list = []
    CO2tax_list = []
    energy_costs_List = []
    techno_price_data = {}
    #x_data_list = []
    for techno in techno_list:
        capex_list = []
        techno_prices_f_name = f"{namespace}.{techno}.techno_detailed_prices" #	"energy_detailed_techno_prices" for Hydrogen and Fuel
        price_details = execution_engine.dm.get_value(techno_prices_f_name)

        for year in year_list:
            filtereddata = price_details[price_details['years'] == year] # Filtering data for a year of 2023
            capex_price = filtereddata['CAPEX_Part'].iloc[0]
            opex_price = filtereddata['OPEX_Part'].iloc[0]
            CO2tax_price = filtereddata['CO2Tax_Part'].iloc[0]
            price = filtereddata[techno].iloc[0]
            capex_list.append(capex_price)
            opex_list.append(opex_price)
            CO2tax_list.append(CO2tax_price)
            energy_costs_List.append(price)
        if price_name == 'CAPEX_Part':
            techno_price_data[techno] = capex_list
        elif price_name == 'OPEX_Part':
            techno_price_data[techno] = opex_list
        elif price_name == 'CO2Tax_Part':
            techno_price_data[techno] = CO2tax_list
        else:
            techno_price_data[techno] = energy_costs_List

    trace_list = []
    for key in techno_price_data.keys():
        trace1 = go.Bar(
            x=[key],
            y=[techno_price_data[key][0]],
            name=key + ' (' + str(year_list[0]) + ')',
            # offset=-0.2
        )
        trace_list.append(trace1)

    steps = []
    for i in range(len(year_list)):
        initial_y_values = []
        for key in techno_price_data.keys():
            initial_y_values.append(techno_price_data[key][i])
        step = dict(
            method='update',
            args=[{
                'x': [[i] for i in list(techno_price_data.keys())],
                'y[0]': initial_y_values,
                'name': [f'{x} ({year_list[i]}) ' for x in list(techno_price_data.keys())],  #list(techno_price_data.keys())
            }],
            label=str(year_list[i])
        )
        steps.append(step)
    # Create slider
    sliders = [dict(
        active=0,
        pad=dict(t=10),
        steps=steps
    )]

    # Set figure layout
    layout = go.Layout(
        title=title,
        xaxis=dict(title='Technology'),
        yaxis=dict(title=y_label +' ($/MWh)'),
        sliders=sliders,
        barmode='group'
    )


    fig = go.Figure(data=trace_list, layout=layout)


    #fig.show()
    new_chart = InstantiatedPlotlyNativeChart(
        fig, chart_name=title, default_title=True)
    return new_chart
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

    split_title = namespace.split('.')
    title = split_title[len(split_title) - 1] + ' Capex Price'
    energy = execution_engine.dm.get_disciplines_with_name(namespace)[0].mdo_discipline_wrapp.wrapper.energy_name
    if f'{energy} Capex value' in graphs_list:
        capex_bar_slider_graph = get_techno_price_data(execution_engine, namespace, title, 'CAPEX_Part', 'Capex')
        instanciated_charts.append(capex_bar_slider_graph)

    title = split_title[len(split_title) - 1] + ' Opex Price'
    energy = execution_engine.dm.get_disciplines_with_name(namespace)[0].mdo_discipline_wrapp.wrapper.energy_name
    if f'{energy} Capex value' in graphs_list:
        capex_bar_slider_graph = get_techno_price_data(execution_engine, namespace, title, 'OPEX_Part', 'Opex')
        instanciated_charts.append(capex_bar_slider_graph)

    title = split_title[len(split_title) - 1] + ' Total Price'
    energy = execution_engine.dm.get_disciplines_with_name(namespace)[0].mdo_discipline_wrapp.wrapper.energy_name
    if f'{energy} Capex value' in graphs_list:
        capex_bar_slider_graph = get_techno_price_data(execution_engine, namespace, title, 'Total_Price', 'Price')
        instanciated_charts.append(capex_bar_slider_graph)


    return instanciated_charts
