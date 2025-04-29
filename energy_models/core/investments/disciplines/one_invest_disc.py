'''
Copyright 2022 Airbus SAS
Modifications on 2023/04/21-2024/06/24 Copyright 2023 Capgemini

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
from copy import deepcopy

from climateeconomics.core.core_witness.climateeco_discipline import (
    ClimateEcoDiscipline,
)
from sostrades_core.execution_engine.sos_wrapp import SoSWrapp
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import (
    InstanciatedSeries,
    TwoAxesInstanciatedChart,
)

from energy_models.core.ccus.ccus import CCUS
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.investments.one_invest import OneInvest
from energy_models.glossaryenergy import GlossaryEnergy


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

    investments_df_variable = deepcopy(GlossaryEnergy.InvestmentDf)
    investments_df_variable["namespace"] = GlossaryEnergy.NS_WITNESS

    DESC_IN = {
        GlossaryEnergy.YearStart: ClimateEcoDiscipline.YEAR_START_DESC_IN,
        GlossaryEnergy.YearEnd: GlossaryEnergy.YearEndVar,
        f"{GlossaryEnergy.CCUS}.{GlossaryEnergy.InvestmentsValue}": deepcopy(investments_df_variable),
        f"{GlossaryEnergy.EnergyMix}.{GlossaryEnergy.InvestmentsValue}": deepcopy(investments_df_variable),
        GlossaryEnergy.invest_mix: GlossaryEnergy.invest_mix_df,
        GlossaryEnergy.energy_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                                     'possible_values': EnergyMix.energy_list,
                                     'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy_study',
                                     'editable': False, 'structuring': True},
        GlossaryEnergy.ccs_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                                  'possible_values': CCUS.ccs_list,
                                  'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy_study',
                                  'editable': False,
                                  'structuring': True},
    }

    energy_name = "one_invest"

    DESC_OUT = {
        'all_invest_df': {'type': 'dataframe', 'unit': GlossaryEnergy.TechnoInvestDf['unit']}
    }
    _maturity = 'Research'

    def __init__(self, sos_name, logger: logging.Logger):
        super().__init__(sos_name, logger)
        self.one_invest_model = None

    def init_execution(self):
        self.one_invest_model = OneInvest()

    def setup_sos_disciplines(self):
        '''
        Construct the desc_out to couple energy invest levels to techno_invest_disc
        '''
        dynamic_outputs = {}
        dynamic_inputs = {}

        if GlossaryEnergy.energy_list in self.get_data_in():
            energy_list = self.get_sosdisc_inputs(GlossaryEnergy.energy_list)
            if energy_list is not None:
                for energy in energy_list:
                    if energy == GlossaryEnergy.biomass_dry:
                        pass
                    else:
                        # Add technologies_list to inputs
                        dynamic_inputs[f'{energy}.{GlossaryEnergy.techno_list}'] = {
                            'type': 'list', 'subtype_descriptor': {'list': 'string'}, 'structuring': True,
                            'visibility': 'Shared', 'namespace': 'ns_energy',}
                        if f'{energy}.{GlossaryEnergy.techno_list}' in self.get_data_in():
                            technology_list = self.get_sosdisc_inputs(f'{energy}.{GlossaryEnergy.techno_list}')
                            # Add all invest_level outputs
                            if technology_list is not None:
                                techno_invest_df_energy = deepcopy(GlossaryEnergy.TechnoInvestDf)
                                techno_invest_df_energy["namespace"] = "ns_energy"
                                techno_invest_df_energy["visibility"] = 'Shared'
                                for techno in technology_list:
                                    dynamic_outputs[f'{energy}.{techno}.{GlossaryEnergy.InvestLevelValue}'] = techno_invest_df_energy

        if GlossaryEnergy.ccs_list in self.get_data_in():
            ccs_list = self.get_sosdisc_inputs(GlossaryEnergy.ccs_list)
            if ccs_list is not None:
                for ccs in ccs_list:
                    # Add technologies_list to inputs
                    dynamic_inputs[f'{ccs}.{GlossaryEnergy.techno_list}'] = {
                        'type': 'list', 'subtype_descriptor': {'list': 'string'}, 'structuring': True,
                        'visibility': 'Shared', 'namespace': GlossaryEnergy.NS_CCS,}
                    # Add all invest_level outputs
                    if f'{ccs}.{GlossaryEnergy.techno_list}' in self.get_data_in():
                        technology_list = self.get_sosdisc_inputs(
                            f'{ccs}.{GlossaryEnergy.techno_list}')
                        techno_invest_df_ccs = deepcopy(GlossaryEnergy.TechnoInvestDf)
                        techno_invest_df_ccs["namespace"] = GlossaryEnergy.NS_CCS
                        techno_invest_df_ccs["visibility"] = 'Shared'
                        if technology_list is not None:
                            for techno in technology_list:
                                dynamic_outputs[f'{ccs}.{techno}.{GlossaryEnergy.InvestLevelValue}'] = techno_invest_df_ccs

        self.add_inputs(dynamic_inputs)
        self.add_outputs(dynamic_outputs)

    def run(self):

        input_dict = self.get_sosdisc_inputs()

        self.one_invest_model.compute(input_dict)

        self.store_sos_outputs_values(self.one_invest_model.outputs)

    def compute_sos_jacobian(self):

        pass

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['Invest Distribution']
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
                if chart_filter.filter_key == GlossaryEnergy.Years:
                    pass

        energy_streams = self.get_sosdisc_inputs("energy_list")
        ccs_streams = self.get_sosdisc_inputs("ccs_list")

        instanciated_charts.append(self.get_streams_invests(
            chart_name="Invests in energy",
            stream_list=energy_streams,
            post_proc_section="Energy investments",
            key_chart=True
        ))
        instanciated_charts.append(self.get_streams_invests(
            chart_name="Invests in CCUS",
            stream_list=ccs_streams,
            post_proc_section="CCUS investments",
            key_chart=True
        ))

        for stream in energy_streams:
            instanciated_charts.append(self.get_one_streams_detail(
                chart_name=f"Investments in {stream} technologies",
                stream_name=stream,
                post_proc_section="Energy investments"
            ))

        for stream in ccs_streams:
            instanciated_charts.append(self.get_one_streams_detail(
                chart_name=f"Investments in {stream} technologies",
                stream_name=stream,
                post_proc_section="CCUS investments"
            ))


        return instanciated_charts

    def get_streams_invests(self, chart_name: str,
                            stream_list: list[str], post_proc_section, key_chart:bool):
        all_invests = self.get_sosdisc_outputs("all_invest_df")
        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, GlossaryEnergy.TechnoInvestDf['unit'],
                                             stacked_bar=True,
                                             chart_name=chart_name)

        for stream in stream_list:
            stream_cols = [col for col in all_invests.columns if col.startswith(f'{stream}.')]
            stream_invest = all_invests[stream_cols].sum(axis=1)

            new_series = InstanciatedSeries(all_invests[GlossaryEnergy.Years], stream_invest, stream, 'bar', True)
            new_chart.series.append(new_series)
        new_chart.post_processing_section_name = post_proc_section
        new_chart.post_processing_is_key_chart = key_chart
        return new_chart

    def get_one_streams_detail(self, chart_name: str, stream_name: str, post_proc_section):
        all_invests = self.get_sosdisc_outputs("all_invest_df")
        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, GlossaryEnergy.TechnoInvestDf['unit'],
                                             stacked_bar=True,
                                             chart_name=chart_name)

        stream_cols = [col for col in all_invests.columns if col.startswith(f'{stream_name}.')]
        stream_invest = all_invests[stream_cols].sum(axis=1)

        new_series = InstanciatedSeries(all_invests[GlossaryEnergy.Years], stream_invest, stream_name, 'bar', True)
        new_chart.series.append(new_series)

        new_chart.post_processing_section_name = post_proc_section
        return new_chart