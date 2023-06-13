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

import pandas as pd
from plotly.express.colors import qualitative

YEAR_COMPARISON = 2023
DECIMAL = 2
def post_processing_filters(execution_engine, namespace):
    '''
    WARNING : the execution_engine and namespace arguments are necessary to retrieve the filters
    '''
    filters = []

    chart_list = []
    energy = execution_engine.dm.get_disciplines_with_name(namespace)[
        0].mdo_discipline_wrapp.wrapper.energy_name
    chart_list += [f'{energy} CO2 intensity']
    chart_list += [f'{energy} CO2 breakdown sankey']
    chart_list += [f'{energy} CO2 breakdown bar']
    chart_list += [f'{energy} Figures table']

    # The filters are set to False by default since the graphs are not yet
    # mature
    filters.append(ChartFilter('Charts', chart_list, chart_list, 'Charts'))

    return filters

def get_figures_table(table):
    '''
    Table chart where Capex, Opex, CO2_Tax and total price comparison
    '''
    fig = ff.create_table(table)
    new_chart = InstantiatedPlotlyNativeChart(fig, chart_name='')

    return new_chart

def get_comparision_data(execution_engine, namespace):

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

        filtereddata = price_details[price_details['years'] == 2023] # Filtering data for a year of 2023
        capex_price = float(filtereddata['CAPEX_Part'].to_string(index=False))
        opex_price = float(filtereddata['OPEX_Part'].to_string(index=False))
        CO2tax_price = float(filtereddata['CO2Tax_Part'].to_string(index=False))
        price = float(filtereddata[techno].to_string(index=False)) #'energy_costs'

        capex_price_percentage = (capex_price)*100/price
        opex_price_percentage = (opex_price) * 100 / price
        CO2tax_price_percentage = (CO2tax_price) * 100 / price

        capex_list.append(str(round(capex_price, DECIMAL)) + ' (' + str(round(capex_price_percentage, DECIMAL)) + '%)')
        opex_list.append(str(round(opex_price, DECIMAL)) + ' (' + str(round(opex_price_percentage, DECIMAL)) + '%)')
        CO2tax_list.append(str(round(CO2tax_price, DECIMAL)) + ' (' + str(round(CO2tax_price_percentage, DECIMAL)) + '%)')
        energy_costs_List.append(round(price, DECIMAL))



    table_data = {'Technology': techno_list}
    price_data = {'CAPEX ($/MWh)': capex_list, 'OPEX ($/MWh)': opex_list, 'CO2Tax ($/MWh)':  CO2tax_list, 'Price ($/MWh)': energy_costs_List}
    table_data.update(price_data)
    table = pd.DataFrame(table_data)
    return table

def post_processings(execution_engine, namespace, filters):
    '''
    WARNING : the execution_engine and namespace arguments are necessary to retrieve the post_processings
    '''

    price_comparision_table_data = get_comparision_data(execution_engine, namespace)

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
        new_table = get_figures_table(price_comparision_table_data)
        instanciated_charts.append(new_table)


    if f'{energy} CO2 intensity' in graphs_list:
        chart_name = f'{energy} CO2 intensity summary'
        new_chart = get_chart_green_technologies(
            execution_engine, namespace, energy_name=energy, chart_name=chart_name)
        if new_chart is not None:
            instanciated_charts.append(new_chart)

        chart_name = f'{energy} CO2 intensity by years'
        new_chart = get_chart_green_technologies(
            execution_engine, namespace, energy_name=energy, chart_name=chart_name, summary=False)
        if new_chart is not None:
            instanciated_charts.append(new_chart)
    # ---
    if f'{energy} CO2 breakdown sankey' in graphs_list:
        chart_name = f'{energy} CO2 breakdown sankey summary'
        new_chart = get_chart_Energy_CO2_breakdown_sankey(
            execution_engine, namespace, energy_name=energy, chart_name=chart_name)
        if new_chart is not None:
            instanciated_charts.append(new_chart)

        chart_name = f'{energy} CO2 breakdown sankey by years'
        new_chart = get_chart_Energy_CO2_breakdown_sankey(
            execution_engine, namespace, energy_name=energy, chart_name=chart_name, summary=False)
        if new_chart is not None:
            instanciated_charts.append(new_chart)


    return instanciated_charts


