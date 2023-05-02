
from energy_models.core.stream_type.energy_models.heat import MediumTemperatureHeat
from energy_models.core.techno_type.base_techno_models.heat_techno import MediumHeatTechno
from energy_models.core.stream_type.resources_models.water import Water
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture

import numpy as np


class NaturalGasMediumHeat(MediumHeatTechno):
    """
    From Renewable Fuels Association - https://heatrfa.org/ethanol-101/how-is-heat-made

        56 pounds of corn --> 17 pounds of captured CO2 + 2.9 gallons on Heat (+ corn residues)

    Conversions:
        - 1 gallon = 0.00378541 m3
        - 1 pound = 0.45359237 kg
    """

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs to produce 1kWh of biodiesel
        """
        self.cost_details[f'{Methane.name}_needs'] = self.get_theoretical_methane_needs()
        self.cost_details[f'{Water.name}_needs'] = self.get_theoretical_water_needs()
        self.cost_details[f'{Electricity.name}_needs'] = self.get_theoretical_electricity_needs()

        self.cost_details[f'{Methane.name}'] = \
            self.prices[f'{Methane.name}'] * \
            self.cost_details[f'{Methane.name}_needs'] / \
            self.cost_details['efficiency']

        self.cost_details[f'{Water.name}'] = \
            self.resources_prices[f'{Water.name}'] * \
            self.cost_details[f'{Water.name}_needs'] / \
            self.cost_details['efficiency']

        self.cost_details[f'{Electricity.name}'] = \
            self.prices[Electricity.name] * \
            self.cost_details[f'{Electricity.name}_needs'] / \
            self.cost_details['efficiency']

        return self.cost_details[f'{Methane.name}'] + self.cost_details[f'{Water.name}'] + \
               self.cost_details[f'{Electricity.name}']

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        elec_needs = self.get_theoretical_electricity_needs()
        methane_needs = self.get_theoretical_methane_needs()
        efficiency = self.techno_infos_dict['efficiency']
        return {Electricity.name: np.identity(len(self.years)) * elec_needs / efficiency,
                Methane.name: np.identity(len(self.years)) * methane_needs / efficiency,
                }

    def grad_price_vs_resources_price(self):
        '''
        Compute the gradient of global price vs resources prices
        '''
        efficiency = self.techno_infos_dict['efficiency']
        water_needs = self.get_theoretical_water_needs()

        return {Water.name: np.identity(len(self.years)) * water_needs / efficiency,
                }

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

        self.consumption[f'{Methane.name} ({self.product_energy_unit})'] = self.cost_details[f'{Methane.name}_needs'] * \
            self.production[f'{MediumTemperatureHeat.name} ({self.product_energy_unit})'] / \
            self.cost_details['efficiency']
        self.consumption[f'{Water.name} ({self.mass_unit})'] = self.cost_details[f'{Water.name}_needs'] * \
            self.production[f'{MediumTemperatureHeat.name} ({self.product_energy_unit})'] / \
            self.cost_details['efficiency']

    def compute_CO2_emissions_from_input_resources(self):
        '''
        Need to take into account CO2 from electricity/fuel production
        '''

        self.cost_details[f'{Electricity.name}_needs'] = self.get_theoretical_electricity_needs()

        self.carbon_emissions[f'{Electricity.name}'] = self.energy_CO2_emissions[f'{Electricity.name}'] * \
            self.cost_details[f'{Electricity.name}_needs'] / \
            self.cost_details['efficiency']

        self.carbon_emissions[Methane.name] = self.energy_CO2_emissions[Methane.name] * \
            self.cost_details[f'{Methane.name}_needs'] / \
            self.cost_details['efficiency']

        self.carbon_emissions[Water.name] = self.resources_CO2_emissions[Water.name] * \
                                               self.cost_details[f'{Water.name}_needs'] / \
                                               self.cost_details['efficiency']

        return self.carbon_emissions[f'{Electricity.name}'] + self.carbon_emissions[f'{Methane.name}'] + \
               self.carbon_emissions[Water.name]

    def get_theoretical_methane_needs(self):
        """
        56 pounds of corn --> 17 pounds of captured CO2 + 2.9 gallons on Ethanol
        Conversions:
        - 1 gallon = 0.00378541 m3
        - 1 pound = 0.45359237 kg
        """
        methane_demand = self.techno_infos_dict['methane_demand']

        heat_density = MediumTemperatureHeat.data_energy_dict['density']                       # kg/m3
        heat_calorific_value = MediumTemperatureHeat.data_energy_dict['calorific_value']       # kWh/kg
        methane_calorific_value = Methane.data_energy_dict['calorific_value']    # kWh/kg

        methane_needs = methane_demand * methane_calorific_value / (heat_density * heat_calorific_value)

        return methane_needs

    def get_theoretical_water_needs(self):
        """
        From Renewable Fuel Association (https://heatrfa.org/file/1795/waterusagenrel-1.pdf)
        3 to 4 gallons of water per gallon of heat produced

        Needs in kg of Water per kWh of Heat
        """
        water_demand = self.techno_infos_dict['water_demand']
        water_density = Water.data_energy_dict['density']                       # kg/m3
        heat_density = MediumTemperatureHeat.data_energy_dict['density']                   # kg/m3
        heat_calorific_value = MediumTemperatureHeat.data_energy_dict['calorific_value']   # kWh/kg

        water_needs = water_demand * water_density / (heat_density * heat_calorific_value)
        return water_needs

    def get_theoretical_electricity_needs(self):
        """
        From Ethanol Today Online (http://www.heattoday.com/index.php?option=com_content&task=view&id=5&fid=53&Itemid=6)
        Electricity usage there averaged 0.70 kilowatt hours per gallon of ethanol.
        """
        elec_demand = self.techno_infos_dict['elec_demand']
        heat_density = MediumTemperatureHeat.data_energy_dict['density']                   # kg/m3
        heat_calorific_value = MediumTemperatureHeat.data_energy_dict['calorific_value']   # kWh/kg

        electricity_needs = elec_demand / (heat_density * heat_calorific_value)

        return electricity_needs

    def get_theoretical_co2_prod(self, unit='kg/kWh'):
        """
        56 pounds of corn --> 17 pounds of captured CO2 + 2.9 gallons on Ethanol

        Conversions:
        - 1 gallon = 0.00378541 m3
        - 1 pound = 0.45359237 kg
        """
        co2_captured__production = self.techno_infos_dict['co2_captured__production']
        heat_density = MediumTemperatureHeat.data_energy_dict['density']                       # kg/m3
        heat_calorific_value = MediumTemperatureHeat.data_energy_dict['calorific_value']       # kWh/kg

        co2_prod = co2_captured__production / (heat_density * heat_calorific_value)

        return co2_prod
