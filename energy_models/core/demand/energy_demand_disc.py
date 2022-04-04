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


from energy_models.core.demand.energy_demand import EnergyDemand
from energy_models.core.energy_mix.energy_mix import EnergyMix
from sos_trades_core.execution_engine.sos_discipline import SoSDiscipline
from sos_trades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sos_trades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart
from energy_models.core.stream_type.energy_models.electricity import Electricity


class EnergyDemandDiscipline(SoSDiscipline):

    # ontology information
    _ontology_data = {
        'label': 'Energy Demand Model',
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

    DESC_IN = {'year_start': {'type': 'int', 'default': 2020, 'unit': '[-]', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
               'year_end': {'type': 'int', 'default': 2050, 'unit': '[-]', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
               'energy_production_detailed': {'type': 'dataframe', 'unit': 'TWh',
                                              'dataframe_descriptor': {'years': ('int',  [1900, 2100], False),
                                                                       'demand': ('float',  None, True)},
                                              'dataframe_edition_locked': False,
                                              'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_mix'},
               'initial_electricity_demand': {'type': 'float', 'default': 22847.66, 'unit': 'TWh'},
               'demand_efficiency': {'type': 'float', 'default': 0.99, 'unit': '-'},
               'electricity_demand_constraint_ref': {'type': 'float', 'default': 100.0, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ref'},
               }

    DESC_OUT = {'electricity_demand_constraint': {'type': 'dataframe', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_functions'},
                'electricity_demand': {'type': 'dataframe', 'unit': 'TWh'},
                }
    name = EnergyDemand.name
    # The list of all energy constraints implemented in the discipline
    energy_constraint_list = [Electricity.name]
    elec_prod_column = EnergyDemand.elec_prod_column

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.demand_model = EnergyDemand('EnergyDemand')
        self.demand_model.configure_parameters(inputs_dict)

    def run(self):
        #-- get inputs
        inputs_dict = self.get_sosdisc_inputs()

        #-- configure class with inputs
        self.demand_model.configure_parameters_update(inputs_dict)
        #-- compute informations
        self.demand_model.compute()

        self.store_sos_outputs_values(
            {'electricity_demand_constraint': self.demand_model.get_elec_demand_constraint(),
             'electricity_demand': self.demand_model.get_elec_demand()})

    def compute_sos_jacobian(self):
        '''
        Compute gradient of electricity_demand_constraint
        '''
        delec_demand_cosntraint_delec_prod = self.demand_model.compute_delec_demand_constraint_delec_prod()
        self.set_partial_derivative_for_other_types(
            ('electricity_demand_constraint', 'electricity_demand_constraint'), ('energy_production_detailed', self.elec_prod_column),  delec_demand_cosntraint_delec_prod)

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['Electricity Demand Constraint']
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

        if 'Electricity Demand Constraint' in charts:
            new_chart = self.get_chart_elec_demand_constraint()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_chart_elec_demand_constraint(self):
        chart_name = 'Electricity Demand Constraint'

        new_chart = TwoAxesInstanciatedChart('years', 'Energy demand [TWh]',
                                             chart_name=chart_name, stacked_bar=True)

        electricity_demand = self.get_sosdisc_outputs('electricity_demand')

        serie = InstanciatedSeries(
            electricity_demand['years'].values.tolist(),
            electricity_demand['elec_demand (TWh)'].values.tolist(), 'electricity demand', 'lines')
        new_chart.series.append(serie)

        energy_production_detailed = self.get_sosdisc_inputs(
            'energy_production_detailed')
        net_elec_prod = energy_production_detailed
        serie = InstanciatedSeries(
            net_elec_prod['years'].values.tolist(),
            net_elec_prod[self.elec_prod_column].values.tolist(), 'electricity net production', 'lines')
        new_chart.series.append(serie)

        return new_chart
