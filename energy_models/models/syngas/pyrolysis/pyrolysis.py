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
from energy_models.core.techno_type.base_techno_models.syngas_techno import SyngasTechno
from energy_models.glossaryenergy import GlossaryEnergy


class Pyrolysis(SyngasTechno):
    syngas_COH2_ratio = 0.5 / 0.45 * 100.0  # in %

    def compute_resources_needs(self):
        # syngas produced in kg by 1kg of wood
        syngas_kg = 1.0 * self.techno_infos_dict['syngas_yield']

        # kwh produced by 1kg of wood

        syngas_kwh = self.data_energy_dict['calorific_value'] * syngas_kg

        # wood needs in kg to produce 1kWh of syngas
        self.cost_details[f"{GlossaryEnergy.WoodResource}_needs"] = 1 / syngas_kwh

    def compute_byproducts_production(self):

        self.production_detailed[f'{CarbonCapture.flue_gas_name} ({GlossaryEnergy.mass_unit})'] = self.techno_infos_dict[
                                                                                            'CO2_from_production'] / \
                                                                                        self.data_energy_dict[
                                                                                            'calorific_value'] * \
                                                                                        self.production_detailed[
                                                                                            f'{SyngasTechno.energy_name} ({self.product_unit})']

        self.production_detailed[f'char ({GlossaryEnergy.mass_unit})'] = self.production_detailed[
                                                                   f'{SyngasTechno.energy_name} ({self.product_unit})'] * \
                                                               self.techno_infos_dict['char_yield'] / \
                                                               self.techno_infos_dict['syngas_yield']

        self.production_detailed[f'bio_oil ({GlossaryEnergy.mass_unit})'] = self.production_detailed[
                                                                      f'{SyngasTechno.energy_name} ({self.product_unit})'] * \
                                                                  self.techno_infos_dict['bio_oil_yield'] / \
                                                                  self.techno_infos_dict['syngas_yield']
