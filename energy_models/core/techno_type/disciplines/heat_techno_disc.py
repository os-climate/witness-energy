'''
Copyright 2023 Capgemini

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

from energy_models.core.stream_type.energy_models.heat import (
    hightemperatureheat,
    lowtemperatureheat,
    mediumtemperatureheat,
)
from energy_models.core.techno_type.techno_disc import TechnoDiscipline
from energy_models.glossaryenergy import GlossaryEnergy


class HeatTechnoDiscipline(TechnoDiscipline):
    DESC_OUT = {
        'heat_flux': {'type': 'dataframe', 'unit': 'TWh/Gha',
                             'dataframe_descriptor': {
                                 GlossaryEnergy.Years: ('int', [1900, GlossaryEnergy.YearEndDefaultCore], True),
                                 'heat_flux': ('float', [1.e-8, 1e30], True),
                             },
                     }
    }

    DESC_OUT.update(TechnoDiscipline.DESC_OUT)

    def get_chart_filter_list(self):
        chart_filters = super().get_chart_filter_list()
        chart_filters[0].extend(['heat_flux'])

        return chart_filters

    def get_post_processing_list(self, filters=None):
        """
        Basic post processing method for the model
        """
        instanciated_charts = super().get_post_processing_list(filters)
        charts = []

        if filters is not None:
            for chart_filter in filters:
                if chart_filter.filter_key == 'charts':
                    charts = chart_filter.selected_values

        heat_flux = self.get_sosdisc_outputs('heat_flux')

        if 'heat_flux' in charts:
            x_data = heat_flux[GlossaryEnergy.Years].values
            y_data = heat_flux['heat_flux'].values
            x_label = GlossaryEnergy.Years
            y_label = 'heat_flux'
            series_name = y_label
            title = 'Detailed heat_flux over the years'
            new_chart = self.get_charts(title, x_data, y_data, x_label, y_label, series_name, True)
            instanciated_charts.append(new_chart)

        return instanciated_charts


    @staticmethod
    def get_charts(title, x_data, y_data, x_label, y_label, series_name, stacked_bar):
        """
        Line graph object for x and y data
        title = string for graph name
        x_data = dataframe
        y_data = dataframe
        x_label = string for x-axis name
        y_label = string for y-axis name
        series_name = string for series name
        stacked_bar = for bar chart stacking
        """

        chart_name = title
        if stacked_bar:
            new_chart = TwoAxesInstanciatedChart(x_label, y_label,
                                                 chart_name=chart_name, stacked_bar=True)
        else:
            new_chart = TwoAxesInstanciatedChart(x_label, y_label,
                                                 chart_name=chart_name)
        serie = InstanciatedSeries(
            x_data.tolist(),
            y_data.tolist(), series_name, 'lines')
        new_chart.series.append(serie)

        return new_chart

class LowHeatTechnoDiscipline(HeatTechnoDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Low Heat Model',
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
    DESC_IN = {GlossaryEnergy.TransportCostValue: {'type': 'dataframe', 'unit': '$/t',
                                                   'visibility': TechnoDiscipline.SHARED_VISIBILITY,
                                                   'namespace': 'ns_heat_low',
                                                   'dataframe_descriptor': {GlossaryEnergy.Years: (
                                                   'int', [1900, GlossaryEnergy.YearEndDefaultCore], False),
                                                                            'transport': ('float', None, True)},
                                                   'dataframe_edition_locked': False},
               GlossaryEnergy.TransportMarginValue: {'type': 'dataframe', 'unit': '%',
                                                     'visibility': TechnoDiscipline.SHARED_VISIBILITY,
                                                     'namespace': 'ns_heat_low',
                                                     'dataframe_descriptor': {GlossaryEnergy.Years: (
                                                     'int', [1900, GlossaryEnergy.YearEndDefaultCore], False),
                                                                              GlossaryEnergy.MarginValue: (
                                                                              'float', None, True)},
                                                     'dataframe_edition_locked': False},
               'data_fuel_dict': {'type': 'dict', 'visibility': TechnoDiscipline.SHARED_VISIBILITY,
                                  'namespace': 'ns_heat_low', 'default': lowtemperatureheat.data_energy_dict},
               }
    DESC_IN.update(HeatTechnoDiscipline.DESC_IN)

    _maturity = 'Research'

    stream_name = lowtemperatureheat.name



class MediumHeatTechnoDiscipline(HeatTechnoDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Medium Heat Model',
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
    DESC_IN = {GlossaryEnergy.TransportCostValue: {'type': 'dataframe', 'unit': '$/t',
                                                   'visibility': TechnoDiscipline.SHARED_VISIBILITY,
                                                   'namespace': 'ns_heat_medium',
                                                   'dataframe_descriptor': {GlossaryEnergy.Years: (
                                                   'int', [1900, GlossaryEnergy.YearEndDefaultCore], False),
                                                                            'transport': ('float', None, True)},
                                                   'dataframe_edition_locked': False},
               GlossaryEnergy.TransportMarginValue: {'type': 'dataframe', 'unit': '%',
                                                     'visibility': TechnoDiscipline.SHARED_VISIBILITY,
                                                     'namespace': 'ns_heat_medium',
                                                     'dataframe_descriptor': {GlossaryEnergy.Years: (
                                                     'int', [1900, GlossaryEnergy.YearEndDefaultCore], False),
                                                                              GlossaryEnergy.MarginValue: (
                                                                              'float', None, True)},
                                                     'dataframe_edition_locked': False},
               'data_fuel_dict': {'type': 'dict', 'visibility': TechnoDiscipline.SHARED_VISIBILITY,
                                  'namespace': 'ns_heat_medium', 'default': mediumtemperatureheat.data_energy_dict},
               }
    DESC_IN.update(HeatTechnoDiscipline.DESC_IN)

    _maturity = 'Research'

    stream_name = mediumtemperatureheat.name




class HighHeatTechnoDiscipline(HeatTechnoDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'High Heat Model',
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
    DESC_IN = {GlossaryEnergy.TransportCostValue: {'type': 'dataframe', 'unit': '$/t',
                                                   'visibility': TechnoDiscipline.SHARED_VISIBILITY,
                                                   'namespace': 'ns_heat_high',
                                                   'dataframe_descriptor': {GlossaryEnergy.Years: (
                                                   'int', [1900, GlossaryEnergy.YearEndDefaultCore], False),
                                                                            'transport': ('float', None, True)},
                                                   'dataframe_edition_locked': False},
               GlossaryEnergy.TransportMarginValue: {'type': 'dataframe', 'unit': '%',
                                                     'visibility': TechnoDiscipline.SHARED_VISIBILITY,
                                                     'namespace': 'ns_heat_high',
                                                     'dataframe_descriptor': {GlossaryEnergy.Years: (
                                                     'int', [1900, GlossaryEnergy.YearEndDefaultCore], False),
                                                                              GlossaryEnergy.MarginValue: (
                                                                              'float', None, True)},
                                                     'dataframe_edition_locked': False},
               'data_fuel_dict': {'type': 'dict', 'visibility': TechnoDiscipline.SHARED_VISIBILITY,
                                  'namespace': 'ns_heat_high', 'default': hightemperatureheat.data_energy_dict},
               # 'flux_input_dict': {'type': 'dict', 'visibility': TechnoDiscipline.SHARED_VISIBILITY,
               #                   'namespace': 'ns_heat_high', 'default': hightemperatureheat.data_energy_dict},
               }
    DESC_IN.update(HeatTechnoDiscipline.DESC_IN)

    _maturity = 'Research'

    stream_name = GlossaryEnergy.hightemperatureheat_energyname



    def get_chart_filter_list(self):
        chart_filters = super().get_chart_filter_list()
        chart_filters[0].extend(['heat_flux'])

        return chart_filters
