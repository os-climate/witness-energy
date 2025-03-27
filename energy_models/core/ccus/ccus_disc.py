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
import copy
import logging

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
from sostrades_optimization_plugins.models.autodifferentiated_discipline import (
    AutodifferentiedDisc,
)

from energy_models.core.ccus.ccus import CCUS
from energy_models.glossaryenergy import GlossaryEnergy


class CCUS_Discipline(AutodifferentiedDisc):
    # ontology information
    _ontology_data = {
        'label': 'Carbon Capture and Storage Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fa-solid fa-people-carry-box fa-fw',
        'version': '',
    }

    ccs_list = CCUS.ccs_list

    DESC_IN = {GlossaryEnergy.YearStart: ClimateEcoDiscipline.YEAR_START_DESC_IN,
               GlossaryEnergy.YearEnd: GlossaryEnergy.YearEndVar,
               GlossaryEnergy.EnergyMixCCSDemandsDfValue: GlossaryEnergy.EnergyMixCCSDemandsDf,
               GlossaryEnergy.EnergyMixCCSConsumptionDfValue: GlossaryEnergy.EnergyMixCCSConsumptionDf,
           }

    DESC_OUT = {
        GlossaryEnergy.CCUS_CO2EmissionsDfValue: GlossaryEnergy.CCUS_CO2EmissionsDf,
        GlossaryEnergy.CCUSOutputValue: GlossaryEnergy.CCUSOutput,
        f"{GlossaryEnergy.CCUS}_{GlossaryEnergy.EnergyDemandValue}": GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.EnergyDemandDf),
        f"{GlossaryEnergy.CCUS}.{GlossaryEnergy.EnergyConsumptionValue}": GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.EnergyConsumptionDf),
        f"{GlossaryEnergy.CCUS}.{GlossaryEnergy.LandUseRequiredValue}": GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.StreamLandUseDf),
        GlossaryEnergy.CCUSPriceValue: GlossaryEnergy.CCUSPrice,
        GlossaryEnergy.CCUSAvailabilityRatiosValue: GlossaryEnergy.CCUSAvailabilityRatios,
        f"{GlossaryEnergy.carbon_captured}_demand_breakdown": {"type": "dict"},
        f"{GlossaryEnergy.carbon_storage}_demand_breakdown": {"type": "dict"},
        "demands_df": {"type": "dataframe"},
    }

    def __init__(self, sos_name, logger: logging.Logger):
        super().__init__(sos_name, logger)
        self.model = None

    def init_execution(self):
        self.model = CCUS(GlossaryEnergy.CCUS)

    def setup_sos_disciplines(self):
        dynamic_inputs = {}
        dynamic_outputs = {}

        for ccs_stream in self.ccs_list:
            vars_to_update_ccs_namespace = {
                GlossaryEnergy.StreamEnergyConsumptionValue: GlossaryEnergy.StreamEnergyConsumption,
                GlossaryEnergy.StreamEnergyDemandValue: GlossaryEnergy.StreamEnergyDemand,
                GlossaryEnergy.StreamProductionValue: GlossaryEnergy.StreamProductionDf,
                GlossaryEnergy.StreamPricesValue: GlossaryEnergy.StreamPrices,
                GlossaryEnergy.LandUseRequiredValue: GlossaryEnergy.StreamLandUseDf,
            }
            for key, var_descr in vars_to_update_ccs_namespace.items():
                copy_var_descr = copy.copy(var_descr)
                copy_var_descr["namespace"] = GlossaryEnergy.NS_CCS
                copy_var_descr["visibility"] = "Shared"
                dynamic_inputs[f'{ccs_stream}.{key}'] = copy_var_descr

        self.update_default_values()
        self.add_inputs(dynamic_inputs),
        self.add_outputs(dynamic_outputs)

    def update_default_values(self):
        """
        Update all default dataframes with years
        """
        if self.get_data_in() is not None:
            if GlossaryEnergy.YearEnd in self.get_data_in() and GlossaryEnergy.YearStart in self.get_data_in() and 'co2_for_food' in self.get_data_in():
                year_start, year_end = self.get_sosdisc_inputs([GlossaryEnergy.YearStart, GlossaryEnergy.YearEnd])
                if year_start is not None and year_end is not None:
                    default_co2_for_food = pd.DataFrame({
                        GlossaryEnergy.Years: np.arange(year_start, year_end + 1),
                        f'{GlossaryEnergy.carbon_captured} for food (Mt)': 0.0})
                    self.update_default_value('co2_for_food', 'in', default_co2_for_food)



    def get_chart_filter_list(self):
        chart_filters = []
        chart_list = [
            'Production',
            'Demand and availabilities ratio',
            'Energy consumption and demand',
            'Price'
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

        df_output = self.get_sosdisc_outputs(GlossaryEnergy.CCUSOutputValue)
        years = df_output[GlossaryEnergy.Years]
        energy_mix_consumption = self.get_sosdisc_inputs(GlossaryEnergy.EnergyMixCCSConsumptionDfValue)
        if 'Production' in charts:
            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, GlossaryEnergy.CCUSOutput["unit"], chart_name='CCUS sector production', y_min_zero=False)

            serie = InstanciatedSeries(years, df_output[GlossaryEnergy.carbon_storage], 'Carbon storage capacity', 'lines')
            new_chart.series.append(serie)

            serie = InstanciatedSeries(years, df_output[GlossaryEnergy.carbon_captured], 'Carbon captured', 'lines')
            new_chart.series.append(serie)

            serie = InstanciatedSeries(years, - energy_mix_consumption[GlossaryEnergy.carbon_captured], 'Carbon captured reused by Energy sector', 'bar')
            new_chart.series.append(serie)

            serie = InstanciatedSeries(years, df_output['Carbon captured to store (after direct usages)'], 'Carbon captured to store (after direct usages)', 'lines')
            new_chart.series.append(serie)

            serie = InstanciatedSeries(years, df_output['Carbon captured and stored'], 'Carbon captured and stored', 'lines')
            new_chart.series.append(serie)

            new_chart.post_processing_section_name = "Production"
            instanciated_charts.append(new_chart)

        if 'Demand and availabilities ratio' in charts:
            ratios_df = self.get_sosdisc_outputs(GlossaryEnergy.CCUSAvailabilityRatiosValue)
            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, GlossaryEnergy.CCUSAvailabilityRatios["unit"], chart_name='Availibility ratios (demand satisfaction)')


            for stream in self.ccs_list:
                serie = InstanciatedSeries(years, ratios_df[stream], self.pimp_string(stream), 'lines')
                new_chart.series.append(serie)

            new_chart.post_processing_section_name = 'Demand and availabilities ratio'
            instanciated_charts.append(new_chart)

        if 'Demand and availabilities ratio' in charts:
            demands_df = self.get_sosdisc_outputs("demands_df")


            for stream in self.ccs_list:
                new_chart = TwoAxesInstanciatedChart(
                    GlossaryEnergy.Years, GlossaryEnergy.CCUSOutput["unit"], chart_name=f'{self.pimp_string(stream)}: Demand vs production', stacked_bar=True)
                serie = InstanciatedSeries(years, demands_df[stream], 'Demand', 'lines')
                new_chart.series.append(serie)
                serie = InstanciatedSeries(years, df_output[stream], 'Production', 'lines')
                new_chart.series.append(serie)
                demand_breakdown_dict = self.get_sosdisc_outputs(f"{stream}_demand_breakdown")
                for key, value in demand_breakdown_dict.items():
                    serie = InstanciatedSeries(years, value, "Demand component: " + key, 'bar')
                    new_chart.series.append(serie)


                new_chart.post_processing_section_name = 'Demand and availabilities ratio'
                instanciated_charts.append(new_chart)

        if 'Energy consumption and demand' in charts:
            df_energies_demand = self.get_sosdisc_outputs(f"{GlossaryEnergy.CCUS}_{GlossaryEnergy.EnergyDemandValue}")
            df_energies_consumption = self.get_sosdisc_outputs(f"{GlossaryEnergy.CCUS}.{GlossaryEnergy.EnergyConsumptionValue}")

            # consumption
            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, GlossaryEnergy.EnergyConsumptionDf["unit"],
                                                 chart_name='CCUS energy consumption', stacked_bar=True)
            for stream in df_energies_demand.columns:
                if stream != GlossaryEnergy.Years:
                    serie = InstanciatedSeries(years, df_energies_consumption[stream], self.pimp_string(stream), 'bar')
                    new_chart.series.append(serie)
            new_chart.post_processing_section_name = 'Energy consumption and demand'
            instanciated_charts.append(new_chart)

            # demand
            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, GlossaryEnergy.EnergyDemandDf["unit"], chart_name='CCUS energy demand', stacked_bar=True)
            for stream in df_energies_demand.columns:
                if stream != GlossaryEnergy.Years:
                    serie = InstanciatedSeries(years, df_energies_demand[stream], self.pimp_string(stream), 'bar')
                    new_chart.series.append(serie)
            new_chart.post_processing_section_name = 'Energy consumption and demand'
            instanciated_charts.append(new_chart)

        if 'Price' in charts:
            df_price = self.get_sosdisc_outputs(GlossaryEnergy.CCUSPriceValue)
            mappping_legend = {
                GlossaryEnergy.carbon_storage: 'Storage price component',
                GlossaryEnergy.carbon_captured: 'Carbon capture price component',
            }

            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, GlossaryEnergy.CCUSPrice["unit"], chart_name='CCUS price', stacked_bar=True)
            serie = InstanciatedSeries(years, df_price["Captured and stored"], "Price per CO2 ton captured and stored", 'lines')
            new_chart.series.append(serie)
            for stream in self.ccs_list:
                price_stream_df = self.get_sosdisc_inputs(f'{stream}.{GlossaryEnergy.StreamPricesValue}')
                serie = InstanciatedSeries(years, price_stream_df[stream], mappping_legend[stream], 'bar')
                new_chart.series.append(serie)

            new_chart.post_processing_section_name = 'Price'
            instanciated_charts.append(new_chart)


        return  instanciated_charts