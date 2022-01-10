'''
mode: python; py-indent-offset: 4; tab-width: 8; coding: utf-8
Copyright (c) 2020 Airbus SAS.
All rights reserved.
'''
import numpy as np

from energy_models.core.investments.base_invest import compute_norm_mix
from energy_models.core.investments.energy_invest import EnergyInvest
from sos_trades_core.execution_engine.sos_discipline import SoSDiscipline
from sos_trades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sos_trades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart
from sos_trades_core.tools.post_processing.pie_charts.instanciated_pie_chart import InstanciatedPieChart

from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.carbon_models.carbon_storage import CarbonStorage


class InvestCCSDiscipline(SoSDiscipline):
    DESC_IN = {
        'year_start': {'type': 'int', 'default': 2020, 'unit': '[-]',
                       'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'year_end': {'type': 'int', 'default': 2050, 'unit': '[-]',
                     'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},

        'ccs_investment': {'type': 'dataframe', 'unit': 'G$',
                           'dataframe_descriptor': {'years': ('int',  [1900, 2100], False),
                                                    'energy_investment': ('float',  None, True)},
                           'dataframe_edition_locked': False},
        'invest_ccs_mix': {'type': 'dataframe',
                           'dataframe_descriptor': {'years': ('int',  [1900, 2100], False)},
                           'dataframe_edition_locked': False},
        'ccs_list': {'type': 'string_list', 'possible_values': [CarbonCapture.name, CarbonStorage.name],
                     'default': [CarbonCapture.name, CarbonStorage.name],
                     'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_study', 'editable': False, 'structuring': True}
    }

    energy_name = "invest_energy"

    DESC_OUT = {
        'ccs_invest_df': {'type': 'dataframe', 'unit': 'G$'}
    }
    _maturity = 'Research'

    def init_execution(self):
        self.energy_model = EnergyInvest(self.energy_name)

    def setup_sos_disciplines(self):
        '''
        Construct the desc_out to couple energy invest levels to techno_invest_disc
        '''
        dynamic_outputs = {}

        if 'ccs_list' in self._data_in:
            ccs_list = self.get_sosdisc_inputs('ccs_list')
            if ccs_list is not None:
                for ccs_name in ccs_list:
                    dynamic_outputs[f'{ccs_name}.invest_level'] = {
                        'type': 'dataframe', 'unit': 'G$'}

        self.add_outputs(dynamic_outputs)

    def run(self):

        input_dict = self.get_sosdisc_inputs()
        ccs_invest_df = input_dict['ccs_investment'].copy(deep=True)
        ccs_invest_df['ccs_investment'] = input_dict['ccs_investment']['energy_investment']
        self.energy_model.set_energy_list(input_dict['ccs_list'])
        ccs_invest_df, unit = self.energy_model.get_invest_distrib(
            ccs_invest_df,
            input_dict['invest_ccs_mix'],
            input_unit='G$',
            output_unit='G$',
            column_name='energy_investment'
        )

        output_dict = {'ccs_invest_df': ccs_invest_df}

        for ccs_name in input_dict['ccs_list']:
            output_dict[f'{ccs_name}.invest_level'] = ccs_invest_df[[
                'years', ccs_name]].rename(columns={ccs_name: 'invest'})
        self.store_sos_outputs_values(output_dict)

    def compute_sos_jacobian(self):

        inputs_dict = self.get_sosdisc_inputs()

        years = np.arange(inputs_dict['year_start'],
                          inputs_dict['year_end'] + 1)
        norm_mix = compute_norm_mix(
            inputs_dict['invest_ccs_mix'], inputs_dict['ccs_list'])
        for energy in inputs_dict['ccs_list']:
            grad_energy = inputs_dict['invest_ccs_mix'][energy].values / \
                norm_mix.values
            self.set_partial_derivative_for_other_types(
                (f'{energy}.invest_level', 'invest'), ('ccs_investment', 'energy_investment'),  np.identity(len(years)) * grad_energy)

            invest_copy = inputs_dict['ccs_investment'].copy(deep=True)
            invest_copy.reset_index(inplace=True)
            invest_copy['ccs_investment'] = inputs_dict['ccs_investment']['energy_investment']

            grad_energy_mix = invest_copy['ccs_investment'].values * (
                norm_mix.values - inputs_dict['invest_ccs_mix'][energy].values) / norm_mix.values**2
            self.set_partial_derivative_for_other_types(
                (f'{energy}.invest_level', 'invest'), ('invest_ccs_mix', energy),  np.identity(len(years)) * grad_energy_mix)
            for energy_other in inputs_dict['ccs_list']:
                if energy != energy_other:
                    grad_energy_mix_other = -invest_copy['ccs_investment'].values * \
                        inputs_dict['invest_ccs_mix'][energy].values / \
                        norm_mix.values**2
                    self.set_partial_derivative_for_other_types(
                        (f'{energy}.invest_level', 'invest'), ('invest_ccs_mix', energy_other),  np.identity(len(years)) * grad_energy_mix_other)

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
            ccs_invest_df = self.get_sosdisc_outputs(
                'ccs_invest_df')
            ccs_list = self.get_sosdisc_inputs(
                'ccs_list')
            chart_name = f'Distribution of Investments vs years'

            new_chart = TwoAxesInstanciatedChart('years', 'Invest [G$]',
                                                 chart_name=chart_name, stacked_bar=True)

            for energy in ccs_list:
                invest = ccs_invest_df[energy].values
                # Add total price
                serie = InstanciatedSeries(
                    ccs_invest_df['years'].values.tolist(),
                    invest.tolist(), energy, 'bar')

                new_chart.series.append(serie)

            instanciated_charts.append(new_chart)
            for year in years_list:
                values = [ccs_invest_df.loc[ccs_invest_df['years']
                                            == year][energy].sum() for energy in ccs_list]
                if sum(values) != 0.0:
                    pie_chart = InstanciatedPieChart(
                        f'CCS investments in {year}', ccs_list, values)
                    instanciated_charts.append(pie_chart)
        return instanciated_charts