def get_chart_green_technologies(execution_engine, namespace, energy_name, chart_name='Technologies CO2 intensity',
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
        execution_engine, namespace, columns=['price_per_kWh', 'price_per_kWh_wotaxes',
                                              'CO2_per_kWh', 'production', 'invest'])
    energy_list = list(set(multilevel_df.index.droplevel(1)))
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
                      production, invest, total_CO2, CO2_taxes_array,
                      price_per_kWh_wotaxes]
        hovertemplate = '<br>Name: %{customdata[0]}' + \
                        '<br>Mean Price per kWh before CO2 tax: %{customdata[7]: .2e}' + \
                        '<br>Mean CO2 per kWh: %{customdata[2]: .2e}' + \
                        '<br>Integrated Total CO2: %{customdata[5]: .2e}' + \
                        '<br>Integrated Production: %{customdata[3]: .2e}' + \
                        '<br>Integrated Invest: %{customdata[4]: .2e}' + \
                        '<br>Mean Price per kWh: %{customdata[1]: .2e}' + \
                        '<br>Mean CO2 taxes: %{customdata[6]: .2e}'
        marker_sizes = np.multiply(production, 20.0) / \
                       pintmax + 10.0
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
                             visible=True)
        fig.add_trace(scatter)
    else:
        # Fill figure with data by year
        for i_year in range(len(years)):
            ################
            # -technology level-#
            ################
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
                price_per_kWh += [row['price_per_kWh'][i_year], ]
                price_per_kWh_wotaxes += [row['price_per_kWh_wotaxes'][i_year], ]
                CO2_per_kWh += [row['CO2_per_kWh'][i_year], ]
                label += [i, ]
                production += [row['production'][i_year], ]
                invest += [row['invest'][i_year], ]
                total_CO2 += [row['CO2_per_kWh'][i_year] *
                              row['production'][i_year], ]
                CO2_taxes_array += [CO2_taxes[i_year], ]
            customdata = [label, price_per_kWh, CO2_per_kWh,
                          production, invest, total_CO2, CO2_taxes_array,
                          price_per_kWh_wotaxes]
            hovertemplate = '<br>Name: %{customdata[0]}' + \
                            '<br>Price per kWh before CO2 tax: %{customdata[7]: .2e}' + \
                            '<br>CO2 per kWh: %{customdata[2]: .2e}' + \
                            '<br>Total CO2: %{customdata[5]: .2e}' + \
                            '<br>Production: %{customdata[3]: .2e}' + \
                            '<br>Invest: %{customdata[4]: .2e}' + \
                            '<br>Price per kWh: %{customdata[1]: .2e}' + \
                            '<br>CO2 taxes: %{customdata[6]: .2e}'
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

    fig.update_xaxes(title_text='Price per MWh [$/MWh] (without CO2 taxes)')
    fig.update_yaxes(title_text='CO2 per kWh [kgCO2/kWh]')
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
    idx = pd.MultiIndex.from_tuples([], names=['energy', 'techno'])
    multilevel_df = pd.DataFrame(
        index=idx,
        columns=['production', 'invest', 'CO2_per_kWh', 'price_per_kWh', 'price_per_kWh_wotaxes'])
    energy_list = [execution_engine.dm.get_disciplines_with_name(namespace)[
                       0].mdo_discipline_wrapp.wrapper.energy_name]
    for energy in energy_list:
        energy_disc = execution_engine.dm.get_disciplines_with_name(
            f'{namespace}')[0]
        techno_list = energy_disc.get_sosdisc_inputs('technologies_list')
        for techno in techno_list:
            techno_disc = execution_engine.dm.get_disciplines_with_name(
                f'{namespace}.{techno}')[0]
            production_techno = techno_disc.get_sosdisc_outputs(
                'techno_production')[f'{energy} (TWh)'].values * \
                                techno_disc.get_sosdisc_inputs(
                                    'scaling_factor_techno_production')
            invest_techno = techno_disc.get_sosdisc_inputs('invest_level')[
                                f'invest'].values * \
                            techno_disc.get_sosdisc_inputs('scaling_factor_invest_level')
            # Calculate total CO2 emissions
            data_fuel_dict = techno_disc.get_sosdisc_inputs('data_fuel_dict')
            carbon_emissions = techno_disc.get_sosdisc_outputs(
                'CO2_emissions_detailed')
            CO2_per_use = np.zeros(
                len(carbon_emissions['years']))
            if 'CO2_per_use' in data_fuel_dict and 'high_calorific_value' in data_fuel_dict:
                if data_fuel_dict['CO2_per_use_unit'] == 'kg/kg':
                    CO2_per_use = np.ones(
                        len(carbon_emissions['years'])) * data_fuel_dict['CO2_per_use'] / data_fuel_dict[
                                      'high_calorific_value']
                elif data_fuel_dict['CO2_per_use_unit'] == 'kg/kWh':
                    CO2_per_use = np.ones(
                        len(carbon_emissions['years'])) * data_fuel_dict['CO2_per_use']
            for emission_type in carbon_emissions:
                if emission_type == techno:
                    total_carbon_emissions = CO2_per_use + \
                                             carbon_emissions[techno].values
            CO2_per_kWh_techno = total_carbon_emissions
            # Data for scatter plot
            price_per_kWh_techno = techno_disc.get_sosdisc_outputs('techno_prices')[
                f'{techno}'].values
            price_per_kWh_wotaxes_techno = techno_disc.get_sosdisc_outputs('techno_prices')[
                f'{techno}_wotaxes'].values
            idx = pd.MultiIndex.from_tuples(
                [(f'{energy}', f'{techno}')], names=['energy', 'techno'])
            columns_techno = ['energy', 'technology',
                              'production', 'invest',
                              'CO2_per_kWh', 'price_per_kWh',
                              'price_per_kWh_wotaxes']
            techno_df = pd.DataFrame([(energy, techno, production_techno, invest_techno, CO2_per_kWh_techno,
                                       price_per_kWh_techno, price_per_kWh_wotaxes_techno)],
                                     index=idx, columns=columns_techno)
            multilevel_df = multilevel_df.append(techno_df)

    years = np.arange(energy_disc.get_sosdisc_inputs(
        'year_start'), energy_disc.get_sosdisc_inputs('year_end') + 1, 1)

    # If columns is not None, return a subset of multilevel_df with selected
    # columns
    if columns != None and type(columns) == list:
        multilevel_df = pd.DataFrame(multilevel_df[columns])

    return multilevel_df, years


