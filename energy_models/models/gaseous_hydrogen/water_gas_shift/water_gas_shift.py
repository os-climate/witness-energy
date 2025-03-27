'''
Copyright 2022 Airbus SAS
Modifications on 2023/09/25-2024/06/24 Copyright 2023 Capgemini

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


from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.core.stream_type.carbon_models.carbon_monoxyde import CO
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.energy_models.syngas import (
    compute_calorific_value as compute_syngas_calorific_value,
)
from energy_models.core.stream_type.energy_models.syngas import (
    compute_molar_mass as compute_syngas_molar_mass,
)
from energy_models.core.stream_type.resources_models.water import Water
from energy_models.core.techno_type.base_techno_models.gaseous_hydrogen_techno import (
    GaseousHydrogenTechno,
)
from energy_models.glossaryenergy import GlossaryEnergy


class WGS(GaseousHydrogenTechno):

    def __init__(self, name):
        super().__init__(name)
        self.available_power = None
        self.slope_capex = None

    def configure_parameters_update(self):
        GaseousHydrogenTechno.configure_parameters_update(self)
        self.inputs['syngas_ratio'] /= 100.
        self.inputs['needed_syngas_ratio'] /= 100.0

    def compute_available_power(self):
        data_config = self.inputs['data_fuel_dict']
        nitrogen_molar_mass = 2 * 14
        input_molar_mass = 0.3 * data_config['molar_mass'] + 0.3 * CO.data_energy_dict['molar_mass'] + \
                           0.25 * CO2.data_energy_dict['molar_mass'] + 0.1 * Methane.data_energy_dict['molar_mass'] \
                           + 0.05 * nitrogen_molar_mass

        input_calorific_value = 0.3 * data_config['calorific_value'] + 0.3 * CO.data_energy_dict[
            'calorific_value'] + \
                                0.25 * CO2.data_energy_dict['calorific_value'] + \
                                0.1 * Methane.data_energy_dict['calorific_value']

        # molar mass is in g/mol
        input_power = self.inputs['techno_infos_dict']['input_power'] * \
                      input_molar_mass / 1000.0 * input_calorific_value

        syngas_needs = self.get_theoretical_syngas_needs(1.0)

        self.available_power = input_power * self.inputs['techno_infos_dict']['full_load_hours'] / syngas_needs * self.inputs['techno_infos_dict']['efficiency']


    def capex_unity_harmonizer(self):
        '''
        Overload the check_capex_unity for this particular model 
        '''
        data_config = self.inputs['techno_infos_dict']
        capex_list = self.np.array(data_config['Capex_init_vs_CO_conversion'])
        data_config.update(self.inputs['data_fuel_dict'])

        capex_list = capex_list * \
                     data_config['euro_dollar'] / self.available_power
        # Need to convertcapex_list in $/kWh
        final_sg_ratio = 1.0 - self.np.array(data_config['CO_conversion']) / 100.0
        initial_sg_ratio = 0.3 / 0.3
        delta_sg_ratio = initial_sg_ratio - final_sg_ratio

        self.slope_capex = (
                                   capex_list[0] - capex_list[1]) / (delta_sg_ratio[0] - delta_sg_ratio[1])
        b = capex_list[0] - self.slope_capex * delta_sg_ratio[0]

        def func_capex(delta_sg_ratio):
            return self.slope_capex * delta_sg_ratio + b

        #         func_capex_a = sc.interp1d(delta_sg_ratio, capex_list,
        #                                    kind='linear', fill_value='extrapolate')

        capex_init = func_capex(
            self.inputs['syngas_ratio'][0] - self.inputs['needed_syngas_ratio'])

        return capex_init * 1000.0

    def get_electricity_needs(self):
        self.compute_available_power()
        elec_power = self.inputs['techno_infos_dict']['elec_demand']
        elec_demand = elec_power * self.inputs['techno_infos_dict']['full_load_hours'] / self.available_power

        return elec_demand

    def compute_resources_needs(self):
        # need in kg
        self.outputs[f"{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.WaterResource}_needs"] = self.get_theoretical_water_needs()/ self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

    def compute_energies_needs(self):
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.electricity}_needs'] = self.get_electricity_needs()
        # in kwh of fuel by kwh of H2
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:syngas_needs'] = self.get_theoretical_syngas_needs(self.inputs['syngas_ratio']) / self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

    def compute_byproducts_production(self):
        # production
        # self.production[f'{lowheattechno.stream_name} ({self.product_unit})'] = \
        #     self.inputs['techno_infos_dict']['low_heat_production'] * \
        #     self.production[f'{GaseousHydrogenTechno.stream_name} ({self.product_unit})']  # in TWH
        pass


    def get_theoretical_syngas_needs(self, syngas_ratio):
        ''' 
        (H2 +r1CO) + cH20 --> dCO2 + e(H2 +r2CO)

        e = (1+r1)/(1+r2)
        c = (r1-r2)/(1+r2)
        d = r1 - r2(1+r1)/(1+r2)
        '''

        mol_H2 = (1.0 + syngas_ratio) / (1.0 + self.inputs['needed_syngas_ratio'])
        mol_syngas = 1.0

        # r1*mmCO + mmH2/(1+r1)
        syngas_molar_mass = compute_syngas_molar_mass(syngas_ratio)
        syngas_calorific_value = compute_syngas_calorific_value(
            syngas_ratio)

        # needed syngas_ratio could be 0 in this case syngas is H2
        needed_syngas_molar_mass = compute_syngas_molar_mass(
            self.inputs['needed_syngas_ratio'])
        needed_calorific_value = compute_syngas_calorific_value(
            self.inputs['needed_syngas_ratio'])
        syngas_needs = mol_syngas * syngas_molar_mass * syngas_calorific_value / \
                       (mol_H2 * needed_syngas_molar_mass *
                        needed_calorific_value)

        return syngas_needs

    def get_theoretical_water_needs(self):
        ''' 
        (H2 +r1CO) + cH20 --> dCO2 + e(H2 +r2CO)

        e = (1+r1)/(1+r2)
        c = (r1-r2)/(1+r2)
        d = r1 - r2(1+r1)/(1+r2)
        '''

        mol_H20 = (self.inputs['syngas_ratio'] - self.inputs['needed_syngas_ratio']) / \
                  (1.0 + self.inputs['needed_syngas_ratio'])
        mol_H2 = (1.0 + self.inputs['syngas_ratio']) / (1.0 + self.inputs['needed_syngas_ratio'])

        # needed syngas_ratio could be 0 in this case syngas is H2
        needed_syngas_molar_mass = compute_syngas_molar_mass(
            self.inputs['needed_syngas_ratio'])
        needed_calorific_value = compute_syngas_calorific_value(
            self.inputs['needed_syngas_ratio'])

        water_data = Water.data_energy_dict
        water_needs = mol_H20 * water_data['molar_mass'] / \
                      (mol_H2 * needed_syngas_molar_mass *
                       needed_calorific_value)

        return water_needs

    def compute_co2_from_flue_gas_intensity_scope_1(self, unit='kg/kWh'):
        ''' 
        Get co2 producted in kg co2 /kWh H2
        1 mol of CO2 for 4 mol of H2
        Warning : molar mass is in g/mol but we divide and multiply by one
        '''

        mol_H2 = (1.0 + self.inputs['syngas_ratio']) / (1.0 + self.inputs['needed_syngas_ratio'])
        mol_CO2 = self.inputs['syngas_ratio'] - self.inputs['needed_syngas_ratio'] * mol_H2

        co2_data = CO2.data_energy_dict

        # needed syngas_ratio could be 0 in this case syngas is H2
        needed_syngas_molar_mass = compute_syngas_molar_mass(
            self.inputs['needed_syngas_ratio'])
        needed_calorific_value = compute_syngas_calorific_value(
            self.inputs['needed_syngas_ratio'])

        if unit == 'kg/kWh':
            co2_prod = mol_CO2 * co2_data['molar_mass'] / \
                       (mol_H2 * needed_syngas_molar_mass *
                        needed_calorific_value)
        elif unit == 'kg/kg':
            co2_prod = mol_CO2 * co2_data['molar_mass'] / \
                       (mol_H2 * needed_syngas_molar_mass)
        else:
            raise Exception("unit not handled")

        return co2_prod
