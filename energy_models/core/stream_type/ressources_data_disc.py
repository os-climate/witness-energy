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

from energy_models.core.stream_type.ressources_models.methanol import Methanol
from energy_models.core.stream_type.ressources_models.natural_oil import NaturalOil
from energy_models.core.stream_type.ressources_models.oil import CrudeOil
from energy_models.core.stream_type.ressources_models.oxygen import Oxygen
from energy_models.core.stream_type.ressources_models.potassium_hydroxide import PotassiumHydroxide
from energy_models.core.stream_type.ressources_models.sodium_hydroxide import SodiumHydroxide
from sos_trades_core.execution_engine.sos_discipline import SoSDiscipline
from sos_trades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sos_trades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart


def get_static_CO2_emissions(years):

    ressources_CO2_emissions = pd.DataFrame()

    ressources_CO2_emissions['years'] = years
    ressources_CO2_emissions['water'] = 0.0
    ressources_CO2_emissions['sea_water'] = 0.0
    # feedstock_recovery from GHGenius
    ressources_CO2_emissions['uranium fuel'] = 0.474 / 277.78
    ressources_CO2_emissions['CO2'] = -1.0
    # https://bioenergykdf.net/system/files/Net%20CO2...Coal-Fired%20Power.pdf
    # 0.425g of C in 1 kg of dry-biomass meaning in term of CO2
    ressources_CO2_emissions['biomass_dry'] = - 0.425 * 44.01 / 12.0
    ressources_CO2_emissions['wet_biomass'] = - 0.425 * 44.01 / 12.0
    # Carbon Footprint ofStrait Vegetable Oil and Bio Diesel Fuel Produced
    # from Used Cooking Oil
    ressources_CO2_emissions[NaturalOil.name] = -2.95
    # https://methanolfuels.org/about-methanol/environment/
    ressources_CO2_emissions[Methanol.name] = 0.54
    ressources_CO2_emissions[SodiumHydroxide.name] = 0.6329
    ressources_CO2_emissions['wood'] = 1.78
    ressources_CO2_emissions['managed_wood'] = 0.0
    ressources_CO2_emissions['oxygen'] = 0.0
    ressources_CO2_emissions['crude oil'] = 0.02533
    ressources_CO2_emissions['solid_fuel'] = 0.64 / 4.86
    ressources_CO2_emissions['calcium'] = 0.0
    ressources_CO2_emissions['potassium'] = 0.0
    ressources_CO2_emissions['amine'] = 0.0

    return ressources_CO2_emissions


def get_static_prices(years):

    year_co2 = [2020, 2025, 2030, 2035, 2040, 2045, 2050]

    # $/t
    price_co2 = [40.0, 45.0, 52.0, 63.0, 74.0, 96.0, 119.0]

    func = sc.interp1d(year_co2, price_co2,
                       kind='linear', fill_value='extrapolate')

    ressources_prices_default = pd.DataFrame({'years': years,
                                              'CO2': func(years),
                                              'uranium fuel': 1390000.0,
                                              'biomass_dry': 68.12,
                                              'wet_biomass': 56.0,
                                              'wood': 120.0,
                                              'carbon': 25000.0,
                                              CrudeOil.name: 44.0,
                                              # https://www.neste.com/investors/market-data/palm-and-rapeseed-oil-prices
                                              f'{NaturalOil.name}': 1100.0,

                                              f'{Methanol.name}': 400.0,
                                              f'{SodiumHydroxide.name}': 425.0,
                                              # https://www.ceicdata.com/en/china/china-petroleum--chemical-industry-association-petrochemical-price-inorganic-chemical-material/cn-market-price-monthly-avg-inorganic-chemical-material-potassium-hydroxide-92
                                              f'{PotassiumHydroxide.name}': 772.0,
                                              f'{Oxygen.name}': 60.0,
                                              f'calcium': 85.0,
                                              f'potassium': 500.0,
                                              f'amine': 1300.0,
                                              'sea_water': 1.4313,
                                              'water': 1.78})

    return ressources_prices_default


