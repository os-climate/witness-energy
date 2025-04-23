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
        'smooth_type': {'type': 'string', 'default': 'cons_smooth_max',
                        'possible_values': ['cons_smooth_max' ],
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
        GlossaryEnergy.EnergiesUsedForProductionValue: GlossaryEnergy.EnergiesUsedForProduction,

        f"{GlossaryEnergy.CO2}_intensity_by_energy": GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.GHGIntensityEnergies),
        f"{GlossaryEnergy.CH4}_intensity_by_energy": GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.GHGIntensityEnergies),
        f"{GlossaryEnergy.N2O}_intensity_by_energy": GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.GHGIntensityEnergies),

        GlossaryEnergy.CCSUsedForProductionValue: GlossaryEnergy.CCSUsedForProduction,
        GlossaryEnergy.InvestmentBeforeYearStartValue: GlossaryEnergy.InvestmentBeforeYearStartDf,
        GlossaryEnergy.ConstructionDelay: {'type': 'int', 'unit': 'years', 'user_level': 2},
        'initial_production': {'type': 'float', 'unit': 'TWh'},
        'techno_is_ccus': {'type': 'bool', "default": False, 'description': 'False for techno of energy production, true for CCUS technos'},
        'techno_is_carbon_capture': {'type': 'bool', "default": False, 'description': 'Says if techno is for carbon capture'},
        GlossaryEnergy.LifetimeName: {'type': 'int', 'unit': 'years', "description": "lifetime of a plant of the techno"},
        GlossaryEnergy.InitialPlantsAgeDistribFactor: {'type': 'float', 'unit': 'years', "description": "lifetime of a plant of the techno"},
        "extra_ghg_from_external_source": {'type': 'list', 'unit': 'Mt/TWh', "default": [], "description": "emissions associated to other stream consumed to include in scope 1 by unit of external source consumed"},
    }

    DESC_OUT = {
        # actual consumptions:
        GlossaryEnergy.TechnoEnergyConsumptionValue: GlossaryEnergy.TechnoEnergyConsumption,
        GlossaryEnergy.TechnoResourceConsumptionValue: GlossaryEnergy.TechnoResourceConsumption,

        # demands for energy:
        GlossaryEnergy.TechnoEnergyDemandsValue: GlossaryEnergy.TechnoEnergyDemands,
        GlossaryEnergy.TechnoResourceDemandsValue: GlossaryEnergy.TechnoResourceDemands,

        # demands for CCS (certain technos):
        GlossaryEnergy.TechnoCCSDemandsValue: GlossaryEnergy.TechnoCCSDemands,
        GlossaryEnergy.TechnoCCSConsumptionValue: GlossaryEnergy.TechnoCCSConsumption,

        GlossaryEnergy.TechnoTargetProductionValue: {'type': 'dataframe', 'unit': 'TWh',
                                                     'description': "The techno target production is the maximum theoritical production multiplied by the utilisation ratio"},
        # emissions
        GlossaryEnergy.TechnoScope1GHGEmissionsValue: GlossaryEnergy.TechnoScope1GHGEmissions,
        'ghg_intensity_scope_1': {'type': 'dataframe', 'unit': 'Mt/TWh', 'description': "GHG intensity for techno production (scope 1)"},
        'ghg_intensity_scope_2': {'type': 'dataframe', 'unit': 'Mt/TWh', 'description': "GHG intensity for techno production (scope 2), related to external energies and resources usage"},
        'techno_scope_2_ghg_emissions': {'type': 'dataframe', 'unit': 'Mt/TWh', 'description': "GHG intensity for techno production (scope 2), related to external energies and resources usage"},
        'ghg_intensity_scope_2_details_CO2': {'type': 'dataframe', 'unit': 'Mt/TWh', 'description': "GHG intensity scope 2 details for CO2 (composition of the CO2 intensity)"},
        'ghg_intensity_scope_2_details_CH4': {'type': 'dataframe', 'unit': 'Mt/TWh', 'description': "GHG intensity scope 2 details for CH4 (composition of the CH4 intensity)"},
        'ghg_intensity_scope_2_details_N2O': {'type': 'dataframe', 'unit': 'Mt/TWh', 'description': "GHG intensity scope 2 details for N2O (composition of the N2O intensity)"},

        'mean_age_production': GlossaryEnergy.MeanAgeProductionDf,
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

            values_dict, go = self.collect_var_for_dynamic_setup([GlossaryEnergy.EnergiesUsedForProductionValue])
            if go:
                energies_used_for_production = values_dict[GlossaryEnergy.EnergiesUsedForProductionValue]
                cost_of_streams_usage_var = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.CostOfStreamsUsageDf)
                cost_of_streams_usage_var["dataframe_descriptor"].update({stream: ("float", [0., 1e30], False) for stream in energies_used_for_production})
                dynamic_outputs[GlossaryEnergy.CostOfStreamsUsageValue] = cost_of_streams_usage_var

                dynamic_inputs.update({
                    GlossaryEnergy.StreamPricesValue: GlossaryEnergy.get_stream_prices_df(stream_used_for_production=energies_used_for_production),
                })

            # ratios inputs:
            values_dict, go = self.collect_var_for_dynamic_setup([
                GlossaryEnergy.BoolApplyStreamRatio, GlossaryEnergy.BoolApplyResourceRatio,
                GlossaryEnergy.BoolApplyRatio, GlossaryEnergy.YearStart, GlossaryEnergy.YearEnd,
                GlossaryEnergy.CCSUsedForProductionValue, 'techno_is_ccus'
            ])
            if go:
                years = np.arange(values_dict[GlossaryEnergy.YearStart], values_dict[GlossaryEnergy.YearEnd] + 1)
                if values_dict[GlossaryEnergy.BoolApplyStreamRatio]:
                    if len(values_dict[GlossaryEnergy.CCSUsedForProductionValue]) > 0:
                        default_ccs_ratios = pd.DataFrame({
                            GlossaryEnergy.Years: years, GlossaryEnergy.carbon_captured: 100., GlossaryEnergy.carbon_storage: 100.,
                        })
                        ccus_availability_ratios_var = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.CCUSAvailabilityRatios)
                        ccus_availability_ratios_var["default"] = default_ccs_ratios
                        dynamic_inputs[GlossaryEnergy.CCUSAvailabilityRatiosValue] = ccus_availability_ratios_var
                    if not values_dict['techno_is_ccus']:
                        # Energy techno
                        all_streams_demand_ratio_default = pd.DataFrame({GlossaryEnergy.Years: years})
                        dynamic_inputs[GlossaryEnergy.AllStreamsDemandRatioValue] = {'type': 'dataframe', 'unit': '-',
                                                                                     'default': all_streams_demand_ratio_default,
                                                                                     'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                                                     'namespace': 'ns_energy',
                                                                                     "dynamic_dataframe_columns": True,
                                                                                     self.GRADIENTS: True,
                                                                                     }
                    
                    else:
                        # CCUS techno
                        variable = GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.EnergyMarketRatioAvailabilities)
                        variable["default"]  = pd.DataFrame({GlossaryEnergy.Years: years})
                        dynamic_inputs[GlossaryEnergy.EnergyMarketRatioAvailabilitiesValue] = variable
                if values_dict[GlossaryEnergy.BoolApplyResourceRatio]:
                    resource_ratio_dict = dict(zip(EnergyMix.resource_list, np.ones(len(years)) * 100.0))
                    resource_ratio_dict[GlossaryEnergy.Years] = years
                    all_resource_ratio_usable_demand_default = pd.DataFrame(resource_ratio_dict)
                    dynamic_inputs[ResourceMixModel.RATIO_USABLE_DEMAND] = {'type': 'dataframe', 'unit': '-',
                                                                            'default': all_resource_ratio_usable_demand_default,
                                                                            'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                                            'namespace': 'ns_resource',
                                                                            "dynamic_dataframe_columns": True}

        dynamic_outputs.update({
            GlossaryEnergy.TechnoPricesValue: GlossaryEnergy.get_techno_price_df(techno_name=self.techno_name),
            GlossaryEnergy.TechnoProductionValue: GlossaryEnergy.TechnoProductionDf,
            'techno_production_infos': {'type': 'dataframe', 'unit': '-', "dynamic_dataframe_columns": True},
            GlossaryEnergy.LandUseRequiredValue: GlossaryEnergy.TechnoLandUseDf,
            f"{self.stream_name}.{self.techno_name}.{GlossaryEnergy.TechnoFlueGasProductionValue}": GlossaryEnergy.TechnoFlueGasProduction,
        GlossaryEnergy.TechnoDetailedPricesValue: GlossaryEnergy.get_techno_detailed_price_df(techno_name=self.techno_name),
        })
        di, do = self.add_additionnal_dynamic_variables()
        do.update(dynamic_outputs)
        di.update(dynamic_inputs)
        self.add_inputs(di)
        self.add_outputs(do)

    def add_additionnal_dynamic_variables(self):
        """Temporary method to be able to do multiple add_outputs in setup_sos_disciplines before it is done generically in sostradescore"""
        return {}, {}

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

        values_dict, go = self.collect_var_for_dynamic_setup([GlossaryEnergy.EnergiesUsedForProductionValue])
        if not go:
            streams_used_for_prod = GlossaryEnergy.TechnoStreamsUsedDict[self.techno_name] if self.techno_name in GlossaryEnergy.TechnoStreamsUsedDict else []
            ccs_streams = [GlossaryEnergy.carbon_captured, GlossaryEnergy.carbon_storage]
            energies_used_for_prod = list(set(streams_used_for_prod) - set(ccs_streams))
            ccs_streams_used_for_prod = list(set(streams_used_for_prod).intersection(set(ccs_streams)))
            self.update_default_value(GlossaryEnergy.EnergiesUsedForProductionValue, 'in', energies_used_for_prod)
            self.update_default_value(GlossaryEnergy.CCSUsedForProductionValue, 'in', ccs_streams_used_for_prod)

        values_dict, go = self.collect_var_for_dynamic_setup([GlossaryEnergy.YearStart, GlossaryEnergy.YearEnd])
        if go:
            years = np.arange(values_dict[GlossaryEnergy.YearStart], values_dict[GlossaryEnergy.YearEnd] + 1)
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
                      "Energy consumption",
                      "Energy demand",
                      "Investments",
                      'Factory Mean Age',
                      GlossaryEnergy.UtilisationRatioValue,
                      'Non-Use Capital',
                      'Installed capacity',
                      'Power plants initial age distribution',
                      'Capex']
        for ghg in GlossaryEnergy.GreenHouseGases:
            chart_list.append(f"{ghg} intensity")
            chart_list.append(f"{ghg} emissions")
            pass

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
            instanciated_charts.append(new_chart)

        if 'Detailed prices' in charts \
                and '$/t' in price_unit_list \
                and 'calorific_value' in data_fuel_dict:
            new_chart = self.get_chart_detailed_price_in_dollar_kg()
            instanciated_charts.append(new_chart)

        if "Production":
            new_chart = self.get_chart_production()
            instanciated_charts.append(new_chart)

        if "Production":
            new_chart = self.get_chart_production_capacity()
            instanciated_charts.append(new_chart)

        if "Energy consumption":
            instanciated_charts.extend(self.get_chart_energy_consumption())

        if "Energy demand":
            instanciated_charts.extend(self.get_chart_energy_demand())

        if 'Applied Ratio' in charts:
            new_chart = self.get_chart_applied_ratio()
            instanciated_charts.append(new_chart)

        if GlossaryEnergy.UtilisationRatioValue in charts:
            new_chart = self.get_utilisation_ratio_chart()
            instanciated_charts.append(new_chart)

        if 'Initial Production' in charts:
            new_chart = self.get_chart_initial_production()
            instanciated_charts.append(new_chart)

        if 'Factory Mean Age' in charts:
            new_chart = self.get_chart_factory_mean_age()
            instanciated_charts.append(new_chart)

        for ghg in GlossaryEnergy.GreenHouseGases:
            if f'{ghg} intensity' in charts:
                instanciated_charts.extend(self.get_chart_ghg_intensity_kwh(ghg))

            if f'{ghg} emissions' in charts:
                instanciated_charts.extend(self.get_chart_ghg_emissions(ghg))

        if 'Non-Use Capital' in charts:
            new_chart = self.get_chart_non_use_capital()
            instanciated_charts.append(new_chart)
        if 'Installed capacity' in charts:
            new_chart = self.get_chart_installed_capacity(technos_info_dict)
            instanciated_charts.append(new_chart)
        if 'Power plants initial age distribution' in charts:
            new_chart = self.get_chart_initial_age_distrib()
            instanciated_charts.append(new_chart)

        if 'Capex' in charts:
            new_chart = self.get_chart_capex()
            instanciated_charts.append(new_chart)

        if "Investments" in charts:
            new_chart = self.get_chart_investments()
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
        new_chart.post_processing_section_name = "Ratios"
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

        new_chart.post_processing_section_name = "Prices & Capex"
        new_chart.post_processing_is_key_chart = True
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
        new_chart.post_processing_section_name = "Prices & Capex"
        new_chart.post_processing_is_key_chart = True
        return new_chart

    def get_chart_investments(self):
        # Chart for input investments
        invest_during_study = self.get_sosdisc_inputs(GlossaryEnergy.InvestLevelValue)
        chart_name = f'Investments in {self.techno_name}'

        displayed_unit = 'M$'
        assert GlossaryEnergy.TechnoInvestDf['unit'] == GlossaryEnergy.InvestmentBeforeYearStartDf['unit']
        conversion_factor = GlossaryEnergy.conversion_dict[GlossaryEnergy.TechnoInvestDf['unit']][displayed_unit]
        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, displayed_unit,
                                             chart_name=chart_name, stacked_bar=True)
        invest = invest_during_study[GlossaryEnergy.InvestValue].values * conversion_factor
        serie = InstanciatedSeries(
            invest_during_study[GlossaryEnergy.Years],
            invest, 'During study', 'bar')

        new_chart.series.append(serie)

        invest_before_study = self.get_sosdisc_inputs(GlossaryEnergy.InvestmentBeforeYearStartValue)
        invest = invest_before_study[GlossaryEnergy.InvestValue].values * conversion_factor
        serie = InstanciatedSeries(
            invest_before_study[GlossaryEnergy.Years],
            invest, 'Past invests (construction delay)', 'bar')

        new_chart.series.append(serie)
        new_chart.post_processing_is_key_chart = True
        new_chart.post_processing_section_name = "Capital & Investments"

        return new_chart

    def get_chart_applied_ratio(self):
        # Charts for consumption and prod
        applied_ratio = self.get_sosdisc_outputs('applied_ratio')
        chart_name = f'Ratio applied on {self.techno_name} technology energy Production'
        fig = go.Figure()
        fig.add_trace(go.Bar(x=list(applied_ratio[GlossaryEnergy.Years]),
                             y=list(applied_ratio['applied_ratio']),
                             marker=dict(color=list(applied_ratio['applied_ratio']),
                                         colorscale='Emrld'),
                             hovertext=list(applied_ratio['limiting_input'])))
        new_chart = InstantiatedPlotlyNativeChart(
            fig, chart_name=chart_name, default_title=True)
        new_chart.post_processing_section_name = "Ratios"
        return new_chart

    def get_chart_initial_production(self):

        year_start = self.get_sosdisc_inputs(GlossaryEnergy.YearStart)
        initial_production = self.get_sosdisc_outputs(GlossaryEnergy.InitialPlantsTechnoProductionValue)

        study_production = self.get_sosdisc_outputs(GlossaryEnergy.TechnoTargetProductionValue)
        chart_name = f'{self.stream_name} World Production via {self.techno_name}<br>with {year_start} factories distribution'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, f'{self.stream_name} production [{self.stream_unit}]',
                                             chart_name=chart_name.capitalize())

        serie = InstanciatedSeries(
            initial_production[GlossaryEnergy.Years],
            initial_production[f'cumulative production ({self.stream_unit})'], f'Initial production by {year_start} factories', 'lines')

        study_prod = study_production[f'{self.stream_name}'].values
        new_chart.series.append(serie)
        years_study = study_production[GlossaryEnergy.Years].values.tolist()
        years_study.insert(0, year_start - 1)
        study_prod_l = study_prod.tolist()
        study_prod_l.insert(0, initial_production[f'cumulative production ({self.stream_unit})'].values[-1])
        serie = InstanciatedSeries(years_study, study_prod_l, 'Predicted production', 'lines')
        new_chart.series.append(serie)
        new_chart.post_processing_section_name = "Production & consumption"

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
            new_chart.post_processing_section_name = "Production & consumption"

            return new_chart

    def get_chart_ghg_intensity_kwh(self, ghg):
        instanciated_charts = []
        ghg_intensity_scope_1 = self.get_sosdisc_outputs('ghg_intensity_scope_1')
        ghg_intensity_scope_2 = self.get_sosdisc_outputs('ghg_intensity_scope_2')
        ghg_intensity_scope_2_details = self.get_sosdisc_outputs(f'ghg_intensity_scope_2_details_{ghg}')

        chart_name = f'{ghg} intensity of {self.stream_name} via {self.techno_name} (Scope 1 & 2)'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Mt/TWh', chart_name=chart_name, stacked_bar=True)

        serie = InstanciatedSeries(ghg_intensity_scope_1[GlossaryEnergy.Years], ghg_intensity_scope_1[ghg],'Scope 1', 'bar')
        new_chart.series.append(serie)

        serie = InstanciatedSeries(ghg_intensity_scope_2[GlossaryEnergy.Years], ghg_intensity_scope_2[ghg], 'Scope 2', 'bar')
        new_chart.series.append(serie)
        new_chart.post_processing_section_name = "GHG intensity"
        instanciated_charts.append(new_chart)

        # Scope 2 details
        if ghg_intensity_scope_2[ghg].max() > 0:
            chart_name = f'Scope 2 {ghg} intensity breakdown of {self.stream_name}'

            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Mt/TWh', chart_name=chart_name, stacked_bar=True)

            for col in ghg_intensity_scope_2_details.columns:
                if col != GlossaryEnergy.Years:
                    serie = InstanciatedSeries(ghg_intensity_scope_2[GlossaryEnergy.Years], ghg_intensity_scope_2[ghg], col, 'bar')
                    new_chart.series.append(serie)

            serie = InstanciatedSeries(ghg_intensity_scope_2[GlossaryEnergy.Years], ghg_intensity_scope_2[ghg], 'Scope 2', 'lines')
            new_chart.series.append(serie)
            new_chart.post_processing_section_name = "GHG intensity"
            instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_chart_ghg_emissions(self, ghg):
        instanciated_charts = []
        scope_1_emissions = self.get_sosdisc_outputs(GlossaryEnergy.TechnoScope1GHGEmissionsValue)
        techno_scope_2_ghg_emissions = self.get_sosdisc_outputs('techno_scope_2_ghg_emissions')

        chart_name = f'{ghg} emissions of {self.stream_name} via {self.techno_name} (Scope 1 & 2)'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, GlossaryEnergy.TechnoScope1GHGEmissions['unit'], chart_name=chart_name, stacked_bar=True)

        if ghg == GlossaryEnergy.CO2:
            flue_gas_emissions_scope_1 = self.get_sosdisc_outputs(f"{self.stream_name}.{self.techno_name}.{GlossaryEnergy.TechnoFlueGasProductionValue}")
            if flue_gas_emissions_scope_1[GlossaryEnergy.CO2FromFlueGas].min() > 0:
                serie = InstanciatedSeries(scope_1_emissions[GlossaryEnergy.Years], scope_1_emissions[ghg], 'Flue gas contribution to scope 1', 'lines')
                new_chart.series.append(serie)

        serie = InstanciatedSeries(scope_1_emissions[GlossaryEnergy.Years], scope_1_emissions[ghg], 'Scope 1', 'bar')
        new_chart.series.append(serie)

        serie = InstanciatedSeries(techno_scope_2_ghg_emissions[GlossaryEnergy.Years], techno_scope_2_ghg_emissions[ghg], 'Scope 2', 'bar')
        new_chart.series.append(serie)
        new_chart.post_processing_section_name = "GHG emissions"
        instanciated_charts.append(new_chart)

        return instanciated_charts

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
        new_chart.post_processing_section_name = "Capital & Investments"

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
        new_chart.post_processing_section_name = "Production & consumption"
        new_chart.post_processing_is_key_chart = True

        return new_chart

    def get_chart_initial_age_distrib(self):
        age_distrib = self.get_sosdisc_outputs('initial_age_distrib')
        chart_name = 'Age distribution of initial power plants / factories'

        new_chart = TwoAxesInstanciatedChart('Age', '%', chart_name=chart_name)

        serie = InstanciatedSeries(
            age_distrib['age'],
            age_distrib['distrib'], '', 'bar')

        new_chart.series.append(serie)
        new_chart.post_processing_section_name = "Production & consumption"
        return new_chart

    def get_chart_capex(self):
        cost_details = self.get_sosdisc_outputs(GlossaryEnergy.TechnoDetailedPricesValue)
        chart_name = 'Capex'
        years = cost_details[GlossaryEnergy.Years]
        capex = cost_details[f'Capex_{self.techno_name}']
        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, '$/MWh', chart_name=chart_name, y_min_zero=True)
        serie = InstanciatedSeries(years, capex, '', 'lines')

        new_chart.series.append(serie)
        new_chart.post_processing_section_name = "Prices & Capex"
        new_chart.post_processing_is_key_chart = True
        return new_chart

    def get_chart_energy_consumption(self):
        energy_consumptions = self.get_sosdisc_outputs(GlossaryEnergy.TechnoEnergyConsumptionValue)
        chart_name = f'Energy consumptions by {self.techno_name}'


        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, GlossaryEnergy.TechnoEnergyConsumption['unit'], chart_name=chart_name, stacked_bar=True)

        for col in energy_consumptions.columns:
            if col != GlossaryEnergy.Years:

                new_chart.series.append(InstanciatedSeries(
                    energy_consumptions[GlossaryEnergy.Years],
                    energy_consumptions[col], self.pimp_string(col), 'bar')
                )


        new_chart.post_processing_section_name = "Energies consumption & demand"
        new_chart.post_processing_is_key_chart = True

        return [new_chart] if len(new_chart.series) else []

    def get_chart_energy_demand(self):
        energy_demands = self.get_sosdisc_outputs(GlossaryEnergy.TechnoEnergyDemandsValue)
        chart_name = f'Energy demand by {self.techno_name}'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, GlossaryEnergy.TechnoEnergyDemands['unit'],
                                             chart_name=chart_name, stacked_bar=True)

        for col in energy_demands.columns:
            if col != GlossaryEnergy.Years:
                new_chart.series.append(InstanciatedSeries(
                    energy_demands[GlossaryEnergy.Years],
                    energy_demands[col], self.pimp_string(col), 'bar')
                )

        new_chart.post_processing_section_name = "Energies consumption & demand"

        return [new_chart] if len(new_chart.series) else []

    def get_chart_production(self):
        production_detailed = self.get_sosdisc_outputs("techno_production_infos")
        production = self.get_sosdisc_outputs(GlossaryEnergy.TechnoProductionValue)
        chart_name = f'Production of {self.stream_name} by {self.techno_name}'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, f'{self.stream_unit}', chart_name=chart_name, stacked_bar=True)


        new_chart.series.append(InstanciatedSeries(
            production_detailed[GlossaryEnergy.Years],
            production_detailed['target_production'], 'Target production (given investment and utilisation ratio)', 'lines')
        )

        new_chart.series.append(InstanciatedSeries(
            production[GlossaryEnergy.Years],
            production[f'{self.stream_name}'], 'Production achieved',
            'bar')
        )

        new_chart.post_processing_section_name = "Production & consumption"
        new_chart.post_processing_is_key_chart = True

        return new_chart

    def get_chart_production_capacity(self):
        production_detailed = self.get_sosdisc_outputs("techno_production_infos")
        chart_name = f'Production capacity of {self.stream_name} by {self.techno_name}'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, f'{self.stream_unit}', chart_name=chart_name, stacked_bar=True)

        new_chart.series.append(InstanciatedSeries(
            production_detailed[GlossaryEnergy.Years],
            production_detailed['max_theoritical_new_plant_production'], 'Maximal theoritical production (given investment)', 'lines')
        )
        new_chart.series.append(InstanciatedSeries(
            production_detailed[GlossaryEnergy.Years],
            production_detailed['target_production'], 'Target production (given investment and utilisation ratio)', 'lines')
        )
        new_chart.series.append(InstanciatedSeries(
            production_detailed[GlossaryEnergy.Years],
            production_detailed['max_theoritical_historical_plants_production'], 'Initial plants maximal theoritical production', 'bar')
        )

        new_chart.series.append(InstanciatedSeries(
            production_detailed[GlossaryEnergy.Years],
            production_detailed['max_theoritical_new_plant_production'], 'New plants maximal theoritical production',
            'bar')
        )

        new_chart.annotation_upper_left = {'Maximal theoritical production': 'Assumed no limiting input (resource or energy) and techno used at 100%.'}
        new_chart.post_processing_section_name = "Production & consumption"

        return new_chart