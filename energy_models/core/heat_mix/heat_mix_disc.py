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

from climateeconomics.core.core_witness.climateeco_discipline import ClimateEcoDiscipline
from energy_models.core.heat_mix.heat_mix import HeatMix
from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from energy_models.core.stream_type.energy_models.heat import lowtemperatureheat
from energy_models.core.stream_type.energy_models.heat import mediumtemperatureheat
from energy_models.glossaryenergy import GlossaryEnergy
from sostrades_core.execution_engine.sos_wrapp import SoSWrapp


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
               'CO2_emission_mix': {'type': 'dataframe', 'unit': 'G$',
                                           'dataframe_edition_locked': False,
                                           'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                                    'heat.hightemperatureheat.NaturalGasBoilerHighHeat': (
                                                                        'float', None, True),
                                                                    'heat.hightemperatureheat.ElectricBoilerHighHeat': (
                                                                        'float', None, True),
                                                                    'heat.hightemperatureheat.HeatPumpHighHeat': (
                                                                        'float', None, True),
                                                                    'heat.hightemperatureheat.GeothermalHighHeat': (
                                                                        'float', None, True),
                                                                    'heat.hightemperatureheat.CHPHighHeat': (
                                                                        'float', None, True),
                                                                    'heat.hightemperatureheat.HydrogenBoilerHighHeat': (
                                                                        'float', None, True),
                                                                    'heat.lowtemperatureheat.NaturalGasBoilerLowHeat': (
                                                                        'float', None, True),
                                                                    'heat.lowtemperatureheat.ElectricBoilerLowHeat': (
                                                                        'float', None, True),
                                                                    'heat.lowtemperatureheat.HeatPumpLowHeat': (
                                                                        'float', None, True),
                                                                    'heat.lowtemperatureheat.GeothermalLowHeat': (
                                                                        'float', None, True),
                                                                    'heat.lowtemperatureheat.CHPLowHeat': (
                                                                        'float', None, True),
                                                                    'heat.lowtemperatureheat.HydrogenBoilerLowHeat': (
                                                                        'float', None, True),
                                                                    'heat.mediumtemperatureheat.NaturalGasBoilerMediumHeat': (
                                                                        'float', None, True),
                                                                    'heat.mediumtemperatureheat.ElectricBoilerMediumHeat': (
                                                                        'float', None, True),
                                                                    'heat.mediumtemperatureheat.HeatPumpMediumHeat': (
                                                                        'float', None, True),
                                                                    'heat.mediumtemperatureheat.GeothermalMediumHeat': (
                                                                        'float', None, True),
                                                                    'heat.mediumtemperatureheat.CHPMediumHeat': (
                                                                        'float', None, True),
                                                                    'heat.mediumtemperatureheat.HydrogenBoilerMediumHeat': (
                                                                        'float', None, True),
                                                                    }},
               }

    DESC_OUT = {
        GlossaryEnergy.EnergyCO2EmissionsValue: {'type': 'dataframe', 'unit': 'kg/kWh'},
        'CO2MinimizationObjective': {'type': 'array', 'unit': '-',
            'visibility': SoSWrapp.SHARED_VISIBILITY,
            'namespace':GlossaryEnergy.NS_FUNCTIONS
                                    },
                }

    energy_name = HeatMix.name
    energy_class_dict = HeatMix.energy_class_dict
    LowTemperatureHeat_name = lowtemperatureheat.name
    MediumTemperatureHeat_name = mediumtemperatureheat.name
    HighTemperatureHeat_name = hightemperatureheat.name

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.energy_model = HeatMix(self.energy_name)
        # self.energy_model.configure_parameters(inputs_dict)

    def setup_sos_disciplines(self):

        dynamic_inputs = {}
        dynamic_outputs = {}
        inputs_dict = self.get_sosdisc_inputs()
        if GlossaryEnergy.energy_list in self.get_data_in():
            energy_list = inputs_dict[GlossaryEnergy.energy_list]
            # self.update_default_energy_list()
            if energy_list is not None:
                for energy in energy_list:
                    # ns_energy = self.get_ns_energy(energy)

                    dynamic_inputs[f'{energy}.{GlossaryEnergy.techno_list}'] = {
                        'type': 'list', 'subtype_descriptor': {'list': 'string'}, 'structuring': True,
                        'visibility': 'Shared', 'namespace': 'ns_energy',
                        'possible_values': self.energy_class_dict[energy].default_techno_list,
                        'default': self.energy_class_dict[energy].default_techno_list}

                    if f'{energy}.{GlossaryEnergy.techno_list}' in self.get_data_in():
                        technology_list = self.get_sosdisc_inputs(
                            f'{energy}.{GlossaryEnergy.techno_list}')
                        if technology_list is not None:
                            for techno in technology_list:
                                dynamic_outputs[f'{energy}.{techno}.{GlossaryEnergy.CO2EmissionsValue}'] = {
                                    'type': 'dataframe', 'unit': 'kg/kWh',
                                    'visibility': 'Shared', 'namespace': 'ns_energy'}


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


    def run(self):
        # -- get inputs

        input_dict = self.get_sosdisc_inputs()

        self.energy_model.compute(input_dict)

        energyCO2emissionsvalue, CO2MinimizationObjective = self.energy_model.compute(input_dict)

        output_dict = {GlossaryEnergy.EnergyCO2EmissionsValue: energyCO2emissionsvalue,
                       'CO2MinimizationObjective': CO2MinimizationObjective, }

        for energy in input_dict[GlossaryEnergy.energy_list]:
            for techno in input_dict[f'{energy}.{GlossaryEnergy.techno_list}']:
                output_dict[f'{energy}.{techno}.{GlossaryEnergy.CO2EmissionsValue}'] = pd.DataFrame(
                    {GlossaryEnergy.Years: input_dict['CO2_emission_mix'][GlossaryEnergy.Years].values,
                     GlossaryEnergy.CO2EmissionsValue: input_dict['CO2_emission_mix'][
                         f'{energy}.{techno}'].values})

        self.store_sos_outputs_values(output_dict)


    def get_ns_energy(self, energy):
        '''
        Returns the namespace of the energy
        In case  of biomass , it is computed in agriculture model

        '''

        ns_energy = energy

        return ns_energy

    def compute_sos_jacobian(self):
        inputs_dict = self.get_sosdisc_inputs()

        years = np.arange(inputs_dict[GlossaryEnergy.YearStart],
                          inputs_dict[GlossaryEnergy.YearEnd] + 1)

        delta_years = len(years)
        identity = np.identity(delta_years)
        ones = np.ones(delta_years)

        for techno in self.energy_model.distribution_list:
            self.set_partial_derivative_for_other_types(
                (GlossaryEnergy.EnergyCO2EmissionsValue, GlossaryEnergy.EnergyCO2EmissionsValue),
                ('CO2_emission_mix', techno), identity) #,identity * 1e-3

            self.set_partial_derivative_for_other_types(
                ('CO2MinimizationObjective',),
                ('CO2_emission_mix', techno), ones) #* 1e-3

