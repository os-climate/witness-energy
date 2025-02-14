'''
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
'''
import logging

import numpy as np
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
from energy_models.core.investments.investments_redistribution import (
    InvestmentsRedistribution,
)
from energy_models.glossaryenergy import GlossaryEnergy


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
    # update used dictionaries in DESC_IN with specific informations
    energy_list_desc_dict = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.EnergyList)
    energy_list_desc_dict.update({'possible_values': EnergyMix.energy_list})
    ccs_list_desc_dict = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.CCSList)
    ccs_list_desc_dict.update({'possible_values': CCUS.ccs_list})
    DESC_IN = {
        GlossaryEnergy.YearStart: ClimateEcoDiscipline.YEAR_START_DESC_IN,
        GlossaryEnergy.YearEnd: GlossaryEnergy.YearEndVar,
        GlossaryEnergy.EnergyListName: energy_list_desc_dict,
        GlossaryEnergy.CCSListName: ccs_list_desc_dict,
        GlossaryEnergy.EconomicsDfValue: GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.EconomicsDf),
        GlossaryEnergy.EnergyInvestPercentageGDPName: GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.EnergyInvestPercentageGDP)
    }

    DESC_OUT = {
        GlossaryEnergy.EnergyInvestmentsWoTaxValue: GlossaryEnergy.EnergyInvestmentsWoTax,
    }
    _maturity = 'Research'

    def __init__(self, sos_name, logger: logging.Logger):
        super().__init__(sos_name, logger)
        self.invest_redistribution_model = None

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
        if GlossaryEnergy.energy_list in self.get_data_in():
            energy_list = self.get_sosdisc_inputs(GlossaryEnergy.energy_list)
            if energy_list is not None:
                for energy in energy_list:
                    if energy != GlossaryEnergy.biomass_dry:
                        # Add technologies_list to inputs
                        techno_list_desc_dict = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.TechnoList)
                        # update informations of technologies list with specific ones (namespace, default and possible values)
                        techno_list_desc_dict.update({'namespace': 'ns_energy',})
                        dynamic_inputs[f'{energy}.{GlossaryEnergy.techno_list}'] = techno_list_desc_dict
                        # Add all invest_level outputs
                        if f'{energy}.{GlossaryEnergy.techno_list}' in self.get_data_in():
                            technology_list = self.get_sosdisc_inputs(f'{energy}.{GlossaryEnergy.techno_list}')
                            if technology_list is not None:
                                for techno in technology_list:
                                    # update dataframe descriptor with used technologies
                                    techno_invest_percentage_desc[self.DATAFRAME_DESCRIPTOR].update(
                                        {techno: ("float", None, True)})
                                    # use generic invest level from Glossary and update namespace
                                    invest_level_desc_dict = GlossaryEnergy.get_dynamic_variable(
                                        GlossaryEnergy.InvestLevel)
                                    invest_level_desc_dict.update({'namespace': 'ns_energy'})
                                    dynamic_outputs[
                                        f'{energy}.{techno}.{GlossaryEnergy.InvestLevelValue}'] = invest_level_desc_dict

        if GlossaryEnergy.ccs_list in self.get_data_in():
            ccs_list = self.get_sosdisc_inputs(GlossaryEnergy.ccs_list)
            if ccs_list is not None:
                for ccs in ccs_list:
                    # Add technologies_list to inputs
                    techno_list_desc_dict = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.TechnoList)
                    techno_list_desc_dict.update({'namespace': GlossaryEnergy.NS_CCS})
                    dynamic_inputs[f'{ccs}.{GlossaryEnergy.TechnoListName}'] = techno_list_desc_dict
                    # Add all invest_level outputs
                    if f'{ccs}.{GlossaryEnergy.techno_list}' in self.get_data_in():
                        technology_list = self.get_sosdisc_inputs(
                            f'{ccs}.{GlossaryEnergy.techno_list}')
                        if technology_list is not None:
                            for techno in technology_list:
                                # update dataframe descriptor
                                techno_invest_percentage_desc[self.DATAFRAME_DESCRIPTOR].update(
                                    {techno: ("float", None, True)})
                                # use generic invest level from Glossary and update namespace

                                invest_level_desc_dict = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.InvestLevel)
                                invest_level_desc_dict.update({'namespace': GlossaryEnergy.NS_CCS})
                                dynamic_outputs[
                                    f'{ccs}.{techno}.{GlossaryEnergy.InvestLevelValue}'] = invest_level_desc_dict
        # use updated informations for variable
        dynamic_inputs[GlossaryEnergy.TechnoInvestPercentageName] = techno_invest_percentage_desc
        self.add_inputs(dynamic_inputs)
        self.add_outputs(dynamic_outputs)

    def check_data_integrity(self):
        '''
        Check data integrity of the discipline

        '''
        inputs_dict = self.get_sosdisc_inputs()
        self.init_execution()

        integrity_msg_dict = self.invest_redistribution_model.check_data_integrity(inputs_dict)

        for var_name, integrity_msg in integrity_msg_dict.items():
            var_full_name = self.get_input_var_full_name(var_name)
            self.dm.set_data(
                var_full_name, self.CHECK_INTEGRITY_MSG, integrity_msg)

    def run(self):

        input_dict = self.get_sosdisc_inputs()
        self.invest_redistribution_model.configure_parameters(input_dict)
        self.invest_redistribution_model.compute()

        # add energy investments wo tax to output dictionnary
        output_dict = {
            GlossaryEnergy.EnergyInvestmentsWoTaxValue: self.invest_redistribution_model.energy_investment_wo_tax,
        }

        # add investments in all technologies (except for biomass dry to output)
        for energy in input_dict[GlossaryEnergy.energy_list] + input_dict[GlossaryEnergy.ccs_list]:
            if energy != GlossaryEnergy.biomass_dry:
                for techno_name, invest_techno in self.invest_redistribution_model.investment_per_technology_dict.items():
                    output_dict[f'{techno_name}.{GlossaryEnergy.InvestLevelValue}'] = invest_techno

        self.store_sos_outputs_values(output_dict)

    def compute_sos_jacobian(self):
        # compute derivative of output wrt to coupled inputs (in this discipline only economics df is coupled)
        inputs_dict = self.get_sosdisc_inputs()

        years = np.arange(inputs_dict[GlossaryEnergy.YearStart],
                          inputs_dict[GlossaryEnergy.YearEnd] + 1)

        delta_years = len(years)
        identity = np.identity(delta_years)
        energy_list = inputs_dict[GlossaryEnergy.EnergyListName]
        percentage_gdp_invest_energy = inputs_dict[GlossaryEnergy.EnergyInvestPercentageGDPName][
                                           GlossaryEnergy.EnergyInvestPercentageGDPName].values / 100.  # divide by 100 as it is percentage and *1e3 as we convert to G$
        techno_invest_percentage_df = inputs_dict[GlossaryEnergy.TechnoInvestPercentageName]
        economics_df = inputs_dict[GlossaryEnergy.EconomicsDfValue]

        for energy, techno_list in self.invest_redistribution_model.techno_list_dict.items():
            for techno in techno_list:
                grad_inv_level_wrt_economics = percentage_gdp_invest_energy * identity * techno_invest_percentage_df[
                    techno].values / 100.
                grad_inv_level_wrt_gdp_perc = identity * economics_df[GlossaryEnergy.OutputNetOfDamage].values * \
                                              techno_invest_percentage_df[
                                                  techno].values / 100.

                self.set_partial_derivative_for_other_types(
                    (f'{energy}.{techno}.{GlossaryEnergy.InvestLevelValue}', GlossaryEnergy.InvestValue),
                    (GlossaryEnergy.EconomicsDfValue, GlossaryEnergy.OutputNetOfDamage),
                    grad_inv_level_wrt_economics * 1e3)

                self.set_partial_derivative_for_other_types(
                    (f'{energy}.{techno}.{GlossaryEnergy.InvestLevelValue}', GlossaryEnergy.InvestValue),
                    (GlossaryEnergy.EnergyInvestPercentageGDPName, GlossaryEnergy.EnergyInvestPercentageGDPName),
                    grad_inv_level_wrt_gdp_perc * 1e3 / 100.)

        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.EnergyInvestmentsWoTaxValue, GlossaryEnergy.EnergyInvestmentsWoTaxValue),
            (GlossaryEnergy.EconomicsDfValue, GlossaryEnergy.OutputNetOfDamage),
            percentage_gdp_invest_energy * identity)

        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.EnergyInvestmentsWoTaxValue, GlossaryEnergy.EnergyInvestmentsWoTaxValue),
            (GlossaryEnergy.EnergyInvestPercentageGDPName, GlossaryEnergy.EnergyInvestPercentageGDPName),
            economics_df[GlossaryEnergy.OutputNetOfDamage].values * identity / 100.)


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

            chart_name = 'Distribution of investments on each energy '

            new_chart_energy = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Invest [G$]',
                                                        chart_name=chart_name, stacked_bar=True)
            energy_list = inputs_dict[GlossaryEnergy.energy_list]
            ccs_list = inputs_dict[GlossaryEnergy.ccs_list]
            # add a chart per energy with breakdown of investments in every technology of the energy
            for energy in energy_list + ccs_list:
                list_energy = []
                if energy != GlossaryEnergy.biomass_dry:
                    chart_name = f'Distribution of investments for {energy} '
                    new_chart_techno = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Invest [G$]',
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


            instanciated_charts.insert(0, new_chart_energy)

        return instanciated_charts
