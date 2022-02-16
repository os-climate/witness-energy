'''
mode: python; py-indent-offset: 4; tab-width: 8; coding: utf-8
Copyright (c) 2020 Airbus SAS.
All rights reserved.
'''
import numpy as np

from energy_models.core.investments.energy_invest import EnergyInvest
from energy_models.core.investments.base_invest import compute_norm_mix
from sos_trades_core.execution_engine.sos_discipline import SoSDiscipline
from sos_trades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sos_trades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart
from sos_trades_core.tools.post_processing.pie_charts.instanciated_pie_chart import InstanciatedPieChart


class InvestTechnoDiscipline(SoSDiscipline):

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
        'year_start': {'type': 'int', 'default': 2020, 'unit': '[-]',
                       'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'year_end': {'type': 'int', 'default': 2050, 'unit': '[-]',
                     'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'invest_level': {'type': 'dataframe', 'unit': 'G$',
                         'dataframe_descriptor': {'years': ('int',  [1900, 2100], False),
                                                  'invest': ('float',  None, True)},
                         'dataframe_edition_locked': False},
        'invest_techno_mix': {'type': 'dataframe',
                              'dataframe_descriptor': {'years': ('int',  [1900, 2100], False)},
                              'dataframe_edition_locked': False},
        'technologies_list': {'type': 'string_list', 'structuring': True}
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

        if 'technologies_list' in self._data_in:
            techno_list = self.get_sosdisc_inputs('technologies_list')
            if techno_list is not None:
                for techno in techno_list:
                    dynamic_outputs[f'{techno}.invest_level'] = {
                        'type': 'dataframe', 'unit': 'G$'}

        self.add_outputs(dynamic_outputs)

    def run(self):

        input_dict = self.get_sosdisc_inputs()

        self.energy_model.set_energy_list(input_dict['technologies_list'])
        techno_invest_df, unit = self.energy_model.get_invest_distrib(
            input_dict['invest_level'], input_dict['invest_techno_mix'], input_unit='G$', output_unit='G$')

        output_dict = {'techno_invest_df': techno_invest_df}

        for techno in input_dict['technologies_list']:
            output_dict[f'{techno}.invest_level'] = techno_invest_df[[
                'years', techno]].rename(columns={techno: 'invest'})
        self.store_sos_outputs_values(output_dict)

    def compute_sos_jacobian(self):

        inputs_dict = self.get_sosdisc_inputs()

        years = np.arange(inputs_dict['year_start'],
                          inputs_dict['year_end'] + 1)
        norm_mix = compute_norm_mix(
            inputs_dict['invest_techno_mix'], inputs_dict['technologies_list'])
        for techno in inputs_dict['technologies_list']:
            grad_techno = inputs_dict['invest_techno_mix'][techno].values / \
                norm_mix.values
            self.set_partial_derivative_for_other_types(
                (f'{techno}.invest_level', 'invest'), ('invest_level', 'invest'),  np.identity(len(years)) * grad_techno)
            grad_techno_mix = inputs_dict['invest_level']['invest'].values * (
                norm_mix.values - inputs_dict['invest_techno_mix'][techno].values) / norm_mix.values**2
            self.set_partial_derivative_for_other_types(
                (f'{techno}.invest_level', 'invest'), ('invest_techno_mix', techno),  np.identity(len(years)) * grad_techno_mix)
            for techno_other in inputs_dict['technologies_list']:
                if techno != techno_other:
                    grad_techno_mix_other = -inputs_dict['invest_level']['invest'].values * \
                        inputs_dict['invest_techno_mix'][techno].values / \
                        norm_mix.values**2
                    self.set_partial_derivative_for_other_types(
                        (f'{techno}.invest_level', 'invest'), ('invest_techno_mix', techno_other),  np.identity(len(years)) * grad_techno_mix_other)

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['Invest Distribution']
        chart_filters.append(ChartFilter(
            'Charts Investments', chart_list, chart_list, 'charts_invest'))

        year_start, year_end = self.get_sosdisc_inputs(
            ['year_start', 'year_end'])
        years = list(np.arange(year_start, year_end + 1, 5))
        chart_filters.append(ChartFilter(
            'Years for invest mix', years, [year_start, year_end], 'years'))
        return chart_filters

    def get_post_processing_list(self, filters=None):

        # For the outputs, making a graph for block fuel vs range and blocktime vs
        # range

        instanciated_charts = []
        charts = []
        years_list = [self.get_sosdisc_inputs('year_start')]
        # Overload default value with chart filter
        if filters is not None:
            for chart_filter in filters:
                if chart_filter.filter_key == 'charts_invest':
                    charts = chart_filter.selected_values
                if chart_filter.filter_key == 'years':
                    years_list = chart_filter.selected_values

        if 'Invest Distribution' in charts:
            techno_invest_df = self.get_sosdisc_outputs(
                'techno_invest_df')
            techno_mix = self.get_sosdisc_inputs(
                'invest_techno_mix')
            techno_list = self.get_sosdisc_inputs(
                'technologies_list')
            chart_name = f'Distribution of Investments vs years'

            new_chart = TwoAxesInstanciatedChart('years', 'Invest [G$]',
                                                 chart_name=chart_name, stacked_bar=True)
            display_techno_list = []

            for techno in techno_list:
                invest = techno_invest_df[techno].values
                # Add total price
                serie = InstanciatedSeries(
                    techno_invest_df['years'].values.tolist(),
                    invest.tolist(), techno, 'bar')

                cut_techno_name = techno.split(".")
                display_techno_name = cut_techno_name[len(
                    cut_techno_name) - 1].replace("_", " ")
                display_techno_list.append(display_techno_name)

                new_chart.series.append(serie)

            instanciated_charts.append(new_chart)
            for year in years_list:
                values = [techno_invest_df.loc[techno_invest_df['years']
                                               == year][techno].sum() for techno in techno_list]
                if sum(values) != 0.0:
                    pie_chart = InstanciatedPieChart(
                        f'Technology investments in {year}', display_techno_list, values)
                    instanciated_charts.append(pie_chart)
        return instanciated_charts
