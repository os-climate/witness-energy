
from energy_models.core.stream_type.energy_models.heat import LowTemperatureHeat
from energy_models.core.techno_type.base_techno_models.heat_techno import LowHeatTechno
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture

import numpy as np


class NaturalGasLowHeat(LowHeatTechno):


    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs to produce 1kWh of heat
        """
        self.cost_details[f'{Methane.name}_needs'] = self.get_theoretical_methane_needs()

        self.cost_details[f'{Methane.name}'] = \
            self.prices[f'{Methane.name}'] * \
            self.cost_details[f'{Methane.name}_needs'] / \
            self.cost_details['efficiency']

        return self.cost_details[f'{Methane.name}']

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        methane_needs = self.get_theoretical_methane_needs()
        efficiency = self.techno_infos_dict['efficiency']
        return {
                Methane.name: np.identity(len(self.years)) * methane_needs / efficiency
                }

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

        self.consumption[f'{Methane.name} ({self.product_energy_unit})'] = self.cost_details[f'{Methane.name}_needs'] * \
            self.production[f'{LowTemperatureHeat.name} ({self.product_energy_unit})']

    def compute_CO2_emissions_from_input_resources(self):
        '''
        Need to take into account CO2 from fuel production
        '''

        self.carbon_emissions[Methane.name] = self.energy_CO2_emissions[Methane.name] * \
            self.cost_details[f'{Methane.name}_needs'] / \
            self.cost_details['efficiency']

        return self.carbon_emissions[f'{Methane.name}']

    def get_theoretical_methane_needs(self):

        methane_demand = self.techno_infos_dict['methane_demand']

        heat_density = Methane.data_energy_dict['density']                       # kg/m3
        #heat_calorific_value = Methane.data_energy_dict['calorific_value']       # kWh/kg
       # methane_calorific_value = Methane.data_energy_dict['calorific_value']    # kWh/kg
        cost_details = Methane.data_energy_dict['cost_details']

        #methane_needs = methane_demand * methane_calorific_value / (heat_density * heat_calorific_value)
        methane_needs = (methane_demand / heat_density) * cost_details
        return methane_needs



    def get_theoretical_co2_prod(self, unit='kg/kWh'):

        co2_captured__production = self.techno_infos_dict['co2_captured__production']
        heat_density = Methane.data_energy_dict['density']                       # kg/Nm3
        heat_calorific_value = Methane.data_energy_dict['calorific_value']       # kWh/kg

        co2_prod = co2_captured__production / (heat_density * heat_calorific_value)

        return co2_prod
