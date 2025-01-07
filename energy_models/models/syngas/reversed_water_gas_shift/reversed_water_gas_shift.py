'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2023/11/16 Copyright 2023 Capgemini

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

from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.core.stream_type.carbon_models.carbon_monoxyde import CO
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import (
    GaseousHydrogen,
)
from energy_models.core.stream_type.energy_models.syngas import (
    compute_calorific_value as compute_syngas_calorific_value,
)
from energy_models.core.stream_type.energy_models.syngas import (
    compute_molar_mass as compute_syngas_molar_mass,
)
from energy_models.core.stream_type.resources_models.water import Water
from energy_models.core.techno_type.base_techno_models.syngas_techno import SyngasTechno
from energy_models.core.techno_type.techno_type import TechnoType
from energy_models.glossaryenergy import GlossaryEnergy


class RWGS(SyngasTechno):

    def __init__(self, name):
        super().__init__(name)
        self.esk = None
        self.available_power = None
        self.slope_capex: float = 0.0
        self.slope_elec_demand: float = 0.0

    def compute(self):
        TechnoType.compute(self)

    def configure_parameters_update(self):

        # We need these lines if both configure because syngas is the coupling variable (so in configure_parameters_update)
        # but is also used in configure energy data for physical parameters (
        # so in configure parameters)
        self.inputs['syngas_ratio'] /= 100.0
        self.inputs['needed_syngas_ratio'] /= 100.0
        self.syngas_COH2_ratio = self.inputs['syngas_ratio']

        SyngasTechno.configure_parameters_update(self)

    def capex_unity_harmonizer(self):
        '''
        Overload the check_capex_unity for this particular model 
        '''
        data_config = self.inputs['techno_infos_dict']
        capex_list = np.array(data_config['Capex_init_vs_CO_H2_ratio'])

        # input power was in mol/h
        # We multiply by molar mass and calorific value of the paper to get
        # input power in kW

        final_syngas_ratio = np.array(data_config['CO_H2_ratio'])

        # molar mass is in g/mol !!
        syngas_molar_mass = compute_syngas_molar_mass(final_syngas_ratio)
        syngas_calorific_value = compute_syngas_calorific_value(
            final_syngas_ratio)

        # Available power is now in kW
        self.available_power = np.array(
            data_config['available_power']) * syngas_molar_mass / 1000.0 * syngas_calorific_value
        # Need to convertcapex_list in $/kWh
        capex_list = capex_list / self.available_power / \
                     data_config['full_load_hours']

        initial_syngas_ratio = 0.0
        delta_syngas_ratio = final_syngas_ratio - initial_syngas_ratio

        self.slope_capex = (
                                   capex_list[0] - capex_list[1]) / (delta_syngas_ratio[0] - delta_syngas_ratio[1])
        b = capex_list[0] - self.slope_capex * delta_syngas_ratio[0]

        def func_capex(delta_sg_ratio):
            return self.slope_capex * delta_sg_ratio + b

        # func_capex = sc.interp1d(delta_sg_ratio, capex_list,
        #                         kind='linear', fill_value='extrapolate')

        # func_capex = sc.interp1d(delta_syngas_ratio, capex_list,
        #                         kind='linear', fill_value='extrapolate')

        capex_init = func_capex(self.inputs['needed_syngas_ratio'] - self.inputs['syngas_ratio'][0])

        return capex_init

    def get_electricity_needs(self):

        elec_demand = self.inputs['techno_infos_dict']['elec_demand'] / \
                      self.available_power / self.inputs['techno_infos_dict']['full_load_hours']
        final_syngas_ratio = np.array(self.inputs['techno_infos_dict']['CO_H2_ratio'])
        initial_syngas_ratio = 0.0
        delta_syngas_ratio = final_syngas_ratio - initial_syngas_ratio

        self.slope_elec_demand = (elec_demand[0] - elec_demand[1]) / \
                                 (delta_syngas_ratio[0] - delta_syngas_ratio[1])
        b = elec_demand[0] - self.slope_elec_demand * delta_syngas_ratio[0]

        def func_elec_demand(syngas_ratio):
            return self.slope_elec_demand * syngas_ratio + b

        # func_elec_demand = sc.interp1d(delta_syngas_ratio, elec_demand,
        # kind='linear', fill_value='extrapolate')

        elec_demand = func_elec_demand(
            self.inputs['needed_syngas_ratio'] - self.inputs['syngas_ratio'])
        return elec_demand

    def compute_resources_needs(self):
        self.outputs[f"{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.CO2Resource}_needs"] = self.get_theoretical_co2_needs() / self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

    def compute_other_streams_needs(self):
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.electricity}_needs'] = self.get_electricity_needs()

        # Cost of methane for 1 kWH of H2
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:syngas_needs'] = self.get_theoretical_syngas_needs(self.inputs['syngas_ratio']) / self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']


    def compute_byproducts_production(self):
        th_water_prod = self.get_theoretical_water_prod()

        self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:{Water.name} ({GlossaryEnergy.mass_unit})'] = th_water_prod * \
                                                                       self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:'
                                                                           f'{SyngasTechno.energy_name} ({self.product_unit})']

    def compute_streams_consumption(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """

        super().compute_streams_consumption()

        self.outputs[f'{GlossaryEnergy.TechnoConsumptionValue}:{CarbonCapture.name} ({GlossaryEnergy.mass_unit})'] = self.outputs[f"{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.CO2Resource}_needs"] * \
                                                                                self.outputs[f'{GlossaryEnergy.TechnoDetailedProductionValue}:{SyngasTechno.energy_name} ({self.product_unit})']  # in kg

    def get_theoretical_syngas_needs(self, syngas_ratio):
        ''' 
        dCO2 + e(H2 +r1CO)-->  (H2 +r2CO) + cH20 

        e = (1+r2)/(1+r1)
        c = (r2-r1)/(1+r1)
        d = r2 - r1(1+r2)/(1+r1)
        '''
        mol_syngas_in = (1.0 + self.inputs['needed_syngas_ratio']) / \
                        (1.0 + syngas_ratio)
        mol_syngas_out = 1.0

        syngas_molar_mass_in = compute_syngas_molar_mass(syngas_ratio)
        syngas_calorific_value_in = compute_syngas_calorific_value(
            syngas_ratio)

        # needed syngas_ratio could be 0 in this case syngas is H2
        syngas_molar_mass_out = compute_syngas_molar_mass(
            self.inputs['needed_syngas_ratio'])
        calorific_value_out = compute_syngas_calorific_value(
            self.inputs['needed_syngas_ratio'])

        syngas_needs = mol_syngas_in * syngas_molar_mass_in * syngas_calorific_value_in / \
                       (mol_syngas_out * syngas_molar_mass_out *
                        calorific_value_out)

        return syngas_needs

    def get_theoretical_water_prod(self):
        ''' 
        dCO2 + e(H2 +r1CO)-->  (H2 +r2CO) + cH20 

        e = (1+r2)/(1+r1)
        c = (r2-r1)/(1+r1)
        d = r2 - r1(1+r2)/(1+r1)
        '''

        mol_H20 = (self.inputs['needed_syngas_ratio'] - self.inputs['syngas_ratio']) / \
                  (1.0 + self.inputs['syngas_ratio'])
        mol_H2 = 1.0

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

    def get_theoretical_co2_needs(self, unit='kg/kWh'):
        ''' 
        dCO2 + e(H2 +r1CO)-->  (H2 +r2CO) + cH20 

        e = (1+r2)/(1+r1)
        c = (r2-r1)/(1+r1)
        d = r2 - r1(1+r2)/(1+r1)
        '''

        mol_H2 = 1.0
        mol_CO2 = self.inputs['needed_syngas_ratio'] - self.inputs['syngas_ratio'] * (1.0 + self.inputs['needed_syngas_ratio']) / \
                  (1.0 + self.inputs['syngas_ratio'])

        co2_data = CO2.data_energy_dict

        # needed syngas_ratio could be 0 in this case syngas is H2
        needed_syngas_molar_mass = compute_syngas_molar_mass(
            self.inputs['needed_syngas_ratio'])
        needed_calorific_value = compute_syngas_calorific_value(
            self.inputs['needed_syngas_ratio'])

        if unit == 'kg/kWh':
            co2_needs = mol_CO2 * co2_data['molar_mass'] / \
                        (mol_H2 * needed_syngas_molar_mass *
                         needed_calorific_value)
        elif unit == 'kg/kg':
            co2_needs = mol_CO2 * co2_data['molar_mass'] / \
                        (mol_H2 * needed_syngas_molar_mass)
        else:
            raise Exception("The unit is not handled")
        return co2_needs
