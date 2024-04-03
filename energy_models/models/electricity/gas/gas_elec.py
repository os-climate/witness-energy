'''
Copyright 2022 Airbus SAS
Modifications on 2023/10/03-2023/11/16 Copyright 2023 Capgemini

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
from energy_models.core.stream_type.carbon_models.nitrous_oxide import N2O
from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
from energy_models.core.techno_type.base_techno_models.electricity_techno import ElectricityTechno


class GasElec(ElectricityTechno):
    COPPER_RESOURCE_NAME = ResourceGlossary.CopperResource


    def compute_other_energies_needs(self):
        self.cost_details[f'{Methane.name}_needs'] = self.techno_infos_dict['kwh_methane/kwh']

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ?
        """

        co2_prod = self.get_theoretical_co2_prod()

        # Consumption
        self.consumption_detailed[f'{Methane.name} ({self.product_energy_unit})'] = self.techno_infos_dict[
                                                                                        'kwh_methane/kwh'] * \
                                                                                    self.production_detailed[
                                                                                        f'{ElectricityTechno.energy_name} ({self.product_energy_unit})']

        # Production
        self.production_detailed[f'{CarbonCapture.flue_gas_name} ({self.mass_unit})'] = co2_prod * \
                                                                                        self.production_detailed[
                                                                                            f'{ElectricityTechno.energy_name} ({self.product_energy_unit})']

        self.production_detailed[f'{hightemperatureheat.name} ({self.product_energy_unit})'] = \
        self.consumption_detailed[f'{Methane.name} ({self.product_energy_unit})'] - \
        self.production_detailed[f'{ElectricityTechno.energy_name} ({self.product_energy_unit})']

        self.compute_ghg_emissions(Methane.emission_name, related_to=Methane.name)
        self.compute_ghg_emissions(N2O.name, related_to=Methane.name)

    def compute_consumption_and_installed_power(self):
        """
        Compute the resource consumption and the power installed (MW) of the technology for a given investment
        """

        # FOR ALL_RESOURCES DISCIPLINE

        copper_needs = self.get_theoretical_copper_needs(self)
        self.consumption_detailed[f'{self.COPPER_RESOURCE_NAME} ({self.mass_unit})'] = copper_needs * \
                                                                                       self.installed_power[
                                                                                           'new_power_production']  # in Mt

    def get_theoretical_co2_prod(self, unit='kg/kWh'):
        '''
        Get co2 needs in kg co2 /kWh
        '''
        methane_data = Methane.data_energy_dict
        # kg of C02 per kg of methane burnt
        methane_co2 = methane_data['CO2_per_use']
        # Amount of methane in kwh for 1 kwh of elec
        methane_need = self.techno_infos_dict['kwh_methane/kwh']
        calorific_value = methane_data['calorific_value']  # kWh/kg

        co2_prod = methane_co2 / calorific_value * methane_need
        return co2_prod

    def compute_ch4_emissions(self):
        '''
        Method to compute CH4 emissions from methane consumption
        The proposed V0 only depends on consumption.
        Equation and emission factor are taken from the GAINS model
        https://previous.iiasa.ac.at/web/home/research/researchPrograms/air/IR54-GAINS-CH4.pdf

        emission_factor is in Mt/TWh
        '''
        ghg_type = Methane.emission_name
        emission_factor = self.techno_infos_dict[f'{ghg_type}_emission_factor']

        self.production_detailed[f'{ghg_type} ({self.mass_unit})'] = emission_factor * \
                                                                     self.consumption_detailed[
                                                                         f'{Methane.name} ({self.product_energy_unit})']

    @staticmethod
    def get_theoretical_copper_needs(self):
        """
        According to the IEA, Gaz powered stations need 1100 kg of copper for each MW implemented
        Computing the need in Mt/MW
        """
        copper_need = self.techno_infos_dict['copper_needs'] / 1000 / 1000 / 1000

        return copper_need
