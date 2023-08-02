'''
Copyright 2022 Airbus SAS

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

from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart
from sostrades_core.tools.post_processing.plotly_native_charts.instantiated_plotly_native_chart import \
    InstantiatedPlotlyNativeChart

import numpy as np
from matplotlib.pyplot import cm
from plotly import graph_objects as go
from plotly.subplots import make_subplots
from plotly import figure_factory as ff
from sostrades_core.tools.post_processing.tables.instanciated_table import InstanciatedTable
import pandas as pd
from plotly.express.colors import qualitative

YEAR_COMPARISON = [2023, 2050]
DECIMAL = 2
# print('YEAR_COMPARISON', YEAR_COMPARISON)
def post_processing_filters(execution_engine, namespace):
    '''
    WARNING : the execution_engine and namespace arguments are necessary to retrieve the filters
    '''
    filters = []

    chart_list = []
    energy_list = []
    energy = execution_engine.dm.get_disciplines_with_name(namespace)[
        0].mdo_discipline_wrapp.wrapper.energy_name
    chart_list += [f'{energy} Figures table']

    # The filters are set to False by default since the graphs are not yet
    # mature
    filters.append(ChartFilter('Charts', chart_list, chart_list, 'Charts'))

    return filters


def get_techno_price_filter_data(execution_engine, namespace, year, title, price_name, y_label):

    '''
    Extracting Capex, Opex, CO2_Tax and total price from data manager for all technologies in the techno list
    '''
    table_list = []
    disc = execution_engine.dm.get_disciplines_with_name(namespace)
    disc_input = disc[0].get_sosdisc_inputs()
    energy_list = disc_input['energy_list']
    #print('energy_list', energy_list)
    techno_list = []
    EnergyDict = {}
    techno_production_dict = {}
    year_list = []
    energy_name_list = []

    for energ in energy_list:
        var_f_name = f"{namespace}.{energ}.technologies_list"
        var_energyproduction_name = f"{namespace}.{energ}.energy_production_detailed"

        if 'biomass_dry' not in var_f_name:
            EnergyDict[f"{energ}"] = {}
            loc_techno_list = execution_engine.dm.get_value(var_f_name)
            result = [f"{energ}." + direction for direction in loc_techno_list]
            techno_list.extend(result)
            EnergyDict[f"{energ}"]['TechnoName'] = loc_techno_list
            loc_energyproduction_df = execution_engine.dm.get_value(var_energyproduction_name)
            production_filtereddata = loc_energyproduction_df[loc_energyproduction_df['years'] == year]
            # print(list(loc_energyproduction_df.columns))
            # print(production_filtereddata.to_string())
            for col in production_filtereddata.columns:
                if col != 'years':
                    production_techno_name = col.replace(energ, '').replace('(TWh)', '').strip()
                    prod_value = production_filtereddata[col].iloc[0]
                    techno_production_dict[production_techno_name] = prod_value
        # print(techno_production_dict)

    techno_name_list = []
    for energyname in EnergyDict.keys():
        capex_average_price = 0
        opex_average_price = 0
        energy_average_price = 0
        energy_name_list.append(energyname)

    techno_price_filter_data = {}
    for techno in EnergyDict[energyname]['TechnoName']:
        techno_prices_f_name = f"{namespace}.{energyname}.{techno}.techno_detailed_prices"  # "energy_detailed_techno_prices" for Hydrogen and Fuel
        price_details = execution_engine.dm.get_value(techno_prices_f_name)
        techno_name_list.append(techno)
        year_list = price_details['years'].tolist()

        capex_list = price_details['CAPEX_Part'].tolist()
        opex_list = price_details['OPEX_Part'].tolist()
        CO2tax_list = price_details['CO2Tax_Part'].tolist()
        energy_costs_List = price_details[techno].tolist()

        if price_name == 'CAPEX_Part':
            techno_price_filter_data[techno] = capex_list
        elif price_name == 'OPEX_Part':
            techno_price_filter_data[techno] = opex_list
        elif price_name == 'CO2Tax_Part':
            techno_price_filter_data[techno] = CO2tax_list
        else:
            techno_price_filter_data[techno] = energy_costs_List
    # capex_list = []
    # opex_list = []
    # CO2tax_list = []
    # energy_costs_List = []
    # techno_name_list =[]
    # energy_name_list = []
    #
    # average_capex_list = []
    # average_opex_list = []
    # average_CO2tax_list = []
    # average_energy_costs_List = []

    # for energyname in EnergyDict.keys():
    #     total_stream_production = 0
    #     capex_average_price = 0
    #     opex_average_price = 0
    #     CO2tax_average_price = 0
    #     energy_average_price = 0
    #     energy_name_list.append(energyname)
    #
    #     for techno in EnergyDict[energyname]['TechnoName']:
    #         techno_prices_f_name = f"{namespace}.{energyname}.{techno}.techno_detailed_prices" #	"energy_detailed_techno_prices" for Hydrogen and Fuel
    #         price_details = execution_engine.dm.get_value(techno_prices_f_name)
    #         techno_name_list.append(techno)
    #         filtereddata = price_details[price_details['years'] == year]
    #         capex_price = filtereddata['CAPEX_Part'].iloc[0]
    #         opex_price = filtereddata['OPEX_Part'].iloc[0]
    #         CO2tax_price = filtereddata['CO2Tax_Part'].iloc[0]
    #         price = filtereddata[techno].iloc[0]
    #
    #         total_stream_production = total_stream_production + techno_production_dict[techno]
    #         capex_average_price = capex_average_price + capex_price * techno_production_dict[techno]
    #         opex_average_price = opex_average_price + opex_price * techno_production_dict[techno]
    #         CO2tax_average_price = CO2tax_average_price + CO2tax_price * techno_production_dict[techno]
    #         energy_average_price = energy_average_price + price * techno_production_dict[techno]
    #
    #
    #         capex_price_percentage = (capex_price) * 100 / price
    #         opex_price_percentage = (opex_price) * 100 / price
    #         CO2tax_price_percentage = (CO2tax_price) * 100 / price
    #
    #         capex_list.append(str(round(capex_price, DECIMAL)) + ' (' + str(round(capex_price_percentage, DECIMAL)) + '%)')
    #         opex_list.append(str(round(opex_price, DECIMAL)) + ' (' + str(round(opex_price_percentage, DECIMAL)) + '%)')
    #         CO2tax_list.append(str(round(CO2tax_price, DECIMAL)) + ' (' + str(round(CO2tax_price_percentage, DECIMAL)) + '%)')
    #         energy_costs_List.append(round(price, DECIMAL))
    #
    #     if total_stream_production != 0:
    #         average_capex_value = capex_average_price/total_stream_production
    #         average_opex_value = opex_average_price / total_stream_production
    #         average_CO2tax_value = CO2tax_average_price / total_stream_production
    #         average_price_value = energy_average_price / total_stream_production
    #
    #         average_capex_price_percentage = (average_capex_value) * 100 / average_price_value
    #         average_opex_price_percentage = (average_opex_value) * 100 / average_price_value
    #         average_CO2tax_price_percentage = (average_CO2tax_value) * 100 / average_price_value
    #         average_capex_list.append(str(round(average_capex_value, DECIMAL)) + ' (' + str(round(average_capex_price_percentage, DECIMAL)) + '%)')
    #         average_opex_list.append(str(round(average_opex_value, DECIMAL)) + ' (' + str(round(average_opex_price_percentage, DECIMAL)) + '%)')
    #         average_CO2tax_list.append(str(round(average_CO2tax_value, DECIMAL)) + ' (' + str(round(average_CO2tax_price_percentage, DECIMAL)) + '%)')
    #         average_energy_costs_List.append(round(average_price_value, DECIMAL))


    # Technology price detail table
    # headers = ['Technology', 'CAPEX ($/MWh)', 'OPEX ($/MWh)', 'CO2Tax ($/MWh)', 'Price ($/MWh)']
    # cells = []
    # cells.append(techno_name_list)
    # cells.append(capex_list)
    # cells.append(opex_list)
    # cells.append(CO2tax_list)
    # cells.append(energy_costs_List)

    # table = InstanciatedTable('Capex/Opex/CO2Tax Price and Percentage Production Average Data Comparison for Year ' + str(year), headers, cells)
    # table_list.append(table)

    # headers_average = ['Energy', 'CAPEX ($/MWh)', 'OPEX ($/MWh)', 'CO2Tax ($/MWh)', 'Price ($/MWh)']
    # cells_average  = []
    # cells_average.append(energy_name_list)
    # cells_average.append(average_capex_list)
    # cells_average.append(average_opex_list)
    # cells_average.append(average_CO2tax_list)
    # cells_average.append(average_energy_costs_List)
    # table_average = InstanciatedTable('Capex/Opex/CO2Tax Price and Percentage Production Average Data Comparison for Year ' + str(year), headers_average, cells_average)
    # table_list.append(table_average)

    # To display initial charts for start year
    key_list = list(techno_price_filter_data.keys())
    initial_y_values = []
    for key in techno_price_filter_data.keys():
        initial_y_values.append(techno_price_filter_data[key][0])
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
        for key in techno_price_filter_data.keys():
            y_values.append(techno_price_filter_data[key][i])
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
    # fig.show()
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
    energy = execution_engine.dm.get_disciplines_with_name(namespace)[0].mdo_discipline_wrapp.wrapper.energy_name
    absolute_value_table = []
    average_value_table = []
    if f'{energy} Figures table' in graphs_list: #
        for year in YEAR_COMPARISON:
            new_table = get_techno_price_filter_data(execution_engine, namespace, year)
            #new_table = get_figures_table(price_comparision_table_data, str(year))
            absolute_value_table.append(new_table[0])
            average_value_table.append(new_table[1])

    split_title = namespace.split('.')
    title = split_title[len(split_title) - 1] + ' Capex Price'
    energy = execution_engine.dm.get_disciplines_with_name(namespace)[0].mdo_discipline_wrapp.wrapper.energy_name
    if f'{energy} Capex value' in graphs_list:
        capex_bar_slider_graph = get_techno_price_filter_data(execution_engine, namespace, title, 'CAPEX_Part', 'Capex')
        instanciated_charts.append(capex_bar_slider_graph)

    title = split_title[len(split_title) - 1] + ' Opex Price'
    energy = execution_engine.dm.get_disciplines_with_name(namespace)[0].mdo_discipline_wrapp.wrapper.energy_name
    if f'{energy} Capex value' in graphs_list:
        opex_bar_slider_graph = get_techno_price_filter_data(execution_engine, namespace, title, 'OPEX_Part', 'Opex')
        instanciated_charts.append(opex_bar_slider_graph)

    title = split_title[len(split_title) - 1] + ' Total Price'
    energy = execution_engine.dm.get_disciplines_with_name(namespace)[0].mdo_discipline_wrapp.wrapper.energy_name
    if f'{energy} Capex value' in graphs_list:
        total_price_slider_graph = get_techno_price_filter_data(execution_engine, namespace, title, 'Total_Price', 'Price')
        instanciated_charts.append(total_price_slider_graph)

    # instanciated_charts = absolute_value_table + average_value_table

    return instanciated_charts

