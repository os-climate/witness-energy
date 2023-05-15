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
from energy_models.core.stream_type.energy_models.heat import MediumTemperatureHeat
from energy_models.core.techno_type.base_techno_models.heat_techno import MediumHeatTechno
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture

import numpy as np


class HeatPump(MediumHeatTechno):
    """
    From Renewable Fuels Association - https://ethanolrfa.org/ethanol-101/how-is-ethanol-made

        56 pounds of corn --> 17 pounds of captured CO2 + 2.9 gallons on Ethanol (+ corn residues)

    Conversions:
        - 1 gallon = 0.00378541 m3
        - 1 pound = 0.45359237 kg
    """
    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs to produce 1kWh of biodiesel
        """

        self.cost_details[f'{Electricity.name}_needs'] = self.get_theoretical_electricity_needs()

        #print('############', self.cost_details)


        self.cost_details[f'{Electricity.name}'] = \
            self.prices[Electricity.name] * \
            self.cost_details[f'{Electricity.name}_needs'] / \
            self.cost_details['efficiency']

        return self.cost_details[f'{Electricity.name}']

   # def grad_price_vs_energy_price(self):
   #     '''
   #     Compute the gradient of global price vs energy prices
   #     Work also for total CO2_emissions vs energy CO2 emissions
   #     '''
   #
   #     elec_needs = self.get_theoretical_electricity_needs()
   #     Mean_Temperature = MediumTemperatureHeat.data_energy_dict['Mean_Temperature']
   #     Ambient_Temperature = MediumTemperatureHeat.data_energy_dict['Output_Temperature']
   #     COP = Ambient_Temperature / (Mean_Temperature - Ambient_Temperature)
   #     efficiency = COP
   #     return {Electricity.name: np.identity(len(self.years)) * elec_needs / efficiency,
   #             BiomassDry.name: np.identity(len(self.years)) * biomass_needs / efficiency,
   #             }
##
##    def grad_price_vs_resources_price(self):
##        '''
##        Compute the gradient of global price vs resources prices
##        '''
##        efficiency = self.techno_infos_dict['efficiency']
##        water_needs = self.get_theoretical_water_needs()
##
##        return {Water.name: np.identity(len(self.years)) * water_needs / efficiency,
##                }

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        """

        self.compute_primary_energy_production()

        # Production
        carbon_production_factor = self.get_theoretical_co2_prod()
        self.production[f'{CarbonCapture.name} ({self.mass_unit})'] = carbon_production_factor * \
            self.production[f'{MediumTemperatureHeat.name} ({self.product_energy_unit})'] / \
            self.cost_details['efficiency']

        # Consumption
        self.consumption[f'{Electricity.name} ({self.product_energy_unit})'] = self.cost_details[f'{Electricity.name}_needs'] * \
            self.production[f'{MediumTemperatureHeat.name} ({self.product_energy_unit})'] / \
            self.cost_details['efficiency']


    def get_theoretical_electricity_needs(self):
        Mean_Temperature = self.techno_infos_dict['mean_temperature']
        Output_Temperature = self.techno_infos_dict['output_temperature']
        COP = Output_Temperature/(Output_Temperature - Mean_Temperature)
        electricity_needs = 1 / COP   # (heating_space*heat_required_per_meter_square) / COP

        return electricity_needs

##    def get_theoretical_co2_prod(self, unit='kg/kWh'):
##        """
##        56 pounds of corn --> 17 pounds of captured CO2 + 2.9 gallons on Ethanol
##
##        Conversions:
##        - 1 gallon = 0.00378541 m3
##        - 1 pound = 0.45359237 kg
##        """
##        co2_captured__production = self.techno_infos_dict['co2_captured__production']
##        ethanol_density = Ethanol.data_energy_dict['density']                       # kg/m3
##        ethanol_calorific_value = Ethanol.data_energy_dict['calorific_value']       # kWh/kg
##
##        co2_prod = co2_captured__production / (ethanol_density * ethanol_calorific_value)
##
##        return co2_prod
