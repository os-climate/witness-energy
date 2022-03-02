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

from energy_models.core.techno_type.base_techno_models.biogas_techno import BioGasTechno
from energy_models.core.stream_type.energy_models.wet_biomass import WetBiomass
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary

import numpy as np


class AnaerobicDigestion(BioGasTechno):

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs to produce 1kg of CH4
        """

        self.cost_details['elec_needs'] = self.get_electricity_needs()
        # in kwh of fuel by kwh of H2

        biomass_data = WetBiomass.data_energy_dict
        # Wet biomass_needs are in kg/m^3
        self.cost_details['wet_biomass_needs'] = self.techno_infos_dict['wet_biomass_needs'] / \
            self.data_energy_dict['density'] / \
            self.data_energy_dict['calorific_value']

        # Cost of electricity for 1 kWH of H2
        self.cost_details[Electricity.name] = list(self.prices[Electricity.name] * self.cost_details['elec_needs']
                                                   )
        # Cost of biomass is in $/kg
        self.cost_details[WetBiomass.name] = list(self.resources_prices[ResourceGlossary.WetBiomass['name']] * self.cost_details['wet_biomass_needs']
                                                  )

        return self.cost_details[Electricity.name] + self.cost_details[WetBiomass.name]

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices 
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        elec_needs = self.get_electricity_needs()

        return {Electricity.name: np.identity(len(self.years)) * elec_needs}

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """

        self.compute_primary_energy_production()

        # Consumption
        self.consumption[f'{WetBiomass.name} ({self.mass_unit})'] = self.cost_details['wet_biomass_needs'] * \
            self.production[f'{BioGasTechno.energy_name} ({self.product_energy_unit})']  # in kWH
        self.consumption[f'{Electricity.name} ({self.product_energy_unit})'] = self.cost_details['elec_needs'] * \
            self.production[f'{BioGasTechno.energy_name} ({self.product_energy_unit})']  # in kWH

    def compute_CO2_emissions_from_input_resources(self):
        '''
        Need to take into account  CO2 from electricity production and negative CO2 from biomass
        '''

        self.carbon_emissions[f'{WetBiomass.name}'] = self.resources_CO2_emissions[ResourceGlossary.WetBiomass['name']] * \
            self.cost_details['wet_biomass_needs']

        self.carbon_emissions[Electricity.name] = self.energy_CO2_emissions[Electricity.name] * \
            self.cost_details['elec_needs']

        return self.carbon_emissions[f'{WetBiomass.name}'] + self.carbon_emissions[Electricity.name]
