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
import pandas as pd

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.investments.base_invest import compute_norm_mix
from energy_models.core.investments.energy_invest import EnergyInvest
from energy_models.glossaryenergy import GlossaryEnergy
from sostrades_core.execution_engine.sos_wrapp import SoSWrapp
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart
from sostrades_core.tools.post_processing.pie_charts.instanciated_pie_chart import InstanciatedPieChart


class InvestEnergyDiscipline(SoSWrapp):
    # ontology information
    _ontology_data = {
        'label': 'Energy Investment Model',
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
        GlossaryEnergy.YearStart: {'type': 'int', 'default': GlossaryEnergy.YeartStartDefault, 'unit': '[-]',
                                   'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        GlossaryEnergy.YearEnd: {'type': 'int', 'default': 2050, 'unit': '[-]',
                                 'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        GlossaryEnergy.EnergyInvestmentsValue: {'type': 'dataframe',
                                                'dataframe_descriptor': {GlossaryEnergy.Years: (
                                                'int', [1900, GlossaryEnergy.YeartEndDefault], False),
                                                                         GlossaryEnergy.EnergyInvestmentsValue: (
                                                                         'float', None, True)},
                                                'dataframe_edition_locked': False},
        'scaling_factor_energy_investment': {'type': 'float', 'default': 1e2, 'user_level': 2, 'visibility': 'Shared',
                                             'namespace': 'ns_public'},
        'invest_energy_mix': {'type': 'dataframe',
                              'dataframe_descriptor': {
                                  GlossaryEnergy.Years: ('int', [1900, GlossaryEnergy.YeartEndDefault], False),
                                  GlossaryEnergy.EnergyInvestmentsValue: ('float', None, True),
                                  GlossaryEnergy.methane: ('float', None, True),
                                  GlossaryEnergy.electricity: ('float', None, True),
                                  f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}': ('float', None, True)},
                              'dataframe_edition_locked': False},
        GlossaryEnergy.energy_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                                     'possible_values': EnergyMix.energy_list,
                                     'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy_study',
                                     'editable': False, 'structuring': True}
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

        if GlossaryEnergy.energy_list in self.get_data_in():
            energy_list = self.get_sosdisc_inputs(GlossaryEnergy.energy_list)
            if energy_list is not None:
                for energy in energy_list:
                    dynamic_outputs[f'{energy}.{GlossaryEnergy.InvestLevelValue}'] = {
                        'type': 'dataframe', 'unit': 'G$'}

        self.add_outputs(dynamic_outputs)

    def run(self):

        input_dict = self.get_sosdisc_inputs()
        energy_invest_df = input_dict[GlossaryEnergy.EnergyInvestmentsValue].copy(deep=True)
        energy_invest_df[GlossaryEnergy.EnergyInvestmentsValue] = input_dict[GlossaryEnergy.EnergyInvestmentsValue][
                                                                      GlossaryEnergy.EnergyInvestmentsValue] * \
                                                                  self.energy_model.rescaling_factor
        self.energy_model.set_energy_list(input_dict[GlossaryEnergy.energy_list])

        scaling_factor_energy_investment = input_dict['scaling_factor_energy_investment']
        scaled_energy_investment = pd.DataFrame(
            {GlossaryEnergy.Years: input_dict[GlossaryEnergy.EnergyInvestmentsValue][GlossaryEnergy.Years],
             GlossaryEnergy.EnergyInvestmentsValue: input_dict[GlossaryEnergy.EnergyInvestmentsValue][
                                                        GlossaryEnergy.EnergyInvestmentsValue] * scaling_factor_energy_investment})

        energy_invest_df, unit = self.energy_model.get_invest_distrib(
            scaled_energy_investment,
            input_dict['invest_energy_mix'],
            input_unit='G$',
            output_unit='G$',
            column_name=GlossaryEnergy.EnergyInvestmentsValue
        )

        output_dict = {'energy_invest_df': energy_invest_df}

        for energy in input_dict[GlossaryEnergy.energy_list]:
            output_dict[f'{energy}.{GlossaryEnergy.InvestLevelValue}'] = energy_invest_df[[
                GlossaryEnergy.Years, energy]].rename(columns={energy: GlossaryEnergy.InvestValue})
        self.store_sos_outputs_values(output_dict)

    def compute_sos_jacobian(self):

        inputs_dict = self.get_sosdisc_inputs()

        scaling_factor_energy_investment = inputs_dict['scaling_factor_energy_investment']
        years = np.arange(inputs_dict[GlossaryEnergy.YearStart],
                          inputs_dict[GlossaryEnergy.YearEnd] + 1)
        norm_mix = compute_norm_mix(
            inputs_dict['invest_energy_mix'], inputs_dict[GlossaryEnergy.energy_list])

        for energy in inputs_dict[GlossaryEnergy.energy_list]:
            grad_energy = inputs_dict['invest_energy_mix'][energy].values / \
                          norm_mix.values
            self.set_partial_derivative_for_other_types(
                (f'{energy}.{GlossaryEnergy.InvestLevelValue}', GlossaryEnergy.InvestValue),
                (GlossaryEnergy.EnergyInvestmentsValue, GlossaryEnergy.EnergyInvestmentsValue),
                scaling_factor_energy_investment * np.identity(len(years)) * grad_energy[:, np.newaxis])

            invest_copy = inputs_dict[GlossaryEnergy.EnergyInvestmentsValue].copy(deep=True)
            invest_copy.reset_index(inplace=True)
            invest_copy[GlossaryEnergy.EnergyInvestmentsValue] = inputs_dict[GlossaryEnergy.EnergyInvestmentsValue][
                                                                     GlossaryEnergy.EnergyInvestmentsValue] * \
                                                                 scaling_factor_energy_investment

            grad_energy_mix = invest_copy[GlossaryEnergy.EnergyInvestmentsValue].values * (
                    norm_mix.values - inputs_dict['invest_energy_mix'][energy].values) / norm_mix.values ** 2
            self.set_partial_derivative_for_other_types(
                (f'{energy}.{GlossaryEnergy.InvestLevelValue}', GlossaryEnergy.InvestValue),
                ('invest_energy_mix', energy),
                np.identity(len(years)) * grad_energy_mix[:, np.newaxis])
            for energy_other in inputs_dict[GlossaryEnergy.energy_list]:
                if energy != energy_other:
                    grad_energy_mix_other = -invest_copy[GlossaryEnergy.EnergyInvestmentsValue].values * \
                                            inputs_dict['invest_energy_mix'][energy].values / \
                                            norm_mix.values ** 2
                    self.set_partial_derivative_for_other_types(
                        (f'{energy}.{GlossaryEnergy.InvestLevelValue}', GlossaryEnergy.InvestValue),
                        ('invest_energy_mix', energy_other),
                        np.identity(len(years)) * grad_energy_mix_other[:, np.newaxis])

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['Invest Distribution']
        chart_filters.append(ChartFilter(
            'Charts Investments', chart_list, chart_list, 'charts_invest'))

        year_start, year_end = self.get_sosdisc_inputs(
            [GlossaryEnergy.YearStart, GlossaryEnergy.YearEnd])
        years = list(np.arange(year_start, year_end + 1, 5))
        chart_filters.append(ChartFilter(
            'Years for invest mix', years, [year_start, year_end], GlossaryEnergy.Years))
        return chart_filters

    def get_post_processing_list(self, filters=None):

        # For the outputs, making a graph for block fuel vs range and blocktime vs
        # range

        instanciated_charts = []
        charts = []
        years_list = [self.get_sosdisc_inputs(GlossaryEnergy.YearStart)]
        # Overload default value with chart filter
        if filters is not None:
            for chart_filter in filters:
                if chart_filter.filter_key == 'charts_invest':
                    charts = chart_filter.selected_values
                if chart_filter.filter_key == GlossaryEnergy.Years:
                    years_list = chart_filter.selected_values

        if 'Invest Distribution' in charts:
            energy_invest_df = self.get_sosdisc_outputs(
                'energy_invest_df')
            energy_list = self.get_sosdisc_inputs(
                GlossaryEnergy.energy_list)
            chart_name = f'Distribution of Investments vs years'

            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Invest [G$]',
                                                 chart_name=chart_name, stacked_bar=True)

            for energy in energy_list:
                invest = energy_invest_df[energy].values
                # Add total price
                serie = InstanciatedSeries(
                    energy_invest_df[GlossaryEnergy.Years].values.tolist(),
                    invest.tolist(), energy, 'bar')

                new_chart.series.append(serie)

            instanciated_charts.append(new_chart)
            for year in years_list:
                values = [energy_invest_df.loc[energy_invest_df[GlossaryEnergy.Years]
                                               == year][energy].sum() for energy in energy_list]
                if sum(values) != 0.0:
                    pie_chart = InstanciatedPieChart(
                        f'Energy investments in {year}', energy_list, values)
                    instanciated_charts.append(pie_chart)
        return instanciated_charts
