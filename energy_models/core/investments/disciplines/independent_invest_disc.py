'''
Copyright 2022 Airbus SAS
Modifications on 2023/04/21-2023/11/06 Copyright 2023 Capgemini

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
'''
mode: python; py-indent-offset: 4; tab-width: 8; coding: utf-8
'''
import numpy as np
import pandas as pd

from climateeconomics.glossarycore import GlossaryCore
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.investments.independent_invest import IndependentInvest
from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
from sostrades_core.execution_engine.sos_wrapp import SoSWrapp
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart
from climateeconomics.core.core_witness.climateeco_discipline import ClimateEcoDiscipline
from energy_models.core.ccus.ccus import CCUS


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
        'year_start': ClimateEcoDiscipline.YEAR_START_DESC_IN,
        'year_end': ClimateEcoDiscipline.YEAR_END_DESC_IN,
        'invest_mix': {'type': 'dataframe', 'unit': 'G$',
                       'dataframe_edition_locked': False,
                       'dataframe_descriptor': {'years': ('float', None, True),
                                                'electricity.SolarPv': ('float', None, True),
                                                'electricity.WindOnshore': ('float', None, True),
                                                'electricity.CoalGen': ('float', None, True),
                                                'methane.FossilGas': ('float', None, True),
                                                'methane.UpgradingBiogas': ('float', None, True),
                                                'hydrogen.gaseous_hydrogen.WaterGasShift': ('float', None, True),
                                                'hydrogen.gaseous_hydrogen.Electrolysis.AWE': ('float', None, True),
                                                'carbon_capture.direct_air_capture.AmineScrubbing': (
                                                'float', None, True),
                                                'carbon_capture.flue_gas_capture.CalciumLooping': ('float', None, True),
                                                'carbon_storage.DeepSalineFormation': ('float', None, True),
                                                'carbon_storage.GeologicMineralization': ('float', None, True),
                                                'methane.Methanation': ('float', None, True),
                                                'hydrogen.gaseous_hydrogen.PlasmaCracking': ('float', None, True),
                                                'hydrogen.gaseous_hydrogen.Electrolysis.SOEC': ('float', None, True),
                                                'hydrogen.gaseous_hydrogen.Electrolysis.PEM': ('float', None, True),
                                                'heat.hightemperatureheat.NaturalGasBoilerHighHeat': ('float', None, True),
                                                'heat.hightemperatureheat.ElectricBoilerHighHeat': ('float', None, True),
                                                'heat.hightemperatureheat.HeatPumpHighHeat': ('float', None, True),
                                                'heat.hightemperatureheat.GeothermalHighHeat': ('float', None, True),
                                                'heat.hightemperatureheat.CHPHighHeat': ('float', None, True),
                                                'heat.hightemperatureheat.HydrogenBoilerHighHeat': ('float', None, True),
                                                'heat.lowtemperatureheat.NaturalGasBoilerLowHeat': ('float', None, True),
                                                'heat.lowtemperatureheat.ElectricBoilerLowHeat': ('float', None, True),
                                                'heat.lowtemperatureheat.HeatPumpLowHeat': ('float', None, True),
                                                'heat.lowtemperatureheat.GeothermalLowHeat': ('float', None, True),
                                                'heat.lowtemperatureheat.CHPLowHeat': ('float', None, True),
                                                'heat.lowtemperatureheat.HydrogenBoilerLowHeat': ('float', None, True),
                                                'heat.mediumtemperatureheat.NaturalGasBoilerMediumHeat': ('float', None, True),
                                                'heat.mediumtemperatureheat.ElectricBoilerMediumHeat': ('float', None, True),
                                                'heat.mediumtemperatureheat.HeatPumpMediumHeat': ('float', None, True),
                                                'heat.mediumtemperatureheat.GeothermalMediumHeat': ('float', None, True),
                                                'heat.mediumtemperatureheat.CHPMediumHeat': ('float', None, True),
                                                'heat.mediumtemperatureheat.HydrogenBoilerMediumHeat': ('float', None, True),
                                                'biogas.AnaerobicDigestion': ('float', None, True),
                                                'syngas.BiomassGasification': ('float', None, True),
                                                'syngas.SMR': ('float', None, True),
                                                'syngas.Pyrolysis': ('float', None, True),
                                                'syngas.AutothermalReforming': ('float', None, True),
                                                'syngas.CoElectrolysis': ('float', None, True),
                                                'syngas.CoalGasification': ('float', None, True),
                                                'fuel.liquid_fuel.Refinery': ('float', None, True),
                                                'fuel.liquid_fuel.FischerTropsch': ('float', None, True),
                                                'fuel.hydrotreated_oil_fuel.HefaDecarboxylation': ('float', None, True),
                                                'fuel.hydrotreated_oil_fuel.HefaDeoxygenation': ('float', None, True),
                                                'solid_fuel.CoalExtraction': ('float', None, True),
                                                'solid_fuel.Pelletizing': ('float', None, True),
                                                'electricity.WindOffshore': ('float', None, True),
                                                'electricity.SolarThermal': ('float', None, True),
                                                'electricity.Geothermal': ('float', None, True),
                                                'electricity.Hydropower': ('float', None, True),
                                                'electricity.Nuclear': ('float', None, True),
                                                'electricity.CombinedCycleGasTurbine': ('float', None, True),
                                                'electricity.GasTurbine': ('float', None, True),
                                                'electricity.BiogasFired': ('float', None, True),
                                                'electricity.BiomassFired': ('float', None, True),
                                                'electricity.OilGen': ('float', None, True),
                                                'fuel.biodiesel.Transesterification': ('float', None, True),
                                                'fuel.ethanol.BiomassFermentation': ('float', None, True),
                                                'hydrogen.liquid_hydrogen.HydrogenLiquefaction': ('float', None, True),
                                                'carbon_capture.direct_air_capture.CalciumPotassiumScrubbing': (
                                                'float', None, True),
                                                'carbon_capture.flue_gas_capture.ChilledAmmoniaProcess': (
                                                'float', None, True),
                                                'carbon_capture.flue_gas_capture.CO2Membranes': ('float', None, True),
                                                'carbon_capture.flue_gas_capture.MonoEthanolAmine': (
                                                'float', None, True),
                                                'carbon_capture.flue_gas_capture.PiperazineProcess': (
                                                'float', None, True),
                                                'carbon_capture.flue_gas_capture.PressureSwingAdsorption': (
                                                'float', None, True),
                                                'carbon_storage.BiomassBuryingFossilization': ('float', None, True),
                                                'carbon_storage.DeepOceanInjection': ('float', None, True),
                                                'carbon_storage.DepletedOilGas': ('float', None, True),
                                                'carbon_storage.EnhancedOilRecovery': ('float', None, True),
                                                'carbon_storage.PureCarbonSolidStorage': ('float', None, True),
                                                'renewable.RenewableSimpleTechno': ('float', None, True),
                                                'fossil.FossilSimpleTechno': ('float', None, True),
                                                'carbon_capture.direct_air_capture.DirectAirCaptureTechno' : ('float', None, True),
                                                'carbon_capture.flue_gas_capture.FlueGasTechno': ('float', None, True),
                                                'carbon_storage.CarbonStorageTechno': ('float', None, True),
                                                }},
        'energy_list': {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                        'possible_values': EnergyMix.energy_list,
                        'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy_study',
                        'editable': False, 'structuring': True},
        'ccs_list': {'type': 'list', 'subtype_descriptor': {'list': 'string'}, 'possible_values': CCUS.ccs_list,
                     'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy_study', 'editable': False,
                     'structuring': True},
        'forest_investment': {'type': 'dataframe', 'unit': 'G$', 'visibility': 'Shared',
                              'dataframe_descriptor': {'years': ('float', None, False),
                                                       'forest_investment': ('float', None, False)}, 'namespace': 'ns_invest',
                              'dataframe_edition_locked': False},
    }

    energy_name = "one_invest"

    DESC_OUT = {
        GlossaryCore.EnergyInvestmentsWoTaxValue: GlossaryCore.EnergyInvestmentsWoTax,
        GlossaryCore.EnergyInvestmentsMinimizationObjective: {'type': 'array', 'unit': '-',
                                                  'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                  'namespace': 'ns_functions'},
    }
    _maturity = 'Research'

    def init_execution(self):
        self.independent_invest_model = IndependentInvest()

    def setup_sos_disciplines(self):
        '''
        Construct the desc_out to couple energy invest levels to techno_invest_disc
        '''
        dynamic_outputs = {}
        dynamic_inputs = {}

        if 'energy_list' in self.get_data_in():
            energy_list = self.get_sosdisc_inputs('energy_list')
            if energy_list is not None:
                for energy in energy_list:
                    if energy == BiomassDry.name:
                        dynamic_inputs['managed_wood_investment'] = {
                            'type': 'dataframe', 'unit': 'G$', 'visibility': 'Shared',
                            'dataframe_descriptor': {'years': ('float', None, False),
                                                     'investment': ('float', None, False)},
                            'namespace': 'ns_forest', 'dataframe_edition_locked': False,}
                        dynamic_inputs['deforestation_investment'] = {
                            'type': 'dataframe', 'unit': 'G$', 'visibility': 'Shared',
                            'dataframe_descriptor': {'years': ('float', None, False),
                                                     'investment': ('float', None, False)},
                            'namespace': 'ns_forest', 'dataframe_edition_locked': False}
                        dynamic_inputs['crop_investment'] = {
                            'type': 'dataframe', 'unit': 'G$', 'visibility': 'Shared',
                            'dataframe_descriptor': {'years': ('float', None, False),
                                                     'investment': ('float', None, False)},
                            'namespace': 'ns_crop', 'dataframe_edition_locked': False}
                    else:
                        # Add technologies_list to inputs
                        dynamic_inputs[f'{energy}.technologies_list'] = {
                            'type': 'list', 'subtype_descriptor': {'list': 'string'}, 'structuring': True,
                            'visibility': 'Shared', 'namespace': 'ns_energy',
                            'possible_values': EnergyMix.stream_class_dict[energy].default_techno_list,
                            'default': EnergyMix.stream_class_dict[energy].default_techno_list}
                        # Add all invest_level outputs
                        if f'{energy}.technologies_list' in self.get_data_in():
                            technology_list = self.get_sosdisc_inputs(
                                f'{energy}.technologies_list')
                            if technology_list is not None:
                                for techno in technology_list:
                                    dynamic_outputs[f'{energy}.{techno}.invest_level'] = {
                                        'type': 'dataframe', 'unit': 'G$',
                                        'visibility': 'Shared', 'namespace': 'ns_energy'}

        if 'ccs_list' in self.get_data_in():
            ccs_list = self.get_sosdisc_inputs('ccs_list')
            if ccs_list is not None:
                for ccs in ccs_list:
                    # Add technologies_list to inputs
                    dynamic_inputs[f'{ccs}.technologies_list'] = {
                        'type': 'list', 'subtype_descriptor': {'list': 'string'}, 'structuring': True,
                        'visibility': 'Shared', 'namespace': 'ns_ccs',
                        'possible_values': EnergyMix.stream_class_dict[ccs].default_techno_list}
                    # Add all invest_level outputs
                    if f'{ccs}.technologies_list' in self.get_data_in():
                        technology_list = self.get_sosdisc_inputs(
                            f'{ccs}.technologies_list')
                        if technology_list is not None:
                            for techno in technology_list:
                                dynamic_outputs[f'{ccs}.{techno}.invest_level'] = {
                                    'type': 'dataframe', 'unit': 'G$', 'visibility': 'Shared', 'namespace': 'ns_ccs'}

        self.add_inputs(dynamic_inputs)
        self.add_outputs(dynamic_outputs)

    def run(self):

        input_dict = self.get_sosdisc_inputs()

        energy_investment_wo_tax, energy_invest_objective = self.independent_invest_model.compute(
            input_dict)

        output_dict = {GlossaryCore.EnergyInvestmentsWoTaxValue: energy_investment_wo_tax,
                       GlossaryCore.EnergyInvestmentsMinimizationObjective: energy_invest_objective, }

        for energy in input_dict['energy_list'] + input_dict['ccs_list']:
            if energy == BiomassDry.name:
                pass
            else:
                for techno in input_dict[f'{energy}.technologies_list']:
                    output_dict[f'{energy}.{techno}.invest_level'] = pd.DataFrame(
                        {'years': input_dict['invest_mix']['years'].values,
                         'invest': input_dict['invest_mix'][f'{energy}.{techno}'].values})

        self.store_sos_outputs_values(output_dict)

    def compute_sos_jacobian(self):
        inputs_dict = self.get_sosdisc_inputs()

        years = np.arange(inputs_dict['year_start'],
                          inputs_dict['year_end'] + 1)

        delta_years = len(years)
        identity = np.identity(delta_years)
        ones = np.ones(delta_years)

        for techno in self.independent_invest_model.distribution_list:
            self.set_partial_derivative_for_other_types(
                (GlossaryCore.EnergyInvestmentsWoTaxValue, GlossaryCore.EnergyInvestmentsWoTaxValue),
                ('invest_mix', techno),
                identity * 1e-3)

            self.set_partial_derivative_for_other_types(
                (GlossaryCore.EnergyInvestmentsMinimizationObjective,),
                ('invest_mix', techno),
                ones * 1e-3)

            self.set_partial_derivative_for_other_types(
                (f'{techno}.invest_level', 'invest'),
                ('invest_mix', techno),
                np.identity(len(years)))

        self.set_partial_derivative_for_other_types(
            (GlossaryCore.EnergyInvestmentsWoTaxValue, GlossaryCore.EnergyInvestmentsWoTaxValue),
            ('forest_investment', 'forest_investment'),
            identity * 1e-3)

        self.set_partial_derivative_for_other_types(
            (GlossaryCore.EnergyInvestmentsMinimizationObjective,),
            ('forest_investment', 'forest_investment'),
            ones * 1e-3)

        energy_list = inputs_dict['energy_list']
        if BiomassDry.name in energy_list:
            for techno in ['managed_wood_investment', 'deforestation_investment', 'crop_investment']:
                self.set_partial_derivative_for_other_types(
                    (GlossaryCore.EnergyInvestmentsWoTaxValue, GlossaryCore.EnergyInvestmentsWoTaxValue),
                    (techno, 'investment'),
                    identity * 1e-3)

                self.set_partial_derivative_for_other_types(
                    (GlossaryCore.EnergyInvestmentsMinimizationObjective,),
                    (techno, 'investment'),
                    ones * 1e-3)

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

        if 'Invest Distribution' in charts:
            techno_invests = self.get_sosdisc_inputs(
                'invest_mix')

            chart_name = f'Distribution of investments on each energy vs years'

            new_chart_energy = TwoAxesInstanciatedChart('years', 'Invest [G$]',
                                                        chart_name=chart_name, stacked_bar=True)
            energy_list = self.get_sosdisc_inputs('energy_list')
            ccs_list = self.get_sosdisc_inputs('ccs_list')
            for energy in energy_list + ccs_list:
                techno_list = [
                    col for col in techno_invests.columns if col.startswith(f'{energy}.')]
                short_df = techno_invests[techno_list]
                chart_name = f'Distribution of investments for {energy} vs years'
                new_chart_techno = TwoAxesInstanciatedChart('years', 'Invest [G$]',
                                                            chart_name=chart_name, stacked_bar=True)

                for techno in techno_list:
                    serie = InstanciatedSeries(
                        techno_invests['years'].values.tolist(),
                        short_df[techno].values.tolist(), techno, 'bar')

                    new_chart_techno.series.append(serie)
                instanciated_charts.append(new_chart_techno)
                invest = short_df.sum(axis=1).values
                # Add total price
                serie = InstanciatedSeries(
                    techno_invests['years'].values.tolist(),
                    invest.tolist(), energy, 'bar')

                new_chart_energy.series.append(serie)

            forest_investment = self.get_sosdisc_inputs('forest_investment')
            chart_name = f'Distribution of reforestation investments vs years'
            agriculture_chart = TwoAxesInstanciatedChart('years', 'Invest [G$]',
                                                         chart_name=chart_name, stacked_bar=True)
            serie_agriculture = InstanciatedSeries(
                forest_investment['years'].values.tolist(),
                forest_investment['forest_investment'].values.tolist(), 'Reforestation', 'bar')
            agriculture_chart.series.append(serie_agriculture)
            instanciated_charts.append(agriculture_chart)
            serie = InstanciatedSeries(
                forest_investment['years'].values.tolist(),
                forest_investment['forest_investment'].tolist(), 'Reforestation', 'bar')

            new_chart_energy.series.append(serie)

            if BiomassDry.name in energy_list:
                chart_name = f'Distribution of agriculture sector investments vs years'
                agriculture_chart = TwoAxesInstanciatedChart('years', 'Invest [G$]',
                                                             chart_name=chart_name, stacked_bar=True)

                for techno in ['managed_wood_investment', 'deforestation_investment', 'crop_investment']:
                    invest = self.get_sosdisc_inputs(techno)
                    serie_agriculture = InstanciatedSeries(
                        invest['years'].values.tolist(),
                        invest['investment'].values.tolist(), techno.replace("_investment", ""), 'bar')
                    agriculture_chart.series.append(serie_agriculture)
                    serie = InstanciatedSeries(
                        invest['years'].values.tolist(),
                        invest['investment'].tolist(), techno.replace("_investment", ""), 'bar')
                    new_chart_energy.series.append(serie)
                instanciated_charts.append(agriculture_chart)
                instanciated_charts.insert(0, new_chart_energy)

            instanciated_charts.insert(0, new_chart_energy)

        return instanciated_charts
