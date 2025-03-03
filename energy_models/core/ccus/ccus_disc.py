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
import logging

import numpy as np
import pandas as pd
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
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.glossaryenergy import GlossaryEnergy


class CCUS_Discipline(SoSWrapp):
    # ontology information
    _ontology_data = {
        'label': 'Carbon Capture and Storage Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fa-solid fa-people-carry-box fa-fw',
        'version': '',
    }

    ccs_list = [GlossaryEnergy.carbon_capture, GlossaryEnergy.carbon_storage]
    DESC_IN = {
        GlossaryEnergy.YearStart: ClimateEcoDiscipline.YEAR_START_DESC_IN,
        GlossaryEnergy.YearEnd: {'type': 'int',
                        'unit': 'year', 'visibility': 'Shared', 'namespace': 'ns_public', 'range': [2000, 2300]},
        'co2_emissions_needed_by_energy_mix': {'type': 'dataframe', 'unit': 'Gt',
                                               'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy',
                                               'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                                        'carbon_capture needed by energy mix (Gt)': ('float', None, True),
                                                                        }, },
        'scaling_factor_energy_production': {'type': 'float', 'default': 1e3, 'user_level': 2, 'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'carbon_capture_from_energy_mix': {'type': 'dataframe', 'unit': 'Gt',
                                           'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy',
                                           'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                                    'carbon_capture from energy mix (Gt)': ('float', None, True), }, },
        'co2_for_food': {
            'type': 'dataframe', 'unit': 'Mt',
            'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy',
            'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True), f'{GlossaryEnergy.carbon_capture} for food (Mt)': ('float', None, True), }
    }
    }

    DESC_OUT = {
        'co2_emissions_ccus': {'type': 'dataframe', 'unit': 'Mt'},
        'carbon_storage_capacity (Gt)': {'type': 'dataframe', 'unit': 'Mt'},
        'co2_emissions_ccus_Gt': {'type': 'dataframe', 'unit': 'Gt', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                                  'namespace': GlossaryEnergy.NS_CCS},

        'CCS_price': {'type': 'dataframe', 'unit': '$/tCO2', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                      'namespace': 'ns_energy_study'},
    }

    def __init__(self, sos_name, logger: logging.Logger):
        super().__init__(sos_name, logger)
        self.ccus_model = None

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.ccus_model = CCUS(GlossaryEnergy.ccus_type)
        self.ccus_model.configure_parameters(inputs_dict)

    def setup_sos_disciplines(self):

        dynamic_inputs = {}
        dynamic_outputs = {}

        for ccs_name in self.ccs_list:
            dynamic_inputs[f'{ccs_name}.{GlossaryEnergy.StreamConsumptionValue}'] = {
                'type': 'dataframe', 'unit': 'PWh', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                'namespace': GlossaryEnergy.NS_CCS,
                "dynamic_dataframe_columns": True}
            dynamic_inputs[f'{ccs_name}.{GlossaryEnergy.StreamConsumptionWithoutRatioValue}'] = {
                'type': 'dataframe', 'unit': 'PWh', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                'namespace': GlossaryEnergy.NS_CCS,
                "dynamic_dataframe_columns": True}
            dynamic_inputs[f'{ccs_name}.{GlossaryEnergy.EnergyProductionValue}'] = {
                'type': 'dataframe', 'unit': 'PWh', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                'namespace': GlossaryEnergy.NS_CCS,
                'dynamic_dataframe_columns': True}
            dynamic_inputs[f'{ccs_name}.{GlossaryEnergy.StreamPricesValue}'] = {
                'type': 'dataframe', 'unit': '$/MWh', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                'namespace': GlossaryEnergy.NS_CCS,
                'dynamic_dataframe_columns': True}
            dynamic_inputs[f'{ccs_name}.{GlossaryEnergy.LandUseRequiredValue}'] = {
                'type': 'dataframe', 'unit': 'Gha', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                'namespace': GlossaryEnergy.NS_CCS,
                "dynamic_dataframe_columns": True}

        self.update_default_values()
        self.add_inputs(dynamic_inputs),
        self.add_outputs(dynamic_outputs)

    def update_default_values(self):
        """
        Update all default dataframes with years
        """
        if self.get_data_in() is not None:
            if GlossaryEnergy.YearEnd in self.get_data_in() and GlossaryEnergy.YearStart in self.get_data_in() and 'co2_for_food' in self.get_data_in():
                year_start, year_end = self.get_sosdisc_inputs([GlossaryEnergy.YearStart, GlossaryEnergy.YearEnd])
                if year_start is not None and year_end is not None:
                    default_co2_for_food = pd.DataFrame({
                        GlossaryEnergy.Years: np.arange(year_start, year_end + 1),
                        f'{GlossaryEnergy.carbon_capture} for food (Mt)': 0.0})
                    self.update_default_value('co2_for_food', 'in', default_co2_for_food)

    def run(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.ccus_model.configure_parameters(inputs_dict)
        self.ccus_model.compute()
        self.store_sos_outputs_values(self.ccus_model.outputs_dict)

    def compute_sos_jacobian(self):
        year_start, year_end = self.get_sosdisc_inputs([GlossaryEnergy.YearStart, GlossaryEnergy.YearEnd])
        years = np.arange(year_start, year_end + 1)
        d_co2_emissions = self.ccus_model.grad_co2_emissions_ccus_Gt()
        for input_var, list_gradients in d_co2_emissions.items():
            for column, grad_value in list_gradients:
                self.set_partial_derivative_for_other_types(
                    ('co2_emissions_ccus_Gt', f'{GlossaryEnergy.carbon_storage} Limited by capture (Gt)'),
                    (input_var, column),
                    grad_value)

        if GlossaryEnergy.carbon_capture in self.ccs_list:
            self.set_partial_derivative_for_other_types(
                ('CCS_price', 'ccs_price_per_tCO2'),
                (f'{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.StreamPricesValue}', GlossaryEnergy.carbon_capture),
                np.identity(len(years)))
        if GlossaryEnergy.carbon_storage in self.ccs_list:
            self.set_partial_derivative_for_other_types(
                ('CCS_price', 'ccs_price_per_tCO2'),
                (f'{GlossaryEnergy.carbon_storage}.{GlossaryEnergy.StreamPricesValue}', GlossaryEnergy.carbon_storage),
                np.identity(len(years)))

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['CCS price', 'CO2 storage limited by capture']

        chart_filters.append(ChartFilter(
            'Charts', chart_list, chart_list, 'charts'))

        price_unit_list = ['$/MWh', '$/t']
        chart_filters.append(ChartFilter(
            'Price unit', price_unit_list, price_unit_list, 'price_unit'))

        year_start, year_end = self.get_sosdisc_inputs(
            [GlossaryEnergy.YearStart, GlossaryEnergy.YearEnd])
        years = list(np.arange(year_start, year_end + 1, 5))
        chart_filters.append(ChartFilter(
            'Years for energy mix', years, [year_start, year_end], GlossaryEnergy.Years))
        return chart_filters

    def get_post_processing_list(self, filters=None):

        # For the outputs, making a graph for block fuel vs range and blocktime vs
        # range

        instanciated_charts = []
        charts = []

        # Overload default value with chart filter
        if filters is not None:
            for chart_filter in filters:
                if chart_filter.filter_key == 'charts':
                    charts = chart_filter.selected_values

        if 'CCS price' in charts:
            new_chart = self.get_chart_CCS_price()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'CO2 storage limited by capture' in charts:
            new_chart = self.get_chart_co2_limited_storage()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_chart_CCS_price(self):

        ccs_prices = self.get_sosdisc_outputs('CCS_price')
        years = list(ccs_prices[GlossaryEnergy.Years].values)
        chart_name = 'CCS price'
        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, '[$/tCO2]', chart_name=chart_name, stacked_bar=True)
        visible_line = True

        carbon_capture_price = self.get_sosdisc_inputs(f'{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.StreamPricesValue}')[
            GlossaryEnergy.carbon_capture].values
        carbon_storage_price = self.get_sosdisc_inputs(f'{GlossaryEnergy.carbon_storage}.{GlossaryEnergy.StreamPricesValue}')[
            GlossaryEnergy.carbon_storage].values

        new_series = InstanciatedSeries(years, carbon_capture_price, 'Capture', 'bar', visible_line)
        new_chart.series.append(new_series)

        new_series = InstanciatedSeries(years, carbon_storage_price, 'Storage', 'bar', visible_line)
        new_chart.series.append(new_series)

        new_series = InstanciatedSeries(years, ccs_prices['ccs_price_per_tCO2'].values.tolist(), 'CCS price', 'lines', visible_line)
        new_chart.series.append(new_series)

        return new_chart

    def get_chart_co2_to_store(self):
        '''
        Plot a graph to understand CO2 to store
        '''
        chart_name = 'CO2 emissions captured, used and to store'
        co2_emissions = self.get_sosdisc_outputs('co2_emissions_ccus')
        co2_for_food = self.get_sosdisc_inputs('co2_for_food')
        carbon_capture_from_energy_mix = self.get_sosdisc_inputs('carbon_capture_from_energy_mix')
        co2_emissions_needed_by_energy_mix = self.get_sosdisc_inputs('co2_emissions_needed_by_energy_mix')
        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'CO2 emissions (Gt)',
                                             chart_name=chart_name, stacked_bar=True)

        x_serie_1 = co2_emissions[GlossaryEnergy.Years].values.tolist()

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit}) from CC technos'].values / 1.0e3).tolist(),
            'CO2 captured from CC technos', 'bar')
        new_chart.add_series(serie)
        """
        serie = InstanciatedSeries(
            x_serie_1,
            carbon_capture_from_energy_mix[f'{GlossaryEnergy.carbon_capture} from energy mix (Gt)'].values.tolist(),
            'CO2 captured from energy mix', 'bar')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (-co2_emissions_needed_by_energy_mix[f'{GlossaryEnergy.carbon_capture} needed by energy mix (Gt)'].values).tolist(),
            f'{GlossaryEnergy.carbon_capture} used by energy mix' ,'bar')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (-co2_for_food[f'{GlossaryEnergy.carbon_capture} for food (Mt)'].values / 1.0e3).tolist(), f'{GlossaryEnergy.carbon_capture} used for food', 'bar')
        new_chart.add_series(serie)
        """

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'{GlossaryEnergy.carbon_capture} to be stored (Mt)'].values / 1.0e3).tolist(), 'CO2 captured to store')
        new_chart.add_series(serie)

        return new_chart

    def get_chart_co2_limited_storage(self):
        '''
        Plot a graph to understand storage
        '''
        chart_name = 'CO2 capture management'
        co2_emissions = self.get_sosdisc_outputs('co2_emissions_ccus')
        carbon_storage_capacity = self.get_sosdisc_outputs('carbon_storage_capacity (Gt)')
        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, '[Gt]', chart_name=chart_name, stacked_bar=True)

        years = co2_emissions[GlossaryEnergy.Years].values.tolist()
        serie = InstanciatedSeries(
            years,
            (co2_emissions[f'{GlossaryEnergy.carbon_capture} to be stored (Mt)'].values / 1.0e3).tolist(), 'CO2 captured to store')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            years,
            (carbon_storage_capacity['carbon_storage_capacity (Gt)']).tolist(), 'CO2 storage capacity')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            years,
            (co2_emissions[f'{GlossaryEnergy.carbon_storage} Limited by capture (Mt)'].values / 1.0e3).tolist(),
            'CO2 captured and stored', 'bar')
        new_chart.add_series(serie)
        return new_chart

    def get_chart_co2_emissions_sources(self):
        '''
        Plot all CO2 emissions sources
        '''
        chart_name = 'CO2 emissions sources'
        co2_emissions = self.get_sosdisc_outputs('co2_emissions')
        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'CO2 emissions (Gt)',
                                             chart_name=chart_name)

        x_serie_1 = co2_emissions[GlossaryEnergy.Years].values.tolist()

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions['Total CO2 by use (Mt)'].values / 1.0e3).tolist(), 'CO2 by use (net production burned)')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'Total {CarbonCapture.flue_gas_name} ({GlossaryEnergy.mass_unit})'].values / 1.0e3).tolist(),
            'Flue gas from plants')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1, (co2_emissions[f'{GlossaryEnergy.carbon_capture} from energy mix (Mt)'].values / 1.0e3).tolist(),
            'Carbon capture from energy mix (FT or Sabatier)')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'{GlossaryEnergy.carbon_capture} from energy mix (Mt)'].values / 1.0e3).tolist(),
            'CO2 from energy mix (machinery fuels)')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions['CO2 emissions sources'].values / 1.0e3).tolist(), 'Total sources')
        new_chart.add_series(serie)

        return new_chart
