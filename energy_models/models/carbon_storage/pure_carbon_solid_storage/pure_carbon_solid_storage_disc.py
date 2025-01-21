'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/14-2024/06/24 Copyright 2023 Capgemini

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
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import (
    InstanciatedSeries,
    TwoAxesInstanciatedChart,
)

from energy_models.core.stream_type.carbon_models.carbon import Carbon
from energy_models.core.techno_type.disciplines.carbon_storage_techno_disc import (
    CSTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.carbon_storage.pure_carbon_solid_storage.pure_carbon_solid_storage import (
    PureCarbonSS,
)


class PureCarbonSolidStorageDiscipline(CSTechnoDiscipline):
    """**EnergyModelsDiscipline** is the :class:`~gems.core.discipline.MDODiscipline`
    implementing the computation of Energy Models outputs."""

    # ontology information
    _ontology_data = {
        'label': 'Pure Carbon Solid Storage Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-flask fa-fw',
        'version': '',
    }
    techno_name = GlossaryEnergy.PureCarbonSolidStorage

    techno_infos_dict_default = {'maturity': 0,
                                 'Opex_percentage': 0,
                                 'WACC': 0.1,  # Weighted averaged cost of capital for the carbon storage plant
                                 'learning_rate': 0,
                                 # Fasihi, M., Efimova, O. and Breyer, C., 2019.
                                 # Techno-economic assessment of CO2 direct air capture plants.
                                 # Journal of cleaner production, 224,
                                 # pp.957-980.
                                 'Capex_init': 0.0175,
                                 # 730 euro/tCO2 in Fashi2019 Capex initial at year 2020 1.11 euro/$
                                 'Capex_init_unit': '$/kgCO2',
                                 'efficiency': 1,
                                 'CO2_capacity_peryear': 3.6E+8,  # kg CO2 /year
                                 'CO2_capacity_peryear_unit': 'kg CO2/year',
                                 'real_factor_CO2': 1.0,
                                 GlossaryEnergy.TransportCostValue: 0.0,
                                 'transport_cost_unit': '$/kgCO2',
                                 'enthalpy': 1.124,
                                 'enthalpy_unit': 'kWh/kgC02',
                                 GlossaryEnergy.EnergyEfficiency: 1,
                                 f"{GlossaryEnergy.CarbonResource}_needs": 1. / Carbon.data_energy_dict[GlossaryEnergy.CO2PerUse],
                                 'techno_evo_eff': 'no',
                                 }

    techno_info_dict = techno_infos_dict_default

    initial_storage = 0
    
    carbon_zero_quantity_to_be_stored = pd.DataFrame(
        {GlossaryEnergy.Years: range(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1), GlossaryEnergy.carbon_storage: 0.})

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               
               'carbon_quantity_to_be_stored': {'type': 'dataframe', 'unit': 'Mt',
                                                'default': carbon_zero_quantity_to_be_stored, 'namespace': 'ns_carb',
                                                'visibility': 'Shared', 'structuring': True,
                                                'dataframe_descriptor': {GlossaryEnergy.Years: ('int', None, False),
                                                                         GlossaryEnergy.carbon_storage: ('float', None, False),
                                                                         }
                                                }}
    # -- add specific techno outputs to this
    DESC_IN.update(CSTechnoDiscipline.DESC_IN)

    # -- add specific techno outputs to this
    DESC_OUT = {
        PureCarbonSS.CARBON_TO_BE_STORED_CONSTRAINT: {
            'type': 'dataframe', 'unit': 'Mt', 'visibility': 'Shared', 'namespace': GlossaryEnergy.NS_FUNCTIONS, CSTechnoDiscipline.GRADIENTS: True},
    }

    DESC_OUT.update(CSTechnoDiscipline.DESC_OUT)

    _maturity = 'Research'

    def setup_sos_disciplines(self):

        super().setup_sos_disciplines()

        if self.get_data_in() is not None:
            if GlossaryEnergy.YearStart in self.get_data_in():
                year_start, year_end = self.get_sosdisc_inputs([GlossaryEnergy.YearStart, GlossaryEnergy.YearEnd])
                if year_start is not None and year_end is not None:
                    years = np.arange(year_start, year_end + 1)

                    if self.get_sosdisc_inputs('carbon_quantity_to_be_stored') is not None:
                        if self.get_sosdisc_inputs('carbon_quantity_to_be_stored')[
                            GlossaryEnergy.Years].values.tolist() != list(years):
                            self.update_default_value(
                                'carbon_quantity_to_be_stored', self.IO_TYPE_IN,
                                pd.DataFrame({GlossaryEnergy.Years: years, GlossaryEnergy.carbon_storage: 0.}))

    def init_execution(self):
        self.model = PureCarbonSS(self.techno_name)

    def get_chart_filter_list(self):

        chart_filters = super().get_chart_filter_list()
        chart_filters[0].extend('Constraint')

        return chart_filters

    def get_post_processing_list(self, filters=None):

        # For the outputs, making a graph for block fuel vs range and blocktime vs
        # range

        instanciated_charts = CSTechnoDiscipline.get_post_processing_list(
            self, filters)
        charts = []
        # Overload default value with chart filter
        if filters is not None:
            for chart_filter in filters:
                if chart_filter.filter_key == 'charts':
                    charts = chart_filter.selected_values

        if 'Constraint' in charts:
            new_chart = self.get_chart_constraint()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_chart_constraint(self):
        # -- get inputs
        inputs = list(self.DESC_IN.keys())
        inputs += list(self.inst_desc_in.keys())
        inputs_dict = self.get_sosdisc_inputs()  # inputs, in_dict=True)

        outputs_dict = self.get_sosdisc_outputs()  # outputs, in_dict=True)

        # -- configure class with inputs
        self.techno_model.configure_parameters_update(inputs_dict)

        carbon_quantity_to_be_stored = inputs_dict.pop(
            'carbon_quantity_to_be_stored')
        consumption = outputs_dict.pop(GlossaryEnergy.TechnoConsumptionValue)

        constraint = self.techno_model.compute_constraint(
            carbon_quantity_to_be_stored, consumption)

        output_var = pd.merge(constraint, carbon_quantity_to_be_stored,
                              how="right", left_on=GlossaryEnergy.Years, right_on=GlossaryEnergy.Years)
        all_var = pd.merge(output_var, consumption, how="right",
                           left_on=GlossaryEnergy.Years, right_on=GlossaryEnergy.Years)

        var_list = list(all_var.keys())
        var_list.remove(GlossaryEnergy.Years)

        chart_name = 'Carbon to be stored from cracking constraint'
        max_value = 0
        min_value = 0
        for var in var_list:
            max_value = max(
                max(all_var[var].values.tolist()), max_value)
            min_value = min(min(all_var[var].values.tolist()), min_value)

        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'carbon storage [Mt]', primary_ordinate_axis_range=[min_value, max_value],
            chart_name=chart_name)

        for var in var_list:
            type = 'bar'
            if var == GlossaryEnergy.carbon_storage:
                title = 'Plasmacracking_carbon_to_be_stored'
            elif var == 'carbon (Mt)':
                title = 'Consumption'
            elif var == 'carbon_to_be_stored_constraint':
                title = 'Constraint: Consumption - Plasmacracking_carbon_to_be_stored'
                type = 'lines'
            else:
                title = 'Plasmacracking_carbon_to_be_stored'

            serie = InstanciatedSeries(
                all_var[GlossaryEnergy.Years].values.tolist(),
                all_var[var].values.tolist(), title, type)
            new_chart.series.append(serie)

        return new_chart
