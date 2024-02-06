'''
Copyright 2022 Airbus SAS
Modifications on 2023/05/31-2023/11/16 Copyright 2023 Capgemini

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

        return energy_CO2_emission, energy_CO2_emission_objective




    def compute_CO2_emissions(self, inputs_dict: dict):

        self.compute_distribution_list(inputs_dict)
        techno_CO2_emission = inputs_dict['CO2_emission_mix'][self.distribution_list]
        techno_CO2_emission_sum = techno_CO2_emission.sum(axis=1).values

        energy_CO2_emission = pd.DataFrame(
            {GlossaryEnergy.Years: inputs_dict['CO2_emission_mix'][GlossaryEnergy.Years],
             GlossaryEnergy.EnergyCO2EmissionsValue: techno_CO2_emission_sum})
        return energy_CO2_emission

    def compute_energy_CO2_emission_objective(self, energy_CO2_emission):
        '''
        Compute the CO2 emission_ratio in kgCO2/kWh for the MDA
        '''

        energy_CO2_emission_objective = energy_CO2_emission[GlossaryEnergy.EnergyCO2EmissionsValue].values.sum()
        return energy_CO2_emission_objective


    def compute_grad_CO2_emissions(self):
        '''
        Compute CO2 total emissions
        '''
        # Initialize dataframes
        len_years = len(self.production[GlossaryEnergy.Years])

        co2_production = pd.DataFrame({GlossaryEnergy.Years: self.production[GlossaryEnergy.Years]})
        co2_consumption = pd.DataFrame(
            {GlossaryEnergy.Years: self.production[GlossaryEnergy.Years]})

        dtot_CO2_emissions = {}
        # Do not loop over carbon capture and carbon storage which will be
        # handled differently
        for energy in self.subelements_list:
            if energy in self.energy_list:

                # gather all production columns with a CO2 name in it
                for col, production in self.sub_production_dict[energy].items():
                    if col in self.CO2_list:
                        co2_production[f'{energy} {col}'] = production.values
                # gather all consumption columns with a CO2 name in it
                for col, consumption in self.sub_consumption_dict[energy].items():
                    if col in self.CO2_list:
                        co2_consumption[f'{energy} {col}'] = consumption.values

        #                 # Compute the CO2 emitted during the use of the net energy
        #                 # If net energy is negative, CO2 by use is equals to zero
        #                 net_prod = net_production[
        #                     f'production {energy} ({self.energy_class_dict[energy].unit})'].values
        #
        #                 dtot_CO2_emissions[f'Total CO2 by use (Mt) vs {energy}#co2_per_use'] = np.maximum(
        #                     0, net_prod)
        #
        #                 # Specific case when net prod is equal to zero
        #                 # if we increase the prod of an energy the net prod will react
        #                 # however if we decrease the cons it does nothing
        #                 net_prod_sign = net_prod.copy()
        #                 net_prod_sign[net_prod_sign == 0] = 1
        #                 dtot_CO2_emissions[f'Total CO2 by use (Mt) vs {energy}#prod'] = self.co2_per_use[energy]['CO2_per_use'].values * \
        #                     np.maximum(0, np.sign(net_prod_sign))
        #                 dtot_CO2_emissions[f'Total CO2 by use (Mt) vs {energy}#cons'] = - self.co2_per_use[energy]['CO2_per_use'].values * \
        #                     np.maximum(0, np.sign(net_prod))
        # #                         co2_production[f'{energy} CO2 by use (Mt)'] = self.stream_class_dict[energy].data_energy_dict['CO2_per_use'] / \
        # #                             high_calorific_value * np.maximum(
        # 0.0, self.production[f'production {energy}
        # ({self.energy_class_dict[energy].unit})'].values)

        ''' CARBON STORAGE 
         Total carbon storage is production of carbon storage
         Solid carbon is gaseous equivalent in the production for
         solidcarbonstorage technology
        '''
        if CarbonStorage.name in self.sub_production_dict:
            dtot_CO2_emissions[
                f'{CarbonStorage.name} (Mt) vs {CarbonStorage.name}#{CarbonStorage.name}#prod'] = np.ones(
                len_years)
        #             self.total_co2_emissions[f'{CarbonStorage.name} (Mt)'] = self.sub_production_dict[
        #                 CarbonStorage.name][CarbonStorage.name].values
        #         else:
        #             self.total_co2_emissions[f'{CarbonStorage.name} (Mt)'] = 0.0

        ''' CARBON CAPTURE from CC technos       
         Total carbon capture = carbon captured from carboncapture stream +
         carbon captured from energies (can be negative if FischerTropsch needs carbon
         captured)
        '''
        if CarbonCapture.name in self.sub_production_dict:
            dtot_CO2_emissions[
                f'{CarbonCapture.name} (Mt) from CC technos vs {CarbonCapture.name}#{CarbonCapture.name}#prod'] = np.ones(
                len_years)
        #             self.total_co2_emissions[f'{CarbonCapture.name} (Mt) from CC technos'] = self.sub_production_dict[
        #                 CarbonCapture.name][CarbonCapture.name].values
        #         else:
        #             self.total_co2_emissions[f'{CarbonCapture.name} (Mt) from CC technos'] = 0.0

        ''' CARBON CAPTURE from energy mix
        Total carbon capture from energy mix if the technology offers carbon_capture
         Ex : upgrading biogas technology is the same as Amine Scrubbing but
         on a different gas (biogas for upgrading biogas and flue gas for
         Amien scrubbing)
        '''
        energy_producing_carbon_capture = co2_production[[
            col for col in co2_production if col.endswith(f'{CarbonCapture.name} (Mt)')]]
        energy_producing_carbon_capture_list = [key.replace(
            f' {CarbonCapture.name} (Mt)', '') for key in energy_producing_carbon_capture]
        if len(energy_producing_carbon_capture_list) != 0:
            for energy1 in energy_producing_carbon_capture_list:
                dtot_CO2_emissions[
                    f'{CarbonCapture.name} from energy mix (Gt) vs {energy1}#{CarbonCapture.name} (Mt)#prod'] = np.ones(
                    len_years)
        #             self.total_co2_emissions[f'{CarbonCapture.name} from energy mix (Mt)'] = energy_producing_carbon_capture.sum(
        #                 axis=1).values
        #         else:
        #             self.total_co2_emissions[
        #                 f'{CarbonCapture.name} from energy mix (Mt)'] = 0.0

        ''' CARBON CAPTURE needed by energy mix
        Total carbon capture needed by energy mix if a technology needs carbon_capture
         Ex :Sabatier process or RWGS in FischerTropsch technology 
        '''
        energy_needing_carbon_capture = co2_consumption[[
            col for col in co2_consumption if col.endswith(f'{CarbonCapture.name} (Mt)')]]
        energy_needing_carbon_capture_list = [key.replace(
            f' {CarbonCapture.name} (Mt)', '') for key in energy_needing_carbon_capture]
        if len(energy_needing_carbon_capture_list) != 0:
            for energy1 in energy_needing_carbon_capture_list:
                dtot_CO2_emissions[
                    f'{CarbonCapture.name} needed by energy mix (Gt) vs {energy1}#{CarbonCapture.name} (Mt)#cons'] = np.ones(
                    len_years)
        #             self.total_co2_emissions[f'{CarbonCapture.name} needed by energy mix (Mt)'] = energy_needing_carbon_capture.sum(
        #                 axis=1).values
        #         else:
        #             self.total_co2_emissions[
        #                 f'{CarbonCapture.name} needed by energy mix (Mt)'] = 0.0

        ''' CO2 from energy mix       
         CO2 expelled by energy mix technologies during the process 
         i.e. for machinery or tractors 
        '''
        energy_producing_co2 = co2_production[[
            col for col in co2_production if col.endswith(f'{CO2.name} (Mt)')]]
        energy_producing_co2_list = [key.replace(
            f' {CO2.name} (Mt)', '') for key in energy_producing_co2]
        if len(energy_producing_co2_list) != 0:
            for energy1 in energy_producing_co2_list:
                dtot_CO2_emissions[
                    f'{CO2.name} from energy mix (Mt) vs {energy1}#{CO2.name} (Mt)#prod'] = np.ones(len_years)

        #             self.total_co2_emissions[f'{CO2.name} from energy mix (Mt)'] = energy_producing_co2.sum(
        #                 axis=1).values
        #         else:
        #             self.total_co2_emissions[
        #                 f'{CO2.name} from energy mix (Mt)'] = 0.0

        ''' CO2 removed by energy mix       
         CO2 removed by energy mix technologies during the process 
         i.e. biomass processes as managed wood or crop energy
        '''
        energy_removing_co2 = co2_consumption[[
            col for col in co2_consumption if col.endswith(f'{CO2.name} (Mt)')]]
        energy_removing_co2_list = [key.replace(
            f' {CO2.name} (Mt)', '') for key in energy_removing_co2]
        if len(energy_removing_co2_list) != 0:
            for energy1 in energy_removing_co2_list:
                dtot_CO2_emissions[
                    f'{CO2.name} removed by energy mix (Mt) vs {energy1}#{CO2.name} (Mt)#cons'] = np.ones(len_years)
        #             self.total_co2_emissions[f'{CO2.name} removed by energy mix (Mt)'] = energy_removing_co2.sum(
        #                 axis=1).values
        #         else:
        #             self.total_co2_emissions[
        #                 f'{CO2.name} removed energy mix (Mt)'] = 0.0

        ''' Total C02 from Flue gas
            sum of all production of flue gas 
            it could be equal to carbon capture from CC technos if enough investment but not sure
        '''
        #         self.total_co2_emissions[f'Total {CarbonCapture.flue_gas_name} (Mt)'] = self.co2_production[[
        # col for col in self.co2_production if
        # col.endswith(f'{CarbonCapture.flue_gas_name} (Mt)')]].sum(axis=1)
        for col in co2_production:
            if col.endswith(f'{CarbonCapture.flue_gas_name} (Mt)'):
                energy1 = col.replace(
                    f' {CarbonCapture.flue_gas_name} (Mt)', '')
                dtot_CO2_emissions[
                    f'Total {CarbonCapture.flue_gas_name} (Mt) vs {energy1}#{CarbonCapture.flue_gas_name} (Mt)#prod'] = np.ones(
                    len_years)
        ''' Carbon captured that needs to be stored
            sum of the one from CC technos and the one directly captured 
            we delete the one needed by energy mix and potentially later the CO2 for food
        '''

        #         self.total_co2_emissions[f'{CarbonCapture.name} to be stored (Mt)'] = self.total_co2_emissions[f'{CarbonCapture.name} (Mt) from CC technos'] + \
        #             self.total_co2_emissions[f'{CarbonCapture.name} from energy mix (Mt)'] - \
        #             self.total_co2_emissions[f'{CarbonCapture.name} needed by energy mix (Mt)'] -\
        #             self.total_co2_emissions[f'{CO2.name} for food (Mt)'

        new_key = f'{CarbonCapture.name} to be stored (Mt)'
        key_dep_tuple_list = [(f'{CarbonCapture.name} (Mt) from CC technos', 1.0),
                              (f'{CarbonCapture.name} from energy mix (Mt)', 1.0),
                              (f'{CarbonCapture.name} needed by energy mix (Mt)', -1.0)]
        dtot_CO2_emissions = update_new_gradient(
            dtot_CO2_emissions, key_dep_tuple_list, new_key)

        return dtot_CO2_emissions


    def compute_distribution_list(self, input_dict):
        self.distribution_list = []
        for energy in input_dict[GlossaryEnergy.energy_list]:
            for techno in input_dict[f'{energy}.{GlossaryEnergy.techno_list}']:
                self.distribution_list.append(f'{energy}.{techno}')

def update_new_gradient(grad_dict, key_dep_tuple_list, new_key):
    '''
        Update new gradient which are dependent of old ones by simple sum or difference
    '''
    new_grad_dict = grad_dict.copy()
    for key in grad_dict:
        for old_key, factor in key_dep_tuple_list:
            if key.startswith(old_key):
                # the grad of old key is equivalent to the new key because its
                # a sum
                new_grad_key = key.replace(old_key, new_key)
                if new_grad_key in new_grad_dict:
                    new_grad_dict[new_grad_key] = new_grad_dict[new_grad_key] + \
                                                  grad_dict[key] * factor
                else:
                    new_grad_dict[new_grad_key] = grad_dict[key] * factor

    return new_grad_dict
