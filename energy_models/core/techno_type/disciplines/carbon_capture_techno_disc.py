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

from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.techno_type.techno_disc import TechnoDiscipline
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart \
    import InstanciatedSeries, TwoAxesInstanciatedChart

import numpy as np


class CCTechnoDiscipline(TechnoDiscipline):

    # ontology information
    _ontology_data = {
        'label': 'Carbon Capture Techology Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-air-freshener fa-fw',
        'version': '',
    }
    DESC_IN = {'transport_cost': {'type': 'dataframe', 'unit': '$/t', 'visibility': TechnoDiscipline.SHARED_VISIBILITY,
                                  'namespace': 'ns_carbon_capture',
                                  'dataframe_descriptor': {'years': ('int',  [1900, 2100], False),
                                                           'transport': ('float',  None, True)},
                                  'dataframe_edition_locked': False},
               'transport_margin': {'type': 'dataframe', 'unit': '%', 'visibility': TechnoDiscipline.SHARED_VISIBILITY,
                                    'namespace': 'ns_carbon_capture',
                                    'dataframe_descriptor': {'years': ('int',  [1900, 2100], False),
                                                             'margin': ('float',  None, True)},
                                    'dataframe_edition_locked': False},
               'fg_ratio_effect': {'type': 'bool', 'visibility': TechnoDiscipline.SHARED_VISIBILITY,
                                   'namespace': 'ns_carbon_capture', 'default': True},
               'data_fuel_dict': {'type': 'dict', 'visibility': TechnoDiscipline.SHARED_VISIBILITY,
                                  'namespace': 'ns_carbon_capture', 'default': CarbonCapture.data_energy_dict,
                                  'unit': 'defined in dict'},

               }
    DESC_IN.update(TechnoDiscipline.DESC_IN)

    _maturity = 'Research'

    energy_name = CarbonCapture.name

    def set_partial_derivatives_flue_gas(self, energy_name='electricity'):

        inputs_dict = self.get_sosdisc_inputs()
        scaling_factor_invest_level = inputs_dict['scaling_factor_invest_level']
        scaling_factor_techno_consumption = self.get_sosdisc_inputs(
            'scaling_factor_techno_consumption')
        scaling_factor_techno_production = self.get_sosdisc_inputs(
            'scaling_factor_techno_production')
        dcapex_dfluegas = self.techno_model.compute_dcapex_dfg_ratio(
            inputs_dict['flue_gas_mean']['flue_gas_mean'].values,
            inputs_dict['invest_level'].loc[inputs_dict['invest_level']['years'] <=
                                            inputs_dict['year_end']]['invest'].values,
            inputs_dict['techno_infos_dict'], inputs_dict['fg_ratio_effect'])

        crf = self.techno_model.compute_crf(inputs_dict['techno_infos_dict'])
        dfactory_dfluegas = dcapex_dfluegas * \
            (crf + inputs_dict['techno_infos_dict']['Opex_percentage'])

        delec_dflue_gas = self.techno_model.compute_delec_dfg_ratio(
            inputs_dict['flue_gas_mean']['flue_gas_mean'].values, inputs_dict['fg_ratio_effect'], energy_name)

        margin = inputs_dict['margin'].loc[inputs_dict['margin']['years']
                                           <= inputs_dict['year_end']]['margin'].values

        dprice_dfluegas = (dfactory_dfluegas + delec_dflue_gas) * np.split(margin, len(margin)) / \
            100.0

        self.set_partial_derivative_for_other_types(
            ('techno_prices', f'{self.techno_name}'), ('flue_gas_mean', 'flue_gas_mean'), dprice_dfluegas)

        self.set_partial_derivative_for_other_types(
            ('techno_prices', f'{self.techno_name}_wotaxes'), ('flue_gas_mean', 'flue_gas_mean'), dprice_dfluegas)

        capex = self.get_sosdisc_outputs('techno_detailed_prices')[
            f'Capex_{self.techno_name}'].values

        dprod_dfluegas = self.techno_model.compute_dprod_dfluegas(
            capex, inputs_dict['invest_level']['invest'].values,
            inputs_dict['invest_before_ystart']['invest'].values,
            inputs_dict['techno_infos_dict'], dcapex_dfluegas)

        self.set_partial_derivative_for_other_types(
            ('techno_production', f'{self.energy_name} ({self.techno_model.product_energy_unit})'), (
                'flue_gas_mean', 'flue_gas_mean'),
            dprod_dfluegas * self.techno_model.applied_ratio['applied_ratio'].values[:, np.newaxis] * scaling_factor_invest_level / scaling_factor_techno_production)

        production, consumption = self.get_sosdisc_outputs(
            ['techno_production', 'techno_consumption'])
        for column in consumption:
            dprod_column_dfluegas = dprod_dfluegas.copy()
            if column not in ['years']:
                var_cons = (consumption[column] /
                            production[f'{self.energy_name} ({self.techno_model.product_energy_unit})']).fillna(
                    0)
                for line in range(len(consumption[column].values)):
                    dprod_column_dfluegas[line, :] = dprod_dfluegas[line,
                                                                    :] * var_cons[line]
                self.set_partial_derivative_for_other_types(
                    ('techno_consumption', column), ('flue_gas_mean', 'flue_gas_mean'),
                    dprod_column_dfluegas * self.techno_model.applied_ratio['applied_ratio'].values[:, np.newaxis] * scaling_factor_invest_level / scaling_factor_techno_production)
                self.set_partial_derivative_for_other_types(
                    ('techno_consumption_woratio',
                     column), ('flue_gas_mean', 'flue_gas_mean'),
                    dprod_column_dfluegas * scaling_factor_invest_level / scaling_factor_techno_production)

        dnon_use_capital_dflue_gas_mean, dtechnocapital_dflue_gas_mean = self.techno_model.compute_dnon_usecapital_dfluegas(
            dcapex_dfluegas, dprod_dfluegas)

        self.set_partial_derivative_for_other_types(
            ('non_use_capital', self.techno_model.name), ('flue_gas_mean', 'flue_gas_mean'), dnon_use_capital_dflue_gas_mean)
        self.set_partial_derivative_for_other_types(
            ('techno_capital', self.techno_model.name), ('flue_gas_mean', 'flue_gas_mean'), dtechnocapital_dflue_gas_mean)

    def get_chart_filter_list(self, proxy):

        chart_filters = []
        chart_list = ['Detailed prices',
                      'Consumption and production',
                      'Initial Production']
        if self.get_sosdisc_inputs('is_apply_ratio'):
            chart_list.extend(['Applied Ratio'])
        chart_filters.append(ChartFilter(
            'Charts', chart_list, chart_list, 'charts'))

        price_unit_list = ['$/tCO2']
        chart_filters.append(ChartFilter(
            'Price unit', price_unit_list, price_unit_list, 'price_unit'))
        return chart_filters

    def get_post_processing_list(self, proxy, filters=None):

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
            new_chart = self.get_chart_detailed_price_in_dollar_tCO2(proxy)
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'Consumption and production' in charts:
            new_chart = self.get_chart_investments(proxy)
            if new_chart is not None:
                instanciated_charts.append(new_chart)

            new_charts = self.get_charts_consumption_and_production(proxy)
            for new_chart in new_charts:
                if new_chart is not None:
                    instanciated_charts.append(new_chart)

            new_charts = self.get_charts_consumption_and_production_energy(proxy)
            for new_chart in new_charts:
                if new_chart is not None:
                    instanciated_charts.append(new_chart)

        if 'Applied Ratio' in charts:
            new_chart = self.get_chart_applied_ratio(proxy)
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'Initial Production' in charts:
            if 'initial_production' in proxy.get_data_in():
                new_chart = self.get_chart_initial_production(proxy)
                if new_chart is not None:
                    instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_chart_detailed_price_in_dollar_tCO2(self, proxy):

        techno_detailed_prices = proxy.get_sosdisc_outputs(
            'techno_detailed_prices')

        chart_name = f'Detailed prices of {self.techno_name} technology over the years'
        year_start = min(techno_detailed_prices['years'].values.tolist())
        year_end = max(techno_detailed_prices['years'].values.tolist())
        minimum = 0
        maximum = max(
            (techno_detailed_prices[self.techno_name].values).tolist()) * 1.2

        new_chart = TwoAxesInstanciatedChart('years', 'Prices [$/tCO2]', [year_start, year_end], [minimum, maximum],
                                             chart_name=chart_name)

        if 'percentage_resource' in proxy.get_data_in():
            percentage_resource = proxy.get_sosdisc_inputs(
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

    def get_chart_investments(self, proxy):
        # Chart for input investments
        input_investments = proxy.get_sosdisc_inputs('invest_level')

        chart_name = f'Input investments over the years'

        new_chart = TwoAxesInstanciatedChart('years', 'Investments [G$]',
                                             chart_name=chart_name, stacked_bar=True)
        invest = input_investments['invest'].values
        serie = InstanciatedSeries(
            input_investments['years'].values.tolist(),
            invest.tolist(), '', 'bar')

        new_chart.series.append(serie)

        return new_chart

    def get_charts_consumption_and_production(self, proxy):
        instanciated_charts = []
        # Charts for consumption and prod
        techno_consumption = proxy.get_sosdisc_outputs(
            'techno_detailed_consumption')
        techno_production = proxy.get_sosdisc_outputs(
            'techno_detailed_production')
        chart_name = f'{self.techno_name} resources production & consumption <br>with input investments'

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
                legend_title = f'{products} product'.replace(
                    "(Mt)", "")
                serie = InstanciatedSeries(
                    techno_production['years'].values.tolist(),
                    energy_twh.tolist(), legend_title, 'bar')

                new_chart.series.append(serie)
        instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_charts_consumption_and_production_energy(self, proxy):
        instanciated_charts = []
        # Charts for consumption and prod
        techno_consumption = proxy.get_sosdisc_outputs(
            'techno_detailed_consumption')
        techno_production = proxy.get_sosdisc_outputs(
            'techno_detailed_production')
        chart_name = f'{self.techno_name} energy production & consumption<br>with input investments'

        new_chart = TwoAxesInstanciatedChart('years', 'Energy [TWh]',
                                             chart_name=chart_name, stacked_bar=True)

        for reactant in techno_consumption.columns:
            if reactant != 'years' and reactant.endswith('(TWh)'):
                energy_twh = -techno_consumption[reactant].values
                legend_title = f'{reactant} consumption'.replace(
                    "(TWh)", "")
                serie = InstanciatedSeries(
                    techno_consumption['years'].values.tolist(),
                    energy_twh.tolist(), legend_title, 'bar')

                new_chart.series.append(serie)

        for products in techno_production.columns:
            if products != 'years' and products.endswith('(TWh)'):
                energy_twh = techno_production[products].values
                legend_title = f'{products}'.replace(
                    "(TWh)", "")
                serie = InstanciatedSeries(
                    techno_production['years'].values.tolist(),
                    energy_twh.tolist(), legend_title, 'bar')

                new_chart.series.append(serie)
        instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_chart_initial_production(self, proxy):

        year_start = proxy.get_sosdisc_inputs(
            'year_start')
        initial_production = proxy.get_sosdisc_inputs(
            'initial_production')
        initial_age_distrib = proxy.get_sosdisc_inputs(
            'initial_age_distrib')
        initial_prod = initial_age_distrib.copy(deep=True)
        initial_prod['CO2 (Mt)'] = initial_prod['distrib'] / \
            100.0 * initial_production
        initial_prod['years'] = year_start - initial_prod['age']
        initial_prod.sort_values('years', inplace=True)
        initial_prod['cum CO2 (Mt)'] = initial_prod['CO2 (Mt)'].cumsum()

        study_production = proxy.get_sosdisc_outputs(
            'techno_detailed_production')
        chart_name = f'World CO2 capture via {self.techno_name}<br>with 2020 factories distribution'

        new_chart = TwoAxesInstanciatedChart('years', f'{self.energy_name} (Mt)',
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
