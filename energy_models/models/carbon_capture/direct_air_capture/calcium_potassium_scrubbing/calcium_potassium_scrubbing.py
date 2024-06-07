'''
Copyright 2022 Airbus SAS
Modifications on 2023/09/19-2023/11/16 Copyright 2023 Capgemini

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

from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.resources_models.calcium_oxide import CalciumOxide
from energy_models.core.stream_type.resources_models.potassium_hydroxide import (
    PotassiumHydroxide,
)
from energy_models.core.stream_type.resources_models.resource_glossary import (
    ResourceGlossary,
)
from energy_models.core.techno_type.base_techno_models.carbon_capture_techno import (
    CCTechno,
)
from energy_models.glossaryenergy import GlossaryEnergy


class CalciumPotassium(CCTechno):

    def compute_resources_needs(self):
        self.cost_details[f'{ResourceGlossary.PotassiumResource}_needs'] = self.compute_potassium_need() / self.techno_infos_dict[
            GlossaryEnergy.EnergyEfficiency]
        self.cost_details[f'{ResourceGlossary.CalciumResource}_needs'] = self.compute_calcium_need() / self.techno_infos_dict[
            GlossaryEnergy.EnergyEfficiency]

    def get_heat_needs(self):
        """
        Get the heat needs for 1 kwh of the energy producted by the technology
        """

        if 'heat_demand' in self.techno_infos_dict:
            heat_need = self.check_energy_demand_unit(self.techno_infos_dict['heat_demand_unit'],
                                                      self.techno_infos_dict['heat_demand'])

        else:
            heat_need = 0.0

        return heat_need

    def compute_other_energies_needs(self):
        self.cost_details[f'{GlossaryEnergy.electricity}_needs'] = self.get_electricity_needs()
        self.cost_details[f'{Methane.name}_needs'] = self.get_heat_needs()

    def compute_production(self):


        self.production_detailed[f'{CarbonCapture.flue_gas_name} ({self.mass_unit})'] = self.cost_details[
                                                                                            f'{Methane.name}_needs'] * \
                                                                                        self.production_detailed[
                                                                                            f'{CCTechno.energy_name} ({self.product_energy_unit})'] * \
                                                                                        Methane.data_energy_dict[
                                                                                            GlossaryEnergy.CO2PerUse] / \
                                                                                        Methane.data_energy_dict[
                                                                                            'calorific_value']

    def compute_potassium_need(self):
        """
        'reaction': 'CO2 + 2KOH --> H2O + K2CO3'
        unit : kg_potassium/kg_CO2
        """
        # https://pubs.acs.org/doi/pdf/10.1021/acs.iecr.7b02613 amine
        # efficiency
        KOH_molar_mass = PotassiumHydroxide.data_energy_dict['molar_mass']
        CO2_molar_mass = CarbonCapture.data_energy_dict['molar_mass']

        KOH_need = 2 * KOH_molar_mass / CO2_molar_mass * \
                   (1 - self.techno_infos_dict['potassium_refound_efficiency'])

        return KOH_need

    def compute_calcium_need(self):
        """
        'reaction': 'K2CO3 + Ca(OH)2 --> 2KOH + CaCO3'
        unit : kg_calcium/kg_CO2
        """

        # efficiency
        CaO_molar_mass = CalciumOxide.data_energy_dict['molar_mass']
        CO2_molar_mass = CarbonCapture.data_energy_dict['molar_mass']

        CaO_need = (CaO_molar_mass / CO2_molar_mass) * \
                   (1 - self.techno_infos_dict['calcium_refound_efficiency'])

        return CaO_need
