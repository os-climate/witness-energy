'''
Copyright 2024 Capgemini

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

from energy_models.core.investments.convex_combination_model import ConvexCombinationModel
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, TwoAxesInstanciatedChart
from sostrades_core.execution_engine.sos_wrapp import SoSWrapp
from energy_models.glossaryenergy import GlossaryEnergy
from climateeconomics.glossarycore import GlossaryCore
import numpy as np

class InvestmentsProfileBuilderDisc(SoSWrapp):
    # ontology information
    _ontology_data = {
        'label': 'InvestmentsProfileBuilderDisc',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-coins fa-fw',
        'version': '',
    }

    DESC_IN = {
        'n_profiles': {'type': 'int', 'unit': '-', 'user_level': 3},
        'column_names': {'type': 'list', 'subtype_descriptor': {'list': 'string'}}
    }

    DESC_OUT = {}

    def setup_sos_disciplines(self):
        '''
        Construct the desc_out to couple energy invest levels to techno_invest_disc
        '''
        dynamic_inputs = {}
        dynamic_outputs = {}
        df_descriptor = None

        if 'n_profiles' in self.get_data_in():
            n_profiles = self.get_sosdisc_inputs('n_profiles')
            if n_profiles is not None:
                for i in range(n_profiles):
                    dynamic_inputs[f'coeff_{i}'] = {'type': 'float', 'unit': '-'}

        if 'column_names' in self.get_data_in():
            column_names = self.get_sosdisc_inputs('column_names')
            if column_names is not None and n_profiles is not None:
                df_descriptor = {GlossaryEnergy.Years: ("int", [1900, GlossaryCore.YearEndDefault],False)}
                df_descriptor.update({col: ("float", [0.0, 1e30], False) for col in column_names})
                for i in range(n_profiles):
                    dynamic_inputs[f'df_{i}'] = {
                        "type": "dataframe", "unit": "G$",
                        "dataframe_descriptor": df_descriptor,
                    }

        if df_descriptor is not None:
            dynamic_outputs[GlossaryEnergy.invest_mix] = {
                "type": "dataframe", "unit": "G$",
                "dataframe_descriptor": df_descriptor,
                "namespace": "ns_invest", #same namespace as for invest_mix in discipline InvestmentDistribution
                "visibility": "Shared",
            }

        self.add_inputs(dynamic_inputs)
        self.add_outputs(dynamic_outputs)

    def run(self):  # type: (...) -> None
        self.model = ConvexCombinationModel()

        inputs = self.get_sosdisc_inputs()
        n_profiles = inputs['n_profiles']
        self.model.store_inputs(
            positive_coefficients={f'coeff_{i}': inputs[f'coeff_{i}'] for i in range(n_profiles)},
            dataframes=[inputs[f'df_{i}'] for i in range(n_profiles)]
        )

        self.model.compute()

        outputs = {
            GlossaryEnergy.invest_mix: self.model.convex_combination_df
        }

        self.store_sos_outputs_values(outputs)

    def compute_sos_jacobian(self):
        dict_in = self.get_sosdisc_inputs()
        column_names_list = dict_in['column_names']
        n_profiles = dict_in['n_profiles']
        for col_name in column_names_list:
            for i in range(n_profiles):
                derivative = self.model.d_convex_combination_d_coeff_in(col_name, f'coeff_{i}')
                self.set_partial_derivative_for_other_types(
                    (GlossaryEnergy.invest_mix, col_name),
                    (f'coeff_{i}',), derivative.reshape((6,1))
                    )

    def get_chart_filter_list(self):
        chart_filters = []
        chart_list = ['Invest Distribution']
        chart_filters.append(ChartFilter(
            'Charts Investments', chart_list, chart_list, 'charts_invest'))
        return chart_filters

    def get_post_processing_list(self, filters=None):
        instanciated_charts = []
        charts = []

        # Overload default value with chart filter
        if filters is not None:
            for chart_filter in filters:
                if chart_filter.filter_key == 'charts_invest':
                    charts = chart_filter.selected_values

        invest_profile = self.get_sosdisc_outputs(GlossaryEnergy.invest_mix)
        years = list(invest_profile['years'].values)
        column_names = self.get_sosdisc_inputs('column_names')
        graph_name = "Output profile invest"

        graph = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Invest [G$]',
                                         chart_name=graph_name)

        columns_to_include_in_output_graph = [column for column in column_names if column != GlossaryEnergy.Years]

        for idx, column in enumerate(column_names):
            chart_name = f"Investments in {column}"

            # we want to plot the generic invest profiles of each column on 1 graph, not 1 graph for each of the n_profile
            if idx < len(columns_to_include_in_output_graph):
                chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Invest [G$]',
                                                 chart_name=chart_name)

                n_profiles = self.get_sosdisc_inputs('n_profiles')
                for i in range(n_profiles):
                    input_series_values = list(self.get_sosdisc_inputs(f'df_{i}')[column].values)
                    input_serie_obj = InstanciatedSeries(years, input_series_values, f'df_{i}', "lines")
                    chart.add_series(input_serie_obj)

                instanciated_charts.append(chart)

            if column in columns_to_include_in_output_graph:
                series_values = list(invest_profile[column].values)
                serie_obj = InstanciatedSeries(years, series_values, column, "lines")
                graph.add_series(serie_obj)

        instanciated_charts.append(graph)

        return instanciated_charts