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

from energy_models.core.energy_mix.energy_mix import EnergyMix
from sos_trades_core.execution_engine.sos_discipline import SoSDiscipline
from sos_trades_core.tools.post_processing.charts.chart_filter import ChartFilter
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.core.stream_type.carbon_models.carbon_storage import CarbonStorage
from sos_trades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart
from sos_trades_core.tools.post_processing.pie_charts.instanciated_pie_chart import InstanciatedPieChart
from energy_models.core.stream_type.energy_models.syngas import Syngas
from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
from energy_models.core.stream_type.energy_models.liquid_fuel import LiquidFuel
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import GaseousHydrogen
from energy_models.core.stream_type.energy_models.liquid_hydrogen import LiquidHydrogen
from copy import deepcopy
from energy_models.core.stream_type.energy_models.solid_fuel import SolidFuel
from energy_models.core.stream_type.energy_models.electricity import Electricity
from sos_trades_core.tools.base_functions.exp_min import compute_dfunc_with_exp_min,\
    compute_func_with_exp_min
from plotly import graph_objects as go
from sos_trades_core.tools.post_processing.plotly_native_charts.instantiated_plotly_native_chart import InstantiatedPlotlyNativeChart
from sos_trades_core.tools.post_processing.tables.instanciated_table import InstanciatedTable
from sos_trades_core.tools.cst_manager.func_manager_common import get_dsmooth_dvariable
from energy_models.core.ccus.ccus import CCUS


