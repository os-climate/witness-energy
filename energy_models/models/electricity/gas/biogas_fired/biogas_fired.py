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
from energy_models.core.techno_type.base_techno_models.electricity_techno import ElectricityTechno
from energy_models.core.stream_type.energy_models.biogas import BioGas
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture


class BiogasFired(ElectricityTechno):

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs which depends on the technology 
        """
        # Cost of biogas for 1 kWH
        self.cost_details[BioGas.name] = list(
            self.prices[BioGas.name] * self.techno_infos_dict['biogas_needs'])

        return self.cost_details[BioGas.name]

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """

        self.compute_primary_energy_production()

        co2_prod = self.get_theoretical_co2_prod()
        self.production[f'{CarbonCapture.flue_gas_name} ({self.mass_unit})'] = co2_prod * \
            self.production[f'{ElectricityTechno.energy_name} ({self.product_energy_unit})']

        # Consumption
        self.consumption[f'{BioGas.name} ({self.product_energy_unit})'] = self.techno_infos_dict['biogas_needs'] * \
            self.production[f'{ElectricityTechno.energy_name} ({self.product_energy_unit})']

    def get_theoretical_co2_prod(self, unit='kg/kWh'):
        ''' 
        Get co2 needs in kg co2 /kWh 
        '''
        biogas_data = BioGas.data_energy_dict
        # kg of C02 per kg of biogas burnt
        biogas_co2 = biogas_data['CO2_per_use']
        # Amount of biogas in kwh for 1 kwh of elec
        biogas_need = self.techno_infos_dict['biogas_needs']
        calorific_value = biogas_data['calorific_value']  # kWh/kg

        co2_prod = biogas_co2 / calorific_value * biogas_need
        return co2_prod

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        biogas_needs = self.techno_infos_dict['biogas_needs']
        # Note that efficiency = 1
        return {BioGas.name: np.identity(len(self.years)) * biogas_needs}
