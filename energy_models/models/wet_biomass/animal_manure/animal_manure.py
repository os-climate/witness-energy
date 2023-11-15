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
from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.core.techno_type.base_techno_models.wet_biomass_techno import WetBiomassTechno
from energy_models.core.stream_type.energy_models.electricity import Electricity


class AnimalManure(WetBiomassTechno):

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs to produce 1kg of wood
        """

        self.cost_details['elec_needs'] = self.get_electricity_needs()
        self.cost_details[f'{Electricity.name}'] = list(
            self.prices[f'{Electricity.name}'] * self.cost_details['elec_needs'])

        return self.cost_details[f'{Electricity.name}']

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """

        
        self.consumption_detailed[f'{Electricity.name} (kWh)'] = self.cost_details['elec_needs'] * \
                                                                 self.production_detailed[f'{WetBiomassTechno.energy_name} (kWh)']  # in kWH

        self.production_detailed[f'{CO2.name} (kg)'] = self.techno_infos_dict['CO2_from_production'] / \
                                                       self.data_energy_dict['calorific_value'] * \
                                                       self.production_detailed[f'{WetBiomassTechno.energy_name} (kWh)']

    def compute_CO2_emissions_from_input_resources(self):
        '''
        Need to take into account  CO2 from electricity/fuel production
        '''

        self.carbon_intensity[f'{Electricity.name}'] = self.energy_CO2_emissions[f'{Electricity.name}'] * \
                                                       self.cost_details['elec_needs']

        return self.carbon_intensity[f'{Electricity.name}']
