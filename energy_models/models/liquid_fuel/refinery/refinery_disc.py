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
import numpy as np

from energy_models.models.liquid_fuel.refinery.refinery import Refinery
from energy_models.core.techno_type.disciplines.liquid_fuel_techno_disc import LiquidFuelTechnoDiscipline

from sos_trades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, TwoAxesInstanciatedChart
from sos_trades_core.tools.post_processing.charts.chart_filter import ChartFilter
from energy_models.core.stream_type.energy_models.liquid_fuel import LiquidFuel
from energy_models.core.stream_type.energy_models.kerosene import Kerosene
from energy_models.core.stream_type.energy_models.gasoline import Gasoline
from energy_models.core.stream_type.energy_models.lpg import LiquefiedPetroleumGas
from energy_models.core.stream_type.energy_models.heating_oil import HeatingOil
from energy_models.core.stream_type.energy_models.ultralowsulfurdiesel import UltraLowSulfurDiesel


class RefineryDiscipline(LiquidFuelTechnoDiscipline):
    """**EnergyModelsDiscipline** is the :class:`~gems.core.discipline.MDODiscipline`
    implementing the computation of Energy Models outputs."""


    # ontology information
    _ontology_data = {
        'label': 'Refinery Liquid Fuel Model',
        'type': 'Test',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-gas-pump fa-fw',
        'version': '',
    }
    techno_name = 'Refinery'
    lifetime = 35
    construction_delay = 3
    # only energetical valuable product taken into acocun. Wastes are not
    # taken into account
    # mass ratio of product for 1 kg of crude oil refined
    product_break_down = {LiquidFuelTechnoDiscipline.kerosene_name: 0.137,
                          LiquidFuelTechnoDiscipline.gasoline_name: 0.465,
                          LiquidFuelTechnoDiscipline.lpg_name: 0.058,
                          LiquidFuelTechnoDiscipline.heating_oil_name: 0.085,
                          LiquidFuelTechnoDiscipline.ulsd_name: 0.094,
                          }

    techno_infos_dict_default = {'maturity': 0,
                                 'Opex_percentage': 0.04,
                                 'CO2_from_production': 0.65 / 2.0,  # we split 0.65 in refinery and oil extraction
                                 # However it is really depending on type of extraction
                                 # see
                                 # https://theicct.org/sites/default/files/ICCT_crudeoil_Eur_Dec2010_sum.pdf
                                 'CO2_from_production_unit': 'kg/kg',
                                 # https://www.e-education.psu.edu/eme801/node/470
                                 # 1 kg of crude oil is 11.3 kWh
                                 # 0.137 * 11.9 kero
                                 # 0.058 * 12.8 lpg
                                 # 0.094 * 11.86 ulsd
                                 # 0.085 * 12.47 heating oil
                                 # 0.465 * 12.06 gasoline
                                 #  'fuel_demand': 0.137 * 11.9 + 0.058 * 12.8 + 0.094 * 11.86 + 0.085 * 12.47 + 0.465 * 12.06 / 11.3,
                                 'fuel_demand': 1,
                                 'fuel_demand_unit': 'kWh/kWh',
                                 # CF : Crude oil refinery on bibliography folder
                                 # ratio elec use / kerosene product
                                 'elec_demand': 0.008,
                                 'elec_demand_unit': 'kWh/kWh',
                                 # for now constant in time but should increase
                                 # with time 10%/10year according to Fasihi2019
                                 'WACC': 0.1,  # Weighted averaged cost of capital for the carbon capture plant
                                 'learning_rate': 0.0,  # 0.15,
                                 'lifetime': lifetime,  # should be modified
                                 'lifetime_unit': 'years',
                                 # 22000 euro/bpd : 1 barrel = 1553,41kwh of
                                 # liquid_fuel per 24 hours
                                 # Capex initial at year 2020
                                 'Capex_init': 22000 / (1553.41 / 24.0 * 8000.0),
                                 'Capex_init_unit': '$/kWh',
                                 'efficiency': 0.89,  # https://publications.anl.gov/anlpubs/2011/01/69026.pdf
                                 'techno_evo_eff': 'no',
                                 'construction_delay': construction_delay,
                                 'pourcentage_of_total': 0.09,
                                 'product_break_down': product_break_down}

    techno_info_dict = techno_infos_dict_default

    initial_production = 53200.0  # in TWh at year_start from ourworldindata

    # Invest from WEI2020
    invest_before_year_start = pd.DataFrame(

        {'past years': np.arange(-construction_delay, 0), 'invest': [462, 477, 470]})

    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime - 1),
                                             'distrib': [4.7, 4.63, 4.52, 4.85, 4.299999999999999,
                                                         4.189999999999999, 4.079999999999998, 3.969999999999998,
                                                         3.8599999999999977, 3.7499999999999973, 3.639999999999997,
                                                         3.5299999999999967, 3.4199999999999964, 3.309999999999996,
                                                         3.1999999999999957, 3.0899999999999954, 2.979999999999995,
                                                         2.8699999999999948, 2.7599999999999945, 2.649999999999994,
                                                         2.539999999999994, 2.4299999999999935, 2.319999999999993,
                                                         2.209999999999993, 2.0999999999999925, 1.9899999999999922,
                                                         1.879999999999992, 1.7699999999999916, 1.6599999999999913,
                                                         1.609999999999991, 1.8399999999999906, 1.7299999999999903,
                                                         1.61999999999999]
                                             })

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default},
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'age': ('int',  [0, 100], False),
                                                                'distrib': ('float',  None, True)},
                                       'dataframe_edition_locked': False},
               'invest_before_ystart': {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int',  [-20, -1], False),
                                                                 'invest': ('float',  None, True)},
                                        'dataframe_edition_locked': False}}
    # -- add specific techno outputs to this
    DESC_IN.update(LiquidFuelTechnoDiscipline.DESC_IN)

    # -- add specific techno outputs to this
    refinery_flue_gas_ratio = np.array([0.12])
    DESC_OUT = {'flue_gas_co2_ratio': {
        'type': 'array', 'default': refinery_flue_gas_ratio}}
    DESC_OUT.update(LiquidFuelTechnoDiscipline.DESC_OUT)

    _maturity = 'Research'

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = Refinery(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)

    def compute_sos_jacobian(self):
        # Grad of price vs energyprice

        LiquidFuelTechnoDiscipline.compute_sos_jacobian(self)

        grad_dict = self.techno_model.grad_price_vs_energy_price()

        carbon_emissions = self.get_sosdisc_outputs(
            'CO2_emissions')

        self.set_partial_derivatives_techno(
            grad_dict, carbon_emissions)

    def set_partial_derivatives_techno(self, grad_dict, carbon_emissions):
        """
        Generic method to set partial derivatives of techno_prices / energy_prices, energy_CO2_emissions and dco2_emissions/denergy_co2_emissions
        """

        for energy, value in grad_dict.items():

            grad_total = value * np.split(self.techno_model.margin['margin'].values, len(self.techno_model.margin['margin'].values)) / \
                100.0
            grad_total_efficiency = grad_total / self.techno_model.configure_efficiency()

            self.set_partial_derivative_for_other_types(
                ('techno_prices', self.techno_name), ('energy_prices', energy), grad_total_efficiency)
            self.set_partial_derivative_for_other_types(
                ('techno_prices', f'{self.techno_name}_wotaxes'), ('energy_CO2_emissions', energy), np.zeros(len(self.techno_model.years)))
            self.set_partial_derivative_for_other_types(
                ('techno_prices', f'{self.techno_name}_wotaxes'), ('energy_prices', energy), grad_total_efficiency)

            self.set_partial_derivative_for_other_types(
                ('CO2_emissions', self.techno_name), ('energy_CO2_emissions', energy), value)

