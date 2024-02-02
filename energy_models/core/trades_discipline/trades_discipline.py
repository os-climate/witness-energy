'''
Copyright 2022 Airbus SAS
Modifications on 2023/09/27-2023/11/16 Copyright 2023 Capgemini

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

from energy_models.glossaryenergy import GlossaryEnergy
from sostrades_core.execution_engine.sos_wrapp import SoSWrapp
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries
from sostrades_core.tools.post_processing.pareto_front_optimal_charts.instanciated_pareto_front_optimal_chart import \
    InstantiatedParetoFrontOptimalChart


class TradesDiscipline(SoSWrapp):
    """
    """

    # ontology information
    _ontology_data = {
        'label': 'Core Energy Trades Model',
        'type': 'Official',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-poll fa-fw',
        'version': '',
    }
    _maturity = 'Research'

    DESC_IN = {'scenario_list': {SoSWrapp.TYPE: 'list', SoSWrapp.SUBTYPE: {'list': 'string'},
                                 SoSWrapp.VISIBILITY:
                                     SoSWrapp.SHARED_VISIBILITY, SoSWrapp.NAMESPACE: 'ns_scatter_scenario',
                                 'structuring': True},
               GlossaryEnergy.YearEnd: {'type': 'int', 'default': 2050, 'unit': '[-]',
                                        'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_public'},
               'scaling_factor_energy_production': {'type': 'float', 'default': 1e3, 'user_level': 2,
                                                    'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                    'namespace': 'ns_public'}}
    DESC_OUT = {}

    def setup_sos_disciplines(self):

        if 'scenario_list' in self.get_data_in():
            scenario_list = self.get_sosdisc_inputs('scenario_list')

            if scenario_list is not None:
                inputs = {}
                ns_value_short = self.ee.ns_manager.get_shared_namespace_value(
                    self, 'ns_scatter_scenario')
                ns_value_long = self.ee.ns_manager.get_shared_namespace_value(
                    self, 'ns_trade_input')
                for scenario in scenario_list:
                    inputs[f'{scenario}{ns_value_long.split(ns_value_short)[1]}.co2_emissions'] = {
                        'type': 'dataframe', 'unit': 'Mt', 'visibility': 'Shared', 'namespace': 'ns_scatter_scenario'}
                    inputs[
                        f'{scenario}{ns_value_long.split(ns_value_short)[1]}.{GlossaryEnergy.EnergyProductionValue}'] = {
                        'type': 'dataframe', 'unit': 'MWh', 'visibility': 'Shared', 'namespace': 'ns_scatter_scenario'}

                self.add_inputs(inputs)

    def run(self):

        pass

    def get_chart_filter_list(self):

        chart_filters = []

        chart_list = ['CO2 emissions vs Energy production']

        chart_filters.append(ChartFilter(
            'Charts', chart_list, chart_list, 'Charts'))

        return chart_filters

    def get_post_processing_list(self, chart_filters=None):

        instanciated_charts = []

        # Overload default value with chart filter
        if chart_filters is not None:
            for chart_filter in chart_filters:
                if chart_filter.filter_key == 'Charts':
                    graphs_list = chart_filter.selected_values
        else:
            graphs_list = [
                'CO2 emissions vs Energy production']

        scenario_list = self.get_sosdisc_inputs(
            'scenario_list')

        dynamic_inputs = self.get_sosdisc_inputs(
            list(self.inst_desc_in.keys()), in_dict=True)

        year_end = self.get_sosdisc_inputs(GlossaryEnergy.YearEnd)
        scaling_factor_energy_production = self.get_sosdisc_inputs(
            'scaling_factor_energy_production')

        """
        -------------
        -------------
        PARETO OPTIMAL CHART
        -------------
        -------------
        """
        if 'CO2 emissions vs Energy production' in graphs_list:

            chart_name = f'CO2 emissions vs Energy production in {year_end}'

            energy_production = {}
            CO2_emissions = {}

            for input, value in dynamic_inputs.items():
                if input.endswith('co2_emissions'):
                    CO2_emissions[input.split('.')[0]] = list(
                        value[value[GlossaryEnergy.Years] == year_end]['Total CO2 emissions'].values)[0] * 1.0e6
                elif input.endswith(GlossaryEnergy.EnergyProductionValue):
                    energy_production[input.split('.')[0]] = list(
                        value[value[GlossaryEnergy.Years] == year_end]['Total production'].values)[
                                                                 0] * 1.0e6 * scaling_factor_energy_production

            min_energy = min(list(energy_production.values()))
            max_energy = max(list(energy_production.values()))
            maxs = max(max_energy, abs(min_energy))
            if maxs >= 1.0e9:
                max_energy /= 1.0e9
                min_energy /= 1.0e9
                legend_letter_energy = 'G'
                factor_energy = 1.0e9
            elif 1.0e9 > maxs >= 1.0e6:
                max_energy /= 1.0e6
                min_energy /= 1.0e6
                legend_letter_energy = 'M'
                factor_energy = 1.0e6
            elif 1.0e6 > maxs >= 1.0e3:
                max_energy /= 1.0e3
                min_energy /= 1.0e3
                legend_letter_energy = 'k'
                factor_energy = 1.0e3
            else:
                legend_letter_energy = ''
                factor_energy = 1.0

            max_value_co2 = max(list(CO2_emissions.values()))

            if max_value_co2 >= 1.0e9:
                max_value_co2 /= 1.0e9
                legend_letter_co2 = 'G'
                factor_co2 = 1.0e9
            elif 1.0e9 > max_value_co2 >= 1.0e6:
                max_value_co2 /= 1.0e6
                legend_letter_co2 = 'M'
                factor_co2 = 1.0e6
            elif 1.0e6 > max_value_co2 >= 1.0e3:
                max_value_co2 /= 1.0e3
                legend_letter_co2 = 'k'
                factor_co2 = 1.0e3
            else:
                legend_letter_co2 = ''
                factor_co2 = 1.0

            new_pareto_chart = InstantiatedParetoFrontOptimalChart(
                abscissa_axis_name=f'Energy production ({legend_letter_energy}Wh)',
                primary_ordinate_axis_name=f'CO2 emissions ({legend_letter_co2}t)',
                abscissa_axis_range=[min_energy -
                                     max_energy * 0.05, max_energy * 1.05],
                primary_ordinate_axis_range=[
                    0.0 - max_value_co2 * 0.05, max_value_co2 * 1.05],
                chart_name=chart_name)

            for scenario in scenario_list:
                new_serie = InstanciatedSeries([energy_production[scenario] / factor_energy],
                                               [CO2_emissions[scenario] / factor_co2],
                                               scenario, 'scatter',
                                               custom_data=f'{scenario}')
                new_pareto_chart.add_serie(new_serie)

            # Calculating and adding pareto front
            sorted_energy_prod = sorted(energy_production.values())
            sorted_scenarios = []
            for val in sorted_energy_prod:
                for scen, energy_prod in energy_production.items():
                    if energy_prod == val:
                        sorted_scenarios.append(scen)

            sorted_list = sorted([[energy_production[scenario], CO2_emissions[scenario]]
                                  for scenario in sorted_scenarios], reverse=True)
            pareto_front = [sorted_list[0]]
            for pair in sorted_list[1:]:
                if pair[1] <= pareto_front[-1][1]:
                    pareto_front.append(pair)

            pareto_front_serie = InstanciatedSeries(
                [pair[0] for pair in pareto_front], [pair[1] for pair in pareto_front], 'Pareto front', 'lines')
            new_pareto_chart.add_pareto_front_optimal(pareto_front_serie)

            instanciated_charts.append(new_pareto_chart)

        return instanciated_charts
