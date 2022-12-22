'''
Copyright 2022 Airbus SAS

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
import scipy.interpolate as sc

from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
from sostrades_core.execution_engine.sos_wrapp import SoSWrapp
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart
from climateeconomics.core.core_witness.climateeco_discipline import ClimateEcoDiscipline


def get_static_CO2_emissions(years):

    resources_CO2_emissions_dict = {'years': years}

    resources_CO2_emissions_dict.update({ResourceGlossary.GlossaryDict[resource]['name']:
                                         ResourceGlossary.GlossaryDict[resource]['CO2_emissions'] for resource in ResourceGlossary.GlossaryDict.keys()})
    return pd.DataFrame(resources_CO2_emissions_dict)


def get_static_prices(years):

    year_co2 = [2020, 2025, 2030, 2035, 2040, 2045, 2050]

    # $/t
    price_co2 = [40.0, 45.0, 52.0, 63.0, 74.0, 96.0, 119.0]

    func = sc.interp1d(year_co2, price_co2,
                       kind='linear', fill_value='extrapolate')

    resources_prices_default_dict = {'years': years,
                                     ResourceGlossary.GlossaryDict['CO2']['name']: func(years)}

    resources_prices_default_dict.update(
        {ResourceGlossary.GlossaryDict[resource]['name']: ResourceGlossary.GlossaryDict[resource]['price'] for resource in ResourceGlossary.GlossaryDict.keys()})

    return pd.DataFrame(resources_prices_default_dict)


class ResourcesDisc(SoSWrapp):

    # ontology information
    _ontology_data = {
        'label': 'Energy Data Resources Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-cubes fa-fw',
        'version': '',
    }
    year_start_default = 2020
    year_end_default = 2050

    years = np.arange(year_start_default, year_end_default + 1)

    DESC_IN = {'year_start': ClimateEcoDiscipline.YEAR_START_DESC_IN,
               'year_end': ClimateEcoDiscipline.YEAR_END_DESC_IN,
               'resources_price': {'type': 'dataframe', 'unit': '[$/t]',
                                   'dataframe_descriptor': {'years': ('int',  [1900, 2100], False)},
                                   'dataframe_edition_locked': False,
                                   'default': get_static_prices(years)},
               'resources_CO2_emissions': {'type': 'dataframe', 'unit': '[kgCO2/kg]',
                                           'dataframe_descriptor': {'years': ('int',  [1900, 2100], False)},
                                           'dataframe_edition_locked': False,
                                           'default': get_static_CO2_emissions(years)}}

    DESC_OUT = {

        'resources_price': {'type': 'dataframe', 'unit': '[$/t]', 'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy_study'},
        'resources_CO2_emissions': {'type': 'dataframe', 'unit': '[kgCO2/kg]', 'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy_study'}
    }

    def setup_sos_disciplines(self):

        if self.get_data_in() is not None:
            if 'year_start' in self.get_data_in():
                year_start, year_end = self.get_sosdisc_inputs(
                    ['year_start', 'year_end'])
                years = np.arange(year_start, year_end + 1)
                resources_price = self.get_sosdisc_inputs(
                    'resources_price')
                new_default_prices = get_static_prices(years)
                new_default_emissions = get_static_CO2_emissions(years)

                # If the value of the df is the default we specified, we need to modify also the value
                #(if the value is different it is a user value do not modify the value)
                if resources_price is None or len(resources_price['years'].values) != len(years):
                    self.update_default_value(
                        'resources_price', self.IO_TYPE_IN, new_default_prices)
                    self.update_default_value(
                        'resources_CO2_emissions', self.IO_TYPE_IN, new_default_emissions)

    def run(self):
        """

        """
        year_start = self.get_sosdisc_inputs('year_start')
        year_end = self.get_sosdisc_inputs('year_end')

        years = np.arange(year_start, year_end + 1)

        resources_price = self.get_sosdisc_inputs('resources_price')

        co2_emissions = self.get_sosdisc_inputs('resources_CO2_emissions')

        outputs_dict = {'resources_price': resources_price,
                        'resources_CO2_emissions': co2_emissions}
        # -- store outputs
        self.store_sos_outputs_values(outputs_dict)

    def compute_sos_jacobian(self):
        pass

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['Resources prices', 'Resources CO2 emissions']
        chart_filters.append(ChartFilter(
            'Charts', chart_list, chart_list, 'charts'))

        return chart_filters

    def get_post_processing_list(self, filters=None):

        instanciated_charts = []
        charts = []
        # Overload default value with chart filter
        if filters is not None:
            for chart_filter in filters:
                if chart_filter.filter_key == 'charts':
                    charts = chart_filter.selected_values

        if 'Resources prices' in charts:
            new_chart = self.get_chart_prices_in_dollar_kg()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'Resources CO2 emissions' in charts:
            new_chart = self.get_chart_CO2_emissions()
            if new_chart is not None:
                instanciated_charts.append(new_chart)
        return instanciated_charts

    def get_chart_prices_in_dollar_kg(self):

        resources_price = self.get_sosdisc_outputs(
            'resources_price')
        chart_name = f'Resources prices'

        new_chart = TwoAxesInstanciatedChart('Years', 'Prices [$/t]',
                                             chart_name=chart_name)

        columns = list(resources_price.columns)
        for column in columns:
            if column != 'years':
                values = resources_price[column].values
                serie = InstanciatedSeries(
                    resources_price['years'].values.tolist(),
                    values.tolist(), f'{column} price', 'lines')
                new_chart.series.append(serie)

        return new_chart

    def get_chart_CO2_emissions(self):

        resources_co2_emissions = self.get_sosdisc_outputs(
            'resources_CO2_emissions')
        chart_name = f'Resources CO2 emissions in kgCO2/kg'

        new_chart = TwoAxesInstanciatedChart('Years', 'CO2 emissions [kgCO2/kg]',
                                             chart_name=chart_name)

        columns = list(resources_co2_emissions.columns)
        for column in columns:
            if column != 'years':
                values = resources_co2_emissions[column].values
                serie = InstanciatedSeries(
                    resources_co2_emissions['years'].values.tolist(),
                    values.tolist(), column, 'lines')
                new_chart.series.append(serie)

        return new_chart
