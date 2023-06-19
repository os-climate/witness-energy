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
def post_processing_filters(execution_engine, namespace):
    '''
    WARNING : the execution_engine and namespace arguments are necessary to retrieve the filters
    '''
    filters = []

    chart_list = []
    energy = execution_engine.dm.get_disciplines_with_name(namespace)[
        0].mdo_discipline_wrapp.wrapper.energy_name
    chart_list += [f'{energy} Figures table']

    # The filters are set to False by default since the graphs are not yet
    # mature
    filters.append(ChartFilter('Charts', chart_list, chart_list, 'Charts'))

    return filters

def get_figures_table(table, title):
    '''
    Table chart where Capex, Opex, CO2_Tax and total price comparison
    '''
    fig = ff.create_table(table)
    new_chart = InstantiatedPlotlyNativeChart(fig, chart_name=title)

    return new_chart

def get_comparision_data(execution_engine, namespace, year):

    '''
    Extracting Capex, Opex, CO2_Tax and total price from data manager for all technologies in the techno list
    '''

    table = None
    disc = execution_engine.dm.get_disciplines_with_name(namespace)
    disc_input = disc[0].get_sosdisc_inputs()
    energy_list = disc_input['energy_list']
    #print('energy_list', energy_list)
    techno_list = []
    EnergyDict = {}
    for energ in energy_list:
        var_f_name = f"{namespace}.{energ}.technologies_list"
        if 'biomass_dry' not in var_f_name:
            EnergyDict[f"{namespace}.{energ}"] = {}
            loc_techno_list = execution_engine.dm.get_value(var_f_name)
            result = [f"{namespace}.{energ}." + direction for direction in loc_techno_list]
            techno_list.extend(result)
            EnergyDict[f"{namespace}.{energ}"]['TechnoName'] = loc_techno_list

    capex_list = []
    opex_list = []
    CO2tax_list = []
    energy_costs_List = []
    techno_name_list =[]
    for energyname in EnergyDict.keys():
        for techno in EnergyDict[energyname]['TechnoName']:
            techno_prices_f_name = f"{energyname}.{techno}.techno_detailed_prices" #	"energy_detailed_techno_prices" for Hydrogen and Fuel
            print('techno_prices_f_name', techno_prices_f_name)
            price_details = execution_engine.dm.get_value(techno_prices_f_name)
            techno_name_list.append(techno)
            filtereddata = price_details[price_details['years'] == year]
            capex_price = filtereddata['CAPEX_Part'].iloc[0]
            opex_price = filtereddata['OPEX_Part'].iloc[0]
            CO2tax_price = filtereddata['CO2Tax_Part'].iloc[0]
            price = filtereddata[techno].iloc[0]

            capex_price_percentage = (capex_price) * 100 / price
            opex_price_percentage = (opex_price) * 100 / price
            CO2tax_price_percentage = (CO2tax_price) * 100 / price

            capex_list.append(str(round(capex_price, DECIMAL)) + ' (' + str(round(capex_price_percentage, DECIMAL)) + '%)')
            opex_list.append(str(round(opex_price, DECIMAL)) + ' (' + str(round(opex_price_percentage, DECIMAL)) + '%)')
            CO2tax_list.append(str(round(CO2tax_price, DECIMAL)) + ' (' + str(round(CO2tax_price_percentage, DECIMAL)) + '%)')
            energy_costs_List.append(round(price, DECIMAL))

    headers = ['Technology', 'CAPEX ($/MWh)', 'OPEX ($/MWh)', 'CO2Tax ($/MWh)', 'Price ($/MWh)']
    cells = []
    cells.append(techno_name_list)
    cells.append(capex_list)
    cells.append(opex_list)
    cells.append(CO2tax_list)
    cells.append(energy_costs_List)


    # table_data = {'Technology': techno_name_list}
    # price_data = {'CAPEX ($/MWh)': capex_list, 'OPEX ($/MWh)': opex_list, 'CO2Tax ($/MWh)':  CO2tax_list, 'Price ($/MWh)': energy_costs_List}
    # table_data.update(price_data)
    # table = pd.DataFrame(table_data)

    table = InstanciatedTable(str(year), headers, cells)
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
            new_table = get_comparision_data(execution_engine, namespace, year)
            #new_table = get_figures_table(price_comparision_table_data, str(year))
            instanciated_charts.append(new_table)
    return instanciated_charts

