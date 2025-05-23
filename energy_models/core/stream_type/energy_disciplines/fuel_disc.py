'''
Copyright 2022 Airbus SAS
Modifications on 2023/09/27-2024/06/24 Copyright 2023 Capgemini

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
from sostrades_core.tools.post_processing.pie_charts.instanciated_pie_chart import (
    InstanciatedPieChart,
)

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.energy_disciplines.bio_diesel_disc import (
    BioDieselDiscipline,
)
from energy_models.core.stream_type.energy_disciplines.ethanol_disc import (
    EthanolDiscipline,
)
from energy_models.core.stream_type.energy_disciplines.hydrotreated_oil_fuel_disc import (
    HydrotreatedOilFuelDiscipline,
)
from energy_models.core.stream_type.energy_disciplines.liquid_fuel_disc import (
    LiquidFuelDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy


class FuelDiscipline(SoSWrapp):
    # ontology information
    _ontology_data = {
        'label': 'Fuel Energy Model',
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

    name = GlossaryEnergy.fuel
    energy_name = name
    fuel_list = [LiquidFuelDiscipline.stream_name,
                 HydrotreatedOilFuelDiscipline.stream_name,
                 BioDieselDiscipline.stream_name,
                 EthanolDiscipline.stream_name,
                 ]

    DESC_IN = {GlossaryEnergy.YearStart: ClimateEcoDiscipline.YEAR_START_DESC_IN,
               GlossaryEnergy.YearEnd: GlossaryEnergy.YearEndVar,
               'exp_min': {'type': 'bool', 'default': True, 'user_level': 2},
               GlossaryEnergy.energy_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                                            'possible_values': EnergyMix.energy_list,
                                            'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy_study',
                                            'editable': False, 'structuring': True},
               }

    DESC_OUT = {GlossaryEnergy.StreamPricesValue: {'type': 'dataframe', 'unit': '$/MWh'},
                'energy_detailed_techno_prices': {'type': 'dataframe', 'unit': '$/MWh'},
                GlossaryEnergy.StreamEnergyConsumptionValue: {'type': 'dataframe', 'unit': 'PWh'},
                GlossaryEnergy.StreamProductionValue: {'type': 'dataframe', 'unit': 'PWh'},
                GlossaryEnergy.StreamProductionDetailedValue: GlossaryEnergy.StreamProductionDetailedDf,
                }

    def __init__(self, sos_name, logger: logging.Logger):
        super().__init__(sos_name, logger)
        self.energy_list = None

    def setup_sos_disciplines(self):
        '''
        Overload SoSDiscipline setup_sos_disciplines
        '''

        dynamic_inputs = {}

        if GlossaryEnergy.energy_list in self.get_data_in():
            energy_mix_list = self.get_sosdisc_inputs(GlossaryEnergy.energy_list)
            if energy_mix_list is not None:
                self.energy_list = list(
                    set(FuelDiscipline.fuel_list).intersection(set(energy_mix_list)))
                for energy in self.energy_list:
                    dynamic_inputs[f'{energy}.{GlossaryEnergy.StreamPricesValue}'] = {'type': 'dataframe',
                                                                                      'unit': '$/MWh',
                                                                                      'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                                                      'namespace': GlossaryEnergy.NS_ENERGY_MIX
                                                                                      }
                    dynamic_inputs[f'{energy}.energy_detailed_techno_prices'] = {'type': 'dataframe',
                                                                                 'unit': '$/MWh',
                                                                                 'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                                                 'namespace': GlossaryEnergy.NS_ENERGY_MIX
                                                                                 }
                    dynamic_inputs[f'{energy}.{GlossaryEnergy.StreamEnergyConsumptionValue}'] = {'type': 'dataframe',
                                                                                           'unit': 'PWh',
                                                                                           'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                                                           'namespace': GlossaryEnergy.NS_ENERGY_MIX
                                                                                                 }
                    dynamic_inputs[f'{energy}.{GlossaryEnergy.StreamProductionValue}'] = {'type': 'dataframe',
                                                                                          'unit': 'PWh',
                                                                                          'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                                                          'namespace': GlossaryEnergy.NS_ENERGY_MIX
                                                                                          }
                    dynamic_inputs[f'{energy}.{GlossaryEnergy.StreamProductionDetailedValue}'] = {'type': 'dataframe',
                                                                                                  'unit': 'TWh',
                                                                                                  'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                                                                  'namespace': GlossaryEnergy.NS_ENERGY_MIX
                                                                                                  }

        self.add_inputs(dynamic_inputs)

    def run(self):
        '''
        Overload SoSDiscipline run
        '''

        # init dataframes
        year_start, year_end = self.get_sosdisc_inputs(
            [GlossaryEnergy.YearStart, GlossaryEnergy.YearEnd])
        years = np.arange(year_start, year_end + 1)

        energy_prices = pd.DataFrame({GlossaryEnergy.Years: years})
        energy_detailed_techno_prices = pd.DataFrame({GlossaryEnergy.Years: years})
        energy_production = pd.DataFrame({GlossaryEnergy.Years: years})
        energy_consumption = pd.DataFrame({GlossaryEnergy.Years: years})
        energy_production_detailed = pd.DataFrame({GlossaryEnergy.Years: years})
        energy_prices[GlossaryEnergy.fuel] = 0
        energy_prices['fuel_production'] = 0

        # loop over fuel energies
        for energy in self.energy_list:
            energy_price = self.get_sosdisc_inputs(f'{energy}.{GlossaryEnergy.StreamPricesValue}')
            energy_techno_prices = self.get_sosdisc_inputs(
                f'{energy}.energy_detailed_techno_prices')
            energy_cons = self.get_sosdisc_inputs(
                f'{energy}.{GlossaryEnergy.StreamEnergyConsumptionValue}')
            energy_prod = self.get_sosdisc_inputs(
                f'{energy}.{GlossaryEnergy.StreamProductionValue}')
            energy_techno_prod = self.get_sosdisc_inputs(
                f'{energy}.{GlossaryEnergy.StreamProductionDetailedValue}')

            energy_prices = pd.concat(
                [energy_prices, energy_price.drop(GlossaryEnergy.Years, axis=1)], axis=1)
            energy_detailed_techno_prices = pd.concat(
                [energy_detailed_techno_prices, energy_techno_prices.drop(GlossaryEnergy.Years, axis=1)], axis=1)
            energy_production = pd.concat(
                [energy_production, energy_prod.drop(GlossaryEnergy.Years, axis=1)], axis=1)
            energy_consumption = pd.concat(
                [energy_consumption, energy_cons.drop(GlossaryEnergy.Years, axis=1)], axis=1)
            energy_production_detailed = pd.concat(
                [energy_production_detailed, energy_techno_prod.drop(GlossaryEnergy.Years, axis=1)], axis=1)

            # mean price weighted with production for each energy
            energy_prices[GlossaryEnergy.fuel] += [price * production for price,
                                                             production in
                                      zip(energy_prices[f'{energy}'], energy_production[f'{energy}'])]
            energy_prices['fuel_production'] += energy_production[f'{energy}']

        # aggregations
        energy_prices[GlossaryEnergy.fuel] = energy_prices[GlossaryEnergy.fuel] / \
                                energy_prices['fuel_production']
        energy_prices.drop('fuel_production', axis=1)
        energy_production = energy_production.T.groupby(level=0).sum()
        energy_consumption = energy_consumption.T.groupby(level=0).sum()
        energy_consumption.T.groupby(level=0).sum()

        energy_production_detailed = energy_production_detailed.T.groupby(level=0).sum()

        outputs_dict = {GlossaryEnergy.StreamPricesValue: energy_prices,
                        'energy_detailed_techno_prices': energy_detailed_techno_prices,
                        GlossaryEnergy.StreamProductionValue: energy_production.T,
                        GlossaryEnergy.StreamEnergyConsumptionValue: energy_consumption.T,
                        GlossaryEnergy.StreamProductionDetailedValue: energy_production_detailed.T,
                        }

        self.store_sos_outputs_values(outputs_dict)

    def compute_sos_jacobian(self):
        """Compute nothing, here to avoid l1 error."""
        pass

    # POST PROCESSING
    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['Energy price', 'Technology price',
                      'Consumption and production', 'Technology production']

        chart_filters.append(ChartFilter(
            'Charts', chart_list, chart_list, 'charts'))

        price_unit_list = ['$/MWh', '$/t']
        chart_filters.append(ChartFilter(
            'Price unit', price_unit_list, price_unit_list, 'price_unit'))

        year_start, year_end = self.get_sosdisc_inputs(
            [GlossaryEnergy.YearStart, GlossaryEnergy.YearEnd])
        years = list(np.arange(year_start, year_end + 1, 5))
        chart_filters.append(ChartFilter('Years for techno mix', years, [
            year_start, year_end], GlossaryEnergy.Years))
        return chart_filters

    def get_post_processing_list(self, filters=None):

        instanciated_charts = []
        charts = []
        price_unit_list = ['$/MWh', '$/t']
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

        if 'Energy price' in charts and '$/MWh' in price_unit_list:
            new_chart = self.get_chart_energy_price_in_dollar_mwh()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'Technology price' in charts and '$/MWh' in price_unit_list:
            new_chart = self.get_chart_techno_price_in_dollar_mwh()
            if new_chart is not None:
                instanciated_charts.append(new_chart)
        # if 'Energy price' in charts and '$/t' in price_unit_list and 'calorific_value' in self.get_sosdisc_inputs('data_fuel_dict'):
        #     new_chart = self.get_chart_energy_price_in_dollar_kg()
        #     if new_chart is not None:
        #         instanciated_charts.append(new_chart)

        if 'Consumption and production' in charts:
            new_charts = self.get_charts_consumption_and_production()
            for new_chart in new_charts:
                if new_chart is not None:
                    instanciated_charts.append(new_chart)
        if 'Technology production' in charts:
            new_charts = self.get_chart_technology_mix(years_list)
            for new_chart in new_charts:
                if new_chart is not None:
                    instanciated_charts.append(new_chart)
            new_charts = self.get_charts_production_by_techno()
            for new_chart in new_charts:
                if new_chart is not None:
                    instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_chart_energy_price_in_dollar_mwh(self):
        energy_prices = self.get_sosdisc_outputs(GlossaryEnergy.StreamPricesValue)
        chart_name = f'Detailed prices of {self.energy_name} mix '
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'Prices [$/MWh]', chart_name=chart_name, y_min_zero=True)

        for energy in [GlossaryEnergy.fuel] + self.energy_list:
            display_energy_name = energy.split(".")[-1].replace("_", " ")
            serie = InstanciatedSeries(
                energy_prices[GlossaryEnergy.Years].values.tolist(),
                energy_prices[energy].values.tolist(), f'{display_energy_name} mix price', 'lines')

            new_chart.add_series(serie)

        return new_chart

    def get_chart_techno_price_in_dollar_mwh(self):
        techno_prices = self.get_sosdisc_outputs(
            'energy_detailed_techno_prices')
        chart_name = f'Detailed prices of {self.energy_name} technologies mix '
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'Prices [$/MWh]', chart_name=chart_name)

        techno_list = [techno for techno in techno_prices if techno != GlossaryEnergy.Years]

        for techno in techno_list:
            display_techno_name = techno.split(".")[-1].replace("_", " ")
            serie = InstanciatedSeries(
                techno_prices[GlossaryEnergy.Years].values.tolist(),
                techno_prices[techno].values.tolist(), f'{display_techno_name} mix price', 'lines')

            new_chart.add_series(serie)

        return new_chart

    def get_charts_consumption_and_production(self):
        instanciated_charts = []
        # Charts for consumption and prod
        energy_consumption = self.get_sosdisc_outputs(GlossaryEnergy.StreamEnergyConsumptionValue)
        energy_production = self.get_sosdisc_outputs(GlossaryEnergy.StreamProductionValue)

        energy_consumptionunit = GlossaryEnergy.StreamEnergyConsumption['unit']
        eneryg_prod_unit = GlossaryEnergy.StreamProductionDf['unit'].split(' or ')[0]
        # one graph for production and one for consumption for clarity
        chart_name = f'{self.energy_name} Production with input investments'
        prod_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, f'Energy [{eneryg_prod_unit}]',
                                              chart_name=chart_name, stacked_bar=True)
        chart_name = f'{self.energy_name} Consumption with input investments'
        cons_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, f'Energy [{energy_consumptionunit}]',
                                              chart_name=chart_name, stacked_bar=True)

        for reactant in energy_consumption.columns:
            if reactant != GlossaryEnergy.Years:
                energy_twh = energy_consumption[reactant].values
                serie = InstanciatedSeries(energy_consumption[GlossaryEnergy.Years], energy_twh.tolist(), reactant, 'bar')
                cons_chart.add_series(serie)

        for products in energy_production.columns:
            # We do not plot technology H2 production on this graph
            # Pie charts are here to see difference of production between
            # technologies
            if products != GlossaryEnergy.Years and self.energy_name not in products:
                energy_twh = energy_production[products].values
                serie = InstanciatedSeries(energy_production[GlossaryEnergy.Years].values.tolist(),
                                           energy_twh.tolist(), products,
                                           'bar')

                prod_chart.add_series(serie)

        for energy in self.energy_list:
            display_energy_name = energy.split(".")[-1].replace("_", " ")
            legend_title = f'{display_energy_name} production'.replace(
                "(TWh)", "")
            energy_prod_twh = energy_production[f'{energy}'].values * 1e3
            serie = InstanciatedSeries(energy_production[GlossaryEnergy.Years].values.tolist(),
                                       energy_prod_twh.tolist(),
                                       legend_title,
                                       'bar')

            prod_chart.add_series(serie)
        instanciated_charts.append(prod_chart)
        instanciated_charts.append(cons_chart)

        # Check if we have kg in the consumption or prod :
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
            legend_title = f'{reactant_found} consumption'.replace("(Mt)", "")
            cons_chart_name = f'{legend_title} of {self.energy_name} with input investments'
            cons_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Mass [Gt]',
                                                  chart_name=cons_chart_name, stacked_bar=True)
        elif kg_values_production == 1 and kg_values_consumption == 0:
            display_product_found_name = product_found.split(
                ".")[-1].replace("_", " ")
            legend_title = f'{display_product_found_name} production'.replace(
                "(Mt)", "")
            prod_chart_name = f'{legend_title} of {self.energy_name} with input investments'
            prod_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Mass [Gt]',
                                                  chart_name=prod_chart_name, stacked_bar=True)
        else:
            cons_chart_name = f'{self.energy_name} mass Consumption with input investments'
            cons_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Mass [Gt]',
                                                  chart_name=cons_chart_name, stacked_bar=True)
            prod_chart_name = f'{self.energy_name} mass Production with input investments'
            prod_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Mass [Gt]',
                                                  chart_name=prod_chart_name, stacked_bar=True)

        for reactant in energy_consumption.columns:
            if reactant != GlossaryEnergy.Years and reactant.endswith('(Mt)'):
                display_reactant_name = reactant.split(
                    ".")[-1].replace("_", " ")
                legend_title = f'{display_reactant_name} consumption'.replace(
                    "(Mt)", "")
                mass = -energy_consumption[reactant].values / \
                       1.0e3 * 1e3
                serie = InstanciatedSeries(energy_consumption[GlossaryEnergy.Years].values.tolist(),
                                           mass.tolist(),
                                           legend_title,
                                           'bar')
                cons_chart.add_series(serie)

        for product in energy_production.columns:
            if product != GlossaryEnergy.Years and product.endswith('(Mt)'):
                display_product_name = product.split(".")[-1].replace("_", " ")
                legend_title = f'{display_product_name} production'.replace(
                    "(Mt)", "")
                mass = energy_production[product].values / \
                       1.0e3 * 1e3
                serie = InstanciatedSeries(energy_production[GlossaryEnergy.Years].values.tolist(),
                                           mass.tolist(),
                                           legend_title,
                                           'bar')
                prod_chart.add_series(serie)

        if kg_values_consumption > 0:
            instanciated_charts.append(cons_chart)
        elif kg_values_production > 0:
            instanciated_charts.append(prod_chart)

        return instanciated_charts

    def get_charts_production_by_techno(self):
        instanciated_charts = []
        # Charts for consumption and prod
        energy_production = self.get_sosdisc_outputs(
            GlossaryEnergy.StreamProductionDetailedValue)

        chart_name = f'Technology production for {self.energy_name}'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Production (TWh)',
                                             chart_name=chart_name, stacked_bar=True)

        techno_list = [
            techno for techno in energy_production if techno != GlossaryEnergy.Years]

        for techno in techno_list:
            techno_prod = energy_production[techno].values
            display_techno_name = techno.split(".")[-1].replace("_", " ")

            serie = InstanciatedSeries(
                energy_production[GlossaryEnergy.Years].values.tolist(),
                techno_prod.tolist(), display_techno_name, 'bar')
            new_chart.add_series(serie)

        instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_chart_technology_mix(self, years_list):
        instanciated_charts = []

        energy_production = self.get_sosdisc_outputs(
            GlossaryEnergy.StreamProductionDetailedValue)
        techno_list = [
            techno for techno in energy_production if techno != GlossaryEnergy.Years]
        display_techno_list = []

        for techno in techno_list:
            cut_techno_name = techno.split(".")
            display_techno_name = cut_techno_name[len(
                cut_techno_name) - 1].replace("_", " ")
            display_techno_list.append(display_techno_name)

        for year in years_list:
            values = [energy_production.loc[energy_production[GlossaryEnergy.Years]
                                            == year][techno].sum() for techno in techno_list]

            if sum(values) != 0.0:
                pie_chart = InstanciatedPieChart(
                    f'Technology productions in {year}', display_techno_list, values)
                instanciated_charts.append(pie_chart)

        return instanciated_charts
