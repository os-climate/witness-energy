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


from energy_models.core.stream_type.energy_models.biodiesel import BioDiesel
from energy_models.core.stream_type.resources_models.glycerol import Glycerol
from energy_models.core.stream_type.resources_models.methanol import Methanol
from energy_models.core.stream_type.resources_models.natural_oil import NaturalOil
from energy_models.core.stream_type.resources_models.sodium_hydroxide import (
    SodiumHydroxide,
)
from energy_models.core.stream_type.resources_models.water import Water
from energy_models.core.techno_type.base_techno_models.biodiesel_techno import (
    BioDieselTechno,
)
from energy_models.glossaryenergy import GlossaryEnergy


class Transesterification(BioDieselTechno):
    """Reaction: in Mt: 1.23 oil + 0.1 methanol = 1.22 biodiesel + 0.12 glycerol or
    in kg 1.0082 oil + 0.082 methanol = 1 biodiesel + 0.0984 glycerol"""

    def compute_resources_needs(self):
        # need in kg/kwh biodiesel
        self.cost_details[f'{Methanol.name}_needs'] = self.get_theoretical_methanol_needs() / self.cost_details['efficiency']
        # need in kg oil/kWh biodiesel
        self.cost_details[f'{NaturalOil.name}_needs'] = self.get_theoretical_natural_oil_needs() / self.cost_details['efficiency']
        # need in kg/kwh biodiesel
        self.cost_details[f'{SodiumHydroxide.name}_needs'] = self.get_theoretical_sodium_hydroxide_needs() / self.cost_details['efficiency']
        # need in kg/kwh biodiesel
        self.cost_details[f'{Water.name}_needs'] = self.get_theoretical_water_needs() / self.cost_details['efficiency']
        # need in kWh/kwh biodiesel

    def compute_other_streams_needs(self):
        self.cost_details[f'{GlossaryEnergy.electricity}_needs'] = self.get_theoretical_electricity_needs() / self.cost_details['efficiency']

    def compute_byproducts_production(self):
        self.production_detailed[f'{Glycerol.name} ({GlossaryEnergy.mass_unit})'] = 0.12 * self.production_detailed[
            f'{BioDiesel.name} ({self.product_unit})'] / \
                                                                          self.data_energy_dict['calorific_value']

    def get_theoretical_methanol_needs(self):
        """
        Get methanol needs in kg methanol / kWh biodiesel
        in kg 1.0082 oil + 0.082 methanol = 1 biodiesel + 0.0984 glycerol
        for 1kWh equivalent of biodiesel: 10.362 kg oil + 0.842 kg of methanol = 10.2778 kg of biodiesel + 1.0109 kg of glycerol
        """
        biodiesel_calorific_value = self.data_energy_dict['calorific_value']

        methanol_needs = 0.0819672311 / biodiesel_calorific_value

        return methanol_needs

    def get_theoretical_natural_oil_needs(self):
        """
        Get NaturalOil needs in kg oil /kWh biodiesel
        in kg 1.0082 oil + 0.082 NaturalOil = 1 biodiesel + 0.0984 glycerol
        for 1kWh equivalent of biodiesel: 10.362 kg oil + 0.842 kg of NaturalOil = 10.2778 kg of biodiesel + 1.0109 kg of glycerol
        """
        biodiesel_calorific_value = self.data_energy_dict['calorific_value']

        natural_oil_needs = 1.008196721 / biodiesel_calorific_value

        return natural_oil_needs

    def get_theoretical_sodium_hydroxide_needs(self):
        """
        Get SodiumHydroxide needs in kg SodiumHydroxide /kWh biodiesel
        in kg 1.0082 oil + 0.082 SodiumHydroxide = 1 biodiesel + 0.0984 glycerol
        for 1kWh equivalent of biodiesel: 10.362 kg oil + 0.842 kg of SodiumHydroxide = 10.2778 kg of biodiesel + 1.0109 kg of glycerol
        """
        biodiesel_calorific_value = self.data_energy_dict['calorific_value']

        sodiumhydroxyde_needs = 0.01 / biodiesel_calorific_value

        return sodiumhydroxyde_needs

    def get_theoretical_water_needs(self):
        """
        Get water needs in kg water /kWh biodiesel
        in kg 1.0082 oil + 0.082 SodiumHydroxide = 1 biodiesel + 0.0984 glycerol
        for 1kWh equivalent of biodiesel: 10.362 kg oil + 0.842 kg of SodiumHydroxide = 10.2778 kg of biodiesel + 1.0109 kg of glycerol
        """
        biodiesel_calorific_value = self.data_energy_dict['calorific_value']

        water_needs = 0.017 / biodiesel_calorific_value

        return water_needs

    def get_theoretical_electricity_needs(self):
        """
        Get electricity needs in kWh elec /kWh biodiesel
        in kg 1.0082 oil + 0.082 SodiumHydroxide +0.02kWh elec= 1 biodiesel + 0.0984 glycerol
        for 1kWh equivalent of biodiesel: 10.362 kg oil + 0.842 kg of SodiumHydroxide + = 10.2778 kg of biodiesel + 1.0109 kg of glycerol
        """
        biodiesel_calorific_value = self.data_energy_dict['calorific_value']

        elec_needs = 0.02 / biodiesel_calorific_value

        return elec_needs
