'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/14-2023/11/09 Copyright 2023 Capgemini

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

from climateeconomics.core.core_witness.climateeco_discipline import ClimateEcoDiscipline
from energy_models.core.demand.energy_demand import EnergyDemand
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.glossaryenergy import GlossaryEnergy
from sostrades_core.execution_engine.sos_wrapp import SoSWrapp
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart


class EnergyDemandDiscipline(SoSWrapp):
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

    DESC_IN = {GlossaryEnergy.YearStart: ClimateEcoDiscipline.YEAR_START_DESC_IN,
               GlossaryEnergy.YearEnd: ClimateEcoDiscipline.YEAR_END_DESC_IN,
               GlossaryEnergy.EnergyProductionDetailedValue: {'type': 'dataframe', 'unit': 'TWh',
                                                              'dataframe_descriptor': {
                                                                  GlossaryEnergy.Years: ('int', [1900, GlossaryEnergy.YeartEndDefault], False),
                                                                  'demand': ('float', None, True),
                                                                  f'production {GlossaryEnergy.electricity} (TWh)': ('float', None, True),
                                                                  f'production {GlossaryEnergy.hydrogen}.{GlossaryEnergy.liquid_hydrogen} (TWh)': ('float', None, True),
                                                                  f'production {GlossaryEnergy.fuel}.{GlossaryEnergy.liquid_fuel} (TWh)': ('float', None, True),
                                                                  f'production {GlossaryEnergy.fuel}.{GlossaryEnergy.biodiesel} (TWh)': ('float', None, True),
                                                                  f'production {GlossaryEnergy.methane} (TWh)': ('float', None, True),
                                                                  f'production {GlossaryEnergy.biogas} (TWh)': ('float', None, True),
                                                                  f'production {GlossaryEnergy.fuel}.{GlossaryEnergy.hydrotreated_oil_fuel} (TWh)': ('float', None, True),
                                                              },
                                                              'dataframe_edition_locked': False,
                                                              'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                              'namespace': GlossaryEnergy.NS_ENERGY_MIX},
               # 'default': 22847.66
               # old value is 20900TWh
               'initial_electricity_demand': {'type': 'float', 'default': 18000., 'unit': 'TWh'},
               'long_term_elec_machine_efficiency': {'type': 'float', 'default': 0.985, 'unit': '-'},
               'electricity_demand_constraint_ref': {'type': 'float', 'default': 2500.0, 'unit': 'TWh',
                                                     'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                     'namespace': GlossaryEnergy.NS_REFERENCE},
               GlossaryEnergy.PopulationDf['var_name']: GlossaryEnergy.PopulationDf,
               GlossaryEnergy.TransportDemandValue: {'type': 'dataframe', 'dataframe_descriptor': {
                   GlossaryEnergy.Years: ('int', [1900, GlossaryEnergy.YeartEndDefault], False),
                   GlossaryEnergy.TransportDemandValue: ('float', None, True)},
                                                     'dataframe_edition_locked': False, 'unit': 'TWh'},
               'transport_demand_constraint_ref': {'type': 'float', 'default': 6000.0, 'unit': 'TWh',
                                                   'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                   'namespace': GlossaryEnergy.NS_REFERENCE},
               'additional_demand_transport': {'type': 'float', 'default': 10., 'unit': '%'}}

    DESC_OUT = {
        'electricity_demand_constraint': {'type': 'dataframe', 'unit': 'TWh', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                                          'namespace': GlossaryEnergy.NS_FUNCTIONS},
        'electricity_demand': {'type': 'dataframe', 'unit': 'TWh'},
        'transport_demand_constraint': {'type': 'array', 'unit': 'TWh', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                                        'namespace': GlossaryEnergy.NS_FUNCTIONS},
        'net_transport_production': {'type': 'array', 'unit': 'TWh'},
        }
    name = EnergyDemand.name
    # The list of all energy constraints implemented in the discipline
    energy_constraint_list = [Electricity.name] + \
                             EnergyDemand.energy_list_transport
    elec_prod_column = EnergyDemand.elec_prod_column

    def __init__(self, sos_name, logger: logging.Logger):
        super().__init__(sos_name, logger)
        self.demand_model = None

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.demand_model = EnergyDemand('EnergyDemand')
        self.demand_model.configure_parameters(inputs_dict)

    def run(self):
        # -- get inputs
        inputs_dict = self.get_sosdisc_inputs()

        # -- configure class with inputs
        self.demand_model.configure_parameters_update(inputs_dict)
        # -- compute informations
        self.demand_model.compute()

        self.store_sos_outputs_values(
            {'electricity_demand_constraint': self.demand_model.get_elec_demand_constraint(),
             'electricity_demand': self.demand_model.get_elec_demand(),
             'transport_demand_constraint': self.demand_model.get_transport_demand_constraint(),
             'net_transport_production': self.demand_model.net_transport_production})

    def compute_sos_jacobian(self):
        '''
        Compute gradient of electricity_demand_constraint
        '''
        delec_demand_cosntraint_delec_prod = self.demand_model.compute_delec_demand_constraint_delec_prod()
        self.set_partial_derivative_for_other_types(
            ('electricity_demand_constraint', 'elec_demand_constraint'),
            (GlossaryEnergy.EnergyProductionDetailedValue, self.elec_prod_column), delec_demand_cosntraint_delec_prod)

        delec_demand_cosntraint_dpop = self.demand_model.compute_delec_demand_constraint_dpop()
        self.set_partial_derivative_for_other_types(
            ('electricity_demand_constraint', 'elec_demand_constraint'),
            (GlossaryEnergy.PopulationDfValue, GlossaryEnergy.PopulationValue), delec_demand_cosntraint_dpop)
        dtransport_demand_denergy_prod = self.demand_model.compute_dtransport_demand_dprod()

        for energy_name in self.demand_model.energy_list_transport:
            self.set_partial_derivative_for_other_types(
                ('transport_demand_constraint',), (GlossaryEnergy.EnergyProductionDetailedValue,
                                                   f"production {energy_name} ({EnergyMix.stream_class_dict[energy_name].unit})"),
                dtransport_demand_denergy_prod)

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['Electricity Demand Constraint',
                      'Electrical Machine Efficiency', 'Transport Demand Constraint']
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

        if 'Electrical Machine Efficiency' in charts:
            new_chart = self.get_chart_elec_machine_efficiency()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'Transport Demand Constraint' in charts:
            new_chart = self.get_chart_transport_demand_constraint()

            if new_chart is not None:
                instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_chart_elec_demand_constraint(self):
        chart_name = 'Electricity Demand Constraint'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Energy demand [TWh]',
                                             chart_name=chart_name, stacked_bar=True)

        electricity_demand = self.get_sosdisc_outputs('electricity_demand')

        serie = InstanciatedSeries(
            electricity_demand[GlossaryEnergy.Years].values.tolist(),
            electricity_demand['elec_demand (TWh)'].values.tolist(), 'electricity demand', 'lines')
        new_chart.series.append(serie)

        energy_production_detailed = self.get_sosdisc_inputs(
            GlossaryEnergy.EnergyProductionDetailedValue)
        net_elec_prod = energy_production_detailed
        serie = InstanciatedSeries(
            net_elec_prod[GlossaryEnergy.Years].values.tolist(),
            net_elec_prod[self.elec_prod_column].values.tolist(), 'electricity net production', 'lines')
        new_chart.series.append(serie)

        return new_chart

    def get_chart_transport_demand_constraint(self):
        chart_name = 'Transport Demand Constraint'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Energy demand [TWh]',
                                             chart_name=chart_name, stacked_bar=True)

        note = {
            'Transport energies': 'Liquid hydrogen, liquid fuel, biodiesel, methane, biogas, HEFA'}
        new_chart.annotation_upper_left = note
        transport_demand, energy_production_detailed = self.get_sosdisc_inputs(
            [GlossaryEnergy.TransportDemandValue, GlossaryEnergy.EnergyProductionDetailedValue])

        serie = InstanciatedSeries(
            transport_demand[GlossaryEnergy.Years].values.tolist(),
            transport_demand[GlossaryEnergy.TransportDemandValue].values.tolist(), 'transport demand', 'lines')
        new_chart.series.append(serie)
        net_transport_production = self.get_sosdisc_outputs(
            'net_transport_production')
        serie = InstanciatedSeries(
            transport_demand[GlossaryEnergy.Years].values.tolist(),
            net_transport_production.tolist(), 'transport energies net production', 'lines')
        new_chart.series.append(serie)

        return new_chart

    def get_chart_elec_machine_efficiency(self):
        chart_name = 'Electrical Machine Efficiency'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Electrical efficiency [-]',
                                             chart_name=chart_name, stacked_bar=True)

        years = np.arange(2000, 2050)
        elec_efficiency = self.demand_model.electrical_machine_efficiency(
            years)

        serie = InstanciatedSeries(
            years.tolist(),
            elec_efficiency.tolist(), '', 'lines')
        new_chart.series.append(serie)

        return new_chart
