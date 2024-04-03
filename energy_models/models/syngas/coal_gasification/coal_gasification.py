'''
Copyright 2022 Airbus SAS
Modifications on 2023/09/25-2023/11/16 Copyright 2023 Capgemini

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

import numpy as np

from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.energy_models.solid_fuel import SolidFuel
from energy_models.core.techno_type.base_techno_models.syngas_techno import SyngasTechno


class CoalGasification(SyngasTechno):
    syngas_COH2_ratio = 47.0 / 22.0 * 100.0  # in %

    def compute_other_energies_needs(self):
        # in kwh of fuel by kwh of syngas
        self.cost_details['solid_fuel_needs'] = self.get_fuel_needs()


    def compute_CO2_emissions_from_input_resources(self):
        ''' 
        Need to take into account negative CO2 from biomass and positive from elec
        '''

        self.carbon_intensity[SolidFuel.name] = self.energy_CO2_emissions[SolidFuel.name] * \
                                                self.cost_details['solid_fuel_needs']

        return self.carbon_intensity[SolidFuel.name]

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """

        self.consumption_detailed[f'{SolidFuel.name} ({self.product_energy_unit})'] = self.cost_details[
                                                                                          'solid_fuel_needs'] * \
                                                                                      self.production_detailed[
                                                                                          f'{SyngasTechno.energy_name} ({self.product_energy_unit})']  # in kWH

        # self.consumption[f'{hightemperatureheat.name} ({self.product_energy_unit})'] = self.cost_details['solid_fuel_needs'] * \
        #     self.production[f'{SyngasTechno.energy_name} ({self.product_energy_unit})']  # in kWH

        self.production_detailed[f'{CarbonCapture.flue_gas_name} ({self.mass_unit})'] = self.techno_infos_dict[
                                                                                            'CO2_from_production'] / \
                                                                                        self.data_energy_dict[
                                                                                            'calorific_value'] * \
                                                                                        self.production_detailed[
                                                                                            f'{SyngasTechno.energy_name} ({self.product_energy_unit})']
