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


from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.techno_type.base_techno_models.carbon_capture_techno import (
    CCTechno,
)
from energy_models.glossaryenergy import GlossaryEnergy


class Amine(CCTechno):
    def get_heat_needs(self):
        """
        Get the heat needs for 1 kwh of the energy producted by the technology
        """

        if 'heat_demand' in self.inputs['techno_infos_dict']:
            heat_need = self.check_energy_demand_unit(self.inputs['techno_infos_dict']['heat_demand_unit'],
                                                      self.inputs['techno_infos_dict']['heat_demand'])

        else:
            heat_need = 0.0

        return heat_need

    def compute_other_streams_needs(self):
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.electricity}_needs'] = self.get_electricity_needs()
        self.outputs[f"{GlossaryEnergy.TechnoDetailedPricesValue}:{Methane.name}_needs"] = self.get_heat_needs()
        
    def compute_resources_needs(self):
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.AmineResource}_needs'] = self.compute_amine_need() / self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:efficiency']

    def compute_scope_2_emissions(self):
        '''
        Need to take into account  CO2 from Methane and electricity consumption
        '''

        self.outputs[f'CO2_emissions_detailed:{Methane.name}'] = self.inputs[f'{GlossaryEnergy.StreamsCO2EmissionsValue}:{Methane.name}'] * self.outputs[f"{GlossaryEnergy.TechnoDetailedPricesValue}:{Methane.name}_needs"]

        self.outputs[f'CO2_emissions_detailed:{GlossaryEnergy.electricity}'] = self.inputs[f'{GlossaryEnergy.StreamsCO2EmissionsValue}:{GlossaryEnergy.electricity}'] * self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.electricity}_needs']

        self.outputs[f'CO2_emissions_detailed:{GlossaryEnergy.AmineResource}'] = self.inputs[f'{GlossaryEnergy.RessourcesCO2EmissionsValue}:{GlossaryEnergy.AmineResource}'] * \
                                                                self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.AmineResource}_needs']
        self.outputs['CO2_emissions_detailed:Scope 2'] = self.outputs[f'CO2_emissions_detailed:{Methane.name}'] + self.outputs[f'CO2_emissions_detailed:{GlossaryEnergy.electricity}'] + self.outputs[f'CO2_emissions_detailed:{GlossaryEnergy.AmineResource}'] - 1.0

    def compute_byproducts_production(self):
        self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:{CarbonCapture.flue_gas_name} ({GlossaryEnergy.mass_unit})'] = \
            self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{Methane.name}_needs'] * \
            self.outputs[f'{GlossaryEnergy.TechnoProductionWithoutRatioValue}:{CCTechno.energy_name} ({self.product_unit})'] * \
            Methane.data_energy_dict[GlossaryEnergy.CO2PerUse] / Methane.data_energy_dict['calorific_value']

    def compute_amine_need(self):
        """
        'reaction': 'RNH2(Amine) + CO2 <--> (RNHCOO-) + (H+)'
        unit : kg_Amine/kg_CO2
        """
        # Buijs, W. and De Flart, S., 2017.
        # Direct air capture of CO2 with an amine resin: A molecular modeling study of the CO2 capturing process.
        # Industrial & engineering chemistry research, 56(43), pp.12297-12304.
        # https://pubs.acs.org/doi/pdf/10.1021/acs.iecr.7b02613 amine
        # efficiency
        CO2_mol_per_kg_amine = 1.1
        CO2_molar_mass = 44.0

        kg_CO2_per_kg_amine = CO2_mol_per_kg_amine * CO2_molar_mass

        return 1 / kg_CO2_per_kg_amine
