'''
mode: python; py-indent-offset: 4; tab-width: 8; coding: utf-8
Copyright (c) 2020 Airbus SAS.
All rights reserved.
'''
import numpy as np
import pandas as pd

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
from energy_models.core.investments.base_invest import compute_norm_mix
from energy_models.core.investments.one_invest import OneInvest
from sostrades_core.execution_engine.sos_wrapp import SoSWrapp
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart
from sostrades_core.tools.post_processing.pie_charts.instanciated_pie_chart import InstanciatedPieChart
from climateeconomics.core.core_witness.climateeco_discipline import ClimateEcoDiscipline
from energy_models.core.ccus.ccus import CCUS


class OneInvestDiscipline(SoSWrapp):
    # ontology information
    _ontology_data = {
        'label': 'Investment Distribution Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-share-alt fa-fw',
        'version': '',
    }
    energy_mix_name = EnergyMix.name

    DESC_IN = {
        'year_start': ClimateEcoDiscipline.YEAR_START_DESC_IN,
        'year_end': ClimateEcoDiscipline.YEAR_END_DESC_IN,
        'energy_investment': {'type': 'dataframe', 'unit': '100G$',
                              'dataframe_descriptor': {'years': ('int', [1900, 2100], False),
                                                       'energy_investment': ('float', None, True)},
                              'dataframe_edition_locked': False,
                              'visibility': 'Shared', 'namespace': 'ns_witness'},
        'scaling_factor_energy_investment': {'type': 'float', 'default': 1e2, 'user_level': 2, 'visibility': 'Shared',
                                             'namespace': 'ns_public'},
        'invest_mix': {'type': 'dataframe',
                       'dataframe_descriptor': {'years': ('int', [1900, 2100], False)},
                       'dataframe_edition_locked': False},
        'energy_list': {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                        'possible_values': EnergyMix.energy_list,
                        'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy_study',
                        'editable': False, 'structuring': True},
        'ccs_list': {'type': 'list', 'subtype_descriptor': {'list': 'string'}, 'possible_values': CCUS.ccs_list,
                     'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy_study', 'editable': False,
                     'structuring': True},
        # WIP is_dev to remove once its validated on dev processes
        'is_dev': {'type': 'bool', 'default': False, 'user_level': 2, 'structuring': True,
                   'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_public'}
    }

    energy_name = "one_invest"

    DESC_OUT = {
        'all_invest_df': {'type': 'dataframe', 'unit': 'G$'}
    }
    _maturity = 'Research'

    def init_execution(self):
        self.one_invest_model = OneInvest()

    def setup_sos_disciplines(self):
        '''
        Construct the desc_out to couple energy invest levels to techno_invest_disc
        '''
        dynamic_outputs = {}
        dynamic_inputs = {}

        if 'is_dev' in self.get_data_in():
            is_dev = self.get_sosdisc_inputs('is_dev')
        if 'energy_list' in self.get_data_in():
            energy_list = self.get_sosdisc_inputs('energy_list')
            if energy_list is not None:
                for energy in energy_list:
                    if energy == BiomassDry.name and is_dev == True:
                        pass
                    else:
                        # Add technologies_list to inputs
                        dynamic_inputs[f'{energy}.technologies_list'] = {
                            'type': 'list', 'subtype_descriptor': {'list': 'string'}, 'structuring': True,
                            'visibility': 'Shared', 'namespace': 'ns_energy',
                            'possible_values': EnergyMix.stream_class_dict[energy].default_techno_list,
                            'default': EnergyMix.stream_class_dict[energy].default_techno_list}
                        if f'{energy}.technologies_list' in self.get_data_in():
                            technology_list = self.get_sosdisc_inputs(
                                f'{energy}.technologies_list')
                            # Add all invest_level outputs
                            if technology_list is not None:
                                for techno in technology_list:
                                    dynamic_outputs[f'{energy}.{techno}.invest_level'] = {
                                        'type': 'dataframe', 'unit': 'G$',
                                        'visibility': 'Shared', 'namespace': 'ns_energy',}

        if 'ccs_list' in self.get_data_in():
            ccs_list = self.get_sosdisc_inputs('ccs_list')
            if ccs_list is not None:
                for ccs in ccs_list:
                    # Add technologies_list to inputs
                    dynamic_inputs[f'{ccs}.technologies_list'] = {
                        'type': 'list', 'subtype_descriptor': {'list': 'string'}, 'structuring': True,
                        'visibility': 'Shared', 'namespace': 'ns_ccs',
                        'possible_values': EnergyMix.stream_class_dict[ccs].default_techno_list,
                        'default': EnergyMix.stream_class_dict[ccs].default_techno_list}
                    # Add all invest_level outputs
                    if f'{ccs}.technologies_list' in self.get_data_in():
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
        is_dev = input_dict['is_dev']
        all_invest_df = self.one_invest_model.compute(input_dict)

        output_dict = {'all_invest_df': all_invest_df}

        for energy in input_dict['energy_list'] + input_dict['ccs_list']:
            if energy == BiomassDry.name and is_dev == True:
                pass
            else:
                for techno in input_dict[f'{energy}.technologies_list']:
                    output_dict[f'{energy}.{techno}.invest_level'] = pd.DataFrame(
                        {'years': input_dict['energy_investment']['years'].values,
                         'invest': all_invest_df[f'{energy}.{techno}'].values})

        self.store_sos_outputs_values(output_dict)

    def compute_sos_jacobian(self):

        inputs_dict = self.get_sosdisc_inputs()

        scaling_factor_energy_investment = inputs_dict['scaling_factor_energy_investment']
        years = np.arange(inputs_dict['year_start'],
                          inputs_dict['year_end'] + 1)
        norm_mix = compute_norm_mix(
            inputs_dict['invest_mix'], self.one_invest_model.distribution_list)

        for techno in self.one_invest_model.distribution_list:
            grad_energy = inputs_dict['invest_mix'][techno].values / \
                          norm_mix.values
            self.set_partial_derivative_for_other_types(
                (f'{techno}.invest_level', 'invest'), ('energy_investment', 'energy_investment'),
                scaling_factor_energy_investment * np.identity(len(years)) * grad_energy[:, np.newaxis])

            grad_techno_mix = inputs_dict['energy_investment'][
                                  'energy_investment'].values * scaling_factor_energy_investment * (
                                      norm_mix.values - inputs_dict['invest_mix'][techno].values) / norm_mix.values ** 2
            self.set_partial_derivative_for_other_types(
                (f'{techno}.invest_level', 'invest'), ('invest_mix', techno),
                np.identity(len(years)) * grad_techno_mix[:, np.newaxis])
            for techno_other in self.one_invest_model.distribution_list:
                if techno != techno_other:
                    grad_techno_mix_other = -inputs_dict['energy_investment'][
                        'energy_investment'].values * scaling_factor_energy_investment * \
                                            inputs_dict['invest_mix'][techno].values / \
                                            norm_mix.values ** 2
                    self.set_partial_derivative_for_other_types(
                        (f'{techno}.invest_level', 'invest'), ('invest_mix', techno_other),
                        np.identity(len(years)) * grad_techno_mix_other[:, np.newaxis])

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
            all_invest_df = self.get_sosdisc_outputs(
                'all_invest_df')

            chart_name = f'Distribution of investments on each energy vs years'

            new_chart_energy = TwoAxesInstanciatedChart('years', 'Invest [G$]',
                                                        chart_name=chart_name, stacked_bar=True)
            energy_list = self.get_sosdisc_inputs(
                'energy_list')
            ccs_list = self.get_sosdisc_inputs(
                'ccs_list')
            for energy in energy_list + ccs_list:
                techno_list = [
                    col for col in all_invest_df.columns if col.startswith(f'{energy}.')]
                short_df = all_invest_df[techno_list]
                chart_name = f'Distribution of investments for {energy} vs years'
                new_chart_techno = TwoAxesInstanciatedChart('years', 'Invest [G$]',
                                                            chart_name=chart_name, stacked_bar=True)

                for techno in techno_list:
                    serie = InstanciatedSeries(
                        all_invest_df['years'].values.tolist(),
                        short_df[techno].values.tolist(), techno, 'bar')

                    new_chart_techno.series.append(serie)
                instanciated_charts.append(new_chart_techno)
                invest = short_df.sum(axis=1).values
                # Add total price
                serie = InstanciatedSeries(
                    all_invest_df['years'].values.tolist(),
                    invest.tolist(), energy, 'bar')

                new_chart_energy.series.append(serie)

            instanciated_charts.insert(0, new_chart_energy)

        #             for year in years_list:
        #                 values = [all_invest_df.loc[all_invest_df['years']
        #                                             == year][[
        #                                                 col for col in all_invest_df.columns if col.startswith(f'{energy}.')]].sum(axis=1).values[0] for energy in energy_list + ccs_list]
        #                 if sum(values) != 0.0:
        #                     pie_chart = InstanciatedPieChart(
        #                         f'Energy investments in {year}', energy_list + ccs_list, values)
        #                     instanciated_charts.append(pie_chart)
        return instanciated_charts
