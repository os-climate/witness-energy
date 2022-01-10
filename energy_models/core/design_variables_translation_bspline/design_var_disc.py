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

from energy_models.core.design_variables_translation_bspline.design_var import Design_var
from sos_trades_core.execution_engine.sos_discipline import SoSDiscipline
import numpy as np
import pandas as pd
from plotly import graph_objects as go

from sos_trades_core.tools.post_processing.plotly_native_charts.instantiated_plotly_native_chart import InstantiatedPlotlyNativeChart
from sos_trades_core.tools.post_processing.charts.chart_filter import ChartFilter


class Design_Var_Discipline(SoSDiscipline):
    EXPORT_XVECT = 'export_xvect'

    DESC_IN = {
        'year_start': {'type': 'int', 'default': 2020, 'unit': '[-]', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_witness'},
        'year_end': {'type': 'int', 'default': 2100, 'unit': '[-]', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_witness'},
        'time_step': {'type': 'int', 'default': 1, 'visibility': 'Shared', 'unit': 'year', 'namespace': 'ns_witness'},
        'energy_list': {'type': 'string_list', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_study', 'editable': False, 'structuring': True},
        'ccs_list': {'type': 'string_list', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_study', 'editable': False, 'structuring': True},
        'ccs_percentage_array': {'type': 'array', 'unit': '$/t', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_witness'},
        'design_space': {'type': 'dataframe', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_optim'},

        EXPORT_XVECT: {'type': 'bool', 'default': False}
    }

    DESC_OUT = {
        'invest_energy_mix': {'type': 'dataframe', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_mix'},
        'invest_ccs_mix': {'type': 'dataframe', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ccs'},
        'ccs_percentage': {'type': 'dataframe', 'unit': '%', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ccs'},
    }

    def setup_sos_disciplines(self):

        dynamic_inputs = {}
        dynamic_outputs = {}

        if 'energy_list' in self._data_in:
            energy_list = self.get_sosdisc_inputs('energy_list')
            if energy_list is not None:
                for energy in energy_list:
                    energy_wo_dot = energy.replace('.', '_')
                    dynamic_inputs[f'{energy}.{energy_wo_dot}_array_mix'] = {
                        'type': 'array', 'unit': '%', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_mix'}

                    dynamic_inputs[f'{energy}.technologies_list'] = {'type': 'string_list',
                                                                     'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_mix', 'structuring': True}

                    dynamic_outputs[f'{energy}.invest_techno_mix'] = {
                        'type': 'dataframe', 'unit': '$',
                        'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_mix'}

                    if f'{energy}.technologies_list' in self._data_in:
                        technology_list = self.get_sosdisc_inputs(
                            f'{energy}.technologies_list')

                        if technology_list is not None:
                            for techno in technology_list:
                                techno_wo_dot = techno.replace('.', '_')
                                dynamic_inputs[f'{energy}.{techno}.{energy_wo_dot}_{techno_wo_dot}_array_mix'] = {
                                    'type': 'array', 'unit': '%', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_mix'}

        if 'ccs_list' in self._data_in:
            ccs_list = self.get_sosdisc_inputs('ccs_list')
            if ccs_list is not None:
                for ccs_name in ccs_list:
                    ccs_name_wo_dot = ccs_name.replace('.', '_')
                    dynamic_inputs[f'{ccs_name}.{ccs_name_wo_dot}_array_mix'] = {
                        'type': 'array', 'unit': '%', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ccs'}

                    dynamic_inputs[f'{ccs_name}.technologies_list'] = {'type': 'string_list',
                                                                       'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ccs', 'structuring': True}

                    dynamic_outputs[f'{ccs_name}.invest_techno_mix'] = {
                        'type': 'dataframe', 'unit': '$',
                        'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ccs'}

                    if f'{ccs_name}.technologies_list' in self._data_in:
                        technology_list = self.get_sosdisc_inputs(
                            f'{ccs_name}.technologies_list')

                        if technology_list is not None:
                            for techno in technology_list:
                                techno_wo_dot = techno.replace('.', '_')
                                dynamic_inputs[f'{ccs_name}.{techno}.{ccs_name_wo_dot}_{techno_wo_dot}_array_mix'] = {
                                    'type': 'array', 'unit': '%', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ccs'}
        self.add_inputs(dynamic_inputs)
        self.add_outputs(dynamic_outputs)
        self.iter = 0

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()

        self.design = Design_var(inputs_dict)

    def run(self):
        inputs_dict = self.get_sosdisc_inputs()

        self.design.configure(inputs_dict)
        self.store_sos_outputs_values(self.design.output_dict)

    def compute_sos_jacobian(self):

        inputs_dict = self.get_sosdisc_inputs()

        years = np.arange(inputs_dict['year_start'],
                          inputs_dict['year_end'] + 1, inputs_dict['time_step'])

        for energy in inputs_dict['energy_list']:
            energy_wo_dot = energy.replace('.', '_')
            self.set_partial_derivative_for_other_types(
                (f'invest_energy_mix',
                 energy), (f'{energy}.{energy_wo_dot}_array_mix',),
                self.design.bspline_dict[f'{energy}.{energy_wo_dot}_array_mix']['b_array'])

            for techno in inputs_dict[f'{energy}.technologies_list']:
                techno_wo_dot = techno.replace('.', '_')
                self.set_partial_derivative_for_other_types(
                    (f'{energy}.invest_techno_mix', techno), (
                        f'{energy}.{techno}.{energy_wo_dot}_{techno_wo_dot}_array_mix',),
                    self.design.bspline_dict[f'{energy}.{techno}.{energy_wo_dot}_{techno_wo_dot}_array_mix']['b_array'])

        for ccs in inputs_dict['ccs_list']:
            ccs_wo_dot = ccs.replace('.', '_')
            self.set_partial_derivative_for_other_types(
                (f'invest_ccs_mix',
                 ccs), (f'{ccs}.{ccs_wo_dot}_array_mix',),
                self.design.bspline_dict[f'{ccs}.{ccs_wo_dot}_array_mix']['b_array'])

            for techno in inputs_dict[f'{ccs}.technologies_list']:
                techno_wo_dot = techno.replace('.', '_')
                self.set_partial_derivative_for_other_types(
                    (f'{ccs}.invest_techno_mix', techno), (
                        f'{ccs}.{techno}.{ccs_wo_dot}_{techno_wo_dot}_array_mix',),
                    self.design.bspline_dict[f'{ccs}.{techno}.{ccs_wo_dot}_{techno_wo_dot}_array_mix']['b_array'])

        self.set_partial_derivative_for_other_types(
            (f'ccs_percentage', 'ccs_percentage'), (f'ccs_percentage_array',),  self.design.bspline_dict['ccs_percentage_array']['b_array'])

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['test']
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
                if chart_filter.filter_key == 'charts':
                    charts = chart_filter.selected_values
        if 'test' in charts:
            list_dv = [key for key in self.get_sosdisc_inputs().keys() if key not in [
                'year_start', 'year_end', 'time_step', 'linearization_mode', 'cache_type', 'cache_file_path', 'design_space']]
            for parameter in list_dv:
                new_chart = self.get_chart_BSpline(
                    parameter=parameter)
                if new_chart is not None:
                    instanciated_charts.append(new_chart)
        return instanciated_charts

    def get_chart_BSpline(self, parameter):
        """
        Function to create post-proc for the design variables with display of the control points used to 
        calculate the B-Splines.
        The activation/deactivation of control points is accounted for by inserting the values from the design space
        dataframe into the ctrl_pts if need be (activated_elem==False) and at the appropriate index.
        Input: parameter (name), parameter values, design_space
        Output: InstantiatedPlotlyNativeChart
        """
        design_space = self.get_sosdisc_inputs('design_space')
        if parameter not in design_space['variable'].to_list():
            return None
        ctrl_pts = list(self.get_sosdisc_inputs(parameter))
        for i, activation in enumerate(design_space.loc[design_space['variable']
                                                        == parameter, 'activated_elem'].to_list()[0]):
            if not activation and len(design_space.loc[design_space['variable'] == parameter, 'value'].to_list()[0]) > i:
                ctrl_pts.insert(i, design_space.loc[design_space['variable']
                                                    == parameter, 'value'].to_list()[0][i])
        eval_pts = None
        for key in self.get_sosdisc_outputs().keys():
            for column in self.get_sosdisc_outputs(key).columns:
                if column in parameter:
                    eval_pts = self.get_sosdisc_outputs(key)[column].values
                    years = self.get_sosdisc_outputs(key)['years'].values
        if eval_pts is None:
            print('eval pts not found in sos_disc_outputs')
            return None
        else:
            chart_name = f'B-Spline for {parameter}'
            fig = go.Figure()
            if 'complex' in str(type(ctrl_pts[0])):
                ctrl_pts = [np.real(value) for value in ctrl_pts]
            if 'complex' in str(type(eval_pts[0])):
                eval_pts = [np.real(value) for value in eval_pts]
            x_ctrl_pts = np.linspace(
                years[0], years[-1], len(ctrl_pts))
            marker_dict = dict(size=150 / len(ctrl_pts), line=dict(
                width=150 / (3 * len(ctrl_pts)), color='DarkSlateGrey'))
            fig.add_trace(go.Scatter(x=list(x_ctrl_pts),
                                     y=list(ctrl_pts), name='Poles',
                                     mode='lines+markers',
                                     marker=marker_dict))
            fig.add_trace(go.Scatter(x=list(years),
                                     y=list(eval_pts), name='B-Spline'))
            fig.update_layout(title={'text': chart_name, 'x': 0.5, 'y': 1.0, 'xanchor': 'center', 'yanchor': 'top'},
                              xaxis_title='years', yaxis_title=f'value of {parameter}')
            new_chart = InstantiatedPlotlyNativeChart(
                fig, chart_name=chart_name, default_title=True)
        return new_chart
