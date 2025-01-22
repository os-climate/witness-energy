'''
Copyright 2022 Airbus SAS
Modifications on 23/11/2023 Copyright 2023 Capgemini

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

from energy_models.core.stream_type.carbon_models.carbon_monoxyde import CO
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import (
    GaseousHydrogen,
)
from energy_models.core.stream_type.energy_type import EnergyType
from energy_models.glossaryenergy import GlossaryEnergy


class Syngas(EnergyType):
    name = GlossaryEnergy.syngas
    default_techno_list = [GlossaryEnergy.Pyrolysis, GlossaryEnergy.SMR, GlossaryEnergy.AutothermalReforming,
                           GlossaryEnergy.CoElectrolysis, GlossaryEnergy.BiomassGasification, GlossaryEnergy.CoalGasification]
    data_energy_dict = {
        'maturity': 10,
        'WACC': 0.1,
        # Gu, H. and Bergman, R., 2015.
        # Life-cycle GHG emissions of electricity from syngas produced by pyrolyzing woody biomass.
        # In Proceedings of the 58th International Convention of Society of Wood Science and Technology
        # June 7-12, 2015 Jackson Lake Lodge, Grand Teton National Park,
        # Wyoming, USA, pp. 376-389. (pp. 376-389).
        GlossaryEnergy.CO2PerUse: 2.38 * 0.095,
        'CO2_per_use_unit': 'kg/kg',
        'NOx_per_energy': 0.0,
        'NOX_per_energy_unit': 'mg/kg',
        # 'density': (2 / 71 + 28 / 1.14) / 30,
        'density_unit': 'kg/m^3',
        # 'molar_mass': 30,
        'molar_mass_unit': 'g/mol',
        # (considering 1 mol of H2 : 33.3 * 2/30 and 1 mol of CO 11.79 * 28/30)
        # 'calorific_value': 13.22,
        'calorific_value_unit': 'kWh/kg',
        # 'high_calorific_value': 13.22,
        'high_calorific_value_unit': 'kWh/kg',
    }

    def __init__(self, name):
        self.syngas_ratio_mean = None
        self.syngas_ratio = {}
        EnergyType.__init__(self, name)

    def configure_parameters(self, inputs_dict):
        EnergyType.configure_parameters(self, inputs_dict)

    def configure_parameters_update(self, inputs_dict):
        EnergyType.configure_parameters_update(self, inputs_dict)
        for techno in self.subelements_list:
            self.syngas_ratio[techno] = inputs_dict[f'{techno}.syngas_ratio'][0]
        # Added to overwrite the definition of data energy dict input from energy type but with a deepcopy
        self.data_energy_dict_input = deepcopy(inputs_dict['data_fuel_dict'])

    def compute_syngas_ratio(self):
        """
        Method to compute syngas ratio using production by 
        """
        self.syngas_ratio_mean = self.zeros_array
        for techno in self.subelements_list:
            #             self.mix_weights[techno] = self.production_by_techno[f'{self.name} {techno} ({GlossaryEnergy.energy_unit})'] / \
            #                 self.production[f'{self.name}']
            self.syngas_ratio_mean = np.add(self.syngas_ratio_mean, self.syngas_ratio[techno] *
                                            self.mix_weights[techno].values / 100.0)
        return self.syngas_ratio_mean


def compute_molar_mass(syngas_ratio):
    '''
    syngas ratio is the molar ratio of CO over H2 
    We compute the molar mass following this ratio 
    if ratio is equal to zero syngas is h2
    syngas_ratio must be between 0 and 1 (not in %)
    '''
    molar_mass = (syngas_ratio * CO.data_energy_dict['molar_mass'] +
                  GaseousHydrogen.data_energy_dict['molar_mass']) / (1.0 + syngas_ratio)
    return molar_mass


def compute_calorific_value(syngas_ratio):
    '''
    syngas ratio is the molar ratio of CO over H2 
    We compute the calorific_value following this ratio 
    Ratio is on mol not kg !! So we need molar_mass ratio in the computation
    if ratio is equal to zero syngas is h2
    syngas_ratio must be between 0 and 1 (not in %)
    '''
    calorific_value = (syngas_ratio * CO.data_energy_dict['molar_mass'] * CO.data_energy_dict['calorific_value'] +
                       GaseousHydrogen.data_energy_dict['molar_mass'] * GaseousHydrogen.data_energy_dict[
                           'calorific_value']) / (
                                  GaseousHydrogen.data_energy_dict['molar_mass'] + syngas_ratio * CO.data_energy_dict[
                              'molar_mass'])

    return calorific_value


def compute_high_calorific_value(syngas_ratio):
    '''
    syngas ratio is the molar ratio of CO over H2 
    We compute the calorific_value following this ratio 
    Ratio is on mol not kg !! So we need molar_mass ratio in the computation
    if ratio is equal to zero syngas is h2
    syngas_ratio must be between 0 and 1 (not in %)
    '''
    calorific_value = (syngas_ratio * CO.data_energy_dict['molar_mass'] * CO.data_energy_dict['high_calorific_value'] +
                       GaseousHydrogen.data_energy_dict['molar_mass'] * GaseousHydrogen.data_energy_dict[
                           'high_calorific_value']) / (
                                  GaseousHydrogen.data_energy_dict['molar_mass'] + syngas_ratio * CO.data_energy_dict[
                              'molar_mass'])

    return calorific_value


def compute_dcal_val_dsyngas_ratio(syngas_ratio, type_cal='calorific_value'):
    calup = (syngas_ratio * CO.data_energy_dict['molar_mass'] * CO.data_energy_dict[type_cal] +
             GaseousHydrogen.data_energy_dict['molar_mass'] * GaseousHydrogen.data_energy_dict[type_cal])

    caldown = (GaseousHydrogen.data_energy_dict['molar_mass'] +
               syngas_ratio * CO.data_energy_dict['molar_mass'])

    dcalup = CO.data_energy_dict['molar_mass'] * \
             CO.data_energy_dict[type_cal]

    dcaldown = CO.data_energy_dict['molar_mass']

    dcalorific_val_dsyngas = (
                                     dcalup * caldown - dcaldown * calup) / (caldown ** 2)

    return dcalorific_val_dsyngas


def compute_density(syngas_ratio):
    '''
    syngas ratio is the molar ratio of CO over H2 
    We compute the density following this ratio 
    Ratio is on mol not kg !! So we need molar_mass ratio in the computation
    if ratio is equal to zero syngas is h2
    '''
    density = (syngas_ratio * CO.data_energy_dict['molar_mass'] * CO.data_energy_dict['density'] +
               GaseousHydrogen.data_energy_dict['molar_mass'] * CO.data_energy_dict['density']) / (
                          GaseousHydrogen.data_energy_dict['molar_mass'] + syngas_ratio * CO.data_energy_dict[
                      'molar_mass'])

    return density
