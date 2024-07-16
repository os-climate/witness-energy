'''
Copyright 2023 Capgemini

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
import pandas as pd

from energy_models.core.stream_type.energy_models.heat import mediumtemperatureheat
from energy_models.core.techno_type.base_techno_models.medium_heat_techno import (
    mediumheattechno,
)
from energy_models.glossaryenergy import GlossaryEnergy


class GeothermalHeat(mediumheattechno):
    # self.Mean_Temperature = 500
    # self.Output_Temperature =400
    def __init__(self, name):
        super().__init__(name)
        self.land_rate = None
        self.heat_flux = None
        self.heat_flux_distribution = None

    def compute_other_streams_needs(self):
        self.cost_details[f'{GlossaryEnergy.electricity}_needs'] = self.get_theoretical_electricity_needs() / self.cost_details['efficiency']
        
    def compute_byproducts_production(self):
        # Production
        carbon_production_factor = self.get_theoretical_co2_prod()
        self.production_detailed[f'{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit})'] = carbon_production_factor * \
                                                                               self.production_detailed[
                                                                                   f'{mediumtemperatureheat.name} ({self.product_unit})'] / \
                                                                               self.cost_details['efficiency']

    def get_theoretical_electricity_needs(self):
        mean_temperature = self.techno_infos_dict['mean_temperature']
        output_temperature = self.techno_infos_dict['output_temperature']
        COP = output_temperature / (output_temperature - mean_temperature)
        electricity_needs = 1 / COP  # (heating_space*heat_required_per_meter_square) / COP

        return electricity_needs

    @staticmethod
    def get_theoretical_steel_needs(self):
        """
        Page:21 #https://www.energy.gov/eere/geothermal/articles/life-cycle-analysis-results-geothermal-systems-comparison-other-power
        According to the www.energy.gov, Geothermal need 968 kg of copper for each MW implemented. Computing the need in Mt/MW
        """
        steel_need = self.techno_infos_dict['steel_needs'] / 1000 / 1000 / 1000

        return steel_need

    def configure_input(self, inputs_dict):
        '''
        Configure with inputs_dict from the discipline
        '''
        self.land_rate = inputs_dict['flux_input_dict']['land_rate']

    def compute_heat_flux(self):
        land_rate = self.land_rate
        self.heat_flux = land_rate / self.cost_details['energy_costs'].values
        self.heat_flux_distribution = pd.DataFrame({GlossaryEnergy.Years: self.cost_details[GlossaryEnergy.Years],
                                                    'heat_flux': self.heat_flux})
        return self.heat_flux_distribution
