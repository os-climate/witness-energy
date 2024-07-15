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
from energy_models.core.stream_type.carbon_models.nitrous_oxide import N2O
from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from energy_models.core.stream_type.energy_models.solid_fuel import SolidFuel
from energy_models.core.techno_type.base_techno_models.electricity_techno import (
    ElectricityTechno,
)
from energy_models.glossaryenergy import GlossaryEnergy


class CoalGen(ElectricityTechno):
    def compute_resources_needs(self):
        # need in kg/kWh
        self.cost_details[f"{GlossaryEnergy.WaterResource}_needs"] = self.techno_infos_dict['water_demand']

    def compute_other_streams_needs(self):
        # in kwh of fuel by kwh of electricity
        self.cost_details[f'{SolidFuel.name}_needs'] = self.techno_infos_dict['fuel_demand'] / \
                                                self.cost_details['efficiency']

    def compute_byproducts_production(self):
        elec_needs = self.get_electricity_needs()
        self.production_detailed[f'{ElectricityTechno.energy_name} ({self.product_unit})'] = \
            self.production_detailed[
                f'{ElectricityTechno.energy_name} ({self.product_unit})'] * (1.0 - elec_needs)
        self.production_detailed[f'{CarbonCapture.flue_gas_name} ({GlossaryEnergy.mass_unit})'] = self.techno_infos_dict[
                                                                                            'CO2_from_production'] * \
                                                                                        self.production_detailed[
                                                                                            f'{ElectricityTechno.energy_name} ({self.product_unit})']
        self.production_detailed[f'{hightemperatureheat.name} ({self.product_unit})'] = \
            self.consumption_detailed[f'{SolidFuel.name} ({self.product_unit})'] - \
            self.production_detailed[f'{ElectricityTechno.energy_name} ({self.product_unit})']

        self.compute_ghg_emissions(N2O.name, related_to=SolidFuel.name)

    def compute_dprod_dinvest(self, capex_list, invest_list, invest_before_year_start, techno_dict,
                              dcapex_list_dinvest_list):
        dprod_dinvest = ElectricityTechno.compute_dprod_dinvest(
            self, capex_list, invest_list, invest_before_year_start, techno_dict, dcapex_list_dinvest_list)
        elec_needs = self.get_electricity_needs()

        return dprod_dinvest * (1.0 - elec_needs)
