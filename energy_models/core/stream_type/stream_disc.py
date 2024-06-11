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
from climateeconomics.core.core_witness.climateeco_discipline import (
    ClimateEcoDiscipline,
)
from sostrades_core.execution_engine.sos_wrapp import SoSWrapp
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import (
    InstanciatedSeries,
    TwoAxesInstanciatedChart,
)
from sostrades_core.tools.post_processing.pie_charts.instanciated_pie_chart import (
    InstanciatedPieChart,
)

from energy_models.core.stream_type.resources_models.resource_glossary import (
    ResourceGlossary,
)
from energy_models.glossaryenergy import GlossaryEnergy


class StreamDiscipline(SoSWrapp):
    # ontology information
    _ontology_data = {
        'label': 'Core Stream Type Model',
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
        GlossaryEnergy.YearStart: ClimateEcoDiscipline.YEAR_START_DESC_IN,
        GlossaryEnergy.YearEnd: GlossaryEnergy.YearEndVar,
        'exp_min': {'type': 'bool', 'default': True, 'user_level': 2},
        'scaling_factor_energy_production': {'type': 'float', 'default': 1e3, 'unit': '-', 'user_level': 2,
                                             'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'scaling_factor_energy_consumption': {'type': 'float', 'default': 1e3, 'unit': '-', 'user_level': 2,
                                              'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_public'},
        'scaling_factor_techno_consumption': {'type': 'float', 'default': 1e3, 'unit': '-',
                                              'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_public',
                                              'user_level': 2},
        'scaling_factor_techno_production': {'type': 'float', 'default': 1e3, 'unit': '-',
                                             'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_public',
                                             'user_level': 2}
    }

    # -- Here are the results of concatenation of each techno prices,consumption and production
    DESC_OUT = {
        GlossaryEnergy.EnergyPricesValue: {'type': 'dataframe', 'unit': '$/MWh'},
        'energy_detailed_techno_prices': {'type': 'dataframe', 'unit': '$/MWh'},
        # energy_production and energy_consumption stored in PetaWh for
        # coupling variables scaling
        GlossaryEnergy.EnergyConsumptionValue: {'type': 'dataframe', 'unit': 'PWh'},
        GlossaryEnergy.EnergyConsumptionWithoutRatioValue: {'type': 'dataframe', 'unit': 'PWh'},
        GlossaryEnergy.EnergyProductionValue: {'type': 'dataframe', 'unit': 'PWh'},
        GlossaryEnergy.EnergyProductionDetailedValue: GlossaryEnergy.EnergyProductionDetailedDf,
        'techno_mix': {'type': 'dataframe', 'unit': '%'},
        GlossaryEnergy.LandUseRequiredValue: {'type': 'dataframe', 'unit': 'Gha'},
        GlossaryEnergy.EnergyTypeCapitalDfValue: GlossaryEnergy.EnergyTypeCapitalDf
    }

    _maturity = 'Research'
    energy_name = 'stream'

    def __init__(self, sos_name, logger: logging.Logger):
        super().__init__(sos_name=sos_name, logger=logger)
        self.grad_techno_mix_vs_prod_dict = None
        self.energy_model = None

    def setup_sos_disciplines(self):
        dynamic_inputs = {}

        if GlossaryEnergy.techno_list in self.get_data_in():
            techno_list = self.get_sosdisc_inputs(GlossaryEnergy.techno_list)
            if techno_list is not None:
                for techno in techno_list:
                    dynamic_inputs[f'{techno}.{GlossaryEnergy.TechnoCapitalValue}'] = \
                        GlossaryEnergy.get_dynamic_variable(GlossaryEnergy.TechnoCapitalDf)
                    dynamic_inputs[f'{techno}.{GlossaryEnergy.TechnoConsumptionValue}'] = {
                        'type': 'dataframe', 'unit': 'TWh or Mt',
                        'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                 f'{GlossaryEnergy.electricity} (TWh)': ('float', None, True),
                                                 f'{ResourceGlossary.AmineResource} (Mt)': ('float', None, True),
                                                 f'{GlossaryEnergy.methane} (TWh)': ('float', None, True),
                                                 f'{ResourceGlossary.CalciumResource} (Mt)': ('float', None, True),
                                                 f'{ResourceGlossary.PotassiumResource} (Mt)': ('float', None, True),
                                                 f'{GlossaryEnergy.biomass_dry} (TWh)': ('float', None, True),
                                                 f'{GlossaryEnergy.carbon_capture} (Mt)': ('float', None, True),
                                                 f'{ResourceGlossary.CarbonResource} (Mt)': ('float', None, True), }}
                    dynamic_inputs[f'{techno}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}'] = {
                        'type': 'dataframe', 'unit': 'TWh or Mt',
                        'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                 f'{ResourceGlossary.AmineResource} (Mt)': ('float', None, True),
                                                 f'{GlossaryEnergy.methane} (TWh)': ('float', None, True),
                                                 f'{ResourceGlossary.CalciumResource} (Mt)': ('float', None, True),
                                                 f'{ResourceGlossary.PotassiumResource} (Mt)': ('float', None, True),
                                                 f'{GlossaryEnergy.electricity} (TWh)': ('float', None, True),
                                                 f'{GlossaryEnergy.biomass_dry} (TWh)': ('float', None, True),
                                                 f'{GlossaryEnergy.carbon_capture} (Mt)': ('float', None, True),
                                                 f'{ResourceGlossary.CarbonResource} (Mt)': ('float', None, True),
                                                 }}
                    dynamic_inputs[f'{techno}.{GlossaryEnergy.TechnoProductionValue}'] = {
                        'type': 'dataframe', 'unit': 'TWh or Mt',
                        'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                 f'{GlossaryEnergy.carbon_capture} (Mt)': ('float', None, True),
                                                 'CO2 from Flue Gas (Mt)': ('float', None, True),
                                                 f'{GlossaryEnergy.carbon_storage} (Mt)': ('float', None, True),
                                                 }}
                    dynamic_inputs[f'{techno}.{GlossaryEnergy.TechnoPricesValue}'] = {
                        'type': 'dataframe', 'unit': '$/MWh',
                        'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                 f'{GlossaryEnergy.direct_air_capture}.AmineScrubbing': ('float', None, True),
                                                 f'{GlossaryEnergy.direct_air_capture}.AmineScrubbing_wotaxes': ('float', None, True),
                                                 f'{GlossaryEnergy.direct_air_capture}.CalciumPotassiumScrubbing': ('float', None, True),
                                                 f'{GlossaryEnergy.direct_air_capture}.CalciumPotassiumScrubbing_wotaxes': ('float', None, True),
                                                 f'{GlossaryEnergy.flue_gas_capture}.CalciumLooping': ('float', None, True),
                                                 f'{GlossaryEnergy.flue_gas_capture}.CalciumLooping_wotaxes': ('float', None, True),
                                                 f'{GlossaryEnergy.flue_gas_capture}.ChilledAmmoniaProcess': ('float', None, True),
                                                 f'{GlossaryEnergy.flue_gas_capture}.ChilledAmmoniaProcess_wotaxes': ('float', None, True),
                                                 f'{GlossaryEnergy.flue_gas_capture}.CO2Membranes': ('float', None, True),
                                                 f'{GlossaryEnergy.flue_gas_capture}.CO2Membranes_wotaxes': ('float', None, True),
                                                 f'{GlossaryEnergy.flue_gas_capture}.MonoEthanolAmine': ('float', None, True),
                                                 f'{GlossaryEnergy.flue_gas_capture}.MonoEthanolAmine_wotaxes': ('float', None, True),
                                                 f'{GlossaryEnergy.flue_gas_capture}.PiperazineProcess': ('float', None, True),
                                                 f'{GlossaryEnergy.flue_gas_capture}.PiperazineProcess_wotaxes': ('float', None, True),
                                                 f'{GlossaryEnergy.flue_gas_capture}.PressureSwingAdsorption': ('float', None, True),
                                                 f'{GlossaryEnergy.flue_gas_capture}.PressureSwingAdsorption_wotaxes': ('float', None, True),
                                                 'BiomassBuryingFossilization': ('float', None, True),
                                                 'BiomassBuryingFossilization_wotaxes': ('float', None, True),
                                                 'DeepOceanInjection': ('float', None, True),
                                                 'DeepOceanInjection_wotaxes': ('float', None, True),
                                                 'DeepSalineFormation': ('float', None, True),
                                                 'DeepSalineFormation_wotaxes': ('float', None, True),
                                                 'DepletedOilGas': ('float', None, True),
                                                 'DepletedOilGas_wotaxes': ('float', None, True),
                                                 'EnhancedOilRecovery': ('float', None, True),
                                                 'EnhancedOilRecovery_wotaxes': ('float', None, True),
                                                 'GeologicMineralization': ('float', None, True),
                                                 'GeologicMineralization_wotaxes': ('float', None, True),
                                                 'PureCarbonSolidStorage': ('float', None, True),
                                                 'PureCarbonSolidStorage_wotaxes': ('float', None, True),
                                                 }}
                    dynamic_inputs[f'{techno}.{GlossaryEnergy.LandUseRequiredValue}'] = {
                        'type': 'dataframe', 'unit': 'Gha',
                        'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                 f'{GlossaryEnergy.direct_air_capture}.AmineScrubbing (Gha)': ('float', None, True),
                                                 f'{GlossaryEnergy.direct_air_capture}.CalciumPotassiumScrubbing (Gha)': ('float', None, True),
                                                 f'{GlossaryEnergy.flue_gas_capture}.CalciumLooping (Gha)': ('float', None, True),
                                                 f'{GlossaryEnergy.flue_gas_capture}.ChilledAmmoniaProcess (Gha)': ('float', None, True),
                                                 f'{GlossaryEnergy.flue_gas_capture}.CO2Membranes (Gha)': ('float', None, True),
                                                 f'{GlossaryEnergy.flue_gas_capture}.MonoEthanolAmine (Gha)': ('float', None, True),
                                                 f'{GlossaryEnergy.flue_gas_capture}.PiperazineProcess (Gha)': ('float', None, True),
                                                 f'{GlossaryEnergy.flue_gas_capture}.PressureSwingAdsorption (Gha)': ('float', None, True),
                                                 'BiomassBuryingFossilization (Gha)': ('float', None, True),
                                                 'DeepOceanInjection (Gha)': ('float', None, True),
                                                 'DeepSalineFormation (Gha)': ('float', None, True),
                                                 'DepletedOilGas (Gha)': ('float', None, True),
                                                 'EnhancedOilRecovery (Gha)': ('float', None, True),
                                                 'GeologicMineralization (Gha)': ('float', None, True),
                                                 'PureCarbonSolidStorage (Gha)': ('float', None, True),
                                                 }}

        self.add_inputs(dynamic_inputs)

    def run(self):
        '''
        Run for all stream disciplines
        '''
        # -- get inputs
        inputs_dict = self.get_sosdisc_inputs()
        # -- configure class with inputs
        self.energy_model.configure(inputs_dict)
        # -- compute informations
        cost_details, production, consumption, consumption_woratio, techno_mix = self.energy_model.compute(inputs_dict,
                                                                                                           exp_min=
                                                                                                           inputs_dict[
                                                                                                               'exp_min'])

        cost_details_technos = self.energy_model.sub_prices

        # Scale production and consumption
        for column in production.columns:
            if column != GlossaryEnergy.Years:
                production[column] /= inputs_dict['scaling_factor_energy_production']
        for column in consumption.columns:
            if column != GlossaryEnergy.Years:
                consumption[column] /= inputs_dict['scaling_factor_energy_consumption']
                consumption_woratio[column] /= inputs_dict['scaling_factor_energy_consumption']

        outputs_dict = {GlossaryEnergy.EnergyPricesValue: cost_details,
                        'energy_detailed_techno_prices': cost_details_technos,
                        GlossaryEnergy.EnergyConsumptionValue: consumption,
                        GlossaryEnergy.EnergyConsumptionWithoutRatioValue: consumption_woratio,
                        GlossaryEnergy.EnergyProductionValue: production,
                        GlossaryEnergy.EnergyProductionDetailedValue: self.energy_model.production_by_techno,
                        'techno_mix': techno_mix,
                        GlossaryEnergy.LandUseRequiredValue: self.energy_model.land_use_required,
                        GlossaryEnergy.EnergyTypeCapitalDfValue: self.energy_model.energy_type_capital
                        }
        
        self.store_sos_outputs_values(outputs_dict)

    def compute_sos_jacobian(self):

        inputs_dict = self.get_sosdisc_inputs()
        outputs_dict = self.get_sosdisc_outputs()
        years = np.arange(inputs_dict[GlossaryEnergy.YearStart],
                          inputs_dict[GlossaryEnergy.YearEnd] + 1)
        identity = np.eye(len(years))
        technos_list = inputs_dict[GlossaryEnergy.techno_list]
        list_columns_energyprod = list(
            outputs_dict[GlossaryEnergy.EnergyProductionValue].columns)
        list_columns_consumption = list(
            outputs_dict[GlossaryEnergy.EnergyConsumptionValue].columns)
        mix_weight = outputs_dict['techno_mix']
        scaling_factor_energy_production = inputs_dict['scaling_factor_energy_production']
        scaling_factor_energy_consumption = inputs_dict['scaling_factor_energy_consumption']
        element_list = self.energy_model.subelements_list
        full_element_list = [
            f'{self.energy_model.name} {element} ({self.energy_model.unit})' for element in element_list]
        element_dict = dict(zip(element_list, full_element_list))
        self.grad_techno_mix_vs_prod_dict = self.energy_model.compute_grad_element_mix_vs_prod(
            self.energy_model.production_by_techno, element_dict, exp_min=inputs_dict['exp_min'],
            min_prod=self.energy_model.min_prod)
        for techno in technos_list:
            mix_weight_techno = mix_weight[techno].values / 100.0
            list_columnstechnoprod = list(
                inputs_dict[f'{techno}.{GlossaryEnergy.TechnoProductionValue}'].columns)
            list_columnstechnocons = list(
                inputs_dict[f'{techno}.{GlossaryEnergy.TechnoConsumptionValue}'].columns)
            techno_prod_name_with_unit = [
                tech for tech in list_columnstechnoprod if tech.startswith(self.energy_name)][0]

            for column_name in list_columns_energyprod:

                if column_name != GlossaryEnergy.Years:
                    if column_name == self.energy_name:
                        self.set_partial_derivative_for_other_types(
                            (GlossaryEnergy.EnergyProductionValue, column_name),
                            (f'{techno}.{GlossaryEnergy.TechnoProductionValue}', techno_prod_name_with_unit),
                            inputs_dict['scaling_factor_techno_production'] * np.identity(
                                len(years)) / scaling_factor_energy_production)
                    else:
                        for col_technoprod in list_columnstechnoprod:
                            if column_name == col_technoprod:
                                self.set_partial_derivative_for_other_types(
                                    (GlossaryEnergy.EnergyProductionValue, column_name),
                                    (f'{techno}.{GlossaryEnergy.TechnoProductionValue}', col_technoprod),
                                    inputs_dict['scaling_factor_techno_production'] * np.identity(
                                        len(years)) / scaling_factor_energy_production)

            for column_name in list_columns_consumption:

                if column_name != GlossaryEnergy.Years:
                    if column_name == self.energy_name:
                        self.set_partial_derivative_for_other_types(
                            (GlossaryEnergy.EnergyConsumptionValue, column_name),
                            (f'{techno}.{GlossaryEnergy.TechnoConsumptionValue}', techno_prod_name_with_unit),
                            inputs_dict['scaling_factor_techno_consumption'] * np.identity(
                                len(years)) / scaling_factor_energy_consumption)
                        self.set_partial_derivative_for_other_types(
                            (GlossaryEnergy.EnergyConsumptionWithoutRatioValue, column_name), (
                            f'{techno}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}',
                            techno_prod_name_with_unit), inputs_dict['scaling_factor_techno_consumption'] * np.identity(
                                len(years)) / scaling_factor_energy_consumption)

                    else:
                        # loop on resources
                        for col_technoprod in list_columnstechnocons:
                            if column_name == col_technoprod:
                                self.set_partial_derivative_for_other_types(
                                    (GlossaryEnergy.EnergyConsumptionValue, column_name),
                                    (f'{techno}.{GlossaryEnergy.TechnoConsumptionValue}', col_technoprod),
                                    inputs_dict['scaling_factor_techno_consumption'] * np.identity(
                                        len(years)) / scaling_factor_energy_consumption)
                                self.set_partial_derivative_for_other_types(
                                    (GlossaryEnergy.EnergyConsumptionWithoutRatioValue, column_name),
                                    (f'{techno}.{GlossaryEnergy.TechnoConsumptionWithoutRatioValue}', col_technoprod),
                                    inputs_dict['scaling_factor_techno_consumption'] * np.identity(
                                        len(years)) / scaling_factor_energy_consumption)

            for column_name in list_columnstechnoprod:
                if column_name.startswith(self.energy_name):
                    grad_techno_mix_vs_prod = self.grad_techno_mix_vs_prod_dict[techno]
                    #                     grad_techno_mix_vs_prod = (
                    #                         outputs_dict[GlossaryEnergy.EnergyProductionValue][self.energy_name].values -
                    #                         inputs_dict[f'{techno}.{GlossaryEnergy.TechnoProductionValue}'][column_name].values
                    #                     ) / outputs_dict[GlossaryEnergy.EnergyProductionValue][self.energy_name].values**2

                    # The mix_weight_techno is zero means that the techno is negligible else we do nothing
                    # np.sign gives 0 if zero and 1 if value so it suits well
                    # with our needs
                    grad_techno_mix_vs_prod = grad_techno_mix_vs_prod * \
                                              np.sign(mix_weight_techno)

                    self.set_partial_derivative_for_other_types(
                        ('techno_mix', techno), (f'{techno}.{GlossaryEnergy.TechnoProductionValue}', column_name),
                        inputs_dict['scaling_factor_techno_production'] * np.identity(
                            len(years)) * 100.0 * grad_techno_mix_vs_prod)

                    grad_price_vs_prod = inputs_dict[f'{techno}.{GlossaryEnergy.TechnoPricesValue}'][techno].values * \
                                         grad_techno_mix_vs_prod
                    grad_price_wotaxes_vs_prod = inputs_dict[f'{techno}.{GlossaryEnergy.TechnoPricesValue}'][
                                                     f'{techno}_wotaxes'].values * \
                                                 grad_techno_mix_vs_prod
                    for techno_other in technos_list:
                        if techno_other != techno:
                            mix_weight_techno_other = mix_weight[techno_other].values / 100.0
                            grad_techno_mix_vs_prod = self.grad_techno_mix_vs_prod_dict[
                                f'{techno} {techno_other}']
                            grad_techno_mix_vs_prod = grad_techno_mix_vs_prod * \
                                                      np.sign(mix_weight_techno_other)
                            grad_price_vs_prod += inputs_dict[f'{techno_other}.{GlossaryEnergy.TechnoPricesValue}'][
                                                      techno_other].values * \
                                                  grad_techno_mix_vs_prod
                            grad_price_wotaxes_vs_prod += \
                            inputs_dict[f'{techno_other}.{GlossaryEnergy.TechnoPricesValue}'][
                                f'{techno_other}_wotaxes'].values * grad_techno_mix_vs_prod

                            self.set_partial_derivative_for_other_types(
                                ('techno_mix', techno_other),
                                (f'{techno}.{GlossaryEnergy.TechnoProductionValue}', column_name),
                                inputs_dict['scaling_factor_techno_production'] * np.identity(
                                    len(years)) * 100.0 * grad_techno_mix_vs_prod)

                    self.set_partial_derivative_for_other_types(
                        (GlossaryEnergy.EnergyPricesValue, self.energy_name),
                        (f'{techno}.{GlossaryEnergy.TechnoProductionValue}', column_name),
                        inputs_dict['scaling_factor_techno_production'] * np.identity(len(years)) * grad_price_vs_prod)

                    self.set_partial_derivative_for_other_types(
                        (GlossaryEnergy.EnergyPricesValue, f'{self.energy_name}_wotaxes'),
                        (f'{techno}.{GlossaryEnergy.TechnoProductionValue}', column_name),
                        inputs_dict['scaling_factor_techno_production'] * np.identity(
                            len(years)) * grad_price_wotaxes_vs_prod)

            self.set_partial_derivative_for_other_types(
                (GlossaryEnergy.EnergyPricesValue, self.energy_name),
                (f'{techno}.{GlossaryEnergy.TechnoPricesValue}', techno),
                np.diag(outputs_dict['techno_mix'][techno] / 100.0))

            self.set_partial_derivative_for_other_types(
                (GlossaryEnergy.EnergyPricesValue, f'{self.energy_name}_wotaxes'),
                (f'{techno}.{GlossaryEnergy.TechnoPricesValue}', f'{techno}_wotaxes'),
                np.diag(outputs_dict['techno_mix'][techno] / 100.0))

            self.set_partial_derivative_for_other_types(
                (GlossaryEnergy.LandUseRequiredValue, f'{techno} (Gha)'),
                (f'{techno}.{GlossaryEnergy.LandUseRequiredValue}', f'{techno} (Gha)'), np.identity(len(years)))

        for techno in technos_list:
            self.set_partial_derivative_for_other_types(
                (GlossaryEnergy.EnergyTypeCapitalDfValue, GlossaryEnergy.Capital),
                (f"{techno}.{GlossaryEnergy.TechnoCapitalValue}", GlossaryEnergy.Capital),
                identity,
            )

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['Energy price',
                      'Technology mix',
                      'Consumption and production',
                      GlossaryEnergy.Capital]
        chart_filters.append(ChartFilter(
            'Charts', chart_list, chart_list, 'charts'))

        price_unit_list = ['$/MWh', '$/t']
        chart_filters.append(ChartFilter(
            'Price unit', price_unit_list, price_unit_list, 'price_unit'))

        year_start, year_end = self.get_sosdisc_inputs(
            [GlossaryEnergy.YearStart, GlossaryEnergy.YearEnd])
        years = list(np.arange(year_start, year_end + 1, 5))
        chart_filters.append(ChartFilter(
            'Years for techno mix', years, [year_start, year_end], GlossaryEnergy.Years))
        return chart_filters

    def get_post_processing_list(self, filters=None):

        # For the outputs, making a graph for block fuel vs range and blocktime vs
        # range

        instanciated_charts = []
        charts = []
        price_unit_list = ['$/MWh', '$/t']
        unit = 'TWh'
        years_list = [self.get_sosdisc_inputs(GlossaryEnergy.YearStart)]
        # Overload default value with chart filter
        if filters is not None:
            for chart_filter in filters:
                if chart_filter.filter_key == 'charts':
                    charts = chart_filter.selected_values
                if chart_filter.filter_key == 'price_unit':
                    price_unit_list = chart_filter.selected_values
                if chart_filter.filter_key == GlossaryEnergy.Years:
                    years_list = chart_filter.selected_values

        if 'Energy price' in charts and '$/MWh' in price_unit_list:
            new_chart = self.get_chart_energy_price_in_dollar_kwh()
            if new_chart is not None:
                instanciated_charts.append(new_chart)
        if 'Energy price' in charts and '$/t' in price_unit_list and 'calorific_value' in self.get_sosdisc_inputs(
                'data_fuel_dict'):
            new_chart = self.get_chart_energy_price_in_dollar_kg()
            if new_chart is not None:
                instanciated_charts.append(new_chart)
        if 'Consumption and production' in charts:
            new_charts = self.get_charts_consumption_and_production()
            for new_chart in new_charts:
                if new_chart is not None:
                    instanciated_charts.append(new_chart)
        if 'Technology mix' in charts:
            new_charts = self.get_chart_technology_mix(years_list)
            for new_chart in new_charts:
                if new_chart is not None:
                    instanciated_charts.append(new_chart)
            new_charts = self.get_charts_production_by_techno(unit)
            for new_chart in new_charts:
                if new_chart is not None:
                    instanciated_charts.append(new_chart)

        if GlossaryEnergy.Capital in charts:
            chart = self.get_capital_breakdown_by_technos()
            instanciated_charts.append(chart)
        return instanciated_charts

    def get_chart_energy_price_in_dollar_kwh(self):
        energy_prices = self.get_sosdisc_outputs(GlossaryEnergy.EnergyPricesValue)
        chart_name = f'Detailed prices of {self.energy_name} mix over the years'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'Prices [$/MWh]', chart_name=chart_name)

        serie = InstanciatedSeries(
            energy_prices[GlossaryEnergy.Years].values.tolist(),
            energy_prices[self.energy_name].values.tolist(), f'{self.energy_name} mix price', 'lines')

        new_chart.series.append(serie)

        technology_list = self.get_sosdisc_inputs(GlossaryEnergy.techno_list)

        for technology in technology_list:
            techno_price = self.get_sosdisc_inputs(
                f'{technology}.{GlossaryEnergy.TechnoPricesValue}')
            serie = InstanciatedSeries(
                energy_prices[GlossaryEnergy.Years].values.tolist(),
                techno_price[technology].values.tolist(), f'{technology} price', 'lines')
            new_chart.series.append(serie)

        return new_chart

    def get_chart_energy_price_in_dollar_kg(self):
        energy_prices = self.get_sosdisc_outputs(GlossaryEnergy.EnergyPricesValue)
        chart_name = f'Detailed prices of {self.energy_name} mix over the years'
        new_chart = TwoAxesInstanciatedChart(
            GlossaryEnergy.Years, 'Prices [$/t]', chart_name=chart_name)
        total_price = energy_prices[self.energy_name].values * \
                      self.get_sosdisc_inputs('data_fuel_dict')['calorific_value']
        serie = InstanciatedSeries(
            energy_prices[GlossaryEnergy.Years].values.tolist(),
            total_price.tolist(), f'{self.energy_name} mix price', 'lines')

        new_chart.series.append(serie)

        technology_list = self.get_sosdisc_inputs(GlossaryEnergy.techno_list)

        for technology in technology_list:
            techno_price = self.get_sosdisc_inputs(
                f'{technology}.{GlossaryEnergy.TechnoPricesValue}')
            techno_price_kg = techno_price[technology].values * \
                              self.get_sosdisc_inputs('data_fuel_dict')['calorific_value']
            serie = InstanciatedSeries(
                energy_prices[GlossaryEnergy.Years].values.tolist(),
                techno_price_kg.tolist(), f'{technology}', 'lines')
            new_chart.series.append(serie)

        return new_chart

    def get_charts_consumption_and_production(self):
        instanciated_charts = []
        # Charts for consumption and prod
        energy_consumption = self.get_sosdisc_outputs(GlossaryEnergy.EnergyConsumptionValue)
        energy_production = self.get_sosdisc_outputs(GlossaryEnergy.EnergyProductionValue)
        scaling_factor_energy_consumption = self.get_sosdisc_inputs(
            'scaling_factor_energy_consumption')
        scaling_factor_energy_production = self.get_sosdisc_inputs(
            'scaling_factor_energy_production')
        chart_name = f'{self.energy_name} Production & consumption<br>with input investments'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Energy [TWh]',
                                             chart_name=chart_name, stacked_bar=True)

        for reactant in energy_consumption.columns:
            if reactant != GlossaryEnergy.Years and reactant.endswith('(TWh)'):
                energy_twh = - \
                                 energy_consumption[reactant].values * \
                             scaling_factor_energy_consumption
                legend_title = f'{reactant} consumption'.replace(
                    "(TWh)", "")
                serie = InstanciatedSeries(
                    energy_consumption[GlossaryEnergy.Years].values.tolist(),
                    energy_twh.tolist(), legend_title, 'bar')

                new_chart.series.append(serie)

        for products in energy_production.columns:
            # We do not plot technology H2 production on this graph
            # Pie charts are here to see difference of production between
            # technologies
            if products != GlossaryEnergy.Years and products.endswith('(TWh)') and self.energy_name not in products:
                energy_twh = energy_production[products].values * \
                             scaling_factor_energy_production
                legend_title = f'{products} production'.replace(
                    "(TWh)", "")
                serie = InstanciatedSeries(
                    energy_production[GlossaryEnergy.Years].values.tolist(),
                    energy_twh.tolist(), legend_title, 'bar')

                new_chart.series.append(serie)
        energy_prod_twh = energy_production[self.energy_name].values * \
                          scaling_factor_energy_production
        serie = InstanciatedSeries(
            energy_production[GlossaryEnergy.Years].values.tolist(),
            energy_prod_twh.tolist(), self.energy_name, 'bar')

        new_chart.series.append(serie)
        instanciated_charts.append(new_chart)

        # Check if we have kg in the consumption or prod :

        kg_values_consumption = 0
        reactant_found = ''
        for reactant in energy_consumption.columns:
            if reactant != GlossaryEnergy.Years and reactant.endswith('(Mt)'):
                kg_values_consumption += 1
                reactant_found = reactant

        kg_values_production = 0
        product_found = ''
        for product in energy_production.columns:
            if product != GlossaryEnergy.Years and product.endswith('(Mt)'):
                kg_values_production += 1
                product_found = product
        if kg_values_consumption == 1 and kg_values_production == 0:
            legend_title = f'{reactant_found} consumption'.replace(
                "(Mt)", "")
            chart_name = f'{legend_title} of {self.energy_name} with input investments'
        elif kg_values_production == 1 and kg_values_consumption == 0:
            legend_title = f'{product_found} production'.replace(
                "(Mt)", "")
            chart_name = f'{legend_title} of {self.energy_name} with input investments'
        else:
            chart_name = f'{self.energy_name} mass Production & consumption<br>with input investments'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'Mass [Gt]',
                                             chart_name=chart_name, stacked_bar=True)

        for reactant in energy_consumption.columns:
            if reactant != GlossaryEnergy.Years and reactant.endswith('(Mt)'):
                legend_title = f'{reactant} consumption'.replace(
                    "(Mt)", "")
                mass = -energy_consumption[reactant].values / \
                       1.0e3 * scaling_factor_energy_consumption
                serie = InstanciatedSeries(
                    energy_consumption[GlossaryEnergy.Years].values.tolist(),
                    mass.tolist(), legend_title, 'bar')
                new_chart.series.append(serie)
        for product in energy_production.columns:
            if product != GlossaryEnergy.Years and product.endswith('(Mt)'):
                legend_title = f'{product} production'.replace(
                    "(Mt)", "")
                mass = energy_production[product].values / \
                       1.0e3 * scaling_factor_energy_production
                serie = InstanciatedSeries(
                    energy_production[GlossaryEnergy.Years].values.tolist(),
                    mass.tolist(), legend_title, 'bar')
                new_chart.series.append(serie)

        if kg_values_consumption > 0 or kg_values_production > 0:
            instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_charts_production_by_techno(self, unit):
        instanciated_charts = []
        # Charts for consumption and prod
        energy_production = self.get_sosdisc_outputs(
            GlossaryEnergy.EnergyProductionDetailedValue)

        chart_name = f'Technology production for {self.energy_name}'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, f'Production ({unit})',
                                             chart_name=chart_name, stacked_bar=True)
        techno_list = self.get_sosdisc_inputs(GlossaryEnergy.techno_list)

        for techno in techno_list:
            column_name = f'{self.energy_name} {techno} ({unit})'
            techno_prod = energy_production[column_name].values

            serie = InstanciatedSeries(
                energy_production[GlossaryEnergy.Years].values.tolist(),
                techno_prod.tolist(), techno, 'bar')
            new_chart.series.append(serie)
        instanciated_charts.append(new_chart)

        return instanciated_charts

    def get_chart_technology_mix(self, years_list):
        instanciated_charts = []
        techno_list = self.get_sosdisc_inputs(GlossaryEnergy.techno_list)
        energy_production = self.get_sosdisc_outputs(
            GlossaryEnergy.EnergyProductionDetailedValue)
        techno_production = energy_production[[GlossaryEnergy.Years]]
        display_techno_list = []

        for techno in techno_list:
            if self.energy_name in [GlossaryEnergy.carbon_capture, GlossaryEnergy.carbon_storage]:
                unit = '(Mt)'
            else:
                unit = '(TWh)'
            techno_title = [
                col for col in energy_production if col.endswith(f' {techno} {unit}')]
            techno_production.loc[:,
            techno] = energy_production[techno_title[0]]
            cut_techno_name = techno.split(".")
            display_techno_name = cut_techno_name[len(
                cut_techno_name) - 1].replace("_", " ")
            display_techno_list.append(display_techno_name)

        for year in years_list:
            values = [techno_production.loc[techno_production[GlossaryEnergy.Years]
                                            == year][techno].sum() for techno in techno_list]

            if sum(values) != 0.0:
                pie_chart = InstanciatedPieChart(
                    f'Technology productions in {year}', display_techno_list, values)
                instanciated_charts.append(pie_chart)

        return instanciated_charts

    def get_capital_breakdown_by_technos(self):
        energy_type_capital = self.get_sosdisc_outputs(GlossaryEnergy.EnergyTypeCapitalDfValue)
        techno_list = self.get_sosdisc_inputs(GlossaryEnergy.techno_list)

        years = list(energy_type_capital[GlossaryEnergy.Years].values)
        chart_name = 'Breakdown of capital by technos'

        chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'G$',
                                         chart_name=chart_name, stacked_bar=True)

        for techno in techno_list:
            ordonate_data = list(
                self.get_sosdisc_inputs(f"{techno}.{GlossaryEnergy.TechnoCapitalValue}")[
                    GlossaryEnergy.Capital].values)

            new_series = InstanciatedSeries(
                years, ordonate_data, techno, 'bar', True)

            chart.series.append(new_series)

        new_series = InstanciatedSeries(
            years, list(energy_type_capital[GlossaryEnergy.Capital].values), 'Total', 'lines', True)

        chart.series.append(new_series)

        return chart
