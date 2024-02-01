'''
Copyright 2022 Airbus SAS
Modifications on 2023/04/19-2023/11/16 Copyright 2023 Capgemini

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

from copy import deepcopy

import numpy as np
import pandas as pd
from plotly import graph_objects as go

from climateeconomics.core.core_witness.climateeco_discipline import ClimateEcoDiscipline
from energy_models.core.heat_mix.heat_mix import HeatMix
from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import GaseousHydrogen
from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from energy_models.core.stream_type.energy_models.heat import lowtemperatureheat
from energy_models.core.stream_type.energy_models.heat import mediumtemperatureheat
from energy_models.core.stream_type.energy_models.liquid_fuel import LiquidFuel
from energy_models.core.stream_type.energy_models.liquid_hydrogen import LiquidHydrogen
from energy_models.core.stream_type.energy_models.solid_fuel import SolidFuel
from energy_models.core.stream_type.energy_models.syngas import Syngas
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
from energy_models.glossaryenergy import GlossaryEnergy
from sostrades_core.execution_engine.sos_wrapp import SoSWrapp
from sostrades_core.tools.base_functions.exp_min import compute_dfunc_with_exp_min, \
    compute_func_with_exp_min
from sostrades_core.tools.cst_manager.func_manager_common import get_dsmooth_dvariable
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart
from sostrades_core.tools.post_processing.pie_charts.instanciated_pie_chart import InstanciatedPieChart
from sostrades_core.tools.post_processing.plotly_native_charts.instantiated_plotly_native_chart import \
    InstantiatedPlotlyNativeChart
from sostrades_core.tools.post_processing.tables.instanciated_table import InstanciatedTable


class Heat_Mix_Discipline(SoSWrapp):
    # ontology information
    _ontology_data = {
        'label': 'Heat Mix Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-battery-full fa-fw',
        'version': '',
    }

    DESC_IN = {GlossaryEnergy.energy_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                               'possible_values': HeatMix.energy_list,
                               'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy_study',
                               'editable': False, 'structuring': True},
               GlossaryEnergy.YearStart: ClimateEcoDiscipline.YEAR_START_DESC_IN,
               GlossaryEnergy.YearEnd: ClimateEcoDiscipline.YEAR_END_DESC_IN,
               'alpha': {'type': 'float', 'range': [0., 1.], 'default': 0.5, 'unit': '-',
                         'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy_study'},
               # 'primary_energy_percentage': {'type': 'float', 'range': [0., 1.], 'unit': '-', 'default': 0.8,
               #                               'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_ref'},
               'normalization_value_demand_constraints': {'type': 'float', 'default': 1000.0, 'unit': 'Twh',
                                                          'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                          'namespace': 'ns_ref'},
               GlossaryEnergy.CO2Taxes['var_name']: GlossaryEnergy.CO2Taxes,
               'minimum_energy_production': {'type': 'float', 'default': 1e4,
                                             'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_public',
                                             'unit': 'TWh'},
               'total_prod_minus_min_prod_constraint_ref': {'type': 'float', 'default': 1e4, 'unit': 'Twh',
                                                            'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                            'namespace': 'ns_ref'},
               'exp_min': {'type': 'bool', 'default': True, 'user_level': 2},
               'production_threshold': {'type': 'float', 'default': 1e-3, 'unit': 'Twh'},
               'scaling_factor_energy_production': {'type': 'float', 'default': 1e3, 'unit': '-', 'user_level': 2,
                                                    'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                    'namespace': 'ns_public'},
               'scaling_factor_energy_consumption': {'type': 'float', 'default': 1e3, 'unit': '-', 'user_level': 2,
                                                     'visibility': SoSWrapp.SHARED_VISIBILITY,
                                                     'namespace': 'ns_public'},
               'ratio_ref': {'type': 'float', 'default': 500., 'unit': '-', 'user_level': 2,
                             'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_ref'},
               }

    DESC_OUT = {
        # GlossaryEnergy.EnergyPricesValue: {'type': 'dataframe', 'unit': '$/MWh'},
        # GlossaryEnergy.EnergyCO2EmissionsValue: {'type': 'dataframe', 'unit': 'kg/kWh'},
        'energy_CO2_emissions_after_use': {'type': 'dataframe', 'unit': 'kg/kWh'},
        'co2_emissions_by_energy': {'type': 'dataframe', 'unit': 'Mt'},
        GlossaryEnergy.EnergyProductionValue: {'type': 'dataframe', 'unit': 'PWh'},
        GlossaryEnergy.EnergyProductionDetailedValue: {'type': 'dataframe', 'unit': 'TWh'},
        'energy_production_brut': {'type': 'dataframe', 'unit': 'TWh'},
        'energy_production_brut_detailed': {'type': 'dataframe', 'unit': 'TWh'},
        'energy_mix': {'type': 'dataframe', 'unit': '%'},
        'energy_prices_after_tax': {'type': 'dataframe', 'unit': '$/MWh'},
        'energy_production_objective': {'type': 'array', 'unit': '-', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                                        'namespace': 'ns_functions'},
        'primary_energies_production': {'type': 'dataframe', 'unit': 'TWh',
                                        'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_functions'},
        'land_demand_df': {'type': 'dataframe', 'unit': 'Gha'},
        GlossaryEnergy.EnergyMeanPriceValue: GlossaryEnergy.EnergyMeanPrice,
        'production_energy_net_positive': {'type': 'dataframe', 'unit': 'TWh'},
        HeatMix.TOTAL_PROD_MINUS_MIN_PROD_CONSTRAINT_DF: {
            'type': 'dataframe', 'unit': 'TWh',
            'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_functions'},
        HeatMix.CONSTRAINT_PROD_H2_LIQUID: {
            'type': 'dataframe', 'unit': 'TWh',
            'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_functions'
        },
        GlossaryEnergy.AllStreamsDemandRatioValue: {'type': 'dataframe', 'unit': '-', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                                     'namespace': 'ns_energy',
                                     'dataframe_descriptor': {GlossaryEnergy.Years: ('int', [1900, 2100], False),
                                                              GlossaryEnergy.CO2Tax: ('float', None, True)}
                                     },
        'ratio_objective': {'type': 'array', 'unit': '-', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                            'namespace': 'ns_functions'},
        'resources_demand': {'type': 'dataframe', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                             'namespace': 'ns_resource', 'unit': 'Mt'},
        'resources_demand_woratio': {'type': 'dataframe', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                                     'namespace': 'ns_resource', 'unit': 'Mt'},
        'co2_emissions_needed_by_energy_mix': {'type': 'dataframe', 'unit': 'Gt',
                                               'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy'},
        'carbon_capture_from_energy_mix': {'type': 'dataframe', 'unit': 'Gt',
                                           'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy'},
        GlossaryEnergy.EnergyCapitalDfValue: GlossaryEnergy.EnergyCapitalDf
    }

    energy_name = HeatMix.name
    energy_class_dict = HeatMix.energy_class_dict
    stream_class_dict = HeatMix.stream_class_dict
    LowTemperatureHeat_name = lowtemperatureheat.name
    MediumTemperatureHeat_name = mediumtemperatureheat.name
    HighTemperatureHeat_name = hightemperatureheat.name
    energy_constraint_list = HeatMix.energy_constraint_list
    movable_fuel_list = HeatMix.movable_fuel_list

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.energy_model = HeatMix(self.energy_name)
        self.energy_model.configure_parameters(inputs_dict)

    def setup_sos_disciplines(self):

        dynamic_inputs = {}
        dynamic_outputs = {}
        inputs_dict = self.get_sosdisc_inputs()
        if GlossaryEnergy.energy_list in self.get_data_in():
            energy_list = inputs_dict[GlossaryEnergy.energy_list]
            self.update_default_energy_list()
            if energy_list is not None:
                for energy in energy_list:
                    ns_energy = self.get_ns_energy(energy)
                    dynamic_inputs[f'{ns_energy}.{GlossaryEnergy.EnergyConsumptionValue}'] = {
                        'type': 'dataframe', 'unit': 'PWh',
                        "dynamic_dataframe_columns": True}
                    dynamic_inputs[f'{ns_energy}.{GlossaryEnergy.EnergyConsumptionWithoutRatioValue}'] = {
                        'type': 'dataframe', 'unit': 'PWh',"dynamic_dataframe_columns": True}
                    dynamic_inputs[f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}'] = {
                        'type': 'dataframe', 'unit': 'PWh',"dynamic_dataframe_columns": True}
                    dynamic_inputs[f'{ns_energy}.{GlossaryEnergy.EnergyPricesValue}'] = {
                        'type': 'dataframe', 'unit': '$/MWh',"dynamic_dataframe_columns": True}
                    dynamic_inputs[f'{ns_energy}.{GlossaryEnergy.LandUseRequiredValue}'] = {
                        'type': 'dataframe', 'unit': 'Gha',"dynamic_dataframe_columns": True}

                    dynamic_inputs[f'{ns_energy}.{GlossaryEnergy.EnergyTypeCapitalDfValue}'] = \
                        GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.EnergyTypeCapitalDf)
                    if energy in self.energy_class_dict:
                        # Biomass energy is computed by the agriculture model
                        dynamic_inputs[f'{ns_energy}.{GlossaryEnergy.CO2EmissionsValue}'] = {
                            'type': 'dataframe', 'unit': 'kg/kWh', "dynamic_dataframe_columns": True}
                        dynamic_inputs[f'{ns_energy}.CO2_per_use'] = {
                            'type': 'dataframe', 'unit': 'kg/kWh',
                            'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                     GlossaryEnergy.CO2Tax: ('float', None, True),
                                                     'CO2_per_use': ('float', None, True),
                                                     },
                        }

        self.update_default_with_years(inputs_dict)

        self.add_inputs(dynamic_inputs)
        self.add_outputs(dynamic_outputs)

    def update_default_with_years(self, inputs_dict):
        '''
        Update default variables knowing the year start and the year end
        '''
        if GlossaryEnergy.YearStart in inputs_dict:
            years = np.arange(inputs_dict[GlossaryEnergy.YearStart], inputs_dict[GlossaryEnergy.YearEnd] + 1)
            lh_perc_default = np.concatenate(
                (np.ones(5) * 1e-4, np.ones(len(years) - 5) / 4), axis=None)
            self.set_dynamic_default_values(
                {'liquid_hydrogen_percentage': lh_perc_default})

    def update_default_energy_list(self):
        '''
        Update the default value of technologies list with techno discipline below the energy node and in possible values
        '''

        found_energies = self.found_energy_under_HeatMix()
        self.set_dynamic_default_values({GlossaryEnergy.energy_list: found_energies})

    def found_energy_under_HeatMix(self):
        '''
        Set the default value of the energy list and the ccs_list with discipline under the energy_mix which are in possible values
        '''
        my_name = self.get_disc_full_name()
        possible_energy = HeatMix.energy_list
        found_energy_list = self.dm.get_discipline_names_with_starting_name(
            my_name)
        short_energy_list = [name.split(
            f'{my_name}.')[-1] for name in found_energy_list if f'{my_name}.' in name]

        possible_short_energy_list = [
            techno for techno in short_energy_list if techno in possible_energy]

        return possible_short_energy_list

    def run(self):
        # -- get inputs
        inputs_dict_orig = self.get_sosdisc_inputs()
        # -- configure class with inputs
        inputs_dict = {}
        inputs_dict.update(inputs_dict_orig)

        self.energy_model.compute(inputs_dict)

        # -- Compute objectives with alpha trades
        alpha = inputs_dict['alpha']
        delta_years = inputs_dict[GlossaryEnergy.YearEnd] - inputs_dict[GlossaryEnergy.YearStart] + 1

        energy_production_objective = np.asarray(
            [(1. - alpha) * self.energy_model.production[GlossaryEnergy.TotalProductionValue][0] * delta_years
             / self.energy_model.production[GlossaryEnergy.TotalProductionValue].sum(), ])

        # -- store outputs
        if HeatMix.PRODUCTION in self.energy_model.energy_prices:
            self.energy_model.energy_prices.drop(
                columns=[HeatMix.PRODUCTION], inplace=True)
        # energy_production stored in PetaWh for coupling variables scaling
        scaled_energy_production = pd.DataFrame(
            {GlossaryEnergy.Years: self.energy_model.production[GlossaryEnergy.Years].values,
             GlossaryEnergy.TotalProductionValue: self.energy_model.production[GlossaryEnergy.TotalProductionValue].values /
                                                inputs_dict[
                                                    'scaling_factor_energy_production']})

        # print('')
        # print(self.energy_model.total_carbon_emissions.to_string())
        outputs_dict = {
                        # GlossaryEnergy.EnergyPricesValue: self.energy_model.energy_prices,
                        'co2_emissions_by_energy': self.energy_model.emissions_by_energy,
                        # GlossaryEnergy.EnergyCO2EmissionsValue: self.energy_model.total_carbon_emissions,
                        'energy_CO2_emissions_after_use': self.energy_model.carbon_emissions_after_use,
                        GlossaryEnergy.EnergyProductionValue: scaled_energy_production,
                        GlossaryEnergy.EnergyProductionDetailedValue: self.energy_model.production,
                        'energy_production_brut': self.energy_model.production_raw[
                            [GlossaryEnergy.Years, GlossaryEnergy.TotalProductionValue]],
                        'energy_production_brut_detailed': self.energy_model.production_raw,
                        'energy_mix': self.energy_model.mix_weights,
                        'energy_prices_after_tax': self.energy_model.price_by_energy,
                        'energy_production_objective': energy_production_objective,
                        'land_demand_df': self.energy_model.land_use_required,
                        GlossaryEnergy.EnergyMeanPriceValue: self.energy_model.energy_mean_price,
                        'production_energy_net_positive': self.energy_model.net_positive_consumable_energy_production,
                        self.energy_model.TOTAL_PROD_MINUS_MIN_PROD_CONSTRAINT_DF: self.energy_model.total_prod_minus_min_prod_constraint_df,
                        GlossaryEnergy.AllStreamsDemandRatioValue: self.energy_model.all_streams_demand_ratio,
                        # 'ratio_objective': self.energy_model.ratio_objective,
                        'resources_demand': self.energy_model.resources_demand,
                        'resources_demand_woratio': self.energy_model.resources_demand_woratio,
                        GlossaryEnergy.EnergyCapitalDfValue: self.energy_model.energy_capital
                        }

        # primary_energy_percentage = inputs_dict['primary_energy_percentage']

        # outputs_dict['primary_energies_production'] = pd.DataFrame()

        # -- store outputs

        self.store_sos_outputs_values(outputs_dict)

    def compute_sos_jacobian(self):

        inputs_dict_orig = self.get_sosdisc_inputs()
        # -- biomass dry values are coming from agriculture mix discipline, but needs to be used in model with biomass dry name
        inputs_dict = {}
        inputs_dict.update(inputs_dict_orig)
        energy_list = inputs_dict[GlossaryEnergy.energy_list] #+ inputs_dict[GlossaryEnergy.ccs_list]
        outputs_dict = self.get_sosdisc_outputs()
        stream_class_dict = HeatMix.stream_class_dict
        years = np.arange(inputs_dict[GlossaryEnergy.YearStart],
                          inputs_dict[GlossaryEnergy.YearEnd] + 1)
        identity = np.eye(len(years))
        production_detailed_df = outputs_dict[GlossaryEnergy.EnergyProductionDetailedValue]
        minimum_energy_production = inputs_dict['minimum_energy_production']
        production_threshold = inputs_dict['production_threshold']
        total_prod_minus_min_prod_constraint_ref = inputs_dict[
            'total_prod_minus_min_prod_constraint_ref']
        production_energy_net_pos = outputs_dict['production_energy_net_positive']
        energies = [j for j in energy_list if j not in [
            'carbon_storage', 'carbon_capture']]
        mix_weight = outputs_dict['energy_mix']
        scaling_factor_energy_production = inputs_dict['scaling_factor_energy_production']
        scaling_factor_energy_consumption = inputs_dict['scaling_factor_energy_consumption']
        energy_price_after_tax = outputs_dict['energy_prices_after_tax']
        sub_production_dict, sub_consumption_dict = {}, {}
        sub_consumption_woratio_dict = self.energy_model.sub_consumption_woratio_dict
        for energy in energy_list:
            sub_production_dict[energy] = inputs_dict[f'{energy}.{GlossaryEnergy.EnergyProductionValue}'] * \
                                          scaling_factor_energy_production
            sub_consumption_dict[energy] = inputs_dict[f'{energy}.{GlossaryEnergy.EnergyConsumptionValue}'] * \
                                           scaling_factor_energy_consumption

        # -------------------------------------------#
        # ---- Production / Consumption gradients----#
        # -------------------------------------------#
        for energy in inputs_dict[GlossaryEnergy.energy_list]: #+ inputs_dict[GlossaryEnergy.ccs_list]:
            ns_energy = self.get_ns_energy(energy)
            self.set_partial_derivative_for_other_types(
                (GlossaryEnergy.EnergyCapitalDfValue, GlossaryEnergy.Capital),
                (f'{ns_energy}.{GlossaryEnergy.EnergyTypeCapitalDfValue}', GlossaryEnergy.Capital),
                identity / 1e3
            )

        for energy in energy_list:
            ns_energy = self.get_ns_energy(energy)

            if energy in energies:

                # ---- Loop on energy again to differentiate production and consumption ----#
                for energy_input in energy_list:
                    ns_energy_input = self.get_ns_energy(energy_input)
                    list_columns_energy_consumption = list(
                        inputs_dict[f'{energy_input}.{GlossaryEnergy.EnergyConsumptionValue}'].columns)
                    if f'{energy} ({stream_class_dict[energy].unit})' in list_columns_energy_consumption:
                        # ---- Consumption gradients----#
                        dtotal_prod_denergy_cons = - \
                            self.compute_dtotal_production_denergy_production(
                                production_detailed_df, minimum_energy_production, 0.0)
                        dprod_objective_dcons = self.compute_denergy_production_objective_dprod(
                            dtotal_prod_denergy_cons, inputs_dict['alpha'],
                            outputs_dict[GlossaryEnergy.EnergyProductionValue], years)
                        self.set_partial_derivative_for_other_types(
                            (GlossaryEnergy.EnergyProductionValue, GlossaryEnergy.TotalProductionValue), (
                                f'{ns_energy_input}.{GlossaryEnergy.EnergyConsumptionValue}',
                                f'{energy} ({stream_class_dict[energy].unit})'),
                            scaling_factor_energy_consumption * dtotal_prod_denergy_cons / scaling_factor_energy_production)
                        self.set_partial_derivative_for_other_types(
                            (GlossaryEnergy.EnergyProductionDetailedValue, GlossaryEnergy.TotalProductionValue),
                            (f'{ns_energy_input}.{GlossaryEnergy.EnergyConsumptionValue}',
                             f'{energy} ({stream_class_dict[energy].unit})'),
                            scaling_factor_energy_consumption * dtotal_prod_denergy_cons / scaling_factor_energy_production * scaling_factor_energy_production)
                        self.set_partial_derivative_for_other_types(
                            (GlossaryEnergy.EnergyProductionDetailedValue,
                             'Total production (uncut)'),
                            (f'{ns_energy_input}.{GlossaryEnergy.EnergyConsumptionValue}',
                             f'{energy} ({stream_class_dict[energy].unit})'),
                            -scaling_factor_energy_consumption * np.identity(
                                len(years)) / scaling_factor_energy_production * scaling_factor_energy_production)
                        self.set_partial_derivative_for_other_types(
                            (GlossaryEnergy.EnergyProductionDetailedValue,
                             f'production {energy} ({stream_class_dict[energy].unit})'),
                            (f'{ns_energy_input}.{GlossaryEnergy.EnergyConsumptionValue}',
                             f'{energy} ({stream_class_dict[energy].unit})'),
                            -scaling_factor_energy_consumption * np.identity(
                                len(years)) / scaling_factor_energy_production * scaling_factor_energy_production)

                        self.set_partial_derivative_for_other_types(
                            ('energy_production_objective',),
                            (f'{ns_energy_input}.{GlossaryEnergy.EnergyConsumptionValue}',
                             f'{energy} ({stream_class_dict[energy].unit})'),
                            scaling_factor_energy_consumption * dprod_objective_dcons / scaling_factor_energy_production)

            else:
                # CCUS
                self.set_partial_derivative_for_other_types(
                    (GlossaryEnergy.EnergyProductionDetailedValue,
                     f'production {energy} ({stream_class_dict[energy].unit})'),
                    (f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', energy),
                    np.identity(len(years)) * scaling_factor_energy_production)
                # ---- Loop on energy again to differentiate production and consumption ----#
                for energy_input in energy_list:
                    ns_energy_input = self.get_ns_energy(energy_input)
                    list_columns_energy_consumption = list(
                        inputs_dict[f'{energy_input}.{GlossaryEnergy.EnergyConsumptionValue}'].columns)
                    if f'{energy} ({stream_class_dict[energy].unit})' in list_columns_energy_consumption:
                        self.set_partial_derivative_for_other_types(
                            (GlossaryEnergy.EnergyProductionDetailedValue,
                             f'production {energy} ({stream_class_dict[energy].unit})'),
                            (f'{ns_energy_input}.{GlossaryEnergy.EnergyConsumptionValue}',
                             f'{energy} ({stream_class_dict[energy].unit})'),
                            -scaling_factor_energy_consumption * np.identity(
                                len(years)) / scaling_factor_energy_production * scaling_factor_energy_production)
        # -------------------------#
        # ---- Prices gradients----#
        # -------------------------#
        for energy in energy_list:
            ns_energy = self.get_ns_energy(energy)
            if energy in energies:
                # self.set_partial_derivative_for_other_types(
                #     ('energy_prices_after_tax',
                #      energy), (f'{ns_energy}.{GlossaryEnergy.EnergyPricesValue}', energy),
                #     np.identity(len(years)))
                self.set_partial_derivative_for_other_types(
                    ('energy_prices_after_tax', energy), (GlossaryEnergy.CO2TaxesValue, GlossaryEnergy.CO2Tax),
                    inputs_dict[f'{energy}.CO2_per_use']['CO2_per_use'].values *
                    np.identity(len(years)))
                self.set_partial_derivative_for_other_types(
                    ('energy_prices_after_tax',
                     energy), (f'{ns_energy}.CO2_per_use', 'CO2_per_use'),
                    inputs_dict[GlossaryEnergy.CO2TaxesValue][GlossaryEnergy.CO2Tax].values *
                    np.identity(len(years)))

        # -------------------------------#
        # ---Resource Demand gradients---#
        # -------------------------------#

        resource_list = HeatMix.RESOURCE_LIST
        for energy in energy_list:
            ns_energy = self.get_ns_energy(energy)
            for resource in inputs_dict[f'{energy}.{GlossaryEnergy.EnergyConsumptionValue}']:
                resource_wo_unit = resource.replace(
                    f" ({ResourceGlossary.UNITS['consumption']})", '')
                if resource_wo_unit in resource_list:
                    self.set_partial_derivative_for_other_types(('resources_demand', resource_wo_unit), (
                        f'{ns_energy}.{GlossaryEnergy.EnergyConsumptionValue}', resource), scaling_factor_energy_consumption * np.identity(
                        len(years)))
                    self.set_partial_derivative_for_other_types(('resources_demand_woratio', resource_wo_unit), (
                        f'{ns_energy}.{GlossaryEnergy.EnergyConsumptionWithoutRatioValue}', resource),
                                                                scaling_factor_energy_consumption * np.identity(
                                                                    len(years)))
        # -----------------------------#
        # ---- Mean Price gradients----#
        # -----------------------------#
        element_dict = dict(zip(energies, energies))
        self.grad_energy_mix_vs_prod_dict = self.energy_model.compute_grad_element_mix_vs_prod(
            deepcopy(production_energy_net_pos), element_dict, exp_min=inputs_dict['exp_min'],
            min_prod=production_threshold)
        dmean_price_dco2_tax = np.zeros((len(years), len(years)))
        for energy in energy_list:
            ns_energy = self.get_ns_energy(energy)
            if energy in energies:
                mix_weight_energy = mix_weight[energy].values
                dmean_price_dco2_tax += inputs_dict[f'{energy}.CO2_per_use']['CO2_per_use'].values * \
                                        mix_weight_energy
                self.set_partial_derivative_for_other_types(
                    (GlossaryEnergy.EnergyMeanPriceValue,
                     GlossaryEnergy.EnergyPriceValue), (f'{ns_energy}.CO2_per_use', 'CO2_per_use'),
                    inputs_dict[GlossaryEnergy.CO2TaxesValue][GlossaryEnergy.CO2Tax].values *
                    mix_weight_energy * np.identity(len(years)))
                dmean_price_dprod = self.compute_dmean_price_dprod(
                    energy, energies,
                    mix_weight, energy_price_after_tax,
                    production_energy_net_pos, production_detailed_df)

            for energy_input in energy_list:
                if energy_input in energies:
                    ns_energy_input = self.get_ns_energy(energy_input)
                    list_columns_energy_consumption = list(
                        inputs_dict[f'{energy_input}.{GlossaryEnergy.EnergyConsumptionValue}'].columns)
                    if f'{energy} ({stream_class_dict[energy].unit})' in list_columns_energy_consumption:
                        if energy in energies:
                            dmean_price_dcons = self.compute_dmean_price_dprod(energy, energies, mix_weight,
                                                                               energy_price_after_tax,
                                                                               production_energy_net_pos,
                                                                               production_detailed_df, cons=True)
                            self.set_partial_derivative_for_other_types(
                                (GlossaryEnergy.EnergyMeanPriceValue, GlossaryEnergy.EnergyPriceValue),
                                (f'{ns_energy_input}.{GlossaryEnergy.EnergyConsumptionValue}',
                                 f'{energy} ({stream_class_dict[energy].unit})'),
                                scaling_factor_energy_consumption * dmean_price_dcons)
        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.EnergyMeanPriceValue, GlossaryEnergy.EnergyPriceValue), (GlossaryEnergy.CO2TaxesValue, GlossaryEnergy.CO2Tax),
            dmean_price_dco2_tax * np.identity(len(years)))

        # --------------------------------#
        # -- New CO2 emissions gradients--#
        # --------------------------------#

        co2_emissions_needed_by_energy_mix = outputs_dict['co2_emissions_needed_by_energy_mix']
        carbon_capture_from_energy_mix = outputs_dict['carbon_capture_from_energy_mix']
        self.energy_model.configure_parameters_update(inputs_dict)
        dtot_co2_emissions = self.energy_model.compute_grad_CO2_emissions()

        for key, value in dtot_co2_emissions.items():
            co2_emission_column = key.split(' vs ')[0]
            energy_prod_info = key.split(' vs ')[1]
            energy = energy_prod_info.split('#')[0]
            last_part_key = energy_prod_info.split('#')[1]

        # -----------------------------------#
        # ---- Demand Violation gradients----#
        # -----------------------------------#
        for energy in energies:
            for energy_input in energy_list:
                ns_energy_input = self.get_ns_energy(energy_input)
                list_columnsenergyprod = list(
                    inputs_dict[f'{energy_input}.{GlossaryEnergy.EnergyProductionValue}'].columns)
                list_columns_energy_consumption = list(
                    inputs_dict[f'{energy_input}.{GlossaryEnergy.EnergyConsumptionValue}'].columns)
                list_index_prod = [j == energy for j in list_columnsenergyprod]
                list_index_conso = [
                    j == f'{energy} ({self.stream_class_dict[energy].unit})' for j in list_columns_energy_consumption]

                if True in list_index_conso:
                    dtotal_prod_denergy_cons = - \
                        self.compute_dtotal_production_denergy_production(
                            production_detailed_df, minimum_energy_production, 0.0)

                    self.set_partial_derivative_for_other_types((HeatMix.TOTAL_PROD_MINUS_MIN_PROD_CONSTRAINT_DF,
                                                                 HeatMix.TOTAL_PROD_MINUS_MIN_PROD_CONSTRAINT),
                                                                (f'{ns_energy_input}.{GlossaryEnergy.EnergyConsumptionValue}',
                                                                 list_columns_energy_consumption[
                                                                     list_index_conso.index(True)]),
                                                                -scaling_factor_energy_consumption * np.identity(
                                                                    len(years)) / total_prod_minus_min_prod_constraint_ref)

        # --------------------------------------#
        # ---- Stream Demand ratio gradients ---#
        # --------------------------------------#
        all_streams_demand_ratio = outputs_dict[GlossaryEnergy.AllStreamsDemandRatioValue]
        energy_production_brut_detailed = outputs_dict['energy_production_brut_detailed']
        ratio_ref = inputs_dict['ratio_ref']
        # Loop on streams
        dobjective_dratio = self.compute_dratio_objective(
            all_streams_demand_ratio, ratio_ref, energy_list)
        ienergy = 0
        for energy in energy_list:
            ns_energy = self.get_ns_energy(energy)
            ddemand_ratio_denergy_prod, ddemand_ratio_denergy_cons = self.compute_ddemand_ratio_denergy_production(
                energy, sub_production_dict, sub_consumption_woratio_dict, stream_class_dict,
                scaling_factor_energy_production, years, energy_production_brut_detailed)
            self.set_partial_derivative_for_other_types(
                (GlossaryEnergy.AllStreamsDemandRatioValue,
                 f'{energy}'), (f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', energy),
                ddemand_ratio_denergy_prod)
            dobjective_dratio_energy = np.array([dobjective_dratio[ienergy + iyear * len(
                energy_list)] for iyear in range(len(years))]).reshape((1, len(years)))
            dobjective_dprod = np.matmul(
                dobjective_dratio_energy, ddemand_ratio_denergy_prod)

            self.set_partial_derivative_for_other_types(
                ('ratio_objective',), (f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', energy), dobjective_dprod)
            # ---- Loop on energy again to differentiate production and consumption ----#
            for energy_input in energy_list:
                ns_energy_input = self.get_ns_energy(energy_input)
                list_columns_energy_consumption = list(
                    inputs_dict[f'{energy_input}.{GlossaryEnergy.EnergyConsumptionValue}'].columns)
                if f'{energy} ({stream_class_dict[energy].unit})' in list_columns_energy_consumption:
                    self.set_partial_derivative_for_other_types(
                        (GlossaryEnergy.AllStreamsDemandRatioValue, f'{energy}'), (
                            f'{ns_energy_input}.{GlossaryEnergy.EnergyConsumptionWithoutRatioValue}',
                            f'{energy} ({stream_class_dict[energy].unit})'), ddemand_ratio_denergy_cons)
                    dobjective_dcons = np.matmul(
                        dobjective_dratio_energy, ddemand_ratio_denergy_cons)
                    self.set_partial_derivative_for_other_types(
                        ('ratio_objective',), (
                            f'{ns_energy_input}.{GlossaryEnergy.EnergyConsumptionWithoutRatioValue}',
                            f'{energy} ({stream_class_dict[energy].unit})'), dobjective_dcons)
            ienergy += 1
        # --------------------------------------#
        # ---- Land use constraint gradients----#
        # --------------------------------------#

        for energy in energy_list:
            ns_energy = self.get_ns_energy(energy)
            for key in outputs_dict['land_demand_df']:
                if key in inputs_dict[f'{energy}.{GlossaryEnergy.LandUseRequiredValue}'] and key != GlossaryEnergy.Years:
                    self.set_partial_derivative_for_other_types(('land_demand_df', key),
                                                                (f'{ns_energy}.{GlossaryEnergy.LandUseRequiredValue}', key),
                                                                np.identity(len(years)))

    def set_gradient_for_co2_emissions(self, co2_variable, co2_emissions, co2_emission_column, energy, energy_prod_info,
                                       last_part_key, value, inputs_dict, years):

        if co2_emission_column in co2_emissions.columns:

            ns_energy = self.get_ns_energy(energy)

            '''
            Needed by energy mix gradient
            '''

            if last_part_key == 'prod':
                self.set_partial_derivative_for_other_types(
                    (co2_variable,
                     co2_emission_column), (f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', energy),
                    np.identity(len(years)) * inputs_dict['scaling_factor_energy_production'] * value / 1.0e3)
            elif last_part_key == 'cons':
                for energy_df in inputs_dict[GlossaryEnergy.energy_list]:
                    ns_energy_df = self.get_ns_energy(energy_df)
                    list_columnsenergycons = list(
                        inputs_dict[f'{energy_df}.{GlossaryEnergy.EnergyConsumptionValue}'].columns)
                    if f'{energy} (TWh)' in list_columnsenergycons:
                        self.set_partial_derivative_for_other_types(
                            (co2_variable, co2_emission_column),
                            (f'{ns_energy_df}.{GlossaryEnergy.EnergyConsumptionValue}',
                             f'{energy} (TWh)'),
                            np.identity(len(years)) * inputs_dict['scaling_factor_energy_consumption'] * value / 1.0e3)
            elif last_part_key == 'co2_per_use':
                self.set_partial_derivative_for_other_types(
                    (co2_variable,
                     co2_emission_column), (f'{ns_energy}.CO2_per_use', 'CO2_per_use'),
                    np.identity(len(years)) * value / 1.0e3)

            else:
                very_last_part_key = energy_prod_info.split('#')[2]
                if very_last_part_key == 'prod':
                    self.set_partial_derivative_for_other_types(
                        (co2_variable, co2_emission_column), (
                            f'{ns_energy}.{GlossaryEnergy.EnergyProductionValue}', last_part_key),
                        np.identity(len(years)) * inputs_dict['scaling_factor_energy_production'] * value / 1.0e3)
                elif very_last_part_key == 'cons':
                    self.set_partial_derivative_for_other_types(
                        (co2_variable, co2_emission_column), (
                            f'{ns_energy}.{GlossaryEnergy.EnergyConsumptionValue}', last_part_key),
                        np.identity(len(years)) * inputs_dict['scaling_factor_energy_production'] * value / 1.0e3)

    def compute_dratio_objective(self, stream_ratios, ratio_ref, energy_list):
        '''
        Compute the ratio_objective with the gradient of stream_ratios vs any input and the ratio ojective value
        obj = smooth_maximum(100.0 - ratio_arrays, 3)/ratio_ref

        dobj/dratio = -dsmooth_max(100.0 - ratio_arrays, 3)/ratio_ref
        '''

        dsmooth_dvar = get_dsmooth_dvariable(
            100.0 - stream_ratios[energy_list].values.flatten(), 3)
        dobjective_dratio = -np.asarray(dsmooth_dvar) / ratio_ref

        return dobjective_dratio

    def compute_denergy_production_objective_dprod(self, dtotal_production_denergy_production, alpha, prod, years):
        ''' energy_production_objective = np.asarray([(1. - alpha) * self.energy_model.production[GlossaryEnergy.TotalProductionValue][0] * delta_years
                                                  / self.energy_model.production[GlossaryEnergy.TotalProductionValue].sum(), ])
        '''

        tot_energy_production_sum = prod[GlossaryEnergy.TotalProductionValue].sum()
        dtot_energy_production_sum = dtotal_production_denergy_production.sum(
            axis=0)
        tot_energy_production_0 = prod[GlossaryEnergy.TotalProductionValue][0]
        dtot_energy_production_0 = dtotal_production_denergy_production[0]

        delta_years = (years[-1] - years[0] + 1)

        u = (1. - alpha) * \
            tot_energy_production_0 * delta_years
        v = tot_energy_production_sum
        u_prime = (1. - alpha) * dtot_energy_production_0 * \
                  delta_years
        v_prime = dtot_energy_production_sum
        dprod_objective_dprod = u_prime / v - u * v_prime / v ** 2

        return dprod_objective_dprod

    def compute_dproduction_net_denergy_production(self, energy, production_df, energy_price):
        '''
        energy_mean = sum(energy*1e6*prod*1e6)/total*1e6
        '''

        denergy_mean_prod = (
                                    energy_price[energy] * 1e6 * production_df[GlossaryEnergy.TotalProductionValue] -
                                    production_df[
                                        'energy_price_pond']) / (
                                    1e6 * (production_df[GlossaryEnergy.TotalProductionValue]) ** 2)

        # derivative of negative prod is 0
        index_l = production_df[production_df[f'production {energy} (TWh)']
                                == 0].index
        denergy_mean_prod.loc[index_l] = 0
        return denergy_mean_prod

    def compute_dtotal_production_denergy_production(self, production_detailed_df, min_energy, total_loss_percent):
        '''
        Compute gradient of production[GlossaryEnergy.TotalProductionValue] by {energy}.energy_prod[{energy}] taking into account
        the exponential decrease towards the limit applied on the calculation of the total net energy production
        Inputs: minimum_energy_production, production_df
        Outputs:dtotal_production_denergy_production
        '''
        years = production_detailed_df[GlossaryEnergy.Years]
        dtotal_production_denergy_production = np.ones(len(years))
        dtotal_production_denergy_production *= (
                1.0 - total_loss_percent)

        total_prod = production_detailed_df['Total production (uncut)'].values
        if total_prod.min() < min_energy:
            # To avoid underflow : exp(-200) is considered to be the
            # minimum value for the exp
            total_prod[total_prod < -200.0 * min_energy] = -200.0 * min_energy
            dtotal_production_denergy_production[total_prod < min_energy] = np.exp(
                total_prod[total_prod < min_energy] / min_energy) * np.exp(-1) / 10.0 * (1.0 - total_loss_percent)

        return np.identity(len(years)) * dtotal_production_denergy_production

    def compute_ddemand_ratio_denergy_production(self, energy, sub_production_dict, sub_consumption_dict,
                                                 stream_class_dict,
                                                 scaling_factor_production, years, energy_production_brut_detailed):
        '''! Compute the gradient of the demand ratio vs energy production function :
                 -the ratio is capped to one if energy_prod>energy_cons, hence the special condition.
                 -the function is designed to be used even if no energy_input is specified (to get ddemand_ratio_denergy_prod gradient alone)
        @param energy: string, name of the energy
        @param sub_production_dict: dictionary with the raw production for all the energies
        @param sub_consumption_dict: dictionary with the raw consumption for all energies
        @param stream_class_dict: dictionary with informations on the energies
        @param scaling_factor_production: float used to scale the energy production at input/output of the model
        @return ddemand_ratio_denergy_prod, ddemand_ratio_denergy_cons: numpy.arrays, shape=(len(years),len(years)) with the gradients
        '''

        # Calculate energy production and consumption
        energy_production = sub_production_dict[f'{energy}'][f'{energy}'].values
        if energy in HeatMix.raw_tonet_dict.keys():
            column_name = f'{HeatMix.PRODUCTION} {energy} ({self.stream_class_dict[energy].unit})'

            prod_raw_to_substract = energy_production_brut_detailed[column_name].values * \
                                    (1.0 - HeatMix.raw_tonet_dict[energy])
            energy_production -= prod_raw_to_substract
        energy_consumption = np.zeros(len(years))
        for consu in sub_consumption_dict.values():
            if f'{energy} ({self.stream_class_dict[energy].unit})' in consu.columns:
                energy_consumption = np.sum([energy_consumption, consu[
                    f'{energy} ({self.stream_class_dict[energy].unit})'].values], axis=0)

        # If prod < cons, set the identity element for the given year to the
        # corresponding value
        denergy_prod_limited = compute_dfunc_with_exp_min(
            energy_production, 1.0e-10)
        energy_prod_limited = compute_func_with_exp_min(
            energy_production, 1.0e-10)
        energy_cons_limited = compute_func_with_exp_min(
            energy_consumption, 1.0e-10)

        ddemand_ratio_denergy_prod = np.identity(len(years)) * 100.0
        # If prod < cons, set the identity element for the given year to
        # the corresponding value
        denergy_cons_limited = compute_dfunc_with_exp_min(
            energy_consumption, 1.0e-10)
        energy_cons_limited = compute_func_with_exp_min(
            energy_consumption, 1.0e-10)
        ddemand_ratio_denergy_cons = np.identity(len(years)) * 100.0 * \
                                     np.where((energy_prod_limited <= energy_cons_limited) * (
                                             energy_prod_limited / energy_cons_limited > 1E-15),
                                              -scaling_factor_production * energy_prod_limited * denergy_cons_limited /
                                              energy_cons_limited ** 2,
                                              0.0)

        if energy in HeatMix.raw_tonet_dict.keys():

            denergy_prod_limited = np.identity(len(years)) * 100.0 * \
                                   np.where((energy_prod_limited <= energy_cons_limited) * (
                                           energy_prod_limited / energy_cons_limited > 1E-15),
                                            denergy_prod_limited * scaling_factor_production * HeatMix.raw_tonet_dict[
                                                energy] /
                                            energy_cons_limited,
                                            0.0)
        else:
            denergy_prod_limited = np.identity(len(years)) * 100.0 * \
                                   np.where((energy_prod_limited <= energy_cons_limited) * (
                                           energy_prod_limited / energy_cons_limited > 1E-15),
                                            denergy_prod_limited * scaling_factor_production /
                                            energy_cons_limited,
                                            0.0)

        return denergy_prod_limited, ddemand_ratio_denergy_cons

    def compute_dmean_price_dprod(self, energy, energies, mix_weight, energy_price_after_tax,
                                  production_energy_net_pos_consumable, production_detailed_df, cons=False):
        """
        Function that returns the gradient of mean_price compared to energy_prod
        Params:
            - energy: name of the energy derived by
            - energies: list of all the energies
            - mix_weight: dataframe of the energies ratio
            - energy_price_after_tax: dataframe with values
            - production_energy_net_pos_consumable: dataframe with values
            - production_detailed_df: dataframe with values
        Output:
            - dmean_price_dprod
        """
        mix_weight_energy = mix_weight[energy].values
        # The mix_weight_techno is zero means that the techno is negligible else we do nothing
        # np.sign gives 0 if zero and 1 if value so it suits well
        # with our needs
        grad_energy_mix_vs_prod = self.grad_energy_mix_vs_prod_dict[energy] * \
                                  np.sign(mix_weight_energy)
        grad_price_vs_prod = energy_price_after_tax[energy].values * \
                             grad_energy_mix_vs_prod
        for energy_other in energies:
            if energy_other != energy:
                mix_weight_techno_other = mix_weight[energy_other].values
                grad_energy_mix_vs_prod = self.grad_energy_mix_vs_prod_dict[
                                              f'{energy} {energy_other}'] * np.sign(mix_weight_techno_other)
                grad_price_vs_prod += energy_price_after_tax[energy_other].values * \
                                      grad_energy_mix_vs_prod
        # If the prod is negative then there is no gradient
        # BUT if the prod is zero a gradient in 0+ exists
        # then we check the sign of prod but if zero the gradient
        # should not be zero
        gradient_sign = np.sign(production_energy_net_pos_consumable[energy].values) + (
                production_detailed_df[f'production {energy} (TWh)'].values == 0.0)
        years = production_detailed_df[GlossaryEnergy.Years].values

        dmean_price_dprod = grad_price_vs_prod * \
                            gradient_sign * np.identity(len(years))
        # if dmean_price_dcons
        if cons:
            dmean_price_dprod = -grad_price_vs_prod * \
                                np.sign(
                                    production_energy_net_pos_consumable[energy].values) * np.identity(len(years))
        return dmean_price_dprod

    def get_ns_energy(self, energy):
        '''
        Returns the namespace of the energy
        In case  of biomass , it is computed in agriculture model

        '''

        # if energy == BiomassDry.name:
        #     ns_energy = AgricultureMixDiscipline.name
        # else:
        ns_energy = energy

        return ns_energy

