'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/14-2023/11/16 Copyright 2023 Capgemini

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
'''
mode: python; py-indent-offset: 4; tab-width: 8; coding: utf-8
'''
import numpy as np

from climateeconomics.glossarycore import GlossaryCore
from energy_models.core.investments.base_invest import compute_norm_mix
from energy_models.core.investments.energy_invest import EnergyInvest
from sostrades_core.execution_engine.sos_wrapp import SoSWrapp
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart
from sostrades_core.tools.post_processing.pie_charts.instanciated_pie_chart import InstanciatedPieChart


class InvestTechnoDiscipline(SoSWrapp):
    # ontology information
    _ontology_data = {
        'label': 'Energy Technologies Investment Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': '',
        'version': '',
    }
    DESC_IN = {
        GlossaryCore.YearStart: {'type': 'int', 'default': 2020, 'unit': '[-]',
                       'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        GlossaryCore.YearEnd: {'type': 'int', 'default': 2050, 'unit': '[-]',
                     'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        GlossaryCore.InvestLevelValue: {'type': 'dataframe', 'unit': 'G$',
                         'dataframe_descriptor': {GlossaryCore.Years: ('int', [1900, 2100], False),
                                                  GlossaryCore.InvestValue: ('float', None, True)},
                         'dataframe_edition_locked': False},
        'invest_techno_mix': {'type': 'dataframe',
                              'dataframe_descriptor': {GlossaryCore.Years: ('int', [1900, 2100], False),
                                                       'SMR': ('float', None, False),
                                                       'Electrolysis': ('float', None, False),
                                                       'CoalGasification': ('float', None, False),},
                              'dataframe_edition_locked': False},
        GlossaryCore.techno_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'}, 'structuring': True}
    }

    energy_name = "invest_techno"

    DESC_OUT = {
        'techno_invest_df': {'type': 'dataframe', 'unit': 'G$'}
    }
    _maturity = 'Research'

    def init_execution(self):
        self.energy_model = EnergyInvest(self.energy_name)

    def setup_sos_disciplines(self):
        '''
        Construct the desc_out to couple techno invest levels to techno price disciplines
        '''
        dynamic_outputs = {}

        if GlossaryCore.techno_list in self.get_data_in():
            techno_list = self.get_sosdisc_inputs(GlossaryCore.techno_list)
            if techno_list is not None:
                for techno in techno_list:
                    dynamic_outputs[f'{techno}.{GlossaryCore.InvestLevelValue}'] = {
                        'type': 'dataframe', 'unit': 'G$'}

        self.add_outputs(dynamic_outputs)

    def run(self):

        input_dict = self.get_sosdisc_inputs()

        self.energy_model.set_energy_list(input_dict[GlossaryCore.techno_list])
        techno_invest_df, unit = self.energy_model.get_invest_distrib(
            input_dict[GlossaryCore.InvestLevelValue], input_dict['invest_techno_mix'], input_unit='G$', output_unit='G$')

        output_dict = {'techno_invest_df': techno_invest_df}

        for techno in input_dict[GlossaryCore.techno_list]:
            output_dict[f'{techno}.{GlossaryCore.InvestLevelValue}'] = techno_invest_df[[
                GlossaryCore.Years, techno]].rename(columns={techno: GlossaryCore.InvestValue})
        self.store_sos_outputs_values(output_dict)

    def compute_sos_jacobian(self):

        inputs_dict = self.get_sosdisc_inputs()

        years = np.arange(inputs_dict[GlossaryCore.YearStart],
                          inputs_dict[GlossaryCore.YearEnd] + 1)
        norm_mix = compute_norm_mix(
            inputs_dict['invest_techno_mix'], inputs_dict[GlossaryCore.techno_list])
        for techno in inputs_dict[GlossaryCore.techno_list]:
            grad_techno = inputs_dict['invest_techno_mix'][techno].values / \
                          norm_mix.values
            self.set_partial_derivative_for_other_types(
                (f'{techno}.{GlossaryCore.InvestLevelValue}', GlossaryCore.InvestValue), (GlossaryCore.InvestLevelValue, GlossaryCore.InvestValue), np.identity(len(years)) * grad_techno)
            grad_techno_mix = inputs_dict[GlossaryCore.InvestLevelValue][GlossaryCore.InvestValue].values * (
                    norm_mix.values - inputs_dict['invest_techno_mix'][techno].values) / norm_mix.values ** 2
            self.set_partial_derivative_for_other_types(
                (f'{techno}.{GlossaryCore.InvestLevelValue}', GlossaryCore.InvestValue), ('invest_techno_mix', techno),
                np.identity(len(years)) * grad_techno_mix)
            for techno_other in inputs_dict[GlossaryCore.techno_list]:
                if techno != techno_other:
                    grad_techno_mix_other = -inputs_dict[GlossaryCore.InvestLevelValue][GlossaryCore.InvestValue].values * \
                                            inputs_dict['invest_techno_mix'][techno].values / \
                                            norm_mix.values ** 2
                    self.set_partial_derivative_for_other_types(
                        (f'{techno}.{GlossaryCore.InvestLevelValue}', GlossaryCore.InvestValue), ('invest_techno_mix', techno_other),
                        np.identity(len(years)) * grad_techno_mix_other)

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['Invest Distribution']
        chart_filters.append(ChartFilter(
            'Charts Investments', chart_list, chart_list, 'charts_invest'))

        year_start, year_end = self.get_sosdisc_inputs(
            [GlossaryCore.YearStart, GlossaryCore.YearEnd])
        years = list(np.arange(year_start, year_end + 1, 5))
        chart_filters.append(ChartFilter(
            'Years for invest mix', years, [year_start, year_end], GlossaryCore.Years))
        return chart_filters

    def get_post_processing_list(self, filters=None):

        # For the outputs, making a graph for block fuel vs range and blocktime vs
        # range

        instanciated_charts = []
        charts = []
        years_list = [self.get_sosdisc_inputs(GlossaryCore.YearStart)]
        # Overload default value with chart filter
        if filters is not None:
            for chart_filter in filters:
                if chart_filter.filter_key == 'charts_invest':
                    charts = chart_filter.selected_values
                if chart_filter.filter_key == GlossaryCore.Years:
                    years_list = chart_filter.selected_values

        if 'Invest Distribution' in charts:
            techno_invest_df = self.get_sosdisc_outputs(
                'techno_invest_df')
            techno_mix = self.get_sosdisc_inputs(
                'invest_techno_mix')
            techno_list = self.get_sosdisc_inputs(
                GlossaryCore.techno_list)
            chart_name = f'Distribution of Investments vs years'

            new_chart = TwoAxesInstanciatedChart(GlossaryCore.Years, 'Invest [G$]',
                                                 chart_name=chart_name, stacked_bar=True)
            display_techno_list = []

            for techno in techno_list:
                invest = techno_invest_df[techno].values
                # Add total price
                serie = InstanciatedSeries(
                    techno_invest_df[GlossaryCore.Years].values.tolist(),
                    invest.tolist(), techno, 'bar')

                cut_techno_name = techno.split(".")
                display_techno_name = cut_techno_name[len(
                    cut_techno_name) - 1].replace("_", " ")
                display_techno_list.append(display_techno_name)

                new_chart.series.append(serie)

            instanciated_charts.append(new_chart)
            for year in years_list:
                values = [techno_invest_df.loc[techno_invest_df[GlossaryCore.Years]
                                               == year][techno].sum() for techno in techno_list]
                if sum(values) != 0.0:
                    pie_chart = InstanciatedPieChart(
                        f'Technology investments in {year}', display_techno_list, values)
                    instanciated_charts.append(pie_chart)
        return instanciated_charts
