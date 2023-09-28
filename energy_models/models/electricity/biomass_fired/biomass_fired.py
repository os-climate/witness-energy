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
from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
from energy_models.core.stream_type.energy_models.heat import hightemperatureheat


class BiomassFired(ElectricityTechno):

    COPPER_RESOURCE_NAME = ResourceGlossary.Copper['name']

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs which depends on the technology
        """
        # Cost of biomass for 1 kWH
        self.cost_details[BiomassDry.name] = list(
            self.prices[BiomassDry.name] * self.techno_infos_dict['biomass_needs'])

        return self.cost_details[BiomassDry.name]

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ?
        """

        self.compute_primary_energy_production()

        co2_prod = self.get_theoretical_co2_prod()
        self.production[f'{CarbonCapture.flue_gas_name} ({self.mass_unit})'] = co2_prod * \
            self.production[f'{ElectricityTechno.energy_name} ({self.product_energy_unit})']

        self.production[f'{hightemperatureheat.name} ({self.product_energy_unit})'] = self.consumption[f'{BiomassDry.name} ({self.product_energy_unit})'] - \
             self.production[f'{ElectricityTechno.energy_name} ({self.product_energy_unit})']   #TWh

        # Consumption
        self.consumption[f'{BiomassDry.name} ({self.product_energy_unit})'] = self.techno_infos_dict['biomass_needs'] * \
            self.production[f'{ElectricityTechno.energy_name} ({self.product_energy_unit})']
        
    def compute_consumption_and_power_production(self):
        """
        Compute the resource consumption and the power installed (MW) of the technology for a given investment
        """
        self.compute_primary_power_production()

        # FOR ALL_RESOURCES DISCIPLINE

        copper_needs = self.get_theoretical_copper_needs(self)
        self.consumption[f'{self.COPPER_RESOURCE_NAME} ({self.mass_unit})'] = copper_needs * self.power_production['new_power_production'] # in Mt

    def get_theoretical_co2_prod(self, unit='kg/kWh'):
        '''
        Get co2 needs in kg co2 /kWh
        '''
        biomass_data = BiomassDry.data_energy_dict
        # kg of C02 per kg of biomass burnt
        biomass_co2 = biomass_data['CO2_per_use']
        # Amount of biomass in kwh for 1 kwh of elec
        biomass_need = self.techno_infos_dict['biomass_needs']
        calorific_value = biomass_data['calorific_value']  # kWh/kg

        co2_prod = biomass_co2 / calorific_value * biomass_need
        return co2_prod

    @staticmethod
    def get_theoretical_copper_needs(self):
        """
        No data found, therefore we make the assumption that it needs at least a generator which uses the same amount of copper as a gaz powered station
        It needs 1100 kg / MW
        Computing the need in Mt/MW
        """
        copper_need = self.techno_infos_dict['copper_needs'] / 1000 / 1000 / 1000

        return copper_need


    def compute_CO2_emissions_from_input_resources(self):
        '''
        Need to take into account  CO2 from methane extraction
        '''

        self.carbon_emissions[BiomassDry.name] = self.energy_CO2_emissions[BiomassDry.name] * \
            self.techno_infos_dict['biomass_needs']

        return self.carbon_emissions[BiomassDry.name]

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        biomass_needs = self.techno_infos_dict['biomass_needs']
        # Note that efficiency = 1
        return {BiomassDry.name: np.identity(len(self.years)) * biomass_needs}
