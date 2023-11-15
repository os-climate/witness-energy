"""
Copyright 2023 Capgemini

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import numpy as np
import pandas as pd

from climateeconomics.glossarycore import GlossaryCore
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.investments.investments_redistribution import InvestmentsRedistribution
from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
from sostrades_core.execution_engine.sos_wrapp import SoSWrapp
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart
from climateeconomics.core.core_witness.climateeco_discipline import ClimateEcoDiscipline
from energy_models.core.ccus.ccus import CCUS


class InvestmentsRedistributionDisicpline(SoSWrapp):
    # ontology information
    _ontology_data = {
        'label': 'InvestmentsReDistribution',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': '',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-coins fa-fw',
        'version': '',
    }
    energy_mix_name = EnergyMix.name
    DESC_IN = {
        GlossaryCore.YearStart: ClimateEcoDiscipline.YEAR_START_DESC_IN,
        GlossaryCore.YearEnd: ClimateEcoDiscipline.YEAR_END_DESC_IN,
        GlossaryEnergy.EnergyListName: {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                                        'possible_values': EnergyMix.energy_list,
                                        'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy_study',
                                        'editable': False, 'structuring': True},
        GlossaryEnergy.CCSListName: {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                                     'possible_values': CCUS.ccs_list,
                                     'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy_study',
                                     'editable': False,
                                     'structuring': True},
        GlossaryEnergy.ForestInvestmentValue: {'type': 'dataframe', 'unit': 'G$', 'visibility': 'Shared',
                                               'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, False),
                                                                        GlossaryEnergy.ForestInvestmentValue: (
                                                                            'float', None, False)},
                                               'namespace': 'ns_invest',
                                               'dataframe_edition_locked': False},

        GlossaryCore.EconomicsDfValue: GlossaryCore.get_dynamic_variable(GlossaryCore.EconomicsDf),
        GlossaryEnergy.EnergyInvestPercentageGDPName: GlossaryEnergy.get_dynamic_variable(
            GlossaryEnergy.EnergyInvestPercentageGDP)
    }

    DESC_OUT = {
        GlossaryCore.EnergyInvestmentsWoTaxValue: GlossaryCore.EnergyInvestmentsWoTax,
    }
    _maturity = 'Research'

    def init_execution(self):
        self.invest_redistribution_model = InvestmentsRedistribution()

    def setup_sos_disciplines(self):
        '''
        Construct the desc_out to couple energy invest levels to techno_invest_disc
        '''
        dynamic_outputs = {}
        dynamic_inputs = {}
        techno_invest_percentage_desc = GlossaryEnergy.get_dynamic_variable(
            GlossaryEnergy.TechnoInvestPercentage)
        if GlossaryCore.energy_list in self.get_data_in():
            energy_list = self.get_sosdisc_inputs(GlossaryCore.energy_list)
            if energy_list is not None:
                for energy in energy_list:
                    if energy != BiomassDry.name:
                        # Add technologies_list to inputs
                        dynamic_inputs[f'{energy}.{GlossaryCore.techno_list}'] = {
                            'type': 'list', 'subtype_descriptor': {'list': 'string'}, 'structuring': True,
                            'visibility': 'Shared', 'namespace': 'ns_energy',
                            'possible_values': EnergyMix.stream_class_dict[energy].default_techno_list,
                            'default': EnergyMix.stream_class_dict[energy].default_techno_list}
                        # Add all invest_level outputs
                        if f'{energy}.{GlossaryCore.techno_list}' in self.get_data_in():
                            technology_list = self.get_sosdisc_inputs(
                                f'{energy}.{GlossaryCore.techno_list}')
                            if technology_list is not None:
                                for techno in technology_list:
                                    techno_invest_percentage_desc[self.DATAFRAME_DESCRIPTOR].update(
                                        {techno: ("float", None, True)})
                                    dynamic_outputs[f'{energy}.{techno}.{GlossaryCore.InvestLevelValue}'] = {
                                        'type': 'dataframe', 'unit': 'G$',
                                        'visibility': 'Shared', 'namespace': 'ns_energy'}
                    else:
                        # if Biomass dry energy then add relevant variables
                        dynamic_inputs[GlossaryEnergy.ManagedWoodInvestmentName] = GlossaryEnergy.get_dynamic_variable(
                            GlossaryEnergy.ManagedWoodInvestment)
                        dynamic_inputs[
                            GlossaryEnergy.DeforestationInvestmentName] = GlossaryEnergy.get_dynamic_variable(
                            GlossaryEnergy.DeforestationInvestment)
                        dynamic_inputs[GlossaryEnergy.CropInvestmentName] = GlossaryEnergy.get_dynamic_variable(
                            GlossaryEnergy.CropInvestment)

        if GlossaryCore.ccs_list in self.get_data_in():
            ccs_list = self.get_sosdisc_inputs(GlossaryCore.ccs_list)
            if ccs_list is not None:
                for ccs in ccs_list:
                    # Add technologies_list to inputs
                    dynamic_inputs[f'{ccs}.{GlossaryCore.techno_list}'] = {
                        'type': 'list', 'subtype_descriptor': {'list': 'string'}, 'structuring': True,
                        'visibility': 'Shared', 'namespace': 'ns_ccs',
                        'possible_values': EnergyMix.stream_class_dict[ccs].default_techno_list}
                    # Add all invest_level outputs
                    if f'{ccs}.{GlossaryCore.techno_list}' in self.get_data_in():
                        technology_list = self.get_sosdisc_inputs(
                            f'{ccs}.{GlossaryCore.techno_list}')
                        if technology_list is not None:
                            for techno in technology_list:
                                # update dataframe descriptor
                                techno_invest_percentage_desc[self.DATAFRAME_DESCRIPTOR].update(
                                    {techno: ("float", None, True)})
                                dynamic_outputs[f'{ccs}.{techno}.{GlossaryCore.InvestLevelValue}'] = {
                                    'type': 'dataframe', 'unit': 'G$', 'visibility': 'Shared', 'namespace': 'ns_ccs'}
        dynamic_inputs[GlossaryEnergy.TechnoInvestPercentageName] = techno_invest_percentage_desc
        self.add_inputs(dynamic_inputs)
        self.add_outputs(dynamic_outputs)

    def run(self):

        input_dict = self.get_sosdisc_inputs()
        self.invest_redistribution_model.configure_parameters(input_dict)
        self.invest_redistribution_model.compute()

        output_dict = {
            GlossaryCore.EnergyInvestmentsWoTaxValue: self.invest_redistribution_model.energy_investment_wo_tax,
            }

        for energy in input_dict[GlossaryCore.energy_list] + input_dict[GlossaryCore.ccs_list]:
            if energy == BiomassDry.name:
                pass
            else:
                for techno_name, invest_techno in self.invest_redistribution_model.investment_per_technology_dict.items():
                    output_dict[f'{techno_name}.{GlossaryCore.InvestLevelValue}'] = invest_techno

        self.store_sos_outputs_values(output_dict)

    def compute_sos_jacobian(self):
        # compute derivative of output wrt to coupled inputs (in this discipline only economics df is coupled)
        inputs_dict = self.get_sosdisc_inputs()

        years = np.arange(inputs_dict[GlossaryCore.YearStart],
                          inputs_dict[GlossaryCore.YearEnd] + 1)

        delta_years = len(years)
        identity = np.identity(delta_years)
        ones = np.ones(delta_years)
        energy_list = inputs_dict[GlossaryEnergy.EnergyListName]
        ccs_list = inputs_dict[GlossaryEnergy.CCSListName]
        percentage_gdp_invest_energy = inputs_dict[
                                           GlossaryEnergy.EnergyInvestPercentageGDPName] / 100.  # divide by 100 as it is percentage
        techno_invest_percentage_df = inputs_dict[GlossaryEnergy.TechnoInvestPercentageName]

        for energy, techno_list in self.invest_redistribution_model.techno_list_dict.items():
            for techno in techno_list:
                grad_inv_level_wrt_economics = percentage_gdp_invest_energy * identity * techno_invest_percentage_df[
                    techno].values / 100.

                self.set_partial_derivative_for_other_types(
                    (f'{energy}.{techno}.{GlossaryCore.InvestLevelValue}', GlossaryCore.InvestValue),
                    (GlossaryCore.EconomicsDfValue, GlossaryCore.OutputNetOfDamage),
                    grad_inv_level_wrt_economics)

        self.set_partial_derivative_for_other_types(
            (GlossaryCore.EnergyInvestmentsWoTaxValue, GlossaryCore.EnergyInvestmentsWoTaxValue),
            (GlossaryCore.EconomicsDfValue, GlossaryCore.OutputNetOfDamage),
            percentage_gdp_invest_energy * identity * 1e-3)  # 1e-3 to convert G$ to T$

        self.set_partial_derivative_for_other_types(
            (GlossaryCore.EnergyInvestmentsWoTaxValue, GlossaryCore.EnergyInvestmentsWoTaxValue),
            (GlossaryCore.ForestInvestmentValue, GlossaryCore.ForestInvestmentValue),
            identity * 1e-3)

        if BiomassDry.name in energy_list:
            for techno in ['managed_wood_investment', 'deforestation_investment', 'crop_investment']:
                self.set_partial_derivative_for_other_types(
                    (GlossaryCore.EnergyInvestmentsWoTaxValue, GlossaryCore.EnergyInvestmentsWoTaxValue),
                    (techno, GlossaryCore.InvestmentsValue),
                    identity * 1e-3)

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['Invest Distribution']
        chart_filters.append(ChartFilter(
            'Charts Investments', chart_list, chart_list, 'charts_invest'))

        return chart_filters

    def get_post_processing_list(self, filters=None):


        instanciated_charts = []
        charts = []

        # Overload default value with chart filter
        if filters is not None:
            for chart_filter in filters:
                if chart_filter.filter_key == 'charts_invest':
                    charts = chart_filter.selected_values

        inputs_dict = self.get_sosdisc_inputs(
            )
        outputs_dict = self.get_sosdisc_outputs()
        year_start = inputs_dict[GlossaryEnergy.YearStart]
        year_end = inputs_dict[GlossaryEnergy.YearEnd]
        years = np.arange(year_start, year_end + 1)
        if 'Invest Distribution' in charts:

            chart_name = f'Distribution of investments on each energy vs years'

            new_chart_energy = TwoAxesInstanciatedChart(GlossaryCore.Years, 'Invest [G$]',
                                                        chart_name=chart_name, stacked_bar=True)
            energy_list = inputs_dict[GlossaryCore.energy_list]
            ccs_list = inputs_dict[GlossaryCore.ccs_list]
            for energy in energy_list + ccs_list:
                list_energy = []
                if energy != BiomassDry.name:
                    chart_name = f'Distribution of investments for {energy} vs years'
                    new_chart_techno = TwoAxesInstanciatedChart(GlossaryCore.Years, 'Invest [G$]',
                                                                chart_name=chart_name, stacked_bar=True)
                    techno_list_name = f'{energy}.{GlossaryEnergy.TechnoListName}'
                    techno_list = inputs_dict[techno_list_name]
                    for techno in techno_list:
                        invest_level = outputs_dict[f'{energy}.{techno}.{GlossaryEnergy.InvestLevelValue}']

                        serie = InstanciatedSeries(
                            years.tolist(),
                            invest_level[f'{GlossaryEnergy.InvestValue}'].values.tolist(), techno, 'bar')
                        list_energy.append(invest_level[f'{GlossaryEnergy.InvestValue}'].values)
                        new_chart_techno.series.append(serie)

                    instanciated_charts.append(new_chart_techno)
                    total_invest = list(np.sum(list_energy, axis=0))
                    # Add total inbest
                    serie = InstanciatedSeries(
                        years.tolist(),
                        total_invest, energy, 'bar')

                    new_chart_energy.series.append(serie)

            forest_investment = self.get_sosdisc_inputs(GlossaryCore.ForestInvestmentValue)
            chart_name = f'Distribution of reforestation investments vs years'
            agriculture_chart = TwoAxesInstanciatedChart(GlossaryCore.Years, 'Invest [G$]',
                                                         chart_name=chart_name, stacked_bar=True)
            serie_agriculture = InstanciatedSeries(
                forest_investment[GlossaryCore.Years].values.tolist(),
                forest_investment[GlossaryCore.ForestInvestmentValue].values.tolist(), 'Reforestation', 'bar')
            agriculture_chart.series.append(serie_agriculture)
            instanciated_charts.append(agriculture_chart)
            serie = InstanciatedSeries(
                forest_investment[GlossaryCore.Years].values.tolist(),
                forest_investment[GlossaryCore.ForestInvestmentValue].tolist(), 'Reforestation', 'bar')

            new_chart_energy.series.append(serie)

            if BiomassDry.name in energy_list:
                chart_name = f'Distribution of agriculture sector investments vs years'
                agriculture_chart = TwoAxesInstanciatedChart(GlossaryCore.Years, 'Invest [G$]',
                                                             chart_name=chart_name, stacked_bar=True)

                for techno in ['managed_wood_investment', 'deforestation_investment', 'crop_investment']:
                    invest = self.get_sosdisc_inputs(techno)
                    serie_agriculture = InstanciatedSeries(
                        invest[GlossaryCore.Years].values.tolist(),
                        invest[GlossaryCore.InvestmentsValue].values.tolist(), techno.replace("_investment", ""), 'bar')
                    agriculture_chart.series.append(serie_agriculture)
                    serie = InstanciatedSeries(
                        invest[GlossaryCore.Years].values.tolist(),
                        invest[GlossaryCore.InvestmentsValue].tolist(), techno.replace("_investment", ""), 'bar')
                    new_chart_energy.series.append(serie)
                instanciated_charts.append(agriculture_chart)
                instanciated_charts.insert(0, new_chart_energy)

            instanciated_charts.insert(0, new_chart_energy)

        return instanciated_charts
