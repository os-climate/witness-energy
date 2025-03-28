'''
Copyright 2022 Airbus SAS
Modifications on 2023/03/27-2025/01/23 Copyright 2025 Capgemini

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
from __future__ import annotations

import re

import numpy as np
import pandas as pd
from climateeconomics.core.core_witness.climateeco_discipline import (
    ClimateEcoDiscipline,
)
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import (
    InstanciatedSeries,
    TwoAxesInstanciatedChart,
)
from sostrades_core.tools.post_processing.pie_charts.instanciated_pie_chart import (
    InstanciatedPieChart,
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

from energy_models.glossaryenergy import GlossaryEnergy


class StreamDiscipline(AutodifferentiedDisc):
    # ontology information
    _ontology_data = {
        "label": "Core Stream Type Model",
        "type": "Research",
        "source": "SoSTrades Project",
        "validated": "",
        "validated_by": "SoSTrades Project",
        "last_modification_date": "",
        "category": "",
        "definition": "",
        "icon": "",
        "version": "",
    }

    DESC_IN = {
        GlossaryEnergy.YearStart: ClimateEcoDiscipline.YEAR_START_DESC_IN,
        GlossaryEnergy.YearEnd: GlossaryEnergy.YearEndVar,
        GlossaryEnergy.techno_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'}, 'structuring': True, 'unit': '-'},
    }

    DESC_OUT = {
        GlossaryEnergy.StreamEnergyConsumptionValue: GlossaryEnergy.StreamEnergyConsumption,
        GlossaryEnergy.StreamResourceConsumptionValue: GlossaryEnergy.StreamResourceConsumption,
        GlossaryEnergy.StreamEnergyDemandValue: GlossaryEnergy.StreamEnergyDemand,
        GlossaryEnergy.StreamResourceDemandValue: GlossaryEnergy.StreamResourceDemand,
        GlossaryEnergy.StreamCCSDemandValue: GlossaryEnergy.StreamCCSDemand,
        GlossaryEnergy.StreamCCSConsumptionValue: GlossaryEnergy.StreamCCSConsumption,

        GlossaryEnergy.StreamProductionValue: GlossaryEnergy.StreamProductionDf,
        GlossaryEnergy.StreamProductionDetailedValue: GlossaryEnergy.StreamProductionDetailedDf,

        GlossaryEnergy.StreamScope1GHGEmissionsValue: GlossaryEnergy.StreamScope1GHGEmissions,

        'energy_detailed_techno_prices': {'type': 'dataframe', 'unit': '$/MWh'},
        'techno_mix': {'type': 'dataframe', 'unit': '%'},

        GlossaryEnergy.LandUseRequiredValue: GlossaryEnergy.StreamLandUseDf,
        GlossaryEnergy.EnergyTypeCapitalDfValue: GlossaryEnergy.EnergyTypeCapitalDf,
        GlossaryEnergy.StreamScope1GHGIntensityValue: GlossaryEnergy.StreamScope1GHGIntensity,
    }

    _maturity = 'Research'
    stream_name = 'stream'
    unit = ""

    def setup_sos_disciplines(self):
        dynamic_inputs = {}
        dynamic_outputs = {}

        values_dict, go = self.collect_var_for_dynamic_setup([GlossaryEnergy.techno_list])
        if go:
            for techno in values_dict[GlossaryEnergy.techno_list]:
                # consumptions
                dynamic_inputs[f"{techno}.{GlossaryEnergy.TechnoEnergyConsumptionValue}"] = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.TechnoEnergyConsumption)
                dynamic_inputs[f"{techno}.{GlossaryEnergy.TechnoResourceConsumptionValue}"] = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.TechnoResourceConsumption)

                # demands:
                dynamic_inputs[f"{techno}.{GlossaryEnergy.TechnoResourceDemandsValue}"] = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.TechnoResourceDemands)
                dynamic_inputs[f"{techno}.{GlossaryEnergy.TechnoEnergyDemandsValue}"] = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.TechnoEnergyDemands)

                # production
                dynamic_inputs[f'{techno}.{GlossaryEnergy.TechnoProductionValue}'] = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.TechnoProductionDf)

                # emissions
                dynamic_inputs[f'{techno}.{GlossaryEnergy.TechnoScope1GHGEmissionsValue}'] = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.TechnoScope1GHGEmissions)

                dynamic_inputs[f'{techno}.{GlossaryEnergy.TechnoCapitalValue}'] = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.TechnoCapitalDf)
                dynamic_inputs[f'{techno}.{GlossaryEnergy.TechnoPricesValue}'] = GlossaryEnergy.get_techno_price_df(techno)
                dynamic_inputs[f'{techno}.{GlossaryEnergy.LandUseRequiredValue}'] = GlossaryEnergy.TechnoLandUseDf

        dynamic_outputs.update({
            GlossaryEnergy.StreamPricesValue: GlossaryEnergy.get_one_stream_price_df(stream_name=self.stream_name)
        })
        add_di, add_do = self.add_additionnal_dynamic_variables()
        dynamic_inputs.update(add_di)
        dynamic_outputs.update(add_do)
        self.add_inputs(dynamic_inputs)
        self.add_outputs(dynamic_outputs)

    def init_execution(self):  # type: (...) -> None
        self.unit = GlossaryEnergy.unit_dicts[self.stream_name]

    def add_additionnal_dynamic_variables(self):
        """Temporary method to be able to do multiple add_outputs in setup_sos_disciplines before it is done generically in sostradescore"""
        return {}, {}

    def get_chart_filter_list(self):
        chart_filters = []
        chart_list = ['Energy price',
                      "Production",
                      "Consumption",
                      GlossaryEnergy.Capital]
        chart_filters.append(ChartFilter(
            'Charts', chart_list, chart_list, 'charts'))

        price_unit_list = ["$/MWh", "$/t"]
        chart_filters.append(
            ChartFilter("Price unit", price_unit_list, price_unit_list, "price_unit")
        )

        year_start, year_end = self.get_sosdisc_inputs(
            [GlossaryEnergy.YearStart, GlossaryEnergy.YearEnd]
        )
        years = list(np.arange(year_start, year_end + 1, 5))
        chart_filters.append(
            ChartFilter(
                "Years for techno mix",
                years,
                [year_start, year_end],
                GlossaryEnergy.Years,
            )
        )
        return chart_filters

    def get_post_processing_list(self, filters=None):
        # For the outputs, making a graph for block fuel vs range and blocktime vs
        # range

        instanciated_charts = []
        charts = []
        price_unit_list = ['$/MWh', '$/t']
        years_list = [self.get_sosdisc_inputs(GlossaryEnergy.YearStart)]
        # Overload default value with chart filter
        if filters is not None:
            for chart_filter in filters:
                if chart_filter.filter_key == "charts":
                    charts = chart_filter.selected_values
                if chart_filter.filter_key == "price_unit":
                    price_unit_list = chart_filter.selected_values
                if chart_filter.filter_key == GlossaryEnergy.Years:
                    years_list = chart_filter.selected_values

        if "Energy price" in charts and "$/MWh" in price_unit_list:
            new_chart = self.get_chart_energy_price_in_dollar_kwh()
            if new_chart is not None:
                instanciated_charts.append(new_chart)
        if (
            "Energy price" in charts
            and "$/t" in price_unit_list
            and "calorific_value" in self.get_sosdisc_inputs("data_fuel_dict")
        ):
            new_chart = self.get_chart_energy_price_in_dollar_kg()
            if new_chart is not None:
                instanciated_charts.append(new_chart)
        if "Production" in charts:
            new_charts = self.get_charts_production(years_list=years_list)
            instanciated_charts.extend(new_charts)

        if "Consumption" in charts:
            new_charts = self.get_charts_consumptions()
            instanciated_charts.extend(new_charts)

        if GlossaryEnergy.Capital in charts:
            chart = self.get_capital_breakdown_by_technos()
            instanciated_charts.append(chart)

        if "Stream Flow" in charts or True:
            new_chart = self.get_chart_sankey_fluxes(
                years_list,
                chart_name=f"Flow of energy streams for {self.sos_name.split('.')[-1]} production ({self.unit})",
                split_external=True,
            )
            new_chart.post_processing_section_name = "Detailed Stream Flow"
            new_chart.post_processing_is_key_chart = True
            instanciated_charts.append(new_chart)

            new_chart = self.get_chart_sankey_fluxes(
                years_list,
                chart_name="Flow of energy streams (schematic)",
                normalized_links=True,
                split_external=True,
            )
            new_chart.post_processing_section_name = "Detailed Stream Flow"
            instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_chart_energy_price_in_dollar_kwh(self):
        energy_prices = self.get_sosdisc_outputs(GlossaryEnergy.StreamPricesValue)
        chart_name = f'Detailed prices of {self.stream_name} mix '
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, "Prices [$/MWh]", chart_name=chart_name
        )

        serie = InstanciatedSeries(
            energy_prices[GlossaryEnergy.Years],
            energy_prices[self.stream_name], f'{self.pimp_string(self.stream_name)} mix', 'lines')

        new_chart.series.append(serie)

        technology_list = self.get_sosdisc_inputs(GlossaryEnergy.techno_list)

        for technology in technology_list:
            techno_price = self.get_sosdisc_inputs(
                f"{technology}.{GlossaryEnergy.TechnoPricesValue}"
            )
            serie = InstanciatedSeries(
                energy_prices[GlossaryEnergy.Years],
                techno_price[technology], self.pimp_string(technology), 'lines')
            new_chart.series.append(serie)

        new_chart.post_processing_section_name = "Price"
        new_chart.post_processing_is_key_chart = True
        return new_chart

    def get_chart_energy_price_in_dollar_kg(self):
        energy_prices = self.get_sosdisc_outputs(GlossaryEnergy.StreamPricesValue)
        chart_name = f'Detailed prices of {self.stream_name} mix '
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'Prices [$/t]', chart_name=chart_name)
        total_price = energy_prices[self.stream_name] * \
                      self.get_sosdisc_inputs('data_fuel_dict')['calorific_value']
        serie = InstanciatedSeries(
            energy_prices[GlossaryEnergy.Years],
            total_price, f'{self.stream_name} mix', 'lines')

        new_chart.series.append(serie)

        technology_list = self.get_sosdisc_inputs(GlossaryEnergy.techno_list)

        for technology in technology_list:
            techno_price = self.get_sosdisc_inputs(
                f'{technology}.{GlossaryEnergy.TechnoPricesValue}')
            techno_price_kg = techno_price[technology] * \
                              self.get_sosdisc_inputs('data_fuel_dict')['calorific_value']
            serie = InstanciatedSeries(
                energy_prices[GlossaryEnergy.Years],
                techno_price_kg, self.pimp_string(technology), 'lines')
            new_chart.series.append(serie)

        new_chart.post_processing_section_name = "Price"
        new_chart.post_processing_is_key_chart = True
        return new_chart

    def get_charts_production(self, years_list):
        instanciated_charts = []

        # Productions of main stream
        techno_prods_of_main_stream_df = self.get_sosdisc_outputs(GlossaryEnergy.StreamProductionDetailedValue)
        techno_list = self.get_sosdisc_inputs(GlossaryEnergy.techno_list)

        total_stream_prod_df = self.get_sosdisc_outputs(GlossaryEnergy.StreamProductionValue)

        years = techno_prods_of_main_stream_df[GlossaryEnergy.Years]
        chart_name = f'Breakdown of {self.stream_name} production'

        chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, self.unit, chart_name=chart_name, stacked_bar=True)
        for techno in techno_list:
            new_series = InstanciatedSeries(years, techno_prods_of_main_stream_df[f'{techno} ({self.unit})'], techno,
                                            'bar', True)
            chart.series.append(new_series)

        new_series = InstanciatedSeries(years, total_stream_prod_df[f'{self.stream_name} ({self.unit})'], "Total",
                                        'lines', True)
        chart.series.append(new_series)
        chart.post_processing_is_key_chart = True
        chart.post_processing_section_name = "Production"
        instanciated_charts.append(chart)

        # Other byproducts
        byproduct_list = list(filter(lambda x: x != GlossaryEnergy.Years and x != f'{self.stream_name} ({self.unit})', total_stream_prod_df.columns))

        ## energy byproducts
        energy_byproducts = list(filter(lambda x: x.endswith("(TWh)"), byproduct_list))
        if energy_byproducts:
            chart_name = f'Energy byproducts due to {self.stream_name} production'
            chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, self.unit, chart_name=chart_name, stacked_bar=True)
            for bp in energy_byproducts:
                name = self.pimp_string(bp.split(' (')[0])
                new_series = InstanciatedSeries(years, total_stream_prod_df[bp], name, 'bar', True)
                chart.series.append(new_series)
            chart.post_processing_section_name = "Production"
            instanciated_charts.append(chart)

        ## mass byproducts
        mass_byproducts = list(filter(lambda x: x.endswith("(Mt)"), byproduct_list))
        if mass_byproducts:
            chart_name = f'Mass byproducts due to {self.stream_name} production'
            chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, self.unit, chart_name=chart_name, stacked_bar=True)
            for bp in energy_byproducts:
                name = self.pimp_string(bp.split(' (')[0])
                new_series = InstanciatedSeries(years, total_stream_prod_df[bp], name, 'bar', True)
                chart.series.append(new_series)
            chart.post_processing_section_name = "Production"
            instanciated_charts.append(chart)

        new_charts = self.get_chart_technology_mix(years_list)
        instanciated_charts.extend(new_charts)
        return instanciated_charts

    def get_chart_technology_mix(self, years_list):
        instanciated_charts = []
        techno_list = self.get_sosdisc_inputs(GlossaryEnergy.techno_list)
        stream_production_breakdown = self.get_sosdisc_outputs(GlossaryEnergy.StreamProductionDetailedValue)
        display_techno_list = []

        for year in years_list:

            df_at_year = stream_production_breakdown.loc[stream_production_breakdown["years"] == year]
            values = [float(df_at_year[f'{techno} ({self.unit})']) for techno in techno_list]
            pie_chart = InstanciatedPieChart(f'Composition of {self.stream_name} production in {year} ({self.unit})', display_techno_list, values)
            pie_chart.post_processing_section_name = "Production"
            instanciated_charts.append(pie_chart)


        return instanciated_charts

    def get_capital_breakdown_by_technos(self):
        energy_type_capital = self.get_sosdisc_outputs(
            GlossaryEnergy.EnergyTypeCapitalDfValue
        )
        techno_list = self.get_sosdisc_inputs(GlossaryEnergy.techno_list)

        years = energy_type_capital[GlossaryEnergy.Years]
        chart_name = 'Breakdown of capital by technos'

        chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, "G$", chart_name=chart_name, stacked_bar=True
        )
        chart.post_processing_section_name = "Capital"

        for techno in techno_list:
            ordonate_data = self.get_sosdisc_inputs(f"{techno}.{GlossaryEnergy.TechnoCapitalValue}")[GlossaryEnergy.Capital]

            new_series = InstanciatedSeries(years, ordonate_data, techno, 'bar', True)

            chart.series.append(new_series)

        new_series = InstanciatedSeries(years, energy_type_capital[GlossaryEnergy.Capital], 'Total', 'lines', True)
        chart.series.append(new_series)

        return chart

    def get_charts_consumptions(self):
        instanciated_charts = []

        # Productions of main stream
        consumptions_df = self.get_sosdisc_outputs(GlossaryEnergy.StreamEnergyConsumptionValue)

        consumptions_list = list(consumptions_df.columns)
        consumptions_list.remove(GlossaryEnergy.Years)
        years = consumptions_df[GlossaryEnergy.Years]
        ## energy consumptions
        energy_consumption_items = list(filter(lambda x: x.endswith("(TWh)"), consumptions_list))
        if energy_consumption_items:
            chart_name = f'Energies consumptions due to {self.stream_name} production'
            chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'TWh', chart_name=chart_name, stacked_bar=True)
            for item in energy_consumption_items:
                name = self.pimp_string(item.split(' (')[0])
                new_series = InstanciatedSeries(years, consumptions_df[item], name, 'bar', True)
                chart.series.append(new_series)
            chart.post_processing_section_name = "Consumptions"
            instanciated_charts.append(chart)

        ## mass consumptions
        mass_consumption_items = list(filter(lambda x: x.endswith("(Mt)"), consumptions_list))
        if mass_consumption_items:
            chart_name = f'Mass consumptions due to {self.stream_name} production'
            chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Mt', chart_name=chart_name, stacked_bar=True)
            for item in energy_consumption_items:
                name = self.pimp_string(item.split(' (')[0])
                new_series = InstanciatedSeries(years, consumptions_df[item], name, 'bar', True)
                chart.series.append(new_series)
            chart.post_processing_section_name = "Consumptions"
            instanciated_charts.append(chart)


        return instanciated_charts
    def pimp_string(self, val: str):
        val = val.replace("_", ' ')
        val = val.capitalize()
        return val


    def get_chart_sankey_fluxes(
        self,
        years_list,
        chart_name="Energy Flow",
        streams_filter: list | None = None,
        normalized_links: bool = False,
        split_external: bool = False,
    ):
        """Create sankey chart correlating production and consumption of all technos in stream disc."""

        # Get list of energy technologies
        techno_list = self.get_sosdisc_inputs(GlossaryEnergy.TechnoListName)
        year_start, year_end = self.get_sosdisc_inputs([GlossaryEnergy.YearStart, GlossaryEnergy.YearEnd])
        years = np.arange(year_start, year_end + 1)

        # Initialize dictionary with all consumptions / productions
        techno_dictionary = {}

        # Get dataframes and put them in dictionary format
        for techno in techno_list:
            consumption = self.get_sosdisc_inputs(
                f"{techno}.{GlossaryEnergy.TechnoEnergyConsumptionValue}"
            ).copy()
            production = self.get_sosdisc_inputs(
                f"{techno}.{GlossaryEnergy.TechnoProductionValue}"
            ).copy()

            # Add Years to dataframes
            if GlossaryEnergy.Years not in consumption.columns:
                consumption[GlossaryEnergy.Years] = years

            if GlossaryEnergy.Years not in production.columns:
                production[GlossaryEnergy.Years] = years

            # Update dictionary
            techno_dictionary[techno] = {
                "input": consumption,
                "output": production,
            }

        # Get Net Production
        production = self.get_sosdisc_outputs(
            f"{GlossaryEnergy.StreamProductionValue}"
        ).copy()
        production.columns = [c.replace("production ", "") for c in production.columns]
        consumption = pd.DataFrame({GlossaryEnergy.Years: years})

        # Add Years to dataframes
        if GlossaryEnergy.Years not in production.columns:
            production[GlossaryEnergy.Years] = years

        # Switch prod /consumption as we want the node to "consume" the available streams
        techno_dictionary["available"] = {
            "input": production,
            "output": consumption,
        }

        # Get Consumption
        consumption = self.get_sosdisc_outputs(
            f"{GlossaryEnergy.StreamEnergyConsumptionValue}"
        ).copy()
        production = pd.DataFrame({GlossaryEnergy.Years: years})

        # Add Years to dataframes
        if GlossaryEnergy.Years not in consumption.columns:
            consumption[GlossaryEnergy.Years] = years

        # Switch prod /consumption as we want the node to "consume" the available streams
        techno_dictionary["requested"] = {
            "input": production,
            "output": consumption,
        }

        # Filter out resources
        for dfs in techno_dictionary.values():
            dfs["input"] = dfs["input"][
                [c for c in dfs["input"].columns if "(Mt)" not in c]
            ]
            dfs["output"] = dfs["output"][
                [c for c in dfs["output"].columns if "(Mt)" not in c]
            ]

        # Remove units from all streams, to handle inconsistent naming
        for actor in techno_dictionary:
            techno_dictionary[actor]["input"].columns = [
                re.sub(r"\s*\([^)]*\)", "", c)
                for c in techno_dictionary[actor]["input"].columns
            ]
            techno_dictionary[actor]["output"].columns = [
                re.sub(r"\s*\([^)]*\)", "", c)
                for c in techno_dictionary[actor]["output"].columns
            ]

        # filter streams
        if streams_filter is not None:
            for dfs in techno_dictionary.values():
                existing_columns = list(set(streams_filter) & set(dfs["input"].columns))
                dfs["input"] = dfs["input"][[GlossaryEnergy.Years] + existing_columns]
                existing_columns = list(
                    set(streams_filter) & set(dfs["output"].columns)
                )
                dfs["output"] = dfs["output"][[GlossaryEnergy.Years] + existing_columns]

        # Create sankey plot
        colormap = available_colormaps["energy"]
        fig = create_sankey_with_slider(
            techno_dictionary,
            colormap=colormap,
            normalized_links=normalized_links,
            split_external=split_external,
            output_node="available",
            input_node="requested",
        )

        # return chart
        return InstantiatedPlotlyNativeChart(fig, chart_name)