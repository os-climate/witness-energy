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

import numpy as np
import pandas as pd
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import (
    InstanciatedSeries,
    TwoAxesInstanciatedChart,
)

from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from energy_models.core.techno_type.disciplines.heat_techno_disc import (
    HighHeatTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.heat.high.geothermal_high_heat.geothermal_high_heat import (
    GeothermalHeat,
)


class GeothermalHighHeatDiscipline(HighHeatTechnoDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Geothermal High Heat Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-gas-pump fa-fw',
        'version': '',
    }
    # -- add specific techno inputs to this
    techno_name = GlossaryEnergy.GeothermalHighHeat
    energy_name = hightemperatureheat.name

    lifetime = 25  # in years # https://www.energy.gov/eere/geothermal/articles/life-cycle-analysis-results-geothermal-systems-comparison-other-power

    techno_infos_dict_default = {
        'Capex_init': 3830,
        # https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2017/Aug/IRENA_Geothermal_Power_2017.pdf
        'Capex_init_unit': '$/kW',
        'Opex_percentage': 0.0287,
        # https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2017/Aug/IRENA_Geothermal_Power_2017.pdf
        'efficiency': 1,  # consumptions and productions already have efficiency included
        'CO2_from_production': 0.122,
        # high GHG concentrations in the reservoir fluid # https://documents1.worldbank.org/curated/en/875761592973336676/pdf/Greenhouse-Gas-Emissions-from-Geothermal-Power-Production.pdf
        'CO2_from_production_unit': 'kg/kWh',
        'maturity': 5,
        'learning_rate': 0.00,
        'full_load_hours': 8760.0,
        'WACC': 0.075,
        'techno_evo_eff': 'no',
        'output_temperature': 500,
        # Average High Temperature, Page Number 152, #https://www.medeas.eu/system/files/documentation/files/D8.11%28D35%29%20Model%20Users%20Manual.pdf
        'mean_temperature': 200,
        'output_temperature_unit': 'K',
        'mean_temperature_unit': 'K',
        'steel_needs': 968,
        # Page:21 #https://www.energy.gov/eere/geothermal/articles/life-cycle-analysis-results-geothermal-systems-comparison-other-power
    }

    # geothermal_high_heat Heat production
    # production in 2019 #https://en.wikipedia.org/wiki/Geothermal_power
    # in TWh
    initial_production = 182500 / 3  # Equally split for High, low and Medium Heat production, #https://www.iea.org/data-and-statistics/charts/direct-use-of-geothermal-energy-world-2012-2024

    distrib = [9.677419355, 7.52688172, 0,
               5.376344086, 4.301075269, 5.376344086, 11.82795699, 21.50537634,
               13.97849462, 9.677419355, 7.52688172, 1.075268817,
               2.150537634, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': 100 / sum(distrib) * np.array(distrib)})  # to review

    flux_input_dict = {'land_rate': 23000, 'land_rate_unit': '$/Gha', }
    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
                      'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'age': ('int', [0, 100], False),
                                                                'distrib': ('float', None, True)},
                                       'dataframe_edition_locked': False},
               

               'flux_input_dict': {'type': 'dict', 'default': flux_input_dict, 'unit': 'defined in dict'},
               }
    DESC_IN.update(HighHeatTechnoDiscipline.DESC_IN)
    # -- add specific techno outputs to this
    DESC_OUT = HighHeatTechnoDiscipline.DESC_OUT
    _maturity = 'Research'

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = GeothermalHeat(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
        self.techno_model.configure_input(inputs_dict)

    def add_additionnal_dynamic_output(self):
        dynamic_outputs = {}
        dynamic_outputs['heat_flux'] = {'type': 'dataframe', 'unit': 'TWh/Gha',
                                        'dataframe_descriptor': {
                                            GlossaryEnergy.Years: ('int', [1900, GlossaryEnergy.YearEndDefaultCore], True),
                                            'heat_flux': ('float', [1.e-8, 1e30], True),
                                            },
                                        }

        return dynamic_outputs

    def run(self):
        '''
        Run for all energy disciplines
        '''

        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model.configure_parameters_update(inputs_dict)
        super().run()
        self.techno_model.compute_heat_flux()

        outputs_dict = {'heat_flux': self.techno_model.heat_flux_distribution}
        
        self.store_sos_outputs_values(outputs_dict)

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
