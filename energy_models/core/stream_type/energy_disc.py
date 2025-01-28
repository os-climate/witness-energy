'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/14-2024/06/24 Copyright 2023 Capgemini

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

import numpy as np
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import (
    InstanciatedSeries,
    TwoAxesInstanciatedChart,
)
from sostrades_optimization_plugins.models.autodifferentiated_discipline import (
    AutodifferentiedDisc,
)

from energy_models.core.stream_type.stream_disc import StreamDiscipline
from energy_models.glossaryenergy import GlossaryEnergy


class EnergyDiscipline(StreamDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Core Energy Type Model',
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

    unit = "TWh"
    DESC_IN = {GlossaryEnergy.CO2Taxes['var_name']: GlossaryEnergy.CO2Taxes,
               }
    DESC_IN.update(StreamDiscipline.DESC_IN)

    # -- Here are the results of concatenation of each techno prices,consumption and production

    DESC_OUT = {
        GlossaryEnergy.CO2EmissionsValue: {'type': 'dataframe', 'unit': 'kg/kWh'},
        GlossaryEnergy.CO2PerUse: GlossaryEnergy.CO2PerUseDf,
        GlossaryEnergy.CH4PerUse: GlossaryEnergy.CH4PerUseDf,
        GlossaryEnergy.N2OPerUse: GlossaryEnergy.N2OPerUseDf}

    DESC_OUT.update(StreamDiscipline.DESC_OUT)

    _maturity = 'Research'
    stream_name = 'energy'

    def add_additionnal_dynamic_variables(self):
        dynamic_inputs = {}
        dynamic_outputs = {}
        if GlossaryEnergy.techno_list in self.get_data_in():
            techno_list = self.get_sosdisc_inputs(GlossaryEnergy.techno_list)
            if techno_list is not None:
                techno_list = self.get_sosdisc_inputs(GlossaryEnergy.techno_list)
                for techno in techno_list:
                    dynamic_inputs[f'{techno}.{GlossaryEnergy.CO2EmissionsValue}'] = {
                        'type': 'dataframe', 'unit': 'kg/kWh', AutodifferentiedDisc.GRADIENTS: True,
                        "dynamic_dataframe_columns": True}

        return dynamic_inputs, dynamic_outputs

    def found_technos_under_energy(self):
        '''
        Set the default value of the technology list with discipline under the energy which are in possible values
        '''
        my_name = self.get_disc_full_name()
        possible_technos = self.get_data_in()[GlossaryEnergy.techno_list][self.POSSIBLE_VALUES]
        found_technos_list = self.dm.get_discipline_names_with_starting_name(
            my_name)
        short_technos_list = [name.split(
            f'{my_name}.')[-1] for name in found_technos_list if f'{my_name}.' in name]

        possible_short_technos_list = [
            techno for techno in short_technos_list if techno in possible_technos]
        return possible_short_technos_list


    def get_chart_filter_list(self):

        chart_filters = StreamDiscipline.get_chart_filter_list(self)
        chart_filters[0].filter_values.append('CO2 emissions')
        chart_filters[0].selected_values.append('CO2 emissions')

        return chart_filters

    def get_post_processing_list(self, filters=None):

        # For the outputs, making a graph for block fuel vs range and blocktime vs
        # range

        instanciated_charts = StreamDiscipline.get_post_processing_list(
            self, filters)
        charts = []
        # Overload default value with chart filter
        if filters is not None:
            for chart_filter in filters:
                if chart_filter.filter_key == 'charts':
                    charts = chart_filter.selected_values

        if 'CO2 emissions' in charts:
            new_charts = self.get_chart_comparison_carbon_intensity()
            for new_chart in new_charts:
                if new_chart is not None:
                    instanciated_charts.append(new_chart)

            new_charts = self.get_chart_co2_emissions()
            for new_chart in new_charts:
                if new_chart is not None:
                    instanciated_charts.append(new_chart)
        return instanciated_charts

    def get_chart_comparison_carbon_intensity(self):
        new_charts = []
        chart_name = f'Comparison of carbon intensity due to production<br>of {self.stream_name} technologies'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'CO2 emissions [kg/kWh]', chart_name=chart_name)

        technology_list = self.get_sosdisc_inputs(GlossaryEnergy.techno_list)

        for technology in technology_list:
            techno_emissions = self.get_sosdisc_inputs(
                f'{technology}.{GlossaryEnergy.CO2EmissionsValue}')
            year_list = techno_emissions[GlossaryEnergy.Years]
            emission_list = techno_emissions[technology]
            serie = InstanciatedSeries(
                year_list, emission_list, technology, 'lines')
            new_chart.series.append(serie)
        new_charts.append(new_chart)
        chart_name = f'Comparison of carbon intensity for {self.stream_name} technologies (production + use)'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'CO2 emissions [kg/kWh]', chart_name=chart_name)

        co2_per_use = self.get_sosdisc_outputs(
            GlossaryEnergy.CO2PerUse)

        for technology in technology_list:
            techno_emissions = self.get_sosdisc_inputs(
                f'{technology}.{GlossaryEnergy.CO2EmissionsValue}')
            year_list = techno_emissions[GlossaryEnergy.Years]
            emission_list = techno_emissions[technology] + \
                            co2_per_use[GlossaryEnergy.CO2PerUse]
            serie = InstanciatedSeries(
                year_list, emission_list, technology, 'lines')
            new_chart.series.append(serie)

        new_charts.append(new_chart)
        return new_charts

    def get_chart_co2_emissions(self):
        new_charts = []
        chart_name = f'Comparison of CO2 emissions due to production and use<br>of {self.stream_name} technologies'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'CO2 emissions (Mt)', chart_name=chart_name, stacked_bar=True)

        technology_list = self.get_sosdisc_inputs(GlossaryEnergy.techno_list)

        co2_per_use = self.get_sosdisc_outputs(GlossaryEnergy.CO2PerUse)

        stream_production = self.get_sosdisc_outputs(GlossaryEnergy.StreamProductionValue)
        for technology in technology_list:
            techno_emissions = self.get_sosdisc_inputs(f'{technology}.{GlossaryEnergy.CO2EmissionsValue}')
            year_list = techno_emissions[GlossaryEnergy.Years]
            emission_list = techno_emissions[technology] * stream_production[f"{self.stream_name} ({self.unit})"] * 1e3
            serie = InstanciatedSeries(year_list, emission_list, technology, 'bar')
            new_chart.series.append(serie)

        co2_per_use = co2_per_use[GlossaryEnergy.CO2PerUse] * stream_production[f"{self.stream_name} ({self.unit})"] * 1e3
        serie = InstanciatedSeries(year_list, co2_per_use, 'CO2 from use of brut production', 'bar')
        new_chart.series.append(serie)
        new_charts.append(new_chart)

        return new_charts
