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
from energy_models.core.energy_ghg_emissions.energy_ghg_emissions import EnergyGHGEmissions
from climateeconomics.sos_wrapping.sos_wrapping_agriculture.agriculture.agriculture_mix_disc import AgricultureMixDiscipline
from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
from sos_trades_core.execution_engine.sos_discipline import SoSDiscipline
from energy_models.core.energy_mix.energy_mix import EnergyMix

from sos_trades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sos_trades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart

import numpy as np
from climateeconomics.core.core_witness.climateeco_discipline import ClimateEcoDiscipline
from climateeconomics.core.core_emissions.ghg_emissions_model import GHGEmissions
from climateeconomics.sos_wrapping.sos_wrapping_emissions.ghgemissions.ghgemissions_discipline import GHGemissionsDiscipline


class EnergyGHGEmissionsDiscipline(SoSDiscipline):

    # ontology information
    _ontology_data = {
        'label': 'Energy GHG emissions Model',
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
        'GHG_global_warming_potential20':  {'type': 'dict', 'unit': 'kgCO2eq/kg', 'default': GHGemissionsDiscipline.GWP_20_default, 'visibility': ClimateEcoDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_witness', 'user_level': 3},
        'GHG_global_warming_potential100':  {'type': 'dict', 'unit': 'kgCO2eq/kg', 'default': GHGemissionsDiscipline.GWP_100_default, 'visibility': ClimateEcoDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_witness', 'user_level': 3},
        'energy_production_detailed': {'type': 'dataframe', 'unit': 'TWh', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy'},
        'co2_emissions_ccus_Gt': {'type': 'dataframe', 'unit': 'Gt', 'visibility': ClimateEcoDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ccs'},
        'co2_emissions_needed_by_energy_mix': {'type': 'dataframe', 'unit': 'Gt', 'visibility': ClimateEcoDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy'}, }

    DESC_OUT = {
        'CO2_emissions_sources': {'type': 'dataframe', 'unit': 'Gt'},
        'CO2_emissions_sinks':  {'type': 'dataframe', 'unit': 'Gt'},
        'GHG_total_energy_emissions':  {'type': 'dataframe', 'unit': 'Gt', 'visibility': ClimateEcoDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_witness'},
        'GHG_emissions_per_energy':  {'type': 'dict', 'unit': 'Gt'},
        'GWP_emissions': {'type': 'dataframe', 'unit': 'GtCO2eq'},
    }

    name = f'{GHGemissionsDiscipline.name}.Energy'

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.model = EnergyGHGEmissions(self.name)
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
                    if energy == BiomassDry.name:
                        for ghg in GHGEmissions.GHG_TYPE_LIST:
                            dynamic_inputs[f'{AgricultureMixDiscipline.name}.{ghg}_per_use'] = {
                                'type': 'dataframe', 'unit': 'kg/kWh', 'namespace': 'ns_witness', 'visibility': SoSDiscipline.SHARED_VISIBILITY}
                        dynamic_inputs[f'{AgricultureMixDiscipline.name}.energy_consumption'] = {
                            'type': 'dataframe', 'unit': 'PWh', 'namespace': 'ns_witness', 'visibility': SoSDiscipline.SHARED_VISIBILITY}
                        dynamic_inputs[f'{AgricultureMixDiscipline.name}.energy_production'] = {
                            'type': 'dataframe', 'unit': 'PWh', 'namespace': 'ns_witness', 'visibility': SoSDiscipline.SHARED_VISIBILITY}
                    else:
                        for ghg in GHGEmissions.GHG_TYPE_LIST:
                            dynamic_inputs[f'{energy}.{ghg}_per_use'] = {
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
        inputs_dict = self.get_sosdisc_inputs()

        self.model.configure_parameters_update(inputs_dict)
        self.model.compute_ghg_emissions()

        outputs_dict = {
            'GHG_total_energy_emissions': self.model.ghg_total_emissions,
            'GHG_emissions_per_energy': self.model.ghg_production_dict,
            'CO2_emissions_sources': self.model.CO2_sources_Gt,
            'CO2_emissions_sinks': self.model.CO2_sinks_Gt,
            'GWP_emissions': self.model.gwp_emissions

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
        CO2_emissions_sources = outputs_dict['CO2_emissions_sources']
        CO2_emissions_sinks = outputs_dict['CO2_emissions_sinks']
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
            if co2_emission_column in CO2_emissions_sources.columns and energy in energy_list:
                ns_energy = energy
                if energy == BiomassDry.name:
                    ns_energy = AgricultureMixDiscipline.name
                if last_part_key == 'prod':
                    if 'Total CO2 by use' in co2_emission_column:
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_sources',
                             co2_emission_column), ('energy_production_detailed', f'production {energy} (TWh)'),
                            np.identity(len(years)) * value / 1e3)
                    else:
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_sources',
                             co2_emission_column), (f'{ns_energy}.energy_production', energy),
                            np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)
                elif last_part_key == 'cons':
                    for energy_df in energy_list:
                        list_columnsenergycons = list(
                            inputs_dict[f'{energy_df}.energy_consumption'].columns)
                        if f'{energy} (TWh)' in list_columnsenergycons:
                            self.set_partial_derivative_for_other_types(
                                ('CO2_emissions_sources', co2_emission_column), (
                                    f'{energy_df}.energy_consumption', f'{energy} (TWh)'),
                                np.identity(len(years)) * scaling_factor_energy_consumption * value / 1e3)
#                 elif last_part_key == 'co2_per_use':
#                     self.set_partial_derivative_for_other_types(
#                         ('CO2_emissions_sources',
#                          co2_emission_column), (f'{ns_energy}.CO2_per_use', 'CO2_per_use'),
#                         np.identity(len(years)) * value / 1e3)

                else:
                    very_last_part_key = energy_prod_info.split('#')[2]
                    if very_last_part_key == 'prod':
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_sources', co2_emission_column), (
                                f'{ns_energy}.energy_production', last_part_key),
                            np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)
                    elif very_last_part_key == 'cons':
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_sources', co2_emission_column), (
                                f'{ns_energy}.energy_consumption', last_part_key),
                            np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)

        dtot_co2_emissions = self.model.compute_grad_total_co2_emissions(
            energy_production_detailed)
        for energy in energy_list:
            max_prod_grad = dtot_co2_emissions_sources[
                f'Total CO2 by use (Gt) vs {energy}#co2_per_use']
            if energy == 'biomass_dry':
                for ghg in self.model.GHG_TYPE_LIST:
                    self.set_partial_derivative_for_other_types(
                        ('GHG_total_energy_emissions',
                         f'Total {ghg} emissions'), (f'{AgricultureMixDiscipline.name}.{ghg}_per_use', f'{ghg}_per_use'),
                        np.identity(len(years)) * max_prod_grad / 1e3)
                    value = dtot_co2_emissions[f'Total {ghg} emissions vs prod{energy}']
                    self.set_partial_derivative_for_other_types(
                        ('GHG_total_energy_emissions',
                         f'Total {ghg} emissions'), (f'{AgricultureMixDiscipline.name}.energy_production', energy),
                        np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)
            else:
                for ghg in self.model.GHG_TYPE_LIST:
                    self.set_partial_derivative_for_other_types(
                        ('GHG_total_energy_emissions',
                         f'Total {ghg} emissions'), (f'{energy}.{ghg}_per_use', f'{ghg}_per_use'),
                        np.identity(len(years)) * max_prod_grad / 1e3)
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
            if co2_emission_column in CO2_emissions_sinks.columns and energy in energy_list:
                ns_energy = energy
                if energy == BiomassDry.name:
                    ns_energy = AgricultureMixDiscipline.name
                if last_part_key == 'prod':
                    self.set_partial_derivative_for_other_types(
                        ('CO2_emissions_sinks',
                         co2_emission_column), (f'{ns_energy}.energy_production', energy),
                        np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)
                elif last_part_key == 'cons':
                    for energy_df in energy_list:
                        list_columnsenergycons = list(
                            inputs_dict[f'{energy_df}.energy_consumption'].columns)
                        if f'{energy} (TWh)' in list_columnsenergycons:
                            self.set_partial_derivative_for_other_types(
                                ('CO2_emissions_sinks', co2_emission_column), (
                                    f'{energy_df}.energy_consumption', f'{energy} (TWh)'),
                                np.identity(len(years)) * scaling_factor_energy_consumption * value / 1e3)
                elif last_part_key == 'co2_per_use':
                    self.set_partial_derivative_for_other_types(
                        ('CO2_emissions_sinks',
                         co2_emission_column), (f'{ns_energy}.CO2_per_use', 'CO2_per_use'),
                        np.identity(len(years)) * value / 1e3)
                else:
                    very_last_part_key = energy_prod_info.split('#')[2]
                    if very_last_part_key == 'prod':
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_sinks', co2_emission_column), (
                                f'{ns_energy}.energy_production', last_part_key),
                            np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)
                    elif very_last_part_key == 'cons':
                        self.set_partial_derivative_for_other_types(
                            ('CO2_emissions_sinks', co2_emission_column), (
                                f'{ns_energy}.energy_consumption', last_part_key),
                            np.identity(len(years)) * scaling_factor_energy_production * value / 1e3)

        self.set_partial_derivative_for_other_types(
            ('GHG_total_energy_emissions',
             'Total CO2 emissions'), ('co2_emissions_ccus_Gt', 'carbon_storage Limited by capture (Gt)'), -np.identity(len(years)))
        self.set_partial_derivative_for_other_types(
            ('GHG_total_energy_emissions',
             'Total CO2 emissions'), ('co2_emissions_needed_by_energy_mix', 'carbon_capture needed by energy mix (Gt)'), -np.identity(len(years)))

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['Global Warming Potential', 'Total CO2 emissions',
                      'Emissions per energy',
                      'CO2 sources', 'CO2 sinks']

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

        if 'Global Warming Potential' in charts:
            for gwp_year in [20, 100]:
                new_chart = self.get_chart_gwp(gwp_year)
                if new_chart is not None:
                    instanciated_charts.append(new_chart)

        if 'Total CO2 emissions' in charts:

            new_chart = self.get_chart_total_co2_emissions()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'Emissions per energy' in charts:
            for ghg in EnergyGHGEmissions.GHG_TYPE_LIST:
                new_chart = self.get_chart_ghg_emissions_per_energy(ghg)
                if new_chart is not None:
                    instanciated_charts.append(new_chart)
        if 'CO2 sources' in charts:

            new_chart = self.get_chart_CO2_sources()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'CO2 sinks' in charts:
            new_chart = self.get_chart_CO2_sinks()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_chart_total_co2_emissions(self):
        GHG_total_energy_emissions = self.get_sosdisc_outputs(
            'GHG_total_energy_emissions')

        chart_name = f'Total CO2 emissions for energy sector'
        new_chart = TwoAxesInstanciatedChart(
            'years', 'CO2 emissions [Gt]', chart_name=chart_name)

        new_serie = InstanciatedSeries(list(GHG_total_energy_emissions['years'].values), list(GHG_total_energy_emissions['Total CO2 emissions'].values),
                                       'lines')

        new_chart.series.append(new_serie)

        return new_chart

    def get_chart_gwp(self, gwp_year):
        GWP_emissions = self.get_sosdisc_outputs(
            'GWP_emissions')

        chart_name = f'Global warming potential for energy sector emissions at {gwp_year} years'
        new_chart = TwoAxesInstanciatedChart(
            'years', 'GWP [GtCO2]', chart_name=chart_name, stacked_bar=True)

        for ghg in EnergyGHGEmissions.GHG_TYPE_LIST:
            new_serie = InstanciatedSeries(list(GWP_emissions['years'].values), list(GWP_emissions[f'{ghg}_{gwp_year}'].values),
                                           ghg, 'bar')

            new_chart.series.append(new_serie)

        return new_chart

    def get_chart_ghg_emissions_per_energy(self, ghg):
        GHG_emissions_per_energy = self.get_sosdisc_outputs(
            'GHG_emissions_per_energy')

        chart_name = f'{ghg} emissions per energy'
        new_chart = TwoAxesInstanciatedChart(
            'years', f'{ghg} emissions [Mt]', chart_name=chart_name, stacked_bar=True)
        energy_list = self.get_sosdisc_inputs('energy_list')
        for energy in energy_list:
            ghg_energy = GHG_emissions_per_energy[ghg][[
                col for col in GHG_emissions_per_energy[ghg] if energy in col]].sum(axis=1).values
            if not (ghg_energy == 0).all():
                new_serie = InstanciatedSeries(list(GHG_emissions_per_energy[ghg]['years'].values), list(ghg_energy), energy,
                                               'bar')

                new_chart.series.append(new_serie)

        return new_chart

    def get_chart_CO2_sources(self):
        CO2_emissions_sources = self.get_sosdisc_outputs(
            'CO2_emissions_sources')

        chart_name = f'CO2 emissions by consumption - Sources'
        new_chart = TwoAxesInstanciatedChart(
            'years', 'CO2 emissions [Gt]', chart_name=chart_name)

        for col in CO2_emissions_sources:
            if col != 'years':
                new_serie = InstanciatedSeries(list(CO2_emissions_sources['years'].values), list(CO2_emissions_sources[col].values),
                                               col, 'lines')

                new_chart.series.append(new_serie)

        return new_chart

    def get_chart_CO2_sinks(self):
        CO2_emissions_sinks = self.get_sosdisc_outputs(
            'CO2_emissions_sinks')

        chart_name = f'CO2 emissions by consumption - Sinks'
        new_chart = TwoAxesInstanciatedChart(
            'years', 'CO2 emissions [Gt]', chart_name=chart_name)

        for col in CO2_emissions_sinks:
            if col != 'years':
                new_serie = InstanciatedSeries(list(CO2_emissions_sinks['years'].values), list(CO2_emissions_sinks[col].values),
                                               col, 'lines')

                new_chart.series.append(new_serie)

        return new_chart
