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
from energy_models.core.stream_type.energy_models.heat import LowTemperatureHeat
from energy_models.core.techno_type.base_techno_models.heat_techno import LowHeatTechno
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture

import numpy as np


class HeatPump(LowHeatTechno):
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


        self.cost_details[f'{Electricity.name}'] = \
            self.prices[Electricity.name] * \
            self.cost_details[f'{Electricity.name}_needs'] / \
            self.cost_details['efficiency']

        return self.cost_details[f'{Electricity.name}']

##    def grad_price_vs_energy_price(self):
##        '''
##        Compute the gradient of global price vs energy prices
##        Work also for total CO2_emissions vs energy CO2 emissions
##        '''
##        elec_needs = self.get_theoretical_electricity_needs()
##        biomass_needs = self.get_theoretical_biomass_needs()
##        efficiency = self.techno_infos_dict['efficiency']
##        return {Electricity.name: np.identity(len(self.years)) * elec_needs / efficiency,
##                BiomassDry.name: np.identity(len(self.years)) * biomass_needs / efficiency,
##                }
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
            self.production[f'{LowTemperatureHeat.name} ({self.product_energy_unit})'] / \
            self.cost_details['efficiency']

        # Consumption
        self.consumption[f'{Electricity.name} ({self.product_energy_unit})'] = self.cost_details[f'{Electricity.name}_needs'] * \
            self.production[f'{LowTemperatureHeat.name} ({self.product_energy_unit})'] / \
            self.cost_details['efficiency']

##        self.consumption[f'{BiomassDry.name} ({self.product_energy_unit})'] = self.cost_details[f'{BiomassDry.name}_needs'] * \
##            self.production[f'{Ethanol.name} ({self.product_energy_unit})'] / \
##            self.cost_details['efficiency']
##        self.consumption[f'{Water.name} ({self.mass_unit})'] = self.cost_details[f'{Water.name}_needs'] * \
##            self.production[f'{Ethanol.name} ({self.product_energy_unit})'] / \
##            self.cost_details['efficiency']

##    def compute_CO2_emissions_from_input_resources(self):
##        '''
##        Need to take into account CO2 from electricity/fuel production
##        '''
##
##        self.carbon_emissions[f'{Electricity.name}'] = self.energy_CO2_emissions[f'{Electricity.name}'] * \
##            self.cost_details[f'{Electricity.name}_needs'] / \
##            self.cost_details['efficiency']
##
##        self.carbon_emissions[BiomassDry.name] = self.energy_CO2_emissions[BiomassDry.name] * \
##            self.cost_details[f'{BiomassDry.name}_needs'] / \
##            self.cost_details['efficiency']
##
##        self.carbon_emissions[Water.name] = self.resources_CO2_emissions[Water.name] * \
##                                               self.cost_details[f'{Water.name}_needs'] / \
##                                               self.cost_details['efficiency']
##
##        return self.carbon_emissions[f'{Electricity.name}'] + self.carbon_emissions[f'{BiomassDry.name}'] + \
##               self.carbon_emissions[Water.name]
##
##    def get_theoretical_biomass_needs(self):
##        """
##        56 pounds of corn --> 17 pounds of captured CO2 + 2.9 gallons on Ethanol
##        Conversions:
##        - 1 gallon = 0.00378541 m3
##        - 1 pound = 0.45359237 kg
##        """
##        biomass_demand = self.techno_infos_dict['biomass_dry_demand']
##
##        ethanol_density = Ethanol.data_energy_dict['density']                       # kg/m3
##        ethanol_calorific_value = Ethanol.data_energy_dict['calorific_value']       # kWh/kg
##        biomass_calorific_value = BiomassDry.data_energy_dict['calorific_value']    # kWh/kg
##
##        biomass_needs = biomass_demand * biomass_calorific_value / (ethanol_density * ethanol_calorific_value)
##
##        return biomass_needs
##
##    def get_theoretical_water_needs(self):
##        """
##        From Renewable Fuel Association (https://ethanolrfa.org/file/1795/waterusagenrel-1.pdf)
##        3 to 4 gallons of water per gallon of ethanol produced
##
##        Needs in kg of Water per kWh of Ethanol
##        """
##        water_demand = self.techno_infos_dict['water_demand']
##        water_density = Water.data_energy_dict['density']                       # kg/m3
##        ethanol_density = Ethanol.data_energy_dict['density']                   # kg/m3
##        ethanol_calorific_value = Ethanol.data_energy_dict['calorific_value']   # kWh/kg
##
##        water_needs = water_demand * water_density / (ethanol_density * ethanol_calorific_value)
##        return water_needs


    def get_theoretical_heat_generated(self):
       heating_space = self.techno_infos_dict['heating_space']
       heat_required_per_meter_square = self.techno_infos_dict['heat_required_per_meter_square']                       # kg/m3
       heat_generated = heating_space * heat_required_per_meter_square
       return heat_generated
    def get_theoretical_electricity_needs(self):
        """
        From Ethanol Today Online (http://www.ethanoltoday.com/index.php?option=com_content&task=view&id=5&fid=53&Itemid=6)
        Electricity usage there averaged 0.70 kilowatt hours per gallon of ethanol.
        """
        elec_demand = self.techno_infos_dict['elec_demand']
        # COP = LowTemperatureHeat.data_energy_dict['COP']                   # kg/m3
        # heating_space = self.techno_infos_dict['heating_space']
        # heat_required_per_meter_square = self.techno_infos_dict['heat_required_per_meter_square']
        # #ethanol_calorific_value = HighTemperatureHeat.data_energy_dict['calorific_value']   # kWh/kg

        electricity_needs = elec_demand   # (heating_space*heat_required_per_meter_square) / COP

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