class RessourcesDisc(SoSDiscipline):

    # ontology information
    _ontology_data = {
        'label': 'Energy Data Ressources Model',
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

    DESC_IN = {'year_start': {'type': 'int', 'default': 2020, 'unit': '[-]', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public', 'structuring': True},
               'year_end': {'type': 'int', 'default': 2050, 'unit': '[-]', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public', 'structuring': True},
               'ressources_price': {'type': 'dataframe', 'unit': '[$/t]',
                                    'dataframe_descriptor': {'years': ('int',  [1900, 2100], False)},
                                    'dataframe_edition_locked': False,
                                    'default': get_static_prices(years)},
               'ressources_CO2_emissions': {'type': 'dataframe', 'unit': '[kgCO2/kg]',
                                            'dataframe_descriptor': {'years': ('int',  [1900, 2100], False)},
                                            'dataframe_edition_locked': False,
                                            'default': get_static_CO2_emissions(years)}}

    DESC_OUT = {

        'ressources_price': {'type': 'dataframe', 'unit': '[$/t]', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_study'},
        'ressources_CO2_emissions': {'type': 'dataframe', 'unit': '[kgCO2/kg]', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_study'}
    }

    def setup_sos_disciplines(self):

        if self._data_in is not None:
            if 'year_start' in self._data_in:
                year_start, year_end = self.get_sosdisc_inputs(
                    ['year_start', 'year_end'])
                years = np.arange(year_start, year_end + 1)
                ressources_price = self.get_sosdisc_inputs(
                    'ressources_price')
                new_default_prices = get_static_prices(years)
                new_default_emissions = get_static_CO2_emissions(years)

                # If the value of the df is the default we specified, we need to modify also the value
                #(if the value is different it is a user value do not modify the value)
                if ressources_price is None or len(ressources_price['years'].values) != len(years):
                    self.update_default_value(
                        'ressources_price', self.IO_TYPE_IN, new_default_prices)
                    self.update_default_value(
                        'ressources_CO2_emissions', self.IO_TYPE_IN, new_default_emissions)

    def run(self):
        """

        """
        year_start = self.get_sosdisc_inputs('year_start')
        year_end = self.get_sosdisc_inputs('year_end')

        years = np.arange(year_start, year_end + 1)

        ressources_price = self.get_sosdisc_inputs('ressources_price')

        co2_emissions = self.get_sosdisc_inputs('ressources_CO2_emissions')

        outputs_dict = {'ressources_price': ressources_price,
                        'ressources_CO2_emissions': co2_emissions}
        # -- store outputs
        self.store_sos_outputs_values(outputs_dict)

    def compute_sos_jacobian(self):
        pass

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['Ressources prices', 'Ressources CO2 emissions']
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

        if 'Ressources prices' in charts:
            new_chart = self.get_chart_prices_in_dollar_kg()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'Ressources CO2 emissions' in charts:
            new_chart = self.get_chart_CO2_emissions()
            if new_chart is not None:
                instanciated_charts.append(new_chart)
        return instanciated_charts

    def get_chart_prices_in_dollar_kg(self):

        ressources_price = self.get_sosdisc_outputs(
            'ressources_price')
        chart_name = f'Ressources prices'

        new_chart = TwoAxesInstanciatedChart('Years', 'Prices [$/t]',
                                             chart_name=chart_name)

        columns = list(ressources_price.columns)
        for column in columns:
            if column != 'years':
                values = ressources_price[column].values
                serie = InstanciatedSeries(
                    ressources_price['years'].values.tolist(),
                    values.tolist(), f'{column} price', 'lines')
                new_chart.series.append(serie)

        return new_chart

    def get_chart_CO2_emissions(self):

        ressources_co2_emissions = self.get_sosdisc_outputs(
            'ressources_CO2_emissions')
        chart_name = f'Ressources CO2 emissions in kgCO2/kg'

        new_chart = TwoAxesInstanciatedChart('Years', 'CO2 emissions [kgCO2/kg]',
                                             chart_name=chart_name)

        columns = list(ressources_co2_emissions.columns)
        for column in columns:
            if column != 'years':
                values = ressources_co2_emissions[column].values
                serie = InstanciatedSeries(
                    ressources_co2_emissions['years'].values.tolist(),
                    values.tolist(), column, 'lines')
                new_chart.series.append(serie)

        return new_chart
