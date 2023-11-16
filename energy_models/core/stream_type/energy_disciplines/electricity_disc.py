'''
Copyright 2022 Airbus SAS
Modifications on 2023/04/21-2023/11/09 Copyright 2023 Capgemini

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
from climateeconomics.glossarycore import GlossaryCore
from energy_models.core.stream_type.energy_disc import EnergyDiscipline
from energy_models.core.stream_type.energy_models.electricity import Electricity
from sostrades_core.execution_engine.sos_wrapp import SoSWrapp

import numpy as np
import pandas as pd
from plotly import graph_objects as go
import plotly.colors as plt_color

from sostrades_core.tools.post_processing.plotly_native_charts.instantiated_plotly_native_chart import \
    InstantiatedPlotlyNativeChart
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from energy_models.sos_processes.energy.MDA.energy_process_v0.usecase import hydropower_name


class ElectricityDiscipline(EnergyDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Electricity Energy Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-plug fa-fw',
        'version': '',
    }

    DESC_IN = {GlossaryCore.techno_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                                     'possible_values': Electricity.default_techno_list,
                                     'default': Electricity.default_techno_list,
                                     'visibility': EnergyDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_electricity',
                                     'structuring': True, 'unit': '-'},
               'hydropower_production_current': {'type': 'float',
                                                 'default': 6600.0,
                                                 # 4400TWh is total production,
                                                 # we use a 50% higher value
                                                 'unit': 'Twh',
                                                 'user_level': 2,
                                                 'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                 'namespace': 'ns_ref'},
               'hydropower_constraint_ref': {'type': 'float',
                                             'default': 1000.,
                                             'unit': 'Twh',
                                             'user_level': 2,
                                             'visibility': SoSWrapp.SHARED_VISIBILITY,
                                             'namespace': 'ns_ref'},
               'data_fuel_dict': {'type': 'dict',
                                  'visibility': EnergyDiscipline.SHARED_VISIBILITY,
                                  'namespace': 'ns_electricity',
                                  'default': Electricity.data_energy_dict,
                                  'unit': 'defined in dict'},
               }
    DESC_IN.update(EnergyDiscipline.DESC_IN)

    energy_name = Electricity.name
    DESC_OUT = {}
    # -- add specific techno outputs to this
    DESC_OUT.update(EnergyDiscipline.DESC_OUT)

    def setup_sos_disciplines(self):
        super().setup_sos_disciplines()

        dynamic_outputs = {}
        if GlossaryCore.techno_list in self.get_data_in():
            techno_list = self.get_sosdisc_inputs(GlossaryCore.techno_list)

            if techno_list is not None:
                if hydropower_name in techno_list:
                    dynamic_outputs['prod_hydropower_constraint'] = {'type': 'dataframe', 'user_level': 2,
                                                                     'unit': 'TWh',
                                                                     'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                                     'namespace': 'ns_functions'}
        self.add_outputs(dynamic_outputs)

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.energy_model = Electricity(self.energy_name)
        self.energy_model.configure_parameters(inputs_dict)

    def run(self):
        '''
        Run for all energy disciplines
        '''

        EnergyDiscipline.run(self)
        # -- get inputs
        if hydropower_name in self.energy_model.subelements_list:
            self.energy_model.compute_hydropower_constraint()

            outputs_dict = {'prod_hydropower_constraint': self.energy_model.hydropower_constraint
                            }
        else:
            outputs_dict = {}
        # -- store outputs
        self.store_sos_outputs_values(outputs_dict)

    def compute_sos_jacobian(self):
        '''
        Overide sos jacobian to compute gradient of hydropower constraint
        '''
        inputs_dict = self.get_sosdisc_inputs()

        years = np.arange(inputs_dict[GlossaryCore.YearStart],
                          inputs_dict[GlossaryCore.YearEnd] + 1)
        if hydropower_name in self.energy_model.subelements_list:
            self.set_partial_derivative_for_other_types(('prod_hydropower_constraint', 'hydropower_constraint'), (
                'Hydropower.techno_production', f'{Electricity.name} ({Electricity.unit})'),
                                                        - inputs_dict['scaling_factor_techno_production'] * np.identity(
                                                            len(years)) / inputs_dict['hydropower_constraint_ref'])

        EnergyDiscipline.compute_sos_jacobian(self)

    def get_chart_filter_list(self):

        chart_filters = EnergyDiscipline.get_chart_filter_list(self)
        chart_list = ['Energy price', 'Technology mix', 'CO2 emissions',
                      'Consumption and production', 'Constraints']

        chart_filters.append(ChartFilter(
            'Charts', chart_list, chart_list, 'charts'))

        return chart_filters

    def get_post_processing_list(self, filters=None):

        # For the outputs, making a graph for block fuel vs range and blocktime vs
        # range

        instanciated_charts = EnergyDiscipline.get_post_processing_list(
            self, filters)
        charts = []
        if filters is not None:
            for chart_filter in filters:
                if chart_filter.filter_key == 'charts':
                    charts = chart_filter.selected_values
        if 'Constraints' in charts:
            constraints_list = ['prod_hydropower_constraint']
            new_chart = self.get_chart_constraint(
                constraints_list)
            if new_chart is not None:
                instanciated_charts.append(new_chart)
        return instanciated_charts

    def get_chart_constraint(self, constraints_list):
        """
        Function to create post-proc for the constraints of a node
        Input: constraints list (names)
        Output: InstantiatedPlotlyNativeChart
        """
        constraints_dict = {}
        for constraint in constraints_list:
            constraints_dict[constraint] = list(
                self.get_sosdisc_outputs(constraint).values[:, 1])
        years = list(np.arange(self.get_sosdisc_inputs(
            GlossaryCore.YearStart), self.get_sosdisc_inputs(GlossaryCore.YearEnd) + 1))
        chart_name = 'Constraints'
        fig = go.Figure()
        for key in constraints_dict.keys():
            fig.add_trace(go.Scatter(x=list(years),
                                     y=list(constraints_dict[key]), name=key,
                                     mode='lines', ))
        fig.update_layout(title={'text': chart_name, 'x': 0.5, 'y': 0.95, 'xanchor': 'center', 'yanchor': 'top'},
                          xaxis_title=GlossaryCore.Years, yaxis_title=f'value of constraint')
        fig.update_layout(
            updatemenus=[
                dict(
                    buttons=list([
                        dict(
                            args=[{"yaxis.type": "linear"}],
                            label="Linear",
                            method="relayout"
                        ),
                        dict(
                            args=[{"yaxis.type": "log"}],
                            label="Log",
                            method="relayout"
                        ),
                    ]),
                    type="buttons",
                    direction="right",
                    pad={"r": 10, "t": 10},
                    showactive=True,
                    active=0,
                    x=0.0,
                    xanchor="left",
                    y=1.01,
                    yanchor="bottom"
                ),
            ]
        )
        new_chart = InstantiatedPlotlyNativeChart(
            fig, chart_name=chart_name, default_title=True)
        return new_chart
