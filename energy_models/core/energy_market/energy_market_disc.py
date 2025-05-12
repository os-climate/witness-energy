'''
Copyright 2025 Capgemini

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

from climateeconomics.core.core_witness.climateeco_discipline import (
    ClimateEcoDiscipline,
)
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import (
    InstanciatedSeries,
    TwoAxesInstanciatedChart,
)
from sostrades_optimization_plugins.models.autodifferentiated_discipline import (
    AutodifferentiedDisc,
)

from energy_models.core.energy_market.energy_market_model import EnergyMarket
from energy_models.glossaryenergy import GlossaryEnergy


class EnergyMarketDiscipline(AutodifferentiedDisc):
    # ontology information
    _ontology_data = {
        "label": "Energy Market Model",
        "type": "Research",
        "source": "SoSTrades Project",
        "validated": "",
        "validated_by": "SoSTrades Project",
        "last_modification_date": "",
        "category": "",
        "definition": "",
        "icon": "fa-solid fa-right-left",
        "version": "",
    }

    DESC_IN = {
        GlossaryEnergy.SimplifiedMarketEnergyDemandValue: GlossaryEnergy.SimplifiedMarketEnergyDemand,
        GlossaryEnergy.YearStart: ClimateEcoDiscipline.YEAR_START_DESC_IN,
        GlossaryEnergy.YearEnd: GlossaryEnergy.YearEndVar,
        "consumers_actors": {"type": "list", 'namespace': GlossaryEnergy.NS_WITNESS, "visibility": "Shared", 'structuring': True},
        GlossaryEnergy.EnergyMixNetProductionsDfValue: GlossaryEnergy.EnergyMixNetProductionsDf,
    }

    DESC_OUT = {
        GlossaryEnergy.EnergyMarketRatioAvailabilitiesValue: GlossaryEnergy.EnergyMarketRatioAvailabilities,
        GlossaryEnergy.EnergyMarketDemandsDfValue: GlossaryEnergy.EnergyMarketDemandsDf,
        "sectors_demand_breakdown": {"type": 'dataframe', "description": "breakdown of global demand of energy between sectors", "unit": GlossaryEnergy.EnergyMixEnergiesDemandsDf['unit']},
        GlossaryEnergy.EnergyProdVsDemandObjective: GlossaryEnergy.EnergyProdVsDemandObjectiveVar
    }

    def __init__(self, sos_name, logger):
        super().__init__(sos_name, logger)
        self.model = None

    def init_execution(self):
        self.model = EnergyMarket('EnergyMarket', self.logger)

    def setup_sos_disciplines(self):
        dynamic_inputs = {}
        dynamic_outputs = {}
        values_dict, go = self.collect_var_for_dynamic_setup(["consumers_actors"])
        if go:
            for sector_consumer in values_dict["consumers_actors"]:
                dynamic_inputs[f"{sector_consumer}_{GlossaryEnergy.EnergyDemandValue}"] = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.EnergyDemandDf)

        self.add_inputs(dynamic_inputs)
        self.add_outputs(dynamic_outputs)

    def get_chart_filter_list(self):
        chart_filters = []
        chart_list = [
            'Production',
            'Demand',
            'Production vs demand',
            'Availabilities ratios',
            "Sectors demand breakdown"
        ]

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

        years = self.get_sosdisc_inputs(GlossaryEnergy.EnergyMixNetProductionsDfValue)[GlossaryEnergy.Years]
        destination_unit = GlossaryEnergy.EnergyMixNetProductionsDf['unit']
        production_df = self.get_sosdisc_inputs(GlossaryEnergy.EnergyMixNetProductionsDfValue) * \
                        GlossaryEnergy.conversion_dict[GlossaryEnergy.EnergyMixNetProductionsDf["unit"]][
                            destination_unit]
        total_demand_df = self.get_sosdisc_outputs(GlossaryEnergy.EnergyMarketDemandsDfValue) * \
                          GlossaryEnergy.conversion_dict[GlossaryEnergy.EnergyMarketDemandsDf["unit"]][
                              destination_unit]

        simplified_demand = self.get_sosdisc_inputs(GlossaryEnergy.SimplifiedMarketEnergyDemandValue)
        if 'Production' in charts:
            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, destination_unit,
                                                 chart_name="Production", stacked_bar=True)

            for column in production_df.columns:
                if column not in [GlossaryEnergy.Years, 'Total']:
                    serie = InstanciatedSeries(years, production_df[column], self.pimp_string(column), 'bar')
                    new_chart.add_series(serie)

            serie = InstanciatedSeries(years, production_df["Total"], 'Total net energy production', 'lines')
            new_chart.add_series(serie)

            new_chart.post_processing_section_name = "Production & Demand"

            instanciated_charts.append(new_chart)

        if 'Demand' in charts and not simplified_demand:
            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, destination_unit,
                                                 chart_name="Demand", stacked_bar=True)

            for column in total_demand_df.columns:
                if column not in [GlossaryEnergy.Years, 'Total']:
                    serie = InstanciatedSeries(years, total_demand_df[column], self.pimp_string(column), 'bar')
                    new_chart.add_series(serie)

            serie = InstanciatedSeries(years, total_demand_df["Total"], 'Total net energy demand', 'lines')
            new_chart.add_series(serie)

            new_chart.post_processing_section_name = "Production & Demand"

            instanciated_charts.append(new_chart)

        if 'Production vs demand' in charts:
            if simplified_demand:
                new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, destination_unit, chart_name="Production vs demand", y_min_zero=True)

                serie = InstanciatedSeries(years, production_df["Total"], 'Production', 'lines')
                new_chart.add_series(serie)

                serie = InstanciatedSeries(years, total_demand_df["Total"], 'Demand', 'lines')
                new_chart.add_series(serie)

                new_chart.post_processing_section_name = "Production & Demand"
                new_chart.post_processing_is_key_chart = True
                new_chart.annotation_upper_left = {"Note": 'simplified demand, on total of energy only, not by energy type'}

            else:
                new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, '%',
                                                     chart_name="Delta production & demand (%)")

                for column in total_demand_df.columns:
                    if column not in [GlossaryEnergy.Years, 'Total']:
                        ratio = (production_df[column] - total_demand_df[column]) / (production_df[column] + 1e-6) * 100
                        serie = InstanciatedSeries(years, ratio, self.pimp_string(column), 'lines')
                        new_chart.add_series(serie)
                if simplified_demand:
                    ratio = (production_df["Total"] - total_demand_df["Total"]) / (production_df["Total"] + 1e-6) * 100
                    serie = InstanciatedSeries(years, ratio, self.pimp_string("Total"), 'lines')
                    new_chart.add_series(serie)

                new_chart.annotation_upper_left = {"Note": 'Positive values indicates overproduction, zero means equilibrium'}
                new_chart.post_processing_section_name = "Production & Demand"

            instanciated_charts.append(new_chart)

        if 'Availabilities ratios' in charts:
            ratios_df = self.get_sosdisc_outputs(GlossaryEnergy.EnergyMarketRatioAvailabilitiesValue)
            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, '%', chart_name="Availabilites ratios", y_min_zero=True)

            for column in ratios_df.columns:
                if column not in [GlossaryEnergy.Years, 'Total']:
                    serie = InstanciatedSeries(years, ratios_df[column], self.pimp_string(column), 'lines')
                    new_chart.add_series(serie)

            new_chart.post_processing_section_name = "Production & Demand"
            new_chart.post_processing_is_key_chart = True
            if simplified_demand:
                new_chart.annotation_upper_left = {"Note": 'simplified demand, ratios is computed bases on totals, not by energy type'}

            instanciated_charts.append(new_chart)

        if "Sectors demand breakdown" in charts:
            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, GlossaryEnergy.EnergyMarketDemandsDf['unit'], chart_name="Total energy demand breakdown by sector", y_min_zero=True, stacked_bar=True)

            df_sector_demand = self.get_sosdisc_outputs("sectors_demand_breakdown")
            for column in df_sector_demand.columns:
                if column not in [GlossaryEnergy.Years, 'Total']:
                    serie = InstanciatedSeries(years, df_sector_demand[column], column, 'bar')
                    new_chart.add_series(serie)

            serie = InstanciatedSeries(years, total_demand_df["Total"], "Total demand", 'lines')
            new_chart.add_series(serie)

            new_chart.post_processing_section_name = "Demand breakdown by sector"
            new_chart.post_processing_is_key_chart = True

            instanciated_charts.append(new_chart)

        return instanciated_charts
