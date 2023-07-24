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

def get_comparison_data(execution_engine, namespace, years):
    var_f_name = f"{namespace}.technologies_list"
    techno_list = execution_engine.dm.get_value(var_f_name)

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
    energy_list = execution_engine.dm.get_value(f"{namespace}.energy_list")
    for energy in energy_list:

        energy_ns = f"{namespace}.EnergyMix.{energy}"

        techno_list = execution_engine.dm.get_value(f"{energy_ns}.technologies_list")

        for techno in techno_list:
            techno_ns = f"{energy_ns}.{techno}"
            #var_short_name=f"{namespace}.technologies_list"
            techno_details= execution_engine.dm.get_value(f"{techno_ns}.techno_detailed_prices")
            #on récupère les colonnes stocker qq part  gros data frame avec toutes les données extraite
    #energy = execution_engine.dm.get_disciplines_with_name(namespace)[0].mdo_discipline_wrapp.wrapper.energy_name
            if  'Opex' in graphs_list:
                for year in YEAR_COMPARISON:
                    new_table = get_comparison_data(execution_engine, namespace, year)
            #new_table = get_figures_table(price_comparision_table_data, str(year))
                    instanciated_charts.append(new_table)

            if 'Capex' in graphs_list:
                chart_name = ' Capex value'
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
        price_per_kWh, years, Capex, label, Opex = [
        ], [], [], [], []
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
            Opex += [np.mean(row['Opex']), ]
            label += [i, ]
            production += [np.sum(row['production']), ]
            invest += [np.sum(row['invest']), ]
            total_CO2 += [np.sum(row['Capex'] *
                                 row['production']), ]
            CO2_taxes_array += [np.mean(CO2_taxes), ]
        customdata = [label, price_per_kWh, Capex,
                      Opex,years]
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
        columns=['production', 'invest', 'Capex', 'price_per_kWh', 'years'])
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
            Capex_techno = total_carbon_emissions
            # Data for scatter plot
            price_per_kWh_techno = techno_disc.get_sosdisc_outputs('techno_prices')[
                f'{techno}'].values
            years_techno = techno_disc.get_sosdisc_outputs('techno_prices')[
                f'{techno}_wotaxes'].values
            idx = pd.MultiIndex.from_tuples(
                [(f'{energy}', f'{techno}')], names=['energy', 'techno'])
            columns_techno = ['energy', 'technology',
                              'production', 'invest',
                              'Capex', 'price_per_kWh',
                              'years']
            techno_df = pd.DataFrame([(energy, techno, production_techno, invest_techno, Capex_techno,
                                       price_per_kWh_techno, years_techno)],
                                     index=idx, columns=columns_techno)
            multilevel_df = multilevel_df.append(techno_df)

    years = np.arange(energy_disc.get_sosdisc_inputs(
        'year_start'), energy_disc.get_sosdisc_inputs('year_end') + 1, 1)

    # If columns is not None, return a subset of multilevel_df with selected
    # columns
    if columns != None and type(columns) == list:
        multilevel_df = pd.DataFrame(multilevel_df[columns])

    return multilevel_df, years



