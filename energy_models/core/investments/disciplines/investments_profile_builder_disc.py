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

import numpy as np
from climateeconomics.glossarycore import GlossaryCore
from sostrades_core.execution_engine.sos_wrapp import SoSWrapp
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import (
    InstanciatedSeries,
    TwoAxesInstanciatedChart,
)

from energy_models.core.investments.convex_combination_model import (
    ConvexCombinationModel,
)
from energy_models.glossaryenergy import GlossaryEnergy


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
    '''
    Discipline that generates an output invest profile based on generic input invest profiles and input weights for
    each of those profiles.
    Based on the input boolean EXPORT_PROFILES_AT_POLES, it can either export the output profile at the poles or for all years
    then, the output variable is not named the same, as in the first case it becomes an input of the design_var discipline and
    in the second case it is an input of the investment distribution
    '''

    DESC_IN = {
        'n_profiles': {'type': 'int', 'unit': '-', 'user_level': 3},
        'column_names': {'type': 'list', 'subtype_descriptor': {'list': 'string'}},
        GlossaryEnergy.EXPORT_PROFILES_AT_POLES: {'type': 'bool', 'editable': True, 'structuring': True, 'user_level': 3, 'namespace': 'ns_invest'},
    }

    DESC_OUT = {}

    def setup_sos_disciplines(self):
        '''
        Construct the desc_out to couple energy invest levels to techno_invest_disc
        '''
        dynamic_inputs = {}
        dynamic_outputs = {}
        df_descriptor = None
        column_names = None
        n_profiles = None
        export_profiles_at_poles = None

        if 'n_profiles' in self.get_data_in():
            n_profiles = self.get_sosdisc_inputs('n_profiles')
            if n_profiles is not None:
                for i in range(n_profiles):
                    dynamic_inputs[f'coeff_{i}'] = {'type': 'float', 'unit': '-'}

        if 'column_names' in self.get_data_in():
            column_names = self.get_sosdisc_inputs('column_names')
            if column_names is not None and n_profiles is not None:
                df_descriptor = {GlossaryEnergy.Years: ("int", [1900, GlossaryCore.YearEndDefault], False)}
                df_descriptor.update({col: ("float", [0.0, 1e30], False) for col in column_names})
                for i in range(n_profiles):
                    dynamic_inputs[f'df_{i}'] = {
                        "type": "dataframe", "unit": "G$",
                        "dataframe_descriptor": df_descriptor,
                    }

        if GlossaryEnergy.EXPORT_PROFILES_AT_POLES in self.get_data_in():
            export_profiles_at_poles = self.get_sosdisc_inputs(GlossaryEnergy.EXPORT_PROFILES_AT_POLES)
            if column_names is not None:
                if export_profiles_at_poles is not None and export_profiles_at_poles:
                    dynamic_inputs['nb_poles'] = {'type': 'int', 'unit': '-', 'user_level': 3}

        if df_descriptor is not None and export_profiles_at_poles is not None:
            # the output invest profile can be provided either for all the years or for some limited number of poles.
            if not export_profiles_at_poles:
                dynamic_outputs[GlossaryEnergy.invest_mix] = {
                    "type": "dataframe", "unit": "G$",
                    "dataframe_descriptor": df_descriptor,
                    "namespace": "ns_invest",  # same namespace as for invest_mix in discipline InvestmentDistribution
                    "visibility": "Shared",
                }
            else:
                for var in column_names:
                    dynamic_outputs[f'{var}_array_mix'] = {
                        "type": "array",
                        "unit": "G$",
                        "namespace": "ns_invest",  # same namespace as for design_var discipline inputs as described in design_var_descriptor
                        "visibility": "Shared",
                    }

        self.add_inputs(dynamic_inputs)
        self.add_outputs(dynamic_outputs)

    def compute_poles(self, df, nb_poles):
        '''
        extract the years of the nb_poles and their corresponding index in a given dataframe
        to avoid interpolation, accept non-even step size between the poles
        args
            df [dataframe]: dataframe that contains a column 'Years' (typically, an invest profile)
            nb_poles [int]: number of poles to extract among the list of years
        '''
        years = df[GlossaryEnergy.Years]
        years_poles = np.linspace(years.values.min(), years.values.max(), nb_poles,
                                       dtype='int')  # to avoid interpolation, accept non-even step size between the poles
        poles_index = list(df[df[GlossaryEnergy.Years].isin(years_poles)].index)

        return years_poles, poles_index

    def run(self):  # type: (...) -> None
        self.model = ConvexCombinationModel()

        inputs = self.get_sosdisc_inputs()
        n_profiles = inputs['n_profiles']
        column_names = inputs['column_names']
        export_profiles_at_poles = inputs[GlossaryEnergy.EXPORT_PROFILES_AT_POLES]

        self.model.store_inputs(
            positive_coefficients={f'coeff_{i}': inputs[f'coeff_{i}'] for i in range(n_profiles)},
            dataframes=[inputs[f'df_{i}'] for i in range(n_profiles)],
        )

        self.model.compute()
        convex_combination_df = self.model.convex_combination_df
        # some data are stored in invest_mix, others in _array_mix
        if not export_profiles_at_poles:
            outputs = {
                GlossaryEnergy.invest_mix: self.model.convex_combination_df[[GlossaryEnergy.Years] + column_names]
            }
            self.store_sos_outputs_values(outputs)

        else:
            df = inputs['df_0']
            nb_poles = inputs['nb_poles']
            years_poles, poles_index = self.compute_poles(df, nb_poles)
            for col in column_names:  # extract data at the poles
                df = self.model.convex_combination_df[[GlossaryEnergy.Years] + [col]]
                outputs = {col + '_array_mix': df[df.index.isin(poles_index)][col].values}
                self.store_sos_outputs_values(outputs)

    def compute_sos_jacobian(self):
        dict_in = self.get_sosdisc_inputs()
        column_names_list = dict_in['column_names']
        n_profiles = dict_in['n_profiles']
        df = dict_in['df_0']
        export_profiles_at_poles = dict_in[GlossaryEnergy.EXPORT_PROFILES_AT_POLES]
        poles_index = None  # initialize to avoid pylint error
        if export_profiles_at_poles:
            nb_poles = dict_in['nb_poles']
            years_poles, poles_index = self.compute_poles(df, nb_poles)
        for i in range(n_profiles):
            for col_name in column_names_list:
                derivative = self.model.d_convex_combination_d_coeff_in(col_name, f'coeff_{i}')
                # data can be either stored in invest_mix or in _array_mix
                if not export_profiles_at_poles:
                    self.set_partial_derivative_for_other_types(
                        (GlossaryEnergy.invest_mix, col_name),
                        (f'coeff_{i}',), derivative.reshape((len(derivative), 1))
                        )
                else:
                    derivative_at_poles = derivative[poles_index].reshape((len(poles_index), 1))  # extract gradient at the poles only
                    self.set_partial_derivative(col_name + '_array_mix', f'coeff_{i}', derivative_at_poles)

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

        n_profiles = self.get_sosdisc_inputs('n_profiles')
        column_names = self.get_sosdisc_inputs('column_names')
        df = self.get_sosdisc_inputs('df_0')
        years = list(df[GlossaryEnergy.Years].values)  # all profiles should have the same years
        export_profiles_at_poles = self.get_sosdisc_inputs(GlossaryEnergy.EXPORT_PROFILES_AT_POLES)
        years_poles = None  # initialize to avoid pylint error
        if export_profiles_at_poles:
            nb_poles = self.get_sosdisc_inputs('nb_poles')
            years_poles, poles_index = self.compute_poles(df, nb_poles)

        graph_years = TwoAxesInstanciatedChart(GlossaryEnergy.Years, f'Invest {GlossaryEnergy.invest_mix} [G$]',
                                         chart_name="Output profile invest")
        graph_poles = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Invest array_mix [G$]',
                                         chart_name="Output profile invest at the poles")

        for idx, column in enumerate(column_names):
            chart_name = f"Investments in {column}"

            # we want to plot the generic invest profiles of each column on 1 graph, not 1 graph for each of the n_profile
            if idx < len(column_names):
                chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Invest [G$]',
                                                 chart_name=chart_name)
                for i in range(n_profiles):
                    input_series_values = list(self.get_sosdisc_inputs(f'df_{i}')[column].values)
                    input_serie_obj = InstanciatedSeries(years, input_series_values, f'df_{i}', "lines")
                    chart.add_series(input_serie_obj)

                instanciated_charts.append(chart)

            if not export_profiles_at_poles:
                invest_profile_years = self.get_sosdisc_outputs(GlossaryEnergy.invest_mix)
                series_values = list(invest_profile_years[column].values)
                serie_obj = InstanciatedSeries(years, series_values, column, "lines")
                graph_years.add_series(serie_obj)
            else:
                invest_profile_poles = self.get_sosdisc_outputs(column + '_array_mix')
                series_values = list(invest_profile_poles)
                serie_obj = InstanciatedSeries(list(years_poles), series_values, column + '_array_mix', display_type="scatter",
                                               marker_symbol='circle',
                                               # marker=dict(color='LightSkyBlue', size=20, line=dict(color='MediumPurple', width=2))
                                               )
                graph_poles.add_series(serie_obj)

        if not export_profiles_at_poles:
            instanciated_charts.append(graph_years)
        else:
            instanciated_charts.append(graph_poles)

        return instanciated_charts
