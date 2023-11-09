'''
Copyright 2022 Airbus SAS
Modifications on 2023/04/21-2023/11/09 Copyright 2023 Capgemini

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
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import TwoAxesInstanciatedChart, \
    InstanciatedSeries

import numpy as np


def post_processing_filters(execution_engine, namespace):
    filters = []

    chart_list = ['Factory']
    filters.append(ChartFilter('Charts', filter_values=chart_list,
                               selected_values=chart_list, filter_key='Charts', multiple_selection=True))

    return filters


def post_processings(execution_engine, namespace, filters):
    chart_results = []

    # Overload default value with chart filter
    graphs_list = []
    if filters is not None:
        for chart_filter in filters:
            if chart_filter.filter_key == 'Charts':
                graphs_list.extend(chart_filter.selected_values)

    if 'Factory' in graphs_list:
        energy_list = execution_engine.dm.get_value(
            execution_engine.dm.get_all_namespaces_from_var_name(GlossaryCore.energy_list)[0])
        if len(energy_list) >= 2:
            for energy in energy_list:
                chart = create_chart_factory_comparison_technos(
                    execution_engine, namespace, energy)
                if chart is not None:
                    chart_results.append(chart)
        if not namespace.endswith('AgricultureMix'):
            chart_energy = create_chart_factory_comparison_energy(
                execution_engine, namespace, energy_list)
            chart_results.append(chart_energy)

    return chart_results


def create_chart_factory_comparison_technos(execution_engine, namespace, energy):
    all_ns_detailed_prices = execution_engine.dm.get_all_namespaces_from_var_name(
        GlossaryCore.TechnoDetailedPricesValue)

    energy_detailed_prices = [
        ns for ns in all_ns_detailed_prices if ns.startswith(f'{namespace}.EnergyMix.{energy}')]

    if len(energy_detailed_prices) >= 2:
        chart_name = f'Factory for each {energy} technologies over the years'

        new_chart = TwoAxesInstanciatedChart(GlossaryCore.Years, 'Factory [$/MWh]',
                                             chart_name=chart_name)
        for ns in energy_detailed_prices:
            techno_detailed_prices = execution_engine.dm.get_value(ns)
            techno_name = ns.replace(f'{namespace}.{energy}.', '').replace(
                '.{GlossaryCore.TechnoDetailedPricesValue}', '')
            years = techno_detailed_prices[GlossaryCore.Years].values.tolist()
            factory = techno_detailed_prices[f'{techno_name}_factory'].values.tolist(
            )
            serie = InstanciatedSeries(years, factory, techno_name)

            new_chart.series.append(serie)
        return new_chart
    else:
        return None


def create_chart_factory_comparison_energy(execution_engine, namespace, energy_list):
    all_ns_detailed_prices = execution_engine.dm.get_all_namespaces_from_var_name(
        GlossaryCore.TechnoDetailedPricesValue)
    mean_factory = {}

    for energy in energy_list:
        if energy == 'biomass_dry':
            continue
        ns_energy = f'{namespace}.{energy}'
        energy_production = execution_engine.dm.get_value(f'{ns_energy}.{GlossaryCore.EnergyProductionValue}')
        energy_detailed_prices = [
            ns for ns in all_ns_detailed_prices if ns.startswith(f'{namespace}.{energy}')]
        years = energy_production[GlossaryCore.Years].values
        factory_mean = np.zeros(len(years))
        for techno in energy_detailed_prices:
            techno_name = techno.replace(f'{ns_energy}.', '').replace(
                '.{GlossaryCore.TechnoDetailedPricesValue}', '')
            techno_detailed_prices = execution_engine.dm.get_value(techno)
            factory_techno = techno_detailed_prices[f'{techno_name}_factory'].values
            factory_mean += factory_techno

        mean_factory[energy] = factory_mean / len(energy_detailed_prices)
    chart_name = f'Mean Factory for all energy over the years'

    new_chart = TwoAxesInstanciatedChart(GlossaryCore.Years, 'Factory [$/MWh]',
                                         chart_name=chart_name)
    for energy, value in mean_factory.items():
        serie = InstanciatedSeries(years.tolist(), value.tolist(), energy)
        new_chart.series.append(serie)
    return new_chart
