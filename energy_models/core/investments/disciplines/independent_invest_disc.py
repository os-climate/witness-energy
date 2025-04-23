'''
Copyright 2022 Airbus SAS
Modifications on 2023/04/21-2024/06/24 Copyright 2023 Capgemini

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
from copy import deepcopy

import numpy as np
import pandas as pd
from climateeconomics.core.core_witness.climateeco_discipline import (
    ClimateEcoDiscipline,
)
from sostrades_core.execution_engine.sos_wrapp import SoSWrapp
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import (
    InstanciatedSeries,
    TwoAxesInstanciatedChart,
)

from energy_models.core.ccus.ccus import CCUS
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.investments.independent_invest import IndependentInvest
from energy_models.glossaryenergy import GlossaryEnergy


class IndependentInvestDiscipline(SoSWrapp):
    # ontology information
    _ontology_data = {
        'label': 'InvestmentsDistribution',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-coins fa-fw',
        'version': '',
    }
    energy_mix_name = EnergyMix.name
    DESC_IN = {
        GlossaryEnergy.YearStart: ClimateEcoDiscipline.YEAR_START_DESC_IN,
        GlossaryEnergy.YearEnd: GlossaryEnergy.YearEndVar,
        GlossaryEnergy.invest_mix: GlossaryEnergy.invest_mix_df,
        GlossaryEnergy.energy_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                                     'possible_values': EnergyMix.energy_list,
                                     'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy_study',
                                     'editable': False, 'structuring': True},
        GlossaryEnergy.ccs_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                                  'possible_values': CCUS.ccs_list,
                                  'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy_study',
                                  'editable': False,
                                  'structuring': True},
        "cheat_var_to_force_ms_namespace_update": {'type': 'float', 'default': 0.,
                                  'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy',
                                  'editable': False, 'user_level': 3},
        GlossaryEnergy.MaxBudgetValue : GlossaryEnergy.MaxBudgetDf,
        GlossaryEnergy.MaxBudgetConstraintRefValue: GlossaryEnergy.MaxBudgetConstraintRef
    }

    energy_name = "one_invest"

    investments_df_variable = deepcopy(GlossaryEnergy.InvestmentDf)
    investments_df_variable["namespace"] = GlossaryEnergy.NS_WITNESS

    DESC_OUT = {
        GlossaryEnergy.MaxBudgetConstraintValue: GlossaryEnergy.MaxBudgetConstraint,
        f"{GlossaryEnergy.CCUS}.{GlossaryEnergy.InvestmentsValue}": deepcopy(investments_df_variable),
        f"{GlossaryEnergy.EnergyMix}.{GlossaryEnergy.InvestmentsValue}": deepcopy(investments_df_variable)
    }
    _maturity = 'Research'

    def __init__(self, sos_name, logger: logging.Logger):
        super().__init__(sos_name, logger)
        self.independent_invest_model = None

    def init_execution(self):
        self.independent_invest_model = IndependentInvest()

    def setup_sos_disciplines(self):
        '''
        Construct the desc_out to couple energy invest levels to techno_invest_disc
        '''
        dynamic_outputs = {}
        dynamic_inputs = {}

        if GlossaryEnergy.YearStart in self.get_data_in():
            year_start, year_end = self.get_sosdisc_inputs(
                [GlossaryEnergy.YearStart, GlossaryEnergy.YearEnd])
            years = np.arange(year_start, year_end + 1)
            default_max_budget = pd.DataFrame({GlossaryEnergy.Years: years,
                                                      GlossaryEnergy.MaxBudgetValue: np.zeros_like(years)})
            self.set_dynamic_default_values({GlossaryEnergy.MaxBudgetValue: default_max_budget})

        if GlossaryEnergy.energy_list in self.get_data_in():
            energy_list = self.get_sosdisc_inputs(GlossaryEnergy.energy_list)
            if energy_list is not None:
                for energy in energy_list:
                    # Add technologies_list to inputs
                    dynamic_inputs[f'{energy}.{GlossaryEnergy.techno_list}'] = {
                        'type': 'list', 'subtype_descriptor': {'list': 'string'}, 'structuring': True,
                        'visibility': 'Shared', 'namespace': 'ns_energy',}
                    # Add all invest_level outputs
                    if f'{energy}.{GlossaryEnergy.techno_list}' in self.get_data_in():
                        technology_list = self.get_sosdisc_inputs(
                            f'{energy}.{GlossaryEnergy.techno_list}')
                        if technology_list is not None:
                            for techno in technology_list:
                                dynamic_outputs[f'{energy}.{techno}.{GlossaryEnergy.InvestLevelValue}'] = {
                                    'type': 'dataframe', 'unit': 'G$',
                                    'visibility': 'Shared', 'namespace': 'ns_energy'}

        if GlossaryEnergy.ccs_list in self.get_data_in():
            ccs_list = self.get_sosdisc_inputs(GlossaryEnergy.ccs_list)
            if ccs_list is not None:
                for ccs in ccs_list:
                    # Add technologies_list to inputs
                    dynamic_inputs[f'{ccs}.{GlossaryEnergy.techno_list}'] = {
                        'type': 'list', 'subtype_descriptor': {'list': 'string'}, 'structuring': True,
                        'visibility': 'Shared', 'namespace': GlossaryEnergy.NS_CCS,}
                    # Add all invest_level outputs
                    if f'{ccs}.{GlossaryEnergy.techno_list}' in self.get_data_in():
                        technology_list = self.get_sosdisc_inputs(
                            f'{ccs}.{GlossaryEnergy.techno_list}')
                        if technology_list is not None:
                            for techno in technology_list:
                                dynamic_outputs[f'{ccs}.{techno}.{GlossaryEnergy.InvestLevelValue}'] = {
                                    'type': 'dataframe', 'unit': 'G$', 'visibility': 'Shared',
                                    'namespace': GlossaryEnergy.NS_CCS}

        self.add_inputs(dynamic_inputs)
        self.add_outputs(dynamic_outputs)

    def run(self):

        input_dict = self.get_sosdisc_inputs()
        self.independent_invest_model.compute(input_dict)
        self.store_sos_outputs_values(self.independent_invest_model.outputs)

    def compute_sos_jacobian(self):
        inputs_dict = self.get_sosdisc_inputs()

        years = np.arange(inputs_dict[GlossaryEnergy.YearStart],
                          inputs_dict[GlossaryEnergy.YearEnd] + 1)

        delta_years = len(years)
        identity = np.identity(delta_years)

        max_budget_constraint_ref = inputs_dict[GlossaryEnergy.MaxBudgetConstraintRefValue]
        conversion_factor = GlossaryEnergy.conversion_dict[GlossaryEnergy.invest_mix_df['unit']][GlossaryEnergy.InvestmentDf['unit']]
        conversion_factor_2 = GlossaryEnergy.conversion_dict[GlossaryEnergy.invest_mix_df['unit']][GlossaryEnergy.TechnoInvestDf['unit']]

        for energy in inputs_dict[GlossaryEnergy.energy_list]:
            for techno in inputs_dict[f'{energy}.{GlossaryEnergy.techno_list}']:
                self.set_partial_derivative_for_other_types(
                    (f"{GlossaryEnergy.EnergyMix}.{GlossaryEnergy.InvestmentsValue}", GlossaryEnergy.InvestmentsValue),
                    (GlossaryEnergy.invest_mix, f"{energy}.{techno}"),
                    identity * conversion_factor)

                self.set_partial_derivative_for_other_types(
                    (GlossaryEnergy.MaxBudgetConstraintValue, GlossaryEnergy.MaxBudgetConstraintValue),
                    (GlossaryEnergy.invest_mix, f"{energy}.{techno}"),
                    identity / max_budget_constraint_ref / 1e3)

                self.set_partial_derivative_for_other_types(
                    (f'{energy}.{techno}.{GlossaryEnergy.InvestLevelValue}', GlossaryEnergy.InvestValue),
                    (GlossaryEnergy.invest_mix, f"{energy}.{techno}"),
                    identity * conversion_factor_2)

        for energy in inputs_dict[GlossaryEnergy.ccs_list]:
            for techno in inputs_dict[f'{energy}.{GlossaryEnergy.techno_list}']:
                self.set_partial_derivative_for_other_types(
                    (f"{GlossaryEnergy.CCUS}.{GlossaryEnergy.InvestmentsValue}", GlossaryEnergy.InvestmentsValue),
                    (GlossaryEnergy.invest_mix, f"{energy}.{techno}"),
                    identity * conversion_factor)

                self.set_partial_derivative_for_other_types(
                    (GlossaryEnergy.MaxBudgetConstraintValue, GlossaryEnergy.MaxBudgetConstraintValue),
                    (GlossaryEnergy.invest_mix, f"{energy}.{techno}"),
                    identity / max_budget_constraint_ref / 1e3)

                self.set_partial_derivative_for_other_types(
                    (f'{energy}.{techno}.{GlossaryEnergy.InvestLevelValue}', GlossaryEnergy.InvestValue),
                    (GlossaryEnergy.invest_mix, f"{energy}.{techno}"),
                    identity * conversion_factor_2)


    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['Invest Distribution']
        chart_filters.append(ChartFilter(
            'Charts Investments', chart_list, chart_list, 'charts_invest'))

        return chart_filters

    def get_post_processing_list(self, filters=None):

        # For the outputs, making a graph for block fuel vs range and blocktime vs
        # range

        instanciated_charts = []
        charts = []

        # Overload default value with chart filter
        if filters is not None:
            for chart_filter in filters:
                if chart_filter.filter_key == 'charts_invest':
                    charts = chart_filter.selected_values

        def pimp_string(val: str):
            val = val.replace('_', ' ')
            val = val.replace('.', ' - ')
            val = val[0].upper() + val[1:]
            return val

        if 'Invest Distribution' in charts:
            techno_invests = self.get_sosdisc_inputs(GlossaryEnergy.invest_mix)

            chart_name = 'Distribution of investments on each energy'

            unit = GlossaryEnergy.invest_mix_df['unit']
            new_chart_energy = TwoAxesInstanciatedChart(GlossaryEnergy.Years, f'Invest [{unit}]',
                                                        chart_name=chart_name, stacked_bar=True)

            years = self.get_sosdisc_outputs(GlossaryEnergy.MaxBudgetConstraintValue)[GlossaryEnergy.Years].values
            energy_list = self.get_sosdisc_inputs(GlossaryEnergy.energy_list)
            ccs_list = self.get_sosdisc_inputs(GlossaryEnergy.ccs_list)

            for energy in energy_list + ccs_list:
                techno_list = [
                    col for col in techno_invests.columns if col.startswith(f'{energy}.')]
                short_df = techno_invests[techno_list]
                chart_name = f'Distribution of investments for {pimp_string(energy)}'
                new_chart_techno = TwoAxesInstanciatedChart(GlossaryEnergy.Years, f'Invest [{unit}]',
                                                            chart_name=chart_name, stacked_bar=True)

                for techno in techno_list:
                    serie = InstanciatedSeries(
                        years,
                        short_df[techno].values.tolist(), pimp_string(techno.replace(f'{energy}.', '')), 'bar')

                    new_chart_techno.series.append(serie)
                instanciated_charts.append(new_chart_techno)
                invest = short_df.sum(axis=1).values
                # Add total price

                serie = InstanciatedSeries(
                    years,
                    invest.tolist(), pimp_string(energy), 'bar')

                new_chart_energy.series.append(serie)

            instanciated_charts.insert(0, new_chart_energy)

            series = [np.array(serie.ordinate) for serie in new_chart_energy.series]
            total_invest = np.sum(series, axis=0)
            chart_name = 'Distribution of investments [%]'

            new_chart_energy_ratio = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Share of total invest [%]',
                                                              chart_name=chart_name, stacked_bar=True)
            for serie in new_chart_energy.series:
                serie_ratio = InstanciatedSeries(
                    serie.abscissa,
                    list(np.array(serie.ordinate) / total_invest * 100),
                    serie.series_name, 'bar'
                )
                new_chart_energy_ratio.add_series(serie_ratio)

            instanciated_charts.insert(1, new_chart_energy_ratio)

        return instanciated_charts
