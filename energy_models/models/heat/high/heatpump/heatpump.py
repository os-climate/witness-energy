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
from energy_models.core.stream_type.energy_models.heat import HighTemperatureHeat
from energy_models.core.techno_type.base_techno_models.heat_techno import HighHeatTechno
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture

import numpy as np

class HeatPump(HighHeatTechno):
    #self.Mean_Temperature = 500
    #self.Output_Temperature =400
    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs to produce 1kWh of Heat Pump Heat Generation
        """

        self.cost_details[f'{Electricity.name}_needs'] = self.get_theoretical_electricity_needs()


        self.cost_details[f'{Electricity.name}'] = \
            self.prices[Electricity.name] * \
            self.cost_details[f'{Electricity.name}_needs'] / \
            self.cost_details['efficiency']

        return self.cost_details[f'{Electricity.name}']


    def grad_price_vs_energy_price(self):
        elec_needs = self.get_theoretical_electricity_needs()
        heat_generated = self.get_theoretical_heat_generated()
        Mean_Temperature = HighTemperatureHeat.data_energy_dict['Mean_Temperature']
        Ambient_Temperature = HighTemperatureHeat.data_energy_dict['Output_Temperature']
        COP = Ambient_Temperature / (Mean_Temperature - Ambient_Temperature)
        efficiency = COP
        #efficiency = self.techno_infos_dict['COP']
        return {Electricity.name: np.identity(len(self.years)) * elec_needs / efficiency,
               HighTemperatureHeat.name: np.identity(len(self.years)) * heat_generated / efficiency,
               }

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        """

        self.compute_primary_energy_production()

        # Production
        carbon_production_factor = self.get_theoretical_co2_prod()
        self.production[f'{CarbonCapture.name} ({self.mass_unit})'] = carbon_production_factor * \
            self.production[f'{HighTemperatureHeat.name} ({self.product_energy_unit})'] / \
            self.cost_details['efficiency']

        # Consumption
        self.consumption[f'{Electricity.name} ({self.product_energy_unit})'] = self.cost_details[f'{Electricity.name}_needs'] * \
            self.production[f'{HighTemperatureHeat.name} ({self.product_energy_unit})'] / \
            self.cost_details['efficiency']

    # def get_theoretical_heat_generated(self):
    #    heating_space = self.techno_infos_dict['heating_space']
    #    heat_required_per_meter_square = self.techno_infos_dict['heat_required_per_meter_square']                       # kg/m3
    #    heat_generated = heating_space * heat_required_per_meter_square
    #    return heat_generated

    def get_theoretical_electricity_needs(self):
        #self.Mean_Temperature = 500
        #self.Output_Temperature = 400
        #elec_demand = self.techno_infos_dict['elec_demand']  # kWh/kWh
        #Mean_Temperature = HighTemperatureHeat.data_energy_dict['Mean_Temperature']
        #Ambient_Temperature = HighTemperatureHeat.data_energy_dict['Output_Temperature']
        COP = self.Output_Temperature/(self.Output_Temperature - self.Mean_Temperature)
        # COP = HighTemperatureHeat.data_energy_dict['COP']                   # kg/m3
        # heating_space = self.techno_infos_dict['heating_space']
        # heat_required_per_meter_square = self.techno_infos_dict['heat_required_per_meter_square']
        electricity_needs = 1 / COP   # (heating_space*heat_required_per_meter_square) / COP

        return electricity_needs