class CCUS_Discipline(SoSDiscipline):

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

    DESC_IN = {
        'ccs_list': {'type': 'string_list', 'possible_values': [CarbonCapture.name, CarbonStorage.name],
                     'default': [CarbonCapture.name, CarbonStorage.name],
                     'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_study', 'editable': False, 'structuring': True},
        'year_start': {'type': 'int', 'default': 2020, 'unit': '[-]', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'year_end': {'type': 'int', 'default': 2050, 'unit': '[-]', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'alpha': {'type': 'float', 'range': [0., 1.], 'default': 0.5, 'unit': '-', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_study'},
        'CO2_taxes': {'type': 'dataframe', 'unit': '$/tCO2', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_study',
                      'dataframe_descriptor': {'years': ('int',  [1900, 2100], False),
                                               'CO2_tax': ('float',  None, True)},
                      'dataframe_edition_locked': False},
        'scaling_factor_energy_production': {'type': 'float', 'default': 1e3, 'user_level': 2, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'scaling_factor_energy_consumption': {'type': 'float', 'default': 1e3, 'user_level': 2, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'minimum_energy_production': {'type': 'float', 'default': 1e4, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public',
                                      'unit': 'TWh'},
        'total_prod_minus_min_prod_constraint_ref': {'type': 'float', 'default': 1e4, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ref'},
        'tol_constraint': {'type': 'float', 'default': 1e-3},
        'exp_min': {'type': 'bool', 'default': True, 'user_level': 2},
        'production_threshold': {'type': 'float', 'default': 1e-3},

        'carbonstorage_limit': {'type': 'float', 'default': 12e6, 'unit': 'MT', 'user_level': 2, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ref'},
        'carbonstorage_constraint_ref': {'type': 'float', 'default': 12e6, 'unit': 'MT', 'user_level': 2, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ref'},
        'ratio_ref': {'type': 'float', 'default': 100., 'unit': '', 'user_level': 2, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ref'},
        'co2_emissions_needed_by_energy_mix': {'type': 'dataframe', 'unit': 'Gt', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy'},
        'CO2_emissions_by_use_sources': {'type': 'dataframe', 'unit': 'Gt', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ccs'},
    }

    DESC_OUT = {
        'co2_emissions_ccus': {'type': 'dataframe', 'unit': 'Mt'},
        'co2_emissions_ccus_Gt': {'type': 'dataframe', 'unit': 'Gt', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ccs'},

        'CCS_price': {'type': 'dataframe', 'unit': '$/tCO2', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_study'},
        EnergyMix.CARBON_STORAGE_CONSTRAINT: {'type': 'array', 'unit': '',  'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_functions'},

    }

    energy_name = EnergyMix.name
    stream_class_dict = EnergyMix.stream_class_dict
    SYNGAS_NAME = Syngas.name
    BIOMASS_DRY_NAME = BiomassDry.name
    LIQUID_FUEL_NAME = LiquidFuel.name
    HYDROGEN_NAME = GaseousHydrogen.name
    LIQUID_HYDROGEN_NAME = LiquidHydrogen.name
    SOLIDFUEL_NAME = SolidFuel.name
    ELECTRICITY_NAME = Electricity.name
    GASEOUS_HYDROGEN_NAME = GaseousHydrogen.name

    energy_constraint_list = EnergyMix.energy_constraint_list

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.ccus_model = CCUS(self.energy_name)
        self.ccus_model.configure_parameters(inputs_dict)

    def setup_sos_disciplines(self):

        dynamic_inputs = {}
        dynamic_outputs = {}

        if 'ccs_list' in self._data_in:
            ccs_list = self.get_sosdisc_inputs('ccs_list')
            if ccs_list is not None:
                for ccs_name in ccs_list:
                    dynamic_inputs[f'{ccs_name}.energy_consumption'] = {
                        'type': 'dataframe', 'unit': 'PWh', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ccs'}
                    dynamic_inputs[f'{ccs_name}.energy_consumption_woratio'] = {
                        'type': 'dataframe', 'unit': 'PWh', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ccs'}
                    dynamic_inputs[f'{ccs_name}.energy_production'] = {
                        'type': 'dataframe', 'unit': 'PWh', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ccs'}
                    dynamic_inputs[f'{ccs_name}.energy_prices'] = {
                        'type': 'dataframe', 'unit': '$/MWh', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ccs'}
                    dynamic_inputs[f'{ccs_name}.energy_demand'] = {'type': 'dataframe', 'unit': 'TWh',
                                                                   'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_demand'}

                    dynamic_inputs[f'{ccs_name}.land_use_required'] = {
                        'type': 'dataframe', 'unit': '(Gha)', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ccs'}

                    dynamic_inputs[f'{ccs_name}.data_fuel_dict'] = {
                        'type': 'dict', 'visibility': SoSDiscipline.SHARED_VISIBILITY,
                        'namespace': f'ns_ccs', 'default': self.stream_class_dict[ccs_name].data_energy_dict}

        if 'year_start' in self._data_in and 'year_end' in self._data_in:
            year_start = self.get_sosdisc_inputs('year_start')
            year_end = self.get_sosdisc_inputs('year_end')

            if year_start is not None and year_end is not None:

                dynamic_inputs['co2_for_food'] = {
                    'type': 'dataframe', 'unit': 'Mt', 'default': pd.DataFrame(columns=[f'{CO2.name} for food (Mt)']),  'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy'}

        self.add_inputs(dynamic_inputs)
        self.add_outputs(dynamic_outputs)

    def run(self):
        #-- get inputs
        inputs_dict = self.get_sosdisc_inputs()
        #-- configure class with inputs
        #
        self.ccus_model.configure_parameters_update(inputs_dict)

        self.ccus_model.compute_CO2_emissions()
        self.ccus_model.compute_CCS_price()
        #-- Compute objectives with alpha trades
        alpha = inputs_dict['alpha']
        delta_years = inputs_dict['year_end'] - inputs_dict['year_start'] + 1

        self.ccus_model.compute_carbon_storage_constraint()
        outputs_dict = {
            'co2_emissions_ccus': self.ccus_model.total_co2_emissions,
            'co2_emissions_ccus_Gt': self.ccus_model.total_co2_emissions_Gt,
            'CCS_price': self.ccus_model.CCS_price,
            EnergyMix.CARBON_STORAGE_CONSTRAINT: self.ccus_model.carbon_storage_constraint,
        }

        #-- store outputs

        self.store_sos_outputs_values(outputs_dict)

    def compute_sos_jacobian(self):

        inputs_dict = self.get_sosdisc_inputs()
        outputs_dict = self.get_sosdisc_outputs()
        stream_class_dict = EnergyMix.stream_class_dict
        years = np.arange(inputs_dict['year_start'],
                          inputs_dict['year_end'] + 1)
        energy_list = inputs_dict['ccs_list']
        production_threshold = inputs_dict['production_threshold']
        total_prod_minus_min_prod_constraint_ref = inputs_dict[
            'total_prod_minus_min_prod_constraint_ref']
        energies = [j for j in energy_list if j not in [
            'carbon_storage', 'carbon_capture']]
        scaling_factor_energy_production = inputs_dict['scaling_factor_energy_production']
        scaling_factor_energy_consumption = inputs_dict['scaling_factor_energy_consumption']

        sub_production_dict, sub_consumption_dict = {}, {}
        sub_consumption_woratio_dict = self.ccus_model.sub_consumption_woratio_dict
        for energy in energy_list:
            sub_production_dict[energy] = inputs_dict[f'{energy}.energy_production'] * \
                scaling_factor_energy_production
            sub_consumption_dict[energy] = inputs_dict[f'{energy}.energy_consumption'] * \
                scaling_factor_energy_consumption

        #-------------------------------#
        #---Resource Demand gradients---#
        #-------------------------------#
        resource_list = EnergyMix.RESOURCE_LIST
        for energy in energy_list:
            for resource in inputs_dict[f'{energy}.energy_consumption']:
                if resource in resource_list:
                    self.set_partial_derivative_for_other_types(('All_Demand', resource), (
                        f'{energy}.energy_consumption', resource), scaling_factor_energy_consumption * np.identity(len(years)))
        #-----------------------------#
        #---- Mean Price gradients----#
        #-----------------------------#
        element_dict = dict(zip(energies, energies))

        #--------------------------------#
        #-- New CO2 emissions gradients--#
        #--------------------------------#

        alpha = self.get_sosdisc_inputs('alpha')
        co2_emissions = self.get_sosdisc_outputs('co2_emissions_ccus')
        self.ccus_model.configure_parameters_update(inputs_dict)
        dtot_co2_emissions = self.ccus_model.compute_grad_CO2_emissions(
            co2_emissions, alpha)

        for key, value in dtot_co2_emissions.items():
            co2_emission_column = key.split(' vs ')[0]

            energy_prod_info = key.split(' vs ')[1]
            energy = energy_prod_info.split('#')[0]
            last_part_key = energy_prod_info.split('#')[1]
            if co2_emission_column in co2_emissions.columns and energy in energy_list:

                if last_part_key == 'prod':
                    self.set_partial_derivative_for_other_types(
                        ('co2_emissions_ccus', co2_emission_column), (f'{energy}.energy_production', energy), np.identity(len(years)) * scaling_factor_energy_production * value)
                elif last_part_key == 'cons':
                    for energy_df in energy_list:
                        list_columnsenergycons = list(
                            inputs_dict[f'{energy_df}.energy_consumption'].columns)
                        if f'{energy} (TWh)' in list_columnsenergycons:
                            self.set_partial_derivative_for_other_types(
                                ('co2_emissions_ccus', co2_emission_column), (f'{energy_df}.energy_consumption', f'{energy} (TWh)'), np.identity(len(years)) * scaling_factor_energy_consumption * value)
                elif last_part_key == 'co2_per_use':
                    self.set_partial_derivative_for_other_types(
                        ('co2_emissions_ccus', co2_emission_column), (f'{energy}.CO2_per_use', 'CO2_per_use'), np.identity(len(years)) * value)

                else:
                    very_last_part_key = energy_prod_info.split('#')[2]

                    if very_last_part_key == 'prod':
                        self.set_partial_derivative_for_other_types(
                            ('co2_emissions_ccus', co2_emission_column), (f'{energy}.energy_production', last_part_key), np.identity(len(years)) * scaling_factor_energy_production * value)
                    elif very_last_part_key == 'cons':
                        self.set_partial_derivative_for_other_types(
                            ('co2_emissions_ccus', co2_emission_column), (f'{energy}.energy_consumption', last_part_key), np.identity(len(years)) * scaling_factor_energy_production * value)

            '''
                CO2 emissions Gt
            '''
            if co2_emission_column == f'{CarbonStorage.name} Limited by capture (Mt)':
                co2_emission_column_upd = co2_emission_column.replace(
                    '(Mt)', '(Gt)')
                if last_part_key == 'prod':
                    self.set_partial_derivative_for_other_types(
                        ('co2_emissions_ccus_Gt', co2_emission_column_upd), (f'{energy}.energy_production', energy), np.identity(len(years)) * scaling_factor_energy_production * value / 1.0e3)
                elif last_part_key == 'cons':
                    for energy_df in energy_list:
                        list_columnsenergycons = list(
                            inputs_dict[f'{energy_df}.energy_consumption'].columns)
                        if f'{energy} (TWh)' in list_columnsenergycons:
                            self.set_partial_derivative_for_other_types(
                                ('co2_emissions_ccus_Gt', co2_emission_column_upd), (f'{energy_df}.energy_consumption', f'{energy} (TWh)'), np.identity(len(years)) * scaling_factor_energy_consumption * value / 1.0e3)
                elif last_part_key == 'co2_per_use':
                    self.set_partial_derivative_for_other_types(
                        ('co2_emissions_ccus_Gt', co2_emission_column_upd), (f'{energy}.CO2_per_use', 'CO2_per_use'), np.identity(len(years)) * value / 1.0e3)
                elif energy_prod_info.startswith(f'{CO2.name} for food (Mt)'):
                    self.set_partial_derivative_for_other_types(
                        ('co2_emissions_ccus_Gt', co2_emission_column_upd), ('co2_for_food', f'{CO2.name} for food (Mt)'), np.identity(len(years)) * value / 1.0e3)

                elif energy_prod_info.startswith(f'{CarbonCapture.name} from energy mix (Mt)'):
                    self.set_partial_derivative_for_other_types(
                        ('co2_emissions_ccus_Gt', co2_emission_column_upd), ('CO2_emissions_by_use_sources', f'{CarbonCapture.name} from energy mix (Gt)'), np.identity(len(years)) * value)

                elif energy_prod_info.startswith(f'{CarbonCapture.name} needed by energy mix (Mt)'):
                    self.set_partial_derivative_for_other_types(
                        ('co2_emissions_ccus_Gt', co2_emission_column_upd), ('co2_emissions_needed_by_energy_mix', f'{CarbonCapture.name} needed by energy mix (Gt)'), np.identity(len(years)) * value)

                else:
                    very_last_part_key = energy_prod_info.split('#')[2]
                    if very_last_part_key == 'prod':

                        self.set_partial_derivative_for_other_types(
                            ('co2_emissions_ccus_Gt', co2_emission_column_upd), (f'{energy}.energy_production', last_part_key), np.identity(len(years)) * scaling_factor_energy_production * value / 1.0e3)
                    elif very_last_part_key == 'cons':
                        self.set_partial_derivative_for_other_types(
                            ('co2_emissions_ccus_Gt', co2_emission_column_upd), (f'{energy}.energy_consumption', last_part_key), np.identity(len(years)) * scaling_factor_energy_production * value / 1.0e3)

                '''
                    Carbon storage constraint
                '''
            elif co2_emission_column == 'Carbon storage constraint':

                if last_part_key == 'prod' and energy in energy_list:
                    self.set_partial_derivative_for_other_types(
                        (EnergyMix.CARBON_STORAGE_CONSTRAINT,), (f'{energy}.energy_production', energy),  scaling_factor_energy_production * value)
                elif last_part_key == 'cons' and energy in energy_list:
                    for energy_df in energy_list:
                        list_columnsenergycons = list(
                            inputs_dict[f'{energy_df}.energy_consumption'].columns)
                        if f'{energy} (TWh)' in list_columnsenergycons:
                            self.set_partial_derivative_for_other_types(
                                (EnergyMix.CARBON_STORAGE_CONSTRAINT,), (f'{energy_df}.energy_consumption', f'{energy} (TWh)'), scaling_factor_energy_consumption * value)
                elif last_part_key == 'co2_per_use':
                    self.set_partial_derivative_for_other_types(
                        (EnergyMix.CARBON_STORAGE_CONSTRAINT,), (f'{energy}.CO2_per_use', 'CO2_per_use'),  value)
                elif energy_prod_info.startswith(f'{CO2.name} for food (Mt)'):
                    self.set_partial_derivative_for_other_types(
                        (EnergyMix.CARBON_STORAGE_CONSTRAINT,), ('co2_for_food', f'{CO2.name} for food (Mt)'), value)

                elif energy_prod_info.startswith(f'{CarbonCapture.name} from energy mix (Mt)'):
                    self.set_partial_derivative_for_other_types(
                        (EnergyMix.CARBON_STORAGE_CONSTRAINT,), ('CO2_emissions_by_use_sources', f'{CarbonCapture.name} from energy mix (Gt)'), value * 1e3)

                elif energy_prod_info.startswith(f'{CarbonCapture.name} needed by energy mix (Mt)'):
                    self.set_partial_derivative_for_other_types(
                        (EnergyMix.CARBON_STORAGE_CONSTRAINT,), ('co2_emissions_needed_by_energy_mix', f'{CarbonCapture.name} needed by energy mix (Gt)'), value * 1e3)

                else:
                    very_last_part_key = energy_prod_info.split('#')[2]
                    if very_last_part_key == 'prod':
                        self.set_partial_derivative_for_other_types(
                            (EnergyMix.CARBON_STORAGE_CONSTRAINT,), (f'{energy}.energy_production', last_part_key),  scaling_factor_energy_production * value)
                    elif very_last_part_key == 'cons':
                        self.set_partial_derivative_for_other_types(
                            (EnergyMix.CARBON_STORAGE_CONSTRAINT,), (f'{energy}.energy_consumption', last_part_key),  scaling_factor_energy_production * value)


        if CarbonCapture.name in energy_list:
            self.set_partial_derivative_for_other_types(
                ('CCS_price', 'ccs_price_per_tCO2'), (f'{CarbonCapture.name}.energy_prices', CarbonCapture.name), np.identity(len(years)))
        if CarbonStorage.name in energy_list:
            self.set_partial_derivative_for_other_types(
                ('CCS_price', 'ccs_price_per_tCO2'), (f'{CarbonStorage.name}.energy_prices', CarbonStorage.name), np.identity(len(years)))

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['CCS price', 'Carbon storage constraint',
                      'CO2 storage limited by capture', 'CO2 emissions captured, used and to store']

        chart_filters.append(ChartFilter(
            'Charts', chart_list, chart_list, 'charts'))

        price_unit_list = ['$/MWh', '$/t']
        chart_filters.append(ChartFilter(
            'Price unit', price_unit_list, price_unit_list, 'price_unit'))

        year_start, year_end = self.get_sosdisc_inputs(
            ['year_start', 'year_end'])
        years = list(np.arange(year_start, year_end + 1, 5))
        chart_filters.append(ChartFilter(
            'Years for energy mix', years, [year_start, year_end], 'years'))
        return chart_filters

    def get_post_processing_list(self, filters=None):

        # For the outputs, making a graph for block fuel vs range and blocktime vs
        # range

        instanciated_charts = []
        charts = []

        price_unit_list = ['$/MWh', '$/t']
        years_list = [self.get_sosdisc_inputs('year_start')]
        # Overload default value with chart filter
        if filters is not None:
            for chart_filter in filters:
                if chart_filter.filter_key == 'charts':
                    charts = chart_filter.selected_values
                if chart_filter.filter_key == 'price_unit':
                    price_unit_list = chart_filter.selected_values
                if chart_filter.filter_key == 'years':
                    years_list = chart_filter.selected_values

        if 'Carbon storage constraint' in charts:
            new_chart = self.get_chart_carbon_storage_constraint()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'CCS price' in charts:
            new_chart = self.get_chart_CCS_price()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'CO2 storage limited by capture' in charts:
            new_chart = self.get_chart_co2_limited_storage()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'CO2 emissions captured, used and to store' in charts:
            new_chart = self.get_chart_co2_to_store()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_chart_CCS_price(self):

        ccs_prices = self.get_sosdisc_outputs('CCS_price')

        years = list(ccs_prices['years'].values)

        chart_name = 'CCS price over time'

        new_chart = TwoAxesInstanciatedChart('Years', 'CCS price ($/tCO2)',
                                             chart_name=chart_name)

        visible_line = True

        # add CCS price serie
        new_series = InstanciatedSeries(
            years, ccs_prices['ccs_price_per_tCO2'].values.tolist(), 'CCS price', 'lines', visible_line)
        new_chart.series.append(new_series)

        return new_chart

    def get_chart_co2_to_store(self):
        '''
        Plot a graph to understand CO2 to store
        '''
        chart_name = 'CO2 emissions captured, used and to store'
        co2_emissions = self.get_sosdisc_outputs('co2_emissions_ccus')
        co2_for_food = self.get_sosdisc_inputs('co2_for_food')
        CO2_emissions_by_use_sources = self.get_sosdisc_inputs(
            'CO2_emissions_by_use_sources')
        co2_emissions_needed_by_energy_mix = self.get_sosdisc_inputs(
            'co2_emissions_needed_by_energy_mix')
        new_chart = TwoAxesInstanciatedChart('years', 'CO2 emissions (Gt)',
                                             chart_name=chart_name)

        x_serie_1 = co2_emissions['years'].values.tolist()

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'{CarbonCapture.name} (Mt) from CC technos'].values / 1.0e3).tolist(), 'CO2 captured from CC technos')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (CO2_emissions_by_use_sources[f'{CarbonCapture.name} from energy mix (Gt)'].values).tolist(), f'CO2 captured from energy mix')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (-co2_emissions_needed_by_energy_mix[f'{CarbonCapture.name} needed by energy mix (Gt)'].values).tolist(), f'{CarbonCapture.name} used by energy mix')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (-co2_for_food[f'{CO2.name} for food (Mt)'].values / 1.0e3).tolist(), f'{CO2.name} used for food')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'{CarbonCapture.name} to be stored (Mt)'].values / 1.0e3).tolist(), f'CO2 to store')
        new_chart.add_series(serie)

        return new_chart

    def get_chart_co2_limited_storage(self):
        '''
        Plot a graph to understand storage
        '''
        chart_name = 'CO2 emissions storage limited by CO2 to store'
        co2_emissions = self.get_sosdisc_outputs('co2_emissions_ccus')
        new_chart = TwoAxesInstanciatedChart('years', 'CO2 emissions (Gt)',
                                             chart_name=chart_name)

        x_serie_1 = co2_emissions['years'].values.tolist()
        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'{CarbonCapture.name} to be stored (Mt)'].values / 1.0e3).tolist(), f'CO2 to store')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'{CarbonStorage.name} (Mt)'].values / 1.0e3).tolist(), f'CO2 storage by invest')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'{CarbonStorage.name} Limited by capture (Mt)'].values / 1.0e3).tolist(), f'CO2 storage limited by CO2 to store')
        new_chart.add_series(serie)

        return new_chart

    def get_chart_co2_emissions_sources(self):
        '''
        Plot all CO2 emissions sources 
        '''
        chart_name = 'CO2 emissions sources'
        co2_emissions = self.get_sosdisc_outputs('co2_emissions')
        new_chart = TwoAxesInstanciatedChart('years', 'CO2 emissions (Gt)',
                                             chart_name=chart_name)

        x_serie_1 = co2_emissions['years'].values.tolist()

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions['Total CO2 by use (Mt)'].values / 1.0e3).tolist(), 'CO2 by use (net production burned)')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'Total {CarbonCapture.flue_gas_name} (Mt)'].values / 1.0e3).tolist(), 'Flue gas from plants')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1, (co2_emissions[f'{CarbonCapture.name} from energy mix (Mt)'].values / 1.0e3).tolist(), 'Carbon capture from energy mix (FT or Sabatier)')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'{CO2.name} from energy mix (Mt)'].values / 1.0e3).tolist(), 'CO2 from energy mix (machinery fuels)')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions['CO2 emissions sources'].values / 1.0e3).tolist(), 'Total sources')
        new_chart.add_series(serie)

        return new_chart

    def get_chart_carbon_storage_constraint(self):

        co2_emissions = self.get_sosdisc_outputs('co2_emissions_ccus_Gt')

        carbon_storage_limit = self.get_sosdisc_inputs('carbonstorage_limit')
        years = list(co2_emissions['years'])

        chart_name = 'Cumulated carbon storage (Gt) vs years'

        year_start = years[0]
        year_end = years[len(years) - 1]

        new_chart = TwoAxesInstanciatedChart('years', 'Cumulated carbon storage (Gt)',
                                             chart_name=chart_name)

        visible_line = True

        new_series = InstanciatedSeries(
            years, list(co2_emissions[f'{CarbonStorage.name} Limited by capture (Gt)'].cumsum().values), 'cumulative sum of carbon capture (Gt)', 'lines', visible_line)

        new_chart.series.append(new_series)

        # Rockstrom Limit

        ordonate_data = [carbon_storage_limit / 1e3] * int(len(years) / 5)
        abscisse_data = np.linspace(
            year_start, year_end, int(len(years) / 5))
        new_series = InstanciatedSeries(
            abscisse_data.tolist(), ordonate_data, 'Carbon storage limit (Gt)', 'scatter')

        new_chart.series.append(new_series)

        return new_chart
