'''
Copyright 2022 Airbus SAS
Modifications on 2023/04/21-2023/11/16 Copyright 2023 Capgemini

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

from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart

'''
mode: python; py-indent-offset: 4; tab-width: 8; coding: utf-8
'''

from sostrades_core.execution_engine.sos_wrapp import SoSWrapp


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

    DESC_IN = {'n_profiles': {'type': 'int', 'unit': '-', 'user_level': 3},
               'column_names': {'type': 'list', 'subtype_descriptor': {'list': 'string'}}
               }

    DESC_OUT = {}

    def setup_sos_disciplines(self):
        '''
        Construct the desc_out to couple energy invest levels to techno_invest_disc
        '''
        dynamic_inputs = {}
        dynamic_outputs = {}

        n_profiles = None
        df_descriptor = None
        if 'n_profiles' in self.get_data_in():
            n_profiles = self.get_sosdisc_inputs(['n_profiles'])
            if n_profiles is not None:
                for i in range(n_profiles):
                    dynamic_inputs[f'coeff_{i}'] = {'type': 'float', 'unit': '-'}

        if 'column_names' in self.get_data_in():
            column_names = self.get_sosdisc_inputs(['column_names'])
            if column_names is not None and n_profiles is not None:
                df_descriptor = {col: ("float", [0.0, 1e30], False) for col in column_names}
                for i in range(n_profiles):
                    dynamic_inputs[f'df_{i}'] = {
                        "type": "dataframe", "unit": "G$",
                        "dataframe_descriptor": df_descriptor,
                    }

        if df_descriptor is not None:
            dynamic_outputs['invest_profile'] = {
                "type": "dataframe", "unit": "G$",
                "dataframe_descriptor": df_descriptor,
            }

        self.add_inputs(dynamic_inputs)
        self.add_outputs(dynamic_outputs)

    def run(self):  # type: (...) -> None
        model = ConvexCombinationModel()

        inputs = self.get_sosdisc_inputs()
        n_profiles = inputs['n_profiles']
        model.store_inputs(
            positive_coefficients={f'coeff_{i}': inputs[f'coeff_{i}'] for i in range(n_profiles)},
            dataframes=[inputs[f'df_{i}'] for i in range(n_profiles)]
        )

        model.compute()

        outputs = {
            'invest_profile': model.convex_combination_df
        }

        self.store_sos_outputs_values(outputs)

    def compute_sos_jacobian(self):
        pass
    def get_chart_filter_list(self):
        return []
    def get_post_processing_list(self, filters=None):
        # un graphe qui montre pour chaque colomne, par ex : renewable, les invests dans le renouvelable des n_coefficients chacun des profils selon les années.
        invest_profile = self.get_sosdisc_outputs('invest_profile')
        years = invest_profile['years'].values
        column_names = self.get_sosdisc_inputs(['column_names'])
        charts = []

        for column in column_names:
            chart_data = {
                'years': years,
                'values': list(invest_profile[column].values),
                'label': column
            }
            charts.append(chart_data)

            # Créer un graphique pour chq column
            new_chart = TwoAxesInstanciatedChart(chart_data['years'], chart_data['values'],
                                                     x_label=years, y_label='Invest [G$]',
                                                     chart_name=f"Investments in {chart_data['label']}",
                                                     stacked_bar=True)

            charts.append(new_chart)


        for new_chart in charts:
            new_chart.to_plotly().show()

            return charts
        return []