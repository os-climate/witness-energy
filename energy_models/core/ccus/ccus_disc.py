'''
Copyright 2022 Airbus SAS

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

from energy_models.core.energy_mix.energy_mix import EnergyMix
from sos_trades_core.execution_engine.sos_discipline import SoSDiscipline
from sos_trades_core.tools.post_processing.charts.chart_filter import ChartFilter
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.core.stream_type.carbon_models.carbon_storage import CarbonStorage
from sos_trades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart
from sos_trades_core.tools.post_processing.pie_charts.instanciated_pie_chart import InstanciatedPieChart
from energy_models.core.stream_type.energy_models.syngas import Syngas
from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
from energy_models.core.stream_type.energy_models.liquid_fuel import LiquidFuel
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import GaseousHydrogen
from energy_models.core.stream_type.energy_models.liquid_hydrogen import LiquidHydrogen
from copy import deepcopy
from energy_models.core.stream_type.energy_models.solid_fuel import SolidFuel
from energy_models.core.stream_type.energy_models.electricity import Electricity
from sos_trades_core.tools.base_functions.exp_min import compute_dfunc_with_exp_min,\
    compute_func_with_exp_min
from plotly import graph_objects as go
from sos_trades_core.tools.post_processing.plotly_native_charts.instantiated_plotly_native_chart import InstantiatedPlotlyNativeChart
from sos_trades_core.tools.post_processing.tables.instanciated_table import InstanciatedTable
from sos_trades_core.tools.cst_manager.func_manager_common import get_dsmooth_dvariable
from energy_models.core.ccus.ccus import CCUS


class CCUS_Discipline(SoSDiscipline):

    DESC_IN = {
        'ccs_list': {'type': 'string_list', 'possible_values': [CarbonCapture.name, CarbonStorage.name],
                     'default': [CarbonCapture.name, CarbonStorage.name],
                     'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_study', 'editable': False, 'structuring': True},
        'year_start': {'type': 'int', 'default': 2020, 'unit': '[-]', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'year_end': {'type': 'int', 'default': 2050, 'unit': '[-]', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'alpha': {'type': 'float', 'range': [0., 1.], 'default': 0.5, 'unit': '-', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_study'},
        'CO2_taxes': {'type': 'dataframe', 'unit': '$/tCO2', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy_study',
                      'dataframe_descriptor': {'years': ('int',  [1900, 2100], False),
                                               'CO2_tax': ('float',  None, True)},
                      'dataframe_edition_locked': False},
        'delta_co2_price': {'type': 'float', 'default': 200., 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'scaling_factor_energy_production': {'type': 'float', 'default': 1e3, 'user_level': 2, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'scaling_factor_energy_consumption': {'type': 'float', 'default': 1e3, 'user_level': 2, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'minimum_energy_production': {'type': 'float', 'default': 1e4, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_public',
                                      'unit': 'TWh'},
        'total_prod_minus_min_prod_constraint_ref': {'type': 'float', 'default': 1e4, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ref'},
        'tol_constraint': {'type': 'float', 'default': 1e-3},
        'exp_min': {'type': 'bool', 'default': True, 'user_level': 2},
        'production_threshold': {'type': 'float', 'default': 1e-3},
        'co2_emissions': {'type': 'dataframe', 'unit': 'Mt', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy'},

        'carbonstorage_limit': {'type': 'float', 'default': 12e6, 'unit': 'MT', 'user_level': 2, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ref'},
        'carbonstorage_constraint_ref': {'type': 'float', 'default': 12e6, 'unit': 'MT', 'user_level': 2, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ref'},
        'ratio_ref': {'type': 'float', 'default': 100., 'unit': '', 'user_level': 2, 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ref'},
        'co2_emissions_needed_by_energy_mix': {'type': 'dataframe', 'unit': 'Mt', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy'},
        'co2_emissions_from_energy_mix': {'type': 'dataframe', 'unit': 'Mt', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy'},

    }

    DESC_OUT = {
        'co2_emissions_ccus': {'type': 'dataframe', 'unit': 'Mt'},
        'co2_emissions_ccus_Gt': {'type': 'dataframe', 'unit': 'Gt'},
        'land_demand_ccus_df': {'type': 'dataframe', 'unit': 'Gha', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ccs'},
        'ratio_available_carbon_capture': {'type': 'dataframe', 'unit': '-'},

        'CCS_price': {'type': 'dataframe', 'unit': '$/tCO2'},
        EnergyMix.CARBON_STORAGE_CONSTRAINT: {'type': 'array', 'unit': '',  'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_functions'},
        'ratio_objective_ccs': {'type': 'array', 'unit': '-', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_functions'},
        'all_ccs_demand_ratio': {'type': 'dataframe', 'unit': '-', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy'},

    }

    energy_name = EnergyMix.name
    stream_class_dict = EnergyMix.stream_class_dict
    SYNGAS_NAME = Syngas.name
    BIOMASS_DRY_NAME = BiomassDry.name
    LIQUID_FUEL_NAME = LiquidFuel.name
    HYDROGEN_NAME = GaseousHydrogen.name
    LIQUID_HYDROGEN_NAME = LiquidHydrogen.name
    SOLIDFUEL_NAME = SolidFuel.name
    ELECTRICITY_NAME = Electricity.name
    GASEOUS_HYDROGEN_NAME = GaseousHydrogen.name

    energy_constraint_list = EnergyMix.energy_constraint_list
    movable_fuel_list = EnergyMix.movable_fuel_list

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.ccus_model = CCUS(self.energy_name)
        self.ccus_model.configure_parameters(inputs_dict)

    def setup_sos_disciplines(self):

        dynamic_inputs = {}
        dynamic_outputs = {}

        if 'ccs_list' in self._data_in:
            ccs_list = self.get_sosdisc_inputs('ccs_list')
            if ccs_list is not None:
                for ccs_name in ccs_list:
                    dynamic_inputs[f'{ccs_name}.energy_consumption'] = {
                        'type': 'dataframe', 'unit': 'PWh', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ccs'}
                    dynamic_inputs[f'{ccs_name}.energy_consumption_woratio'] = {
                        'type': 'dataframe', 'unit': 'PWh', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ccs'}
                    dynamic_inputs[f'{ccs_name}.energy_production'] = {
                        'type': 'dataframe', 'unit': 'PWh', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ccs'}
                    dynamic_inputs[f'{ccs_name}.energy_prices'] = {
                        'type': 'dataframe', 'unit': '$/MWh', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ccs'}
                    dynamic_inputs[f'{ccs_name}.energy_demand'] = {'type': 'dataframe', 'unit': 'TWh',
                                                                   'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_demand'}

                    dynamic_inputs[f'{ccs_name}.land_use_required'] = {
                        'type': 'dataframe', 'unit': '(Gha)', 'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_ccs'}

                    dynamic_inputs[f'{ccs_name}.data_fuel_dict'] = {
                        'type': 'dict', 'visibility': SoSDiscipline.SHARED_VISIBILITY,
                        'namespace': f'ns_{ccs_name}', 'default': self.stream_class_dict[ccs_name].data_energy_dict}

        if 'year_start' in self._data_in and 'year_end' in self._data_in:
            year_start = self.get_sosdisc_inputs('year_start')
            year_end = self.get_sosdisc_inputs('year_end')

            if year_start is not None and year_end is not None:
                default_co2_for_food = pd.DataFrame({'years': np.arange(2020, 2050 + 1),
                                                     f'{CO2.name} for food (Mt)': 0.0})
                dynamic_inputs['co2_for_food'] = {'type': 'dataframe', 'unit': 'Mt', 'default': default_co2_for_food,
                                                  'visibility': SoSDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_energy'}

        self.add_inputs(dynamic_inputs)
        self.add_outputs(dynamic_outputs)

    def run(self):
        #-- get inputs
        inputs_dict = self.get_sosdisc_inputs()

        #-- configure class with inputs
        #
        self.ccus_model.configure_parameters_update(inputs_dict)

        self.ccus_model.compute_CO2_emissions()
        self.ccus_model.compute_CCS_price()
        self.ccus_model.compute_all_streams_demand_ratio()
        self.ccus_model.compute_ratio_objective()
        #-- Compute objectives with alpha trades
        alpha = inputs_dict['alpha']
        delta_years = inputs_dict['year_end'] - inputs_dict['year_start'] + 1

        self.ccus_model.compute_carbon_storage_constraint()
        outputs_dict = {
            'co2_emissions_ccus': self.ccus_model.total_co2_emissions,
            'co2_emissions_ccus_Gt': self.ccus_model.total_co2_emissions_Gt,
            'land_demand_ccus_df': self.ccus_model.land_use_required,
            'CCS_price': self.ccus_model.CCS_price,
            'ratio_available_carbon_capture': self.ccus_model.ratio_available_carbon_capture,
            EnergyMix.CARBON_STORAGE_CONSTRAINT: self.ccus_model.carbon_storage_constraint,
            'ratio_objective_ccs': self.ccus_model.ratio_objective,
            'all_ccs_demand_ratio': self.ccus_model.all_streams_demand_ratio
        }

        #-- store outputs

        self.store_sos_outputs_values(outputs_dict)

    def compute_sos_jacobian(self):

        inputs_dict = self.get_sosdisc_inputs()
        outputs_dict = self.get_sosdisc_outputs()
        stream_class_dict = EnergyMix.stream_class_dict
        years = np.arange(inputs_dict['year_start'],
                          inputs_dict['year_end'] + 1)
        energy_list = inputs_dict['ccs_list']
        production_threshold = inputs_dict['production_threshold']
        total_prod_minus_min_prod_constraint_ref = inputs_dict[
            'total_prod_minus_min_prod_constraint_ref']
        energies = [j for j in energy_list if j not in [
            'carbon_storage', 'carbon_capture']]
        scaling_factor_energy_production = inputs_dict['scaling_factor_energy_production']
        scaling_factor_energy_consumption = inputs_dict['scaling_factor_energy_consumption']

        sub_production_dict, sub_consumption_dict = {}, {}
        sub_consumption_woratio_dict = self.ccus_model.sub_consumption_woratio_dict
        for energy in energy_list:
            sub_production_dict[energy] = inputs_dict[f'{energy}.energy_production'] * \
                scaling_factor_energy_production
            sub_consumption_dict[energy] = inputs_dict[f'{energy}.energy_consumption'] * \
                scaling_factor_energy_consumption

        #-------------------------------#
        #---Resource Demand gradients---#
        #-------------------------------#
        resource_list = EnergyMix.RESOURCE_LIST
        for energy in energy_list:
            for resource in inputs_dict[f'{energy}.energy_consumption']:
                if resource in resource_list:
                    self.set_partial_derivative_for_other_types(('All_Demand', resource), (
                        f'{energy}.energy_consumption', resource), scaling_factor_energy_consumption * np.identity(len(years)))
        #-----------------------------#
        #---- Mean Price gradients----#
        #-----------------------------#
        element_dict = dict(zip(energies, energies))

        #--------------------------------#
        #-- New CO2 emissions gradients--#
        #--------------------------------#

        alpha = self.get_sosdisc_inputs('alpha')
        co2_emissions = self.get_sosdisc_outputs('co2_emissions_ccus')
        self.ccus_model.configure_parameters_update(inputs_dict)
        dtot_co2_emissions = self.ccus_model.compute_grad_CO2_emissions(
            co2_emissions, alpha)

        for key, value in dtot_co2_emissions.items():
            co2_emission_column = key.split(' vs ')[0]

            energy_prod_info = key.split(' vs ')[1]
            energy = energy_prod_info.split('#')[0]
            last_part_key = energy_prod_info.split('#')[1]
            if co2_emission_column in co2_emissions.columns and energy in energy_list:

                if last_part_key == 'prod':
                    self.set_partial_derivative_for_other_types(
                        ('co2_emissions_ccus', co2_emission_column), (f'{energy}.energy_production', energy), np.identity(len(years)) * scaling_factor_energy_production * value)
                elif last_part_key == 'cons':
                    for energy_df in energy_list:
                        list_columnsenergycons = list(
                            inputs_dict[f'{energy_df}.energy_consumption'].columns)
                        if f'{energy} (TWh)' in list_columnsenergycons:
                            self.set_partial_derivative_for_other_types(
                                ('co2_emissions_ccus', co2_emission_column), (f'{energy_df}.energy_consumption', f'{energy} (TWh)'), np.identity(len(years)) * scaling_factor_energy_consumption * value)
                elif last_part_key == 'co2_per_use':
                    self.set_partial_derivative_for_other_types(
                        ('co2_emissions_ccus', co2_emission_column), (f'{energy}.CO2_per_use', 'CO2_per_use'), np.identity(len(years)) * value)

                else:
                    very_last_part_key = energy_prod_info.split('#')[2]

                    if very_last_part_key == 'prod':
                        self.set_partial_derivative_for_other_types(
                            ('co2_emissions_ccus', co2_emission_column), (f'{energy}.energy_production', last_part_key), np.identity(len(years)) * scaling_factor_energy_production * value)
                    elif very_last_part_key == 'cons':
                        self.set_partial_derivative_for_other_types(
                            ('co2_emissions_ccus', co2_emission_column), (f'{energy}.energy_consumption', last_part_key), np.identity(len(years)) * scaling_factor_energy_production * value)

            '''
                CO2 emissions Gt
            '''
            if co2_emission_column == f'{CarbonStorage.name} Limited by capture (Mt)':
                if last_part_key == 'prod':
                    self.set_partial_derivative_for_other_types(
                        ('co2_emissions_ccus_Gt', co2_emission_column), (f'{energy}.energy_production', energy), np.identity(len(years)) * scaling_factor_energy_production * value / 1.0e3)
                elif last_part_key == 'cons':
                    for energy_df in energy_list:
                        list_columnsenergycons = list(
                            inputs_dict[f'{energy_df}.energy_consumption'].columns)
                        if f'{energy} (TWh)' in list_columnsenergycons:
                            self.set_partial_derivative_for_other_types(
                                ('co2_emissions_ccus_Gt', co2_emission_column), (f'{energy_df}.energy_consumption', f'{energy} (TWh)'), np.identity(len(years)) * scaling_factor_energy_consumption * value / 1.0e3)
                elif last_part_key == 'co2_per_use':
                    self.set_partial_derivative_for_other_types(
                        ('co2_emissions_ccus_Gt', co2_emission_column), (f'{energy}.CO2_per_use', 'CO2_per_use'), np.identity(len(years)) * value / 1.0e3)
                elif energy_prod_info.startswith('CO2 for food (Mt)'):
                    self.set_partial_derivative_for_other_types(
                        ('co2_emissions_ccus_Gt', co2_emission_column), ('co2_for_food', f'{CO2.name} for food (Mt)'), np.identity(len(years)) * value / 1.0e3)

                elif energy_prod_info.startswith(f'{CarbonCapture.name} from energy mix (Mt)'):
                    self.set_partial_derivative_for_other_types(
                        ('co2_emissions_ccus_Gt', co2_emission_column), ('co2_emissions_from_energy_mix', f'{CarbonCapture.name} from energy mix (Mt)'), np.identity(len(years)) * value / 1.0e3)

                elif energy_prod_info.startswith(f'{CarbonCapture.name} needed by energy mix (Mt)'):
                    self.set_partial_derivative_for_other_types(
                        ('co2_emissions_ccus_Gt', co2_emission_column), ('co2_emissions_needed_by_energy_mix', f'{CarbonCapture.name} needed by energy mix (Mt)'), np.identity(len(years)) * value / 1.0e3)

                else:
                    very_last_part_key = energy_prod_info.split('#')[2]
                    if very_last_part_key == 'prod':
                        self.set_partial_derivative_for_other_types(
                            ('co2_emissions_ccus_Gt', co2_emission_column), (f'{energy}.energy_production', last_part_key), np.identity(len(years)) * scaling_factor_energy_production * value / 1.0e3)
                    elif very_last_part_key == 'cons':
                        self.set_partial_derivative_for_other_types(
                            ('co2_emissions_ccus_Gt', co2_emission_column), (f'{energy}.energy_consumption', last_part_key), np.identity(len(years)) * scaling_factor_energy_production * value / 1.0e3)

                '''
                    Carbon storage constraint
                '''
            elif co2_emission_column == 'Carbon storage constraint':

                if last_part_key == 'prod' and energy in energy_list:
                    self.set_partial_derivative_for_other_types(
                        (EnergyMix.CARBON_STORAGE_CONSTRAINT,), (f'{energy}.energy_production', energy),  scaling_factor_energy_production * value)
                elif last_part_key == 'cons' and energy in energy_list:
                    for energy_df in energy_list:
                        list_columnsenergycons = list(
                            inputs_dict[f'{energy_df}.energy_consumption'].columns)
                        if f'{energy} (TWh)' in list_columnsenergycons:
                            self.set_partial_derivative_for_other_types(
                                (EnergyMix.CARBON_STORAGE_CONSTRAINT,), (f'{energy_df}.energy_consumption', f'{energy} (TWh)'), scaling_factor_energy_consumption * value)
                elif last_part_key == 'co2_per_use':
                    self.set_partial_derivative_for_other_types(
                        (EnergyMix.CARBON_STORAGE_CONSTRAINT,), (f'{energy}.CO2_per_use', 'CO2_per_use'),  value)
                elif energy_prod_info.startswith('CO2 for food (Mt)'):
                    self.set_partial_derivative_for_other_types(
                        (EnergyMix.CARBON_STORAGE_CONSTRAINT,), ('co2_for_food', f'{CO2.name} for food (Mt)'), value)

                elif energy_prod_info.startswith(f'{CarbonCapture.name} from energy mix (Mt)'):
                    self.set_partial_derivative_for_other_types(
                        (EnergyMix.CARBON_STORAGE_CONSTRAINT,), ('co2_emissions_from_energy_mix', f'{CarbonCapture.name} from energy mix (Mt)'), value)

                elif energy_prod_info.startswith(f'{CarbonCapture.name} needed by energy mix (Mt)'):
                    self.set_partial_derivative_for_other_types(
                        (EnergyMix.CARBON_STORAGE_CONSTRAINT,), ('co2_emissions_needed_by_energy_mix', f'{CarbonCapture.name} needed by energy mix (Mt)'), value)

                else:
                    very_last_part_key = energy_prod_info.split('#')[2]
                    if very_last_part_key == 'prod':
                        self.set_partial_derivative_for_other_types(
                            (EnergyMix.CARBON_STORAGE_CONSTRAINT,), (f'{energy}.energy_production', last_part_key),  scaling_factor_energy_production * value)
                    elif very_last_part_key == 'cons':
                        self.set_partial_derivative_for_other_types(
                            (EnergyMix.CARBON_STORAGE_CONSTRAINT,), (f'{energy}.energy_consumption', last_part_key),  scaling_factor_energy_production * value)

                '''
                Ratio available carbon capture
                '''

            elif co2_emission_column == 'ratio_available_carbon_capture':

                if last_part_key == 'prod':
                    self.set_partial_derivative_for_other_types(
                        ('ratio_available_carbon_capture', 'ratio'), (f'{energy}.energy_production', energy),  np.identity(len(years)) * scaling_factor_energy_production * value)
                elif last_part_key == 'cons':
                    for energy_df in energy_list:
                        list_columnsenergycons = list(
                            inputs_dict[f'{energy_df}.energy_consumption'].columns)
                        if f'{energy} (TWh)' in list_columnsenergycons:
                            self.set_partial_derivative_for_other_types(
                                ('ratio_available_carbon_capture', 'ratio'), (f'{energy_df}.energy_consumption', f'{energy} (TWh)'), np.identity(len(years)) * scaling_factor_energy_consumption * value)

                else:
                    very_last_part_key = energy_prod_info.split('#')[2]
                    if very_last_part_key == 'prod':
                        self.set_partial_derivative_for_other_types(
                            ('ratio_available_carbon_capture', 'ratio'), (f'{energy}.energy_production', last_part_key), np.identity(len(years)) * scaling_factor_energy_production * value)
                    elif very_last_part_key == 'cons':
                        self.set_partial_derivative_for_other_types(
                            ('ratio_available_carbon_capture', 'ratio'), (f'{energy}.energy_consumption', last_part_key), np.identity(len(years)) * scaling_factor_energy_production * value)

        #--------------------------------------#
        #---- Stream Demand ratio gradients----#
        #--------------------------------------#
        #--------------------------------------#
        #---- Land use constraint gradients----#
        #--------------------------------------#

        for energy in energy_list:
            for key in outputs_dict['land_demand_ccus_df']:
                if key in inputs_dict[f'{energy}.land_use_required'] and key != 'years':
                    self.set_partial_derivative_for_other_types(('land_demand_ccus_df', key),
                                                                (f'{energy}.land_use_required', key), np.identity(len(years)))
        #---------------------------------------------------#
        #---- Other objectives and constraints gradients----#
        #---------------------------------------------------#
#         if self.SYNGAS_NAME in energy_list:
#
#             dco2_emissions_objective_dsyngas_ratio, dco2_emissions_dsyngas_ratio = self.compute_dco2_emissions_objective_dsyngas_ratio(
#                 'syngas')
#             self.set_partial_derivative(
#                 'co2_emissions_objective', 'syngas_ratio', dco2_emissions_objective_dsyngas_ratio / 100.0)
#             self.set_partial_derivative_for_other_types(
#                 ('co2_emissions_Gt', 'Total CO2 emissions'), ('syngas_ratio',), dco2_emissions_dsyngas_ratio / 1000.0 / 100.0)

        if CarbonCapture.name in energy_list:
            self.set_partial_derivative_for_other_types(
                ('CCS_price', 'ccs_price_per_tCO2'), (f'{CarbonCapture.name}.energy_prices', CarbonCapture.name), np.identity(len(years)))
        if CarbonStorage.name in energy_list:
            self.set_partial_derivative_for_other_types(
                ('CCS_price', 'ccs_price_per_tCO2'), (f'{CarbonStorage.name}.energy_prices', CarbonStorage.name), np.identity(len(years)))

    def compute_dratio_objective(self, stream_ratios,  ratio_ref, energy_list):
        '''
        Compute the ratio_objective with the gradient of stream_ratios vs any input and the ratio ojective value 
        obj = smooth_maximum(100.0 - ratio_arrays, 3)/ratio_ref

        dobj/dratio = -dsmooth_max(100.0 - ratio_arrays, 3)/ratio_ref
        '''

        dsmooth_dvar = get_dsmooth_dvariable(
            100.0 - stream_ratios[energy_list].values.flatten(), 3)
        dobjective_dratio = -np.asarray(dsmooth_dvar) / ratio_ref

        return dobjective_dratio

#     def compute_dco2_emissions_objective_dsyngas_ratio(self, energy):
#         """
#             co2_emissions_objective = np.asarray([alpha * self.energy_model.total_co2_emissions['Total CO2 emissions'].sum()
#                                               / (self.energy_model.total_co2_emissions['Total CO2 emissions'][0] * delta_years), ])
#             -----
#             self.total_co2_emissions[f'{energy} CO2 by use (Mt)'] = self.stream_class_dict[energy].data_energy_dict['CO2_per_use'] / \
#                         self.stream_class_dict[energy].data_energy_dict['high_calorific_value'] * \
#                         self.production[f'production {energy} ({self.energy_class_dict[energy].unit})'].values
#             -----
#             self.stream_class_dict['syngas'].data_energy_dict['high_calorific_value'] = compute_calorific_value(
#             inputs_dict['syngas_ratio'])
#         """
#         net_production = self.get_sosdisc_outputs(
#             'energy_production_detailed')
#         alpha = self.get_sosdisc_inputs('alpha')
#         tot_co2_emissions_sum = self.get_sosdisc_outputs(
#             'co2_emissions')['Total CO2 emissions'].sum()
#         tot_co2_emissions_0 = self.get_sosdisc_outputs(
#             'co2_emissions')['Total CO2 emissions'][0]
#         years = np.arange(self.get_sosdisc_inputs('year_start'),
#                           self.get_sosdisc_inputs('year_end') + 1)
#         delta_years = (years[-1] - years[0] + 1)
#
#         dcalval_dsyngas_ratio = compute_dcal_val_dsyngas_ratio(
#             self.get_sosdisc_inputs('syngas_ratio') / 100.0)
#
#         data_fuel_dict = self.get_sosdisc_inputs(f'{energy}.data_fuel_dict')
#
#         dtot_CO2_emissions = -data_fuel_dict['CO2_per_use'] * \
#             dcalval_dsyngas_ratio * \
#             np.maximum(0.0, net_production[f'production {energy} ({self.stream_class_dict[energy].unit})'].values) / \
#             (data_fuel_dict['high_calorific_value']**2)
#
#         mask = np.insert(np.zeros(len(years) - 1), 0, 1)
#         dco2_emissions_objective_dsyngas_ratio = (alpha * dtot_CO2_emissions /
#                                                   (tot_co2_emissions_0 * delta_years)) - \
#             (mask * dtot_CO2_emissions * alpha * tot_co2_emissions_sum /
#              delta_years / (tot_co2_emissions_0)**2)
#
# return np.atleast_2d(dco2_emissions_objective_dsyngas_ratio),
# dtot_CO2_emissions * np.identity(len(years))

    def compute_ddelta_energy_prices(self, energy):

        years = np.arange(self.get_sosdisc_inputs('year_start'),
                          self.get_sosdisc_inputs('year_end') + 1)

        self.set_partial_derivative(
            f'{energy}.{EnergyMix.DELTA_ENERGY_PRICES}', (f'{energy}.energy_prices', energy), -np.identity(len(years)))

    def compute_ddelta_emissions_co2(self, energy):

        years = np.arange(self.get_sosdisc_inputs('year_start'),
                          self.get_sosdisc_inputs('year_end') + 1)

        self.set_partial_derivative(
            f'{energy}.{EnergyMix.DELTA_CO2_EMISSIONS}', (f'{energy}.CO2_emissions', energy), -np.identity(len(years)))

    def compute_denergy_production_objective_dprod(self, dtotal_production_denergy_production):
        ''' energy_production_objective = np.asarray([(1. - alpha) * self.energy_model.production['Total production'][0] * delta_years
                                                  / self.energy_model.production['Total production'].sum(), ])
        '''
        alpha = self.get_sosdisc_inputs('alpha')
        tot_energy_production_sum = self.get_sosdisc_outputs(
            'energy_production')['Total production'].sum()
        dtot_energy_production_sum = dtotal_production_denergy_production.sum(
            axis=0)
        tot_energy_production_0 = self.get_sosdisc_outputs(
            'energy_production')['Total production'][0]
        dtot_energy_production_0 = dtotal_production_denergy_production[0]
        years = np.arange(self.get_sosdisc_inputs('year_start'),
                          self.get_sosdisc_inputs('year_end') + 1)
        delta_years = (years[-1] - years[0] + 1)

        u = (1. - alpha) * \
            tot_energy_production_0 * delta_years
        v = tot_energy_production_sum
        u_prime = (1. - alpha) * dtot_energy_production_0 * \
            delta_years
        v_prime = dtot_energy_production_sum
        dprod_objective_dprod = u_prime / v - u * v_prime / v**2

        return dprod_objective_dprod

    def compute_dproduction_net_denergy_production(self, energy, production_df, energy_price):
        '''
        energy_mean = sum(energy*1e6*prod*1e6)/total*1e6
        '''

        denergy_mean_prod = (
            energy_price[energy] * 1e6 * production_df['Total production'] - production_df['energy_price_pond']) / (1e6 * (production_df['Total production'])**2)

        # derivative of negative prod is 0
        index_l = production_df[production_df[f'production {energy} (TWh)']
                                == 0].index
        denergy_mean_prod.loc[index_l] = 0
        return denergy_mean_prod

    def compute_dtotal_production_denergy_production(self, production_detailed_df, min_energy):
        '''
        Compute gradient of production['Total production'] by {energy}.energy_prod[{energy}] taking into account 
        the exponential decrease towards the limit applied on the calculation of the total net energy production
        Inputs: minimum_energy_production, production_df
        Outputs:dtotal_production_denergy_production
        '''
        years = production_detailed_df['years']
        dtotal_production_denergy_production = np.ones(len(years))

        pre_limit_total_production = pd.DataFrame({'years': years,
                                                   'Total production': 0.0})
        pre_limit_total_production['Total production'] = production_detailed_df[[
            column for column in production_detailed_df if column.endswith('(TWh)')]].sum(axis=1)

        total_prod = pre_limit_total_production['Total production'].values
        if total_prod.min() < min_energy:
                # To avoid underflow : exp(-200) is considered to be the
                # minimum value for the exp
            total_prod[total_prod < -200.0 * min_energy] = -200.0 * min_energy
            dtotal_production_denergy_production[total_prod < min_energy] = np.exp(
                total_prod[total_prod < min_energy] / min_energy) * np.exp(-1) / 10.0

        return np.identity(len(years)) * dtotal_production_denergy_production

    def compute_ddemand_ratio_denergy_production(self, energy, sub_production_dict, sub_consumption_dict, stream_class_dict,
                                                 scaling_factor_production, years):
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
        ddemand_ratio_denergy_prod = np.identity(len(years)) * 100.0 *\
            np.where(energy_prod_limited <= energy_cons_limited,
                     scaling_factor_production * denergy_prod_limited / energy_cons_limited,
                     0.0)

        # If prod < cons, set the identity element for the given year to
        # the corresponding value
        denergy_cons_limited = compute_dfunc_with_exp_min(
            energy_consumption, 1.0e-10)
        energy_cons_limited = compute_func_with_exp_min(
            energy_consumption, 1.0e-10)
        ddemand_ratio_denergy_cons = np.identity(len(years)) * 100.0 *\
            np.where(energy_prod_limited <= energy_cons_limited,
                     -scaling_factor_production * energy_prod_limited * denergy_cons_limited /
                     energy_cons_limited**2,
                     0.0)

        return ddemand_ratio_denergy_prod, ddemand_ratio_denergy_cons


#

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['Stream ratio', 'Carbon storage constraint']

        chart_filters.append(ChartFilter(
            'Charts', chart_list, chart_list, 'charts'))

        price_unit_list = ['$/MWh', '$/t']
        chart_filters.append(ChartFilter(
            'Price unit', price_unit_list, price_unit_list, 'price_unit'))

        year_start, year_end = self.get_sosdisc_inputs(
            ['year_start', 'year_end'])
        years = list(np.arange(year_start, year_end + 1, 5))
        chart_filters.append(ChartFilter(
            'Years for energy mix', years, [year_start, year_end], 'years'))
        return chart_filters

    def get_post_processing_list(self, filters=None):

        # For the outputs, making a graph for block fuel vs range and blocktime vs
        # range

        instanciated_charts = []
        charts = []

        price_unit_list = ['$/MWh', '$/t']
        years_list = [self.get_sosdisc_inputs('year_start')]
        energy_list = self.get_sosdisc_inputs('ccs_list')
        # Overload default value with chart filter
        if filters is not None:
            for chart_filter in filters:
                if chart_filter.filter_key == 'charts':
                    charts = chart_filter.selected_values
                if chart_filter.filter_key == 'price_unit':
                    price_unit_list = chart_filter.selected_values
                if chart_filter.filter_key == 'years':
                    years_list = chart_filter.selected_values

        if 'CO2 emissions' in charts:
            new_chart = []

            new_chart = self.get_chart_co2_limited_storage()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

            new_chart = self.get_chart_co2_emissions_sinks()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

            new_chart = self.get_chart_co2_emissions_sources()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

            new_chart = self.get_chart_co2_streams()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'Carbon intensity' in charts:
            new_charts = self.get_chart_comparison_carbon_intensity()
            for new_chart in new_charts:
                if new_chart is not None:
                    instanciated_charts.append(new_chart)

        if 'production' in charts:
            new_chart = self.get_chart_energies_net_production()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

            new_chart = self.get_chart_energies_brut_production()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

            new_chart = self.get_chart_energies_net_production_limit()
            if new_chart is not None:
                instanciated_charts.append(new_chart)
        if 'Energy mix' in charts:
            new_charts = self.get_pie_charts_production(years_list)
            for new_chart in new_charts:
                if new_chart is not None:
                    instanciated_charts.append(new_chart)

        if 'Demand violation' in charts and '$/MWh' in price_unit_list:
            new_chart = self.get_chart_demand_violation_kwh()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'Delta price' in charts:
            new_chart = self.get_chart_delta_price()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        if 'Carbon storage constraint' in charts:
            new_chart = self.get_chart_carbon_storage_constraint()
            if new_chart is not None:
                instanciated_charts.append(new_chart)
        if 'Stream ratio' in charts:
            new_chart = self.get_chart_stream_ratio()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

            new_chart = self.get_chart_stream_consumed_by_techno()
            if new_chart is not None:
                instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_chart_solid_energy_elec_constraint(self):
        energy_production_detailed = self.get_sosdisc_outputs(
            'energy_production_detailed')
        solid_fuel_elec_percentage = self.get_sosdisc_inputs(
            'solid_fuel_elec_percentage')
        chart_name = f'Solid energy and electricity production constraint'
        new_chart = TwoAxesInstanciatedChart(
            'years', 'Energy (TWh)', chart_name=chart_name)

        sum_solid_fuel_elec = energy_production_detailed['production solid_fuel (TWh)'].values + \
            energy_production_detailed['production electricity (TWh)'].values
        new_serie = InstanciatedSeries(list(energy_production_detailed['years'].values), list(sum_solid_fuel_elec),
                                       'Sum of solid fuel and electricity productions', 'lines')
        new_chart.series.append(new_serie)

        new_serie = InstanciatedSeries(list(energy_production_detailed['years'].values), list(energy_production_detailed['Total production'].values * solid_fuel_elec_percentage),
                                       f'{100*solid_fuel_elec_percentage}% of total production', 'lines')

        new_chart.series.append(new_serie)
        return new_chart

    def get_chart_liquid_hydrogen_constraint(self):
        energy_production_detailed = self.get_sosdisc_outputs(
            'energy_production_detailed')
        liquid_hydrogen_percentage = self.get_sosdisc_inputs(
            'liquid_hydrogen_percentage')
        chart_name = f'Liquid hydrogen production constraint'
        new_chart = TwoAxesInstanciatedChart(
            'years', 'Energy (TWh)', chart_name=chart_name)

        new_serie = InstanciatedSeries(list(energy_production_detailed['years'].values), list(energy_production_detailed['production hydrogen.liquid_hydrogen (TWh)'].values),
                                       'Liquid hydrogen production', 'lines')
        new_chart.series.append(new_serie)
        new_serie = InstanciatedSeries(list(energy_production_detailed['years'].values), list(energy_production_detailed['production hydrogen.gaseous_hydrogen (TWh)'].values),
                                       'Gaseous hydrogen production', 'lines')
        new_chart.series.append(new_serie)
        constraint = liquid_hydrogen_percentage * \
            (energy_production_detailed['production hydrogen.gaseous_hydrogen (TWh)'].values +
             energy_production_detailed['production hydrogen.liquid_hydrogen (TWh)'].values)
        new_serie = InstanciatedSeries(list(energy_production_detailed['years'].values), list(constraint),
                                       f'{100*liquid_hydrogen_percentage}% of total hydrogen production', 'lines')
        new_chart.series.append(new_serie)
        return new_chart

    def get_chart_energy_price_in_dollar_kwh(self):
        energy_prices = self.get_sosdisc_outputs('energy_prices')

        chart_name = 'Detailed prices of energy mix with CO2 taxes<br>from production (used for technology prices)'
        energy_list = self.get_sosdisc_inputs('energy_list')
        max_value = 0
        for energy in energy_list:
            if self.stream_class_dict[energy].unit == 'TWh':
                techno_price = self.get_sosdisc_inputs(
                    f'{energy}.energy_prices')
                max_value = max(
                    max(energy_prices[energy].values.tolist()), max_value)

        new_chart = TwoAxesInstanciatedChart(
            'years', 'Prices [$/MWh]', primary_ordinate_axis_range=[0, max_value], chart_name=chart_name)

        for energy in energy_list:
            if self.stream_class_dict[energy].unit == 'TWh':
                techno_price = self.get_sosdisc_inputs(
                    f'{energy}.energy_prices')
                serie = InstanciatedSeries(
                    energy_prices['years'].values.tolist(),
                    techno_price[energy].values.tolist(), energy, 'lines')
                new_chart.series.append(serie)

        return new_chart

    def get_chart_co2_streams(self):
        '''
        Plot the total co2 emissions sources - sinks
        '''
        chart_name = 'Total CO2 emissions before and after CCS'
        co2_emissions = self.get_sosdisc_outputs('co2_emissions')
        new_chart = TwoAxesInstanciatedChart('years', 'CO2 emissions (Gt)',
                                             chart_name=chart_name)

        x_serie_1 = co2_emissions['years'].values.tolist()

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions['CO2 emissions sources'].values / 1.0e3).tolist(), 'CO2 emissions sources')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions['CO2 emissions sinks'].values / 1.0e3).tolist(), 'CO2 emissions sinks')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions['Total CO2 emissions'].values / 1.0e3).tolist(), 'CO2 emissions after CCUS')
        new_chart.add_series(serie)

        return new_chart

    def get_chart_co2_to_store(self):
        '''
        Plot a graph to understand CO2 to store
        '''
        chart_name = 'CO2 emissions captured, used and to store'
        co2_emissions = self.get_sosdisc_outputs('co2_emissions')
        new_chart = TwoAxesInstanciatedChart('years', 'CO2 emissions (Gt)',
                                             chart_name=chart_name)

        x_serie_1 = co2_emissions['years'].values.tolist()

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'{CarbonCapture.name} (Mt) from CC technos'].values / 1.0e3).tolist(), 'CO2 captured from CC technos')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'{CarbonCapture.name} from energy mix (Mt)'].values / 1.0e3).tolist(), f'CO2 captured from energy mix')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (-co2_emissions[f'{CarbonCapture.name} needed by energy mix (Mt)'].values / 1.0e3).tolist(), f'{CarbonCapture.name} used by energy mix')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (-co2_emissions[f'{CO2.name} for food (Mt)'].values / 1.0e3).tolist(), f'{CO2.name} used for food')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'{CarbonCapture.name} to be stored (Mt)'].values / 1.0e3).tolist(), f'CO2 to store')
        new_chart.add_series(serie)

        return new_chart

    def get_chart_co2_limited_storage(self):
        '''
        Plot a graph to understand storage
        '''
        chart_name = 'CO2 emissions storage limited by CO2 to store'
        co2_emissions = self.get_sosdisc_outputs('co2_emissions_ccus')
        new_chart = TwoAxesInstanciatedChart('years', 'CO2 emissions (Gt)',
                                             chart_name=chart_name)

        x_serie_1 = co2_emissions['years'].values.tolist()
        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'{CarbonCapture.name} to be stored (Mt)'].values / 1.0e3).tolist(), f'CO2 to store')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'{CarbonStorage.name} (Mt)'].values / 1.0e3).tolist(), f'CO2 storage by invest')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'{CarbonStorage.name} Limited by capture (Mt)'].values / 1.0e3).tolist(), f'CO2 storage limited by CO2 to store')
        new_chart.add_series(serie)

        return new_chart

    def get_chart_co2_emissions_sources(self):
        '''
        Plot all CO2 emissions sources 
        '''
        chart_name = 'CO2 emissions sources'
        co2_emissions = self.get_sosdisc_outputs('co2_emissions')
        new_chart = TwoAxesInstanciatedChart('years', 'CO2 emissions (Gt)',
                                             chart_name=chart_name)

        x_serie_1 = co2_emissions['years'].values.tolist()

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions['Total CO2 by use (Mt)'].values / 1.0e3).tolist(), 'CO2 by use (net production burned)')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'Total {CarbonCapture.flue_gas_name} (Mt)'].values / 1.0e3).tolist(), 'Flue gas from plants')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1, (co2_emissions[f'{CarbonCapture.name} from energy mix (Mt)'].values / 1.0e3).tolist(), 'Carbon capture from energy mix (FT or Sabatier)')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions[f'{CO2.name} from energy mix (Mt)'].values / 1.0e3).tolist(), 'CO2 from energy mix (machinery fuels)')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (co2_emissions['CO2 emissions sources'].values / 1.0e3).tolist(), 'Total sources')
        new_chart.add_series(serie)

        return new_chart

    def get_chart_co2_emissions_sinks(self):
        '''
        Plot all CO2 emissions sinks 
        '''
        chart_name = 'CO2 emissions sinks'
        co2_emissions = self.get_sosdisc_outputs('co2_emissions')
        new_chart = TwoAxesInstanciatedChart('years', 'CO2 emissions (Gt)',
                                             chart_name=chart_name)

        x_serie_1 = co2_emissions['years'].values.tolist()
        serie = InstanciatedSeries(
            x_serie_1,
            (-co2_emissions[f'{CarbonStorage.name} Limited by capture (Mt)'].values / 1.0e3).tolist(), 'Carbon storage limited by capture')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (-co2_emissions[f'{CO2.name} removed by energy mix (Mt)'].values / 1.0e3).tolist(), f'{CO2.name} removed by energy mix')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1, (-co2_emissions[f'{CarbonCapture.name} needed by energy mix (Mt)'].values / 1.0e3).tolist(), f'{CarbonCapture.name} needed by energy mix')
        new_chart.add_series(serie)

        serie = InstanciatedSeries(
            x_serie_1,
            (-co2_emissions['CO2 emissions sinks'].values / 1.0e3).tolist(), 'Total sinks')
        new_chart.add_series(serie)

        return new_chart

    def get_chart_stream_ratio(self):
        '''
        Plot stream ratio chart
        '''
        chart_name = f'Stream Ratio Map'

        all_ccs_demand_ratio = self.get_sosdisc_outputs(
            'all_ccs_demand_ratio')

        years = all_ccs_demand_ratio['years'].values
        streams = [
            col for col in all_ccs_demand_ratio.columns if col not in ['years', ]]

        z = np.asarray(all_ccs_demand_ratio[streams].values).T
        fig = go.Figure()
        fig.add_trace(go.Heatmap(z=list(z), x=list(years), y=list(streams),
                                 type='heatmap', colorscale=['red', 'white'],
                                 colorbar={'title': 'Value of ratio'},
                                 opacity=0.5, zmax=100.0, zmin=0.0,))
        new_chart = InstantiatedPlotlyNativeChart(
            fig, chart_name=chart_name, default_title=True)
        return new_chart

    def get_chart_carbon_storage_constraint(self):

        co2_emissions = self.get_sosdisc_outputs('co2_emissions_ccus')

        carbon_storage_limit = self.get_sosdisc_inputs('carbonstorage_limit')
        years = list(co2_emissions['years'])

        chart_name = 'Cumulated carbon storage (Gt) vs years'

        year_start = years[0]
        year_end = years[len(years) - 1]

        new_chart = TwoAxesInstanciatedChart('years', 'Cumulated carbon storage (Gt)',
                                             chart_name=chart_name)

        visible_line = True

        new_series = InstanciatedSeries(
            years, list(co2_emissions[f'{CarbonStorage.name} Limited by capture (Mt)'].cumsum().values / 1e3), 'cumulative sum of carbon capture (Gt)', 'lines', visible_line)

        new_chart.series.append(new_series)

        # Rockstrom Limit

        ordonate_data = [carbon_storage_limit / 1e3] * int(len(years) / 5)
        abscisse_data = np.linspace(
            year_start, year_end, int(len(years) / 5))
        new_series = InstanciatedSeries(
            abscisse_data.tolist(), ordonate_data, 'Carbon storage limit (Gt)', 'scatter')

        new_chart.series.append(new_series)

        return new_chart
