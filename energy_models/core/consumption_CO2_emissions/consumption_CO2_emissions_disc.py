'''
Copyright 2022 Airbus SAS
Modifications on 2023/04/21-2023/11/16 Copyright 2023 Capgemini

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

from climateeconomics.core.core_witness.climateeco_discipline import (
    ClimateEcoDiscipline,
)
from climateeconomics.sos_wrapping.sos_wrapping_agriculture.agriculture.agriculture_mix_disc import (
    AgricultureMixDiscipline,
)
from energy_models.core.ccus.ccus import CCUS
from energy_models.core.consumption_CO2_emissions.consumption_CO2_emissions import (
    ConsumptionCO2Emissions,
)
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
from energy_models.glossaryenergy import GlossaryEnergy
from sostrades_core.execution_engine.sos_wrapp import SoSWrapp
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import (
    InstanciatedSeries,
    TwoAxesInstanciatedChart,
)


class ConsumptionCO2EmissionsDiscipline(SoSWrapp):
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
        GlossaryEnergy.YearStart: ClimateEcoDiscipline.YEAR_START_DESC_IN,
        GlossaryEnergy.YearEnd: GlossaryEnergy.YearEndVar,
        GlossaryEnergy.energy_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                                     'possible_values': EnergyMix.energy_list,
                                     'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy_study',
                                     'editable': False, 'structuring': True},
        GlossaryEnergy.ccs_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                                  'possible_values': CCUS.ccs_list,
                                  'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy_study',
                                  'editable': False,
                                  'structuring': True},
        'scaling_factor_energy_production': {'type': 'float', 'default': 1e3, 'unit': '-', 'user_level': 2,
                                             'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'scaling_factor_energy_consumption': {'type': 'float', 'default': 1e3, 'unit': '-', 'user_level': 2,
                                              'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        GlossaryEnergy.EnergyProductionDetailedValue: {'type': 'dataframe', 'unit': 'TWh',
                                                       'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                       'namespace': 'ns_energy',
                                                       'dataframe_descriptor': {
                                                           GlossaryEnergy.Years: ('float', None, True),
                                                           f'production {GlossaryEnergy.methane} (TWh)': (
                                                               'float', None, True),
                                                           f'production {GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen} (TWh)': (
                                                               'float', None, True),
                                                           f'production {GlossaryEnergy.biogas} (TWh)': (
                                                               'float', None, True),
                                                           f'production {GlossaryEnergy.syngas} (TWh)': (
                                                               'float', None, True),
                                                           f'production {GlossaryEnergy.fuel}.{GlossaryEnergy.liquid_fuel} (TWh)': (
                                                               'float', None, True),
                                                           f'production {GlossaryEnergy.fuel}.{GlossaryEnergy.hydrotreated_oil_fuel} (TWh)': (
                                                               'float', None, True),
                                                           f'production {GlossaryEnergy.solid_fuel} (TWh)': (
                                                               'float', None, True),
                                                           f'production {GlossaryEnergy.biomass_dry} (TWh)': (
                                                               'float', None, True),
                                                           f'production {GlossaryEnergy.electricity} (TWh)': (
                                                               'float', None, True),
                                                           f'production {GlossaryEnergy.fuel}.{GlossaryEnergy.biodiesel} (TWh)': (
                                                               'float', None, True),
                                                           f'production {GlossaryEnergy.fuel}.{GlossaryEnergy.ethanol} (TWh)': (
                                                               'float', None, True),
                                                           f'production {GlossaryEnergy.hydrogen}.{GlossaryEnergy.liquid_hydrogen} (TWh)': (
                                                               'float', None, True),
                                                           f'production {GlossaryEnergy.carbon_capture} (Mt)': (
                                                               'float', None, True),
                                                           f'production {GlossaryEnergy.carbon_storage} (Mt)': (
                                                               'float', None, True),
                                                           'Total production': ('float', None, True),
                                                           'Total production (uncut)': ('float', None, True), }
                                                       },
    }

    DESC_OUT = {
        'CO2_emissions_by_use_sources': {'type': 'dataframe', 'unit': 'Gt',
                                         'visibility': SoSWrapp.SHARED_VISIBILITY,
                                         'namespace': GlossaryEnergy.NS_CCS},
        'CO2_emissions_by_use_sinks': {'type': 'dataframe', 'unit': 'Gt',
                                       'visibility': SoSWrapp.SHARED_VISIBILITY,
                                       'namespace': GlossaryEnergy.NS_CCS},
    }

    model_name = ConsumptionCO2Emissions.name

    def __init__(self, sos_name, logger: logging.Logger):
        super().__init__(sos_name, logger)
        self.model = None

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.model = ConsumptionCO2Emissions(self.model_name)
        self.model.configure_parameters(inputs_dict)

    def setup_sos_disciplines(self):

        dynamic_inputs = {}
        dynamic_outputs = {}

        if GlossaryEnergy.energy_list in self.get_data_in():
            energy_list = self.get_sosdisc_inputs(GlossaryEnergy.energy_list)
            if energy_list is not None:
                for energy in energy_list:
                    if energy == BiomassDry.name:
                        co2_per_use_var = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.CO2PerUseDf)
                        co2_per_use_var.update({
                            'visbility': 'Shared', 'namespace': GlossaryEnergy.NS_WITNESS
                        })
                        dynamic_inputs[f'{AgricultureMixDiscipline.name}.{GlossaryEnergy.CO2PerUse}'] = co2_per_use_var
                        dynamic_inputs[f'{AgricultureMixDiscipline.name}.{GlossaryEnergy.EnergyConsumptionValue}'] = {
                            'type': 'dataframe', 'unit': 'PWh', 'namespace': GlossaryEnergy.NS_WITNESS,
                            'visibility': SoSWrapp.SHARED_VISIBILITY,
                            'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                     f'{GlossaryEnergy.electricity} (TWh)': ('float', None, True),
                                                     'CO2_resource (Mt)': ('float', None, True),
                                                     }}
                        dynamic_inputs[f'{AgricultureMixDiscipline.name}.{GlossaryEnergy.EnergyProductionValue}'] = {
                            'type': 'dataframe', 'unit': 'PWh', 'namespace': GlossaryEnergy.NS_WITNESS,
                            'visibility': SoSWrapp.SHARED_VISIBILITY,
                            'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                     GlossaryEnergy.biomass_dry: ('float', None, True),
                                                     'CO2_resource (Mt)': ('float', None, True), }}
                    else:
                        dynamic_inputs[f'{energy}.{GlossaryEnergy.CO2PerUse}'] = {
                            'type': 'dataframe', 'unit': 'kg/kWh',
                            'visibility': SoSWrapp.SHARED_VISIBILITY,
                            'namespace': 'ns_energy',
                            'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                     GlossaryEnergy.CO2PerUse: ('float', None, True), }}
                        dynamic_inputs[f'{energy}.{GlossaryEnergy.EnergyConsumptionValue}'] = {
                            'type': 'dataframe', 'unit': 'PWh',
                            'visibility': SoSWrapp.SHARED_VISIBILITY,
                            'namespace': 'ns_energy',
                            'dynamic_dataframe_columns': True}
                        dynamic_inputs[f'{energy}.{GlossaryEnergy.EnergyProductionValue}'] = {
                            'type': 'dataframe', 'unit': 'PWh',
                            'visibility': SoSWrapp.SHARED_VISIBILITY,
                            'namespace': 'ns_energy',
                            'dynamic_dataframe_columns': True}

        if GlossaryEnergy.ccs_list in self.get_data_in():
            ccs_list = self.get_sosdisc_inputs(GlossaryEnergy.ccs_list)
            if ccs_list is not None:
                for ccs in ccs_list:
                    dynamic_inputs[f'{ccs}.{GlossaryEnergy.EnergyProductionValue}'] = {
                        'type': 'dataframe', 'unit': 'PWh',
                        'visibility': SoSWrapp.SHARED_VISIBILITY,
                        'namespace': GlossaryEnergy.NS_CCS,
                        'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                 GlossaryEnergy.carbon_capture: ('float', None, True),
                                                 GlossaryEnergy.carbon_storage: ('float', None, True),
                                                 'CO2 from Flue Gas (Mt)': ('float', None, True),

                                                 }
                    }

        self.add_inputs(dynamic_inputs)
        self.add_outputs(dynamic_outputs)

    def run(self):
        # -- get inputs
        inputs_dict_orig = self.get_sosdisc_inputs()
        # -- configure class with inputs
        # -- biomass dry values are coming from agriculture mix discipline, but needs to be used in model with biomass dry name
        inputs_dict = {}
        inputs_dict.update(inputs_dict_orig)
        energy_list = self.get_sosdisc_inputs(GlossaryEnergy.energy_list)
        if GlossaryEnergy.biomass_dry in energy_list:
            inputs_dict[f'{BiomassDry.name}.{GlossaryEnergy.EnergyConsumptionValue}'] = inputs_dict_orig.pop(
                f'{AgricultureMixDiscipline.name}.{GlossaryEnergy.EnergyConsumptionValue}')
            inputs_dict[f'{BiomassDry.name}.{GlossaryEnergy.EnergyProductionValue}'] = inputs_dict_orig.pop(
                f'{AgricultureMixDiscipline.name}.{GlossaryEnergy.EnergyProductionValue}')
            inputs_dict[f'{BiomassDry.name}.{GlossaryEnergy.CO2PerUse}'] = inputs_dict_orig.pop(
                f'{AgricultureMixDiscipline.name}.{GlossaryEnergy.CO2PerUse}')
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
        years = np.arange(inputs_dict[GlossaryEnergy.YearStart],
                          inputs_dict[GlossaryEnergy.YearEnd] + 1)
        energy_list = inputs_dict[GlossaryEnergy.energy_list]
        ccs_list = inputs_dict[GlossaryEnergy.ccs_list]
        scaling_factor_energy_production = inputs_dict['scaling_factor_energy_production']
        scaling_factor_energy_consumption = inputs_dict['scaling_factor_energy_consumption']
        CO2_emissions_by_use_sources = outputs_dict['CO2_emissions_by_use_sources']
        CO2_emissions_by_use_sinks = outputs_dict['CO2_emissions_by_use_sinks']
        energy_production_detailed = self.get_sosdisc_inputs(
            GlossaryEnergy.EnergyProductionDetailedValue)

        # ------------------------------------#
        # -- CO2 emissions sources gradients--#
        # ------------------------------------#
        dtot_co2_emissions_sources = self.model.compute_grad_CO2_emissions_sources(
            energy_production_detailed)

        for key, value in dtot_co2_emissions_sources.items():
            co2_emission_column = key.split(' vs ')[0]
            energy_prod_info = key.split(' vs ')[1]
            energy = energy_prod_info.split('#')[0]
            last_part_key = energy_prod_info.split('#')[1]
            if co2_emission_column in CO2_emissions_by_use_sources.columns and energy in energy_list:
                ns_energy = energy
                if energy == BiomassDry.name:
                    ns_energy = AgricultureMixDiscipline.name
                if last_part_key == 'prod':
                    if 'Total CO2 by use' in co2_emission_column:
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_by_use_sources',
                             co2_emission_column),
                            (GlossaryEnergy.EnergyProductionDetailedValue, f'production {energy} (TWh)'),
                            np.identity(len(years)) * value / 1e3)
                    else:
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_by_use_sources',
                             co2_emission_column), (f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', energy),
                            np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)
                elif last_part_key == 'cons':
                    for energy_df in energy_list:
                        list_columnsenergycons = list(
                            inputs_dict[f'{energy_df}.{GlossaryEnergy.EnergyConsumptionValue}'].columns)
                        if f'{energy} (TWh)' in list_columnsenergycons:
                            self.set_partial_derivative_for_other_types(
                                ('CO2_emissions_by_use_sources', co2_emission_column), (
                                    f'{energy_df}.{GlossaryEnergy.EnergyConsumptionValue}', f'{energy} (TWh)'),
                                np.identity(len(years)) * scaling_factor_energy_consumption * value / 1e3)
                elif last_part_key == 'co2_per_use':
                    self.set_partial_derivative_for_other_types(
                        ('CO2_emissions_by_use_sources',
                         co2_emission_column), (f'{ns_energy}.{GlossaryEnergy.CO2PerUse}', GlossaryEnergy.CO2PerUse),
                        np.identity(len(years)) * value / 1e3)

                else:
                    very_last_part_key = energy_prod_info.split('#')[2]
                    if very_last_part_key == 'prod':
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_by_use_sources', co2_emission_column), (
                                f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', last_part_key),
                            np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)
                    elif very_last_part_key == 'cons':
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_by_use_sources', co2_emission_column), (
                                f'{ns_energy}.{GlossaryEnergy.EnergyConsumptionValue}', last_part_key),
                            np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)

            # gradient for carbone capture and storage technos producing co2
            elif co2_emission_column in CO2_emissions_by_use_sources.columns and energy in ccs_list:
                ns_energy = energy
                if last_part_key not in ['co2_per_use', 'cons', 'prod']:
                    very_last_part_key = energy_prod_info.split('#')[2]
                    if very_last_part_key == 'prod':
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_by_use_sources', co2_emission_column), (
                                f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', last_part_key),
                            np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)

        # ------------------------------------#
        # -- CO2 emissions sinks gradients--#
        # ------------------------------------#
        dtot_co2_emissions_sinks = self.model.compute_grad_CO2_emissions_sinks()

        for key, value in dtot_co2_emissions_sinks.items():
            co2_emission_column = key.split(' vs ')[0]
            energy_prod_info = key.split(' vs ')[1]
            energy = energy_prod_info.split('#')[0]
            last_part_key = energy_prod_info.split('#')[1]
            if co2_emission_column in CO2_emissions_by_use_sinks.columns and energy in energy_list:
                ns_energy = energy
                if energy == BiomassDry.name:
                    ns_energy = AgricultureMixDiscipline.name
                if last_part_key == 'prod':
                    self.set_partial_derivative_for_other_types(
                        ('CO2_emissions_by_use_sinks',
                         co2_emission_column), (f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', energy),
                        np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)
                elif last_part_key == 'cons':
                    for energy_df in energy_list:
                        list_columnsenergycons = list(
                            inputs_dict[f'{energy_df}.{GlossaryEnergy.EnergyConsumptionValue}'].columns)
                        if f'{energy} (TWh)' in list_columnsenergycons:
                            self.set_partial_derivative_for_other_types(
                                ('CO2_emissions_by_use_sinks', co2_emission_column), (
                                    f'{energy_df}.{GlossaryEnergy.EnergyConsumptionValue}', f'{energy} (TWh)'),
                                np.identity(len(years)) * scaling_factor_energy_consumption * value / 1e3)
                elif last_part_key == 'co2_per_use':
                    self.set_partial_derivative_for_other_types(
                        ('CO2_emissions_by_use_sinks',
                         co2_emission_column), (f'{ns_energy}.{GlossaryEnergy.CO2PerUse}', GlossaryEnergy.CO2PerUse),
                        np.identity(len(years)) * value / 1e3)

                else:
                    very_last_part_key = energy_prod_info.split('#')[2]
                    if very_last_part_key == 'prod':
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_by_use_sinks', co2_emission_column), (
                                f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', last_part_key),
                            np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)
                    elif very_last_part_key == 'cons':
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_by_use_sinks', co2_emission_column), (
                                f'{ns_energy}.{GlossaryEnergy.EnergyConsumptionValue}', last_part_key),
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

        chart_name = 'CO2 emissions by consumption - Sources'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'CO2 emissions (Gt)', chart_name=chart_name)

        for col in CO2_emissions_by_use_sources:
            if col != GlossaryEnergy.Years:
                new_serie = InstanciatedSeries(list(CO2_emissions_by_use_sources[GlossaryEnergy.Years].values),
                                               list(CO2_emissions_by_use_sources[col].values),
                                               col, 'lines')

                new_chart.series.append(new_serie)

        return new_chart

    def get_chart_CO2_sinks(self):
        CO2_emissions_by_use_sinks = self.get_sosdisc_outputs(
            'CO2_emissions_by_use_sinks')

        chart_name = 'CO2 emissions by consumption - Sinks'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'CO2 emissions (Gt)', chart_name=chart_name)

        for col in CO2_emissions_by_use_sinks:
            if col != GlossaryEnergy.Years:
                new_serie = InstanciatedSeries(list(CO2_emissions_by_use_sinks[GlossaryEnergy.Years].values),
                                               list(CO2_emissions_by_use_sinks[col].values),
                                               col, 'lines')

                new_chart.series.append(new_serie)

        return new_chart
