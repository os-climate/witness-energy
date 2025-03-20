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

from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import (
    GaseousHydrogen,
)
from energy_models.core.stream_type.energy_models.hydrotreated_oil_fuel import (
    HydrotreatedOilFuel,
)
from energy_models.core.stream_type.resources_models.natural_oil import NaturalOil
from energy_models.core.techno_type.base_techno_models.hydrotreated_oil_fuel_techno import (
    HydrotreatedOilFuelTechno,
)
from energy_models.glossaryenergy import GlossaryEnergy


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

    def compute_resources_needs(self):
        naturaloil_data = NaturalOil.data_energy_dict
        self.cost_details[f'{NaturalOil.name}_needs'] = self.get_theoretical_natural_oil_needs() / naturaloil_data['calorific_value']

    def compute_other_streams_needs(self):
        self.cost_details[f'{GaseousHydrogen.name}_needs'] = self.get_theoretical_hydrogen_needs() / self.cost_details['efficiency']
        self.cost_details[f'{GlossaryEnergy.electricity}_needs'] = self.elec_consumption_factor

    def compute_byproducts_production(self):
        carbon_production_factor = self.get_theoretical_co2_prod()
        self.production_detailed[f'{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit})'] = carbon_production_factor * \
                                                                               self.production_detailed[
                                                                                   f'{HydrotreatedOilFuel.name} ({self.product_unit})'] / \
                                                                               self.cost_details['efficiency']

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
