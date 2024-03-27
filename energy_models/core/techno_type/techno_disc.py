'''
Copyright 2022 Airbus SAS
Modifications on 2023/03/27-2023/11/16 Copyright 2023 Capgemini

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
from plotly import graph_objects as go

from climateeconomics.core.core_resources.resource_mix.resource_mix import ResourceMixModel
from climateeconomics.core.core_witness.climateeco_discipline import ClimateEcoDiscipline
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.resources_data_disc import get_static_CO2_emissions, get_static_prices
from energy_models.glossaryenergy import GlossaryEnergy
from sostrades_core.execution_engine.sos_wrapp import SoSWrapp
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart
from sostrades_core.tools.post_processing.plotly_native_charts.instantiated_plotly_native_chart import \
    InstantiatedPlotlyNativeChart


class TechnoDiscipline(SoSWrapp):
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

    years_default = np.arange(GlossaryEnergy.YeartStartDefault, 2050 + 1)

    DESC_IN = {
        GlossaryEnergy.YearStart: dict({'structuring': True}, **ClimateEcoDiscipline.YEAR_START_DESC_IN),
        GlossaryEnergy.YearEnd: dict({'structuring': True}, **GlossaryEnergy.YearEndVar),
        GlossaryEnergy.InvestLevelValue: {'type': 'dataframe', 'unit': 'G$',
                                          'dataframe_descriptor': {GlossaryEnergy.Years: ('int', [1900, 2100], False),
                                                                   GlossaryEnergy.InvestValue: ('float', None, True)},
                                          'dataframe_edition_locked': False
                                          },
        GlossaryEnergy.EnergyPricesValue: {'type': 'dataframe', 'unit': '$/MWh',
                                           'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy',
                                           "dynamic_dataframe_columns": True
                                           },
        GlossaryEnergy.EnergyCO2EmissionsValue: {'type': 'dataframe', 'unit': 'kg/kWh',
                                                 'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy',
                                                 "dynamic_dataframe_columns": True
                                                 },

        GlossaryEnergy.MarginValue: {'type': 'dataframe', 'unit': '%',
                                     'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                              GlossaryEnergy.MarginValue: ('float', None, True)}
                                     },
        GlossaryEnergy.UtilisationRatioValue: GlossaryEnergy.UtilisationRatioDf,
        GlossaryEnergy.CO2Taxes['var_name']: GlossaryEnergy.CO2Taxes,
        GlossaryEnergy.ResourcesPriceValue: {'type': 'dataframe', 'unit': '$/t',
                                             'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_resource',
                                             "dynamic_dataframe_columns": True
                                             },
        GlossaryEnergy.RessourcesCO2EmissionsValue: {'type': 'dataframe', 'unit': 'kgCO2/kg',
                                                     'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                     'namespace': 'ns_resource',
                                                     'dataframe_descriptor': {}, "dynamic_dataframe_columns": True},
        'scaling_factor_invest_level': {'type': 'float', 'default': 1e3, 'unit': '-', 'user_level': 2},
        'scaling_factor_techno_consumption': {'type': 'float', 'default': 1e3, 'unit': '-',
                                              'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_public',
                                              'user_level': 2},
        'scaling_factor_techno_production': {'type': 'float', 'default': 1e3, 'unit': '-',
                                             'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_public',
                                             'user_level': 2},
        'smooth_type': {'type': 'string', 'default': 'cons_smooth_max',
                        'possible_values': ['smooth_max', 'soft_max', 'cons_smooth_max'],
                        'user_level': 2, 'structuring': False, 'visibility': SoSWrapp.SHARED_VISIBILITY,
                        'namespace': 'ns_public'},
        'is_apply_ratio': {'type': 'bool', 'default': True, 'user_level': 2, 'structuring': True,
                           'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'is_stream_demand': {'type': 'bool', 'default': True, 'user_level': 2, 'structuring': True,
                             'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'is_apply_resource_ratio': {'type': 'bool', 'default': False, 'user_level': 2, 'structuring': True,
                                    'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_public'}}

    # -- Change output that are not clear, transform to dataframe since r_* is price
    DESC_OUT = {
        GlossaryEnergy.TechnoDetailedPricesValue: {'type': 'dataframe', 'unit': '$/MWh'},
        GlossaryEnergy.TechnoPricesValue: {'type': 'dataframe', 'unit': '$/MWh'},
        GlossaryEnergy.TechnoDetailedConsumptionValue: {'type': 'dataframe', 'unit': 'TWh or Mt'},
        GlossaryEnergy.TechnoConsumptionValue: {'type': 'dataframe', 'unit': 'TWh or Mt'},
        GlossaryEnergy.TechnoConsumptionWithoutRatioValue: {'type': 'dataframe', 'unit': 'TWh or Mt', },
        GlossaryEnergy.TechnoDetailedProductionValue: {'type': 'dataframe', 'unit': 'TWh or Mt'},
        GlossaryEnergy.TechnoProductionValue: {'type': 'dataframe', 'unit': 'TWh or Mt'},
        GlossaryEnergy.TechnoProductionWithoutRatioValue: {'type': 'dataframe', 'unit': 'TWh or Mt'},
        'age_distrib_production': {'type': 'dataframe', 'unit': 'TWh'},
        'mean_age_production': {'type': 'dataframe', 'unit': GlossaryEnergy.Years},
        GlossaryEnergy.CO2EmissionsValue: {'type': 'dataframe', 'unit': 'kg/kWh'},
        'CO2_emissions_detailed': {'type': 'dataframe', 'unit': 'kg/kWh'},
        GlossaryEnergy.LandUseRequiredValue: {'type': 'dataframe', 'unit': 'Gha'},
        'applied_ratio': {'type': 'dataframe', 'unit': '-'},
        'non_use_capital': {'type': 'dataframe', 'unit': 'G$'},
        GlossaryEnergy.InstalledPower: {'type': 'dataframe', 'unit': 'MW'},
        GlossaryEnergy.TechnoCapitalValue: GlossaryEnergy.TechnoCapitalDf
    }
    _maturity = 'Research'

    techno_name = 'Fill techno name'
    energy_name = 'Fill the energy name for this techno'

    def __init__(self, sos_name, logger: logging.Logger):
        super().__init__(sos_name=sos_name, logger=logger)
        self.dprice_dinvest = None
        self.dprod_dinvest = None
        self.dpower_dinvest = None
        self.dprod_dratio = None
        self.dprod_column_dinvest = None
        self.dprod_column_dratio = None
        self.techno_production_derivative = None
        self.techno_consumption_derivative = None
        self.dcons_column_dinvest = None
        self.dprices_demissions = None
        self.grad_total = None
        self.techno_model = None

    def setup_sos_disciplines(self):
        dynamic_inputs = {}
        dynamic_outputs = {}
        if self.get_data_in() is not None:
            self.update_default_dataframes_with_years()

            if 'is_apply_ratio' in self.get_data_in():
                year_start, year_end = self.get_sosdisc_inputs([GlossaryEnergy.YearStart, GlossaryEnergy.YearEnd])
                years = np.arange(year_start, year_end + 1)
                if self.get_sosdisc_inputs('is_stream_demand'):
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
                if self.get_sosdisc_inputs('is_apply_resource_ratio'):
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
        self.add_inputs(dynamic_inputs)
        self.add_outputs(dynamic_outputs)

    def update_default_dataframes_with_years(self):
        '''
        Update all default dataframes with years
        '''
        if GlossaryEnergy.YearStart in self.get_data_in() and GlossaryEnergy.YearEnd in self.get_data_in():
            year_start, year_end = self.get_sosdisc_inputs([GlossaryEnergy.YearStart, GlossaryEnergy.YearEnd])
            if year_start is not None and year_end is not None:
                years = np.arange(year_start, year_end + 1)
                default_margin = pd.DataFrame({GlossaryEnergy.Years: years,
                                               GlossaryEnergy.MarginValue: 110.0})

                default_utilisation_ratio = pd.DataFrame({GlossaryEnergy.Years: years,
                                                          GlossaryEnergy.UtilisationRatioValue: 100.0 * np.ones_like(
                                                              years)})

                self.set_dynamic_default_values({GlossaryEnergy.ResourcesPriceValue: get_static_prices(years),
                                                 GlossaryEnergy.RessourcesCO2EmissionsValue: get_static_CO2_emissions(
                                                     years),
                                                 GlossaryEnergy.MarginValue: default_margin,
                                                 GlossaryEnergy.UtilisationRatioValue: default_utilisation_ratio,
                                                 GlossaryEnergy.TransportCostValue: pd.DataFrame(
                                                     {GlossaryEnergy.Years: years,
                                                      'transport': 0.0}),
                                                 GlossaryEnergy.TransportMarginValue: default_margin})

    def run(self):
        '''
        Generic run for all technologies
        '''
        # -- get inputs
        inputs_dict = self.get_sosdisc_inputs()
        # -- configure class with inputs
        self.techno_model.compute(inputs_dict)

        outputs_dict = {GlossaryEnergy.TechnoDetailedPricesValue: self.techno_model.cost_details,
                        GlossaryEnergy.TechnoPricesValue: self.techno_model.cost_details[
                            [GlossaryEnergy.Years, self.techno_name, f'{self.techno_name}_wotaxes']],
                        GlossaryEnergy.TechnoDetailedConsumptionValue: self.techno_model.consumption_detailed,
                        GlossaryEnergy.TechnoConsumptionValue: self.techno_model.consumption,
                        GlossaryEnergy.TechnoConsumptionWithoutRatioValue: self.techno_model.consumption_woratio,
                        GlossaryEnergy.TechnoDetailedProductionValue: self.techno_model.production_detailed,
                        GlossaryEnergy.TechnoProductionValue: self.techno_model.production,
                        GlossaryEnergy.TechnoProductionWithoutRatioValue: self.techno_model.production_woratio,
                        'age_distrib_production': self.techno_model.age_distrib_prod_df,
                        'mean_age_production': self.techno_model.mean_age_df,
                        GlossaryEnergy.CO2EmissionsValue: self.techno_model.carbon_intensity[
                            [GlossaryEnergy.Years, self.techno_name]],
                        'CO2_emissions_detailed': self.techno_model.carbon_intensity,
                        GlossaryEnergy.LandUseRequiredValue: self.techno_model.land_use,
                        'applied_ratio': self.techno_model.applied_ratio,
                        'non_use_capital': self.techno_model.non_use_capital,
                        GlossaryEnergy.TechnoCapitalValue: self.techno_model.techno_capital,
                        GlossaryEnergy.InstalledPower: self.techno_model.installed_power,
                        }
        
        self.store_sos_outputs_values(outputs_dict)

    def compute_sos_jacobian(self):

        years = self.techno_model.years
        inputs_dict = self.get_sosdisc_inputs()
        outputs_dict = self.get_sosdisc_outputs()
        invest_level = inputs_dict[GlossaryEnergy.InvestLevelValue]
        scaling_factor_invest_level = inputs_dict['scaling_factor_invest_level']
        scaling_factor_techno_production = inputs_dict['scaling_factor_techno_production']
        production = outputs_dict[GlossaryEnergy.TechnoProductionValue]
        consumption = outputs_dict[GlossaryEnergy.TechnoConsumptionValue]
        production_wo_ratio = outputs_dict[GlossaryEnergy.TechnoProductionWithoutRatioValue]
        consumption_wo_ratio = outputs_dict[GlossaryEnergy.TechnoConsumptionWithoutRatioValue]
        installed_power = outputs_dict[GlossaryEnergy.InstalledPower]
        utilisation_ratio = inputs_dict[GlossaryEnergy.UtilisationRatioValue][
            GlossaryEnergy.UtilisationRatioValue].values
        ratio_df = self.techno_model.ratio_df
        dcapex_dinvest = self.techno_model.compute_dcapex_dinvest(invest_level.loc[invest_level[GlossaryEnergy.Years]
                                                                                   <= self.techno_model.year_end][
                                                                      GlossaryEnergy.InvestValue].values * scaling_factor_invest_level,
                                                                  self.techno_model.techno_infos_dict)

        crf = self.techno_model.compute_crf(
            self.techno_model.techno_infos_dict)
        dfactory_dinvest = dcapex_dinvest * \
                           (crf + self.techno_model.techno_infos_dict['Opex_percentage'])

        margin = self.techno_model.margin[GlossaryEnergy.MarginValue].values
        self.dprice_dinvest = dfactory_dinvest * np.split(margin, len(margin)) / \
                              100.0

        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoPricesValue, f'{self.techno_name}'),
            (GlossaryEnergy.InvestLevelValue, GlossaryEnergy.InvestValue),
            self.dprice_dinvest * scaling_factor_invest_level)
        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoPricesValue, f'{self.techno_name}_wotaxes'),
            (GlossaryEnergy.InvestLevelValue, GlossaryEnergy.InvestValue),
            self.dprice_dinvest * scaling_factor_invest_level)

        capex = outputs_dict[GlossaryEnergy.TechnoDetailedPricesValue][
            f'Capex_{self.techno_name}'].values
        # Compute jacobian for enegy_type production
        self.dprod_dinvest = self.techno_model.compute_dprod_dinvest(
            capex, invest_level[GlossaryEnergy.InvestValue].values * scaling_factor_invest_level,
            self.techno_model.invest_before_ystart[GlossaryEnergy.InvestValue].values,
            self.techno_model.techno_infos_dict, dcapex_dinvest)

        self.dpower_dinvest = self.techno_model.compute_dpower_dinvest(
            capex, invest_level[GlossaryEnergy.InvestValue].values * scaling_factor_invest_level,
            self.techno_model.techno_infos_dict, dcapex_dinvest, inputs_dict['scaling_factor_techno_consumption'])

        applied_ratio = outputs_dict['applied_ratio']['applied_ratio'].values
        dprod_name_dinvest = (
                                     self.dprod_dinvest.T * applied_ratio * utilisation_ratio / 100).T * scaling_factor_invest_level / scaling_factor_techno_production
        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoProductionValue, f'{self.energy_name} ({self.techno_model.product_energy_unit})'),
            (GlossaryEnergy.InvestLevelValue, GlossaryEnergy.InvestValue),
            dprod_name_dinvest)

        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoProductionValue, f'{self.energy_name} ({self.techno_model.product_energy_unit})'),
            (GlossaryEnergy.InvestLevelValue, GlossaryEnergy.InvestValue),
            dprod_name_dinvest)

        dprod_dutilisation_ratio = np.diag(
            applied_ratio * production_wo_ratio[f'{self.energy_name} ({self.techno_model.product_energy_unit})'] / 100.)
        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoProductionValue, f'{self.energy_name} ({self.techno_model.product_energy_unit})'),
            (GlossaryEnergy.UtilisationRatioValue, GlossaryEnergy.UtilisationRatioValue),
            dprod_dutilisation_ratio
        )

        # ---Gradient main techno prod vs each ratio
        dapplied_ratio_dratio = self.techno_model.compute_dapplied_ratio_dratios(
            inputs_dict['is_apply_ratio'])
        self.dprod_dratio = {}
        if GlossaryEnergy.AllStreamsDemandRatioValue in inputs_dict.keys():
            for ratio_name in inputs_dict[GlossaryEnergy.AllStreamsDemandRatioValue].columns:
                if ratio_name != GlossaryEnergy.Years:
                    production_woratio = self.techno_model.production_woratio[
                        f'{self.energy_name} ({self.techno_model.product_energy_unit})']
                    self.dprod_dratio[ratio_name] = self.techno_model.compute_dprod_dratio(
                        production_woratio, ratio_name=ratio_name,
                        dapplied_ratio_dratio=dapplied_ratio_dratio)
                    self.set_partial_derivative_for_other_types(
                        (GlossaryEnergy.TechnoProductionValue,
                         f'{self.energy_name} ({self.techno_model.product_energy_unit})'),
                        (GlossaryEnergy.AllStreamsDemandRatioValue, ratio_name),
                        self.dprod_dratio[ratio_name] / 100.)
                    dland_use_dratio = self.techno_model.compute_dprod_dratio(
                        self.techno_model.land_use_woratio[
                            f'{self.techno_model.name} (Gha)'], ratio_name=ratio_name,
                        dapplied_ratio_dratio=dapplied_ratio_dratio)
                    self.set_partial_derivative_for_other_types(
                        (GlossaryEnergy.LandUseRequiredValue, f'{self.techno_model.name} (Gha)'),
                        (GlossaryEnergy.AllStreamsDemandRatioValue, ratio_name),
                        dland_use_dratio / 100.)
        if 'all_resource_ratio_usable_demand' in inputs_dict.keys():
            for ratio_name in inputs_dict['all_resource_ratio_usable_demand'].columns:
                if ratio_name != GlossaryEnergy.Years:
                    production_woratio = self.techno_model.production_woratio[
                        f'{self.energy_name} ({self.techno_model.product_energy_unit})']
                    self.dprod_dratio[ratio_name] = self.techno_model.compute_dprod_dratio(
                        production_woratio, ratio_name=ratio_name,
                        dapplied_ratio_dratio=dapplied_ratio_dratio)
                    self.set_partial_derivative_for_other_types(
                        (GlossaryEnergy.TechnoProductionValue,
                         f'{self.energy_name} ({self.techno_model.product_energy_unit})'),
                        ('all_resource_ratio_usable_demand', ratio_name),
                        self.dprod_dratio[ratio_name] / 100.)
                    dland_use_dratio = self.techno_model.compute_dprod_dratio(
                        self.techno_model.land_use_woratio[
                            f'{self.techno_model.name} (Gha)'], ratio_name=ratio_name,
                        dapplied_ratio_dratio=dapplied_ratio_dratio)
                    self.set_partial_derivative_for_other_types(
                        (GlossaryEnergy.LandUseRequiredValue, f'{self.techno_model.name} (Gha)'),
                        ('all_resource_ratio_usable_demand', ratio_name),
                        dland_use_dratio / 100.)

        # Compute jacobian for other energy production/consumption
        self.dprod_column_dinvest = {}
        self.dprod_column_dratio = {}
        self.techno_production_derivative = {}
        for column in production:
            dprod_column_dinvest = self.dprod_dinvest.copy()
            if column not in [GlossaryEnergy.Years, f'{self.energy_name} ({self.techno_model.product_energy_unit})']:
                var_prod = (production[column] /
                            production[f'{self.energy_name} ({self.techno_model.product_energy_unit})']).fillna(
                    0)
                for line in range(len(years)):
                    # Problem when invest is zero at the first year and prod
                    # consequently zero (but gradient is not null)
                    if self.techno_model.is_invest_before_year(
                            years[line] - self.techno_model.techno_infos_dict[GlossaryEnergy.ConstructionDelay]) \
                            and var_prod[line] == 0.0 and self.dprod_dinvest[line, :].sum() != 0.0 and line != len(
                        years) - 1:
                        var_prod[line] = var_prod[line + 1]
                    dprod_column_dinvest[line, :] = self.dprod_dinvest[line,
                                                    :] * var_prod[line]
                self.dprod_column_dinvest[column] = dprod_column_dinvest
                self.set_partial_derivative_for_other_types(
                    (GlossaryEnergy.TechnoProductionValue, column),
                    (GlossaryEnergy.InvestLevelValue, GlossaryEnergy.InvestValue),
                    (
                                dprod_column_dinvest.T * applied_ratio * utilisation_ratio / 100).T * scaling_factor_invest_level / scaling_factor_techno_production)

                dprod_dutilisation_ratio = np.diag(applied_ratio * production_wo_ratio[column] / 100.)
                self.set_partial_derivative_for_other_types(
                    (GlossaryEnergy.TechnoProductionValue, column),
                    (GlossaryEnergy.UtilisationRatioValue, GlossaryEnergy.UtilisationRatioValue),
                    dprod_dutilisation_ratio
                )

                self.techno_production_derivative[column] = (
                                                                        dprod_column_dinvest.T * applied_ratio).T * scaling_factor_invest_level / scaling_factor_techno_production

                # ---Gradient other techno prods vs each ratio
                self.dprod_column_dratio[column] = {}
                for ratio_name in ratio_df.columns:
                    if GlossaryEnergy.AllStreamsDemandRatioValue in inputs_dict.keys():
                        if ratio_name in inputs_dict[
                            GlossaryEnergy.AllStreamsDemandRatioValue].columns and ratio_name != GlossaryEnergy.Years:
                            production_woratio = self.techno_model.production_woratio[
                                column]
                            self.dprod_column_dratio[column][ratio_name] = self.techno_model.compute_dprod_dratio(
                                production_woratio, ratio_name=ratio_name,
                                dapplied_ratio_dratio=dapplied_ratio_dratio)
                            self.set_partial_derivative_for_other_types(
                                (GlossaryEnergy.TechnoProductionValue, column),
                                (GlossaryEnergy.AllStreamsDemandRatioValue, ratio_name),
                                self.dprod_column_dratio[column][ratio_name] / 100.)
                    if 'all_resource_ratio_usable_demand' in inputs_dict.keys():
                        if ratio_name in inputs_dict[
                            'all_resource_ratio_usable_demand'].columns and ratio_name != GlossaryEnergy.Years:
                            production_woratio = self.techno_model.production_woratio[
                                column]
                            self.dprod_column_dratio[column][ratio_name] = self.techno_model.compute_dprod_dratio(
                                production_woratio, ratio_name=ratio_name,
                                dapplied_ratio_dratio=dapplied_ratio_dratio)
                            self.set_partial_derivative_for_other_types(
                                (GlossaryEnergy.TechnoProductionValue, column),
                                ('all_resource_ratio_usable_demand', ratio_name),
                                self.dprod_column_dratio[column][ratio_name] / 100.)
        self.techno_consumption_derivative = {}
        for column in consumption:

            if column != GlossaryEnergy.Years:

                if column in [f'{resource} (Mt)' for resource in self.techno_model.construction_resource_list]:
                    var_cons = (consumption[column] /
                                installed_power['new_power_production']).fillna(
                        0)
                    self.dcons_column_dinvest = self.dpower_dinvest.copy()
                else:
                    var_cons = (consumption[column] /
                                production[f'{self.energy_name} ({self.techno_model.product_energy_unit})']).fillna(
                        0)
                    self.dcons_column_dinvest = self.dprod_dinvest.copy()

                for line in range(len(years)):
                    # Problem when invest is zero at the first year and prod
                    # consequently zero (but gradient is not null)
                    if self.techno_model.is_invest_before_year(
                            years[line] - self.techno_model.techno_infos_dict[GlossaryEnergy.ConstructionDelay]) \
                            and var_cons[line] == 0.0 and self.dprod_dinvest[line, :].sum() != 0.0 and line != len(
                        years) - 1:
                        var_cons[line] = var_cons[line + 1]
                    self.dcons_column_dinvest[line, :] = self.dprod_dinvest[line,
                                                         :] * var_cons[line]
                    if column in [f'{resource} (Mt)' for resource in self.techno_model.construction_resource_list]:
                        self.dcons_column_dinvest[line, :] = self.dpower_dinvest[line,
                                                             :] * var_cons[line]
                if column in [f'{resource} (Mt)' for resource in self.techno_model.construction_resource_list]:
                    applied_ratio_construction = 1
                    self.set_partial_derivative_for_other_types(
                        (GlossaryEnergy.TechnoConsumptionValue, column),
                        (GlossaryEnergy.InvestLevelValue, GlossaryEnergy.InvestValue),
                        (
                                    self.dcons_column_dinvest.T * applied_ratio_construction).T * scaling_factor_invest_level / scaling_factor_techno_production)
                    self.techno_consumption_derivative[column] = (
                                                                             self.dcons_column_dinvest.T * applied_ratio_construction).T * scaling_factor_invest_level / scaling_factor_techno_production

                else:
                    self.set_partial_derivative_for_other_types(
                        (GlossaryEnergy.TechnoConsumptionValue, column),
                        (GlossaryEnergy.InvestLevelValue, GlossaryEnergy.InvestValue),
                        (
                                    self.dcons_column_dinvest.T * applied_ratio * utilisation_ratio / 100).T * scaling_factor_invest_level / scaling_factor_techno_production)
                    self.techno_consumption_derivative[column] = (
                                                                             self.dcons_column_dinvest.T * applied_ratio).T * scaling_factor_invest_level / scaling_factor_techno_production
                self.set_partial_derivative_for_other_types(
                    (GlossaryEnergy.TechnoConsumptionWithoutRatioValue, column),
                    (GlossaryEnergy.InvestLevelValue, GlossaryEnergy.InvestValue),
                    self.dcons_column_dinvest * scaling_factor_invest_level / scaling_factor_techno_production)

                dcons_dutilisation_ratio = np.diag(applied_ratio * consumption_wo_ratio[column] / 100.)
                self.set_partial_derivative_for_other_types(
                    (GlossaryEnergy.TechnoConsumptionValue, column),
                    (GlossaryEnergy.UtilisationRatioValue, GlossaryEnergy.UtilisationRatioValue),
                    dcons_dutilisation_ratio
                )
                # ---Gradient techno cons vs each ratio
                for ratio_name in ratio_df.columns:
                    if GlossaryEnergy.AllStreamsDemandRatioValue in inputs_dict.keys():
                        if ratio_name in inputs_dict[
                            GlossaryEnergy.AllStreamsDemandRatioValue].columns and ratio_name != GlossaryEnergy.Years:
                            if column in [f'{resource} (Mt)' for resource in
                                          self.techno_model.construction_resource_list]:
                                pass
                            else:
                                consumption_woratio = self.techno_model.consumption_woratio[
                                    column]
                                dprod_dratio = self.techno_model.compute_dprod_dratio(
                                    consumption_woratio, ratio_name=ratio_name,
                                    dapplied_ratio_dratio=dapplied_ratio_dratio)
                                self.set_partial_derivative_for_other_types(
                                    (GlossaryEnergy.TechnoConsumptionValue, column),
                                    (GlossaryEnergy.AllStreamsDemandRatioValue, ratio_name),
                                    dprod_dratio / 100.)
                    if 'all_resource_ratio_usable_demand' in inputs_dict.keys():
                        if ratio_name in inputs_dict[
                            'all_resource_ratio_usable_demand'].columns and ratio_name != GlossaryEnergy.Years:
                            if column in [f'{resource} (Mt)' for resource in
                                          self.techno_model.construction_resource_list]:
                                pass
                            else:
                                consumption_woratio = self.techno_model.consumption_woratio[
                                    column]
                                dprod_dratio = self.techno_model.compute_dprod_dratio(
                                    consumption_woratio, ratio_name=ratio_name,
                                    dapplied_ratio_dratio=dapplied_ratio_dratio)
                                self.set_partial_derivative_for_other_types(
                                    (GlossaryEnergy.TechnoConsumptionValue, column),
                                    ('all_resource_ratio_usable_demand', ratio_name),
                                    dprod_dratio / 100.)

        dland_use_dinvest = self.techno_model.compute_dlanduse_dinvest()
        derivate_land_use = dland_use_dinvest.copy()

        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.LandUseRequiredValue, f'{self.techno_model.name} (Gha)'),
            (GlossaryEnergy.InvestLevelValue, GlossaryEnergy.InvestValue),
            derivate_land_use * applied_ratio[:, np.newaxis] * scaling_factor_invest_level)

        '''
        non_use capital gradients vs invest_level and all_stream_demand_ratio
        '''
        dnon_use_capital_dinvest, dtechnocapital_dinvest = self.techno_model.compute_dnon_usecapital_dinvest(
            dcapex_dinvest, self.dprod_dinvest)
        self.set_partial_derivative_for_other_types(
            ('non_use_capital', self.techno_model.name),
            (GlossaryEnergy.InvestLevelValue, GlossaryEnergy.InvestValue),
            dnon_use_capital_dinvest)

        techno_capital = self.get_sosdisc_outputs(GlossaryEnergy.TechnoCapitalValue)[GlossaryEnergy.Capital].values
        d_non_use_capital_d_utilisation_ratio = np.diag(
            - techno_capital * applied_ratio / 100.
        )
        self.set_partial_derivative_for_other_types(
            ('non_use_capital', self.techno_model.name),
            (GlossaryEnergy.UtilisationRatioValue, GlossaryEnergy.UtilisationRatioValue),
            d_non_use_capital_d_utilisation_ratio)

        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoCapitalValue, GlossaryEnergy.Capital),
            (GlossaryEnergy.InvestLevelValue, GlossaryEnergy.InvestValue),
            dtechnocapital_dinvest)

        dapplied_ratio_dratio = self.techno_model.compute_dapplied_ratio_dratios()
        for ratio_name in ratio_df.columns:
            if GlossaryEnergy.AllStreamsDemandRatioValue in inputs_dict.keys():
                if ratio_name in inputs_dict[
                    GlossaryEnergy.AllStreamsDemandRatioValue].columns and ratio_name != GlossaryEnergy.Years:
                    dnon_use_capital_dratio = self.techno_model.compute_dnon_usecapital_dratio(
                        dapplied_ratio_dratio[ratio_name])
                    self.set_partial_derivative_for_other_types(
                        ('non_use_capital', self.techno_model.name),
                        (GlossaryEnergy.AllStreamsDemandRatioValue, ratio_name),
                        np.identity(len(years)) * dnon_use_capital_dratio / 100.0)
            if 'all_resource_ratio_usable_demand' in inputs_dict.keys():
                if ratio_name in inputs_dict[
                    'all_resource_ratio_usable_demand'].columns and ratio_name != GlossaryEnergy.Years:
                    dnon_use_capital_dratio = self.techno_model.compute_dnon_usecapital_dratio(
                        dapplied_ratio_dratio[ratio_name])
                    self.set_partial_derivative_for_other_types(
                        ('non_use_capital', self.techno_model.name),
                        ('all_resource_ratio_usable_demand', ratio_name),
                        np.identity(len(years)) * dnon_use_capital_dratio / 100.0)

    def set_partial_derivatives_techno(self, grad_dict, carbon_emissions, grad_dict_resources={}):
        """
        Generic method to set partial derivatives of techno_prices / energy_prices, energy_CO2_emissions and dco2_emissions/denergy_co2_emissions
        """
        self.dprices_demissions = {}
        self.grad_total = {}
        for energy, value in grad_dict.items():
            self.grad_total[energy] = value * \
                                      self.techno_model.margin[GlossaryEnergy.MarginValue].values / 100.0
            self.set_partial_derivative_for_other_types(
                (GlossaryEnergy.TechnoPricesValue, self.techno_name),
                (GlossaryEnergy.EnergyPricesValue, energy),
                self.grad_total[energy])
            self.set_partial_derivative_for_other_types(
                (GlossaryEnergy.TechnoPricesValue, f'{self.techno_name}_wotaxes'),
                (GlossaryEnergy.EnergyPricesValue, energy),
                self.grad_total[energy])
            # Means it has no sense to compute carbon emissions as for CC and
            # CS
            if carbon_emissions is not None:
                self.set_partial_derivative_for_other_types(
                    (GlossaryEnergy.CO2EmissionsValue, self.techno_name),
                    (GlossaryEnergy.EnergyCO2EmissionsValue, energy),
                    value)

                # to manage gradient when carbon_emissions is null:
                # sign_carbon_emissions = 1 if carbon_emissions >=0, -1 if
                # carbon_emissions < 0
                sign_carbon_emissions = np.sign(
                    carbon_emissions.loc[carbon_emissions[GlossaryEnergy.Years] <= self.techno_model.year_end][
                        self.techno_name]) + 1 - np.sign(
                    carbon_emissions.loc[carbon_emissions[GlossaryEnergy.Years] <= self.techno_model.year_end][
                        self.techno_name]) ** 2
                grad_on_co2_tax = value * \
                                  self.techno_model.CO2_taxes.loc[
                                      self.techno_model.CO2_taxes[GlossaryEnergy.Years] <= self.techno_model.year_end][
                                      GlossaryEnergy.CO2Tax].values[:, np.newaxis] * np.maximum(
                    0, sign_carbon_emissions).values

                self.dprices_demissions[energy] = grad_on_co2_tax
                self.set_partial_derivative_for_other_types(
                    (GlossaryEnergy.TechnoPricesValue, self.techno_name),
                    (GlossaryEnergy.EnergyCO2EmissionsValue, energy),
                    self.dprices_demissions[energy])
        if carbon_emissions is not None:
            dCO2_taxes_factory = (self.techno_model.CO2_taxes[GlossaryEnergy.Years] <=
                                  self.techno_model.carbon_intensity[GlossaryEnergy.Years].max(
                                  )) * self.techno_model.carbon_intensity[self.techno_name].clip(0).values
            dtechno_prices_dCO2_taxes = dCO2_taxes_factory

            self.set_partial_derivative_for_other_types(
                (GlossaryEnergy.TechnoPricesValue, self.techno_name),
                (GlossaryEnergy.CO2TaxesValue, GlossaryEnergy.CO2Tax),
                dtechno_prices_dCO2_taxes.values * np.identity(len(self.techno_model.years)))

        for resource, value in grad_dict_resources.items():
            self.set_partial_derivative_for_other_types(
                (GlossaryEnergy.TechnoPricesValue, self.techno_name),
                (GlossaryEnergy.ResourcesPriceValue, resource),
                value * self.techno_model.margin[GlossaryEnergy.MarginValue].values / 100.0)
            self.set_partial_derivative_for_other_types(
                (GlossaryEnergy.TechnoPricesValue, f'{self.techno_name}_wotaxes'),
                (GlossaryEnergy.ResourcesPriceValue, resource),
                value * self.techno_model.margin[GlossaryEnergy.MarginValue].values / 100.0)

            if carbon_emissions is not None:
                # resources carbon emissions
                self.set_partial_derivative_for_other_types(
                    (GlossaryEnergy.CO2EmissionsValue, self.techno_name),
                    (GlossaryEnergy.RessourcesCO2EmissionsValue, resource),
                    value)

                sign_carbon_emissions = np.sign(carbon_emissions.loc[carbon_emissions[GlossaryEnergy.Years] <=
                                                                     self.techno_model.year_end][
                                                    self.techno_name]) + 1 - np.sign(
                    carbon_emissions.loc[carbon_emissions[GlossaryEnergy.Years] <=
                                         self.techno_model.year_end][self.techno_name]) ** 2
                grad_on_co2_tax = value * \
                                  self.techno_model.CO2_taxes.loc[self.techno_model.CO2_taxes[GlossaryEnergy.Years] <=
                                                                  self.techno_model.year_end][
                                      GlossaryEnergy.CO2Tax].values[:, np.newaxis] * np.maximum(0,
                                                                                                sign_carbon_emissions).values

                self.dprices_demissions[resource] = grad_on_co2_tax
                self.set_partial_derivative_for_other_types(
                    (GlossaryEnergy.TechnoPricesValue, self.techno_name),
                    (GlossaryEnergy.RessourcesCO2EmissionsValue, resource),
                    self.dprices_demissions[resource])

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['Detailed prices',
                      'Consumption and production',
                      'Initial Production',
                      'Factory Mean Age',
                      'CO2 emissions',
                      GlossaryEnergy.UtilisationRatioValue,
                      'Non-Use Capital',
                      'Power production']
        if self.get_sosdisc_inputs('is_apply_ratio'):
            chart_list.extend(['Applied Ratio'])
        chart_filters.append(ChartFilter(
            'Charts', chart_list, chart_list, 'charts'))

        price_unit_list = ['$/MWh', '$/t']
        chart_filters.append(ChartFilter(
            'Price unit', price_unit_list, price_unit_list, 'price_unit'))
        return chart_filters

    def get_post_processing_list(self, filters=None):

        # For the outputs, making a graph for block fuel_production vs range and blocktime vs
        # range

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
            new_chart = self.get_chart_power_production(technos_info_dict)
            if new_chart is not None:
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

        techno_detailed_prices = self.get_sosdisc_outputs(
            GlossaryEnergy.TechnoDetailedPricesValue)
        chart_name = f'Price breakdown of {self.techno_name}'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Prices [$/MWh]',
                                             chart_name=chart_name, stacked_bar=True)

        if 'percentage_resource' in self.get_data_in():
            percentage_resource = self.get_sosdisc_inputs(
                'percentage_resource')
            new_chart.annotation_upper_left = {
                'Percentage of total price at starting year': f'{percentage_resource[self.energy_name][0]} %'}
            tot_price = techno_detailed_prices[self.techno_name].values / \
                        (percentage_resource[self.energy_name] / 100.)
            serie = InstanciatedSeries(
                techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
                tot_price.tolist(), 'Total price without percentage', 'lines')
            new_chart.series.append(serie)
        # Add total price
        tot_price_mwh = techno_detailed_prices[self.techno_name].values
        serie = InstanciatedSeries(
            techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
            tot_price_mwh.tolist(), 'Total price', 'lines')

        new_chart.series.append(serie)

        factory_price_mwh = techno_detailed_prices[f'{self.techno_name}_factory'].values
        # Factory price
        serie = InstanciatedSeries(
            techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
            factory_price_mwh.tolist(), 'Factory', 'bar')

        new_chart.series.append(serie)

        if 'energy_costs' in techno_detailed_prices:
            # energy_costs
            ec_price_mwh = techno_detailed_prices['energy_costs'].values
            serie = InstanciatedSeries(
                techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
                ec_price_mwh.tolist(), 'Energy costs', 'bar')

            new_chart.series.append(serie)

        transport_price_mwh = techno_detailed_prices['transport'].values
        # Transport price
        serie = InstanciatedSeries(
            techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
            transport_price_mwh.tolist(), 'Transport', 'bar')

        new_chart.series.append(serie)
        # CO2 taxes
        co2_price_mwh = techno_detailed_prices['CO2_taxes_factory'].values
        serie = InstanciatedSeries(
            techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
            co2_price_mwh.tolist(), 'CO2 taxes due to production', 'bar')
        new_chart.series.append(serie)

        serie = InstanciatedSeries(
            techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
            techno_detailed_prices[GlossaryEnergy.MarginValue].values.tolist(), 'Margin', 'bar')
        new_chart.series.append(serie)

        return new_chart

    def get_chart_detailed_price_in_dollar_kg(self):

        techno_detailed_prices = self.get_sosdisc_outputs(
            GlossaryEnergy.TechnoDetailedPricesValue)

        chart_name = f'Price breakdown of {self.techno_name}'
        data_fuel_dict = self.get_sosdisc_inputs('data_fuel_dict')

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Prices [$/t]', stacked_bar=True,
                                             chart_name=chart_name)

        if 'percentage_resource' in self.get_data_in():
            percentage_resource = self.get_sosdisc_inputs(
                'percentage_resource')
            new_chart.annotation_upper_left = {
                'Percentage of total price at starting year': f'{percentage_resource[self.energy_name][0]} %'}
            tot_price = techno_detailed_prices[self.techno_name].values / \
                        (percentage_resource[self.energy_name] / 100.)

            serie = InstanciatedSeries(
                techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
                tot_price.tolist(), 'Total price without percentage', 'lines')
            new_chart.series.append(serie)
        # Add total price

        techno_kg_price = techno_detailed_prices[self.techno_name].values * \
                          data_fuel_dict['calorific_value']
        serie = InstanciatedSeries(
            techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
            techno_kg_price.tolist(), 'Total price', 'lines')

        new_chart.series.append(serie)

        # Factory price
        techno_kg_price = techno_detailed_prices[f'{self.techno_name}_factory'].values * \
                          data_fuel_dict['calorific_value']
        serie = InstanciatedSeries(
            techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
            techno_kg_price.tolist(), 'Factory', 'bar')

        new_chart.series.append(serie)
        if 'energy_costs' in techno_detailed_prices:
            # energy_costs
            techno_kg_price = techno_detailed_prices['energy_costs'].values * \
                              data_fuel_dict['calorific_value']
            serie = InstanciatedSeries(
                techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
                techno_kg_price.tolist(), 'Energy costs', 'bar')

            new_chart.series.append(serie)
        # Transport price
        techno_kg_price = techno_detailed_prices['transport'].values * \
                          data_fuel_dict['calorific_value']
        serie = InstanciatedSeries(
            techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
            techno_kg_price.tolist(), 'Transport', 'bar')

        new_chart.series.append(serie)
        # CO2 taxes
        techno_kg_price = techno_detailed_prices['CO2_taxes_factory'].values * \
                          data_fuel_dict['calorific_value']
        serie = InstanciatedSeries(
            techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
            techno_kg_price.tolist(), 'CO2 taxes due to production', 'bar')
        new_chart.series.append(serie)

        # margin
        techno_kg_price = techno_detailed_prices[GlossaryEnergy.MarginValue].values * \
                          data_fuel_dict['calorific_value']
        serie = InstanciatedSeries(
            techno_detailed_prices[GlossaryEnergy.Years].values.tolist(),
            techno_kg_price.tolist(), 'Margin', 'bar')
        new_chart.series.append(serie)

        return new_chart

    def get_chart_investments(self):
        # Chart for input investments
        input_investments = self.get_sosdisc_inputs(GlossaryEnergy.InvestLevelValue)
        scaling_factor_invest_level = self.get_sosdisc_inputs(
            'scaling_factor_invest_level')

        chart_name = f'Investments in {self.techno_name}'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Investments [M$]',
                                             chart_name=chart_name, stacked_bar=True)
        invest = input_investments[GlossaryEnergy.InvestValue].values * \
                 scaling_factor_invest_level
        serie = InstanciatedSeries(
            input_investments[GlossaryEnergy.Years].values.tolist(),
            invest.tolist(), '', 'bar')

        new_chart.series.append(serie)

        return new_chart

    def get_charts_consumption_and_production(self):
        instanciated_charts = []
        # Charts for consumption and prod
        techno_consumption = self.get_sosdisc_outputs(
            GlossaryEnergy.TechnoDetailedConsumptionValue)
        techno_production = self.get_sosdisc_outputs(
            GlossaryEnergy.TechnoDetailedProductionValue)
        chart_name = f'{self.techno_name} technology energy Production & consumption<br>with input investments'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Energy [TWh]',
                                             chart_name=chart_name.capitalize(), stacked_bar=True)

        for reactant in techno_consumption.columns:
            if reactant != GlossaryEnergy.Years and reactant.endswith('(TWh)'):
                energy_twh = -techno_consumption[reactant].values
                legend_title = f'{reactant} consumption'.replace(
                    "(TWh)", "")
                serie = InstanciatedSeries(
                    techno_consumption[GlossaryEnergy.Years].values.tolist(),
                    energy_twh.tolist(), legend_title, 'bar')

                new_chart.series.append(serie)

        for products in techno_production.columns:
            if products != GlossaryEnergy.Years and products.endswith('(TWh)'):
                energy_twh = techno_production[products].values
                legend_title = f'{products} production'.replace(
                    "(TWh)", "")
                serie = InstanciatedSeries(
                    techno_production[GlossaryEnergy.Years].values.tolist(),
                    energy_twh.tolist(), legend_title, 'bar')

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
                    techno_consumption[GlossaryEnergy.Years].values.tolist(),
                    mass.tolist(), legend_title, 'bar')
                new_chart.series.append(serie)
        for product in techno_production.columns:
            if product != GlossaryEnergy.Years and product.endswith('(Mt)'):
                legend_title = f'{product} production'.replace(
                    "(Mt)", "")
                # 1GT = 1e9T = 1e12 kg
                mass = techno_production[product].values
                serie = InstanciatedSeries(
                    techno_production[GlossaryEnergy.Years].values.tolist(),
                    mass.tolist(), legend_title, 'bar')
                new_chart.series.append(serie)

        if kg_values_consumption > 0 or kg_values_production > 0:
            instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_chart_applied_ratio(self):
        # Charts for consumption and prod
        applied_ratio = self.get_sosdisc_outputs(
            'applied_ratio')
        chart_name = f'Ratio applied on {self.techno_name} technology energy Production'
        fig = go.Figure()
        fig.add_trace(go.Bar(x=applied_ratio[GlossaryEnergy.Years].values.tolist(),
                             y=applied_ratio['applied_ratio'].values.tolist(),
                             marker=dict(color=applied_ratio['applied_ratio'].values.tolist(),
                                         colorscale='Emrld'),
                             hovertext=applied_ratio['min_ratio_name'].values.tolist()))
        new_chart = InstantiatedPlotlyNativeChart(
            fig, chart_name=chart_name, default_title=True)
        return new_chart

    def get_chart_initial_production(self):

        year_start = self.get_sosdisc_inputs(
            GlossaryEnergy.YearStart)
        initial_production = self.get_sosdisc_inputs(
            'initial_production')
        initial_age_distrib = self.get_sosdisc_inputs(
            'initial_age_distrib')
        initial_prod = pd.DataFrame({'age': initial_age_distrib['age'].values,
                                     'distrib': initial_age_distrib['distrib'].values, })
        initial_prod['energy (TWh)'] = initial_prod['distrib'] / \
                                       100.0 * initial_production
        initial_prod[GlossaryEnergy.Years] = year_start - initial_prod['age']
        initial_prod.sort_values(GlossaryEnergy.Years, inplace=True)
        initial_prod['cum energy (TWh)'] = initial_prod['energy (TWh)'].cumsum(
        )
        study_production = self.get_sosdisc_outputs(
            GlossaryEnergy.TechnoDetailedProductionValue)
        chart_name = f'{self.energy_name} World Production via {self.techno_name}<br>with 2020 factories distribution'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, f'{self.energy_name} production [TWh]',
                                             chart_name=chart_name.capitalize())

        serie = InstanciatedSeries(
            initial_prod[GlossaryEnergy.Years].values.tolist(),
            initial_prod[f'cum energy (TWh)'].values.tolist(), 'Initial production by 2020 factories', 'lines')

        study_prod = study_production[f'{self.energy_name} (TWh)'].values
        new_chart.series.append(serie)
        years_study = study_production[GlossaryEnergy.Years].values.tolist()
        years_study.insert(0, year_start - 1)
        study_prod_l = study_prod.tolist()
        study_prod_l.insert(
            0, initial_prod[f'cum energy (TWh)'].values.tolist()[-1])
        serie = InstanciatedSeries(
            years_study,
            study_prod_l, 'Predicted production', 'lines')
        new_chart.series.append(serie)

        return new_chart

    def get_chart_age_distribution_production(self):
        age_distrib_production = self.get_sosdisc_outputs(
            'age_distrib_production')
        chart_name = f'{self.techno_name} factories age in term of TWh of {self.energy_name} production'

        if GlossaryEnergy.Years in age_distrib_production.columns:
            new_chart = TwoAxesInstanciatedChart('age', f'{self.energy_name} production [TWh]',
                                                 chart_name=chart_name.capitalize())
            years = age_distrib_production[GlossaryEnergy.Years].values
            filtered_years = list(
                set([year for year in years if year % 10 == 0]))
            filtered_years.sort()

            for year in filtered_years:
                filtered_df = age_distrib_production.loc[
                    age_distrib_production[GlossaryEnergy.Years] == year].sort_values(
                    'age')
                serie = InstanciatedSeries(
                    filtered_df['age'].values.tolist(),
                    filtered_df['distrib_prod (TWh)'].values.tolist(), f'{year}', 'lines')

                new_chart.series.append(serie)

            return new_chart

    def get_chart_factory_mean_age(self):
        age_distrib_production = self.get_sosdisc_outputs(
            'mean_age_production')

        if GlossaryEnergy.Years in age_distrib_production.columns:
            chart_name = f'{self.techno_name} factories average age'

            new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Mean age',
                                                 chart_name=chart_name.capitalize())

            serie = InstanciatedSeries(
                age_distrib_production[GlossaryEnergy.Years].values.tolist(),
                age_distrib_production['mean age'].values.tolist(), '', 'lines')

            new_chart.series.append(serie)

            return new_chart

    def get_chart_carbon_intensity_kwh(self):

        carbon_emissions = self.get_sosdisc_outputs('CO2_emissions_detailed')
        chart_name = f'Carbon intensity of {self.energy_name} via {self.techno_name}'
        data_fuel_dict = self.get_sosdisc_inputs('data_fuel_dict')

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'CO2 emissions [kgCO2/kWh]',
                                             chart_name=chart_name, stacked_bar=True)

        CO2_per_use = np.zeros(
            len(carbon_emissions[GlossaryEnergy.Years]))
        if 'CO2_per_use' in data_fuel_dict and 'high_calorific_value' in data_fuel_dict:
            if data_fuel_dict['CO2_per_use_unit'] == 'kg/kg':
                CO2_per_use = np.ones(
                    len(carbon_emissions[GlossaryEnergy.Years])) * data_fuel_dict['CO2_per_use'] / data_fuel_dict[
                                  'high_calorific_value']
            elif data_fuel_dict['CO2_per_use_unit'] == 'kg/kWh':
                CO2_per_use = np.ones(
                    len(carbon_emissions[GlossaryEnergy.Years])) * data_fuel_dict['CO2_per_use']
            serie = InstanciatedSeries(
                carbon_emissions[GlossaryEnergy.Years].values.tolist(),
                CO2_per_use.tolist(), f'if {self.energy_name} used', 'bar')

            new_chart.series.append(serie)

        for emission_type in carbon_emissions:
            if emission_type == self.techno_name:
                total_carbon_emissions = CO2_per_use + \
                                         carbon_emissions[self.techno_name].values
                serie = InstanciatedSeries(
                    carbon_emissions[GlossaryEnergy.Years].values.tolist(),
                    carbon_emissions[self.techno_name].values.tolist(), 'Total w/o use', 'lines')
                new_chart.series.append(serie)

                serie = InstanciatedSeries(
                    carbon_emissions[GlossaryEnergy.Years].values.tolist(),
                    total_carbon_emissions.tolist(), 'Total if used', 'lines')
                new_chart.series.append(serie)
            elif emission_type != GlossaryEnergy.Years and not (carbon_emissions[emission_type] == 0).all():
                serie = InstanciatedSeries(
                    carbon_emissions[GlossaryEnergy.Years].values.tolist(),
                    carbon_emissions[emission_type].values.tolist(), emission_type, 'bar')
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
        if 'CO2_per_use' in data_fuel_dict:
            if data_fuel_dict['CO2_per_use_unit'] == 'kg/kg':
                CO2_per_use = np.ones(
                    len(carbon_emissions[GlossaryEnergy.Years])) * data_fuel_dict['CO2_per_use']
            elif data_fuel_dict['CO2_per_use_unit'] == 'kg/kWh':
                CO2_per_use = np.ones(
                    len(carbon_emissions[GlossaryEnergy.Years])) * data_fuel_dict['CO2_per_use'] * data_fuel_dict[
                                  'high_calorific_value']
            serie = InstanciatedSeries(
                carbon_emissions[GlossaryEnergy.Years].values.tolist(),
                CO2_per_use.tolist(), f'if {self.energy_name} used', 'bar')

            new_chart.series.append(serie)

        for emission_type in carbon_emissions:
            if emission_type == self.techno_name:
                total_carbon_emission_wo_use = carbon_emissions[self.techno_name].values * \
                                               data_fuel_dict['high_calorific_value']
                total_carbon_emissions = CO2_per_use + total_carbon_emission_wo_use

                serie = InstanciatedSeries(
                    carbon_emissions[GlossaryEnergy.Years].values.tolist(),
                    total_carbon_emission_wo_use.tolist(), 'Total w/o use', 'lines')
                new_chart.series.append(serie)

                serie = InstanciatedSeries(
                    carbon_emissions[GlossaryEnergy.Years].values.tolist(),
                    total_carbon_emissions.tolist(), 'Total if used ', 'lines')
                new_chart.series.append(serie)
            elif emission_type != GlossaryEnergy.Years and not (carbon_emissions[emission_type] == 0).all():
                emissions_kg_kg = carbon_emissions[emission_type].values * \
                                  data_fuel_dict['high_calorific_value']
                serie = InstanciatedSeries(
                    carbon_emissions[GlossaryEnergy.Years].values.tolist(),
                    emissions_kg_kg.tolist(), emission_type, 'bar')
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
                land_use_required[GlossaryEnergy.Years].values.tolist(),
                land_use_required[f'{self.techno_name} (Gha)'].values.tolist(), 'Gha', 'lines')
            new_chart.series.append(serie)

        return new_chart

    def get_chart_non_use_capital(self):
        non_use_capital = self.get_sosdisc_outputs(
            'non_use_capital')
        techno_capital = self.get_sosdisc_outputs(GlossaryEnergy.TechnoCapitalValue)
        chart_name = f'Capital of {self.techno_name}'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Capital [G$]',
                                             chart_name=chart_name)

        serie = InstanciatedSeries(
            techno_capital[GlossaryEnergy.Years].values.tolist(),
            techno_capital[GlossaryEnergy.Capital].values.tolist(), 'Total capital', 'lines')

        new_chart.series.append(serie)

        serie = InstanciatedSeries(
            non_use_capital[GlossaryEnergy.Years].values.tolist(),
            non_use_capital[self.techno_name].values.tolist(),
            'Unused capital (utilisation ratio + limitation from energy and resources)', 'bar')

        new_chart.series.append(serie)

        return new_chart

    def get_chart_power_production(self, technos_info_dict):
        power_production = self.get_sosdisc_outputs(
            GlossaryEnergy.InstalledPower)
        chart_name = f'Power installed of {self.techno_name} factories'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Power [MW]',
                                             chart_name=chart_name)

        if not 'full_load_hours' in technos_info_dict:
            note = {
                f'The full_load_hours data is not set for {self.techno_name}': 'default = 8760.0 hours, full year hours  '}
            new_chart.annotation_upper_left = note

        serie = InstanciatedSeries(
            power_production[GlossaryEnergy.Years].values.tolist(),
            power_production['total_installed_power'].values.tolist(), 'Total', 'lines')

        new_chart.series.append(serie)

        serie = InstanciatedSeries(
            power_production[GlossaryEnergy.Years].values.tolist(),
            power_production['new_power_production'].values.tolist(), f'Newly implemented', 'lines')

        new_chart.series.append(serie)

        serie = InstanciatedSeries(
            power_production[GlossaryEnergy.Years].values.tolist(),
            power_production['removed_power_production'].values.tolist(), f'Newly dismantled', 'lines')

        new_chart.series.append(serie)

        return new_chart