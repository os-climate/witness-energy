
from energy_models.core.stream_type.energy_models.heat import LowTemperatureHeat
from energy_models.core.techno_type.base_techno_models.heat_techno import LowHeatTechno
from energy_models.core.stream_type.resources_models.water import Water
from energy_models.core.stream_type.energy_models.electricity import Electricity

import numpy as np


class ElectricBoilerHeat(LowHeatTechno):

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs to produce 1kWh of heat
        """
        self.cost_details[f'{Water.name}_needs'] = self.get_theoretical_water_needs()
        self.cost_details[f'{Electricity.name}_needs'] = self.get_theoretical_electricity_needs()

        self.cost_details[f'{Water.name}'] = \
            self.resources_prices[f'{Water.name}'] * \
            self.cost_details[f'{Water.name}_needs'] / \
            self.cost_details['efficiency']

        self.cost_details[f'{Electricity.name}'] = \
            self.prices[Electricity.name] * \
            self.cost_details[f'{Electricity.name}_needs'] / \
            self.cost_details['efficiency']

        return self.cost_details[f'{Water.name}'] + \
            self.cost_details[f'{Electricity.name}']

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        elec_needs = self.get_theoretical_electricity_needs()
        efficiency = self.techno_infos_dict['efficiency']
        return {Electricity.name: np.identity(len(self.years)) * elec_needs / efficiency,
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

        self.production[f'{LowTemperatureHeat.name} ({self.mass_unit})'] = self.production[f'{LowTemperatureHeat.name} ({self.product_energy_unit})']

        # Consumption

        self.consumption[f'{Electricity.name} ({self.product_energy_unit})'] = self.cost_details[f'{Electricity.name}_needs'] * \
            self.production[f'{LowTemperatureHeat.name} ({self.product_energy_unit})']

        self.consumption[f'{Water.name} ({self.mass_unit})'] = self.cost_details[f'{Water.name}_needs'] * \
            self.production[f'{LowTemperatureHeat.name} ({self.product_energy_unit})']

    def get_theoretical_water_needs(self):
        """
        From Renewable Fuel Association (https://ethanolrfa.org/file/1795/waterusagenrel-1.pdf)
        3 to 4 gallons of water per gallon of ethanol produced

        Needs in kg of Water per kWh of Ethanol
        """
        water_demand = self.techno_infos_dict['water_demand']
        water_density = Water.data_energy_dict['density']  # kg/m3
        heat_density = LowTemperatureHeat.data_energy_dict['density']  # kg/m3

        water_needs = water_demand * water_density / heat_density
        return water_needs

    def get_theoretical_electricity_needs(self):
        """
        From Ethanol Today Online (http://www.ethanoltoday.com/index.php?option=com_content&task=view&id=5&fid=53&Itemid=6)
        Electricity usage there averaged 0.70 kilowatt hours per gallon of ethanol.
        """
        elec_demand = self.techno_infos_dict['elec_demand']
        heat_density = LowTemperatureHeat.data_energy_dict['density']  # kg/m3

        electricity_needs = elec_demand /heat_density

        return electricity_needs



