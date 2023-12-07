'''
Copyright 2022 Airbus SAS
Modifications on 2023/03/29-2023/11/16 Copyright 2023 Capgemini

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

from energy_models.core.stream_type.carbon_models.carbon_storage import CarbonStorage
from energy_models.core.stream_type.stream_disc import StreamDiscipline
from energy_models.glossaryenergy import GlossaryEnergy
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart


class CarbonStorageDiscipline(StreamDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Carbon Storage Model',
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

    DESC_IN = {GlossaryEnergy.techno_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                                     'possible_values': CarbonStorage.default_techno_list,
                                     'visibility': 'Shared',
                                     'unit': '-',
                                     'namespace': 'ns_carbon_storage', 'structuring': True},
               'data_fuel_dict': {'type': 'dict', 'visibility': 'Shared',
                                  'namespace': 'ns_carbon_storage', 'default': CarbonStorage.data_energy_dict,
                                  'unit': 'defined in dict'},
               }

    DESC_IN.update(StreamDiscipline.DESC_IN.copy())

    energy_name = CarbonStorage.name

    DESC_OUT = StreamDiscipline.DESC_OUT.copy()  # -- add specific techno outputs to this

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.energy_model = CarbonStorage(self.energy_name)
        self.energy_model.configure_parameters(inputs_dict)

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['CO2 Storage price', 'Technology mix',
                      'Consumption and production', GlossaryEnergy.Capital]
        chart_filters.append(ChartFilter(
            'Charts', chart_list, chart_list, 'charts'))

        price_unit_list = ['$/ton']
        chart_filters.append(ChartFilter(
            'Price unit', price_unit_list, price_unit_list, 'price_unit'))

        year_start, year_end = self.get_sosdisc_inputs(
            [GlossaryEnergy.YearStart, GlossaryEnergy.YearEnd])
        years = list(np.arange(year_start, year_end + 1, 5))
        chart_filters.append(ChartFilter(
            'Years for techno mix', years, [year_start, year_end], GlossaryEnergy.Years))
        return chart_filters

    def get_post_processing_list(self, filters=None):

        # For the outputs, making a graph for block fuel vs range and blocktime vs
        # range

        instanciated_charts = []
        charts = []
        price_unit_list = ['$/ton']
        unit = 'Mt'
        years_list = [self.get_sosdisc_inputs(GlossaryEnergy.YearStart)]
        # Overload default value with chart filter
        if filters is not None:
            for chart_filter in filters:
                if chart_filter.filter_key == 'charts':
                    charts = chart_filter.selected_values
                if chart_filter.filter_key == 'price_unit':
                    price_unit_list = chart_filter.selected_values
                if chart_filter.filter_key == GlossaryEnergy.Years:
                    years_list = chart_filter.selected_values

        if 'CO2 Storage price' in charts and '$/ton' in price_unit_list:
            new_chart = self.get_chart_CO2_storage_price_in_dollar_ton()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'Consumption and production' in charts:
            new_charts = self.get_charts_consumption_and_production()
            for new_chart in new_charts:
                if new_chart is not None:
                    instanciated_charts.append(new_chart)

        if GlossaryEnergy.Capital in charts:
            chart = self.get_capital_breakdown_by_technos()
            instanciated_charts.append(chart)

        if 'Technology mix' in charts:
            new_charts = self.get_chart_technology_mix(years_list)
            for new_chart in new_charts:
                if new_chart is not None:
                    instanciated_charts.append(new_chart)
            new_charts = self.get_charts_production_by_techno(unit)
            for new_chart in new_charts:
                if new_chart is not None:
                    instanciated_charts.append(new_chart)
        return instanciated_charts

    def get_chart_CO2_storage_price_in_dollar_ton(self):
        CO2_storage_prices = self.get_sosdisc_outputs(GlossaryEnergy.EnergyPricesValue)
        chart_name = f'Detailed prices of {self.energy_name} mix over the years'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'Prices [$/ton]', chart_name=chart_name)

        serie = InstanciatedSeries(
            CO2_storage_prices[GlossaryEnergy.Years].values.tolist(),
            (CO2_storage_prices[self.energy_name].values).tolist(), f'{self.energy_name} mix price', 'lines')

        new_chart.series.append(serie)

        technology_list = self.get_sosdisc_inputs(GlossaryEnergy.techno_list)

        for technology in technology_list:
            techno_price = self.get_sosdisc_inputs(
                f'{technology}.{GlossaryEnergy.TechnoPricesValue}')
            serie = InstanciatedSeries(
                CO2_storage_prices[GlossaryEnergy.Years].values.tolist(),
                (techno_price[technology].values).tolist(), f'{technology} price', 'lines')
            new_chart.series.append(serie)

        return new_chart

    def get_charts_consumption_and_production(self):
        instanciated_charts = []
        # Charts for consumption and prod
        energy_consumption = self.get_sosdisc_outputs(GlossaryEnergy.EnergyConsumptionValue)
        energy_production = self.get_sosdisc_outputs(GlossaryEnergy.EnergyProductionValue)
        scaling_factor_energy_consumption = self.get_sosdisc_inputs(
            'scaling_factor_energy_consumption')
        scaling_factor_energy_production = self.get_sosdisc_inputs(
            'scaling_factor_energy_production')
        chart_name = 'Total consumption and production with input investments'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Mass [Mt]',
                                             chart_name=chart_name, stacked_bar=True)

        for reactant in energy_consumption.columns:
            if reactant != GlossaryEnergy.Years and reactant.endswith('(Mt)'):
                energy_twh = - \
                                 energy_consumption[reactant].values * \
                             scaling_factor_energy_consumption
                legend_title = f'{reactant}'.replace(
                    "(Mt)", "")
                serie = InstanciatedSeries(
                    energy_consumption[GlossaryEnergy.Years].values.tolist(),
                    energy_twh.tolist(), legend_title, 'bar')

                new_chart.series.append(serie)

        for products in energy_production.columns:
            # We do not plot technology H2 production on this graph
            # Pie charts are here to see difference of production between
            # technologies
            if products != GlossaryEnergy.Years and products.endswith('(Mt)') and self.energy_name not in products:
                energy_twh = energy_production[products].values * \
                             scaling_factor_energy_production
                legend_title = f'{products}'.replace(
                    "(Mt)", "")
                serie = InstanciatedSeries(
                    energy_production[GlossaryEnergy.Years].values.tolist(),
                    energy_twh.tolist(), legend_title, 'bar')

                new_chart.series.append(serie)
        energy_prod_twh = energy_production[self.energy_name].values
        serie = InstanciatedSeries(
            energy_production[GlossaryEnergy.Years].values.tolist(),
            energy_prod_twh.tolist(), self.energy_name, 'bar')

        new_chart.series.append(serie)
        instanciated_charts.append(new_chart)

        # Chzck if we have kg in the consumption or prod :

        kg_values_consumption = 0
        reactant_found = ''
        for reactant in energy_consumption.columns:
            if reactant != GlossaryEnergy.Years and reactant.endswith('(Mt)'):
                kg_values_consumption += 1
                reactant_found = reactant

        kg_values_production = 0
        product_found = ''
        for product in energy_production.columns:
            if product != GlossaryEnergy.Years and product.endswith('(Mt)'):
                kg_values_production += 1
                product_found = product
        if kg_values_consumption == 1 and kg_values_production == 0:
            legend_title = f'{reactant_found} consumption'.replace(
                "(Mt)", "")
            chart_name = f'{legend_title} of {self.energy_name} with input investments'
        elif kg_values_production == 1 and kg_values_consumption == 0:
            legend_title = f'{product_found} production'.replace(
                "(Mt)", "")
            chart_name = f'{legend_title} of {self.energy_name} with input investments'
        else:
            chart_name = 'Consumption and production with input investments'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Mass [Mt]',
                                             chart_name=chart_name.capitalize(), stacked_bar=True)

        for reactant in energy_consumption.columns:
            if reactant != GlossaryEnergy.Years and reactant.endswith('(Mt)'):
                legend_title = f'{reactant} consumption'.replace(
                    "(Mt)", "")
                mass = -energy_consumption[reactant].values
                serie = InstanciatedSeries(
                    energy_consumption[GlossaryEnergy.Years].values.tolist(),
                    mass.tolist(), legend_title, 'bar')
                new_chart.series.append(serie)
        for product in energy_production.columns:
            if product != GlossaryEnergy.Years and product.endswith('(Mt)') and product != "carbon_storage (Mt)":
                legend_title = f'{product} production'.replace(
                    "(Mt)", "").replace("carbon_storage ", "")
                mass = energy_production[product].values
                serie = InstanciatedSeries(
                    energy_production[GlossaryEnergy.Years].values.tolist(),
                    mass.tolist(), legend_title, 'bar')
                new_chart.series.append(serie)

        if kg_values_consumption > 0 or kg_values_production > 0:
            instanciated_charts.append(new_chart)

        return instanciated_charts
