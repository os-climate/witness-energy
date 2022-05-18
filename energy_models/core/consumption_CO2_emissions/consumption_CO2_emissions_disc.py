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
from climateeconomics.sos_wrapping.sos_wrapping_agriculture.agriculture.agriculture_mix_disc import AgricultureMixDiscipline
from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
from sos_trades_core.execution_engine.sos_discipline import SoSDiscipline
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2

from sos_trades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sos_trades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart

import numpy as np
from climateeconomics.core.core_witness.climateeco_discipline import ClimateEcoDiscipline


class ConsumptionCO2EmissionsDiscipline(SoSDiscipline):

    # ontology information
    _ontology_data = {
        'label': 'CO2 emissions consumption Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-cloud fa-fw',
        'version': '',
    }

    DESC_IN = {
        'year_start': ClimateEcoDiscipline.YEAR_START_DESC_IN,
        'year_end': ClimateEcoDiscipline.YEAR_END_DESC_IN,
        'energy_list': {'type': 'string_list',  'possible_values': EnergyMix.energy_list,
                        'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_study',
                        'editable': False, 'structuring': True},
        'scaling_factor_energy_production': {'type': 'float', 'default': 1e3, 'unit': '-', 'user_level': 2, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'scaling_factor_energy_consumption': {'type': 'float', 'default': 1e3, 'unit': '-', 'user_level': 2, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'energy_production_detailed': {'type': 'dataframe', 'unit': 'TWh', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy'},
        # WIP is_dev to remove once its validated on dev processes
        'is_dev': {'type': 'bool', 'default': False, 'user_level': 2, 'structuring': True, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'}
    }

    DESC_OUT = {
        'CO2_emissions_by_use_sources': {'type': 'dataframe', 'unit': 'Gt',
                                         'visibility': SoSDiscipline.SHARED_VISIBILITY,
                                         'namespace': 'ns_ccs'},
        'CO2_emissions_by_use_sinks':  {'type': 'dataframe', 'unit': 'Gt',
                                        'visibility': SoSDiscipline.SHARED_VISIBILITY,
                                        'namespace': 'ns_ccs'},
    }

    model_name = ConsumptionCO2Emissions.name

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.model = ConsumptionCO2Emissions(self.model_name)
        self.model.configure_parameters(inputs_dict)

    def setup_sos_disciplines(self):

        dynamic_inputs = {}
        dynamic_outputs = {}
        if 'is_dev' in self._data_in:
            is_dev = self.get_sosdisc_inputs('is_dev')

        if 'energy_list' in self._data_in:
            energy_list = self.get_sosdisc_inputs('energy_list')
            if energy_list is not None:
                for energy in energy_list:
                    if energy == BiomassDry.name and is_dev == True:
                        dynamic_inputs[f'{AgricultureMixDiscipline.name}.CO2_per_use'] = {
                            'type': 'dataframe', 'unit': 'kg/kWh', 'namespace': 'ns_witness', 'visibility': SoSDiscipline.SHARED_VISIBILITY}
                        dynamic_inputs[f'{AgricultureMixDiscipline.name}.energy_consumption'] = {
                            'type': 'dataframe', 'unit': 'PWh', 'namespace': 'ns_witness', 'visibility': SoSDiscipline.SHARED_VISIBILITY}
                        dynamic_inputs[f'{AgricultureMixDiscipline.name}.energy_production'] = {
                            'type': 'dataframe', 'unit': 'PWh', 'namespace': 'ns_witness', 'visibility': SoSDiscipline.SHARED_VISIBILITY}
                    else:
                        dynamic_inputs[f'{energy}.CO2_per_use'] = {
                            'type': 'dataframe', 'unit': 'kg/kWh',
                            'visibility': SoSDiscipline.SHARED_VISIBILITY,
                            'namespace': 'ns_energy'}
                        dynamic_inputs[f'{energy}.energy_consumption'] = {
                            'type': 'dataframe', 'unit': 'PWh',
                            'visibility': SoSDiscipline.SHARED_VISIBILITY,
                            'namespace': 'ns_energy'}
                        dynamic_inputs[f'{energy}.energy_production'] = {
                            'type': 'dataframe', 'unit': 'PWh',
                            'visibility': SoSDiscipline.SHARED_VISIBILITY,
                            'namespace': 'ns_energy'}

        self.add_inputs(dynamic_inputs)
        self.add_outputs(dynamic_outputs)

    def run(self):
        #-- get inputs
        inputs_dict_orig = self.get_sosdisc_inputs()
        #-- configure class with inputs
        #-- biomass dry values are coming from agriculture mix discipline, but needs to be used in model with biomass dry name
        inputs_dict = {}
        inputs_dict.update(inputs_dict_orig)
        energy_list = self.get_sosdisc_inputs('energy_list')
        if inputs_dict['is_dev'] and 'biomass_dry' in energy_list:
            inputs_dict[f'{BiomassDry.name}.energy_consumption'] = inputs_dict_orig.pop(
                f'{AgricultureMixDiscipline.name}.energy_consumption')
            inputs_dict[f'{BiomassDry.name}.energy_production'] = inputs_dict_orig.pop(
                f'{AgricultureMixDiscipline.name}.energy_production')
            inputs_dict[f'{BiomassDry.name}.CO2_per_use'] = inputs_dict_orig.pop(
                f'{AgricultureMixDiscipline.name}.CO2_per_use')
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
        is_dev = inputs_dict['is_dev']
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
                ns_energy = energy
                if energy == BiomassDry.name and is_dev:
                    ns_energy = AgricultureMixDiscipline.name
                if last_part_key == 'prod':
                    if 'Total CO2 by use' in co2_emission_column:
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_by_use_sources',
                             co2_emission_column), ('energy_production_detailed', f'production {energy} (TWh)'),
                            np.identity(len(years)) * value / 1e3)
                    else:
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_by_use_sources',
                             co2_emission_column), (f'{ns_energy}.energy_production', energy),
                            np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)
                elif last_part_key == 'cons':
                    for energy_df in energy_list:
                        list_columnsenergycons = list(
                            inputs_dict[f'{energy_df}.energy_consumption'].columns)
                        if f'{energy} (TWh)' in list_columnsenergycons:
                            self.set_partial_derivative_for_other_types(
                                ('CO2_emissions_by_use_sources', co2_emission_column), (
                                    f'{energy_df}.energy_consumption', f'{energy} (TWh)'),
                                np.identity(len(years)) * scaling_factor_energy_consumption * value / 1e3)
                elif last_part_key == 'co2_per_use':
                    self.set_partial_derivative_for_other_types(
                        ('CO2_emissions_by_use_sources',
                         co2_emission_column), (f'{ns_energy}.CO2_per_use', 'CO2_per_use'),
                        np.identity(len(years)) * value / 1e3)

                else:
                    very_last_part_key = energy_prod_info.split('#')[2]
                    if very_last_part_key == 'prod':
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_by_use_sources', co2_emission_column), (
                                f'{ns_energy}.energy_production', last_part_key),
                            np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)
                    elif very_last_part_key == 'cons':
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_by_use_sources', co2_emission_column), (
                                f'{ns_energy}.energy_consumption', last_part_key),
                            np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)

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
                ns_energy = energy
                if energy == BiomassDry.name and is_dev:
                    ns_energy = AgricultureMixDiscipline.name
                if last_part_key == 'prod':
                    self.set_partial_derivative_for_other_types(
                        ('CO2_emissions_by_use_sinks',
                         co2_emission_column), (f'{ns_energy}.energy_production', energy),
                        np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)
                elif last_part_key == 'cons':
                    for energy_df in energy_list:
                        list_columnsenergycons = list(
                            inputs_dict[f'{energy_df}.energy_consumption'].columns)
                        if f'{energy} (TWh)' in list_columnsenergycons:
                            self.set_partial_derivative_for_other_types(
                                ('CO2_emissions_by_use_sinks', co2_emission_column), (
                                    f'{energy_df}.energy_consumption', f'{energy} (TWh)'),
                                np.identity(len(years)) * scaling_factor_energy_consumption * value / 1e3)
                elif last_part_key == 'co2_per_use':
                    self.set_partial_derivative_for_other_types(
                        ('CO2_emissions_by_use_sinks',
                         co2_emission_column), (f'{ns_energy}.CO2_per_use', 'CO2_per_use'),
                        np.identity(len(years)) * value / 1e3)

                else:
                    very_last_part_key = energy_prod_info.split('#')[2]
                    if very_last_part_key == 'prod':
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_by_use_sinks', co2_emission_column), (
                                f'{ns_energy}.energy_production', last_part_key),
                            np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)
                    elif very_last_part_key == 'cons':
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_by_use_sinks', co2_emission_column), (
                                f'{ns_energy}.energy_consumption', last_part_key),
                            np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['CO2 sources', 'CO2 sinks']

        chart_filters.append(ChartFilter(
            'Charts', chart_list, chart_list, 'charts'))

        return chart_filters

    def get_post_processing_list(self, filters=None):

        # For the outputs, making a graph for block fuel vs range and blocktime vs
        # range

        instanciated_charts = []
        charts = []
        if filters is not None:
            for chart_filter in filters:
                charts = chart_filter.selected_values

        if 'CO2 sources' in charts:

            new_chart = self.get_chart_CO2_sources()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'CO2 sinks' in charts:
            new_chart = self.get_chart_CO2_sinks()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_chart_CO2_sources(self):
        CO2_emissions_by_use_sources = self.get_sosdisc_outputs(
            'CO2_emissions_by_use_sources')

        chart_name = f'CO2 emissions by consumption - Sources'
        new_chart = TwoAxesInstanciatedChart(
            'years', 'CO2 emissions (Gt)', chart_name=chart_name)

        for col in CO2_emissions_by_use_sources:
            if col != 'years':
                new_serie = InstanciatedSeries(list(CO2_emissions_by_use_sources['years'].values), list(CO2_emissions_by_use_sources[col].values),
                                               col, 'lines')

                new_chart.series.append(new_serie)

        return new_chart

    def get_chart_CO2_sinks(self):
        CO2_emissions_by_use_sinks = self.get_sosdisc_outputs(
            'CO2_emissions_by_use_sinks')

        chart_name = f'CO2 emissions by consumption - Sinks'
        new_chart = TwoAxesInstanciatedChart(
            'years', 'CO2 emissions (Gt)', chart_name=chart_name)

        for col in CO2_emissions_by_use_sinks:
            if col != 'years':
                new_serie = InstanciatedSeries(list(CO2_emissions_by_use_sinks['years'].values), list(CO2_emissions_by_use_sinks[col].values),
                                               col, 'lines')

                new_chart.series.append(new_serie)

        return new_chart
