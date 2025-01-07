'''
Copyright 2023 Capgemini

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
from plotly import graph_objects as go
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.plotly_native_charts.instantiated_plotly_native_chart import (
    InstantiatedPlotlyNativeChart,
)

from energy_models.glossaryenergy import GlossaryEnergy

YEAR_COMPARISON = [2023, 2050]
DECIMAL = 2


def post_processing_filters(execution_engine, namespace):
    '''
    WARNING : the execution_engine and namespace arguments are necessary to retrieve the filters
    '''
    filters = []
    chart_list = []
    energy = execution_engine.dm.get_disciplines_with_name(namespace)[
        0].discipline_wrapp.wrapper.energy_name
    chart_list += [f'{energy} Capex value']

    # The filters are set to False by default since the graphs are not yet
    # mature
    filters.append(ChartFilter('Charts', chart_list, chart_list, 'Charts'))

    return filters


def get_techno_price_data(execution_engine, namespace, title, price_name, y_label):
    '''
    Extracting Capex, Opex, CO2_Tax and total price from data manager for all technologies in the techno list
    '''

    var_f_name = f"{namespace}.technologies_list"
    techno_list = execution_engine.dm.get_value(var_f_name)

    techno_price_data = {}

    for techno in techno_list:
        techno_prices_f_name = f"{namespace}.{techno}.techno_detailed_prices"  # "energy_detailed_techno_prices" for Hydrogen and Fuel
        price_details = execution_engine.dm.get_value(techno_prices_f_name)
        year_list = price_details[GlossaryEnergy.Years].tolist()
        capex_list = price_details['CAPEX_Part'].tolist()
        opex_list = price_details['OPEX_Part'].tolist()
        CO2tax_list = price_details['CO2Tax_Part'].tolist()
        energy_costs_List = price_details[techno].tolist()

        if price_name == 'CAPEX_Part':
            techno_price_data[techno] = capex_list
        elif price_name == 'OPEX_Part':
            techno_price_data[techno] = opex_list
        elif price_name == 'CO2Tax_Part':
            techno_price_data[techno] = CO2tax_list
        else:
            techno_price_data[techno] = energy_costs_List

    key_list = list(techno_price_data.keys())
    initial_y_values = []
    for key in techno_price_data.keys():
        initial_y_values.append(techno_price_data[key][0])

        trace = go.Bar(
            x=key_list,
            y=initial_y_values,
            marker=dict(
                # set color equal to a variable
                color=initial_y_values,
                cmin=min(initial_y_values), cmax=max(initial_y_values),
                # one of plotly color scales
                colorscale='RdYlGn_r',
                # enable color scale
                showscale=True,
                colorbar=dict(title=y_label, thickness=20),
            )
        )

    steps = []
    for i in range(len(year_list)):
        y_values = []
        for key in techno_price_data.keys():
            y_values.append(techno_price_data[key][i])
        step = dict(
            method='update',
            args=[{
                'x[0]': key_list,  # [[i] for i in list(techno_price_data.keys())],
                'y': [y_values],
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

    fig = go.Figure(data=[trace], layout=layout)

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
    energy = execution_engine.dm.get_disciplines_with_name(namespace)[0].discipline_wrapp.wrapper.energy_name
    if f'{energy} Capex value' in graphs_list:
        capex_bar_slider_graph = get_techno_price_data(execution_engine, namespace, title, 'CAPEX_Part', 'Capex')
        instanciated_charts.append(capex_bar_slider_graph)

    title = split_title[len(split_title) - 1] + ' Opex Price'
    energy = execution_engine.dm.get_disciplines_with_name(namespace)[0].discipline_wrapp.wrapper.energy_name
    if f'{energy} Capex value' in graphs_list:
        opex_bar_slider_graph = get_techno_price_data(execution_engine, namespace, title, 'OPEX_Part', 'Opex')
        instanciated_charts.append(opex_bar_slider_graph)

    title = split_title[len(split_title) - 1] + ' Total Price'
    energy = execution_engine.dm.get_disciplines_with_name(namespace)[0].discipline_wrapp.wrapper.energy_name
    if f'{energy} Capex value' in graphs_list:
        total_price_slider_graph = get_techno_price_data(execution_engine, namespace, title, 'Total_Price', 'Price')
        instanciated_charts.append(total_price_slider_graph)

    return instanciated_charts
