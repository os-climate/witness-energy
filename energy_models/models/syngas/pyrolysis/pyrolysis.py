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


from energy_models.core.techno_type.base_techno_models.syngas_techno import SyngasTechno
from energy_models.glossaryenergy import GlossaryEnergy


class Pyrolysis(SyngasTechno):
    syngas_COH2_ratio = 0.5 / 0.45 * 100.0  # in %

    def compute_resources_needs(self):
        # syngas produced in kg by 1kg of wood
        syngas_kg = 1.0 * self.inputs['techno_infos_dict']['syngas_yield']

        # kwh produced by 1kg of wood

        syngas_kwh = self.inputs['data_energy_dict']['calorific_value'] * syngas_kg

        # wood needs in kg to produce 1kWh of syngas
        self.outputs[f"{GlossaryEnergy.TechnoDetailedPricesValue}:{GlossaryEnergy.WoodResource}_needs"] = 1 / syngas_kwh

    def compute_co2_from_flue_gas_intensity_scope_1(self):
        return self.inputs['techno_infos_dict']['CO2_flue_gas_intensity_by_prod_unit'] / self.inputs['data_energy_dict']['calorific_value']

    def compute_byproducts_production(self):

        self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:char ({GlossaryEnergy.mass_unit})'] = self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:'
                                                                   f'{SyngasTechno.stream_name} ({self.product_unit})'] * \
                                                                                                          self.inputs['techno_infos_dict']['char_yield'] / \
                                                                                                          self.inputs['techno_infos_dict']['syngas_yield']

        self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:bio_oil ({GlossaryEnergy.mass_unit})'] = self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:'
                                                                      f'{SyngasTechno.stream_name} ({self.product_unit})'] * \
                                                                                                             self.inputs['techno_infos_dict']['bio_oil_yield'] / \
                                                                                                             self.inputs['techno_infos_dict']['syngas_yield']
