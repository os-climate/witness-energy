'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/15-2023/11/07 Copyright 2023 Capgemini

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

from climateeconomics.glossarycore import GlossaryCore
from energy_models.core.stream_type.energy_disc import EnergyDiscipline
from energy_models.core.stream_type.energy_models.syngas import Syngas, \
    compute_calorific_value, compute_molar_mass, compute_high_calorific_value, compute_dcal_val_dsyngas_ratio
from energy_models.glossaryenergy import GlossaryEnergy
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart
from energy_models.core.stream_type.stream_disc import StreamDiscipline
from copy import deepcopy


class SyngasDiscipline(EnergyDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Syngas Energy Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-burn fa-fw',
        'version': '',
    }

    DESC_IN = {GlossaryCore.techno_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                                     'possible_values': Syngas.default_techno_list,
                                     'default': Syngas.default_techno_list,
                                     'visibility': EnergyDiscipline.SHARED_VISIBILITY,
                                     'namespace': 'ns_syngas', 'structuring': True,
                                     'unit': '-'},

               'data_fuel_dict': {'type': 'dict',
                                  'visibility': EnergyDiscipline.SHARED_VISIBILITY,
                                  'namespace': 'ns_syngas',
                                  'default': Syngas.data_energy_dict,
                                  'unit': 'defined in dict'},
               }
    DESC_IN.update(EnergyDiscipline.DESC_IN)

    energy_name = Syngas.name

    DESC_OUT = {'syngas_ratio': {'type': 'array', 'unit': '%',
                                 'visibility': EnergyDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_syngas'},
                'syngas_ratio_technos': {'type': 'dict', 'unit': '%', 'subtype_descriptor': {'dict': 'float'},
                                         'visibility': EnergyDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_syngas'},
                }

    # -- add specific techno outputs to this
    DESC_OUT.update(EnergyDiscipline.DESC_OUT)

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.energy_model = Syngas(self.energy_name)
        self.energy_model.configure_parameters(inputs_dict)

    def setup_sos_disciplines(self):
        dynamic_inputs = {}

        if GlossaryCore.techno_list in self.get_data_in():
            techno_list = self.get_sosdisc_inputs(GlossaryCore.techno_list)
            self.update_default_technology_list()
            if techno_list is not None:
                for techno in techno_list:
                    dynamic_inputs[f'{techno}.{GlossaryCore.TechnoConsumptionValue}'] = {
                        'type': 'dataframe', 'unit': 'TWh or Mt',
                        "dynamic_dataframe_columns": True}
                    dynamic_inputs[f'{techno}.{GlossaryCore.TechnoConsumptionWithoutRatioValue}'] = {
                        'type': 'dataframe', 'unit': 'TWh or Mt',
                        "dynamic_dataframe_columns": True}
                    dynamic_inputs[f'{techno}.{GlossaryCore.TechnoProductionValue}'] = {
                        'type': 'dataframe', 'unit': 'TWh or Mt',
                        "dynamic_dataframe_columns": True}
                    dynamic_inputs[f'{techno}.{GlossaryCore.TechnoPricesValue}'] = {
                        'type': 'dataframe', 'unit': '$/MWh',
                        "dynamic_dataframe_columns": True}
                    dynamic_inputs[f'{techno}.{GlossaryCore.CO2EmissionsValue}'] = {
                        'type': 'dataframe', 'unit': 'kg/kWh',
                        "dynamic_dataframe_columns": True}
                    dynamic_inputs[f'{techno}.syngas_ratio'] = {
                        'type': 'array', 'unit': '%'}
                    dynamic_inputs[f'{techno}.{GlossaryCore.LandUseRequiredValue}'] = {
                        'type': 'dataframe', 'unit': 'Gha',
                        "dynamic_dataframe_columns": True}
                    dynamic_inputs[f'{techno}.{GlossaryEnergy.TechnoCapitalDfValue}'] =\
                        GlossaryCore.get_dynamic_variable(GlossaryEnergy.TechnoCapitalDf)

        self.add_inputs(dynamic_inputs)

    def run(self):
        '''
        Overload EnergyDiscipline run
        '''

        StreamDiscipline.run(self)

        # -- get inputs
        syngas_ratio = self.energy_model.compute_syngas_ratio()

        CO2_emissions = self.energy_model.compute_carbon_emissions()

        data_energy_dict = self.compute_data_energy_dict()
        self.energy_model.data_energy_dict_input.update(data_energy_dict)
        ghg_per_use_dict = self.energy_model.compute_ghg_emissions_per_use()

        outputs_dict = {GlossaryCore.CO2EmissionsValue: CO2_emissions,
                        'syngas_ratio': syngas_ratio,
                        'syngas_ratio_technos': self.energy_model.syngas_ratio}
        outputs_dict.update(ghg_per_use_dict)
        # -- store outputs
        self.store_sos_outputs_values(outputs_dict)

    def compute_data_energy_dict(self):

        data_energy_dict = {}
        data_fuel_dict = deepcopy(self.get_sosdisc_inputs('data_fuel_dict'))
        for key, value in data_fuel_dict.items():
            data_energy_dict[key] = value

        data_energy_dict['molar_mass'] = compute_molar_mass(
            self.energy_model.syngas_ratio_mean / 100.0)
        data_energy_dict['high_calorific_value'] = compute_high_calorific_value(
            self.energy_model.syngas_ratio_mean / 100.0)
        data_energy_dict['calorific_value'] = compute_calorific_value(
            self.energy_model.syngas_ratio_mean / 100.0)

        return data_energy_dict

    def compute_sos_jacobian(self):
        """

        """
        EnergyDiscipline.compute_sos_jacobian(self)

        inputs_dict = self.get_sosdisc_inputs()
        outputs_dict = self.get_sosdisc_outputs()

        years = np.arange(inputs_dict[GlossaryCore.YearStart],
                          inputs_dict[GlossaryCore.YearEnd] + 1)
        technos_list = inputs_dict[GlossaryCore.techno_list]
        list_columns_energyprod = list(
            outputs_dict[GlossaryCore.EnergyProductionValue].columns)
        mix_weight = outputs_dict['techno_mix']
        for techno in technos_list:
            mix_weight_techno = mix_weight[techno].values / 100.0
            # The mix_weight_techno is zero means that the techno is negligible else we do nothing
            # np.sign gives 0 if zero and 1 if value so it suits well
            # with our needs
            grad_techno_mix_vs_prod = self.grad_techno_mix_vs_prod_dict[techno] * np.sign(
                mix_weight_techno)
            grad_syngas_prod = np.array(
                inputs_dict[f'{techno}.syngas_ratio']) * grad_techno_mix_vs_prod

            for techno_other in inputs_dict[GlossaryCore.techno_list]:
                if techno != techno_other:
                    mix_weight_techno_other = mix_weight[techno_other].values / 100.0
                    grad_techno_mix_vs_prod = self.grad_techno_mix_vs_prod_dict[f'{techno} {techno_other}'] * np.sign(
                        mix_weight_techno_other)
                    grad_syngas_prod += \
                        np.array(
                            inputs_dict[f'{techno_other}.syngas_ratio']) * grad_techno_mix_vs_prod

            self.set_partial_derivative_for_other_types(
                ('syngas_ratio',),
                (f'{techno}.{GlossaryCore.TechnoProductionValue}', f'{self.energy_name} (TWh)'),
                inputs_dict['scaling_factor_techno_production'] * np.identity(len(years)) * grad_syngas_prod)
            self.set_partial_derivative(
                'syngas_ratio',
                f'{techno}.syngas_ratio',
                np.atleast_2d(mix_weight_techno).T)

            # ctax_use = c_tax_use (kg/kg)/high_calorific_value
            # ctax_use = C/f(sg(x)) with x equals to prod or synags_ratio by techno
            # dctaxuse/dx = -C(f(sg(x))'/f(sg(x))**2 =
            # -c*sg'*f'(sg(x))/f(sg(x))**2
            # -sg'*f'(sg(x))*ctax_use**2/C

            fprimesgx = compute_dcal_val_dsyngas_ratio(
                outputs_dict['syngas_ratio'] / 100.0, type_cal='high_calorific_value')

            co2_per_use = deepcopy(self.get_sosdisc_inputs(
                'data_fuel_dict')['CO2_per_use'])
            if co2_per_use != 0:
                grad_carbon_tax_vs_prod = -grad_syngas_prod * fprimesgx * \
                                          outputs_dict['CO2_per_use']['CO2_per_use'].values ** 2 / \
                                          co2_per_use / 100.0
            else:
                grad_carbon_tax_vs_prod = [0] * len(grad_syngas_prod)

            self.set_partial_derivative_for_other_types(
                ('CO2_per_use', 'CO2_per_use'),
                (f'{techno}.{GlossaryCore.TechnoProductionValue}', f'{self.energy_name} (TWh)'),
                inputs_dict['scaling_factor_techno_production'] * np.identity(len(years)) * grad_carbon_tax_vs_prod)

            if co2_per_use != 0:
                grad_carbon_tax_vs_syngas_ratio = -mix_weight_techno * fprimesgx * \
                                                  outputs_dict['CO2_per_use']['CO2_per_use'].values ** 2 / \
                                                  co2_per_use / 100.0
            else:
                grad_carbon_tax_vs_syngas_ratio = [0] * len(mix_weight_techno)
            self.set_partial_derivative_for_other_types(
                ('CO2_per_use', 'CO2_per_use'),
                (f'{techno}.syngas_ratio',),
                np.atleast_2d(grad_carbon_tax_vs_syngas_ratio).T)

    def get_post_processing_list(self, filters=None):

        generic_filter = EnergyDiscipline.get_chart_filter_list(self)
        instanciated_charts = EnergyDiscipline.get_post_processing_list(
            self, generic_filter)

        year_start, year_end = self.get_sosdisc_inputs(
            [GlossaryCore.YearStart, GlossaryCore.YearEnd])
        years = np.arange(year_start, year_end + 1)
        syngas_ratio = self.get_sosdisc_outputs(
            'syngas_ratio')
        syngas_ratio_technos = self.get_sosdisc_outputs(
            'syngas_ratio_technos')
        chart_name = f'Molar syngas CO over H2 ratio for the global mix'

        new_chart = TwoAxesInstanciatedChart(GlossaryCore.Years, 'CO over H2 molar ratio', [], [],
                                             chart_name=chart_name)

        for techno in syngas_ratio_technos:
            serie = InstanciatedSeries(
                years.tolist(),
                [syngas_ratio_technos[techno]] * len(years), techno, 'lines')

            new_chart.series.append(serie)

        serie = InstanciatedSeries(
            years.tolist(),
            syngas_ratio.tolist(), 'syngas mix', 'lines')

        new_chart.series.append(serie)

        instanciated_charts.append(new_chart)
        return instanciated_charts
