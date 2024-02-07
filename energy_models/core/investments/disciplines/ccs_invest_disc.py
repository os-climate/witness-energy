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
import logging

'''
mode: python; py-indent-offset: 4; tab-width: 8; coding: utf-8
'''
import numpy as np

from energy_models.core.investments.base_invest import compute_norm_mix
from energy_models.core.investments.energy_invest import EnergyInvest
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.carbon_models.carbon_storage import CarbonStorage
from energy_models.glossaryenergy import GlossaryEnergy
from sostrades_core.execution_engine.sos_wrapp import SoSWrapp
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart
from sostrades_core.tools.post_processing.pie_charts.instanciated_pie_chart import InstanciatedPieChart


class InvestCCSDiscipline(SoSWrapp):
    # ontology information
    _ontology_data = {
        'label': 'Energy CCS Investment Model',
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

        'ccs_investment': {'type': 'dataframe', 'unit': 'G$',
                           'dataframe_descriptor': {
                               GlossaryEnergy.Years: ('int', [1900, GlossaryEnergy.YeartEndDefault], False),
                               GlossaryEnergy.EnergyInvestmentsValue: ('float', None, True)},
                           'dataframe_edition_locked': False},
        'invest_ccs_mix': {'type': 'dataframe',
                           'dataframe_descriptor': {
                               GlossaryEnergy.Years: ('int', [1900, GlossaryEnergy.YeartEndDefault], False),
                               GlossaryEnergy.carbon_capture: ('float', None, False),
                               GlossaryEnergy.carbon_storage: ('float', None, False), },
                           'dataframe_edition_locked': False},
        GlossaryEnergy.ccs_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                                  'possible_values': [CarbonCapture.name, CarbonStorage.name],
                                  'default': [CarbonCapture.name, CarbonStorage.name],
                                  'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy_study',
                                  'editable': False,
                                  'structuring': True}
    }

    energy_name = "invest_energy"

    DESC_OUT = {
        'ccs_invest_df': {'type': 'dataframe', 'unit': 'G$'}
    }
    _maturity = 'Research'

    def __init__(self, sos_name, logger: logging.Logger):
        super().__init__(sos_name, logger)
        self.energy_model = None

    def init_execution(self):
        self.energy_model = EnergyInvest(self.energy_name)

    def setup_sos_disciplines(self):
        '''
        Construct the desc_out to couple energy invest levels to techno_invest_disc
        '''
        dynamic_outputs = {}

        if GlossaryEnergy.ccs_list in self.get_data_in():
            ccs_list = self.get_sosdisc_inputs(GlossaryEnergy.ccs_list)
            if ccs_list is not None:
                for ccs_name in ccs_list:
                    dynamic_outputs[f'{ccs_name}.{GlossaryEnergy.InvestLevelValue}'] = {
                        'type': 'dataframe', 'unit': 'G$'}

        self.add_outputs(dynamic_outputs)

    def run(self):

        input_dict = self.get_sosdisc_inputs()
        ccs_invest_df = input_dict['ccs_investment'].copy(deep=True)
        ccs_invest_df['ccs_investment'] = input_dict['ccs_investment'][GlossaryEnergy.EnergyInvestmentsValue]
        self.energy_model.set_energy_list(input_dict[GlossaryEnergy.ccs_list])
        ccs_invest_df, unit = self.energy_model.get_invest_distrib(
            ccs_invest_df,
            input_dict['invest_ccs_mix'],
            input_unit='G$',
            output_unit='G$',
            column_name=GlossaryEnergy.EnergyInvestmentsValue
        )

        output_dict = {'ccs_invest_df': ccs_invest_df}

        for ccs_name in input_dict[GlossaryEnergy.ccs_list]:
            output_dict[f'{ccs_name}.{GlossaryEnergy.InvestLevelValue}'] = ccs_invest_df[[
                GlossaryEnergy.Years, ccs_name]].rename(columns={ccs_name: GlossaryEnergy.InvestValue})
        self.store_sos_outputs_values(output_dict)

    def compute_sos_jacobian(self):

        inputs_dict = self.get_sosdisc_inputs()

        years = np.arange(inputs_dict[GlossaryEnergy.YearStart],
                          inputs_dict[GlossaryEnergy.YearEnd] + 1)
        norm_mix = compute_norm_mix(
            inputs_dict['invest_ccs_mix'], inputs_dict[GlossaryEnergy.ccs_list])
        for energy in inputs_dict[GlossaryEnergy.ccs_list]:
            grad_energy = inputs_dict['invest_ccs_mix'][energy].values / \
                          norm_mix.values
            self.set_partial_derivative_for_other_types(
                (f'{energy}.{GlossaryEnergy.InvestLevelValue}', GlossaryEnergy.InvestValue),
                ('ccs_investment', GlossaryEnergy.EnergyInvestmentsValue),
                np.identity(len(years)) * grad_energy)

            invest_copy = inputs_dict['ccs_investment'].copy(deep=True)
            invest_copy.reset_index(inplace=True)
            invest_copy['ccs_investment'] = inputs_dict['ccs_investment'][GlossaryEnergy.EnergyInvestmentsValue]

            grad_energy_mix = invest_copy['ccs_investment'].values * (
                    norm_mix.values - inputs_dict['invest_ccs_mix'][energy].values) / norm_mix.values ** 2
            self.set_partial_derivative_for_other_types(
                (f'{energy}.{GlossaryEnergy.InvestLevelValue}', GlossaryEnergy.InvestValue), ('invest_ccs_mix', energy),
                np.identity(len(years)) * grad_energy_mix)
            for energy_other in inputs_dict[GlossaryEnergy.ccs_list]:
                if energy != energy_other:
                    grad_energy_mix_other = -invest_copy['ccs_investment'].values * \
                                            inputs_dict['invest_ccs_mix'][energy].values / \
                                            norm_mix.values ** 2
                    self.set_partial_derivative_for_other_types(
                        (f'{energy}.{GlossaryEnergy.InvestLevelValue}', GlossaryEnergy.InvestValue),
                        ('invest_ccs_mix', energy_other),
                        np.identity(len(years)) * grad_energy_mix_other)

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
            ccs_invest_df = self.get_sosdisc_outputs(
                'ccs_invest_df')
            ccs_list = self.get_sosdisc_inputs(
                GlossaryEnergy.ccs_list)
            chart_name = f'Distribution of Investments vs years'

            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Invest [G$]',
                                                 chart_name=chart_name, stacked_bar=True)

            for energy in ccs_list:
                invest = ccs_invest_df[energy].values
                # Add total price
                serie = InstanciatedSeries(
                    ccs_invest_df[GlossaryEnergy.Years].values.tolist(),
                    invest.tolist(), energy, 'bar')

                new_chart.series.append(serie)

            instanciated_charts.append(new_chart)
            for year in years_list:
                values = [ccs_invest_df.loc[ccs_invest_df[GlossaryEnergy.Years]
                                            == year][energy].sum() for energy in ccs_list]
                if sum(values) != 0.0:
                    pie_chart = InstanciatedPieChart(
                        f'CCS investments in {year}', ccs_list, values)
                    instanciated_charts.append(pie_chart)
        return instanciated_charts
