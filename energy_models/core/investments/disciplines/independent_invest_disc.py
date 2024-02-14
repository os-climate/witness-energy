'''
Copyright 2022 Airbus SAS
Modifications on 2023/04/21-2023/11/16 Copyright 2023 Capgemini

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

'''
mode: python; py-indent-offset: 4; tab-width: 8; coding: utf-8
'''
import numpy as np
import pandas as pd

from climateeconomics.core.core_witness.climateeco_discipline import ClimateEcoDiscipline
from energy_models.core.ccus.ccus import CCUS
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.investments.independent_invest import IndependentInvest
from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
from energy_models.glossaryenergy import GlossaryEnergy
from sostrades_core.execution_engine.sos_wrapp import SoSWrapp
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart


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
        GlossaryEnergy.invest_mix: {'type': 'dataframe', 'unit': 'G$',
                                    'dataframe_edition_locked': False,
                                    'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                             f'{GlossaryEnergy.electricity}.SolarPv': ('float', None, True),
                                                             f'{GlossaryEnergy.electricity}.WindOnshore': ('float', None, True),
                                                             f'{GlossaryEnergy.electricity}.CoalGen': ('float', None, True),
                                                             f'{GlossaryEnergy.methane}.FossilGas': ('float', None, True),
                                                             f'{GlossaryEnergy.methane}.UpgradingBiogas': ('float', None, True),
                                                             f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.WaterGasShift': ('float', None, True),
                                                             f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.Electrolysis.AWE': ('float', None, True),
                                                             f'{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.direct_air_capture}.AmineScrubbing': ('float', None, True),
                                                             f'{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.flue_gas_capture}.CalciumLooping': ('float', None, True),
                                                             f'{GlossaryEnergy.carbon_storage}.DeepSalineFormation': ('float', None, True),
                                                             f'{GlossaryEnergy.carbon_storage}.GeologicMineralization': ('float', None, True),
                                                             f'{GlossaryEnergy.methane}.Methanation': ('float', None, True),
                                                             f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.PlasmaCracking': ('float', None, True),
                                                             f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.Electrolysis.SOEC': ('float', None, True),
                                                             f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen}.Electrolysis.PEM': ('float', None, True),
                                                             f'{GlossaryEnergy.heat}.{GlossaryEnergy.hightemperatureheat}.NaturalGasBoilerHighHeat': ('float', None, True),
                                                             f'{GlossaryEnergy.heat}.{GlossaryEnergy.hightemperatureheat}.ElectricBoilerHighHeat': ('float', None, True),
                                                             f'{GlossaryEnergy.heat}.{GlossaryEnergy.hightemperatureheat}.HeatPumpHighHeat': ('float', None, True),
                                                             f'{GlossaryEnergy.heat}.{GlossaryEnergy.hightemperatureheat}.GeothermalHighHeat': ('float', None, True),
                                                             f'{GlossaryEnergy.heat}.{GlossaryEnergy.hightemperatureheat}.CHPHighHeat': ('float', None, True),
                                                             f'{GlossaryEnergy.heat}.{GlossaryEnergy.hightemperatureheat}.HydrogenBoilerHighHeat': (
                                                             'float', None, True),
                                                             f'{GlossaryEnergy.heat}.{GlossaryEnergy.lowtemperatureheat}.NaturalGasBoilerLowHeat': ('float', None, True),
                                                             f'{GlossaryEnergy.heat}.{GlossaryEnergy.lowtemperatureheat}.ElectricBoilerLowHeat': ('float', None, True),
                                                             f'{GlossaryEnergy.heat}.{GlossaryEnergy.lowtemperatureheat}.HeatPumpLowHeat': ('float', None, True),
                                                             f'{GlossaryEnergy.heat}.{GlossaryEnergy.lowtemperatureheat}.GeothermalLowHeat': ('float', None, True),
                                                             f'{GlossaryEnergy.heat}.{GlossaryEnergy.lowtemperatureheat}.CHPLowHeat': ('float', None, True),
                                                             f'{GlossaryEnergy.heat}.{GlossaryEnergy.lowtemperatureheat}.HydrogenBoilerLowHeat': (
                                                             'float', None, True),
                                                             f'{GlossaryEnergy.heat}.{GlossaryEnergy.mediumtemperatureheat}.NaturalGasBoilerMediumHeat': ('float', None, True),
                                                             f'{GlossaryEnergy.heat}.{GlossaryEnergy.mediumtemperatureheat}.ElectricBoilerMediumHeat': ('float', None, True),
                                                             f'{GlossaryEnergy.heat}.{GlossaryEnergy.mediumtemperatureheat}.HeatPumpMediumHeat': ('float', None, True),
                                                             f'{GlossaryEnergy.heat}.{GlossaryEnergy.mediumtemperatureheat}.GeothermalMediumHeat': ('float', None, True),
                                                             f'{GlossaryEnergy.heat}.{GlossaryEnergy.mediumtemperatureheat}.CHPMediumHeat': ('float', None, True),
                                                             f'{GlossaryEnergy.heat}.{GlossaryEnergy.mediumtemperatureheat}.HydrogenBoilerMediumHeat': (
                                                             'float', None, True),
                                                             f'{GlossaryEnergy.biogas}.{GlossaryEnergy.AnaerobicDigestion}': ('float', None, True),
                                                             f'{GlossaryEnergy.syngas}.BiomassGasification': ('float', None, True),
                                                             f'{GlossaryEnergy.syngas}.SMR': ('float', None, True),
                                                             f'{GlossaryEnergy.syngas}.Pyrolysis': ('float', None, True),
                                                             f'{GlossaryEnergy.syngas}.AutothermalReforming': ('float', None, True),
                                                             f'{GlossaryEnergy.syngas}.CoElectrolysis': ('float', None, True),
                                                             f'{GlossaryEnergy.syngas}.CoalGasification': ('float', None, True),
                                                             f'{GlossaryEnergy.fuel}.{GlossaryEnergy.liquid_fuel}.Refinery': ('float', None, True),
                                                             f'{GlossaryEnergy.fuel}.{GlossaryEnergy.liquid_fuel}.FischerTropsch': ('float', None, True),
                                                             f'{GlossaryEnergy.fuel}.{GlossaryEnergy.hydrotreated_oil_fuel}.HefaDecarboxylation': ('float', None, True),
                                                             f'{GlossaryEnergy.fuel}.{GlossaryEnergy.hydrotreated_oil_fuel}.HefaDeoxygenation': ('float', None, True),
                                                             f'{GlossaryEnergy.solid_fuel}.CoalExtraction': ('float', None, True),
                                                             f'{GlossaryEnergy.solid_fuel}.Pelletizing': ('float', None, True),
                                                             f'{GlossaryEnergy.electricity}.WindOffshore': ('float', None, True),
                                                             f'{GlossaryEnergy.electricity}.SolarThermal': ('float', None, True),
                                                             f'{GlossaryEnergy.electricity}.Geothermal': ('float', None, True),
                                                             f'{GlossaryEnergy.electricity}.Hydropower': ('float', None, True),
                                                             f'{GlossaryEnergy.electricity}.Nuclear': ('float', None, True),
                                                             f'{GlossaryEnergy.electricity}.CombinedCycleGasTurbine': ('float', None, True),
                                                             f'{GlossaryEnergy.electricity}.GasTurbine': ('float', None, True),
                                                             f'{GlossaryEnergy.electricity}.BiogasFired': ('float', None, True),
                                                             f'{GlossaryEnergy.electricity}.BiomassFired': ('float', None, True),
                                                             f'{GlossaryEnergy.electricity}.OilGen': ('float', None, True),
                                                             f'{GlossaryEnergy.fuel}.{GlossaryEnergy.biodiesel}.{GlossaryEnergy.Transesterification}': ('float', None, True),
                                                             f'{GlossaryEnergy.fuel}.ethanol.BiomassFermentation': ('float', None, True),
                                                             f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.liquid_hydrogen}.HydrogenLiquefaction': ('float', None, True),
                                                             f'{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.direct_air_capture}.CalciumPotassiumScrubbing': ('float', None, True),
                                                             f'{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.flue_gas_capture}.ChilledAmmoniaProcess': ('float', None, True),
                                                             f'{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.flue_gas_capture}.CO2Membranes': ('float', None, True),
                                                             f'{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.flue_gas_capture}.MonoEthanolAmine': ('float', None, True),
                                                             f'{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.flue_gas_capture}.PiperazineProcess': ('float', None, True),
                                                             f'{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.flue_gas_capture}.PressureSwingAdsorption': ('float', None, True),
                                                             f'{GlossaryEnergy.carbon_storage}.BiomassBuryingFossilization': ('float', None, True),
                                                             f'{GlossaryEnergy.carbon_storage}.DeepOceanInjection': ('float', None, True),
                                                             f'{GlossaryEnergy.carbon_storage}.DepletedOilGas': ('float', None, True),
                                                             f'{GlossaryEnergy.carbon_storage}.EnhancedOilRecovery': ('float', None, True),
                                                             f'{GlossaryEnergy.carbon_storage}.PureCarbonSolidStorage': ('float', None, True),
                                                             f'{GlossaryEnergy.renewable}.RenewableSimpleTechno': ('float', None, True),
                                                             f'{GlossaryEnergy.fossil}.FossilSimpleTechno': ('float', None, True),
                                                             f'{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.direct_air_capture}.DirectAirCaptureTechno': ('float', None, True),
                                                             f'{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.flue_gas_capture}.FlueGasTechno': ('float', None, True),
                                                             f'{GlossaryEnergy.carbon_storage}.CarbonStorageTechno': ('float', None, True),
                                                             }},

        GlossaryEnergy.energy_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                                     'possible_values': EnergyMix.energy_list,
                                     'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy_study',
                                     'editable': False, 'structuring': True},
        GlossaryEnergy.ccs_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'},
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
        GlossaryEnergy.MaxBudgetValue : GlossaryEnergy.MaxBudgetDf,
        GlossaryEnergy.MaxBudgetConstraintRefValue: GlossaryEnergy.MaxBudgetConstraintRef
    }

    energy_name = "one_invest"

    DESC_OUT = {
        GlossaryEnergy.EnergyInvestmentsWoTaxValue: GlossaryEnergy.EnergyInvestmentsWoTax,
        GlossaryEnergy.EnergyInvestmentsMinimizationObjective: {'type': 'array', 'unit': '-',
                                                                'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                                'namespace': GlossaryEnergy.NS_FUNCTIONS},
        GlossaryEnergy.MaxBudgetConstraintValue: GlossaryEnergy.MaxBudgetConstraint
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
                    if energy == BiomassDry.name:
                        dynamic_inputs['managed_wood_investment'] = {
                            'type': 'dataframe', 'unit': 'G$', 'visibility': 'Shared',
                            'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, False),
                                                     GlossaryEnergy.InvestmentsValue: ('float', None, False)},
                            'namespace': 'ns_forest', 'dataframe_edition_locked': False, }
                        dynamic_inputs['deforestation_investment'] = {
                            'type': 'dataframe', 'unit': 'G$', 'visibility': 'Shared',
                            'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, False),
                                                     GlossaryEnergy.InvestmentsValue: ('float', None, False)},
                            'namespace': 'ns_forest', 'dataframe_edition_locked': False}
                        dynamic_inputs['crop_investment'] = {
                            'type': 'dataframe', 'unit': 'G$', 'visibility': 'Shared',
                            'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, False),
                                                     GlossaryEnergy.InvestmentsValue: ('float', None, False)},
                            'namespace': 'ns_crop', 'dataframe_edition_locked': False}
                    else:
                        # Add technologies_list to inputs
                        dynamic_inputs[f'{energy}.{GlossaryEnergy.techno_list}'] = {
                            'type': 'list', 'subtype_descriptor': {'list': 'string'}, 'structuring': True,
                            'visibility': 'Shared', 'namespace': 'ns_energy',
                            'possible_values': EnergyMix.stream_class_dict[energy].default_techno_list,
                            'default': EnergyMix.stream_class_dict[energy].default_techno_list}
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
                        'visibility': 'Shared', 'namespace': GlossaryEnergy.NS_CCS,
                        'possible_values': EnergyMix.stream_class_dict[ccs].default_techno_list}
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

        energy_investment_wo_tax, energy_invest_objective, max_budget_constraint = self.independent_invest_model.compute(
            input_dict)

        output_dict = {GlossaryEnergy.EnergyInvestmentsWoTaxValue: energy_investment_wo_tax,
                       GlossaryEnergy.EnergyInvestmentsMinimizationObjective: energy_invest_objective,
                       GlossaryEnergy.MaxBudgetConstraintValue: max_budget_constraint}

        for energy in input_dict[GlossaryEnergy.energy_list] + input_dict[GlossaryEnergy.ccs_list]:
            if energy == BiomassDry.name:
                pass
            else:
                for techno in input_dict[f'{energy}.{GlossaryEnergy.techno_list}']:
                    output_dict[f'{energy}.{techno}.{GlossaryEnergy.InvestLevelValue}'] = pd.DataFrame(
                        {GlossaryEnergy.Years: input_dict[GlossaryEnergy.invest_mix][GlossaryEnergy.Years].values,
                         GlossaryEnergy.InvestValue: input_dict[GlossaryEnergy.invest_mix][
                             f'{energy}.{techno}'].values})

        self.store_sos_outputs_values(output_dict)

    def compute_sos_jacobian(self):
        inputs_dict = self.get_sosdisc_inputs()

        years = np.arange(inputs_dict[GlossaryEnergy.YearStart],
                          inputs_dict[GlossaryEnergy.YearEnd] + 1)

        delta_years = len(years)
        identity = np.identity(delta_years)
        ones = np.ones(delta_years)

        max_budget_constraint_ref = inputs_dict[GlossaryEnergy.MaxBudgetConstraintRefValue]

        for techno in self.independent_invest_model.distribution_list:
            self.set_partial_derivative_for_other_types(
                (GlossaryEnergy.EnergyInvestmentsWoTaxValue, GlossaryEnergy.EnergyInvestmentsWoTaxValue),
                (GlossaryEnergy.invest_mix, techno),
                identity * 1e-3)

            self.set_partial_derivative_for_other_types(
                (GlossaryEnergy.EnergyInvestmentsMinimizationObjective,),
                (GlossaryEnergy.invest_mix, techno),
                ones * 1e-3)

            self.set_partial_derivative_for_other_types(
                (GlossaryEnergy.MaxBudgetConstraintValue,),
                (GlossaryEnergy.invest_mix, techno),
                identity / max_budget_constraint_ref)

            self.set_partial_derivative_for_other_types(
                (f'{techno}.{GlossaryEnergy.InvestLevelValue}', GlossaryEnergy.InvestValue),
                (GlossaryEnergy.invest_mix, techno),
                np.identity(len(years)))

        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.EnergyInvestmentsWoTaxValue, GlossaryEnergy.EnergyInvestmentsWoTaxValue),
            (GlossaryEnergy.ForestInvestmentValue, GlossaryEnergy.ForestInvestmentValue),
            identity * 1e-3)

        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.EnergyInvestmentsMinimizationObjective,),
            (GlossaryEnergy.ForestInvestmentValue, GlossaryEnergy.ForestInvestmentValue),
            ones * 1e-3)

        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.MaxBudgetConstraintValue,),
            (GlossaryEnergy.ForestInvestmentValue, GlossaryEnergy.ForestInvestmentValue),
            identity / max_budget_constraint_ref)

        energy_list = inputs_dict[GlossaryEnergy.energy_list]
        if BiomassDry.name in energy_list:
            for techno in ['managed_wood_investment', 'deforestation_investment', 'crop_investment']:
                self.set_partial_derivative_for_other_types(
                    (GlossaryEnergy.EnergyInvestmentsWoTaxValue, GlossaryEnergy.EnergyInvestmentsWoTaxValue),
                    (techno, GlossaryEnergy.InvestmentsValue),
                    identity * 1e-3)

                self.set_partial_derivative_for_other_types(
                    (GlossaryEnergy.EnergyInvestmentsMinimizationObjective,),
                    (techno, GlossaryEnergy.InvestmentsValue),
                    ones * 1e-3)

                self.set_partial_derivative_for_other_types(
                    (GlossaryEnergy.MaxBudgetConstraintValue,),
                    (techno, GlossaryEnergy.InvestmentsValue),
                    identity / max_budget_constraint_ref)

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
            techno_invests = self.get_sosdisc_inputs(
                GlossaryEnergy.invest_mix)

            chart_name = f'Distribution of investments on each energy'

            new_chart_energy = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Invest [G$]',
                                                        chart_name=chart_name, stacked_bar=True)
            energy_list = self.get_sosdisc_inputs(GlossaryEnergy.energy_list)
            ccs_list = self.get_sosdisc_inputs(GlossaryEnergy.ccs_list)

            for energy in energy_list + ccs_list:
                techno_list = [
                    col for col in techno_invests.columns if col.startswith(f'{energy}.')]
                short_df = techno_invests[techno_list]
                chart_name = f'Distribution of investments for {pimp_string(energy)}'
                new_chart_techno = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Invest [G$]',
                                                            chart_name=chart_name, stacked_bar=True)

                for techno in techno_list:
                    serie = InstanciatedSeries(
                        techno_invests[GlossaryEnergy.Years].values.tolist(),
                        short_df[techno].values.tolist(), pimp_string(techno.replace(f'{energy}.', '')), 'bar')

                    new_chart_techno.series.append(serie)
                instanciated_charts.append(new_chart_techno)
                invest = short_df.sum(axis=1).values
                # Add total price

                serie = InstanciatedSeries(
                    techno_invests[GlossaryEnergy.Years].values.tolist(),
                    invest.tolist(), pimp_string(energy), 'bar')

                new_chart_energy.series.append(serie)

            forest_investment = self.get_sosdisc_inputs(GlossaryEnergy.ForestInvestmentValue)
            chart_name = f'Distribution of reforestation investments'
            agriculture_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Invest [G$]',
                                                         chart_name=chart_name, stacked_bar=True)
            serie_agriculture = InstanciatedSeries(
                forest_investment[GlossaryEnergy.Years].values.tolist(),
                forest_investment[GlossaryEnergy.ForestInvestmentValue].values.tolist(), 'Reforestation', 'bar')
            agriculture_chart.series.append(serie_agriculture)
            instanciated_charts.append(agriculture_chart)
            serie = InstanciatedSeries(
                forest_investment[GlossaryEnergy.Years].values.tolist(),
                forest_investment[GlossaryEnergy.ForestInvestmentValue].tolist(), 'Reforestation', 'bar')

            new_chart_energy.series.append(serie)

            if BiomassDry.name in energy_list:
                chart_name = f'Distribution of agriculture sector investments'
                agriculture_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Invest [G$]',
                                                             chart_name=chart_name, stacked_bar=True)

                for techno in ['managed_wood_investment', 'deforestation_investment', 'crop_investment']:
                    invest = self.get_sosdisc_inputs(techno)
                    serie_agriculture = InstanciatedSeries(
                        invest[GlossaryEnergy.Years].values.tolist(),
                        invest[GlossaryEnergy.InvestmentsValue].values.tolist(), techno.replace("_investment", ""),
                        'bar')
                    agriculture_chart.series.append(serie_agriculture)
                    serie = InstanciatedSeries(
                        invest[GlossaryEnergy.Years].values.tolist(),
                        invest[GlossaryEnergy.InvestmentsValue].tolist(), techno.replace("_investment", ""), 'bar')
                    new_chart_energy.series.append(serie)
                instanciated_charts.append(agriculture_chart)
                instanciated_charts.insert(0, new_chart_energy)

            instanciated_charts.insert(0, new_chart_energy)

            series = [np.array(serie.ordinate) for serie in new_chart_energy.series]
            total_invest = np.sum(series, axis=0)
            chart_name = f'Distribution of investments [%]'

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

        #max budget constraint charts
        max_budget_df = self.get_sosdisc_inputs(GlossaryEnergy.MaxBudgetValue)
        max_budget = max_budget_df[GlossaryEnergy.MaxBudgetValue].values
        years = max_budget_df[GlossaryEnergy.Years].values
        if max_budget.max() > 0 :

            chart_max_budget = TwoAxesInstanciatedChart(GlossaryEnergy.Years, GlossaryEnergy.MaxBudgetDf['unit'],
                                                              chart_name=GlossaryEnergy.MaxBudgetConstraintValue, stacked_bar=True)

            serie_max_budget = InstanciatedSeries(list(years), list(max_budget), GlossaryEnergy.MaxBudgetValue, 'dash_lines')
            chart_max_budget.add_series(serie_max_budget)

            energy_invests = self.get_sosdisc_outputs(GlossaryEnergy.EnergyInvestmentsWoTaxValue)[GlossaryEnergy.EnergyInvestmentsWoTaxValue].values  * 1000
            serie_invests = InstanciatedSeries(list(years), list(energy_invests), "Invests",
                                                  'bar')
            chart_max_budget.add_series(serie_invests)
            instanciated_charts.insert(1, chart_max_budget)


        return instanciated_charts