#             self.set_partial_derivative_for_other_types(
#                 ('CO2_emissions', energy), ('energy_CO2_emissions', energy), value)
            grad_on_co2_tax = value * \
                self.techno_model.CO2_taxes.loc[self.techno_model.CO2_taxes['years']
                                                <= self.techno_model.year_end]['CO2_tax'].values[:, np.newaxis] * np.maximum(
                    0, np.sign(carbon_emissions[self.techno_name]))[:, np.newaxis]
            self.set_partial_derivative_for_other_types(
                ('techno_prices', self.techno_name), ('energy_CO2_emissions', energy), grad_on_co2_tax * np.split(self.techno_model.margin['margin'].values, len(self.techno_model.margin['margin'].values)) /
                100.0)

            dCO2_taxes_factory = (self.techno_model.CO2_taxes['years'] <= self.techno_model.carbon_emissions['years'].max(
            )) * self.techno_model.carbon_emissions[self.techno_name].clip(0).values
            dtechno_prices_dCO2_taxes = dCO2_taxes_factory * \
                self.techno_model.margin.loc[self.techno_model.margin['years'] <=
                                             self.techno_model.cost_details['years'].max()]['margin'].values / 100.0

            self.set_partial_derivative_for_other_types(
                ('techno_prices', self.techno_name), ('CO2_taxes', 'CO2_tax'), dtechno_prices_dCO2_taxes.values * np.identity(len(self.techno_model.years)))

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['Detailed prices', 'Prices per flow',
                      'Consumption and production', 'Age Distribution Production',
                      'Initial Production', 'Factory Mean Age', 'CO2 emissions']
        chart_filters.append(ChartFilter(
            'Charts', chart_list, chart_list, 'charts'))

        price_unit_list = ['$/MWh', '$/t', '$/USgallon']
        chart_filters.append(ChartFilter(
            'Price unit', price_unit_list, price_unit_list, 'price_unit'))
        return chart_filters

    def get_post_processing_list(self, filters=None):
        instanciated_charts = []
        charts = []
        price_unit_list = ['$/MWh', '$/t', "$/USgallon"]
        years_list = [self.get_sosdisc_inputs('year_start')]
        data_fuel_dict = self.get_sosdisc_inputs('data_fuel_dict')
        other_fuel_dict = self.get_sosdisc_inputs('other_fuel_dict')
        # Overload default value with chart filter
        if filters is not None:
            for chart_filter in filters:
                if chart_filter.filter_key == 'charts':
                    charts = chart_filter.selected_values
                if chart_filter.filter_key == 'price_unit':
                    price_unit_list = chart_filter.selected_values

        generic_filter = LiquidFuelTechnoDiscipline.get_chart_filter_list(
            self)
        instanciated_charts = LiquidFuelTechnoDiscipline.get_post_processing_list(
            self, generic_filter)

        if 'Detailed prices' in charts and '$/USgallon' in price_unit_list:
            techno_detailed_prices = self.get_sosdisc_outputs(
                'techno_detailed_prices')
            chart_name = f'Detailed prices of {self.techno_name} technology over the years'

            new_chart = TwoAxesInstanciatedChart('years', 'Prices [$/USgallon]',
                                                 chart_name=chart_name)

            if 'part_of_total' in self._data_in:
                part_of_total = self.get_sosdisc_inputs('part_of_total')
                new_chart.annotation_upper_left = {
                    'Percentage of total price': f'{part_of_total[0]*100.0} %'}
                tot_price = techno_detailed_prices[self.techno_name].values *  \
                    data_fuel_dict['calorific_value'] / \
                    part_of_total
                serie = InstanciatedSeries(
                    techno_detailed_prices['years'].values.tolist(),
                    tot_price.tolist(), 'Total price without percentage', 'lines')
                new_chart.series.append(serie)
            # Add total price
            techno_gallon_price = techno_detailed_prices[self.techno_name].values *  \
                data_fuel_dict['calorific_value'] * \
                data_fuel_dict['density'] / 1e6 * 3.78
            serie = InstanciatedSeries(
                techno_detailed_prices['years'].values.tolist(),
                techno_gallon_price.tolist(), 'Total price with margin', 'lines')

            new_chart.series.append(serie)
            instanciated_charts.append(new_chart)

        if 'Prices per flow' in charts and '$/USgallon' in price_unit_list:
            techno_detailed_prices = self.get_sosdisc_outputs(
                'techno_detailed_prices')
            chart_name = f'Refinery breakdown price for {self.techno_name} technology over the years'
            year_start = min(techno_detailed_prices['years'].values.tolist())
            year_end = max(techno_detailed_prices['years'].values.tolist())

            new_chart = TwoAxesInstanciatedChart('years', 'Prices [$/USgallon]',
                                                 chart_name=chart_name)

            for energy in other_fuel_dict:
                # if it s a dict, so it is a data_energy_dict
                energy_price_mwh = techno_detailed_prices[self.techno_name].values * \
                    (other_fuel_dict[energy]['calorific_value'] /
                     data_fuel_dict['calorific_value'])

                energy_price_gal = energy_price_mwh *  \
                    data_fuel_dict['calorific_value'] * \
                    data_fuel_dict['density'] / 1e6 * 3.78
                serie = InstanciatedSeries(
                    techno_detailed_prices['years'].values.tolist(),
                    energy_price_gal.tolist(), f'{energy} price', 'lines')
                new_chart.series.append(serie)

            instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_charts_consumption_and_production(self):
        instanciated_charts = []
        # Charts for consumption and prod
        techno_consumption = self.get_sosdisc_outputs(
            'techno_detailed_consumption')
        techno_production = self.get_sosdisc_outputs(
            'techno_detailed_production')
        chart_name = f'{self.techno_name} technology energy Production & consumption<br>with input investments'

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
            if products != 'years' and products.endswith('(TWh)') and products != f'{LiquidFuelTechnoDiscipline.energy_name} (TWh)':
                energy_twh = techno_production[products].values
                legend_title = f'{products} production'.replace(
                    "(TWh)", "")
                serie = InstanciatedSeries(
                    techno_production['years'].values.tolist(),
                    energy_twh.tolist(), legend_title, 'bar')

                new_chart.series.append(serie)
        instanciated_charts.append(new_chart)

        # Check if we have kg in the consumption or prod :

        kg_values_consumption = 0
        reactant_found = None
        for reactant in techno_consumption.columns:
            if reactant != 'years' and reactant.endswith('(Mt)'):
                kg_values_consumption += 1
                reactant_found = reactant

        kg_values_production = 0
        product_found = None
        for product in techno_consumption.columns:
            if product != 'years' and product.endswith('(Mt)'):
                kg_values_production += 1
                product_found = product
        if kg_values_consumption == 1 and kg_values_production == 0:
            legend_title = f'{reactant_found} consumption'.replace(
                "(Mt)", "")
            chart_name = f'{legend_title} of the {self.techno_name} technology<br>with input investments'
        elif kg_values_production == 1 and kg_values_consumption == 0:
            legend_title = f'{product_found} production'.replace(
                "(Mt)", "")
            chart_name = f'{legend_title} of the {self.techno_name} technology<br>with input investments'
        else:
            chart_name = f'{self.techno_name} technology mass Production & consumption<br>with input investments'

        new_chart = TwoAxesInstanciatedChart('years', 'Mass [Mt]',
                                             chart_name=chart_name, stacked_bar=True)

        for reactant in techno_consumption.columns:
            if reactant != 'years' and reactant.endswith('(Mt)'):
                legend_title = f'{reactant} consumption'.replace(
                    "(Mt)", "")
                # 1GT = 1e9T = 1e12 kg
                mass = -techno_consumption[reactant].values
                serie = InstanciatedSeries(
                    techno_consumption['years'].values.tolist(),
                    mass.tolist(), legend_title, 'bar')
                new_chart.series.append(serie)
        for product in techno_production.columns:
            if product != 'years' and product.endswith('(Mt)'):
                legend_title = f'{product} production'.replace(
                    "(Mt)", "")
                # 1GT = 1e9T = 1e12 kg
                mass = techno_production[product].values
                serie = InstanciatedSeries(
                    techno_production['years'].values.tolist(),
                    mass.tolist(), legend_title, 'bar')
                new_chart.series.append(serie)

        if kg_values_consumption > 0 or kg_values_production > 0:
            instanciated_charts.append(new_chart)

        return instanciated_charts
