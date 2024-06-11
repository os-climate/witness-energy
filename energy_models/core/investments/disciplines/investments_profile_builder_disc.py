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

from climateeconomics.glossarycore import GlossaryCore
from sostrades_core.execution_engine.sos_wrapp import SoSWrapp
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import (
    InstanciatedSeries,
    TwoAxesInstanciatedChart,
)
from sostrades_core.execution_engine.design_var.design_var import DesignVar

from energy_models.core.investments.convex_combination_model import (
    ConvexCombinationModel,
)
from energy_models.glossaryenergy import GlossaryEnergy
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
    DESIGN_VAR_DESCRIPTOR = DesignVar.DESIGN_VAR_DESCRIPTOR
    '''
    The DESIGN_VAR_DESCRIPTOR is used by the design variables discipline.
    If it is not an empty dictionnary and if it contains columns that are already in column_names, then
    the corresponding invest profile for this column_name is exported at the years of the poles only. 
    The exported data is then to be used by the design variables discipline instead of the investment Distribution discipline 
    '''

    DESC_IN = {
        'n_profiles': {'type': 'int', 'unit': '-', 'user_level': 3},
        'column_names': {'type': 'list', 'subtype_descriptor': {'list': 'string'}},
        DESIGN_VAR_DESCRIPTOR: {'type': 'dict', 'editable': True, 'structuring': True, 'user_level': 3},
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
        self.columns_to_export_at_poles = None
        self.columns_to_export_at_years = None
        self.years_poles = None # list of years at the poles

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

        if self.DESIGN_VAR_DESCRIPTOR in self.get_data_in():
            design_var_descriptor = self.get_sosdisc_inputs(self.DESIGN_VAR_DESCRIPTOR)
            if column_names is not None:
                self.columns_to_export_at_poles = [col for col in column_names if
                                              col + '_array_mix' in design_var_descriptor.keys()]
                self.columns_to_export_at_years = [col for col in column_names if col not in self.columns_to_export_at_poles]
                if design_var_descriptor is not None and len(self.columns_to_export_at_poles) > 0:
                    dynamic_inputs['nb_poles'] = {'type': 'int', 'unit': '-', 'user_level': 3}


        if df_descriptor is not None and self.columns_to_export_at_poles is not None:
            # the output invest profile can be provided either for all the years or for some limited number of poles.
            # In the second case, the profiles to consider are defined in DESIGN_VAR_DESCRIPTOR as they are provided
            # to the design variables discipline
            df_descriptor_years = df_descriptor.copy()
            list(map(df_descriptor_years.pop, self.columns_to_export_at_poles))
            # should not add the invest mix if all the outputs are given at the poles
            if len(df_descriptor_years.keys()) > 0:
                dynamic_outputs[GlossaryEnergy.invest_mix] = {
                    "type": "dataframe", "unit": "G$",
                    "dataframe_descriptor": df_descriptor_years,
                    "namespace": "ns_invest",  # same namespace as for invest_mix in discipline InvestmentDistribution
                    "visibility": "Shared",
                }
            for var in self.columns_to_export_at_poles:
                df_descriptor_poles = {GlossaryEnergy.Years: ("int", [1900, GlossaryCore.YearEndDefault], False),
                                       var: ("float", [0.0, 1e30], False)
                                       }
                dynamic_outputs[f'{var}_array_mix'] = {
                    "type": "dataframe", "unit": "G$",
                    "dataframe_descriptor": df_descriptor_poles,
                    "namespace": "ns_invest",
                    # same namespace as for invest_mix in discipline InvestmentDistribution
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
            dataframes=[inputs[f'df_{i}'] for i in range(n_profiles)],
        )

        self.model.compute()
        convex_combination_df = self.model.convex_combination_df
        # some data are stored in invest_mix, others in _array_mix
        if len(self.columns_to_export_at_years) > 0:
            outputs = {
                GlossaryEnergy.invest_mix: self.model.convex_combination_df[[GlossaryEnergy.Years] + self.columns_to_export_at_years]
            }
            self.store_sos_outputs_values(outputs)

        if len(self.columns_to_export_at_poles) > 0:
            df = inputs['df_0']
            years = df[GlossaryEnergy.Years] # all profiles should have the same years
            nb_poles = inputs['nb_poles']
            self.years_poles = np.linspace(years.values.min(), years.values.max(), nb_poles, dtype='int') # to avoid interpolation, accept non-even step size between the poles
            self.poles_index = list(df[df[GlossaryEnergy.Years].isin(self.years_poles)].index)
            for col in self.columns_to_export_at_poles: # extract data at the poles
                df = self.model.convex_combination_df[[GlossaryEnergy.Years] + [col]]
                outputs = {col + '_array_mix' : df[df.index.isin(self.poles_index)]}
                self.store_sos_outputs_values(outputs)

    def compute_sos_jacobian(self):
        dict_in = self.get_sosdisc_inputs()
        column_names_list = dict_in['column_names']
        n_profiles = dict_in['n_profiles']
        for i in range(n_profiles):
            for col_name in column_names_list:
                derivative = self.model.d_convex_combination_d_coeff_in(col_name, f'coeff_{i}')
                # some data are stored in invest_mix, others in _array_mix
                if col_name in self.columns_to_export_at_years:
                    self.set_partial_derivative_for_other_types(
                        (GlossaryEnergy.invest_mix, col_name),
                        (f'coeff_{i}',), derivative.reshape((len(derivative), 1))
                        )
                else: #col_name in self.columns_to_export_at_poles:
                    derivative_at_poles = derivative[self.poles_index].reshape((len(self.poles_index), 1)) #extract gradient at the poles only
                    self.set_partial_derivative_for_other_types(
                        (col_name + '_array_mix', col_name),
                        (f'coeff_{i}',), derivative_at_poles
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

        n_profiles = self.get_sosdisc_inputs('n_profiles')
        years = list(self.get_sosdisc_inputs('df_0')[GlossaryEnergy.Years].values)
        column_names = self.get_sosdisc_inputs('column_names')

        graph_years = TwoAxesInstanciatedChart(GlossaryEnergy.Years, f'Invest {GlossaryEnergy.invest_mix} [G$]',
                                         chart_name="Output profile invest")
        graph_poles = TwoAxesInstanciatedChart(GlossaryEnergy.Years, f'Invest array_mix [G$]',
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

            if column in self.columns_to_export_at_years:
                invest_profile_years = self.get_sosdisc_outputs(GlossaryEnergy.invest_mix)
                series_values = list(invest_profile_years[column].values)
                serie_obj = InstanciatedSeries(years, series_values, column, "lines")
                graph_years.add_series(serie_obj)
            elif column in self.columns_to_export_at_poles:
                invest_profile_poles = self.get_sosdisc_outputs(column + '_array_mix')
                series_values = list(invest_profile_poles[column].values)
                serie_obj = InstanciatedSeries(list(self.years_poles), series_values, column + '_array_mix', display_type="scatter",
                                               marker_symbol='circle',
                                               #marker=dict(color='LightSkyBlue', size=20, line=dict(color='MediumPurple', width=2))
                                               )
                graph_poles.add_series(serie_obj)

        if len(self.columns_to_export_at_years) > 0:
            instanciated_charts.append(graph_years)
        if len(self.columns_to_export_at_poles) > 0:
            instanciated_charts.append(graph_poles)

        return instanciated_charts