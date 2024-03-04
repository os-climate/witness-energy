'''
Copyright 2024 Capgemini

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

from energy_models.core.stream_type.base_stream import BaseStream
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.core.stream_type.carbon_models.carbon_storage import CarbonStorage
from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from energy_models.core.stream_type.energy_models.heat import lowtemperatureheat
from energy_models.core.stream_type.energy_models.heat import mediumtemperatureheat
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import GaseousHydrogen

class HeatMix(BaseStream):
    """
    Class Energy mix
    """
    name = 'HeatMix'
    energy_class_dict = {
                         lowtemperatureheat.name: lowtemperatureheat,
                         mediumtemperatureheat.name: mediumtemperatureheat,
                         hightemperatureheat.name: hightemperatureheat,
                         }

    lowtemperatureheat_name = lowtemperatureheat.name
    mediumtemperatureheat_name = mediumtemperatureheat.name
    hightemperatureheat_name = hightemperatureheat.name

    energy_constraint_list = [lowtemperatureheat_name, mediumtemperatureheat_name,
                              hightemperatureheat_name]

    only_energy_list = list(energy_class_dict.keys())
    energy_list = list(energy_class_dict.keys())

    def __init__(self, name):
        '''
        Constructor
        '''
        super(HeatMix, self).__init__(name)

        self.total_co2_emissions = None
        self.total_co2_emissions_Gt = None
        self.inputs = {}

    def compute(self, inputs_dict: dict, exp_min=True):

        energy_CO2_emission = self.compute_CO2_emissions(inputs_dict)

        energy_CO2_emission_objective = self.compute_energy_CO2_emission_objective(energy_CO2_emission)

        total_heat_production = self.compute_total_production(inputs_dict)
        total_energy_heat_production_constraint = self.compute_target_heat_production_constraint(total_heat_production, inputs_dict)

        return energy_CO2_emission, energy_CO2_emission_objective, \
            total_heat_production, total_energy_heat_production_constraint


    def compute_target_heat_production_constraint(self, total_heat_production, inputs_dict):

        total_heat_production_constraint = total_heat_production[GlossaryEnergy.EnergyProductionValue].values \
                                           - inputs_dict[GlossaryEnergy.TargetHeatProductionValue][GlossaryEnergy.TargetHeatProductionValue].values

        return total_heat_production_constraint

    def compute_total_production(self, inputs_dict: dict):
        total_heat_production = pd.DataFrame({GlossaryEnergy.Years:
                                                       inputs_dict[GlossaryEnergy.TargetHeatProductionValue][GlossaryEnergy.Years]})
        total_heat_production[GlossaryEnergy.EnergyProductionValue] = 0
        for energy in inputs_dict[GlossaryEnergy.energy_list]:
            columns_to_sum = [column for column in inputs_dict[f'{energy}.{GlossaryEnergy.EnergyProductionValue}']
                              if not column.endswith(GlossaryEnergy.Years)]

            total_heat_production[GlossaryEnergy.EnergyProductionValue] = \
                total_heat_production[GlossaryEnergy.EnergyProductionValue] + inputs_dict[f'{energy}.{GlossaryEnergy.EnergyProductionValue}'][columns_to_sum].sum(axis=1)


        return total_heat_production

    def compute_CO2_emissions(self, inputs_dict: dict):

        self.compute_distribution_list(inputs_dict)
        techno_CO2_emission = inputs_dict['CO2_emission_mix'][self.distribution_list]

        self.methane_energy_List = [f'heat.hightemperatureheat.{Methane.name}',
                        f'heat.mediumtemperatureheat.{Methane.name}',
                        f'heat.lowtemperatureheat.{Methane.name}']
        self.electricity_energy_List = [ f'heat.hightemperatureheat.{Electricity.name}',
                        f'heat.mediumtemperatureheat.{Electricity.name}',
                        f'heat.lowtemperatureheat.{Electricity.name}']
        self.gaseous_hydrogen_energy_List = [f'heat.hightemperatureheat.{GaseousHydrogen.name}',
                        f'heat.mediumtemperatureheat.{GaseousHydrogen.name}',
                        f'heat.lowtemperatureheat.{GaseousHydrogen.name}']

        # CO2_emission_mix_columns = [column for column in inputs_dict['CO2_emission_mix']
        #                   if not column.endswith(GlossaryEnergy.Years)]
        #
        # result = list(set(CO2_emission_mix_columns) - set(self.distribution_list))
        # print('')
        # print(result)

        methane_CO2_emission = inputs_dict['CO2_emission_mix'][self.methane_energy_List]
        electricity_CO2_emission = inputs_dict['CO2_emission_mix'][self.electricity_energy_List]
        gaseous_hydrogen_CO2_emission = inputs_dict['CO2_emission_mix'][self.gaseous_hydrogen_energy_List]

        # print(techno_CO2_emission.to_string())
        techno_CO2_emission_sum = techno_CO2_emission.sum(axis=1).values
        methane_CO2_emission_sum = methane_CO2_emission.sum(axis=1).values
        electricity_CO2_emission_sum = electricity_CO2_emission.sum(axis=1).values
        gaseous_hydrogen_CO2_emission_sum = gaseous_hydrogen_CO2_emission.sum(axis=1).values

        energy_CO2_emission = pd.DataFrame(
            {GlossaryEnergy.Years: inputs_dict['CO2_emission_mix'][GlossaryEnergy.Years],
             GlossaryEnergy.EnergyCO2EmissionsValue: techno_CO2_emission_sum,
             Methane.name: methane_CO2_emission_sum,
             Electricity.name: electricity_CO2_emission_sum,
             GaseousHydrogen.name: gaseous_hydrogen_CO2_emission_sum,
             })

        # print(energy_CO2_emission.to_string())
        return energy_CO2_emission

    def compute_energy_CO2_emission_objective(self, energy_CO2_emission):
        '''
        Compute the CO2 emission_ratio in kgCO2/kWh for the MDA
        '''

        energy_CO2_emission_objective = energy_CO2_emission[GlossaryEnergy.EnergyCO2EmissionsValue].values.sum()

        return np.array([energy_CO2_emission_objective])
    def compute_distribution_list(self, input_dict):
        self.distribution_list = []
        for energy in input_dict[GlossaryEnergy.energy_list]:
            for techno in input_dict[f'{energy}.{GlossaryEnergy.techno_list}']:
                self.distribution_list.append(f'{energy}.{techno}')
        # self.distribution_list.append(Methane.name)
