'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/14-2023/11/16 Copyright 2023 Capgemini

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

from copy import copy, deepcopy
from climateeconomics.core.core_witness.climateeco_discipline import ClimateEcoDiscipline
from energy_models.core.ccus.ccus import CCUS
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.core.stream_type.carbon_models.carbon_storage import CarbonStorage
from energy_models.core.stream_type.carbon_models.carbon_utilization import CarbonUtilization
from energy_models.glossaryenergy import GlossaryEnergy
from sostrades_core.execution_engine.sos_wrapp import SoSWrapp
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart


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

    DESC_IN = {
        GlossaryEnergy.ccs_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                                  'possible_values': CCUS.ccs_list,
                                  'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy_study',
                                  'editable': False,
                                  'structuring': True},
        GlossaryEnergy.YearStart: ClimateEcoDiscipline.YEAR_START_DESC_IN,
        GlossaryEnergy.YearEnd: {'type': 'int',
                        'unit': 'year', 'visibility': 'Shared', 'namespace': 'ns_public',  'range': [2000,2300]},
        'alpha': {'type': 'float', 'range': [0., 1.], 'default': 0.5, 'unit': '-',
                  'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy_study'},
        'scaling_factor_energy_production': {'type': 'float', 'default': 1e3, 'unit': '-', 'user_level': 2,
                                             'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'scaling_factor_energy_consumption': {'type': 'float', 'default': 1e3, 'unit': '-', 'user_level': 2,
                                              'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'carbonstorage_limit': {'type': 'float', 'default': 12e6, 'unit': 'Mt', 'user_level': 2,
                                'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': GlossaryEnergy.NS_REFERENCE},
        'carbonstorage_constraint_ref': {'type': 'float', 'default': 12e6, 'unit': 'Mt', 'user_level': 2,
                                         'visibility': SoSWrapp.SHARED_VISIBILITY,
                                         'namespace': GlossaryEnergy.NS_REFERENCE},
        'co2_emissions_needed_by_energy_mix': {'type': 'dataframe', 'unit': 'Gt',
                                               'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy',

                                               'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                                        GlossaryEnergy.carbon_capture: ('float', None, True),
                                                                        'CO2 from Flue Gas (Mt)': ('float', None, True),
                                                                        GlossaryEnergy.carbon_storage: ('float', None, True),
                                                                        'carbon_capture from energy mix (Gt)': (
                                                                        'float', None, True),
                                                                        'carbon_capture needed by energy mix (Gt)': (
                                                                            'float', None, True),
                                                                        'heat.hightemperatureheat (TWh)': (
                                                                        'float', None, True),
                                                                        'heat.mediumtemperatureheat (TWh)': (
                                                                        'float', None, True),
                                                                        'heat.lowtemperatureheat (TWh)': (
                                                                        'float', None, True),
                                                                        }, },
        'carbon_capture_from_energy_mix': {'type': 'dataframe', 'unit': 'Gt',
                                           'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy',
                                           'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                                    GlossaryEnergy.carbon_capture: ('float', None, True),
                                                                    'CO2 from Flue Gas (Mt)': ('float', None, True),
                                                                    GlossaryEnergy.carbon_storage: ('float', None, True),
                                                                    'carbon_capture from energy mix (Gt)': (
                                                                    'float', None, True),
                                                                    'heat.hightemperatureheat (TWh)': (
                                                                        'float', None, True),
                                                                    'heat.mediumtemperatureheat (TWh)': (
                                                                        'float', None, True),
                                                                    'heat.lowtemperatureheat (TWh)': (
                                                                        'float', None, True),
                                                                    }, }

    }

    DESC_OUT = {
        'co2_emissions_ccus': {'type': 'dataframe', 'unit': 'Mt'},
        'carbon_storage_by_invest': {'type': 'array', 'unit': 'Mt'},
        'co2_emissions_ccus_Gt': {'type': 'dataframe', 'unit': 'Gt', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                                  'namespace': GlossaryEnergy.NS_CCS},

        'CCS_price': {'type': 'dataframe', 'unit': '$/tCO2', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                      'namespace': 'ns_energy_study'},
        EnergyMix.CARBON_STORAGE_CONSTRAINT: {'type': 'array', 'unit': '',
                                              'visibility': SoSWrapp.SHARED_VISIBILITY,
                                              'namespace': GlossaryEnergy.NS_FUNCTIONS},

    }

    def __init__(self, sos_name, logger: logging.Logger):
        super().__init__(sos_name, logger)
        self.ccus_model = None

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.ccus_model = CCUS(GlossaryEnergy.CCUS)
        self.ccus_model.configure_parameters(inputs_dict)

    def setup_sos_disciplines(self):

        dynamic_inputs = {}
        dynamic_outputs = {}

        if GlossaryEnergy.ccs_list in self.get_data_in():
            ccs_list = self.get_sosdisc_inputs(GlossaryEnergy.ccs_list)
            self.update_default_ccs_list()
            if ccs_list is not None:
                for ccs_name in ccs_list:
                    dynamic_inputs[f'{ccs_name}.{GlossaryEnergy.EnergyConsumptionValue}'] = {
                        'type': 'dataframe', 'unit': 'PWh', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                        'namespace': GlossaryEnergy.NS_CCS,
                        "dynamic_dataframe_columns": True}
                    dynamic_inputs[f'{ccs_name}.{GlossaryEnergy.EnergyConsumptionWithoutRatioValue}'] = {
                        'type': 'dataframe', 'unit': 'PWh', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                        'namespace': GlossaryEnergy.NS_CCS,
                        "dynamic_dataframe_columns": True}
                    dynamic_inputs[f'{ccs_name}.{GlossaryEnergy.EnergyProductionValue}'] = {
                        'type': 'dataframe', 'unit': 'PWh', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                        'namespace': GlossaryEnergy.NS_CCS,
                        'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                 GlossaryEnergy.carbon_capture: ('float', None, True),
                                                 'CO2 from Flue Gas (Mt)': ('float', None, True),
                                                 GlossaryEnergy.carbon_storage: ('float', None, True),
                                                 'heat.hightemperatureheat (TWh)': ('float', None, True),
                                                 'heat.mediumtemperatureheat (TWh)': ('float', None, True),
                                                 'heat.lowtemperatureheat (TWh)': ('float', None, True),
                                                }}

                    dynamic_inputs[f'{ccs_name}.{GlossaryEnergy.EnergyPricesValue}'] = {
                        'type': 'dataframe', 'unit': '$/MWh', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                        'namespace': GlossaryEnergy.NS_CCS,
                        'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),

                                                 GlossaryEnergy.carbon_capture: ('float', None, True),
                                                 'carbon_capture_wotaxes': ('float', None, True),
                                                 GlossaryEnergy.carbon_storage: ('float', None, True),
                                                 'carbon_storage_wotaxes': ('float', None, True),
                                                 'heat.hightemperatureheat (TWh)': ('float', None, True),
                                                 'heat.mediumtemperatureheat (TWh)': ('float', None, True),
                                                 'heat.lowtemperatureheat (TWh)': ('float', None, True),
                                                }}

                    dynamic_inputs[f'{ccs_name}.{GlossaryEnergy.LandUseRequiredValue}'] = {
                        'type': 'dataframe', 'unit': 'Gha', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                        'namespace': GlossaryEnergy.NS_CCS,
                        "dynamic_dataframe_columns": True}

        if GlossaryEnergy.YearStart in self.get_data_in() and GlossaryEnergy.YearEnd in self.get_data_in():
            year_start = self.get_sosdisc_inputs(GlossaryEnergy.YearStart)
            year_end = self.get_sosdisc_inputs(GlossaryEnergy.YearEnd)

            if year_start is not None and year_end is not None:
                dynamic_inputs['co2_for_food'] = {
                    'type': 'dataframe', 'unit': 'Mt', 'default': pd.DataFrame(
                        {GlossaryEnergy.Years: np.arange(year_start, year_end + 1), f'{CO2.name} for food (Mt)': 0.0}),
                    'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy',
                    'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                             'CO2_resource for food (Mt)': ('float', None, True), }
                }

        self.add_inputs(dynamic_inputs),
        self.add_outputs(dynamic_outputs)

    def update_default_ccs_list(self):
        '''
        Update the default value of technologies list with techno discipline below the ccs node and in possible values
        '''

        found_ccs = self.found_ccs_under_ccsmix()
        self.set_dynamic_default_values({GlossaryEnergy.ccs_list: found_ccs})

    def found_ccs_under_ccsmix(self):
        '''
        Set the default value of the ccs list and the ccs_list with discipline under the ccs_mix which are in possible values
        '''
        my_name = self.get_disc_full_name()
        possible_ccs = CCUS.ccs_list
        found_ccs_list = self.dm.get_discipline_names_with_starting_name(
            my_name)
        short_ccs_list = [name.split(
            f'{my_name}.')[-1] for name in found_ccs_list if f'{my_name}.' in name]

        possible_short_ccs_list = [
            techno for techno in short_ccs_list if techno in possible_ccs]

        return possible_short_ccs_list

    def run(self):
        # -- get inputs
        inputs_dict = self.get_sosdisc_inputs()
        # -- configure class with inputs
        #
        self.ccus_model.configure_parameters_update(inputs_dict)

        self.ccus_model.compute_CO2_emissions()
        self.ccus_model.compute_CCS_price()

        self.ccus_model.compute_carbon_storage_constraint()
        outputs_dict = {
            'co2_emissions_ccus': self.ccus_model.total_co2_emissions,
            'carbon_storage_by_invest': self.ccus_model.total_carbon_storage_by_invest,
            'co2_emissions_ccus_Gt': self.ccus_model.total_co2_emissions_Gt,
            'CCS_price': self.ccus_model.CCS_price,
            EnergyMix.CARBON_STORAGE_CONSTRAINT: self.ccus_model.carbon_storage_constraint,
        }

        

        self.store_sos_outputs_values(outputs_dict)

    def compute_sos_jacobian(self):

        inputs_dict = self.get_sosdisc_inputs()

        years = np.arange(inputs_dict[GlossaryEnergy.YearStart],
                          inputs_dict[GlossaryEnergy.YearEnd] + 1)
        ccs_list = inputs_dict[GlossaryEnergy.ccs_list]
        scaling_factor_energy_production = inputs_dict['scaling_factor_energy_production']
        scaling_factor_energy_consumption = inputs_dict['scaling_factor_energy_consumption']

        sub_production_dict, sub_consumption_dict = {}, {}
        for ccs in ccs_list:
            sub_production_dict[ccs] = inputs_dict[f'{ccs}.{GlossaryEnergy.EnergyProductionValue}'] * \
                                       scaling_factor_energy_production
            sub_consumption_dict[ccs] = inputs_dict[f'{ccs}.{GlossaryEnergy.EnergyConsumptionValue}'] * \
                                        scaling_factor_energy_consumption

        # -------------------------------#
        # ---Resource Demand gradients---#
        # -------------------------------#
        resource_list = EnergyMix.RESOURCE_LIST
        for ccs in ccs_list:
            for resource in inputs_dict[f'{ccs}.{GlossaryEnergy.EnergyConsumptionValue}']:
                if resource in resource_list:
                    self.set_partial_derivative_for_other_types(('All_Demand', resource), (
                        f'{ccs}.{GlossaryEnergy.EnergyConsumptionValue}', resource),
                                                                scaling_factor_energy_consumption * np.identity(
                                                                    len(years)))

        # --------------------------------#
        # -- New CO2 emissions gradients--#
        # --------------------------------#

        co2_emissions = self.get_sosdisc_outputs('co2_emissions_ccus')
        self.ccus_model.configure_parameters_update(inputs_dict)
        dtot_co2_emissions = self.ccus_model.compute_grad_CO2_emissions(co2_emissions)

        for key, value in dtot_co2_emissions.items():
            co2_emission_column = key.split(' vs ')[0]

            energy_prod_info = key.split(' vs ')[1]
            energy = energy_prod_info.split('#')[0]
            last_part_key = energy_prod_info.split('#')[1]
            if co2_emission_column in co2_emissions.columns and energy in ccs_list:

                if last_part_key == 'prod':
                    self.set_partial_derivative_for_other_types(
                        ('co2_emissions_ccus', co2_emission_column),
                        (f'{energy}.{GlossaryEnergy.EnergyProductionValue}', energy),
                        np.identity(len(years)) * scaling_factor_energy_production * value)
                elif last_part_key == 'cons':
                    for energy_df in ccs_list:
                        list_columnsenergycons = list(
                            inputs_dict[f'{energy_df}.{GlossaryEnergy.EnergyConsumptionValue}'].columns)
                        if f'{energy} (TWh)' in list_columnsenergycons:
                            self.set_partial_derivative_for_other_types(
                                ('co2_emissions_ccus', co2_emission_column),
                                (f'{energy_df}.{GlossaryEnergy.EnergyConsumptionValue}', f'{energy} (TWh)'),
                                np.identity(len(years)) * scaling_factor_energy_consumption * value)
                elif last_part_key == 'co2_per_use':
                    self.set_partial_derivative_for_other_types(
                        ('co2_emissions_ccus', co2_emission_column), (f'{energy}.CO2_per_use', 'CO2_per_use'),
                        np.identity(len(years)) * value)

                else:
                    very_last_part_key = energy_prod_info.split('#')[2]

                    if very_last_part_key == 'prod':
                        self.set_partial_derivative_for_other_types(
                            ('co2_emissions_ccus', co2_emission_column),
                            (f'{energy}.{GlossaryEnergy.EnergyProductionValue}', last_part_key),
                            np.identity(len(years)) * scaling_factor_energy_production * value)
                    elif very_last_part_key == 'cons':
                        self.set_partial_derivative_for_other_types(
                            ('co2_emissions_ccus', co2_emission_column),
                            (f'{energy}.{GlossaryEnergy.EnergyConsumptionValue}', last_part_key),
                            np.identity(len(years)) * scaling_factor_energy_production * value)

            '''
                CO2 emissions Gt
            '''
            if co2_emission_column == f'{CarbonStorage.name} Limited by capture (Mt)':
                co2_emission_column_upd = co2_emission_column.replace(
                    '(Mt)', '(Gt)')
                if last_part_key == 'prod':
                    self.set_partial_derivative_for_other_types(
                        ('co2_emissions_ccus_Gt', co2_emission_column_upd),
                        (f'{energy}.{GlossaryEnergy.EnergyProductionValue}', energy),
                        np.identity(len(years)) * scaling_factor_energy_production * value / 1.0e3)
                elif last_part_key == 'cons':
                    for energy_df in ccs_list:
                        list_columnsenergycons = list(
                            inputs_dict[f'{energy_df}.{GlossaryEnergy.EnergyConsumptionValue}'].columns)
                        if f'{energy} (TWh)' in list_columnsenergycons:
                            self.set_partial_derivative_for_other_types(
                                ('co2_emissions_ccus_Gt', co2_emission_column_upd),
                                (f'{energy_df}.{GlossaryEnergy.EnergyConsumptionValue}', f'{energy} (TWh)'),
                                np.identity(len(years)) * scaling_factor_energy_consumption * value / 1.0e3)
                elif last_part_key == 'co2_per_use':
                    self.set_partial_derivative_for_other_types(
                        ('co2_emissions_ccus_Gt', co2_emission_column_upd), (f'{energy}.CO2_per_use', 'CO2_per_use'),
                        np.identity(len(years)) * value / 1.0e3)
                elif energy_prod_info.startswith(f'{CO2.name} for food (Mt)'):
                    self.set_partial_derivative_for_other_types(
                        ('co2_emissions_ccus_Gt', co2_emission_column_upd),
                        ('co2_for_food', f'{CO2.name} for food (Mt)'), np.identity(len(years)) * value / 1.0e3)

                elif energy_prod_info.startswith(f'{CarbonCapture.name} from energy mix (Mt)'):
                    self.set_partial_derivative_for_other_types(
                        ('co2_emissions_ccus_Gt', co2_emission_column_upd),
                        ('carbon_capture_from_energy_mix', f'{CarbonCapture.name} from energy mix (Gt)'),
                        np.identity(len(years)) * value)

                elif energy_prod_info.startswith(f'{CarbonCapture.name} needed by energy mix (Mt)'):
                    self.set_partial_derivative_for_other_types(
                        ('co2_emissions_ccus_Gt', co2_emission_column_upd),
                        ('co2_emissions_needed_by_energy_mix', f'{CarbonCapture.name} needed by energy mix (Gt)'),
                        np.identity(len(years)) * value)

                else:
                    very_last_part_key = energy_prod_info.split('#')[2]
                    if very_last_part_key == 'prod':

                        self.set_partial_derivative_for_other_types(
                            ('co2_emissions_ccus_Gt', co2_emission_column_upd),
                            (f'{energy}.{GlossaryEnergy.EnergyProductionValue}', last_part_key),
                            np.identity(len(years)) * scaling_factor_energy_production * value / 1.0e3)
                    elif very_last_part_key == 'cons':
                        self.set_partial_derivative_for_other_types(
                            ('co2_emissions_ccus_Gt', co2_emission_column_upd),
                            (f'{energy}.{GlossaryEnergy.EnergyConsumptionValue}', last_part_key),
                            np.identity(len(years)) * scaling_factor_energy_production * value / 1.0e3)

                '''
                    Carbon storage constraint
                '''
            elif co2_emission_column == 'Carbon storage constraint':

                if last_part_key == 'prod' and energy in ccs_list:
                    self.set_partial_derivative_for_other_types(
                        (EnergyMix.CARBON_STORAGE_CONSTRAINT,),
                        (f'{energy}.{GlossaryEnergy.EnergyProductionValue}', energy),
                        scaling_factor_energy_production * value)
                elif last_part_key == 'cons' and energy in ccs_list:
                    for energy_df in ccs_list:
                        list_columnsenergycons = list(
                            inputs_dict[f'{energy_df}.{GlossaryEnergy.EnergyConsumptionValue}'].columns)
                        if f'{energy} (TWh)' in list_columnsenergycons:
                            self.set_partial_derivative_for_other_types(
                                (EnergyMix.CARBON_STORAGE_CONSTRAINT,),
                                (f'{energy_df}.{GlossaryEnergy.EnergyConsumptionValue}', f'{energy} (TWh)'),
                                scaling_factor_energy_consumption * value)
                elif last_part_key == 'co2_per_use':
                    self.set_partial_derivative_for_other_types(
                        (EnergyMix.CARBON_STORAGE_CONSTRAINT,), (f'{energy}.CO2_per_use', 'CO2_per_use'), value)
                elif energy_prod_info.startswith(f'{CO2.name} for food (Mt)'):
                    self.set_partial_derivative_for_other_types(
                        (EnergyMix.CARBON_STORAGE_CONSTRAINT,), ('co2_for_food', f'{CO2.name} for food (Mt)'), value)

                elif energy_prod_info.startswith(f'{CarbonCapture.name} from energy mix (Mt)'):
                    self.set_partial_derivative_for_other_types(
                        (EnergyMix.CARBON_STORAGE_CONSTRAINT,),
                        ('carbon_capture_from_energy_mix', f'{CarbonCapture.name} from energy mix (Gt)'), value * 1e3)

                elif energy_prod_info.startswith(f'{CarbonCapture.name} needed by energy mix (Mt)'):
                    self.set_partial_derivative_for_other_types(
                        (EnergyMix.CARBON_STORAGE_CONSTRAINT,),
                        ('co2_emissions_needed_by_energy_mix', f'{CarbonCapture.name} needed by energy mix (Gt)'),
                        value * 1e3)

                else:
                    very_last_part_key = energy_prod_info.split('#')[2]
                    if very_last_part_key == 'prod':
                        self.set_partial_derivative_for_other_types(
                            (EnergyMix.CARBON_STORAGE_CONSTRAINT,),
                            (f'{energy}.{GlossaryEnergy.EnergyProductionValue}', last_part_key),
                            scaling_factor_energy_production * value)
                    elif very_last_part_key == 'cons':
                        self.set_partial_derivative_for_other_types(
                            (EnergyMix.CARBON_STORAGE_CONSTRAINT,),
                            (f'{energy}.{GlossaryEnergy.EnergyConsumptionValue}', last_part_key),
                            scaling_factor_energy_production * value)

        if CarbonCapture.name in ccs_list:
            self.set_partial_derivative_for_other_types(
                ('CCS_price', 'ccs_price_per_tCO2'),
                (f'{CarbonCapture.name}.{GlossaryEnergy.EnergyPricesValue}', CarbonCapture.name),
                np.identity(len(years)))
        if CarbonStorage.name in ccs_list:
            self.set_partial_derivative_for_other_types(
                ('CCS_price', 'ccs_price_per_tCO2'),
                (f'{CarbonStorage.name}.{GlossaryEnergy.EnergyPricesValue}', CarbonStorage.name),
                np.identity(len(years)))
        if CarbonUtilization.name in ccs_list:
            self.set_partial_derivative_for_other_types(
                ('CCS_price', 'ccs_price_per_tCO2'),
                (f'{CarbonUtilization.name}.{GlossaryEnergy.EnergyPricesValue}', CarbonUtilization.name),
                np.identity(len(years)))

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

        years = list(ccs_prices[GlossaryEnergy.Years].values)

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
        carbon_capture_from_energy_mix = self.get_sosdisc_inputs(
            'carbon_capture_from_energy_mix')
        co2_emissions_needed_by_energy_mix = self.get_sosdisc_inputs(
            'co2_emissions_needed_by_energy_mix')
        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'CO2 emissions (Gt)',
                                             chart_name=chart_name)

        x_serie_1 = co2_emissions[GlossaryEnergy.Years].values.tolist()

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'{CarbonCapture.name} (Mt) from CC technos'].values / 1.0e3).tolist(),
            'CO2 captured from CC technos')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            carbon_capture_from_energy_mix[f'{CarbonCapture.name} from energy mix (Gt)'].values.tolist(),
            f'CO2 captured from energy mix')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (-co2_emissions_needed_by_energy_mix[f'{CarbonCapture.name} needed by energy mix (Gt)'].values).tolist(),
            f'{CarbonCapture.name} used by energy mix')
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
        carbon_storage_by_invest = self.get_sosdisc_outputs('carbon_storage_by_invest')
        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'CO2 emissions (Gt)',
                                             chart_name=chart_name)

        x_serie_1 = co2_emissions[GlossaryEnergy.Years].values.tolist()
        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'{CarbonCapture.name} to be stored (Mt)'].values / 1.0e3).tolist(), f'CO2 to store')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (carbon_storage_by_invest / 1.0e3).tolist(), f'CO2 storage by invest')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'{CarbonStorage.name} Limited by capture (Mt)'].values / 1.0e3).tolist(),
            f'CO2 storage limited by CO2 to store')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'{CarbonUtilization.name} to be stored (Mt)'].values / 1.0e3).tolist(), f'CO2 to store')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (carbon_storage_by_invest / 1.0e3).tolist(), f'CO2 storage by invest')
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
            (co2_emissions[f'Total {CarbonCapture.flue_gas_name} (Mt)'].values / 1.0e3).tolist(),
            'Flue gas from plants')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1, (co2_emissions[f'{CarbonCapture.name} from energy mix (Mt)'].values / 1.0e3).tolist(),
            'Carbon capture from energy mix (FT or Sabatier)')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'{CO2.name} from energy mix (Mt)'].values / 1.0e3).tolist(),
            'CO2 from energy mix (machinery fuels)')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions['CO2 emissions sources'].values / 1.0e3).tolist(), 'Total sources')
        new_chart.add_series(serie)

        return new_chart

    def get_chart_carbon_storage_constraint(self):

        co2_emissions = self.get_sosdisc_outputs('co2_emissions_ccus_Gt')

        carbon_storage_limit = self.get_sosdisc_inputs('carbonstorage_limit')
        years = list(co2_emissions[GlossaryEnergy.Years])

        chart_name = 'Cumulated carbon storage (Gt) vs years'

        year_start = years[0]
        year_end = years[len(years) - 1]

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Cumulated carbon storage (Gt)',
                                             chart_name=chart_name)

        visible_line = True

        new_series = InstanciatedSeries(
            years, list(co2_emissions[f'{CarbonStorage.name} Limited by capture (Gt)'].cumsum().values),
            'cumulative sum of carbon capture (Gt)', 'lines', visible_line)

        new_chart.series.append(new_series)

        # Rockstrom Limit

        ordonate_data = [carbon_storage_limit / 1e3] * int(len(years) / 5)
        abscisse_data = np.linspace(
            year_start, year_end, int(len(years) / 5))
        new_series = InstanciatedSeries(
            abscisse_data.tolist(), ordonate_data, 'Carbon storage limit (Gt)', 'scatter')

        new_chart.series.append(new_series)

        return new_chart
