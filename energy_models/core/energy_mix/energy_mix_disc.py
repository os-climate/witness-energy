'''
Copyright 2022 Airbus SAS
Modifications on 2023/04/19-2024/06/24 Copyright 2023 Capgemini

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
from sostrades_optimization_plugins.models.autodifferentiated_discipline import (
    AutodifferentiedDisc,
)

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.glossaryenergy import GlossaryEnergy


class Energy_Mix_Discipline(AutodifferentiedDisc):
    # ontology information
    _ontology_data = {
        'label': 'Energy Mix Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': "fa-solid fa-bolt",
        'version': '',
    }
    # All values used to calibrate heat loss percentage
    heat_tfc_2019 = 3561.87
    # + heat losses for transmission,distrib and transport
    heat_use_energy_2019 = 14181. + 232.59
    total_raw_prod_2019 = 183316.
    # total_losses_2019 = 2654.
    heat_losses_percentage_default = (heat_use_energy_2019 - heat_tfc_2019) / total_raw_prod_2019 * 100

    DESC_IN = {GlossaryEnergy.energy_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                                            'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy_study',
                                            'editable': False, 'structuring': True},
               GlossaryEnergy.YearStart: ClimateEcoDiscipline.YEAR_START_DESC_IN,
               GlossaryEnergy.YearEnd: GlossaryEnergy.YearEndVar,
               GlossaryEnergy.TargetEnergyProductionValue: GlossaryEnergy.TargetEnergyProductionDf,
               GlossaryEnergy.CO2Taxes['var_name']: GlossaryEnergy.CO2Taxes,
               'heat_losses_percentage': {'type': 'float', 'default': heat_losses_percentage_default, 'unit': '%',
                                          'range': [0., 100.]}, }

    DESC_OUT = {
        GlossaryEnergy.EnergyPricesValue: {'type': 'dataframe', 'unit': '$/MWh'},
        GlossaryEnergy.TargetProductionConstraintValue: GlossaryEnergy.TargetProductionConstraint,
        'co2_emissions_by_energy': {'type': 'dataframe', 'unit': 'Mt', 'description': 'co2 emissions of each energy'},
        'energy_CO2_emissions': {'type': 'dataframe', 'unit': 'Mt', 'description': 'Total CO2 emissions of energy sector'},
        'energy_production_brut': {'type': 'dataframe', 'unit': 'TWh', AutodifferentiedDisc.GRADIENTS: True},
        'energy_production_brut_detailed': {'type': 'dataframe', 'unit': 'TWh'},
        'net_energy_production_details': {'type': 'dataframe', 'unit': 'TWh', 'description': 'net energy production for each energy'},
        'net_energy_production': {'type': 'dataframe', 'unit': 'TWh', 'description': 'Total net energy production of energy sector'},
        'demands_df': {'type': 'dataframe', 'unit': 'TWh', 'description': 'Total demand from energy sector for each stream'},
        'energy_consumption': {'type': 'dataframe', 'unit': 'TWh'},
        'energy_mix': {'type': 'dataframe', 'unit': '%'},
        'land_demand_df': {'type': 'dataframe', 'unit': 'Gha', AutodifferentiedDisc.GRADIENTS: True},
        GlossaryEnergy.EnergyMeanPriceValue: GlossaryEnergy.EnergyMeanPrice,
        GlossaryEnergy.EnergyCapitalDfValue: GlossaryEnergy.EnergyCapitalDf,
        GlossaryEnergy.AllStreamsDemandRatioValue: GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.AllStreamsDemandRatio)
    }

    def __init__(self, sos_name, logger: logging.Logger):
        super().__init__(sos_name, logger)
        self.model = None

    def init_execution(self):
        self.model = EnergyMix('EnergyMix', self.logger)

    def setup_sos_disciplines(self):
        dynamic_inputs = {}
        dynamic_outputs = {}
        values_dict, go = self.collect_var_for_dynamic_setup([GlossaryEnergy.YearStart, GlossaryEnergy.YearEnd])
        if go:
            years = np.arange(values_dict[GlossaryEnergy.YearStart], values_dict[GlossaryEnergy.YearEnd] + 1)
            default_target_energy_production = pd.DataFrame({
                GlossaryEnergy.Years: years,
                GlossaryEnergy.TargetEnergyProductionValue: np.zeros_like(years)})
            self.set_dynamic_default_values(
                {GlossaryEnergy.TargetEnergyProductionValue: default_target_energy_production})
        values_dict, go = self.collect_var_for_dynamic_setup([GlossaryEnergy.energy_list])

        if go:
            for energy in values_dict[GlossaryEnergy.energy_list]:
                # consumptions :
                dynamic_inputs[f"{energy}.{GlossaryEnergy.StreamEnergyConsumptionValue}"] = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.StreamEnergyConsumption)
                dynamic_inputs[f"{energy}.{GlossaryEnergy.StreamResourceConsumptionValue}"] = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.StreamResourceConsumption)
                # demands :
                dynamic_inputs[f"{energy}.{GlossaryEnergy.StreamEnergyDemandValue}"] = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.StreamEnergyDemand)
                dynamic_inputs[f"{energy}.{GlossaryEnergy.StreamResourceDemandValue}"] = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.StreamResourceDemand)

                dynamic_inputs[f"{energy}.{GlossaryEnergy.StreamScope1GHGEmissionsValue}"] = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.StreamScope1GHGEmissions)

                dynamic_inputs[f'{energy}.{GlossaryEnergy.StreamProductionValue}'] = {'type': 'dataframe', 'unit': 'PWh', "dynamic_dataframe_columns": True}
                dynamic_inputs[f'{energy}.{GlossaryEnergy.EnergyPricesValue}'] = {'type': 'dataframe', 'unit': '$/MWh', "dynamic_dataframe_columns": True}
                dynamic_inputs[f'{energy}.{GlossaryEnergy.LandUseRequiredValue}'] = {'type': 'dataframe', 'unit': 'Gha', "dynamic_dataframe_columns": True}
                dynamic_inputs[f'{energy}.{GlossaryEnergy.EnergyTypeCapitalDfValue}'] = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.EnergyTypeCapitalDf)
                dynamic_inputs[f'{energy}.{GlossaryEnergy.CO2EmissionsValue}'] = {'type': 'dataframe', 'unit': 'kg/kWh', "dynamic_dataframe_columns": True}
                dynamic_inputs[f'{energy}.{GlossaryEnergy.CO2PerUse}'] = {
                    'type': 'dataframe', 'unit': 'kg/kWh',
                    'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                             GlossaryEnergy.CO2PerUse: ('float', None, True),},
                }

        self.add_inputs(dynamic_inputs)
        self.add_outputs(dynamic_outputs)

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = [
            'Production',
            'Price',
            'Emissions',
            'Demands',
            'Target energy production constraint',
            GlossaryEnergy.Capital]

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

        df_prod_brut = self.get_sosdisc_outputs('energy_production_brut')
        years = df_prod_brut[GlossaryEnergy.Years]
        if "Production" in charts:
            df_prod_net = self.get_sosdisc_outputs('net_energy_production')
            df_conso = self.get_sosdisc_outputs('energy_consumption')
            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Prices [TWh]', chart_name='Energy sector production')

            serie = InstanciatedSeries(years, df_prod_brut["Total"], 'Raw production', 'lines')
            new_chart.series.append(serie)

            serie = InstanciatedSeries(years, df_prod_net["Total"], 'Net production', 'lines')
            new_chart.series.append(serie)

            serie = InstanciatedSeries(years, - df_conso["Total"], 'Consumption', 'bar')
            new_chart.series.append(serie)

            new_chart.post_processing_section_name = "Production"
            instanciated_charts.append(new_chart)

        if "Production" in charts:
            df_prod_brut = self.get_sosdisc_outputs('energy_production_brut')
            df_prod_brut_details = self.get_sosdisc_outputs('energy_production_brut_detailed')
            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, '[TWh]', chart_name='Raw production breakdown', stacked_bar=True)
            for col in df_prod_brut_details.columns:
                if col != GlossaryEnergy.Years and col != "Total":
                    serie = InstanciatedSeries(years, df_prod_brut_details[col], col, 'bar')
                    new_chart.series.append(serie)

            serie = InstanciatedSeries(years, df_prod_brut["Total"], 'Total', 'lines')
            new_chart.series.append(serie)
            new_chart.post_processing_section_name = "Production"
            instanciated_charts.append(new_chart)

        if "Production" in charts:
            df_prod_net = self.get_sosdisc_outputs('net_energy_production')
            df_prod_net_details = self.get_sosdisc_outputs('net_energy_production_details')
            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, '[TWh]', chart_name='Net production breakdown', stacked_bar=True)
            for col in df_prod_net_details.columns:
                if col != GlossaryEnergy.Years and col != "Total":
                    serie = InstanciatedSeries(years, df_prod_net_details[col], col, 'bar')
                    new_chart.series.append(serie)

            serie = InstanciatedSeries(years, df_prod_net["Total"], 'Total', 'lines')
            new_chart.series.append(serie)
            new_chart.post_processing_section_name = "Production"
            instanciated_charts.append(new_chart)

        if "Production" in charts:
            df_consumption = self.get_sosdisc_outputs('energy_consumption')
            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, '[TWh]', chart_name='Energy consumption within the energy sector', stacked_bar=True)
            for col in df_consumption.columns:
                if col != GlossaryEnergy.Years and col != "Total":
                    serie = InstanciatedSeries(years, df_consumption[col], col, 'bar')
                    new_chart.series.append(serie)

            serie = InstanciatedSeries(years, df_consumption["Total"], 'Total', 'lines')
            new_chart.series.append(serie)
            new_chart.post_processing_section_name = "Production"
            instanciated_charts.append(new_chart)

        if "Production" in charts:
            df_energy_mix = self.get_sosdisc_outputs('energy_mix')
            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, '%', chart_name='Energy mix', stacked_bar=True)
            for col in df_energy_mix.columns:
                if col != GlossaryEnergy.Years:
                    serie = InstanciatedSeries(years, df_energy_mix[col], col, 'bar')
                    new_chart.series.append(serie)

            new_chart.post_processing_section_name = "Production"
            instanciated_charts.append(new_chart)


        if 'Target energy production constraint' in charts:
            target_energy_production_df = self.get_sosdisc_inputs(GlossaryEnergy.TargetEnergyProductionValue)
            target_energy_production = target_energy_production_df[GlossaryEnergy.TargetEnergyProductionValue]
            years = target_energy_production_df[GlossaryEnergy.Years]
            if target_energy_production.max() > 0:
                chart_target_energy_production = TwoAxesInstanciatedChart(GlossaryEnergy.Years, GlossaryEnergy.TargetEnergyProductionDf['unit'],
                                                            chart_name=GlossaryEnergy.TargetProductionConstraintValue,
                                                            stacked_bar=True)

                serie_target_energy_production = InstanciatedSeries(list(years), list(target_energy_production), 'Minimal energy production required',
                                                      'dash_lines')
                chart_target_energy_production.add_series(serie_target_energy_production)

                energy_production = self.get_sosdisc_outputs('net_energy_production')["Total"]
                serie_production = InstanciatedSeries(list(years), list(energy_production), "Energy production",
                                                   'bar')
                chart_target_energy_production.add_series(serie_production)
                chart_target_energy_production.post_processing_section_name = "Production"
                instanciated_charts.append(chart_target_energy_production)


        if "Price" in charts:
            df_price = self.get_sosdisc_outputs(GlossaryEnergy.EnergyPricesValue)
            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, '$/MWh', chart_name='Energy prices')
            for col in df_price.columns:
                if col != GlossaryEnergy.Years:
                    serie = InstanciatedSeries(years, df_price[col], col, 'lines')
                    new_chart.series.append(serie)

            new_chart.post_processing_section_name = "Price"
            instanciated_charts.append(new_chart)

        if 'Price' in charts:
            new_chart = self.get_chart_energy_mean_price_in_dollar_mwh()
            if new_chart is not None:
                new_chart.post_processing_section_name = "Price"
                instanciated_charts.append(new_chart)

        if "Emissions" in charts:
            df_emissions_by_energy = self.get_sosdisc_outputs("co2_emissions_by_energy")
            df_emissions_co2_total = self.get_sosdisc_outputs("energy_CO2_emissions")
            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Gt', chart_name='CO2 emissions', stacked_bar=True)
            for col in df_emissions_by_energy.columns:
                if col != GlossaryEnergy.Years:
                    serie = InstanciatedSeries(years, df_emissions_by_energy[col], col, 'bar')
                    new_chart.series.append(serie)

            serie = InstanciatedSeries(years, df_emissions_co2_total["Total"], "Total", 'lines')
            new_chart.series.append(serie)

            new_chart.post_processing_section_name= "Emissions"
            instanciated_charts.append(new_chart)

        if "Emissions" in charts:
            df_emissions_by_energy = self.get_sosdisc_outputs("co2_emissions_by_energy")
            df_emissions_co2_total = self.get_sosdisc_outputs("energy_CO2_emissions")
            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, '%', chart_name='CO2 emissions share', stacked_bar=True)
            for col in df_emissions_by_energy.columns:
                if col != GlossaryEnergy.Years:
                    serie = InstanciatedSeries(years, df_emissions_by_energy[col] / df_emissions_co2_total["Total"] * 100., col, 'bar' )
                    new_chart.series.append(serie)

            new_chart.post_processing_section_name = "Emissions"
            instanciated_charts.append(new_chart)

        if "Demands" in charts:
            df_demands_ratio = self.get_sosdisc_outputs(GlossaryEnergy.AllStreamsDemandRatioValue)
            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, '%', chart_name='Demands satisfaction level')
            for col in df_demands_ratio.columns:
                if col != GlossaryEnergy.Years:
                    serie = InstanciatedSeries(years, df_demands_ratio[col] * 100., col, 'lines' )
                    new_chart.series.append(serie)

            new_chart.post_processing_section_name = "Demands"
            instanciated_charts.append(new_chart)

        if "Demands" in charts:
            df_demands = self.get_sosdisc_outputs("demands_df")
            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'TWh', chart_name='Demands for each energy within the energy sector', stacked_bar=True)
            for col in df_demands.columns:
                if col != GlossaryEnergy.Years:
                    serie = InstanciatedSeries(years, df_demands[col], col, 'bar' )
                    new_chart.series.append(serie)

            new_chart.post_processing_section_name = "Demands"
            instanciated_charts.append(new_chart)

        if GlossaryEnergy.Capital in charts:
            new_chart = self.get_chart_capital()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_chart_energy_mean_price_in_dollar_mwh(self):
        energy_mean_price = self.get_sosdisc_outputs(GlossaryEnergy.EnergyMeanPriceValue)

        chart_name = 'Mean price out of energy mix'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'Prices [$/MWh]', chart_name=chart_name)

        serie = InstanciatedSeries(
            energy_mean_price[GlossaryEnergy.Years],
            energy_mean_price[GlossaryEnergy.EnergyPriceValue], 'mean energy', 'lines')
        new_chart.series.append(serie)

        return new_chart

    def get_chart_capital(self):
        capital_df = self.get_sosdisc_outputs(GlossaryEnergy.EnergyCapitalDfValue)

        chart_name = 'Capital'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, f"[{GlossaryEnergy.EnergyCapitalDf['unit']}]", chart_name=chart_name)

        serie = InstanciatedSeries(
            capital_df[GlossaryEnergy.Years],
            capital_df[GlossaryEnergy.Capital], 'Capital', 'lines')
        new_chart.series.append(serie)

        serie = InstanciatedSeries(
            capital_df[GlossaryEnergy.Years],
            capital_df[GlossaryEnergy.NonUseCapital], 'Non used capital (Utilisation ratio or limiting ratio)', 'bar')
        new_chart.series.append(serie)
        new_chart.post_processing_section_name = "Capital"
        return new_chart
