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
    # chart_list += [f'{energy} Figures table']
    chart_list += [f'{energy} Capex value']


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

    var_f_name = f"{namespace}.technologies_list"
    techno_list = execution_engine.dm.get_value(var_f_name)

    capex_list = []
    opex_list = []
    CO2tax_list = []
    energy_costs_List = []
    for techno in techno_list:
        techno_prices_f_name = f"{namespace}.{techno}.techno_detailed_prices" #	"energy_detailed_techno_prices" for Hydrogen and Fuel
        price_details = execution_engine.dm.get_value(techno_prices_f_name)

        filtereddata = price_details[price_details['years'] == year] # Filtering data for a year of 2023
        capex_price = filtereddata['CAPEX_Part'].iloc[0]
        opex_price = filtereddata['OPEX_Part'].iloc[0]
        CO2tax_price = filtereddata['CO2Tax_Part'].iloc[0]
        price = filtereddata[techno].iloc[0]

        capex_price_percentage = (capex_price)*100/price
        opex_price_percentage = (opex_price) * 100 / price
        CO2tax_price_percentage = (CO2tax_price) * 100 / price

        capex_list.append(str(round(capex_price, DECIMAL)) + ' (' + str(round(capex_price_percentage, DECIMAL)) + '%)')
        opex_list.append(str(round(opex_price, DECIMAL)) + ' (' + str(round(opex_price_percentage, DECIMAL)) + '%)')
        CO2tax_list.append(str(round(CO2tax_price, DECIMAL)) + ' (' + str(round(CO2tax_price_percentage, DECIMAL)) + '%)')
        energy_costs_List.append(round(price, DECIMAL))

    headers = ['Technology', 'CAPEX ($/MWh)', 'OPEX ($/MWh)', 'CO2Tax ($/MWh)', 'Price ($/MWh)']
    cells = []
    cells.append(techno_list)
    cells.append(capex_list)
    cells.append(opex_list)
    cells.append(CO2tax_list)
    cells.append(energy_costs_List)


    # table_data = {'Technology': techno_list}
    # price_data = {'CAPEX ($/MWh)': capex_list, 'OPEX ($/MWh)': opex_list, 'CO2Tax ($/MWh)':  CO2tax_list, \
    #               'Price ($/MWh)': energy_costs_List}
    # table_data.update(price_data)
    # table = pd.DataFrame(table_data)
    table = InstanciatedTable('Data Comparison for Year ' + str(year), headers, cells)
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
    @param summary:Boolean, switch from summary (True) to detailed by years via sliders (False)

    @return new_chart: InstantiatedPlotlyNativeChart Scatter plot
    '''

    # Prepare data
    multilevel_df, years = get_multilevel_df(
        execution_engine, namespace, columns=[''])
    capex_list = list(set(multilevel_df.index.droplevel(1)))
    # Create Figure
    fig = go.Figure()
    # Get min and max CO2 emissions for colorscale and max of production for
    # marker size
    array_of_cmin, array_of_cmax, array_of_pmax, array_of_pintmax = [], [], [], []
    for (array_c, array_p) in multilevel_df[['CO2_per_kWh', 'production']].values:
        array_of_cmin += [array_c.min()]
        array_of_cmax += [array_c.max()]
        array_of_pmax += [array_p.max()]
        array_of_pintmax += [array_p.sum()]
    cmin, cmax = np.min(array_of_cmin), np.max(array_of_cmax)
    pmax, pintmax = np.max(array_of_pmax), np.max(array_of_pintmax)
    if summary:
        # Create a graph to aggregate the informations on all years
        price_per_kWh, price_per_kWh_wotaxes, CO2_per_kWh, label, production, invest, total_CO2 = [
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
            price_per_kWh_wotaxes += [np.mean(row['price_per_kWh_wotaxes']), ]
            CO2_per_kWh += [np.mean(row['CO2_per_kWh']), ]
            label += [i, ]
            production += [np.sum(row['production']), ]
            invest += [np.sum(row['invest']), ]
            total_CO2 += [np.sum(row['CO2_per_kWh'] *
                             row['production']), ]
            CO2_taxes_array += [np.mean(CO2_taxes), ]

        customdata = [label, price_per_kWh, CO2_per_kWh,
                      production, invest, total_CO2, CO2_taxes_array,  years]
        hovertemplate = ''

        marker_sizes = np.multiply(production, 20.0) / \
                       pintmax + 10.0
        scatter = go.Scatter(x=list(years), y=list(CO2_per_kWh),
                             customdata=list(np.asarray(customdata, dtype='object').T),
                             hovertemplate=hovertemplate,
                             text=label,
                             textposition="top center",
                             mode='markers+text',
                             marker=dict(color=CO2_per_kWh,
                                         cmin=cmin, cmax=cmax,
                                         colorscale='RdYlGn_r', size=list(marker_sizes),
                                         colorbar=dict(title='CO2 per kWh', thickness=20)),
                             visible=True)
        fig.add_trace(scatter)
    else:
        # Fill figure with data by year
        for i_year in range(len(years)):
            ################
            # -technology level-#
            ################
            price_per_kWh, price_per_kWh_wotaxes, CO2_per_kWh, label, production, invest, total_CO2 = [], [], [], [], [], [], []
            energy_disc = execution_engine.dm.get_disciplines_with_name(namespace)[
                0]
            CO2_taxes, CO2_taxes_array = energy_disc.get_sosdisc_inputs('CO2_taxes')[
                'CO2_tax'].values, []
            for i, row in multilevel_df.iterrows():
                # skip techno that do not produce the selected energy
                if i[0] != energy_name:
                    continue
                price_per_kWh += [row['price_per_kWh'][i_year], ]
                price_per_kWh_wotaxes += [row['price_per_kWh_wotaxes'][i_year], ]
                CO2_per_kWh += [row['CO2_per_kWh'][i_year], ]
                label += [i, ]
                production += [row['production'][i_year], ]
                invest += [row['invest'][i_year], ]
                total_CO2 += [row['CO2 per kWh'][i_year] *
                              row['production'][i_year], ]
                CO2_taxes_array += [CO2_taxes[i_year], ]
            customdata = [label, price_per_kWh, CO2_per_kWh,
                          production, invest, total_CO2, CO2_taxes_array,
                          price_per_kWh_wotaxes]
            hovertemplate = ''
            marker_sizes = np.multiply(production, 20.0) / \
                           pmax + 10.0
            scatter = go.Scatter(x=list(price_per_kWh_wotaxes), y=list(CO2_per_kWh),
                                 customdata=list(np.asarray(customdata, dtype='object').T),
                                 hovertemplate=hovertemplate,
                                 text=label,
                                 textposition="top center",
                                 mode='markers+text',
                                 marker=dict(color=CO2_per_kWh,
                                             cmin=cmin, cmax=cmax,
                                             colorscale='RdYlGn_r', size=list(marker_sizes),
                                             colorbar=dict(title='CO2 per kWh', thickness=20)),
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

def get_multilevel_df(execution_engine, namespace, columns=None):
    '''! Function to create the dataframe with all the data necessary for the graphs in a multilevel [energy, technologies]
    @param execution_engine: Current execution engine object, from which the data is extracted
    @param namespace: Namespace at which the data can be accessed

    @return multilevel_df: Dataframe
    '''
    # Construct a DataFrame to organize the data on two levels: energy and
    # techno
    idx = pd.MultiIndex.from_tuples([], names=['capex', 'year'])
    multilevel_df = pd.DataFrame(
        index=idx,
        columns=[''])
    capex_list = [execution_engine.dm.get_disciplines_with_name(namespace)[
                       0].mdo_discipline_wrapp.wrapper.energy_name]
    for capex in capex_list:
        capex_disc = execution_engine.dm.get_disciplines_with_name(
            f'{namespace}')[0]
        year_list = capex_disc.get_sosdisc_inputs('technologies_list')
        for year in year_list:
            techno_disc = execution_engine.dm.get_disciplines_with_name(
                f'{namespace}.{year}')[0]
            # production_techno = techno_disc.get_sosdisc_outputs(
            #     'techno_production')[f'{capex} (TWh)'].values * \
            #                     techno_disc.get_sosdisc_inputs(
            #                         'scaling_factor_techno_production')
            # invest_techno = techno_disc.get_sosdisc_inputs('invest_level')[
            #                     f'invest'].values * \
            #                 techno_disc.get_sosdisc_inputs('scaling_factor_invest_level')
            # # Calculate total CO2 emissions
            # data_fuel_dict = techno_disc.get_sosdisc_inputs('data_fuel_dict')
            # carbon_emissions = techno_disc.get_sosdisc_outputs(
            #     'CO2_emissions_detailed')
            # CO2_per_use = np.zeros(
            #     len(carbon_emissions['years']))
            # if 'CO2_per_use' in data_fuel_dict and 'high_calorific_value' in data_fuel_dict:
            #     if data_fuel_dict['CO2_per_use_unit'] == 'kg/kg':
            #         CO2_per_use = np.ones(
            #             len(carbon_emissions['years'])) * data_fuel_dict['CO2_per_use'] / data_fuel_dict[
            #                           'high_calorific_value']
            #     elif data_fuel_dict['CO2_per_use_unit'] == 'kg/kWh':
            #         CO2_per_use = np.ones(
            #             len(carbon_emissions['years'])) * data_fuel_dict['CO2_per_use']
            # for emission_type in carbon_emissions:
            #     if emission_type == techno:
            #         total_carbon_emissions = CO2_per_use + \
            #                                  carbon_emissions[techno].values
            # CO2_per_kWh_techno = total_carbon_emissions
            # # Data for scatter plot
            # price_per_kWh_techno = techno_disc.get_sosdisc_outputs('techno_prices')[
            #     f'{techno}'].values
            # price_per_kWh_wotaxes_techno = techno_disc.get_sosdisc_outputs('techno_prices')[
            #     f'{techno}_wotaxes'].values
            idx = pd.MultiIndex.from_tuples(
                [(f'{capex}', f'{year}')], names=['capex', 'year'])
            columns_year = ['']
            techno_df = pd.DataFrame([(capex, year)],
                                     index=idx, columns=columns_year)
            multilevel_df = multilevel_df.append(techno_df)

    years = np.arange(capex_disc.get_sosdisc_inputs(
        'year_start'), capex_disc.get_sosdisc_inputs('year_end') + 1, 1)

    # If columns is not None, return a subset of multilevel_df with selected
    # columns
    if columns != None and type(columns) == list:
        multilevel_df = pd.DataFrame(multilevel_df[columns])

    return multilevel_df, years
# def get_multilevel_df(execution_engine, namespace, columns=None):
#     '''! Function to create the dataframe with all the data necessary for the graphs in a multilevel [energy, technologies]
#     @param execution_engine: Current execution engine object, from which the data is extracted
#     @param namespace: Namespace at which the data can be accessed
#
#     @return multilevel_df: Dataframe
#     '''
#     # Construct a DataFrame to organize the data on two levels: energy and
#     # techno
#     idx = pd.MultiIndex.from_tuples([], names=['energy', 'techno'])
#     multilevel_df = pd.DataFrame(
#         index=idx,
#         columns=['production', 'invest', 'CO2_per_kWh', 'price_per_kWh', 'price_per_kWh_wotaxes'])
#     energy_list = [execution_engine.dm.get_disciplines_with_name(namespace)[
#                        0].mdo_discipline_wrapp.wrapper.energy_name]
#     for energy in energy_list:
#         energy_disc = execution_engine.dm.get_disciplines_with_name(
#             f'{namespace}')[0]
#         techno_list = energy_disc.get_sosdisc_inputs('technologies_list')
#         for techno in techno_list:
#             techno_disc = execution_engine.dm.get_disciplines_with_name(
#                 f'{namespace}.{techno}')[0]
#             production_techno = techno_disc.get_sosdisc_outputs(
#                 'techno_production')[f'{energy} (TWh)'].values * \
#                                 techno_disc.get_sosdisc_inputs(
#                                     'scaling_factor_techno_production')
#             invest_techno = techno_disc.get_sosdisc_inputs('invest_level')[
#                                 f'invest'].values * \
#                             techno_disc.get_sosdisc_inputs('scaling_factor_invest_level')
#             # Calculate total CO2 emissions
#             data_fuel_dict = techno_disc.get_sosdisc_inputs('data_fuel_dict')
#             carbon_emissions = techno_disc.get_sosdisc_outputs(
#                 'CO2_emissions_detailed')
#             CO2_per_use = np.zeros(
#                 len(carbon_emissions['years']))
#             if 'CO2_per_use' in data_fuel_dict and 'high_calorific_value' in data_fuel_dict:
#                 if data_fuel_dict['CO2_per_use_unit'] == 'kg/kg':
#                     CO2_per_use = np.ones(
#                         len(carbon_emissions['years'])) * data_fuel_dict['CO2_per_use'] / data_fuel_dict[
#                                       'high_calorific_value']
#                 elif data_fuel_dict['CO2_per_use_unit'] == 'kg/kWh':
#                     CO2_per_use = np.ones(
#                         len(carbon_emissions['years'])) * data_fuel_dict['CO2_per_use']
#             for emission_type in carbon_emissions:
#                 if emission_type == techno:
#                     total_carbon_emissions = CO2_per_use + \
#                                              carbon_emissions[techno].values
#             CO2_per_kWh_techno = total_carbon_emissions
#             # Data for scatter plot
#             price_per_kWh_techno = techno_disc.get_sosdisc_outputs('techno_prices')[
#                 f'{techno}'].values
#             price_per_kWh_wotaxes_techno = techno_disc.get_sosdisc_outputs('techno_prices')[
#                 f'{techno}_wotaxes'].values
#             idx = pd.MultiIndex.from_tuples(
#                 [(f'{energy}', f'{techno}')], names=['energy', 'techno'])
#             columns_techno = ['energy', 'technology',
#                               'production', 'invest',
#                               'CO2_per_kWh', 'price_per_kWh',
#                               'price_per_kWh_wotaxes']
#             techno_df = pd.DataFrame([(energy, techno, production_techno, invest_techno, CO2_per_kWh_techno,
#                                        price_per_kWh_techno, price_per_kWh_wotaxes_techno)],
#                                      index=idx, columns=columns_techno)
#             multilevel_df = multilevel_df.append(techno_df)
#
#     years = np.arange(energy_disc.get_sosdisc_inputs(
#         'year_start'), energy_disc.get_sosdisc_inputs('year_end') + 1, 1)
#
#     # If columns is not None, return a subset of multilevel_df with selected
#     # columns
#     if columns != None and type(columns) == list:
#         multilevel_df = pd.DataFrame(multilevel_df[columns])
#
#     return multilevel_df, years

