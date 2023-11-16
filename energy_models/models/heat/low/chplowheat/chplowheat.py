
from energy_models.core.stream_type.energy_models.heat import lowtemperatureheat
from energy_models.core.techno_type.base_techno_models.low_heat_techno import lowheattechno
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.techno_type.base_techno_models.electricity_techno import ElectricityTechno
import numpy as np


class CHPLowHeat(lowheattechno):

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs to produce 1kWh of heat
        """
        self.cost_details[f'{Methane.name}_needs'] = self.get_theoretical_methane_needs()
        self.cost_details[f'{Methane.name}'] = \
            self.prices[f'{Methane.name}'] * \
            self.cost_details[f'{Methane.name}_needs']

        # methane_needs

        # output needed in this method is in $/kwh of heat
        # to do so I need to know how much methane is used to produce 1kwh of heat (i need this information in kwh) : methane_needs is in kwh of methane/kwh of heat
        # kwh/kwh * price of methane ($/kwh) : kwh/kwh * $/kwh  ----> $/kwh  : price of methane is in self.prices[f'{Methane.name}']
        # and then we divide by efficiency
        return self.cost_details[f'{Methane.name}']

    def grad_price_vs_energy_price_calc(self):
        '''
        Compute the gradient of global price vs energy prices
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        methane_needs = self.get_theoretical_methane_needs()
        efficiency = self.techno_infos_dict['efficiency']

        return {
                'natural_gas_resource': np.identity(len(self.years)) * methane_needs / efficiency
                }

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        """

        

        # Consumption
        self.consumption_detailed[f'{Methane.name} ({self.product_energy_unit})'] = self.cost_details[f'{Methane.name}_needs'] * \
                                                                                    self.production_detailed[f'{lowtemperatureheat.name} ({self.product_energy_unit})']

        # CO2 production
        self.production_detailed[f'{CarbonCapture.flue_gas_name} ({self.mass_unit})'] = Methane.data_energy_dict['CO2_per_use'] / \
                                                                                        Methane.data_energy_dict['calorific_value'] * \
                                                                                        self.consumption_detailed[f'{Methane.name} ({self.product_energy_unit})']

        self.production_detailed[f'{ElectricityTechno.energy_name} ({self.product_energy_unit})'] = \
            (self.production_detailed[f'{lowtemperatureheat.name} ({self.product_energy_unit})'] /
             (1 - self.techno_infos_dict['efficiency'])) - self.production_detailed[f'{lowtemperatureheat.name} ({self.product_energy_unit})']

    def compute_CO2_emissions_from_input_resources(self):
        '''
        Need to take into account CO2 from Methane production
        '''

        self.carbon_intensity[Methane.name] = self.energy_CO2_emissions[Methane.name] * \
                                              self.cost_details[f'{Methane.name}_needs']

        return self.carbon_intensity[f'{Methane.name}']

    def get_theoretical_methane_needs(self):
        # we need as output kwh/kwh
        methane_demand = self.techno_infos_dict['methane_demand']

        methane_needs = methane_demand

        return methane_needs

    def get_theoretical_electricity_needs(self):
        # we need as output kwh/kwh
        elec_demand = self.techno_infos_dict['elec_demand']

        return elec_demand

    def get_theoretical_co2_prod(self, unit='kg/kWh'):
        co2_captured__production = self.techno_infos_dict['co2_captured__production']
        heat_density = Methane.data_energy_dict['density']  # kg/m^3
        heat_calorific_value = Methane.data_energy_dict['calorific_value']  # kWh/kg

        co2_prod = co2_captured__production / (heat_density * heat_calorific_value)

        return co2_prod


