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


from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.energy_models.solid_fuel import SolidFuel
from energy_models.core.techno_type.base_techno_models.syngas_techno import SyngasTechno
from energy_models.glossaryenergy import GlossaryEnergy


class CoalGasification(SyngasTechno):
    syngas_COH2_ratio = 47.0 / 22.0 * 100.0  # in %

    def get_fuel_needs(self):
        """
        Get the fuel needs for 1 kwh of the energy producted by the technology
        """
        if self.techno_infos_dict['fuel_demand'] != 0.0:
            fuel_need = self.check_energy_demand_unit(self.techno_infos_dict['fuel_demand_unit'],
                                                      self.techno_infos_dict['fuel_demand'])

        else:
            fuel_need = 0.0

        return fuel_need

    def compute_other_streams_needs(self):
        # in kwh of fuel by kwh of syngas
        self.cost_details[f'{SolidFuel.name}_needs'] = self.get_fuel_needs()


    def compute_byproducts_production(self):

        self.production_detailed[f'{CarbonCapture.flue_gas_name} ({GlossaryEnergy.mass_unit})'] = self.techno_infos_dict[
                                                                                            'CO2_from_production'] / \
                                                                                        self.data_energy_dict[
                                                                                            'calorific_value'] * \
                                                                                        self.production_detailed[
                                                                                            f'{SyngasTechno.energy_name} ({self.product_unit})']
