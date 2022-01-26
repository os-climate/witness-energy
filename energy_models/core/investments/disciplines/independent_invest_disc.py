'''
mode: python; py-indent-offset: 4; tab-width: 8; coding: utf-8
Copyright (c) 2020 Airbus SAS.
All rights reserved.
'''
import numpy as np
import pandas as pd

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.investments.base_invest import compute_norm_mix
from energy_models.core.investments.independent_invest import IndependentInvest
from sos_trades_core.execution_engine.sos_discipline import SoSDiscipline
from sos_trades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sos_trades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart
from sos_trades_core.tools.post_processing.pie_charts.instanciated_pie_chart import InstanciatedPieChart
from sos_trades_core.tools.base_functions.exp_min import compute_dfunc_with_exp_min,\
    compute_func_with_exp_min


class IndependentInvestDiscipline(SoSDiscipline):
    energy_mix_name = EnergyMix.name
    DESC_IN = {
        'year_start': {'type': 'int', 'default': 2020, 'unit': '[-]',
                       'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'year_end': {'type': 'int', 'default': 2050, 'unit': '[-]',
                     'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'energy_investment': {'type': 'dataframe', 'unit': '100G$',
                              'dataframe_descriptor': {'years': ('int',  [1900, 2100], False),
                                                       'energy_investment': ('float',  None, True)},
                              'dataframe_edition_locked': False,
                              'visibility': 'Shared', 'namespace': 'ns_witness'},
        'scaling_factor_energy_investment': {'type': 'float', 'default': 1e2, 'user_level': 2, 'visibility': 'Shared', 'namespace': 'ns_public'},
        'invest_mix': {'type': 'dataframe',
                       'dataframe_descriptor': {'years': ('int',  [1900, 2100], False)},
                       'dataframe_edition_locked': False},
        'invest_constraint_ref': {'type': 'float', 'default': 1e2, 'user_level': 2, 'visibility': 'Shared', 'namespace': 'ns_ref'},
        'invest_objective_ref': {'type': 'float', 'default': 1e-1, 'user_level': 2, 'visibility': 'Shared', 'namespace': 'ns_ref'},
        'energy_list': {'type': 'string_list', 'possible_values': EnergyMix.energy_list,
                        'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_study', 'editable': False, 'structuring': True},
        'ccs_list': {'type': 'string_list', 'possible_values': EnergyMix.energy_list,
                     'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_study', 'editable': False, 'structuring': True}
    }

    energy_name = "one_invest"

    DESC_OUT = {
        'invest_constraint': {'type': 'dataframe', 'unit': '', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_functions'},
        'invest_objective': {'type': 'array', 'unit': '', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_functions'}
    }
    _maturity = 'Research'

    def init_execution(self):
        self.independent_invest_model = IndependentInvest()

    def setup_sos_disciplines(self):
        '''
        Construct the desc_out to couple energy invest levels to techno_invest_disc
        '''
        dynamic_outputs = {}
        dynamic_inputs = {}
        if 'energy_list' in self._data_in:
            energy_list = self.get_sosdisc_inputs('energy_list')
            if energy_list is not None:
                for energy in energy_list:
                    # Add technologies_list to inputs
                    dynamic_inputs[f'{energy}.technologies_list'] = {
                        'type': 'string_list', 'structuring': True,
                                'visibility': 'Shared', 'namespace': 'ns_energy'}
                    # Add all invest_level outputs
                    if f'{energy}.technologies_list' in self._data_in:
                        technology_list = self.get_sosdisc_inputs(
                            f'{energy}.technologies_list')
                        if technology_list is not None:
                            for techno in technology_list:
                                dynamic_outputs[f'{energy}.{techno}.invest_level'] = {
                                    'type': 'dataframe', 'unit': 'G$',
                                    'visibility': 'Shared', 'namespace': 'ns_energy'}

        if 'ccs_list' in self._data_in:
            ccs_list = self.get_sosdisc_inputs('ccs_list')
            if ccs_list is not None:
                for ccs in ccs_list:
                    # Add technologies_list to inputs
                    dynamic_inputs[f'{ccs}.technologies_list'] = {
                        'type': 'string_list', 'structuring': True, 'visibility': 'Shared', 'namespace': 'ns_ccs'}
                    # Add all invest_level outputs
                    if f'{ccs}.technologies_list' in self._data_in:
                        technology_list = self.get_sosdisc_inputs(
                            f'{ccs}.technologies_list')
                        if technology_list is not None:
                            for techno in technology_list:
                                dynamic_outputs[f'{ccs}.{techno}.invest_level'] = {
                                    'type': 'dataframe', 'unit': 'G$', 'visibility': 'Shared', 'namespace': 'ns_ccs'}

        self.add_inputs(dynamic_inputs)
        self.add_outputs(dynamic_outputs)

    def run(self):

        input_dict = self.get_sosdisc_inputs()

        invest_constraint_df, invest_objective = self.independent_invest_model.compute_invest_constraint_and_objective(
            input_dict)

        output_dict = {'invest_constraint': invest_constraint_df,
                       'invest_objective': invest_objective}

        for energy in input_dict['energy_list'] + input_dict['ccs_list']:
            for techno in input_dict[f'{energy}.technologies_list']:
                output_dict[f'{energy}.{techno}.invest_level'] = pd.DataFrame({'years': input_dict['energy_investment']['years'].values,
                                                                               'invest': input_dict['invest_mix'][f'{energy}.{techno}'].values})

        self.store_sos_outputs_values(output_dict)

    def compute_sos_jacobian(self):

        inputs_dict = self.get_sosdisc_inputs()

        scaling_factor_energy_investment = inputs_dict['scaling_factor_energy_investment']
        energy_investment = inputs_dict['energy_investment']
        invest_constraint_ref = inputs_dict['invest_constraint_ref']
        invest_objective_ref = inputs_dict['invest_objective_ref']
        years = np.arange(inputs_dict['year_start'],
                          inputs_dict['year_end'] + 1)

        techno_invests = inputs_dict['invest_mix'][[
            col for col in inputs_dict['invest_mix'] if col != 'years']]

        techno_invest_sum = techno_invests.sum(axis=1).values
        energy_invest = energy_investment['energy_investment'].values * \
            scaling_factor_energy_investment
        delta = energy_invest - techno_invest_sum
        exp_min_grad = compute_dfunc_with_exp_min(delta, 1e-6)
        for techno in self.independent_invest_model.distribution_list:
            self.set_partial_derivative_for_other_types(
                (f'{techno}.invest_level', 'invest'), ('invest_mix', techno),  np.identity(len(years)))
            self.set_partial_derivative_for_other_types(
                ('invest_constraint', 'invest_constraint'), ('invest_mix', techno),  -np.identity(len(years)) / invest_constraint_ref)
            self.set_partial_derivative_for_other_types(
                ('invest_objective', 'invest_constraint'), ('invest_mix', techno),  -np.identity(len(years)) / invest_objective_ref / energy_invest * exp_min_grad)

        self.set_partial_derivative_for_other_types(
            ('invest_constraint', 'invest_constraint'), ('energy_investment', 'energy_investment'),  np.identity(len(years)) * scaling_factor_energy_investment / invest_constraint_ref)
        objective_grad = (exp_min_grad * energy_invest - compute_func_with_exp_min(
            delta, 1.0e-6)) / energy_investment['energy_investment'].values**2 / scaling_factor_energy_investment
        self.set_partial_derivative_for_other_types(
            ('invest_objective', 'invest_objective'), ('energy_investment', 'energy_investment'),  np.identity(len(years)) * objective_grad / invest_objective_ref)

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['Invest Distribution', 'Invest Constraint']
        chart_filters.append(ChartFilter(
            'Charts Investments', chart_list, chart_list, 'charts_invest'))

        return chart_filters

    def get_post_processing_list(self, filters=None):

        # For the outputs, making a graph for block fuel vs range and blocktime vs
        # range

        instanciated_charts = []
        charts = []
        # Overload default value with chart filter
        if filters is not None:
            for chart_filter in filters:
                if chart_filter.filter_key == 'charts_invest':
                    charts = chart_filter.selected_values

        if 'Invest Distribution' in charts:
            techno_invests = self.get_sosdisc_inputs(
                'invest_mix')

            chart_name = f'Distribution of investments on each energy vs years'

            new_chart_energy = TwoAxesInstanciatedChart('years', 'Invest [G$]',
                                                        chart_name=chart_name, stacked_bar=True)
            energy_list = self.get_sosdisc_inputs(
                'energy_list')
            ccs_list = self.get_sosdisc_inputs(
                'ccs_list')
            for energy in energy_list + ccs_list:
                techno_list = [
                    col for col in techno_invests.columns if col.startswith(f'{energy}.')]
                short_df = techno_invests[techno_list]
                chart_name = f'Distribution of investments for {energy} vs years'
                new_chart_techno = TwoAxesInstanciatedChart('years', 'Invest [G$]',
                                                            chart_name=chart_name, stacked_bar=True)

                for techno in techno_list:
                    serie = InstanciatedSeries(
                        techno_invests['years'].values.tolist(),
                        short_df[techno].values.tolist(), techno, 'bar')

                    new_chart_techno.series.append(serie)
                instanciated_charts.append(new_chart_techno)
                invest = short_df.sum(axis=1).values
                # Add total price
                serie = InstanciatedSeries(
                    techno_invests['years'].values.tolist(),
                    invest.tolist(), energy, 'bar')

                new_chart_energy.series.append(serie)

            instanciated_charts.insert(0, new_chart_energy)

            if 'Invest Constraint' in charts:

                techno_invests = self.get_sosdisc_inputs(
                    'invest_mix')
                techno_invests_sum = techno_invests[[column for column in techno_invests.columns if column != 'years']].sum(
                    axis=1)
                energy_investment = self.get_sosdisc_inputs(
                    'energy_investment')
                scaling_factor_energy_investment = self.get_sosdisc_inputs(
                    'scaling_factor_energy_investment')

                invest_objective = self.get_sosdisc_outputs(
                    'invest_objective')
                invest_objective_ref = self.get_sosdisc_inputs(
                    'invest_objective_ref')

                if invest_objective is not None:
                    chart_name = 'Delta of distributed and allocated energy investments'
                    new_chart_delta = TwoAxesInstanciatedChart('years', 'Delta investments [G$]',
                                                               chart_name=chart_name)
                    #, secondary_ordinate_axis_name='Constraint'

                    serie = InstanciatedSeries(
                        energy_investment['years'].values.tolist(),
                        (invest_objective * invest_objective_ref).tolist(), '',)
                    new_chart_delta.series.append(serie)

                    instanciated_charts.insert(0, new_chart_delta)

                chart_name = 'Distributed and allocated investments for energy sector '
                new_chart_constraint = TwoAxesInstanciatedChart('years', 'Investments [G$]',
                                                                chart_name=chart_name)
                #, secondary_ordinate_axis_name='Constraint'
                serie = InstanciatedSeries(
                    energy_investment['years'].values.tolist(),
                    (energy_investment['energy_investment'].values * scaling_factor_energy_investment).tolist(), 'Total allocated energy investments',)
                new_chart_constraint.series.append(serie)

                serie = InstanciatedSeries(
                    energy_investment['years'].values.tolist(),
                    techno_invests_sum.values.tolist(), 'Sum of distributed investments',)
                new_chart_constraint.series.append(serie)

                instanciated_charts.insert(0, new_chart_constraint)

        return instanciated_charts
