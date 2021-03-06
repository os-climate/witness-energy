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

import pandas as pd

from energy_models.core.stream_type.carbon_models.carbon_storage import CarbonStorage
from energy_models.core.techno_type.techno_disc import TechnoDiscipline
from sos_trades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sos_trades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart


class CSTechnoDiscipline(TechnoDiscipline):

    # ontology information
    _ontology_data = {
        'label': 'Carbon Storage Technology Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-truck-loading fa-fw',
        'version': '',
    }
    DESC_IN = {'transport_cost': {'type': 'dataframe', 'unit': '$/t', 'visibility': TechnoDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_carbon_storage',
                                  'dataframe_descriptor': {'years': ('int',  [1900, 2100], False),
                                                           'transport': ('float',  None, True)},
                                  'dataframe_edition_locked': False},
               'transport_margin': {'type': 'dataframe', 'unit': '%', 'visibility': TechnoDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_carbon_storage',
                                    'dataframe_descriptor': {'years': ('int',  [1900, 2100], False),
                                                             'margin': ('float',  None, True)},
                                    'dataframe_edition_locked': False},
               'data_fuel_dict': {'type': 'dict', 'visibility': TechnoDiscipline.SHARED_VISIBILITY,
                                  'namespace': 'ns_carbon_storage', 'default': CarbonStorage.data_energy_dict,
                                  'unit': 'defined in dict'},
               }
    DESC_IN.update(TechnoDiscipline.DESC_IN)

    _maturity = 'Research'

    energy_name = CarbonStorage.name

    def compute_sos_jacobian(self):
        # Grad of price vs energyprice

        TechnoDiscipline.compute_sos_jacobian(self)

        grad_dict = self.techno_model.grad_price_vs_energy_price()

        self.set_partial_derivatives_techno(
            grad_dict, None)

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['Detailed prices',
                      'Consumption and production',
                      'Initial Production', 'Factory Mean Age', 'CO2 emissions']
        if self.get_sosdisc_inputs('is_apply_ratio'):
            chart_list.extend(['Applied Ratio'])
        chart_filters.append(ChartFilter(
            'Charts', chart_list, chart_list, 'charts'))

        price_unit_list = ['$/tCO2']
        chart_filters.append(ChartFilter(
            'Price unit', price_unit_list, price_unit_list, 'price_unit'))
        return chart_filters

    def get_post_processing_list(self, filters=None):

        # For the outputs, making a graph for block fuel vs range and blocktime vs
        # range

        instanciated_charts = []
        charts = []
        price_unit_list = ['$/tCO2']
        # Overload default value with chart filter
        if filters is not None:
            for chart_filter in filters:
                if chart_filter.filter_key == 'charts':
                    charts = chart_filter.selected_values
                if chart_filter.filter_key == 'price_unit':
                    price_unit_list = chart_filter.selected_values

        if 'Detailed prices' in charts and '$/tCO2' in price_unit_list:
            new_chart = self.get_chart_detailed_price_in_dollar_ton()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'Consumption and production' in charts:
            new_chart = self.get_chart_investments()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

            new_charts = self.get_charts_consumption_and_production()
            for new_chart in new_charts:
                if new_chart is not None:
                    instanciated_charts.append(new_chart)

        if 'Applied Ratio' in charts:
            new_chart = self.get_chart_applied_ratio()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'Initial Production' in charts:
            if 'initial_production' in self.get_data_in():
                new_chart = self.get_chart_initial_production()
                if new_chart is not None:
                    instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_chart_detailed_price_in_dollar_ton(self):

        techno_detailed_prices = self.get_sosdisc_outputs(
            'techno_detailed_prices')
        chart_name = f'Detailed prices of {self.techno_name} technology over the years'
        year_start = min(techno_detailed_prices['years'].values.tolist())
        year_end = max(techno_detailed_prices['years'].values.tolist())
        minimum = 0
        maximum = max(
            (techno_detailed_prices[self.techno_name].values).tolist()) * 1.2

        new_chart = TwoAxesInstanciatedChart('years', 'Prices [$/tCO2]', [year_start, year_end], [minimum, maximum],
                                             chart_name=chart_name)

        if 'percentage_resource' in self._data_in:
            percentage_resource = self.get_sosdisc_inputs(
                'percentage_resource')
            new_chart.annotation_upper_left = {
                'Percentage of total price at starting year': f'{percentage_resource[self.energy_name][0]} %'}
            tot_price = (techno_detailed_prices[self.techno_name].values) / \
                (percentage_resource[self.energy_name] / 100.)
            serie = InstanciatedSeries(
                techno_detailed_prices['years'].values.tolist(),
                tot_price.tolist(), 'Total price without percentage', 'lines')
            new_chart.series.append(serie)
        # Add total price
        serie = InstanciatedSeries(
            techno_detailed_prices['years'].values.tolist(),
            (techno_detailed_prices[self.techno_name].values).tolist(), 'Total price with margin', 'lines')

        new_chart.series.append(serie)

        # Factory price
        serie = InstanciatedSeries(
            techno_detailed_prices['years'].values.tolist(),
            (techno_detailed_prices[f'{self.techno_name}_factory'].values).tolist(), 'Factory', 'lines')

        new_chart.series.append(serie)

        if 'energy_costs' in techno_detailed_prices:
            # energy_costs
            serie = InstanciatedSeries(
                techno_detailed_prices['years'].values.tolist(),
                (techno_detailed_prices['energy_costs'].values).tolist(), 'Energy costs', 'lines')

            new_chart.series.append(serie)

        # Transport price
        serie = InstanciatedSeries(
            techno_detailed_prices['years'].values.tolist(),
            (techno_detailed_prices['transport'].values).tolist(), 'Transport', 'lines')

        new_chart.series.append(serie)
        # CO2 taxes
        serie = InstanciatedSeries(
            techno_detailed_prices['years'].values.tolist(),
            (techno_detailed_prices['CO2_taxes_factory'].values).tolist(), 'CO2 taxes due to production', 'lines')
        new_chart.series.append(serie)

        return new_chart

    def get_chart_investments(self):
        # Chart for input investments
        input_investments = self.get_sosdisc_inputs('invest_level')

        chart_name = f'Input investments over the years'

        new_chart = TwoAxesInstanciatedChart('years', 'Investments [G$]',
                                             chart_name=chart_name, stacked_bar=True)
        invest = input_investments['invest'].values
        serie = InstanciatedSeries(
            input_investments['years'].values.tolist(),
            invest.tolist(), '', 'bar')

        new_chart.series.append(serie)

        return new_chart

    def get_charts_consumption_and_production(self):
        instanciated_charts = []
        # Charts for consumption and prod
        techno_consumption = self.get_sosdisc_outputs(
            'techno_detailed_consumption')
        techno_production = self.get_sosdisc_outputs(
            'techno_detailed_production')
        chart_name = f'{self.techno_name} technology energy Capture & consumption<br>with input investments'

        new_chart = TwoAxesInstanciatedChart('years', 'Mass [Mt]',
                                             chart_name=chart_name, stacked_bar=True)

        for reactant in techno_consumption.columns:
            if reactant != 'years' and reactant.endswith('(Mt)'):
                energy_twh = -techno_consumption[reactant].values
                legend_title = f'{reactant} consumption'.replace(
                    "(Mt)", "")
                serie = InstanciatedSeries(
                    techno_consumption['years'].values.tolist(),
                    energy_twh.tolist(), legend_title, 'bar')

                new_chart.series.append(serie)

        for products in techno_production.columns:
            if products != 'years' and products.endswith('(Mt)'):
                energy_twh = techno_production[products].values
                legend_title = f'{products}'.replace(
                    "(Mt)", "")
                serie = InstanciatedSeries(
                    techno_production['years'].values.tolist(),
                    energy_twh.tolist(), legend_title, 'bar')

                new_chart.series.append(serie)
        instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_chart_initial_production(self):

        year_start = self.get_sosdisc_inputs(
            'year_start')
        initial_production = self.get_sosdisc_inputs(
            'initial_production')
        initial_age_distrib = self.get_sosdisc_inputs(
            'initial_age_distrib')
        initial_prod = pd.DataFrame({'age': initial_age_distrib['age'].values,
                                     'distrib': initial_age_distrib['distrib'].values, })
        initial_prod['CO2 (Mt)'] = initial_prod['distrib'] / \
            100.0 * initial_production
        initial_prod['years'] = year_start - initial_prod['age']
        initial_prod.sort_values('years', inplace=True)
        initial_prod['cum CO2 (Mt)'] = initial_prod['CO2 (Mt)'].cumsum()

        study_production = self.get_sosdisc_outputs(
            'techno_detailed_production')
        chart_name = f'World {self.energy_name} capture via {self.techno_name}<br>with 2020 factories distribution'

        new_chart = TwoAxesInstanciatedChart('years', f'{self.energy_name} capture (Mt)',
                                             chart_name=chart_name)

        serie = InstanciatedSeries(
            initial_prod['years'].values.tolist(),
            initial_prod[f'cum CO2 (Mt)'].values.tolist(), 'Initial carbon capture by 2020 factories', 'lines')
        study_prod = study_production[f'{self.energy_name} (Mt)'].values
        new_chart.series.append(serie)
        years_study = study_production['years'].values.tolist()
        years_study.insert(0, year_start - 1)
        study_prod_l = study_prod.tolist()
        study_prod_l.insert(
            0, initial_prod[f'cum CO2 (Mt)'].values.tolist()[-1])
        serie = InstanciatedSeries(
            years_study,
            study_prod_l, 'Predicted carbon capture', 'lines')
        new_chart.series.append(serie)

        return new_chart
