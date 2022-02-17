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
from energy_models.core.consumption_CO2_emissions.consumption_CO2_emissions import ConsumptionCO2Emissions
from sos_trades_core.execution_engine.sos_discipline import SoSDiscipline
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2

import numpy as np


class ConsumptionCO2EmissionsDiscipline(SoSDiscipline):

    DESC_IN = {
        'year_start': {'type': 'int', 'default': 2020, 'unit': '[-]', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'year_end': {'type': 'int', 'default': 2050, 'unit': '[-]', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'energy_list': {'type': 'string_list', 'possible_values': EnergyMix.energy_list,
                        'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_study',
                        'editable': False, 'structuring': True},
        'scaling_factor_energy_production': {'type': 'float', 'default': 1e3, 'user_level': 2, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'scaling_factor_energy_consumption': {'type': 'float', 'default': 1e3, 'user_level': 2, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'energy_production_detailed': {'type': 'dataframe', 'unit': 'TWh'},
    }

    DESC_OUT = {
        'CO2_emissions_by_use_sources': {'type': 'dataframe', 'unit': 'Mt',
                                         'visibility': SoSDiscipline.SHARED_VISIBILITY,
                                         'namespace': 'ns_emissions'},
        'CO2_emissions_by_use_sinks':  {'type': 'dataframe', 'unit': 'Mt',
                                        'visibility': SoSDiscipline.SHARED_VISIBILITY,
                                        'namespace': 'ns_emissions'},
    }

    model_name = ConsumptionCO2Emissions.name

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.model = ConsumptionCO2Emissions(self.model_name)
        self.model.configure_parameters(inputs_dict)

    def setup_sos_disciplines(self):

        dynamic_inputs = {}
        dynamic_outputs = {}

        if 'energy_list' in self._data_in:
            energy_list = self.get_sosdisc_inputs('energy_list')
            if energy_list is not None:
                for energy in energy_list:
                    dynamic_inputs[f'{energy}.CO2_per_use'] = {
                        'type': 'dataframe', 'unit': 'kgCO2/kWh',
                        'visibility': SoSDiscipline.SHARED_VISIBILITY,
                        'namespace': 'ns_emissions'}
                    dynamic_inputs[f'{energy}.energy_consumption'] = {
                        'type': 'dataframe', 'unit': 'PWh'}
                    dynamic_inputs[f'{energy}.energy_production'] = {
                        'type': 'dataframe', 'unit': 'PWh'}

        self.add_inputs(dynamic_inputs)
        self.add_outputs(dynamic_outputs)

    def run(self):
        #-- get inputs
        inputs_dict = self.get_sosdisc_inputs()

        #-- configure class with inputs

        self.model.configure_parameters_update(inputs_dict)
        CO2_sources, CO2_sinks = self.model.compute_CO2_emissions()

        outputs_dict = {
            'CO2_emissions_by_use_sources': CO2_sources,
            'CO2_emissions_by_use_sinks': CO2_sinks,
        }
        self.store_sos_outputs_values(outputs_dict)

    def compute_sos_jacobian(self):
        inputs_dict = self.get_sosdisc_inputs()
        outputs_dict = self.get_sosdisc_outputs()
        years = np.arange(inputs_dict['year_start'],
                          inputs_dict['year_end'] + 1)
        energy_list = inputs_dict['energy_list']
        scaling_factor_energy_production = inputs_dict['scaling_factor_energy_production']
        scaling_factor_energy_consumption = inputs_dict['scaling_factor_energy_consumption']
        CO2_emissions_by_use_sources = outputs_dict['CO2_emissions_by_use_sources']
        CO2_emissions_by_use_sinks = outputs_dict['CO2_emissions_by_use_sinks']
        energy_production_detailed = self.get_sosdisc_inputs(
            'energy_production_detailed')

        #------------------------------------#
        #-- CO2 emissions sources gradients--#
        #------------------------------------#
        dtot_co2_emissions_sources = self.model.compute_grad_CO2_emissions_sources(
            energy_production_detailed)

        for key, value in dtot_co2_emissions_sources.items():
            co2_emission_column = key.split(' vs ')[0]
            energy_prod_info = key.split(' vs ')[1]
            energy = energy_prod_info.split('#')[0]
            last_part_key = energy_prod_info.split('#')[1]
            if co2_emission_column in CO2_emissions_by_use_sources.columns and energy in energy_list:

                if last_part_key == 'prod':
                    self.set_partial_derivative_for_other_types(
                        ('CO2_emissions_by_use_sources',
                         co2_emission_column), (f'{energy}.energy_production', energy),
                        np.identity(len(years)) * scaling_factor_energy_production * value)
                elif last_part_key == 'cons':
                    for energy_df in energy_list:
                        list_columnsenergycons = list(
                            inputs_dict[f'{energy_df}.energy_consumption'].columns)
                        if f'{energy} (TWh)' in list_columnsenergycons:
                            self.set_partial_derivative_for_other_types(
                                ('CO2_emissions_by_use_sources', co2_emission_column), (
                                    f'{energy_df}.energy_consumption', f'{energy} (TWh)'),
                                np.identity(len(years)) * scaling_factor_energy_consumption * value)
                elif last_part_key == 'co2_per_use':
                    self.set_partial_derivative_for_other_types(
                        ('CO2_emissions_by_use_sources',
                         co2_emission_column), (f'{energy}.CO2_per_use', 'CO2_per_use'),
                        np.identity(len(years)) * value)

                else:
                    very_last_part_key = energy_prod_info.split('#')[2]
                    if very_last_part_key == 'prod':
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_by_use_sources', co2_emission_column), (
                                f'{energy}.energy_production', last_part_key),
                            np.identity(len(years)) * scaling_factor_energy_production * value)
                    elif very_last_part_key == 'cons':
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_by_use_sources', co2_emission_column), (
                                f'{energy}.energy_consumption', last_part_key),
                            np.identity(len(years)) * scaling_factor_energy_production * value)

        #------------------------------------#
        #-- CO2 emissions sinks gradients--#
        #------------------------------------#
        dtot_co2_emissions_sinks = self.model.compute_grad_CO2_emissions_sinks(
            energy_production_detailed)

        for key, value in dtot_co2_emissions_sinks.items():
            co2_emission_column = key.split(' vs ')[0]
            energy_prod_info = key.split(' vs ')[1]
            energy = energy_prod_info.split('#')[0]
            last_part_key = energy_prod_info.split('#')[1]
            if co2_emission_column in CO2_emissions_by_use_sinks.columns and energy in energy_list:

                if last_part_key == 'prod':
                    self.set_partial_derivative_for_other_types(
                        ('CO2_emissions_by_use_sinks',
                         co2_emission_column), (f'{energy}.energy_production', energy),
                        np.identity(len(years)) * scaling_factor_energy_production * value)
                elif last_part_key == 'cons':
                    for energy_df in energy_list:
                        list_columnsenergycons = list(
                            inputs_dict[f'{energy_df}.energy_consumption'].columns)
                        if f'{energy} (TWh)' in list_columnsenergycons:
                            self.set_partial_derivative_for_other_types(
                                ('CO2_emissions_by_use_sinks', co2_emission_column), (
                                    f'{energy_df}.energy_consumption', f'{energy} (TWh)'),
                                np.identity(len(years)) * scaling_factor_energy_consumption * value)
                elif last_part_key == 'co2_per_use':
                    self.set_partial_derivative_for_other_types(
                        ('CO2_emissions_by_use_sinks',
                         co2_emission_column), (f'{energy}.CO2_per_use', 'CO2_per_use'),
                        np.identity(len(years)) * value)

                else:
                    very_last_part_key = energy_prod_info.split('#')[2]
                    if very_last_part_key == 'prod':
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_by_use_sinks', co2_emission_column), (
                                f'{energy}.energy_production', last_part_key),
                            np.identity(len(years)) * scaling_factor_energy_production * value)
                    elif very_last_part_key == 'cons':
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_by_use_sinks', co2_emission_column), (
                                f'{energy}.energy_consumption', last_part_key),
                            np.identity(len(years)) * scaling_factor_energy_production * value)
