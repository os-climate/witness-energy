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
from energy_models.core.stream_type.energy_models.hydrotreated_oil_fuel import HydrotreatedOilFuel
from energy_models.core.stream_type.resources_models.natural_oil import NaturalOil
from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.core.techno_type.base_techno_models.hydrotreated_oil_fuel_techno import HydrotreatedOilFuelTechno
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import GaseousHydrogen
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture


import numpy as np


class HefaDecarboxylation(HydrotreatedOilFuelTechno):
    # Sources
    # https://biotechnologyforbiofuels.biomedcentral.com/articles/10.1186/s13068-017-0739-7     --> Selected source
    # https://www.etipbioenergy.eu/value-chains/conversion-technologies/conventional-technologies/hydrotreatment-to-hvo

    """
        Chemical reaction: oil + 15H2 = 3fuel + 6H20 (hydrogenation + deoxygenation) --> HEFA "green"
        or
        oil + 6H2 = 3fuel + 3C02 (hydrogenation + decarboxylation)  --> HEFA
    """

    elec_consumption_factor = .185

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs to produce 1MWh of hydrotreated_oil_fuel
        """
        self.cost_details[f'{GaseousHydrogen.name}_needs'] = self.get_theoretical_hydrogen_needs(
        )

        naturaloil_data = NaturalOil.data_energy_dict
        self.cost_details[f'{NaturalOil.name}_needs'] = self.get_theoretical_natural_oil_needs(
        ) / naturaloil_data['calorific_value']

        self.cost_details[f'{Electricity.name}_needs'] = self.elec_consumption_factor

        self.cost_details[f'{NaturalOil.name}'] = list(
            self.resources_prices[f'{NaturalOil.name}'] * self.cost_details[f'{NaturalOil.name}_needs'] / self.cost_details['efficiency'])

        self.cost_details[f'{GaseousHydrogen.name}'] = list(
            self.prices[f'{GaseousHydrogen.name}'] * self.cost_details[f'{GaseousHydrogen.name}_needs'] / self.cost_details['efficiency'])

        self.cost_details[f'{Electricity.name}'] = list(
            self.prices[f'{Electricity.name}'] * self.cost_details[f'{Electricity.name}_needs'])

        return self.cost_details[f'{NaturalOil.name}'] + self.cost_details[f'{GaseousHydrogen.name}'] + self.cost_details[f'{Electricity.name}']

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices 
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        elec_needs = self.elec_consumption_factor
        hydrogen_needs = self.get_theoretical_hydrogen_needs()
        efficiency = self.techno_infos_dict['efficiency']

        return {Electricity.name: np.identity(len(self.years)) * elec_needs,
                GaseousHydrogen.name: np.identity(len(self.years)) * hydrogen_needs / efficiency}

    def grad_price_vs_resources_price(self):
        '''
        Compute the gradient of global price vs resources prices
        '''

        naturaloil_data = NaturalOil.data_energy_dict
        efficiency = self.techno_infos_dict['efficiency']
        oil_needs = self.get_theoretical_natural_oil_needs() / naturaloil_data['calorific_value'] / efficiency
        return {
            NaturalOil.name: np.identity(
                len(self.years)) * oil_needs,
        }

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ?
        """

        

        carbon_production_factor = self.get_theoretical_co2_prod()
        self.production_detailed[f'{CarbonCapture.name} ({self.mass_unit})'] = carbon_production_factor * \
                                                                               self.production_detailed[f'{HydrotreatedOilFuel.name} ({self.product_energy_unit})'] / \
                                                                               self.cost_details['efficiency']

        self.consumption_detailed[f'{Electricity.name} ({self.product_energy_unit})'] = self.cost_details[f'{Electricity.name}_needs'] * \
                                                                                        self.production_detailed[f'{HydrotreatedOilFuel.name} ({self.product_energy_unit})']  # / \

        self.consumption_detailed[f'{GaseousHydrogen.name} ({self.product_energy_unit})'] = self.cost_details[f'{GaseousHydrogen.name}_needs'] * \
                                                                                            self.production_detailed[f'{HydrotreatedOilFuel.name} ({self.product_energy_unit})'] / \
                                                                                            self.cost_details['efficiency']

        naturaloil_data = NaturalOil.data_energy_dict
        self.consumption_detailed[f'{NaturalOil.name} ({self.product_energy_unit})'] = self.cost_details[f'{NaturalOil.name}_needs'] * \
                                                                                       self.production_detailed[f'{HydrotreatedOilFuel.name} ({self.product_energy_unit})'] / \
                                                                                       self.cost_details['efficiency'] * \
                                                                                       naturaloil_data['calorific_value']

    def compute_CO2_emissions_from_input_resources(self):
        """
        Need to take into account  CO2 from electricity/hydrogen production
        """

        self.carbon_emissions[f'{Electricity.name}'] = self.energy_CO2_emissions[f'{Electricity.name}'] * \
            self.cost_details[f'{Electricity.name}_needs']

        self.carbon_emissions[f'{GaseousHydrogen.name}'] = self.energy_CO2_emissions[f'{GaseousHydrogen.name}'] * \
            self.cost_details[f'{GaseousHydrogen.name}_needs'] / \
            self.cost_details['efficiency']

        self.carbon_emissions[f'{NaturalOil.name}'] = self.resources_CO2_emissions[f'{NaturalOil.name}'] * \
            self.cost_details[f'{NaturalOil.name}_needs'] / \
            self.cost_details['efficiency']

        # Theoretical C02 production in kg
        carbon_production_factor = self.get_theoretical_co2_prod()
        self.carbon_emissions[f'{CarbonCapture.name}'] = carbon_production_factor

        return self.carbon_emissions[f'{Electricity.name}'] + self.carbon_emissions[f'{NaturalOil.name}']  \
            + self.carbon_emissions[f'{GaseousHydrogen.name}'] + \
            self.carbon_emissions[f'{CarbonCapture.name}']

    def get_theoretical_natural_oil_needs(self):
        """
       oil + 6H2 = 3fuel + 3C02 (hydrogenation + decarboxylation)
        """
        naturaloil_data = NaturalOil.data_energy_dict

        natural_oil_needs = 1 / 3 * naturaloil_data['calorific_value'] * naturaloil_data['molar_mass'] / \
            (self.data_energy_dict['calorific_value']
             * self.data_energy_dict['molar_mass'])

        return natural_oil_needs

    def get_theoretical_hydrogen_needs(self):
        """
       oil + 6H2 = 3fuel + 3C02 (hydrogenation + decarboxylation)
        """
        hydrogen_data = GaseousHydrogen.data_energy_dict

        gaseous_hydrogen_needs = 6 / 3 * hydrogen_data['calorific_value'] * hydrogen_data['molar_mass'] / \
            (self.data_energy_dict['calorific_value']
             * self.data_energy_dict['molar_mass'])

        return gaseous_hydrogen_needs

    def get_theoretical_co2_prod(self, unit='kg/kWh'):
        """
       oil + 6H2 = 3fuel + 3C02 (hydrogenation + decarboxylation)
        """
        co2_molar_mass = CO2.data_energy_dict['molar_mass']
        co2_prod = (3 / 3) * co2_molar_mass / \
            (self.data_energy_dict['calorific_value']
             * self.data_energy_dict['molar_mass'])

        return co2_prod
