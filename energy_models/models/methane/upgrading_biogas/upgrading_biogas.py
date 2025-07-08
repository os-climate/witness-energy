'''
Copyright 2022 Airbus SAS
Modifications on 2023/10/10-2023/11/16 Copyright 2023 Capgemini

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
from energy_models.core.stream_type.energy_models.biogas import BioGas
from energy_models.core.techno_type.base_techno_models.methane_techno import (
    MethaneTechno,
)
from energy_models.glossaryenergy import GlossaryEnergy


class UpgradingBiogas(MethaneTechno):

    def compute_energies_needs(self):
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.electricity}_needs'] = self.get_electricity_needs() + self.zeros_array
        # in kwh of fuel by kwh of H2

        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.biogas}_needs'] = self.get_biogas_needs() + self.zeros_array

    def compute_resources_needs(self):
        self.outputs[f"{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.MonoEthanolAmineResource}_needs"] = self.get_MEA_loss() + self.zeros_array

    def compute_byproducts_production(self):
        # kg/kWh corresponds to Mt/TWh
        co2_prod = self.get_theoretical_co2_prod()
        self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:{GlossaryEnergy.carbon_captured} ({GlossaryEnergy.mass_unit})'] = \
            co2_prod * self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:{self.stream_name}']

        # production
        # self.production[f'{lowheattechno.stream_name} ({self.product_unit})'] = \
        #     self.inputs['techno_infos_dict']['low_heat_production'] * \
        #     self.production[f'{MethaneTechno.stream_name} ({self.product_unit})']  # in TWH

    def get_biogas_needs(self):
        '''
        COmpute theoretical biogas needs with proportion of CO2 and CH4 given in biogas energy
        Divide by efficiency for realistic demand
        '''
        biogas_data = BioGas.data_energy_dict
        mol_biogas = 1.0
        mol_CH4 = biogas_data['CH4_per_energy']
        biogas_needs = mol_biogas * biogas_data['molar_mass'] * biogas_data['calorific_value'] / \
                       (mol_CH4 * self.inputs['data_fuel_dict']['molar_mass'] *
                        self.inputs['data_fuel_dict']['calorific_value'])
        return biogas_needs / self.inputs['techno_infos_dict']['efficiency']

    def get_MEA_loss(self):
        '''
        MonoEthanolAmine needs are in kg/m^3
        '''

        mea_loss = self.inputs['techno_infos_dict']['MEA_needs'] / (self.inputs['data_fuel_dict']['density'] * self.inputs['data_fuel_dict']['calorific_value'])

        return mea_loss

    def get_theoretical_co2_prod(self, unit='kg/kWh'):
        '''
        Get CO2 prod from upgrading biogas
        With the fraction of CO2 in biogas considered
        '''
        biogas_data = BioGas.data_energy_dict
        mol_CO2 = 1.0 - biogas_data['CH4_per_energy']
        mol_CH4 = biogas_data['CH4_per_energy']
        co2_data = CO2.data_energy_dict

        co2_prod = 0

        if unit == 'kg/kWh':
            co2_prod = mol_CO2 * co2_data['molar_mass'] / \
                       (mol_CH4 * self.inputs['data_fuel_dict']['molar_mass'] *
                        self.inputs['data_fuel_dict']['calorific_value'])
        elif unit == 'kg/kg':
            co2_prod = mol_CO2 * co2_data['molar_mass'] / \
                       (mol_CH4 * self.inputs['data_fuel_dict']['molar_mass'])

        return co2_prod