def get_Capex_multilevel_df(execution_engine, namespace):
    '''! Function to create the dataframe with all the data necessary for the Capex graphs in a multilevel [energy, technologies]
    @param execution_engine: Current execution engine object, from which the data is extracted
    @param namespace: Namespace at which the data can be accessed

    @return multilevel_df: Dataframe
    '''

    energy_disc = execution_engine.dm.get_disciplines_with_name(namespace)[0].mdo_discipline_wrapp.wrapper
    energy_list = [energy_disc.energy_name]

    years = np.arange(energy_disc.get_sosdisc_inputs(
        'year_start'), energy_disc.get_sosdisc_inputs('year_end') + 1, 1)
    # Construct a DataFrame to organize the data on two levels: energy and
    # techno
    idx = pd.MultiIndex.from_tuples([], names=['capex', 'year'])
    columns = ['Capex', 'Year']
    # Gather all the possible emission types
    other_emission_type = []
    for capex in energy_list:
        year_list = energy_disc.get_sosdisc_inputs('technologies_list')
        for year in year_list:
            year_disc = execution_engine.dm.get_disciplines_with_name(
                f'{namespace}.{year}')[0]
    #         carbon_emissions = year_disc.get_sosdisc_outputs(
    #             'CO2_emissions_detailed')
    #         other_emission_type += [col for col in carbon_emissions.columns if col not in [
    #             'years', 'production', year]]
    # other_emission_type = list(set(other_emission_type))
    # columns += [f'CO2_from_{other_emission}_consumption' for other_emission in other_emission_type]
    multilevel_df = pd.DataFrame(
        index=idx,
        columns=columns)
    for capex in energy_list:
        capex_disc = execution_engine.dm.get_disciplines_with_name(
            f'{namespace}')[0]
        techno_list = energy_disc.get_sosdisc_inputs('technologies_list')
        for year in techno_list:
            year_disc = execution_engine.dm.get_disciplines_with_name(
                f'{namespace}.{year}')[0]
            # production_techno = techno_disc.get_sosdisc_outputs(
            #     'techno_production')[f'{energy} (TWh)'].values * \
            #                     techno_disc.get_sosdisc_inputs(
            #                         'scaling_factor_techno_production')
            # Calculate total CO2 emissions
            # data_fuel_dict = techno_disc.get_sosdisc_inputs('data_fuel_dict')
            # carbon_emissions = techno_disc.get_sosdisc_outputs(
            #     'CO2_emissions_detailed')
            # CO2_per_use = np.zeros(
            #     len(carbon_emissions['years']))
            # if 'CO2_per_use' in data_fuel_dict and 'high_calorific_value' in data_fuel_dict:
            #     if data_fuel_dict['CO2_per_use_unit'] == 'kg/kg':
            #         CO2_per_use = np.ones(
            #             len(carbon_emissions['years'])) * data_fuel_dict['CO2_per_use'] / data_fuel_dict[
            #                           'high_calorific_value']
            #     elif data_fuel_dict['CO2_per_use_unit'] == 'kg/kWh':
            #         CO2_per_use = np.ones(
            #             len(carbon_emissions['years'])) * data_fuel_dict['CO2_per_use']
            # CO2_from_other_consumption = dict(
            #     zip([f'CO2_from_{other_emission}_consumption' for other_emission in other_emission_type],
            #         [np.zeros(len(years)) for _ in other_emission_type]))
            # for emission_type in carbon_emissions:
            #     if emission_type == 'years':
            #         continue
            #     elif emission_type == 'production':
            #         CO2_from_production = carbon_emissions[emission_type].values
            #     elif emission_type == techno:
            #         total_carbon_emissions = CO2_per_use + \
            #                                  carbon_emissions[techno].values
            #     else:
            #         CO2_from_other_consumption[f'CO2_from_{emission_type}_consumption'] = carbon_emissions[
            #             emission_type].values
            # CO2_after_use = total_carbon_emissions
            idx = pd.MultiIndex.from_tuples(
                [(f'{capex}', f'{year}')], names=['capex', 'year'])
            columns_techno = ['capex', 'technology']
            techno_df = pd.DataFrame([capex, year],
                                     index=idx, columns=columns_techno)
            multilevel_df = multilevel_df.append(techno_df)

    return multilevel_df, years