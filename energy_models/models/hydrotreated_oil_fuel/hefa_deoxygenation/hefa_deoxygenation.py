'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/09-2023/11/15 Copyright 2023 Capgemini

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

from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import GaseousHydrogen
from energy_models.core.stream_type.energy_models.hydrotreated_oil_fuel import HydrotreatedOilFuel
from energy_models.core.stream_type.resources_models.natural_oil import NaturalOil
from energy_models.core.stream_type.resources_models.water import Water
from energy_models.core.techno_type.base_techno_models.hydrotreated_oil_fuel_techno import HydrotreatedOilFuelTechno


class HefaDeoxygenation(HydrotreatedOilFuelTechno):
    # Sources
    # https://biotechnologyforbiofuels.biomedcentral.com/articles/10.1186/s13068-017-0739-7     --> Selected source
    # https://www.etipbioenergy.eu/value-chains/conversion-technologies/conventional-technologies/hydrotreatment-to-hvo

    """
        Chemical reaction: oil + 15H2 = 3fuel + 6H20 (hydrogenation + deoxygenation) --> HEFA "green"
        or
        oil + 6H2 = 3fuel + 3C02 (hydrogenation + decarboxylation)  --> HEFA
    """

    elec_consumption_factor = .185

    def compute_cost_of_other_energies_usage(self):
        self.cost_details[NaturalOil.name] = list(
            self.resources_prices[NaturalOil.name] * self.cost_details[f'{NaturalOil.name}_needs'] / self.cost_details[
                'efficiency'])

        self.cost_details[GaseousHydrogen.name] = list(
            self.prices[GaseousHydrogen.name] * self.cost_details[f'{GaseousHydrogen.name}_needs'] / self.cost_details[
                'efficiency'])

        self.cost_details[Electricity.name] = list(
            self.prices[Electricity.name] * self.cost_details[f'{Electricity.name}_needs'])


    def compute_other_energies_needs(self):
        self.cost_details[f'{GaseousHydrogen.name}_needs'] = self.get_theoretical_hydrogen_needs(
        )

        naturaloil_data = NaturalOil.data_energy_dict
        self.cost_details[f'{NaturalOil.name}_needs'] = self.get_theoretical_natural_oil_needs(
        ) / naturaloil_data['calorific_value']

        self.cost_details[f'{Electricity.name}_needs'] = self.elec_consumption_factor


    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs to produce 1kWh of hydrotreated_oil_fuel
        """
        super().compute_other_primary_energy_costs()

        return self.cost_details[NaturalOil.name] + self.cost_details[GaseousHydrogen.name] + self.cost_details[Electricity.name]

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

        # Theoretical C02 production in kg
        water_calorific_value = Water.data_energy_dict['calorific_value']
        water_prod_factor = self.get_theoretical_water_prod()
        self.production_detailed[f'{Water.name} ({self.mass_unit})'] = water_prod_factor * self.production_detailed[
            f'{HydrotreatedOilFuel.name} ({self.product_energy_unit})'] / water_calorific_value

        self.consumption_detailed[f'{Electricity.name} ({self.product_energy_unit})'] = self.cost_details[
                                                                                            f'{Electricity.name}_needs'] * \
                                                                                        self.production_detailed[
                                                                                            f'{HydrotreatedOilFuel.name} ({self.product_energy_unit})']

        self.consumption_detailed[f'{GaseousHydrogen.name} ({self.product_energy_unit})'] = self.cost_details[
                                                                                                f'{GaseousHydrogen.name}_needs'] * \
                                                                                            self.production_detailed[
                                                                                                f'{HydrotreatedOilFuel.name} ({self.product_energy_unit})'] / \
                                                                                            self.cost_details[
                                                                                                'efficiency']

        naturaloil_data = NaturalOil.data_energy_dict
        self.consumption_detailed[f'{NaturalOil.name} ({self.product_energy_unit})'] = self.cost_details[
                                                                                           f'{NaturalOil.name}_needs'] * \
                                                                                       self.production_detailed[
                                                                                           f'{HydrotreatedOilFuel.name} ({self.product_energy_unit})'] / \
                                                                                       self.cost_details['efficiency'] * \
                                                                                       naturaloil_data[
                                                                                           'calorific_value']

    def compute_CO2_emissions_from_input_resources(self):
        """
        Need to take into account  CO2 from electricity/hydrogen production
        """

        self.carbon_intensity[Electricity.name] = self.energy_CO2_emissions[Electricity.name] * \
                                                  self.cost_details[f'{Electricity.name}_needs']

        self.carbon_intensity[GaseousHydrogen.name] = self.energy_CO2_emissions[GaseousHydrogen.name] * \
                                                      self.cost_details[f'{GaseousHydrogen.name}_needs'] / \
                                                      self.cost_details['efficiency']

        self.carbon_intensity[NaturalOil.name] = self.resources_CO2_emissions[NaturalOil.name] * \
                                                 self.cost_details[f'{NaturalOil.name}_needs'] / \
                                                 self.cost_details['efficiency']

        return self.carbon_intensity[Electricity.name] + self.carbon_intensity[NaturalOil.name] \
               + self.carbon_intensity[GaseousHydrogen.name]

    def get_theoretical_natural_oil_needs(self):
        """
       oil + 15H2 = 3fuel + 6H20 (hydrogenation + deoxygenation)
        """
        naturaloil_data = NaturalOil.data_energy_dict

        natural_oil_needs = 1 / 3 * naturaloil_data['calorific_value'] * naturaloil_data['molar_mass'] / \
                            (self.data_energy_dict['calorific_value']
                             * self.data_energy_dict['molar_mass'])

        return natural_oil_needs

    def get_theoretical_hydrogen_needs(self):
        """
       oil + 15H2 = 3fuel + 6H20 (hydrogenation + deoxygenation)
        """
        hydrogen_data = GaseousHydrogen.data_energy_dict

        gaseous_hydrogen_needs = 15 / 3 * hydrogen_data['calorific_value'] * hydrogen_data['molar_mass'] / \
                                 (self.data_energy_dict['calorific_value']
                                  * self.data_energy_dict['molar_mass'])

        return gaseous_hydrogen_needs

    def get_theoretical_water_prod(self):
        """
       oil + 15H2 = 3fuel + 6H20 (hydrogenation + deoxygenation)
        """
        water_molar_mass = Water.data_energy_dict['molar_mass']
        water_prod = (6 / 3) * water_molar_mass / (
                self.data_energy_dict['calorific_value'] * self.data_energy_dict['molar_mass'])

        return water_prod
