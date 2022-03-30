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

from energy_models.core.demand.demand_mix import DemandMix
from energy_models.core.energy_mix.energy_mix import EnergyMix
from sos_trades_core.execution_engine.sos_discipline import SoSDiscipline
from sos_trades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sos_trades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.carbon_models.carbon_storage import CarbonStorage


class DemandMixDiscipline(SoSDiscipline):

    # ontology information
    _ontology_data = {
        'label': 'Energy Demand Mix Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-battery-full fa-fw',
        'version': '',
    }

    DESC_IN = {'energy_list': {'type': 'string_list', 'possible_values': EnergyMix.energy_list,
                               'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_study', 'editable': False, 'structuring': True},
               'ccs_list': {'type': 'string_list', 'possible_values': [CarbonCapture.name, CarbonStorage.name],
                            'default': [CarbonCapture.name, CarbonStorage.name],
                            'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_study', 'editable': False, 'structuring': True},
               'year_start': {'type': 'int', 'default': 2020, 'unit': '[-]', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
               'year_end': {'type': 'int', 'default': 2050, 'unit': '[-]', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
               'total_energy_demand': {'type': 'dataframe', 'unit': 'TWh',
                                       'dataframe_descriptor': {'years': ('int',  [1900, 2100], False),
                                                                'demand': ('float',  None, True)},
                                       'dataframe_edition_locked': False}
               }

    energy_name = DemandMix.name

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.energy_model = DemandMix(self.energy_name)
        self.energy_model.configure_parameters(inputs_dict)

    def setup_sos_disciplines(self):
        dynamic_inputs = {}
        dynamic_outputs = {}

        if 'energy_list' in self._data_in:
            energy_list = self.get_sosdisc_inputs('energy_list')
            if energy_list is not None:
                for energy in energy_list:
                    dynamic_inputs[f'{energy}.energy_demand_mix'] = {'type': 'dataframe', 'unit': '%',
                                                                     'dataframe_descriptor': {'years': ('int',  [1900, 2100], False),
                                                                                              'mix': ('float',  None, True)},
                                                                     'dataframe_edition_locked': False,
                                                                     'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_mix'}
                    dynamic_outputs[f'{energy}.energy_demand'] = {
                        'type': 'dataframe', 'unit': 'TWh', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_demand'}

        if 'ccs_list' in self._data_in:
            ccs_list = self.get_sosdisc_inputs('ccs_list')
            if ccs_list is not None:
                for ccs_name in ccs_list:
                    dynamic_inputs[f'{ccs_name}.energy_demand_mix'] = {'type': 'dataframe', 'unit': '%',
                                                                       'dataframe_descriptor': {'years': ('int',  [1900, 2100], False),
                                                                                                'mix': ('float',  None, True)},
                                                                       'dataframe_edition_locked': False,
                                                                       'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ccs'}
                    dynamic_outputs[f'{ccs_name}.energy_demand'] = {
                        'type': 'dataframe', 'unit': 'TWh', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_demand'}

        self.add_inputs(dynamic_inputs)
        self.add_outputs(dynamic_outputs)

        self.update_default_dataframes_with_years()

    def update_default_dataframes_with_years(self):
        '''
        Update all default dataframes with years 
        '''
        if 'year_start' in self._data_in:
            year_start, year_end = self.get_sosdisc_inputs(
                ['year_start', 'year_end'])
            years = np.arange(year_start, year_end + 1)
            self.dm.set_data(self.get_var_full_name(
                'total_energy_demand', self._data_in), 'default', pd.DataFrame({'years': years,
                                                                                'demand': 0.0}), False)

    def run(self):
        #-- get inputs
        inputs_dict = self.get_sosdisc_inputs()

        #-- configure class with inputs
        self.energy_model.configure_parameters_update(inputs_dict)
        #-- compute informations
        self.energy_model.compute()

        #-- store outputs
        energy_list = self.get_sosdisc_inputs('energy_list')
        ccs_list = self.get_sosdisc_inputs('ccs_list')
        complete_list = energy_list + ccs_list
        outputs_dict = {}
        for energy in complete_list:
            key = f'{energy}.energy_demand'
            outputs_dict[key] = self.energy_model.energy_demand_per_energy[energy]
        self.store_sos_outputs_values(outputs_dict)

    def compute_sos_jacobian(self):
        pass

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['Energy Demand']
        chart_filters.append(ChartFilter(
            'Charts', chart_list, chart_list, 'charts'))

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

        if 'Energy Demand' in charts:
            new_chart = self.get_chart_demand_mix()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_chart_demand_mix(self):
        chart_name = 'Energy Demand'
        energy_list = self.get_sosdisc_inputs('energy_list')
        new_chart = TwoAxesInstanciatedChart('years', 'Energy demand [TWh]',
                                             chart_name=chart_name, stacked_bar=True)
        for energy in energy_list:
            demand_mix_df = self.get_sosdisc_outputs(
                f'{energy}.energy_demand')

            serie = InstanciatedSeries(
                demand_mix_df['years'].values.tolist(),
                demand_mix_df['demand'].values.tolist(), f'{energy}', 'bar')
            new_chart.series.append(serie)
        return new_chart