def get_chart_Energy_CO2_breakdown_sankey(execution_engine, namespace, chart_name, energy_name, summary=True):
    '''! Function to create the CO2 breakdown Sankey diagram
    @param execution_engine: Execution engine object from which the data is gathered
    @param namespace: String containing the namespace to access the data
    @param chart_name:String, title of the post_proc
    @param energy: String, name of the energy to display

    @return new_chart: InstantiatedPlotlyNativeChart a Sankey Diagram
    '''

    # Prepare data
    multilevel_df, years = get_CO2_breakdown_multilevel_df(
        execution_engine, namespace)
    energy_list = list(set(multilevel_df.index.droplevel(1)))
    technologies_list = list(multilevel_df.loc[energy_name].index.values)
    other_emission_type = [col for col in multilevel_df.columns if col not in [
        'energy', 'technology', 'production', 'CO2_from_production', 'CO2_per_use', 'CO2_after_use']]
    label_col1 = ['CO2 from production', 'CO2 per use'] + other_emission_type
    label_col2 = technologies_list
    label_col3 = [f'Total CO2 emissions for {energy_name}', ]
    label_list = label_col1 + label_col2 + label_col3

    # Create Figure
    chart_name = f'{chart_name}'
    fig = go.Figure()

    # Fill figure with data by year
    # i_label_dict associates each label with an integer value
    i_label_dict = dict((key, i) for i, key in enumerate(label_list))
    fig = go.Figure()
    cmap_over = cm.get_cmap('Reds')
    cmap_under = cm.get_cmap('Greens')
    if summary:
        source, target = [], []
        source_name, target_name = [], []
        flux, flux_color = [], []
        production_list = []
        for i, technology in enumerate(technologies_list):
            # energies level
            production = np.sum(multilevel_df.loc[(
                energy_name, technology)]['production'])
            # per kWh
            CO2_from_production = np.mean(multilevel_df.loc[(
                energy_name, technology)]['CO2_from_production'])
            CO2_per_use = np.mean(multilevel_df.loc[(
                energy_name, technology)]['CO2_per_use'])
            CO2_after_use = np.mean(multilevel_df.loc[(
                energy_name, technology)]['CO2_after_use'])
            # total
            CO2_from_production_tot = np.sum(multilevel_df.loc[(energy_name, technology)]['CO2_from_production'] *
                                             multilevel_df.loc[(energy_name, technology)]['production']) + \
                                      1e-20
            CO2_per_use_tot = np.sum(multilevel_df.loc[(energy_name, technology)]['CO2_per_use'] *
                                     multilevel_df.loc[(energy_name, technology)]['production']) + \
                              1e-20
            CO2_after_use_tot = np.sum(multilevel_df.loc[(energy_name, technology)]['CO2_after_use'] *
                                       multilevel_df.loc[(energy_name, technology)]['production']) + \
                                1e-20
            # Loop on every other energies
            CO2_from_other_consumption, CO2_from_other_consumption_tot = {}, {}
            for other_emission in other_emission_type:
                CO2_from_other_consumption[other_emission] = np.mean(multilevel_df.loc[
                                                                         (energy_name, technology)][other_emission])
                CO2_from_other_consumption_tot[other_emission] = np.sum(multilevel_df.loc[(
                    energy_name, technology)][other_emission] * multilevel_df.loc[(energy_name, technology)][
                                                                            'production'])
            # col1 to col2
            source += [i_label_dict['CO2 from production'], ]
            source_name += ['CO2 from production', ]
            target += [i_label_dict[technology], ]
            target_name += [technology, ]
            flux += [CO2_from_production_tot, ]
            flux_color += [CO2_from_production, ]
            production_list += [production, ]
            source += [i_label_dict['CO2 per use'], ]
            source_name += ['CO2 per use', ]
            target += [i_label_dict[technology], ]
            target_name += [technology, ]
            flux += [CO2_per_use_tot, ]
            flux_color += [CO2_per_use, ]
            production_list += [production, ]
            for other_emission in other_emission_type:
                source += [
                    i_label_dict[other_emission], ]
                source_name += [other_emission, ]
                target += [i_label_dict[technology], ]
                target_name += [technology, ]
                flux += [CO2_from_other_consumption_tot[other_emission], ]
                flux_color += [CO2_from_other_consumption[other_emission], ]
                production_list += [production, ]
            # col2 to col3
            source += [i_label_dict[technology], ]
            source_name += [technology, ]
            target += [
                i_label_dict[f'Total CO2 emissions for {energy_name}'], ]
            target_name += [f'Total CO2 emissions for {energy_name}', ]
            flux += [CO2_after_use_tot, ]
            flux_color += [CO2_after_use, ]
            production_list += [production, ]
        customdata = list(
            np.array([source_name, target_name, production_list, flux_color,
                      np.where(np.array(flux) <= 1e-20, 0.0, np.array(flux))]).T)
        hovertemplate = '<br>Source: %{customdata[0]}' + \
                        '<br>Target: %{customdata[1]}' + \
                        '<br>Production: %{customdata[2]: .2e}' + \
                        '<br>CO2 per kWh (color): %{customdata[3]: .2e}' + \
                        '<br>Total CO2 (thickness): %{customdata[4]: .2e}'
        rgba_list_over = cmap_over(
            0.1 + np.abs(flux_color) / np.max(np.abs(flux_color)))
        rgba_list_under = cmap_under(
            0.1 + np.abs(flux_color) / np.max(np.abs(flux_color)))
        color_over = ['rgb' + str(tuple(int((255 * (x * 0.8 + 0.2)))
                                        for x in rgba[0:3])) for rgba in rgba_list_over]
        color_under = ['rgb' + str(tuple(int((255 * (x * 0.8 + 0.2)))
                                         for x in rgba[0:3])) for rgba in rgba_list_under]
        color = np.where(np.array(flux_color) > 0.0, color_over, color_under)
        link = dict(source=source, target=target,
                    value=list(np.where(np.abs(flux) > 0.0, 1.0 +
                                        100.0 * np.abs(flux) / np.max(np.abs(flux)), 0.0)),
                    color=list(color),
                    customdata=customdata,
                    hovertemplate=hovertemplate, )
        sankey = go.Sankey(node=dict(pad=15, thickness=20, line=dict(color="black", width=0.5),
                                     label=list(i_label_dict.keys()), color="black"),
                           link=link,
                           visible=False)
        fig.add_trace(sankey)

    else:
        for i_year in range(len(years)):
            source, target = [], []
            source_name, target_name = [], []
            flux, flux_color = [], []
            production_list = []
            for i, technology in enumerate(technologies_list):
                # energies level
                production = multilevel_df.loc[(
                    energy_name, technology)]['production'][i_year]
                # per kWh
                CO2_from_production = multilevel_df.loc[(
                    energy_name, technology)]['CO2_from_production'][i_year]
                CO2_per_use = multilevel_df.loc[(
                    energy_name, technology)]['CO2_per_use'][i_year]
                CO2_after_use = multilevel_df.loc[(
                    energy_name, technology)]['CO2_after_use'][i_year]
                # total
                CO2_from_production_tot = (multilevel_df.loc[(energy_name, technology)]['CO2_from_production'] *
                                           multilevel_df.loc[(energy_name, technology)]['production'])[i_year] + \
                                          1e-20
                CO2_per_use_tot = (multilevel_df.loc[(energy_name, technology)]['CO2_per_use'] *
                                   multilevel_df.loc[(energy_name, technology)]['production'])[i_year] + \
                                  1e-20
                CO2_after_use_tot = (multilevel_df.loc[(energy_name, technology)]['CO2_after_use'] *
                                     multilevel_df.loc[(energy_name, technology)]['production'])[i_year] + \
                                    1e-20
                # Loop on every other energies
                CO2_from_energy_consumption, CO2_from_energy_consumption_tot = {}, {}
                for other_emisson in other_emission_type:
                    CO2_from_energy_consumption[other_emisson] = multilevel_df.loc[
                        (energy_name, technology)][other_emisson][i_year]
                    CO2_from_energy_consumption_tot[other_emisson] = (
                            multilevel_df.loc[(energy_name, technology)][other_emisson] *
                            multilevel_df.loc[(energy_name, technology)]['production'])[i_year]
                # col1 to col2
                source += [i_label_dict['CO2 from production'], ]
                source_name += ['CO2 from production', ]
                target += [i_label_dict[technology], ]
                target_name += [technology, ]
                flux += [CO2_from_production_tot, ]
                flux_color += [CO2_from_production, ]
                production_list += [production, ]
                source += [i_label_dict['CO2 per use'], ]
                source_name += ['CO2 per use', ]
                target += [i_label_dict[technology], ]
                target_name += [technology, ]
                flux += [CO2_per_use_tot, ]
                flux_color += [CO2_per_use, ]
                production_list += [production, ]
                for other_emisson in other_emission_type:
                    source += [
                        i_label_dict[other_emisson], ]
                    source_name += [other_emisson, ]
                    target += [i_label_dict[technology], ]
                    target_name += [technology, ]
                    flux += [CO2_from_energy_consumption_tot[other_emisson], ]
                    flux_color += [CO2_from_energy_consumption[other_emisson], ]
                    production_list += [production, ]
                # col2 to col3
                source += [i_label_dict[technology], ]
                source_name += [technology, ]
                target += [
                    i_label_dict[f'Total CO2 emissions for {energy_name}'], ]
                target_name += [f'Total CO2 emissions for {energy_name}', ]
                flux += [CO2_after_use_tot, ]
                flux_color += [CO2_after_use, ]
                production_list += [production, ]
            customdata = list(
                np.array([source_name, target_name, production_list, flux_color,
                          np.where(np.array(flux) <= 1e-20, 0.0, np.array(flux))]).T)
            hovertemplate = '<br>Source: %{customdata[0]}' + \
                            '<br>Target: %{customdata[1]}' + \
                            '<br>Production: %{customdata[2]: .2e}' + \
                            '<br>CO2 per kWh (color): %{customdata[3]: .2e}' + \
                            '<br>Total CO2 (thickness): %{customdata[4]: .2e}'
            rgba_list_over = cmap_over(
                0.1 + np.abs(flux_color) / np.max(np.abs(flux_color)))
            rgba_list_under = cmap_under(
                0.1 + np.abs(flux_color) / np.max(np.abs(flux_color)))
            color_over = ['rgb' + str(tuple(int((255 * (x * 0.8 + 0.2)))
                                            for x in rgba[0:3])) for rgba in rgba_list_over]
            color_under = ['rgb' + str(tuple(int((255 * (x * 0.8 + 0.2)))
                                             for x in rgba[0:3])) for rgba in rgba_list_under]
            color = np.where(np.array(flux_color) > 0.0,
                             color_over, color_under)
            link = dict(source=source, target=target,
                        value=list(np.where(
                            np.abs(flux) > 0.0, 1.0 + 100.0 * np.abs(flux) / np.max(np.abs(flux)), 0.0)),
                        color=list(color),
                        customdata=customdata,
                        hovertemplate=hovertemplate, )
            sankey = go.Sankey(node=dict(pad=15, thickness=20, line=dict(color="black", width=0.5),
                                         label=list(i_label_dict.keys()), color="black"),
                               link=link,
                               visible=False)
            fig.add_trace(sankey)

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

    fig.data[0].visible = True

    new_chart = InstantiatedPlotlyNativeChart(
        fig, chart_name=chart_name, default_title=True)
    return new_chart


