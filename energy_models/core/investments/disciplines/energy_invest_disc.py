'''
mode: python; py-indent-offset: 4; tab-width: 8; coding: utf-8
Copyright (c) 2020 Airbus SAS.
All rights reserved.
'''
import numpy as np
import pandas as pd

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.investments.base_invest import compute_norm_mix
from energy_models.core.investments.energy_invest import EnergyInvest
from sos_trades_core.execution_engine.sos_discipline import SoSDiscipline
from sos_trades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sos_trades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart
from sos_trades_core.tools.post_processing.pie_charts.instanciated_pie_chart import InstanciatedPieChart


class InvestEnergyDiscipline(SoSDiscipline):
    DESC_IN = {
        'year_start': {'type': 'int', 'default': 2020, 'unit': '[-]',
                       'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'year_end': {'type': 'int', 'default': 2050, 'unit': '[-]',
                     'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'energy_investment': {'type': 'dataframe',
                              'dataframe_descriptor': {'years': ('int',  [1900, 2100], False),
                                                       'energy_investment': ('float',  None, True)},
                              'dataframe_edition_locked': False},
        'scaling_factor_energy_investment': {'type': 'float', 'default': 1e2, 'user_level': 2, 'visibility': 'Shared', 'namespace': 'ns_public'},
        'invest_energy_mix': {'type': 'dataframe',
                              'dataframe_descriptor': {'years': ('int',  [1900, 2100], False)},
                              'dataframe_edition_locked': False},
        'energy_list': {'type': 'string_list', 'possible_values': EnergyMix.energy_list,
                        'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_study', 'editable': False, 'structuring': True}
    }

    energy_name = "invest_energy"

    DESC_OUT = {
        'energy_invest_df': {'type': 'dataframe', 'unit': 'G$'}
    }
    _maturity = 'Research'

    def init_execution(self):
        self.energy_model = EnergyInvest(self.energy_name)

    def setup_sos_disciplines(self):
        '''
        Construct the desc_out to couple energy invest levels to techno_invest_disc
        '''
        dynamic_outputs = {}

        if 'energy_list' in self._data_in:
            energy_list = self.get_sosdisc_inputs('energy_list')
            if energy_list is not None:
                for energy in energy_list:
                    dynamic_outputs[f'{energy}.invest_level'] = {
                        'type': 'dataframe', 'unit': 'G$'}

        self.add_outputs(dynamic_outputs)

    def run(self):

        input_dict = self.get_sosdisc_inputs()
        energy_invest_df = input_dict['energy_investment'].copy(deep=True)
        energy_invest_df['energy_investment'] = input_dict['energy_investment']['energy_investment'] * \
            self.energy_model.rescaling_factor
        self.energy_model.set_energy_list(input_dict['energy_list'])

        scaling_factor_energy_investment = input_dict['scaling_factor_energy_investment']
        scaled_energy_investment = pd.DataFrame(
            {'years': input_dict['energy_investment']['years'], 'energy_investment': input_dict['energy_investment']['energy_investment'] * scaling_factor_energy_investment})

        energy_invest_df, unit = self.energy_model.get_invest_distrib(
            scaled_energy_investment,
            input_dict['invest_energy_mix'],
            input_unit='G$',
            output_unit='G$',
            column_name='energy_investment'
        )

        output_dict = {'energy_invest_df': energy_invest_df}

        for energy in input_dict['energy_list']:
            output_dict[f'{energy}.invest_level'] = energy_invest_df[[
                'years', energy]].rename(columns={energy: 'invest'})
        self.store_sos_outputs_values(output_dict)

    def compute_sos_jacobian(self):

        inputs_dict = self.get_sosdisc_inputs()

        scaling_factor_energy_investment = inputs_dict['scaling_factor_energy_investment']
        years = np.arange(inputs_dict['year_start'],
                          inputs_dict['year_end'] + 1)
        norm_mix = compute_norm_mix(
            inputs_dict['invest_energy_mix'], inputs_dict['energy_list'])

        for energy in inputs_dict['energy_list']:
            grad_energy = inputs_dict['invest_energy_mix'][energy].values / \
                norm_mix.values
            self.set_partial_derivative_for_other_types(
                (f'{energy}.invest_level', 'invest'), ('energy_investment', 'energy_investment'),  scaling_factor_energy_investment * np.identity(len(years)) * grad_energy[:, np.newaxis])

            invest_copy = inputs_dict['energy_investment'].copy(deep=True)
            invest_copy.reset_index(inplace=True)
            invest_copy['energy_investment'] = inputs_dict['energy_investment']['energy_investment'] * \
                scaling_factor_energy_investment

            grad_energy_mix = invest_copy['energy_investment'].values * (
                norm_mix.values - inputs_dict['invest_energy_mix'][energy].values) / norm_mix.values**2
            self.set_partial_derivative_for_other_types(
                (f'{energy}.invest_level', 'invest'), ('invest_energy_mix', energy),  np.identity(len(years)) * grad_energy_mix[:, np.newaxis])
            for energy_other in inputs_dict['energy_list']:
                if energy != energy_other:
                    grad_energy_mix_other = -invest_copy['energy_investment'].values * \
                        inputs_dict['invest_energy_mix'][energy].values / \
                        norm_mix.values**2
                    self.set_partial_derivative_for_other_types(
                        (f'{energy}.invest_level', 'invest'), ('invest_energy_mix', energy_other),  np.identity(len(years)) * grad_energy_mix_other[:, np.newaxis])

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
            energy_invest_df = self.get_sosdisc_outputs(
                'energy_invest_df')
            energy_list = self.get_sosdisc_inputs(
                'energy_list')
            chart_name = f'Distribution of Investments vs years'

            new_chart = TwoAxesInstanciatedChart('years', 'Invest [G$]',
                                                 chart_name=chart_name, stacked_bar=True)

            for energy in energy_list:
                invest = energy_invest_df[energy].values
                # Add total price
                serie = InstanciatedSeries(
                    energy_invest_df['years'].values.tolist(),
                    invest.tolist(), energy, 'bar')

                new_chart.series.append(serie)

            instanciated_charts.append(new_chart)
            for year in years_list:
                values = [energy_invest_df.loc[energy_invest_df['years']
                                               == year][energy].sum() for energy in energy_list]
                if sum(values) != 0.0:
                    pie_chart = InstanciatedPieChart(
                        f'Energy investments in {year}', energy_list, values)
                    instanciated_charts.append(pie_chart)
        return instanciated_charts
