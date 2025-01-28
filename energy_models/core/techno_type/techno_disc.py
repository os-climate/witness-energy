'''
Copyright 2022 Airbus SAS
Modifications on 2023/03/27-2024/06/24 Copyright 2023 Capgemini

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

import numpy as np
import pandas as pd
from climateeconomics.core.core_resources.resource_mix.resource_mix import (
    ResourceMixModel,
)
from climateeconomics.core.core_witness.climateeco_discipline import (
    ClimateEcoDiscipline,
)
from plotly import graph_objects as go
from sostrades_core.execution_engine.sos_wrapp import SoSWrapp
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import (
    InstanciatedSeries,
    TwoAxesInstanciatedChart,
)
from sostrades_core.tools.post_processing.plotly_native_charts.instantiated_plotly_native_chart import (
    InstantiatedPlotlyNativeChart,
)
from sostrades_optimization_plugins.models.autodifferentiated_discipline import (
    AutodifferentiedDisc,
)

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.resources_data_disc import (
    get_default_resources_CO2_emissions,
    get_default_resources_prices,
)
from energy_models.database_witness_energy import DatabaseWitnessEnergy
from energy_models.glossaryenergy import GlossaryEnergy


class TechnoDiscipline(AutodifferentiedDisc):
    # ontology information
    _ontology_data = {
        'label': 'Core Technology Type Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': '',
        'version': '',
    }

    DESC_IN = {
        GlossaryEnergy.YearStart: dict({'structuring': True}, **ClimateEcoDiscipline.YEAR_START_DESC_IN),
        GlossaryEnergy.YearEnd: dict({'structuring': True}, **GlossaryEnergy.YearEndVar),
        GlossaryEnergy.InvestLevelValue: GlossaryEnergy.TechnoInvestDf,
        GlossaryEnergy.MarginValue: GlossaryEnergy.MarginDf,
        GlossaryEnergy.UtilisationRatioValue: GlossaryEnergy.UtilisationRatioDf,
        GlossaryEnergy.CO2TaxesValue: GlossaryEnergy.CO2Taxes,
        'smooth_type': {'type': 'string', 'default': 'smooth_max',
                        'possible_values': ['smooth_max', 'soft_max', 'cons_smooth_max' ],
                        'user_level': 2, 'structuring': False, 'visibility': SoSWrapp.SHARED_VISIBILITY,
                        'namespace': 'ns_public'},
        GlossaryEnergy.BoolApplyRatio: {'type': 'bool', 'default': True, 'user_level': 2, 'structuring': True,
                           'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        GlossaryEnergy.BoolApplyStreamRatio: {'type': 'bool', 'default': True, 'user_level': 2, 'structuring': True,
                             'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        GlossaryEnergy.BoolApplyResourceRatio: {'type': 'bool', 'default': False, 'user_level': 2, 'structuring': True,
                                    'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        GlossaryEnergy.ResourcesUsedForProductionValue: GlossaryEnergy.ResourcesUsedForProduction,
        GlossaryEnergy.ResourcesUsedForBuildingValue: GlossaryEnergy.ResourcesUsedForBuilding,
        GlossaryEnergy.StreamsUsedForProductionValue: GlossaryEnergy.StreamsUsedForProduction,
        GlossaryEnergy.InvestmentBeforeYearStartValue: GlossaryEnergy.InvestmentBeforeYearStartDf,
        GlossaryEnergy.ConstructionDelay: {'type': 'int', 'unit': 'years', 'user_level': 2},
        'initial_production': {'type': 'float', 'unit': 'TWh'},
        GlossaryEnergy.LifetimeName: {'type': 'int', 'unit': 'years', "description": "lifetime of a plant of the techno"},
        GlossaryEnergy.InitialPlantsAgeDistribFactor: {'type': 'float', 'unit': 'years', "description": "lifetime of a plant of the techno"},
    }

    # -- Change output that are not clear, transform to dataframe since r_* is price
    DESC_OUT = {
        GlossaryEnergy.TechnoConsumptionValue: {'type': 'dataframe', 'unit': 'TWh or Mt'},
        GlossaryEnergy.TechnoConsumptionWithoutRatioValue: {'type': 'dataframe', 'unit': 'TWh or Mt', },
        GlossaryEnergy.TechnoProductionWithoutRatioValue: {'type': 'dataframe', 'unit': 'TWh or Mt'},
        'mean_age_production': GlossaryEnergy.MeanAgeProductionDf,
        GlossaryEnergy.CO2EmissionsValue: {'type': 'dataframe', 'unit': 'kg/kWh'},
        'CO2_emissions_detailed': {'type': 'dataframe', 'unit': 'kg/kWh'},
        'applied_ratio': {'type': 'dataframe', 'unit': '-'},
        'initial_age_distrib': {'type': 'dataframe', 'unit': '%',
                                'dataframe_descriptor': {
                                           'age': ('float', None, True),
                                           'distrib': ('float', None, True),
                                           }},
        GlossaryEnergy.InstalledCapacity: GlossaryEnergy.InstalledCapacityDf,
        GlossaryEnergy.TechnoCapitalValue: GlossaryEnergy.TechnoCapitalDf,
        GlossaryEnergy.SpecificCostsForProductionValue: GlossaryEnergy.SpecificCostsForProduction,
        GlossaryEnergy.InitialPlantsTechnoProductionValue: GlossaryEnergy.InitialPlantsTechnoProduction,
    }
    _maturity = 'Research'

    techno_name = 'Fill techno name'
    stream_name = 'Fill the energy name for this techno'

    def setup_sos_disciplines(self):
        dynamic_inputs = {}
        dynamic_outputs = {}
        self.update_default_values()
        if self.get_data_in() is not None:
            if GlossaryEnergy.ResourcesUsedForProductionValue in self.get_data_in() and \
                GlossaryEnergy.YearStart in self.get_data_in() and \
                    GlossaryEnergy.YearEnd in self.get_data_in():
                resources_used_for_production = self.get_sosdisc_inputs(GlossaryEnergy.ResourcesUsedForProductionValue)
                year_start = self.get_sosdisc_inputs(GlossaryEnergy.YearStart)
                year_end = self.get_sosdisc_inputs(GlossaryEnergy.YearEnd)
                if resources_used_for_production is not None and year_start is not None and year_end is not None:
                    cost_of_resource_usage_var = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.CostOfResourceUsageDf)
                    cost_of_resource_usage_var["dataframe_descriptor"].update({resource: ("float", [0., 1e30], False) for resource in resources_used_for_production})
                    dynamic_outputs[GlossaryEnergy.CostOfResourceUsageValue] = cost_of_resource_usage_var

                    resources_co2_emissions_var = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.ResourcesCO2Emissions)
                    resources_co2_emissions_var["dataframe_descriptor"] = {GlossaryEnergy.Years: ("int", [1900, 2100], False)}
                    resources_co2_emissions_var["dataframe_descriptor"].update({energy: ("float", [0., 1e30], False) for energy in resources_used_for_production})

                    years = np.arange(year_start, year_end + 1)
                    default_resources = get_default_resources_CO2_emissions(years)
                    resources_co2_emissions_var["default"] = default_resources
                    dynamic_inputs.update({GlossaryEnergy.RessourcesCO2EmissionsValue: resources_co2_emissions_var})

                    resources_prices = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.ResourcesPrice)
                    resources_prices["dataframe_descriptor"] = {GlossaryEnergy.Years: ("int", [1900, 2100], False)}
                    resources_prices["dataframe_descriptor"].update({energy: ("float", [0., 1e30], False) for energy in resources_used_for_production})

                    years = np.arange(year_start, year_end + 1)
                    default_resources_prices = get_default_resources_prices(years)
                    resources_prices["default"] = default_resources_prices
                    dynamic_inputs.update({GlossaryEnergy.ResourcesPriceValue: resources_prices})

            if GlossaryEnergy.StreamsUsedForProductionValue in self.get_data_in():
                streams_used_for_production = self.get_sosdisc_inputs(GlossaryEnergy.StreamsUsedForProductionValue)
                if streams_used_for_production is not None:
                    cost_of_streams_usage_var = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.CostOfStreamsUsageDf)
                    cost_of_streams_usage_var["dataframe_descriptor"].update({stream: ("float", [0., 1e30], False) for stream in streams_used_for_production})
                    dynamic_outputs[GlossaryEnergy.CostOfStreamsUsageValue] = cost_of_streams_usage_var

                    dynamic_inputs.update({
                        GlossaryEnergy.StreamPricesValue: GlossaryEnergy.get_stream_prices_df(stream_used_for_production=streams_used_for_production),
                        GlossaryEnergy.StreamsCO2EmissionsValue: GlossaryEnergy.get_stream_co2_emissions_df(stream_used_for_production=streams_used_for_production)
                    })

            if GlossaryEnergy.BoolApplyRatio in self.get_data_in():
                year_start, year_end = self.get_sosdisc_inputs([GlossaryEnergy.YearStart, GlossaryEnergy.YearEnd])
                if year_start is not None and year_end is not None:
                    years = np.arange(year_start, year_end + 1)
                    if self.get_sosdisc_inputs(GlossaryEnergy.BoolApplyStreamRatio):
                        demand_ratio_dict = dict(
                            zip(EnergyMix.energy_list, np.linspace(1.0, 1.0, len(years)) * 100.0))
                        demand_ratio_dict[GlossaryEnergy.Years] = years
                        all_streams_demand_ratio_default = pd.DataFrame(
                            demand_ratio_dict)
                        dynamic_inputs[GlossaryEnergy.AllStreamsDemandRatioValue] = {'type': 'dataframe', 'unit': '-',
                                                                                     'default': all_streams_demand_ratio_default,
                                                                                     'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                                                     'namespace': 'ns_energy',
                                                                                     "dynamic_dataframe_columns": True
                                                                                     }
                    if self.get_sosdisc_inputs(GlossaryEnergy.BoolApplyResourceRatio):
                        resource_ratio_dict = dict(
                            zip(EnergyMix.RESOURCE_LIST, np.ones(len(years)) * 100.0))
                        resource_ratio_dict[GlossaryEnergy.Years] = years
                        all_resource_ratio_usable_demand_default = pd.DataFrame(
                            resource_ratio_dict)
                        dynamic_inputs[ResourceMixModel.RATIO_USABLE_DEMAND] = {'type': 'dataframe', 'unit': '-',
                                                                                'default': all_resource_ratio_usable_demand_default,
                                                                                'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                                                'namespace': 'ns_resource',
                                                                                "dynamic_dataframe_columns": True}

        dynamic_outputs.update({
            GlossaryEnergy.TechnoPricesValue: GlossaryEnergy.get_techno_price_df(techno_name=self.techno_name),
            GlossaryEnergy.TechnoProductionValue: GlossaryEnergy.get_techno_prod_df(techno_name=self.techno_name,
                                                                                    energy_name=self.stream_name,
                                                                                    byproducts_list=GlossaryEnergy.techno_byproducts[self.techno_name]),
            GlossaryEnergy.TechnoDetailedProductionValue: GlossaryEnergy.get_techno_prod_df(techno_name=self.techno_name,
                                                                                            energy_name=self.stream_name,
                                                                                            byproducts_list=GlossaryEnergy.techno_byproducts[self.techno_name]),
            GlossaryEnergy.LandUseRequiredValue: GlossaryEnergy.get_land_use_df(techno_name=self.techno_name),
            GlossaryEnergy.TechnoDetailedPricesValue: GlossaryEnergy.get_techno_detailed_price_df(techno_name=self.techno_name),
        })
        self.add_inputs(dynamic_inputs)
        d = self.add_additionnal_dynamic_output()
        d.update(dynamic_outputs)
        self.add_outputs(d)

    def add_additionnal_dynamic_output(self):
        """Temporary method to be able to do multiple add_outputs in setup_sos_disciplines before it is done generically in sostradescore"""
        return {}

    def update_default_values(self):
        '''
        Update all default dataframes with years
        '''
        if GlossaryEnergy.LifetimeName in self.get_data_in():
            lifetime = self.get_sosdisc_inputs(GlossaryEnergy.LifetimeName)
            if lifetime is None:
                lifetime = GlossaryEnergy.TechnoLifetimeDict[self.techno_name]
                self.update_default_value(GlossaryEnergy.LifetimeName, 'in', lifetime)

        if GlossaryEnergy.InitialPlantsAgeDistribFactor in self.get_data_in() and GlossaryEnergy.YearStart in self.get_data_in():
            initial_plant_age_distrib_factor = self.get_sosdisc_inputs(GlossaryEnergy.InitialPlantsAgeDistribFactor)
            year_start = self.get_sosdisc_inputs(GlossaryEnergy.YearStart)
            if year_start is not None and initial_plant_age_distrib_factor is None:
                initial_plant_age_distrib_factor, _ = DatabaseWitnessEnergy.get_techno_age_distrib_factor(self.techno_name, year=year_start)
                self.update_default_value(GlossaryEnergy.InitialPlantsAgeDistribFactor, 'in', initial_plant_age_distrib_factor)

        if 'initial_production' in self.get_data_in() and GlossaryEnergy.YearStart in self.get_data_in():
            year_start = self.get_sosdisc_inputs(GlossaryEnergy.YearStart)
            initial_production = self.get_sosdisc_inputs('initial_production')
            if year_start is not None and initial_production is None:
                initial_production, _ = DatabaseWitnessEnergy.get_techno_prod(self.techno_name, year=year_start - 1)
                self.update_default_value('initial_production', 'in', initial_production)

        construction_delay = None
        if GlossaryEnergy.ConstructionDelay in self.get_data_in():
            construction_delay = GlossaryEnergy.TechnoConstructionDelayDict[self.techno_name]
            self.update_default_value(GlossaryEnergy.ConstructionDelay, 'in', construction_delay)

        if GlossaryEnergy.InvestmentBeforeYearStartValue in self.get_data_in() and GlossaryEnergy.YearStart in self.get_data_in() and 'techno_infos_dict' in self.get_data_in():
            year_start = self.get_sosdisc_inputs(GlossaryEnergy.YearStart)
            invest_before_year_start = self.get_sosdisc_inputs(GlossaryEnergy.InvestmentBeforeYearStartValue)
            if year_start is not None and construction_delay is not None and invest_before_year_start is None:
                default_val, _ = DatabaseWitnessEnergy.get_techno_invest_before_year_start(
                    techno_name=self.techno_name, year_start=year_start, construction_delay=construction_delay)
                self.update_default_value(GlossaryEnergy.InvestmentBeforeYearStartValue, 'in', default_val)

        if GlossaryEnergy.ResourcesUsedForProductionValue in self.get_data_in():
            resource_used_for_prod = self.get_sosdisc_inputs(GlossaryEnergy.ResourcesUsedForProductionValue)
            if resource_used_for_prod is None:
                resource_used_for_prod = GlossaryEnergy.TechnoResourceUsedDict[self.techno_name] if self.techno_name in GlossaryEnergy.TechnoResourceUsedDict else []
                self.update_default_value(GlossaryEnergy.ResourcesUsedForProductionValue, 'in', resource_used_for_prod)

        if GlossaryEnergy.ResourcesUsedForBuildingValue in self.get_data_in():
            resource_used_for_building = self.get_sosdisc_inputs(GlossaryEnergy.ResourcesUsedForBuildingValue)
            if resource_used_for_building is None:
                resource_used_for_building = GlossaryEnergy.TechnoBuildingResourceDict[self.techno_name] if self.techno_name in GlossaryEnergy.TechnoBuildingResourceDict else []
                self.update_default_value(GlossaryEnergy.ResourcesUsedForBuildingValue, 'in', resource_used_for_building)

        if GlossaryEnergy.StreamsUsedForProductionValue in self.get_data_in():
            energies_used_for_prod = self.get_sosdisc_inputs(GlossaryEnergy.StreamsUsedForProductionValue)
            if energies_used_for_prod is None:
                energies_used_for_prod = GlossaryEnergy.TechnoStreamsUsedDict[self.techno_name] if self.techno_name in GlossaryEnergy.TechnoStreamsUsedDict else []
                self.update_default_value(GlossaryEnergy.StreamsUsedForProductionValue, 'in', energies_used_for_prod)

        if GlossaryEnergy.YearStart in self.get_data_in() and GlossaryEnergy.YearEnd in self.get_data_in():
            year_start, year_end = self.get_sosdisc_inputs([GlossaryEnergy.YearStart, GlossaryEnergy.YearEnd])
            if year_start is not None and year_end is not None:
                years = np.arange(year_start, year_end + 1)
                default_margin = pd.DataFrame({GlossaryEnergy.Years: years,
                                               GlossaryEnergy.MarginValue: 110.0})

                default_utilisation_ratio = pd.DataFrame({GlossaryEnergy.Years: years,
                                                          GlossaryEnergy.UtilisationRatioValue: 100.0 * np.ones_like(
                                                              years)})

                self.set_dynamic_default_values({GlossaryEnergy.MarginValue: default_margin,
                                                 GlossaryEnergy.UtilisationRatioValue: default_utilisation_ratio,
                                                 GlossaryEnergy.TransportCostValue: pd.DataFrame(
                                                     {GlossaryEnergy.Years: years,
                                                      'transport': 0.0}),
                                                 GlossaryEnergy.TransportMarginValue: default_margin})

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['Detailed prices',
                      'Consumption and production',
                      'Initial Production',
                      "Production",
                      'Factory Mean Age',
                      'CO2 emissions',
                      GlossaryEnergy.UtilisationRatioValue,
                      'Non-Use Capital',
                      'Power production',
                      'Power plants initial age distribution',
                      'Capex']
        if self.get_sosdisc_inputs(GlossaryEnergy.BoolApplyRatio):
            chart_list.extend(['Applied Ratio'])
        chart_filters.append(ChartFilter(
            'Charts', chart_list, chart_list, 'charts'))

        price_unit_list = ['$/MWh', '$/t']
        chart_filters.append(ChartFilter(
            'Price unit', price_unit_list, price_unit_list, 'price_unit'))
        return chart_filters

    def get_post_processing_list(self, filters=None):

        # For the outputs, making a graph for block fuel vs range and blocktime vs
        # range
        self.stream_unit = GlossaryEnergy.unit_dicts[self.stream_name]
        instanciated_charts = []
        charts = []
        price_unit_list = ['$/MWh', '$/t']
        inputs_dict = self.get_sosdisc_inputs()
        data_fuel_dict = inputs_dict['data_fuel_dict']
        technos_info_dict = inputs_dict['techno_infos_dict']
        # Overload default value with chart filter
        if filters is not None:
            for chart_filter in filters:
                if chart_filter.filter_key == 'charts':
                    charts = chart_filter.selected_values
                if chart_filter.filter_key == 'price_unit':
                    price_unit_list = chart_filter.selected_values

        if 'Detailed prices' in charts and '$/MWh' in price_unit_list:
            new_chart = self.get_chart_detailed_price_in_dollar_kwh()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'Detailed prices' in charts \
                and '$/t' in price_unit_list \
                and 'calorific_value' in data_fuel_dict:
            new_chart = self.get_chart_detailed_price_in_dollar_kg()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if "Production":
            new_chart = self.get_chart_production()
            instanciated_charts.append(new_chart)
        if 'Consumption and production' in charts:
            new_chart = self.get_chart_investments()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

            new_charts = self.get_charts_consumption_and_production()
            for new_chart in new_charts:
                if new_chart is not None:
                    instanciated_charts.append(new_chart)

            new_chart = self.get_chart_required_land()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'Applied Ratio' in charts:
            new_chart = self.get_chart_applied_ratio()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if GlossaryEnergy.UtilisationRatioValue in charts:
            new_chart = self.get_utilisation_ratio_chart()
            instanciated_charts.append(new_chart)

        if 'Initial Production' in charts:
            if 'initial_production' in self.get_data_in():
                new_chart = self.get_chart_initial_production()
                if new_chart is not None:
                    instanciated_charts.append(new_chart)

        if 'Factory Mean Age' in charts:
            new_chart = self.get_chart_factory_mean_age()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'CO2 emissions' in charts:
            new_chart = self.get_chart_carbon_intensity_kwh()
            if new_chart is not None:
                instanciated_charts.append(new_chart)
            if 'calorific_value' in data_fuel_dict and 'high_calorific_value' in data_fuel_dict:
                new_chart = self.get_chart_carbon_intensity_kg()
                if new_chart is not None:
                    instanciated_charts.append(new_chart)
        if 'Non-Use Capital' in charts:
            new_chart = self.get_chart_non_use_capital()
            if new_chart is not None:
                instanciated_charts.append(new_chart)
        if 'Power production' in charts:
            new_chart = self.get_chart_installed_capacity(technos_info_dict)
            if new_chart is not None:
                instanciated_charts.append(new_chart)
        if 'Power plants initial age distribution' in charts:
            new_chart = self.get_chart_initial_age_distrib()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'Capex' in charts:
            new_chart = self.get_chart_capex()
            instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_utilisation_ratio_chart(self):
        utilisation_ratio_df = self.get_sosdisc_inputs(GlossaryEnergy.UtilisationRatioValue)
        years = list(utilisation_ratio_df[GlossaryEnergy.Years].values)
        utilisation_ratio = list(utilisation_ratio_df[GlossaryEnergy.UtilisationRatioValue].values)

        chart_name = GlossaryEnergy.UtilisationRatioValue

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, '%', [years[0], years[-1]], [0, 100],
                                             chart_name=chart_name, stacked_bar=True)

        new_series = InstanciatedSeries(
            years, utilisation_ratio, GlossaryEnergy.UtilisationRatioValue, InstanciatedSeries.BAR_DISPLAY, True)

        new_chart.series.append(new_series)
        return new_chart

    def get_chart_detailed_price_in_dollar_kwh(self):

        techno_detailed_prices = self.get_sosdisc_outputs(GlossaryEnergy.TechnoDetailedPricesValue)
        chart_name = f'Price breakdown of {self.techno_name}'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Prices [$/MWh]',
                                             chart_name=chart_name, stacked_bar=True)

        if 'percentage_resource' in self.get_data_in():
            percentage_resource = self.get_sosdisc_inputs('percentage_resource')
            new_chart.annotation_upper_left = {
                'Percentage of total price at starting year': f'{percentage_resource[self.stream_name][0]} %'}
            tot_price = techno_detailed_prices[self.techno_name].values / \
                        (percentage_resource[self.stream_name] / 100.)
            serie = InstanciatedSeries(
                techno_detailed_prices[GlossaryEnergy.Years],
                tot_price, 'Total price without percentage', 'lines')
            new_chart.series.append(serie)
        # Add total price
        tot_price_mwh = techno_detailed_prices[self.techno_name].values
        serie = InstanciatedSeries(
            techno_detailed_prices[GlossaryEnergy.Years],
            tot_price_mwh, 'Total price', 'lines')

        new_chart.series.append(serie)

        factory_price_mwh = techno_detailed_prices[f'{self.techno_name}_factory'].values
        # Factory price
        serie = InstanciatedSeries(
            techno_detailed_prices[GlossaryEnergy.Years],
            factory_price_mwh, 'Factory', 'bar')

        new_chart.series.append(serie)

        if 'energy_and_resources_costs' in techno_detailed_prices:
            # energy_costs
            ec_price_mwh = techno_detailed_prices['energy_and_resources_costs'].values
            serie = InstanciatedSeries(
                techno_detailed_prices[GlossaryEnergy.Years],
                ec_price_mwh, 'Energy costs', 'bar')

            new_chart.series.append(serie)

        transport_price_mwh = techno_detailed_prices['transport'].values
        # Transport price
        serie = InstanciatedSeries(
            techno_detailed_prices[GlossaryEnergy.Years],
            transport_price_mwh, 'Transport', 'bar')

        new_chart.series.append(serie)
        # CO2 taxes
        co2_price_mwh = techno_detailed_prices['CO2_taxes_factory'].values
        serie = InstanciatedSeries(
            techno_detailed_prices[GlossaryEnergy.Years],
            co2_price_mwh, 'CO2 taxes due to production', 'bar')
        new_chart.series.append(serie)

        serie = InstanciatedSeries(
            techno_detailed_prices[GlossaryEnergy.Years],
            techno_detailed_prices[GlossaryEnergy.MarginValue], 'Margin', 'bar')
        new_chart.series.append(serie)

        return new_chart

    def get_chart_detailed_price_in_dollar_kg(self):

        techno_detailed_prices = self.get_sosdisc_outputs(GlossaryEnergy.TechnoDetailedPricesValue)

        chart_name = f'Price breakdown of {self.techno_name}'
        data_fuel_dict = self.get_sosdisc_inputs('data_fuel_dict')

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Prices [$/t]', stacked_bar=True,
                                             chart_name=chart_name)

        if 'percentage_resource' in self.get_data_in():
            percentage_resource = self.get_sosdisc_inputs('percentage_resource')
            new_chart.annotation_upper_left = {
                'Percentage of total price at starting year': f'{percentage_resource[self.stream_name][0]} %'}
            tot_price = techno_detailed_prices[self.techno_name].values / \
                        (percentage_resource[self.stream_name] / 100.)

            serie = InstanciatedSeries(
                techno_detailed_prices[GlossaryEnergy.Years],
                tot_price, 'Total price without percentage', 'lines')
            new_chart.series.append(serie)
        # Add total price

        techno_kg_price = techno_detailed_prices[self.techno_name].values * \
                          data_fuel_dict['calorific_value']
        serie = InstanciatedSeries(
            techno_detailed_prices[GlossaryEnergy.Years],
            techno_kg_price, 'Total price', 'lines')

        new_chart.series.append(serie)

        # Factory price
        techno_kg_price = techno_detailed_prices[f'{self.techno_name}_factory'].values * \
                          data_fuel_dict['calorific_value']
        serie = InstanciatedSeries(
            techno_detailed_prices[GlossaryEnergy.Years],
            techno_kg_price, 'Factory', 'bar')

        new_chart.series.append(serie)
        if 'energy_and_resources_costs' in techno_detailed_prices:
            # energy_costs
            techno_kg_price = techno_detailed_prices['energy_and_resources_costs'].values * \
                              data_fuel_dict['calorific_value']
            serie = InstanciatedSeries(
                techno_detailed_prices[GlossaryEnergy.Years],
                techno_kg_price, 'Energy costs', 'bar')

            new_chart.series.append(serie)
        # Transport price
        techno_kg_price = techno_detailed_prices['transport'].values * \
                          data_fuel_dict['calorific_value']
        serie = InstanciatedSeries(
            techno_detailed_prices[GlossaryEnergy.Years],
            techno_kg_price, 'Transport', 'bar')

        new_chart.series.append(serie)
        # CO2 taxes
        techno_kg_price = techno_detailed_prices['CO2_taxes_factory'].values * \
                          data_fuel_dict['calorific_value']
        serie = InstanciatedSeries(
            techno_detailed_prices[GlossaryEnergy.Years],
            techno_kg_price, 'CO2 taxes due to production', 'bar')
        new_chart.series.append(serie)

        # margin
        techno_kg_price = techno_detailed_prices[GlossaryEnergy.MarginValue].values * \
                          data_fuel_dict['calorific_value']
        serie = InstanciatedSeries(
            techno_detailed_prices[GlossaryEnergy.Years],
            techno_kg_price, 'Margin', 'bar')
        new_chart.series.append(serie)

        return new_chart

    def get_chart_investments(self):
        # Chart for input investments
        invest_during_study = self.get_sosdisc_inputs(GlossaryEnergy.InvestLevelValue)
        chart_name = f'Investments in {self.techno_name}'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Investments [M$]',
                                             chart_name=chart_name, stacked_bar=True)
        invest = invest_during_study[GlossaryEnergy.InvestValue].values * 1e3
        serie = InstanciatedSeries(
            invest_during_study[GlossaryEnergy.Years],
            invest, 'During study', 'bar')

        new_chart.series.append(serie)

        invest_before_study = self.get_sosdisc_inputs(GlossaryEnergy.InvestmentBeforeYearStartValue)
        invest = invest_before_study[GlossaryEnergy.InvestValue].values * 1e3
        serie = InstanciatedSeries(
            invest_before_study[GlossaryEnergy.Years],
            invest, 'Past invests (construction delay)', 'bar')

        new_chart.series.append(serie)

        return new_chart

    def get_charts_consumption_and_production(self):
        instanciated_charts = []
        # Charts for consumption and prod
        techno_consumption = self.get_sosdisc_outputs(GlossaryEnergy.TechnoConsumptionValue)
        techno_production = self.get_sosdisc_outputs(GlossaryEnergy.TechnoDetailedProductionValue)
        chart_name = f'{self.techno_name} technology energy Production & consumption<br>with input investments'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Energy [TWh]',
                                             chart_name=chart_name.capitalize(), stacked_bar=True)

        for reactant in techno_consumption.columns:
            if reactant != GlossaryEnergy.Years and reactant.endswith('(TWh)'):
                energy_twh = -techno_consumption[reactant].values
                legend_title = f'{reactant} consumption'.replace(
                    "(TWh)", "")
                serie = InstanciatedSeries(
                    techno_consumption[GlossaryEnergy.Years],
                    energy_twh, legend_title, 'bar')

                new_chart.series.append(serie)

        for products in techno_production.columns:
            if products != GlossaryEnergy.Years and products.endswith('(TWh)'):
                energy_twh = techno_production[products].values
                legend_title = f'{products} production'.replace(
                    "(TWh)", "")
                serie = InstanciatedSeries(
                    techno_production[GlossaryEnergy.Years],
                    energy_twh, legend_title, 'bar')

                new_chart.series.append(serie)
        instanciated_charts.append(new_chart)

        # Check if we have kg in the consumption or prod :

        kg_values_consumption = 0
        reactant_found = None
        for reactant in techno_consumption.columns:
            if reactant != GlossaryEnergy.Years and reactant.endswith('(Mt)'):
                kg_values_consumption += 1
                reactant_found = reactant

        kg_values_production = 0
        product_found = None
        for product in techno_production.columns:
            if product != GlossaryEnergy.Years and product.endswith('(Mt)'):
                kg_values_production += 1
                product_found = product
        if kg_values_consumption == 1 and kg_values_production == 0:
            legend_title = f'{reactant_found} consumption'.replace(
                "(Mt)", "")
            chart_name = f'{legend_title} of the {self.techno_name} technology<br>with input investments'
        elif kg_values_production == 1 and kg_values_consumption == 0:
            legend_title = f'{product_found} production'.replace(
                "(Mt)", "")
            chart_name = f'{legend_title} of the {self.techno_name} technology<br>with input investments'
        else:
            chart_name = f'{self.techno_name} technology mass Production & consumption<br>with input investments'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Mass [Mt]',
                                             chart_name=chart_name, stacked_bar=True)

        for reactant in techno_consumption.columns:
            if reactant != GlossaryEnergy.Years and reactant.endswith('(Mt)'):
                legend_title = f'{reactant} consumption'.replace(
                    "(Mt)", "")
                # 1GT = 1e9T = 1e12 kg
                mass = -techno_consumption[reactant].values
                serie = InstanciatedSeries(
                    techno_consumption[GlossaryEnergy.Years],
                    mass, legend_title, 'bar')
                new_chart.series.append(serie)
        for product in techno_production.columns:
            if product != GlossaryEnergy.Years and product.endswith('(Mt)'):
                legend_title = f'{product} production'.replace(
                    "(Mt)", "")
                # 1GT = 1e9T = 1e12 kg
                mass = techno_production[product].values
                serie = InstanciatedSeries(
                    techno_production[GlossaryEnergy.Years],
                    mass, legend_title, 'bar')
                new_chart.series.append(serie)

        if kg_values_consumption > 0 or kg_values_production > 0:
            instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_chart_applied_ratio(self):
        # Charts for consumption and prod
        applied_ratio = self.get_sosdisc_outputs('applied_ratio')
        chart_name = f'Ratio applied on {self.techno_name} technology energy Production'
        fig = go.Figure()
        fig.add_trace(go.Bar(x=applied_ratio[GlossaryEnergy.Years],
                             y=applied_ratio['applied_ratio'],
                             marker=dict(color=applied_ratio['applied_ratio'],
                                         colorscale='Emrld'),
                             hovertext=applied_ratio['limiting_input']))
        new_chart = InstantiatedPlotlyNativeChart(
            fig, chart_name=chart_name, default_title=True)
        return new_chart

    def get_chart_initial_production(self):

        year_start = self.get_sosdisc_inputs(GlossaryEnergy.YearStart)
        initial_production = self.get_sosdisc_outputs(GlossaryEnergy.InitialPlantsTechnoProductionValue)

        study_production = self.get_sosdisc_outputs(GlossaryEnergy.TechnoDetailedProductionValue)
        chart_name = f'{self.stream_name} World Production via {self.techno_name}<br>with {year_start} factories distribution'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, f'{self.stream_name} production [TWh]',
                                             chart_name=chart_name.capitalize())

        serie = InstanciatedSeries(
            initial_production[GlossaryEnergy.Years],
            initial_production['cum energy (TWh)'], f'Initial production by {year_start} factories', 'lines')

        study_prod = study_production[f'{self.stream_name} ({GlossaryEnergy.energy_unit})'].values
        new_chart.series.append(serie)
        years_study = study_production[GlossaryEnergy.Years].values.tolist()
        years_study.insert(0, year_start - 1)
        study_prod_l = study_prod.tolist()
        study_prod_l.insert(0, initial_production['cum energy (TWh)'].values[-1])
        serie = InstanciatedSeries(years_study, study_prod_l, 'Predicted production', 'lines')
        new_chart.series.append(serie)

        return new_chart


    def get_chart_factory_mean_age(self):
        mean_age_production = self.get_sosdisc_outputs('mean_age_production')

        if GlossaryEnergy.Years in mean_age_production.columns:
            chart_name = f'{self.techno_name} factories average age'

            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Mean age',
                                                 chart_name=chart_name.capitalize())

            serie = InstanciatedSeries(
                mean_age_production[GlossaryEnergy.Years],
                mean_age_production['mean age'], '', 'lines')

            new_chart.series.append(serie)

            return new_chart

    def get_chart_carbon_intensity_kwh(self):

        carbon_emissions = self.get_sosdisc_outputs('CO2_emissions_detailed')
        chart_name = f'Carbon intensity of {self.stream_name} via {self.techno_name}'
        data_fuel_dict = self.get_sosdisc_inputs('data_fuel_dict')

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'CO2 emissions [kgCO2/kWh]',
                                             chart_name=chart_name, stacked_bar=True)

        CO2_per_use = np.zeros(
            len(carbon_emissions[GlossaryEnergy.Years]))
        if GlossaryEnergy.CO2PerUse in data_fuel_dict and 'high_calorific_value' in data_fuel_dict:
            if data_fuel_dict['CO2_per_use_unit'] == 'kg/kg':
                CO2_per_use = np.ones(
                    len(carbon_emissions[GlossaryEnergy.Years])) * data_fuel_dict[GlossaryEnergy.CO2PerUse] / data_fuel_dict[
                                  'high_calorific_value']
            elif data_fuel_dict['CO2_per_use_unit'] == 'kg/kWh':
                CO2_per_use = np.ones(
                    len(carbon_emissions[GlossaryEnergy.Years])) * data_fuel_dict[GlossaryEnergy.CO2PerUse]
            serie = InstanciatedSeries(
                carbon_emissions[GlossaryEnergy.Years],
                CO2_per_use, f'if {self.stream_name} used', 'bar')

            new_chart.series.append(serie)

        for emission_type in carbon_emissions:
            if emission_type == self.techno_name:
                total_carbon_emissions = CO2_per_use + \
                                         carbon_emissions[self.techno_name].values
                serie = InstanciatedSeries(
                    carbon_emissions[GlossaryEnergy.Years],
                    carbon_emissions[self.techno_name], 'Total w/o use', 'lines')
                new_chart.series.append(serie)

                serie = InstanciatedSeries(
                    carbon_emissions[GlossaryEnergy.Years],
                    total_carbon_emissions, 'Total if used', 'lines')
                new_chart.series.append(serie)
            elif emission_type != GlossaryEnergy.Years and not (carbon_emissions[emission_type] == 0).all():
                serie = InstanciatedSeries(
                    carbon_emissions[GlossaryEnergy.Years],
                    carbon_emissions[emission_type], emission_type, 'bar')
                new_chart.series.append(serie)

        return new_chart

    def get_chart_carbon_intensity_kg(self):

        carbon_emissions = self.get_sosdisc_outputs('CO2_emissions_detailed')

        chart_name = f'Carbon intensity of {self.techno_name} technology'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'CO2 emissions [kgCO2/kg]',
                                             chart_name=chart_name, stacked_bar=True)
        data_fuel_dict = self.get_sosdisc_inputs('data_fuel_dict')

        CO2_per_use = np.zeros(
            len(carbon_emissions[GlossaryEnergy.Years]))
        if GlossaryEnergy.CO2PerUse in data_fuel_dict:
            if data_fuel_dict['CO2_per_use_unit'] == 'kg/kg':
                CO2_per_use = np.ones(
                    len(carbon_emissions[GlossaryEnergy.Years])) * data_fuel_dict[GlossaryEnergy.CO2PerUse]
            elif data_fuel_dict['CO2_per_use_unit'] == 'kg/kWh':
                CO2_per_use = np.ones(
                    len(carbon_emissions[GlossaryEnergy.Years])) * data_fuel_dict[GlossaryEnergy.CO2PerUse] * data_fuel_dict[
                                  'high_calorific_value']
            serie = InstanciatedSeries(
                carbon_emissions[GlossaryEnergy.Years],
                CO2_per_use, f'if {self.stream_name} used', 'bar')

            new_chart.series.append(serie)

        for emission_type in carbon_emissions:
            if emission_type == self.techno_name:
                total_carbon_emission_wo_use = carbon_emissions[self.techno_name].values * \
                                               data_fuel_dict['high_calorific_value']
                total_carbon_emissions = CO2_per_use + total_carbon_emission_wo_use

                serie = InstanciatedSeries(
                    carbon_emissions[GlossaryEnergy.Years],
                    total_carbon_emission_wo_use, 'Total w/o use', 'lines')
                new_chart.series.append(serie)

                serie = InstanciatedSeries(
                    carbon_emissions[GlossaryEnergy.Years],
                    total_carbon_emissions, 'Total if used ', 'lines')
                new_chart.series.append(serie)
            elif emission_type != GlossaryEnergy.Years and not (carbon_emissions[emission_type] == 0).all():
                emissions_kg_kg = carbon_emissions[emission_type].values * \
                                  data_fuel_dict['high_calorific_value']
                serie = InstanciatedSeries(
                    carbon_emissions[GlossaryEnergy.Years],
                    emissions_kg_kg, emission_type, 'bar')
                new_chart.series.append(serie)

        return new_chart

    def get_chart_required_land(self):
        '''
        if land use required is filled, the chart giving the land use is shown
        '''
        land_use_required = self.get_sosdisc_outputs(GlossaryEnergy.LandUseRequiredValue)

        new_chart = None
        if not (land_use_required[f'{self.techno_name} (Gha)'].all() == 0):
            chart_name = f'Land use required of {self.techno_name}'

            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Land use required [Gha]',
                                                 chart_name=chart_name)

            serie = InstanciatedSeries(
                land_use_required[GlossaryEnergy.Years],
                land_use_required[f'{self.techno_name} (Gha)'], 'Gha', 'lines')
            new_chart.series.append(serie)

        return new_chart

    def get_chart_non_use_capital(self):
        techno_capital = self.get_sosdisc_outputs(GlossaryEnergy.TechnoCapitalValue)
        chart_name = f'Capital of {self.techno_name}'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Capital [G$]',
                                             chart_name=chart_name)

        serie = InstanciatedSeries(
            techno_capital[GlossaryEnergy.Years],
            techno_capital[GlossaryEnergy.Capital], 'Total capital', 'lines')

        new_chart.series.append(serie)

        serie = InstanciatedSeries(
            techno_capital[GlossaryEnergy.Years],
            techno_capital[GlossaryEnergy.NonUseCapital],
            'Unused capital (utilisation ratio + limitation from energy and resources)', 'bar')

        new_chart.series.append(serie)

        return new_chart

    def get_chart_installed_capacity(self, technos_info_dict):
        installed_capacity = self.get_sosdisc_outputs(GlossaryEnergy.InstalledCapacity)
        chart_name = f'Capacity installed of {self.techno_name} factories'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Power [MW]',
                                             chart_name=chart_name)

        if 'full_load_hours' not in technos_info_dict:
            note = {
                f'The full_load_hours data is not set for {self.techno_name}': 'default = 8760.0 hours, full year hours  '}
            new_chart.annotation_upper_left = note

        serie = InstanciatedSeries(
            installed_capacity[GlossaryEnergy.Years],
            installed_capacity['total_installed_capacity'], 'Total', 'lines')

        new_chart.series.append(serie)

        serie = InstanciatedSeries(
            installed_capacity[GlossaryEnergy.Years],
            installed_capacity['newly_installed_capacity'], 'Newly installed', 'lines')

        new_chart.series.append(serie)

        serie = InstanciatedSeries(
            installed_capacity[GlossaryEnergy.Years],
            installed_capacity['removed_installed_capacity'], 'Newly dismantled', 'lines')

        new_chart.series.append(serie)

        return new_chart

    def get_chart_initial_age_distrib(self):
        age_distrib = self.get_sosdisc_outputs('initial_age_distrib')
        chart_name = 'Age distribution of initial power plants / factories'

        new_chart = TwoAxesInstanciatedChart('Age', '%', chart_name=chart_name)

        serie = InstanciatedSeries(
            age_distrib['age'],
            age_distrib['distrib'], '', 'bar')

        new_chart.series.append(serie)
        return new_chart

    def get_chart_capex(self):
        cost_details = self.get_sosdisc_outputs(GlossaryEnergy.TechnoDetailedPricesValue)
        chart_name = 'Capex'
        years = cost_details[GlossaryEnergy.Years]
        capex = cost_details[f'Capex_{self.techno_name}']
        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, '$/MWh', chart_name=chart_name)
        serie = InstanciatedSeries(years, capex, '', 'lines')

        new_chart.series.append(serie)
        return new_chart

    def get_chart_production(self):
        production_detailed = self.get_sosdisc_outputs(GlossaryEnergy.TechnoDetailedProductionValue)
        chart_name = f'Production of {self.stream_name} by {self.techno_name}'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, f'{self.stream_unit}', chart_name=chart_name, stacked_bar=True)

        new_chart.series.append(InstanciatedSeries(
            production_detailed[GlossaryEnergy.Years],
            production_detailed[f'{self.stream_name} ({self.stream_unit})'], 'Total', 'lines')
        )
        new_chart.series.append(InstanciatedSeries(
            production_detailed[GlossaryEnergy.Years],
            production_detailed['production_historical_plants'], 'Initial plants production', 'bar')
        )
        new_chart.series.append(InstanciatedSeries(
            production_detailed[GlossaryEnergy.Years],
            production_detailed['production_newly_builted_plants'], 'New plants production', 'bar')
        )

        return new_chart