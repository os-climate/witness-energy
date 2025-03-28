'''
Copyright 2022 Airbus SAS
Modifications on 2023/04/19-2025/01/23 Copyright 2025 Capgemini

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
import re
from typing import Union

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
from sostrades_optimization_plugins.tools.plot_tools.colormaps import (
    available_colormaps,
)
from sostrades_optimization_plugins.tools.plot_tools.plot_factories import (
    create_sankey_with_slider,
)
from sostrades_optimization_plugins.tools.plot_tools.plotting import (
    InstantiatedPlotlyNativeChart,
)

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.glossaryenergy import GlossaryEnergy


class Energy_Mix_Discipline(AutodifferentiedDisc):
    # ontology information
    _ontology_data = {
        "label": "Energy Mix Model",
        "type": "Research",
        "source": "SoSTrades Project",
        "validated": "",
        "validated_by": "SoSTrades Project",
        "last_modification_date": "",
        "category": "",
        "definition": "",
        "icon": "fa-solid fa-bolt",
        "version": "",
    }
    # All values used to calibrate heat loss percentage
    heat_tfc_2019 = 3561.87
    # + heat losses for transmission,distrib and transport
    heat_use_energy_2019 = 14181.0 + 232.59
    total_raw_prod_2019 = 183316.0
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
        GlossaryEnergy.StreamPricesValue: GlossaryEnergy.StreamPrices,
        GlossaryEnergy.TargetProductionConstraintValue: GlossaryEnergy.TargetProductionConstraint,
        GlossaryEnergy.EnergyMixRawProductionValue: GlossaryEnergy.EnergyMixRawProduction,
        GlossaryEnergy.EnergyMixNetProductionsDfValue: GlossaryEnergy.EnergyMixNetProductionsDf,
        GlossaryEnergy.EnergyMixEnergiesDemandsDfValue: GlossaryEnergy.EnergyMixEnergiesDemandsDf,
        GlossaryEnergy.EnergyMixEnergiesConsumptionDfValue: GlossaryEnergy.EnergyMixEnergiesConsumptionDf,
        GlossaryEnergy.EnergyMixCCSDemandsDfValue: GlossaryEnergy.EnergyMixCCSDemandsDf,
        GlossaryEnergy.EnergyMixCCSConsumptionDfValue: GlossaryEnergy.EnergyMixCCSConsumptionDf,
        'energy_mix': {'type': 'dataframe', 'unit': '%'},
        'land_demand_df': {'type': 'dataframe', 'unit': 'Gha', AutodifferentiedDisc.GRADIENTS: True},
        GlossaryEnergy.EnergyMeanPriceValue: GlossaryEnergy.EnergyMeanPrice,
        GlossaryEnergy.EnergyMixCapitalDfValue: GlossaryEnergy.EnergyMixCapitalDf,
        GlossaryEnergy.AllStreamsDemandRatioValue: GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.AllStreamsDemandRatio),
        GlossaryEnergy.GHGEnergyEmissionsDfValue: GlossaryEnergy.GHGEnergyEmissionsDf
    }
    for ghg in GlossaryEnergy.GreenHouseGases:
        DESC_OUT.update({f'{ghg}_emissions_by_energy': {'type': 'dataframe', 'unit': 'Gt', 'description': f'{ghg} emissions of each energy'},})
        DESC_OUT.update({f'{ghg}_intensity_by_energy': GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.GHGIntensityEnergies),})

    def __init__(self, sos_name, logger):
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
                dynamic_inputs[f"{energy}.{GlossaryEnergy.StreamCCSConsumptionValue}"] = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.StreamCCSConsumption)
                # demands :
                dynamic_inputs[f"{energy}.{GlossaryEnergy.StreamEnergyDemandValue}"] = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.StreamEnergyDemand)
                dynamic_inputs[f"{energy}.{GlossaryEnergy.StreamResourceDemandValue}"] = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.StreamResourceDemand)
                dynamic_inputs[f"{energy}.{GlossaryEnergy.StreamCCSDemandValue}"] = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.StreamCCSDemand)

                dynamic_inputs[f"{energy}.{GlossaryEnergy.StreamScope1GHGIntensityValue}"] = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.StreamScope1GHGIntensity)
                dynamic_inputs[f"{energy}.{GlossaryEnergy.StreamScope1GHGEmissionsValue}"] = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.StreamScope1GHGEmissions)

                dynamic_inputs[f'{energy}.{GlossaryEnergy.StreamProductionValue}'] = GlossaryEnergy.StreamProductionDf
                dynamic_inputs[f'{energy}.{GlossaryEnergy.StreamPricesValue}'] = {'type': 'dataframe', 'unit': '$/MWh', "dynamic_dataframe_columns": True}
                dynamic_inputs[f'{energy}.{GlossaryEnergy.LandUseRequiredValue}'] = GlossaryEnergy.StreamLandUseDf
                dynamic_inputs[f'{energy}.{GlossaryEnergy.EnergyTypeCapitalDfValue}'] = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.EnergyTypeCapitalDf)

        self.add_inputs(dynamic_inputs)
        self.add_outputs(dynamic_outputs)

    def get_chart_filter_list(self):
        chart_filters = []
        chart_list = [
            'Production',
            'Price',
            'Emissions',
            'Emissions intensities',
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
                if chart_filter.filter_key == "charts":
                    charts = chart_filter.selected_values

        df_prod_brut = self.get_sosdisc_outputs(GlossaryEnergy.EnergyMixRawProductionValue)
        years = df_prod_brut[GlossaryEnergy.Years]
        if "Production" in charts:
            df_prod_net = self.get_sosdisc_outputs(GlossaryEnergy.EnergyMixNetProductionsDfValue)
            df_conso = self.get_sosdisc_outputs(GlossaryEnergy.EnergyMixEnergiesConsumptionDfValue)
            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'PWh', chart_name='Energy sector production')

            serie = InstanciatedSeries(years, df_prod_brut["Total"], 'Raw production', 'lines')
            new_chart.series.append(serie)

            serie = InstanciatedSeries(years, df_prod_net["Total"], 'Net production', 'lines')
            new_chart.series.append(serie)

            serie = InstanciatedSeries(years, - df_conso["Total"], 'Consumption', 'bar')
            new_chart.series.append(serie)

            new_chart.post_processing_section_name = "Production"
            new_chart.post_processing_is_key_chart = True
            instanciated_charts.append(new_chart)

        if "Production" in charts:
            df_prod_brut = self.get_sosdisc_outputs(GlossaryEnergy.EnergyMixRawProductionValue)
            df_prod_brut_details = self.get_sosdisc_outputs(GlossaryEnergy.EnergyMixRawProductionValue)
            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, GlossaryEnergy.EnergyMixRawProduction['unit'], chart_name='Raw production breakdown', stacked_bar=True)
            for col in df_prod_brut_details.columns:
                if col != GlossaryEnergy.Years and col != "Total":
                    serie = InstanciatedSeries(years, df_prod_brut_details[col], self.pimp_string(col), 'bar')
                    new_chart.series.append(serie)

            serie = InstanciatedSeries(years, df_prod_brut["Total"], 'Total', 'lines')
            new_chart.series.append(serie)
            new_chart.post_processing_section_name = "Production"
            new_chart.post_processing_is_key_chart = True
            instanciated_charts.append(new_chart)

        if "Production" in charts:
            df_prod_net_details = self.get_sosdisc_outputs(GlossaryEnergy.EnergyMixNetProductionsDfValue)
            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, GlossaryEnergy.EnergyMixNetProductionsDf['unit'], chart_name='Net production breakdown', stacked_bar=True)
            for col in df_prod_net_details.columns:
                if col != GlossaryEnergy.Years and col != "Total":
                    serie = InstanciatedSeries(years, df_prod_net_details[col], self.pimp_string(col), 'bar')
                    new_chart.series.append(serie)

            serie = InstanciatedSeries(years, df_prod_net_details["Total"], 'Total', 'lines')
            new_chart.series.append(serie)
            new_chart.post_processing_section_name = "Production"
            new_chart.post_processing_is_key_chart = True
            instanciated_charts.append(new_chart)

        if "Production" in charts:
            df_consumption = self.get_sosdisc_outputs(GlossaryEnergy.EnergyMixEnergiesConsumptionDfValue)
            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years,
                                                 GlossaryEnergy.EnergyMixEnergiesConsumptionDf['unit'],
                                                 chart_name='Energy consumption within the energy sector', stacked_bar=True)
            for col in df_consumption.columns:
                if col != GlossaryEnergy.Years and col != "Total":
                    serie = InstanciatedSeries(years, df_consumption[col], self.pimp_string(col), 'bar')
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
                    serie = InstanciatedSeries(years, df_energy_mix[col], self.pimp_string(col), 'bar')
                    new_chart.series.append(serie)

            new_chart.post_processing_section_name = "Production"
            instanciated_charts.append(new_chart)


        if 'Target energy production constraint' in charts:
            target_energy_production_df = self.get_sosdisc_inputs(GlossaryEnergy.TargetEnergyProductionValue)
            target_energy_production = target_energy_production_df[GlossaryEnergy.TargetEnergyProductionValue]
            years = target_energy_production_df[GlossaryEnergy.Years]
            if target_energy_production.max() > 0:
                chart_target_energy_production = TwoAxesInstanciatedChart(
                    GlossaryEnergy.Years,
                    GlossaryEnergy.TargetEnergyProductionDf["unit"],
                    chart_name=GlossaryEnergy.TargetProductionConstraintValue,
                    stacked_bar=True,
                )

                serie_target_energy_production = InstanciatedSeries(
                    list(years),
                    list(target_energy_production),
                    "Minimal energy production required",
                    "dash_lines",
                )
                chart_target_energy_production.add_series(
                    serie_target_energy_production
                )

                energy_production = self.get_sosdisc_outputs(GlossaryEnergy.EnergyMixNetProductionsDfValue)["Total"]
                serie_production = InstanciatedSeries(list(years), list(energy_production), "Energy production", 'bar')
                chart_target_energy_production.add_series(serie_production)
                chart_target_energy_production.post_processing_section_name = "Production"
                instanciated_charts.append(chart_target_energy_production)


        if "Price" in charts:
            df_price = self.get_sosdisc_outputs(GlossaryEnergy.StreamPricesValue)
            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, '$/MWh', chart_name='Energy prices')
            for col in df_price.columns:
                if col != GlossaryEnergy.Years:
                    serie = InstanciatedSeries(years, df_price[col], self.pimp_string(col), 'lines')
                    new_chart.series.append(serie)

            new_chart.post_processing_section_name = "Price"
            instanciated_charts.append(new_chart)

        if 'Price' in charts:
            new_chart = self.get_chart_energy_mean_price_in_dollar_mwh()
            if new_chart is not None:
                new_chart.post_processing_section_name = "Price"
                instanciated_charts.append(new_chart)

        if "Emissions" in charts:
            instanciated_charts.extend(self.get_ghg_equivalent_charts())
            for ghg in GlossaryEnergy.GreenHouseGases:
                instanciated_charts.extend(self.get_ghg_charts(ghg))

        if 'Emissions intensities' in charts:
            for ghg in GlossaryEnergy.GreenHouseGases:
                instanciated_charts.extend(self.get_ghg_intensity_by_energy(ghg))

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
            df_demands = self.get_sosdisc_outputs(GlossaryEnergy.EnergyMixEnergiesDemandsDfValue)
            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, GlossaryEnergy.EnergyMixEnergiesDemandsDf['unit'], chart_name='Demands for each energy within the energy sector', stacked_bar=True)
            for col in df_demands.columns:
                if col != GlossaryEnergy.Years:
                    serie = InstanciatedSeries(years, df_demands[col], self.pimp_string(col), 'bar' )
                    new_chart.series.append(serie)

            new_chart.post_processing_section_name = "Demands"
            instanciated_charts.append(new_chart)

        if GlossaryEnergy.Capital in charts:
            new_chart = self.get_chart_capital()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_chart_energy_mean_price_in_dollar_mwh(self):
        energy_mean_price = self.get_sosdisc_outputs(
            GlossaryEnergy.EnergyMeanPriceValue
        )

        chart_name = "Mean price out of energy mix"
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, "Prices [$/MWh]", chart_name=chart_name
        )

        serie = InstanciatedSeries(
            energy_mean_price[GlossaryEnergy.Years],
            energy_mean_price[GlossaryEnergy.EnergyPriceValue], 'mean energy', 'lines')
        new_chart.series.append(serie)

        return new_chart

    def get_chart_capital(self):
        capital_df = self.get_sosdisc_outputs(GlossaryEnergy.EnergyMixCapitalDfValue)

        chart_name = "Capital"
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years,
            f"[{GlossaryEnergy.EnergyMixCapitalDf['unit']}]",
            chart_name=chart_name,
        )

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

    def get_chart_sankey_fluxes(
        self,
        chart_name="Energy Flow",
        streams_filter: Union[list, None] = None,
        normalized_links: bool = False,
        split_external: bool = False,
    ):
        """Create sankey chart correlating production and consumption of all actors in energy mix."""

        # Get list of energy technologies
        energy_list = self.get_sosdisc_inputs(GlossaryEnergy.EnergyListName)

        # Get dataframe that has Years column for sure
        target_energy_production_df = self.get_sosdisc_inputs(
            GlossaryEnergy.TargetEnergyProductionValue
        )
        years = list(target_energy_production_df[GlossaryEnergy.Years])

        # Initialize dictionary with all consumptions / productions
        energy_dictionary = {}

        # Get dataframes and put them in dictionary format
        for energy in energy_list:
            # Gets dataframes
            ns_energy = self.get_ns_stream(energy)
            consumption = self.get_sosdisc_inputs(
                f"{ns_energy}.{GlossaryEnergy.StreamConsumptionValue}"
            ).copy()
            production = self.get_sosdisc_inputs(
                f"{ns_energy}.{GlossaryEnergy.EnergyProductionValue}"
            ).copy()

            # Add Years to dataframes
            if GlossaryEnergy.Years not in consumption.columns:
                consumption[GlossaryEnergy.Years] = years

            if GlossaryEnergy.Years not in production.columns:
                production[GlossaryEnergy.Years] = years

            # Update dictionary
            energy_dictionary[energy] = {
                "input": consumption,
                "output": production,
            }

        # Get Net Production
        production = self.get_sosdisc_outputs(
            f"{GlossaryEnergy.StreamProductionDetailedValue}"
        ).copy()
        production.columns = [c.replace("production ", "") for c in production.columns]
        consumption = pd.DataFrame({GlossaryEnergy.Years: years})

        # Add Years to dataframes
        if GlossaryEnergy.Years not in production.columns:
            production[GlossaryEnergy.Years] = years

        # Switch prod /consumption as we want the node to "consume" the available streams
        energy_dictionary["available<br>for final consumption"] = {
            "input": production,
            "output": consumption,
        }

        # Get dataframe with negative productions to add as a source
        df_negative = production.copy()
        columns_to_process = [
            col for col in df_negative.columns if col != GlossaryEnergy.Years
        ]
        df_negative[columns_to_process] = df_negative[columns_to_process].where(
            df_negative[columns_to_process] < 0, 0
        )
        df_negative[columns_to_process] = df_negative[columns_to_process].abs()

        energy_dictionary["neg_balance"] = {
            "input": consumption,
            "output": df_negative,
        }

        # Filter out resources
        for dfs in energy_dictionary.values():
            dfs["input"] = dfs["input"][
                [c for c in dfs["input"].columns if "(Mt)" not in c]
            ]
            dfs["output"] = dfs["output"][
                [c for c in dfs["output"].columns if "(Mt)" not in c]
            ]

        # Remove units from all streams, to handle inconsistent naming
        for actor in energy_dictionary:
            energy_dictionary[actor]["input"].columns = [
                re.sub(r"\s*\([^)]*\)", "", c)
                for c in energy_dictionary[actor]["input"].columns
            ]
            energy_dictionary[actor]["output"].columns = [
                re.sub(r"\s*\([^)]*\)", "", c)
                for c in energy_dictionary[actor]["output"].columns
            ]

        # filter streams
        if streams_filter is not None:
            for dfs in energy_dictionary.values():
                existing_columns = list(set(streams_filter) & set(dfs["input"].columns))
                dfs["input"] = dfs["input"][[GlossaryEnergy.Years, *existing_columns]]
                existing_columns = list(
                    set(streams_filter) & set(dfs["output"].columns)
                )
                dfs["output"] = dfs["output"][[GlossaryEnergy.Years, *existing_columns]]

        # Create sankey plot
        colormap = available_colormaps["energy"]
        fig = create_sankey_with_slider(
            energy_dictionary,
            colormap=colormap,
            normalized_links=normalized_links,
            split_external=split_external,
            output_node="available<br>for final consumption",
        )

        # return chart
        return InstantiatedPlotlyNativeChart(fig, chart_name)

    def get_ghg_charts(self, ghg: str):
        instanciated_charts = []
        df_total_emissions = self.get_sosdisc_outputs(GlossaryEnergy.GHGEnergyEmissionsDfValue)
        years = df_total_emissions[GlossaryEnergy.Years]
        df_emissions_by_energy = self.get_sosdisc_outputs(f"{ghg}_emissions_by_energy")
        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, GlossaryEnergy.GHGEnergyEmissionsDf['unit'], chart_name=f'{ghg} breakdown by energy',
                                             stacked_bar=True)
        for col in df_emissions_by_energy.columns:
            if col != GlossaryEnergy.Years:
                serie = InstanciatedSeries(years, df_emissions_by_energy[col], self.pimp_string(col), 'bar')
                new_chart.series.append(serie)

        serie = InstanciatedSeries(years, df_total_emissions[ghg], f"Total {ghg} emissions of energy sector", 'lines')
        new_chart.series.append(serie)

        new_chart.post_processing_section_name = "Emissions"
        instanciated_charts.append(new_chart)

        # CO2 eq
        if ghg in [GlossaryEnergy.CH4, GlossaryEnergy.N2O]:
            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, GlossaryEnergy.GHGEnergyEmissionsDf['unit'] + 'CO2 eq',
                                                 chart_name=f'{ghg} breakdown by energy (CO2 eq, 100-year basis)',
                                                 stacked_bar=True)

            for col in df_emissions_by_energy.columns:
                if col != GlossaryEnergy.Years:
                    serie = InstanciatedSeries(years, df_emissions_by_energy[col] * ClimateEcoDiscipline.GWP_100_default[ghg], col, 'bar')
                    new_chart.series.append(serie)

            serie = InstanciatedSeries(years, df_total_emissions[ghg] * ClimateEcoDiscipline.GWP_100_default[ghg], f"Total {ghg} emissions of energy sector (CO2 equivalent, 100-year basis)",
                                       'lines')
            new_chart.series.append(serie)

            new_chart.post_processing_section_name = "Emissions"
            instanciated_charts.append(new_chart)
        return instanciated_charts

    def get_ghg_equivalent_charts(self,):
        instanciated_charts = []
        df_total_emissions = self.get_sosdisc_outputs(GlossaryEnergy.GHGEnergyEmissionsDfValue)
        years = df_total_emissions[GlossaryEnergy.Years]
        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, GlossaryEnergy.GHGEnergyEmissionsDf['unit'],
                                             chart_name='GHG emissions of energy sector (CO2 equivalent, 100-year basis)',
                                             stacked_bar=True)
        total = np.zeros_like(df_total_emissions[GlossaryEnergy.CO2])

        for ghg in GlossaryEnergy.GreenHouseGases:
            serie = InstanciatedSeries(years, df_total_emissions[ghg] * ClimateEcoDiscipline.GWP_100_default[ghg], ghg, 'bar')
            total += df_total_emissions[ghg] * ClimateEcoDiscipline.GWP_100_default[ghg]
            new_chart.series.append(serie)

        serie = InstanciatedSeries(years, total, "Total", 'lines')
        new_chart.series.append(serie)

        new_chart.post_processing_section_name = "Emissions"
        new_chart.post_processing_is_key_chart = True
        instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_ghg_intensity_by_energy(self, ghg: str):
        instanciated_charts = []
        df_emissions_intensity = self.get_sosdisc_outputs(f"{ghg}_intensity_by_energy")
        years = df_emissions_intensity[GlossaryEnergy.Years]
        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, GlossaryEnergy.GHGIntensityEnergies['unit'],
                                             chart_name=f'{ghg} emissions intensities of energies', y_min_zero=True)

        for col in df_emissions_intensity.columns:
            if col != GlossaryEnergy.Years:
                serie = InstanciatedSeries(years, df_emissions_intensity[col], self.pimp_string(col), 'lines')
                new_chart.series.append(serie)

        new_chart.post_processing_section_name = "Emissions intensities"
        instanciated_charts.append(new_chart)

        return instanciated_charts