def get_CO2_breakdown_multilevel_df(execution_engine, namespace):
    '''! Function to create the dataframe with all the data necessary for the CO2 breakdown graphs in a multilevel [energy, technologies]
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
    idx = pd.MultiIndex.from_tuples([], names=['energy', 'techno'])
    columns = ['production', 'CO2_from_production',
               'CO2_per_use', 'CO2_after_use']
    # Gather all the possible emission types
    other_emission_type = []
    for energy in energy_list:
        techno_list = energy_disc.get_sosdisc_inputs('technologies_list')
        for techno in techno_list:
            techno_disc = execution_engine.dm.get_disciplines_with_name(
                f'{namespace}.{techno}')[0]
            carbon_emissions = techno_disc.get_sosdisc_outputs(
                'CO2_emissions_detailed')
            other_emission_type += [col for col in carbon_emissions.columns if col not in [
                'years', 'production', techno]]
    other_emission_type = list(set(other_emission_type))
    columns += [f'CO2_from_{other_emission}_consumption' for other_emission in other_emission_type]
    multilevel_df = pd.DataFrame(
        index=idx,
        columns=columns)
    for energy in energy_list:
        energy_disc = execution_engine.dm.get_disciplines_with_name(
            f'{namespace}')[0]
        techno_list = energy_disc.get_sosdisc_inputs('technologies_list')
        for techno in techno_list:
            techno_disc = execution_engine.dm.get_disciplines_with_name(
                f'{namespace}.{techno}')[0]
            production_techno = techno_disc.get_sosdisc_outputs(
                'techno_production')[f'{energy} (TWh)'].values * \
                                techno_disc.get_sosdisc_inputs(
                                    'scaling_factor_techno_production')
            # Calculate total CO2 emissions
            data_fuel_dict = techno_disc.get_sosdisc_inputs('data_fuel_dict')
            carbon_emissions = techno_disc.get_sosdisc_outputs(
                'CO2_emissions_detailed')
            CO2_per_use = np.zeros(
                len(carbon_emissions['years']))
            if 'CO2_per_use' in data_fuel_dict and 'high_calorific_value' in data_fuel_dict:
                if data_fuel_dict['CO2_per_use_unit'] == 'kg/kg':
                    CO2_per_use = np.ones(
                        len(carbon_emissions['years'])) * data_fuel_dict['CO2_per_use'] / data_fuel_dict[
                                      'high_calorific_value']
                elif data_fuel_dict['CO2_per_use_unit'] == 'kg/kWh':
                    CO2_per_use = np.ones(
                        len(carbon_emissions['years'])) * data_fuel_dict['CO2_per_use']
            CO2_from_other_consumption = dict(
                zip([f'CO2_from_{other_emission}_consumption' for other_emission in other_emission_type],
                    [np.zeros(len(years)) for _ in other_emission_type]))
            for emission_type in carbon_emissions:
                if emission_type == 'years':
                    continue
                elif emission_type == 'production':
                    CO2_from_production = carbon_emissions[emission_type].values
                elif emission_type == techno:
                    total_carbon_emissions = CO2_per_use + \
                                             carbon_emissions[techno].values
                else:
                    CO2_from_other_consumption[f'CO2_from_{emission_type}_consumption'] = carbon_emissions[
                        emission_type].values
            CO2_after_use = total_carbon_emissions
            idx = pd.MultiIndex.from_tuples(
                [(f'{energy}', f'{techno}')], names=['energy', 'techno'])
            columns_techno = ['energy', 'technology', 'production', 'CO2_from_production',
                              'CO2_per_use', 'CO2_after_use'] + list(CO2_from_other_consumption.keys())
            techno_df = pd.DataFrame([[energy, techno, production_techno, CO2_from_production, CO2_per_use,
                                       CO2_after_use] + list(CO2_from_other_consumption.values())],
                                     index=idx, columns=columns_techno)
            multilevel_df = multilevel_df.append(techno_df)

    return multilevel_df, years
