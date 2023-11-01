
from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from energy_models.core.techno_type.base_techno_models.high_heat_techno import highheattechno
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import GaseousHydrogen
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture

import numpy as np
import pandas as pd

class HydrogenBoilerHighHeat(highheattechno):

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs to produce 1kWh of heat
        """
        self.cost_details[f'{GaseousHydrogen.name}_needs'] = self.get_theoretical_hydrogen_needs()

        self.cost_details[f'{GaseousHydrogen.name}'] = \
            self.prices[f'{GaseousHydrogen.name}'] * \
            self.cost_details[f'{GaseousHydrogen.name}_needs'] / \
            self.cost_details['efficiency']

        # hydrogen_needs

        # output needed in this method is in $/kwh of heat
        # to do so I need to know how much hydrogen is used to produce 1kwh of heat (i need this information in kwh) : hydrogen_needs is in kwh of hydrogen/kwh of heat
        # kwh/kwh * price of hydrogen ($/kwh) : kwh/kwh * $/kwh  ----> $/kwh  : price of hydrogen is in self.prices[f'{GaseousHydrogen.name}']
        # and then we divide by efficiency
        return self.cost_details[f'{GaseousHydrogen.name}']

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        """

        self.compute_primary_energy_production()


        # Consumption

        self.consumption[f'{GaseousHydrogen.name} ({self.product_energy_unit})'] = self.cost_details[f'{GaseousHydrogen.name}_needs'] * \
            self.production[f'{hightemperatureheat.name} ({self.product_energy_unit})']
        #self.carbon_emissions
        # print('')
        # print(self.carbon_emissions.to_string())

        # print('')
        # print(self.energy_CO2_emissions.to_string())
        # CO2 production
        # self.production[f'{CarbonCapture.flue_gas_name} ({self.mass_unit})'] = GaseousHydrogen.data_energy_dict['CO2_per_use'] / \
        #                                                                        GaseousHydrogen.data_energy_dict['calorific_value'] * \
        #     self.consumption[f'{GaseousHydrogen.name} ({self.product_energy_unit})']

    # def compute_CO2_emissions_from_input_resources(self):
    #     '''
    #     Need to take into account CO2 from Gaseous Hydrogen production
    #     '''
    #
    #     self.carbon_emissions[GaseousHydrogen.name] = self.energy_CO2_emissions[GaseousHydrogen.name] * \
    #         self.cost_details[f'{GaseousHydrogen.name}_needs']
    #
    #     return self.carbon_emissions[f'{GaseousHydrogen.name}']

    def get_theoretical_hydrogen_needs(self):
        # we need as output kwh/kwh
        hydrogen_demand = self.techno_infos_dict['hydrogen_demand']

        hydrogen_needs = hydrogen_demand

        return hydrogen_needs

    def get_theoretical_co2_prod(self, unit='kg/kWh'):
        co2_captured__production = self.techno_infos_dict['co2_captured__production']
        heat_density = GaseousHydrogen.data_energy_dict['density']  # kg/m^3
        heat_calorific_value = GaseousHydrogen.data_energy_dict['calorific_value']  # kWh/kg

        co2_prod = co2_captured__production / (heat_density * heat_calorific_value)

        return co2_prod


    def configure_input(self, inputs_dict):
        '''
        Configure with inputs_dict from the discipline
        '''
        self.land_rate = inputs_dict['flux_input_dict']['land_rate']

    def compute_heat_flux(self):
        land_rate = self.land_rate
        heat_price = self.compute_other_primary_energy_costs()
        self.heat_flux = land_rate/heat_price
        self.heat_flux_distribution = pd.DataFrame({'years': self.cost_details['years'],
                                               'heat_flux': self.heat_flux})
        return self.heat_flux_distribution



    def grad_price_vs_energy_price_calc(self):
        '''
        Compute the gradient of global price vs energy prices
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        hydrogen_needs = self.get_theoretical_hydrogen_needs()
        efficiency = self.techno_infos_dict['efficiency']
        # print('hydrogen_needs')
        # print(hydrogen_needs)
        # print(efficiency)
        # m = {GaseousHydrogen.name: np.identity(len(self.years)) * hydrogen_needs / efficiency}
        #print(m)
        return {'natural_gas_resource': np.identity(len(self.years)) * hydrogen_needs / efficiency}


