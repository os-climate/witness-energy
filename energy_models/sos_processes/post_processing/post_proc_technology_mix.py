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
import numpy as np
import pandas as pd
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
        0].discipline_wrapp.wrapper.stream_name
    chart_list += [f'{energy} Price data of all technologies']

    # The filters are set to False by default since the graphs are not yet
    # mature
    filters.append(ChartFilter('Charts', chart_list, chart_list, 'Charts'))

    return filters


def get_techno_price_filter_data(execution_engine, namespace, title, price_name, y_label):
    '''
    Extracting Capex, Opex, CO2_Tax and total price from data manager for all technologies in the techno list
    title = string
    price_name = string
    y_label = string
    '''

    filtered_production_technology = 15
    disc = execution_engine.dm.get_disciplines_with_name(namespace)
    disc_input = disc[0].get_sosdisc_inputs()
    energy_list = disc_input[GlossaryEnergy.energy_list]
    techno_list = []
    EnergyDict = {}
    year_list = []
    energy_name_list = []
    var_energyproduction_all_energy_df = pd.DataFrame(columns=[GlossaryEnergy.Years])
    y_incre = 0
    for energ in energy_list:
        var_f_name = f"{namespace}.{energ}.technologies_list"
        var_energyproduction_name = f"{namespace}.{energ}.energy_production_detailed"
        # biomass_dry not having techno list and other than biomass we are extracting energy list
        if GlossaryEnergy.biomass_dry not in var_f_name:
            EnergyDict[f"{energ}"] = {}
            loc_techno_list = execution_engine.dm.get_value(var_f_name)
            result = [f"{energ}." + direction for direction in loc_techno_list]
            techno_list.extend(result)
            EnergyDict[f"{energ}"]['TechnoName'] = loc_techno_list
            var_energyproduction_df = execution_engine.dm.get_value(var_energyproduction_name)
            if y_incre == 0:
                var_energyproduction_all_energy_df = var_energyproduction_df.copy()
                var_energyproduction_all_energy_df.columns = var_energyproduction_all_energy_df.columns.str.replace(
                    energ + " ", energ + ".").str.replace(" (TWh)", "")
            else:
                var_energyproduction_all_energy_df = var_energyproduction_all_energy_df.merge(var_energyproduction_df)
                var_energyproduction_all_energy_df.columns = var_energyproduction_all_energy_df.columns.str.replace(
                    energ + " ", energ + ".").str.replace(" (TWh)", "")  # (r" \(.*\)", "")
                # FIXME: r" is raw string not regex, need to use re.sub
            y_incre += 1

    techno_name_list = []
    techno_price_filter_data = {}
    co2_intensity = {}
    co2_all_years = []
    total_carbon_emissions = None
    # looping energies
    for energyname in EnergyDict.keys():
        energy_name_list.append(energyname)

        # looping technos for each energies
        for techno in EnergyDict[energyname]['TechnoName']:
            # extracting price data from techno_detailed_prices
            techno_prices_f_name = f"{namespace}.{energyname}.{techno}.techno_detailed_prices"
            techno_disc = execution_engine.dm.get_disciplines_with_name(f'{namespace}.{energyname}.{techno}')[0]
            price_details = execution_engine.dm.get_value(techno_prices_f_name)

            techno_name_list.append(techno)
            year_list = price_details[GlossaryEnergy.Years].tolist()
            capex_list = price_details['CAPEX_Part'].tolist()
            energy_costs_List = price_details[techno].tolist()

            # based on price name we are extracting price data
            if price_name == 'CAPEX_Part':
                techno_price_filter_data[energyname + '.' + techno] = capex_list
            else:
                techno_price_filter_data[energyname + '.' + techno] = energy_costs_List

            # Calculate total CO2 intensity
            data_fuel_dict = techno_disc.get_sosdisc_inputs('data_fuel_dict')
            carbon_emissions = techno_disc.get_sosdisc_outputs('CO2_emissions_detailed')
            CO2_per_use = np.zeros(len(year_list))

            if GlossaryEnergy.CO2PerUse in data_fuel_dict and 'high_calorific_value' in data_fuel_dict:
                if data_fuel_dict['CO2_per_use_unit'] == 'kg/kg':
                    CO2_per_use = np.ones(
                        len(year_list)) * data_fuel_dict[GlossaryEnergy.CO2PerUse] / data_fuel_dict[
                                      'high_calorific_value']
                elif data_fuel_dict['CO2_per_use_unit'] == 'kg/kWh':
                    CO2_per_use = np.ones(
                        len(year_list)) * data_fuel_dict[GlossaryEnergy.CO2PerUse]
            for emission_type in carbon_emissions:
                if emission_type == techno:
                    total_carbon_emissions = CO2_per_use + \
                                             carbon_emissions[techno].values
            if total_carbon_emissions is None:
                raise Exception("Error occured for the definition of the variable total_carbon_emissions")
            CO2_per_kWh_techno = total_carbon_emissions
            # Getting data for particular year
            co2_intensity[energyname + '.' + techno] = CO2_per_kWh_techno.tolist()
            # Getting the co2 data for all the years
            co2_all_years.extend(co2_intensity[energyname + '.' + techno])

    # Gathering trace for all the years
    fig = go.Figure()
    key_list = list(techno_price_filter_data.keys())

    for i in range(len(year_list)):
        y_values = []
        co2_values = []
        production_values = []

        for key in techno_price_filter_data.keys():
            y_values.append(techno_price_filter_data[key][i])
            co2_values.append(co2_intensity[key][i])
            production_values.append(var_energyproduction_all_energy_df[key][i])
        # creating dictionary to get all technos, prices and CO2
        data_dict = {'techno': key_list, 'y_values': y_values,
                     'co2': co2_values, 'production': production_values}
        filter_df = pd.DataFrame.from_dict(data_dict)

        # Filtering most producing technologies in descending order based on production values
        techno_filter = filter_df.sort_values(by=['production'], ascending=[False])
        # Extracting data for first 'filtered_production_technology' highest most producing technologies
        # pylint: disable-msg=unsubscriptable-object
        techno_filter_list = techno_filter['techno'].tolist()[:filtered_production_technology]
        y_values = []
        co2_values = []
        for key in techno_filter_list:
            y_values.append(techno_price_filter_data[key][i])
            co2_values.append(co2_intensity[key][i])

        trace = go.Bar(
            x=techno_filter_list,
            y=y_values,
            visible=False,
            marker=dict(
                # set color equal to a variable
                color=co2_values,
                cmin=min(co2_all_years), cmax=max(co2_all_years),
                # one of plotly color scales
                colorscale='RdYlGn_r',
                # enable color scale
                showscale=True,
                colorbar=dict(title='CO2 Intensity (kg/kWh)', thickness=20),
            )
        )
        fig.add_trace(trace)

    steps = []
    for i in range(len(year_list)):
        step = dict(
            method='update',
            args=[{"visible": [False] * len(fig.data)}],
            label=str(year_list[i])
        )
        step["args"][0]["visible"][i] = True
        steps.append(step)

    # Create slider
    sliders = [dict(
        active=0,
        pad=dict(t=50),
        steps=steps
    )]

    # Set figure layout
    layout = go.Layout(
        title=title,
        xaxis=dict(title='Technologies'),
        yaxis=dict(title=y_label + ' ($/MWh)'),
        sliders=sliders,
        barmode='group'
    )
    fig.update_layout(layout)
    fig.update_xaxes(tickangle=25)
    fig.data[0].visible = True

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
    # Sometimes wrapper object is None, TODO Need to find another way to find energy_name
    wrapper_type = execution_engine.dm.get_disciplines_with_name(namespace)[0].discipline_wrapp.wrapper
    if wrapper_type is not None:
        energy = execution_engine.dm.get_disciplines_with_name(namespace)[0].discipline_wrapp.wrapper.stream_name
        if f'{energy} Price data of all technologies' in graphs_list:
            capex_bar_slider_graph = get_techno_price_filter_data(execution_engine, namespace,
                                                                  '15 Most Producing Technologies Capex', 'CAPEX_Part',
                                                                  'Capex')
            instanciated_charts.append(capex_bar_slider_graph)

        energy = execution_engine.dm.get_disciplines_with_name(namespace)[0].discipline_wrapp.wrapper.stream_name
        if f'{energy} Price data of all technologies' in graphs_list:
            total_price_bar_slider_graph = get_techno_price_filter_data(execution_engine, namespace,
                                                                        '15 Most Producing Technologies Price',
                                                                        'PRICE_Part', 'Price')
            instanciated_charts.append(total_price_bar_slider_graph)

    return instanciated_charts
