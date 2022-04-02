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

from energy_models.core.stream_type.resources_data_disc import get_static_CO2_emissions, get_static_prices
from sos_trades_core.execution_engine.sos_discipline import SoSDiscipline
from sos_trades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sos_trades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart
from climateeconomics.core.core_resources.all_resources_model import AllResourceModel
from energy_models.core.energy_mix.energy_mix import EnergyMix
from copy import deepcopy
from plotly import graph_objects as go
from sos_trades_core.tools.post_processing.plotly_native_charts.instantiated_plotly_native_chart import InstantiatedPlotlyNativeChart


class TechnoDiscipline(SoSDiscipline):

    # ontology information
    _ontology_data = {
        'label': 'Core Technology Type Model',
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

    years_default = np.arange(2020, 2051)

    DESC_IN = {
        'year_start': {'type': 'int', 'default': 2020, 'unit': '[-]', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public', 'structuring': True},
        'year_end': {'type': 'int', 'default': 2050, 'unit': '[-]', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public', 'structuring': True},
        'invest_level': {'type': 'dataframe', 'unit': 'G$',
                         'dataframe_descriptor': {'years': ('int',  [1900, 2100], False),
                                                  'invest': ('float',  None, True)},
                         'dataframe_edition_locked': False},
        'energy_prices': {'type': 'dataframe', 'unit': '$/MWh', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy'},
        'energy_CO2_emissions': {'type': 'dataframe', 'unit': 'kgCO2/kWh', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy'},
        'margin': {'type': 'dataframe', 'unit': '%'},
        'CO2_taxes': {'type': 'dataframe', 'unit': '$/tCO2', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_study',
                      'dataframe_descriptor': {'years': ('int',  [1900, 2100], False),
                                               'CO2_tax': ('float',  None, True)},
                      'dataframe_edition_locked': False},
        'resources_price': {'type': 'dataframe', 'unit': '$/t', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_resource'},
        'resources_CO2_emissions': {'type': 'dataframe', 'unit': 'kgCO2/kg', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_resource'},
        'scaling_factor_invest_level': {'type': 'float', 'default': 1e3, 'user_level': 2},
        'scaling_factor_techno_consumption': {'type': 'float', 'default': 1e3, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public', 'user_level': 2},
        'scaling_factor_techno_production': {'type': 'float', 'default': 1e3, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public', 'user_level': 2},
        'is_apply_ratio': {'type': 'bool', 'default': True, 'user_level': 2, 'structuring': True, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'is_stream_demand': {'type': 'bool', 'default': True, 'user_level': 2, 'structuring': True, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'is_apply_resource_ratio': {'type': 'bool', 'default': False, 'user_level': 2, 'structuring': True, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'}}

    # -- Change output that are not clear, transform to dataframe since r_* is price
    DESC_OUT = {
        'techno_detailed_prices': {'type': 'dataframe', 'unit': '$/MWh'},
        'techno_prices': {'type': 'dataframe', 'unit': '$/MWh'},
        'techno_detailed_consumption': {'type': 'dataframe', 'unit': 'TWh or Mt'},
        'techno_consumption': {'type': 'dataframe'},
        'techno_consumption_woratio': {'type': 'dataframe'},
        'techno_detailed_production': {'type': 'dataframe', 'unit': 'TWh or Mt'},
        'techno_production': {'type': 'dataframe'},
        'age_distrib_production': {'type': 'dataframe', 'unit': 'TWh'},
        'mean_age_production': {'type': 'dataframe'},
        'CO2_emissions': {'type': 'dataframe', 'unit': 'kgCO2/kWh'},
        'CO2_emissions_detailed': {'type': 'dataframe', 'unit': 'kgCO2/kWh'},
        'land_use_required': {'type': 'dataframe', 'unit': 'Gha'},
        'applied_ratio': {'type': 'dataframe', 'unit': '-'},
        'lost_capital': {'type': 'dataframe', 'unit': 'G$'},
        'techno_capital': {'type': 'dataframe', 'unit': 'G$'},
    }
    _maturity = 'Research'

    techno_name = 'Fill techno name'
    energy_name = 'Fill the energy name for this techno'

    def __init__(self, sos_name, ee):

        SoSDiscipline.__init__(self, sos_name, ee)
        self.techno_model = None

    def setup_sos_disciplines(self):
        dynamic_inputs = {}
        if self._data_in is not None:

            self.update_default_dataframes_with_years()

            if 'is_apply_ratio' in self._data_in:
                year_start, year_end = self.get_sosdisc_inputs(
                    ['year_start', 'year_end'])
                years = np.arange(year_start, year_end + 1)
                if self.get_sosdisc_inputs('is_stream_demand'):
                    demand_ratio_dict = dict(
                        zip(EnergyMix.energy_list, np.linspace(1.0, 1.0, len(years)) * 100.0))
                    demand_ratio_dict['years'] = years
                    all_streams_demand_ratio_default = pd.DataFrame(
                        demand_ratio_dict)
                    dynamic_inputs['all_streams_demand_ratio'] = {'type': 'dataframe', 'unit': '-',
                                                                  'default': all_streams_demand_ratio_default,
                                                                  'visibility': SoSDiscipline.SHARED_VISIBILITY,
                                                                  'namespace': 'ns_energy'}
                if self.get_sosdisc_inputs('is_apply_resource_ratio'):
                    resource_ratio_dict = dict(
                        zip(EnergyMix.RESOURCE_LIST, np.ones(len(years)) * 100.0))
                    resource_ratio_dict['years'] = years
                    all_resource_ratio_usable_demand_default = pd.DataFrame(
                        resource_ratio_dict)
                    dynamic_inputs[AllResourceModel.RATIO_USABLE_DEMAND] = {'type': 'dataframe', 'unit': '-',
                                                                            'default': all_resource_ratio_usable_demand_default,
                                                                            'visibility': SoSDiscipline.SHARED_VISIBILITY,
                                                                            'namespace': 'ns_resource'}
            self.add_inputs(dynamic_inputs)

    def update_default_dataframes_with_years(self):
        '''
        Update all default dataframes with years 
        '''
        if 'year_start' in self._data_in:
            year_start, year_end = self.get_sosdisc_inputs(
                ['year_start', 'year_end'])
            years = np.arange(year_start, year_end + 1)
            default_margin = pd.DataFrame({'years': years,
                                           'margin': 110.0})

            self.set_dynamic_default_values({'resources_price': get_static_prices(years),
                                             'resources_CO2_emissions': get_static_CO2_emissions(years),
                                             'margin': default_margin,
                                             'transport_cost': pd.DataFrame({'years': years,
                                                                             'transport': 0.0}),
                                             'transport_margin': default_margin})

    def run(self):
        '''
        Generic run for all technologies 
        '''
        # -- get inputs
        inputs_dict = self.get_sosdisc_inputs()
        # -- configure class with inputs
        self.techno_model.configure_parameters_update(inputs_dict)
        # -- compute informations
        cost_details = self.techno_model.compute_price()

        self.techno_model.compute_consumption_and_production()

        # Create a datafarame containing all the ratios
        self.techno_model.select_ratios()

        # Apply the ratios, if a relevant one (resource consumed by the techno)
        # is inferior to one
        self.techno_model.apply_ratios_on_consumption_and_production(
            inputs_dict['is_apply_ratio'])

        self.techno_model.compute_lost_capital()
        age_distribution = self.techno_model.get_all_age_distribution()
        mean_age_production = self.techno_model.get_mean_age_over_years()

        # Scale production and consumption
        consumption_detailed = deepcopy(self.techno_model.consumption)
        production_detailed = deepcopy(self.techno_model.production)
        for column in self.techno_model.consumption.columns:
            if column == 'years':
                continue
            self.techno_model.consumption[column] = self.techno_model.consumption[column].values / \
                inputs_dict['scaling_factor_techno_consumption']
            self.techno_model.consumption_woratio[column] = self.techno_model.consumption_woratio[column].values / \
                inputs_dict['scaling_factor_techno_consumption']
        for column in self.techno_model.production.columns:
            if column == 'years':
                continue
            self.techno_model.production[column] = self.techno_model.production[column].values / \
                inputs_dict['scaling_factor_techno_production']
            self.techno_model.production_woratio[column] = self.techno_model.production_woratio[column].values / \
                inputs_dict['scaling_factor_techno_production']

        outputs_dict = {'techno_detailed_prices': cost_details,
                        'techno_prices': cost_details[['years', self.techno_name, f'{self.techno_name}_wotaxes']],
                        'techno_detailed_consumption': consumption_detailed,
                        'techno_consumption': self.techno_model.consumption,
                        'techno_consumption_woratio': self.techno_model.consumption_woratio,
                        'techno_detailed_production': production_detailed,
                        'techno_production': self.techno_model.production,
                        'age_distrib_production': age_distribution,
                        'mean_age_production': mean_age_production,
                        'CO2_emissions': self.techno_model.carbon_emissions[['years', self.techno_name]],
                        'CO2_emissions_detailed': self.techno_model.carbon_emissions,
                        'land_use_required': self.techno_model.techno_land_use,
                        'applied_ratio': self.techno_model.applied_ratio,
                        'lost_capital': self.techno_model.lost_capital,
                        'techno_capital': self.techno_model.techno_capital,
                        }
        # -- store outputs
        self.store_sos_outputs_values(outputs_dict)

    def compute_sos_jacobian(self):

        years = self.techno_model.years
        inputs_dict = self.get_sosdisc_inputs()
        outputs_dict = self.get_sosdisc_outputs()
        invest_level = inputs_dict['invest_level']
        scaling_factor_invest_level = inputs_dict['scaling_factor_invest_level']
        scaling_factor_techno_production = inputs_dict['scaling_factor_techno_production']
        production = outputs_dict['techno_production']
        consumption = outputs_dict['techno_consumption']
        ratio_df = self.techno_model.ratio_df
        dcapex_dinvest = self.techno_model.compute_dcapex_dinvest(
            invest_level.loc[invest_level['years']
                             <= self.techno_model.year_end]['invest'].values * scaling_factor_invest_level, self.techno_model.techno_infos_dict, self.techno_model.initial_production)

        crf = self.techno_model.compute_crf(
            self.techno_model.techno_infos_dict)
        dfactory_dinvest = dcapex_dinvest * \
            (crf + self.techno_model.techno_infos_dict['Opex_percentage'])

        margin = self.techno_model.margin['margin'].values
        self.dprice_dinvest = dfactory_dinvest * np.split(margin, len(margin)) / \
            100.0

        self.set_partial_derivative_for_other_types(
            ('techno_prices', f'{self.techno_name}'), ('invest_level', 'invest'), self.dprice_dinvest * scaling_factor_invest_level)
        self.set_partial_derivative_for_other_types(
            ('techno_prices', f'{self.techno_name}_wotaxes'), ('invest_level', 'invest'), self.dprice_dinvest * scaling_factor_invest_level)

        capex = outputs_dict['techno_detailed_prices'][
            f'Capex_{self.techno_name}'].values
        # Compute jacobian for enegy_type production
        self.dprod_dinvest = self.techno_model.compute_dprod_dinvest(
            capex, invest_level['invest'].values * scaling_factor_invest_level,
            self.techno_model.invest_before_ystart['invest'].values,
            self.techno_model.techno_infos_dict, dcapex_dinvest)

        applied_ratio = outputs_dict['applied_ratio']['applied_ratio'].values
        dprod_name_dinvest = (
            self.dprod_dinvest.T * applied_ratio).T * scaling_factor_invest_level / scaling_factor_techno_production
        self.set_partial_derivative_for_other_types(
            ('techno_production', f'{self.energy_name} ({self.techno_model.product_energy_unit})'), (
                'invest_level', 'invest'), dprod_name_dinvest)

        #---Gradient main techno prod vs each ratio
        dapplied_ratio_dratio = self.techno_model.compute_dapplied_ratio_dratios(
            inputs_dict['is_apply_ratio'])
        if 'all_streams_demand_ratio' in inputs_dict.keys():
            for ratio_name in inputs_dict['all_streams_demand_ratio'].columns:
                if ratio_name not in ['years']:
                    production_woratio = self.techno_model.production_woratio[
                        f'{self.energy_name} ({self.techno_model.product_energy_unit})']
                    dprod_dratio = self.techno_model.compute_dprod_dratio(
                        production_woratio, ratio_name=ratio_name,
                        dapplied_ratio_dratio=dapplied_ratio_dratio)
                    self.set_partial_derivative_for_other_types(
                        ('techno_production',
                         f'{self.energy_name} ({self.techno_model.product_energy_unit})'), ('all_streams_demand_ratio', ratio_name),
                        dprod_dratio / 100.)
                    dland_use_dratio = self.techno_model.compute_dprod_dratio(
                        self.techno_model.techno_land_use_woratio[
                            f'{self.techno_model.name} (Gha)'], ratio_name=ratio_name,
                        dapplied_ratio_dratio=dapplied_ratio_dratio)
                    self.set_partial_derivative_for_other_types(
                        ('land_use_required', f'{self.techno_model.name} (Gha)'), ('all_streams_demand_ratio', ratio_name),  dland_use_dratio / 100.)

        # Compute jacobian for other energy production/consumption
        self.dprod_column_dinvest = {}
        for column in production:
            dprod_column_dinvest = self.dprod_dinvest.copy()
            if column not in ['years', f'{self.energy_name} ({self.techno_model.product_energy_unit})']:
                var_prod = (production[column] /
                            production[f'{self.energy_name} ({self.techno_model.product_energy_unit})']).fillna(
                    0)
                for line in range(len(years)):
                    # Problem when invest is zero at the first year and prod
                    # consequently zero (but gradient is not null)
                    if self.techno_model.is_invest_before_year(years[line] - self.techno_model.techno_infos_dict['construction_delay']) \
                            and var_prod[line] == 0.0 and self.dprod_dinvest[line, :].sum() != 0.0 and line != len(years) - 1:

                        var_prod[line] = var_prod[line + 1]
                    dprod_column_dinvest[line, :] = self.dprod_dinvest[line,
                                                                       :] * var_prod[line]
                self.dprod_column_dinvest[column] = dprod_column_dinvest
                self.set_partial_derivative_for_other_types(
                    ('techno_production', column), ('invest_level', 'invest'),
                    (dprod_column_dinvest.T * applied_ratio).T * scaling_factor_invest_level / scaling_factor_techno_production)

                #---Gradient other techno prods vs each ratio
                for ratio_name in ratio_df.columns:
                    if 'all_streams_demand_ratio' in inputs_dict.keys():
                        if ratio_name in inputs_dict['all_streams_demand_ratio'].columns and ratio_name not in ['years']:
                            production_woratio = self.techno_model.production_woratio[
                                column]
                            dprod_dratio = self.techno_model.compute_dprod_dratio(
                                production_woratio, ratio_name=ratio_name,
                                dapplied_ratio_dratio=dapplied_ratio_dratio)
                            self.set_partial_derivative_for_other_types(
                                ('techno_production',
                                 column), ('all_streams_demand_ratio', ratio_name),
                                dprod_dratio / 100.)

        for column in consumption:
            self.dcons_column_dinvest = self.dprod_dinvest.copy()
            if column not in ['years']:
                var_cons = (consumption[column] /
                            production[f'{self.energy_name} ({self.techno_model.product_energy_unit})']).fillna(
                    0)
                for line in range(len(years)):
                    # Problem when invest is zero at the first year and prod
                    # consequently zero (but gradient is not null)
                    if self.techno_model.is_invest_before_year(years[line] - self.techno_model.techno_infos_dict['construction_delay']) \
                            and var_cons[line] == 0.0 and self.dprod_dinvest[line, :].sum() != 0.0 and line != len(years) - 1:
                        var_cons[line] = var_cons[line + 1]
                    self.dcons_column_dinvest[line, :] = self.dprod_dinvest[line,
                                                                            :] * var_cons[line]
                self.set_partial_derivative_for_other_types(
                    ('techno_consumption', column), ('invest_level', 'invest'),
                    (self.dcons_column_dinvest.T * applied_ratio).T * scaling_factor_invest_level / scaling_factor_techno_production)
                self.set_partial_derivative_for_other_types(
                    ('techno_consumption_woratio',
                     column), ('invest_level', 'invest'),
                    self.dcons_column_dinvest * scaling_factor_invest_level / scaling_factor_techno_production)
                #---Gradient techno cons vs each ratio
                for ratio_name in ratio_df.columns:
                    if 'all_streams_demand_ratio' in inputs_dict.keys():
                        if ratio_name in inputs_dict['all_streams_demand_ratio'].columns and ratio_name not in ['years']:
                            consumption_woratio = self.techno_model.consumption_woratio[
                                column]
                            dprod_dratio = self.techno_model.compute_dprod_dratio(
                                consumption_woratio, ratio_name=ratio_name,
                                dapplied_ratio_dratio=dapplied_ratio_dratio)
                            self.set_partial_derivative_for_other_types(
                                ('techno_consumption',
                                 column), ('all_streams_demand_ratio', ratio_name),
                                dprod_dratio / 100.)

        dland_use_dinvest = self.techno_model.compute_dlanduse_dinvest()
        derivate_land_use = dland_use_dinvest.copy()

        self.set_partial_derivative_for_other_types(
            ('land_use_required', f'{self.techno_model.name} (Gha)'), ('invest_level', 'invest'), derivate_land_use * applied_ratio[:, np.newaxis] * scaling_factor_invest_level)

        '''
        Lost capital gradients vs invest_level and all_stream_demand_ratio
        '''
        dlost_capital_dinvest, dtechnocapital_dinvest = self.techno_model.compute_dlostcapital_dinvest(
            dcapex_dinvest, self.dprod_dinvest)
        self.set_partial_derivative_for_other_types(
            ('lost_capital', self.techno_model.name), ('invest_level', 'invest'), dlost_capital_dinvest)

        self.set_partial_derivative_for_other_types(
            ('techno_capital', self.techno_model.name), ('invest_level', 'invest'), dtechnocapital_dinvest)

        dapplied_ratio_dratio = self.techno_model.compute_dapplied_ratio_dratios()
        for ratio_name in ratio_df.columns:
            if 'all_streams_demand_ratio' in inputs_dict.keys():
                if ratio_name in inputs_dict['all_streams_demand_ratio'].columns and ratio_name not in ['years']:
                    dlost_capital_dratio = self.techno_model.compute_dlostcapital_dratio(
                        dapplied_ratio_dratio[ratio_name])
                    self.set_partial_derivative_for_other_types(
                        ('lost_capital', self.techno_model.name),
                        ('all_streams_demand_ratio', ratio_name), np.identity(len(years)) * dlost_capital_dratio / 100.0)

    def set_partial_derivatives_techno(self, grad_dict, carbon_emissions, grad_dict_resources={}):
        """
        Generic method to set partial derivatives of techno_prices / energy_prices, energy_CO2_emissions and dco2_emissions/denergy_co2_emissions
        """
        self.dprices_demissions = {}
        self.grad_total = {}
        for energy, value in grad_dict.items():
            self.grad_total[energy] = value * \
                self.techno_model.margin['margin'].values / 100.0
            self.set_partial_derivative_for_other_types(
                ('techno_prices', self.techno_name), ('energy_prices', energy), self.grad_total[energy])
            self.set_partial_derivative_for_other_types(
                ('techno_prices', f'{self.techno_name}_wotaxes'), ('energy_prices', energy), self.grad_total[energy])
            # Means it has no sense to compute carbon emissions as for CC and
            # CS
            if carbon_emissions is not None:
                self.set_partial_derivative_for_other_types(
                    ('CO2_emissions', self.techno_name), ('energy_CO2_emissions', energy), value)

                # to manage gradient when carbon_emissions is null:
                # sign_carbon_emissions = 1 if carbon_emissions >=0, -1 if
                # carbon_emissions < 0
                sign_carbon_emissions = np.sign(
                    carbon_emissions.loc[carbon_emissions['years'] <= self.techno_model.year_end][self.techno_name]) + 1 - np.sign(carbon_emissions.loc[carbon_emissions['years'] <= self.techno_model.year_end][self.techno_name])**2
                grad_on_co2_tax = value * \
                    self.techno_model.CO2_taxes.loc[self.techno_model.CO2_taxes['years'] <= self.techno_model.year_end]['CO2_tax'].values[:, np.newaxis] * np.maximum(
                        0, sign_carbon_emissions).values

                self.dprices_demissions[energy] = grad_on_co2_tax
                self.set_partial_derivative_for_other_types(
                    ('techno_prices', self.techno_name), ('energy_CO2_emissions', energy), self.dprices_demissions[energy])
        if carbon_emissions is not None:
            dCO2_taxes_factory = (self.techno_model.CO2_taxes['years'] <= self.techno_model.carbon_emissions['years'].max(
            )) * self.techno_model.carbon_emissions[self.techno_name].clip(0).values
            dtechno_prices_dCO2_taxes = dCO2_taxes_factory

            self.set_partial_derivative_for_other_types(
                ('techno_prices', self.techno_name), ('CO2_taxes', 'CO2_tax'), dtechno_prices_dCO2_taxes.values * np.identity(len(self.techno_model.years)))

        for resource, value in grad_dict_resources.items():
            self.set_partial_derivative_for_other_types(
                ('techno_prices', self.techno_name), ('resources_price', resource), value *
                self.techno_model.margin['margin'].values / 100.0)
            self.set_partial_derivative_for_other_types(
                ('techno_prices', f'{self.techno_name}_wotaxes'), ('resources_price', resource), value *
                self.techno_model.margin['margin'].values / 100.0)

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['Detailed prices',
                      'Consumption and production',
                      'Initial Production', 'Factory Mean Age', 'CO2 emissions', 'Lost Capital']
        if self.get_sosdisc_inputs('is_apply_ratio'):
            chart_list.extend(['Applied Ratio'])
        chart_filters.append(ChartFilter(
            'Charts', chart_list, chart_list, 'charts'))

        price_unit_list = ['$/MWh', '$/t']
        chart_filters.append(ChartFilter(
            'Price unit', price_unit_list, price_unit_list, 'price_unit'))
        return chart_filters

    def get_post_processing_list(self, filters=None):

        # For the outputs, making a graph for block fuel vs range and blocktime vs
        # range

        instanciated_charts = []
        charts = []
        price_unit_list = ['$/MWh', '$/t']
        data_fuel_dict = self.get_sosdisc_inputs('data_fuel_dict')
        # Overload default value with chart filter
        if filters is not None:
            for chart_filter in filters:
                if chart_filter.filter_key == 'charts':
                    charts = chart_filter.selected_values
                if chart_filter.filter_key == 'price_unit':
                    price_unit_list = chart_filter.selected_values

        if 'Detailed prices' in charts and '$/MWh' in price_unit_list:
            new_chart = self.get_chart_detailed_price_in_dollar_kwh()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'Detailed prices' in charts \
                and '$/t' in price_unit_list \
                and 'calorific_value' in data_fuel_dict:
            new_chart = self.get_chart_detailed_price_in_dollar_kg()
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

            new_chart = self.get_chart_required_land()
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

        if 'Factory Mean Age' in charts:
            new_chart = self.get_chart_factory_mean_age()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'CO2 emissions' in charts:
            new_chart = self.get_chart_co2_emissions_kwh()
            if new_chart is not None:
                instanciated_charts.append(new_chart)
            if 'calorific_value' in data_fuel_dict and 'high_calorific_value' in data_fuel_dict:
                new_chart = self.get_chart_co2_emissions_kg()
                if new_chart is not None:
                    instanciated_charts.append(new_chart)
        if 'Lost Capital' in charts:
            new_chart = self.get_chart_lost_capital()
            if new_chart is not None:
                instanciated_charts.append(new_chart)
        return instanciated_charts

    def get_chart_detailed_price_in_dollar_kwh(self):

        techno_detailed_prices = self.get_sosdisc_outputs(
            'techno_detailed_prices')
        chart_name = f'Detailed prices of {self.techno_name} technology over the years'
        year_start = min(techno_detailed_prices['years'].values.tolist())
        year_end = max(techno_detailed_prices['years'].values.tolist())
        minimum = 0.0
        maximum = max(
            techno_detailed_prices[self.techno_name].values.tolist()) * 1.2

        new_chart = TwoAxesInstanciatedChart('years', 'Prices [$/MWh]', [year_start, year_end], [minimum, maximum],
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
        tot_price_mwh = techno_detailed_prices[self.techno_name].values
        serie = InstanciatedSeries(
            techno_detailed_prices['years'].values.tolist(),
            tot_price_mwh.tolist(), 'Total price with margin', 'lines')

        new_chart.series.append(serie)

        factory_price_mwh = techno_detailed_prices[f'{self.techno_name}_factory'].values
        # Factory price
        serie = InstanciatedSeries(
            techno_detailed_prices['years'].values.tolist(),
            factory_price_mwh.tolist(), 'Factory', 'lines')

        new_chart.series.append(serie)

        if 'energy_costs' in techno_detailed_prices:
            # energy_costs
            ec_price_mwh = techno_detailed_prices['energy_costs'].values
            serie = InstanciatedSeries(
                techno_detailed_prices['years'].values.tolist(),
                ec_price_mwh.tolist(), 'Energy costs', 'lines')

            new_chart.series.append(serie)

        transport_price_mwh = techno_detailed_prices['transport'].values
        # Transport price
        serie = InstanciatedSeries(
            techno_detailed_prices['years'].values.tolist(),
            transport_price_mwh.tolist(), 'Transport', 'lines')

        new_chart.series.append(serie)
        # CO2 taxes
        co2_price_mwh = techno_detailed_prices['CO2_taxes_factory'].values
        serie = InstanciatedSeries(
            techno_detailed_prices['years'].values.tolist(),
            co2_price_mwh.tolist(), 'CO2 taxes due to production', 'lines')
        new_chart.series.append(serie)

        return new_chart

    def get_chart_detailed_price_in_dollar_kg(self):

        techno_detailed_prices = self.get_sosdisc_outputs(
            'techno_detailed_prices')

        chart_name = f'Detailed prices of {self.techno_name} technology over the years'
        year_start = min(techno_detailed_prices['years'].values.tolist())
        year_end = max(techno_detailed_prices['years'].values.tolist())
        data_fuel_dict = self.get_sosdisc_inputs('data_fuel_dict')
        minimum = 0
        maximum = max(
            techno_detailed_prices[self.techno_name].values.tolist()) * 1.2 * data_fuel_dict['calorific_value']

        new_chart = TwoAxesInstanciatedChart('years', 'Prices [$/t]', [year_start, year_end], [minimum, maximum],
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

        techno_kg_price = techno_detailed_prices[self.techno_name].values * \
            data_fuel_dict['calorific_value']
        serie = InstanciatedSeries(
            techno_detailed_prices['years'].values.tolist(),
            techno_kg_price.tolist(), 'Total price with margin', 'lines')

        new_chart.series.append(serie)

        # Factory price
        techno_kg_price = techno_detailed_prices[f'{self.techno_name}_factory'].values * \
            data_fuel_dict['calorific_value']
        serie = InstanciatedSeries(
            techno_detailed_prices['years'].values.tolist(),
            techno_kg_price.tolist(), 'Factory', 'lines')

        new_chart.series.append(serie)
        if 'energy_costs' in techno_detailed_prices:
            # energy_costs
            techno_kg_price = techno_detailed_prices['energy_costs'].values * \
                data_fuel_dict['calorific_value']
            serie = InstanciatedSeries(
                techno_detailed_prices['years'].values.tolist(),
                techno_kg_price.tolist(), 'Energy costs', 'lines')

            new_chart.series.append(serie)
        # Transport price
        techno_kg_price = techno_detailed_prices['transport'].values * \
            data_fuel_dict['calorific_value']
        serie = InstanciatedSeries(
            techno_detailed_prices['years'].values.tolist(),
            techno_kg_price.tolist(), 'Transport', 'lines')

        new_chart.series.append(serie)
        # CO2 taxes
        techno_kg_price = techno_detailed_prices['CO2_taxes_factory'].values * \
            data_fuel_dict['calorific_value']
        serie = InstanciatedSeries(
            techno_detailed_prices['years'].values.tolist(),
            techno_kg_price.tolist(), 'CO2 taxes due to production', 'lines')
        new_chart.series.append(serie)

        return new_chart

    def get_chart_investments(self):
        # Chart for input investments
        input_investments = self.get_sosdisc_inputs('invest_level')
        scaling_factor_invest_level = self.get_sosdisc_inputs(
            'scaling_factor_invest_level')

        chart_name = f'Input investments over the years'

        new_chart = TwoAxesInstanciatedChart('years', 'Investments [M$]',
                                             chart_name=chart_name, stacked_bar=True)
        invest = input_investments['invest'].values * \
            scaling_factor_invest_level
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
        chart_name = f'{self.techno_name} technology energy Production & consumption<br>with input investments'

        new_chart = TwoAxesInstanciatedChart('years', 'Energy [TWh]',
                                             chart_name=chart_name.capitalize(), stacked_bar=True)

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

    def get_chart_applied_ratio(self):
        # Charts for consumption and prod
        applied_ratio = self.get_sosdisc_outputs(
            'applied_ratio')
        chart_name = f'Ratio applied on {self.techno_name} technology energy Production'
        fig = go.Figure()
        fig.add_trace(go.Bar(x=applied_ratio['years'].values.tolist(),
                             y=applied_ratio['applied_ratio'].values.tolist(),
                             marker=dict(color=applied_ratio['applied_ratio'].values.tolist(),
                                         colorscale='Emrld'),
                             hovertext=applied_ratio['min_ratio_name'].values.tolist()))
        new_chart = InstantiatedPlotlyNativeChart(
            fig, chart_name=chart_name, default_title=True)
        return new_chart

    def get_chart_initial_production(self):

        year_start = self.get_sosdisc_inputs(
            'year_start')
        initial_production = self.get_sosdisc_inputs(
            'initial_production')
        initial_age_distrib = self.get_sosdisc_inputs(
            'initial_age_distrib')
        initial_prod = pd.DataFrame({'age': initial_age_distrib['age'].values,
                                     'distrib': initial_age_distrib['distrib'].values, })
        initial_prod['energy (TWh)'] = initial_prod['distrib'] / \
            100.0 * initial_production
        initial_prod['years'] = year_start - initial_prod['age']
        initial_prod.sort_values('years', inplace=True)
        initial_prod['cum energy (TWh)'] = initial_prod['energy (TWh)'].cumsum(
        )
        study_production = self.get_sosdisc_outputs(
            'techno_detailed_production')
        chart_name = f'{self.energy_name} World Production via {self.techno_name}<br>with 2020 factories distribution'

        new_chart = TwoAxesInstanciatedChart('years', f'{self.energy_name} production (TWh)',
                                             chart_name=chart_name.capitalize())

        serie = InstanciatedSeries(
            initial_prod['years'].values.tolist(),
            initial_prod[f'cum energy (TWh)'].values.tolist(), 'Initial production by 2020 factories', 'lines')

        study_prod = study_production[f'{self.energy_name} (TWh)'].values
        new_chart.series.append(serie)
        years_study = study_production['years'].values.tolist()
        years_study.insert(0, year_start - 1)
        study_prod_l = study_prod.tolist()
        study_prod_l.insert(
            0, initial_prod[f'cum energy (TWh)'].values.tolist()[-1])
        serie = InstanciatedSeries(
            years_study,
            study_prod_l, 'Predicted production', 'lines')
        new_chart.series.append(serie)

        return new_chart

    def get_chart_age_distribution_production(self):
        age_distrib_production = self.get_sosdisc_outputs(
            'age_distrib_production')
        chart_name = f'{self.techno_name} factories age in term of TWh of {self.energy_name} production'

        if 'years' in age_distrib_production.columns:
            new_chart = TwoAxesInstanciatedChart('age', f'{self.energy_name} production (TWh)',
                                                 chart_name=chart_name.capitalize())
            years = age_distrib_production['years'].values
            filtered_years = list(
                set([year for year in years if year % 10 == 0]))
            filtered_years.sort()

            for year in filtered_years:
                filtered_df = age_distrib_production.loc[age_distrib_production['years'] == year].sort_values(
                    'age')
                serie = InstanciatedSeries(
                    filtered_df['age'].values.tolist(),
                    filtered_df['distrib_prod (TWh)'].values.tolist(), f'{year}', 'lines')

                new_chart.series.append(serie)

            return new_chart

    def get_chart_factory_mean_age(self):
        age_distrib_production = self.get_sosdisc_outputs(
            'mean_age_production')

        if 'years' in age_distrib_production.columns:
            chart_name = f'{self.techno_name} factories average age over years'

            year_start = min(age_distrib_production['years'].values.tolist())
            year_end = max(age_distrib_production['years'].values.tolist())
            minimum = 0
            maximum = max(age_distrib_production['mean age'].values.tolist())

            new_chart = TwoAxesInstanciatedChart('years', 'Mean age', [year_start, year_end],
                                                 [minimum, maximum + 5],
                                                 chart_name=chart_name.capitalize())

            serie = InstanciatedSeries(
                age_distrib_production['years'].values.tolist(),
                age_distrib_production['mean age'].values.tolist(), '', 'lines')

            new_chart.series.append(serie)

            return new_chart

    def get_chart_co2_emissions_kwh(self):

        carbon_emissions = self.get_sosdisc_outputs('CO2_emissions_detailed')
        chart_name = f'CO2 emissions of {self.energy_name} via {self.techno_name}'
        data_fuel_dict = self.get_sosdisc_inputs('data_fuel_dict')

        new_chart = TwoAxesInstanciatedChart('years', 'CO2 emissions [kgCO2/kWh]',
                                             chart_name=chart_name, stacked_bar=True)

        CO2_per_use = np.zeros(
            len(carbon_emissions['years']))
        if 'CO2_per_use' in data_fuel_dict and 'high_calorific_value' in data_fuel_dict:
            if data_fuel_dict['CO2_per_use_unit'] == 'kg/kg':
                CO2_per_use = np.ones(
                    len(carbon_emissions['years'])) * data_fuel_dict['CO2_per_use'] / data_fuel_dict['high_calorific_value']
            elif data_fuel_dict['CO2_per_use_unit'] == 'kg/kWh':
                CO2_per_use = np.ones(
                    len(carbon_emissions['years'])) * data_fuel_dict['CO2_per_use']
            serie = InstanciatedSeries(
                carbon_emissions['years'].values.tolist(),
                CO2_per_use.tolist(), f'if {self.energy_name} used', 'bar')

            new_chart.series.append(serie)

        for emission_type in carbon_emissions:
            if emission_type == self.techno_name:
                total_carbon_emissions = CO2_per_use + \
                    carbon_emissions[self.techno_name].values
                serie = InstanciatedSeries(
                    carbon_emissions['years'].values.tolist(),
                    carbon_emissions[self.techno_name].values.tolist(), 'Total w/o use', 'lines')
                new_chart.series.append(serie)

                serie = InstanciatedSeries(
                    carbon_emissions['years'].values.tolist(),
                    total_carbon_emissions.tolist(), 'Total if used', 'lines')
                new_chart.series.append(serie)
            elif emission_type != 'years' and not (carbon_emissions[emission_type] == 0).all():
                serie = InstanciatedSeries(
                    carbon_emissions['years'].values.tolist(),
                    carbon_emissions[emission_type].values.tolist(), emission_type, 'bar')
                new_chart.series.append(serie)

        return new_chart

    def get_chart_co2_emissions_kg(self):

        carbon_emissions = self.get_sosdisc_outputs('CO2_emissions_detailed')

        chart_name = f'CO2 emissions from {self.techno_name} technology'

        new_chart = TwoAxesInstanciatedChart('years', 'CO2 emissions [kgCO2/kg]',
                                             chart_name=chart_name, stacked_bar=True)
        data_fuel_dict = self.get_sosdisc_inputs('data_fuel_dict')

        CO2_per_use = np.zeros(
            len(carbon_emissions['years']))
        if 'CO2_per_use' in data_fuel_dict:
            if data_fuel_dict['CO2_per_use_unit'] == 'kg/kg':
                CO2_per_use = np.ones(
                    len(carbon_emissions['years'])) * data_fuel_dict['CO2_per_use']
            elif data_fuel_dict['CO2_per_use_unit'] == 'kg/kWh':
                CO2_per_use = np.ones(
                    len(carbon_emissions['years'])) * data_fuel_dict['CO2_per_use'] * data_fuel_dict['high_calorific_value']
            serie = InstanciatedSeries(
                carbon_emissions['years'].values.tolist(),
                CO2_per_use.tolist(), f'if {self.energy_name} used', 'bar')

            new_chart.series.append(serie)

        for emission_type in carbon_emissions:
            if emission_type == self.techno_name:
                total_carbon_emission_wo_use = carbon_emissions[self.techno_name].values * \
                    data_fuel_dict['high_calorific_value']
                total_carbon_emissions = CO2_per_use + total_carbon_emission_wo_use

                serie = InstanciatedSeries(
                    carbon_emissions['years'].values.tolist(),
                    total_carbon_emission_wo_use.tolist(), 'Total w/o use', 'lines')
                new_chart.series.append(serie)

                serie = InstanciatedSeries(
                    carbon_emissions['years'].values.tolist(),
                    total_carbon_emissions.tolist(), 'Total if used ', 'lines')
                new_chart.series.append(serie)
            elif emission_type != 'years' and not (carbon_emissions[emission_type] == 0).all():
                emissions_kg_kg = carbon_emissions[emission_type].values * \
                    data_fuel_dict['high_calorific_value']
                serie = InstanciatedSeries(
                    carbon_emissions['years'].values.tolist(),
                    emissions_kg_kg.tolist(), emission_type, 'bar')
                new_chart.series.append(serie)

        return new_chart

    def get_chart_required_land(self):
        '''
        if land use required is filled, the chart giving the land use is shown
        '''
        land_use_required = self.get_sosdisc_outputs('land_use_required')

        new_chart = None
        if not (land_use_required[f'{self.techno_name} (Gha)'].all() == 0):
            chart_name = f'Land use required of {self.techno_name} technology over the years'

            new_chart = TwoAxesInstanciatedChart('years', 'Land use required [Gha]',
                                                 chart_name=chart_name)

            serie = InstanciatedSeries(
                land_use_required['years'].values.tolist(),
                land_use_required[f'{self.techno_name} (Gha)'].values.tolist(), 'Gha', 'lines')
            new_chart.series.append(serie)

        return new_chart

    def get_chart_lost_capital(self):
        lost_capital = self.get_sosdisc_outputs(
            'lost_capital')
        techno_capital = self.get_sosdisc_outputs(
            'techno_capital')
        chart_name = f'Lost capital due to unused {self.techno_name} factories vs total capital'

        new_chart = TwoAxesInstanciatedChart('years', 'Capital [G$]',
                                             chart_name=chart_name)

        serie = InstanciatedSeries(
            techno_capital['years'].values.tolist(),
            techno_capital[self.techno_name].values.tolist(), 'Total capital', 'lines')

        new_chart.series.append(serie)

        serie = InstanciatedSeries(
            lost_capital['years'].values.tolist(),
            lost_capital[self.techno_name].values.tolist(), 'Lost Capital', 'bar')

        new_chart.series.append(serie)

        return new_chart
