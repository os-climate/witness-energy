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

from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import (
    InstanciatedSeries,
    TwoAxesInstanciatedChart,
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


    _maturity = 'Research'
    stream_name = 'energy'

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
