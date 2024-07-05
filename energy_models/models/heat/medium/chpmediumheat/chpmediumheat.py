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


from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.energy_models.heat import mediumtemperatureheat
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.techno_type.base_techno_models.electricity_techno import (
    ElectricityTechno,
)
from energy_models.core.techno_type.base_techno_models.medium_heat_techno import (
    mediumheattechno,
)
from energy_models.glossaryenergy import GlossaryEnergy


class CHPMediumHeat(mediumheattechno):

    def compute_other_energies_needs(self):
        self.cost_details[f'{Methane.name}_needs'] = self.get_theoretical_methane_needs()


        # methane_needs

        # output needed in this method is in $/kwh of heat
        # to do so I need to know how much methane is used to produce 1kwh of heat (i need this information in kwh) : methane_needs is in kwh of methane/kwh of heat
        # kwh/kwh * price of methane ($/kwh) : kwh/kwh * $/kwh  ----> $/kwh  : price of methane is in self.prices[f'{Methane.name}']
        # and then we divide by efficiency

    def compute_production(self):
        # CO2 production
        self.production_detailed[f'{CarbonCapture.flue_gas_name} ({GlossaryEnergy.mass_unit})'] = Methane.data_energy_dict[
                                                                                            GlossaryEnergy.CO2PerUse] / \
                                                                                        Methane.data_energy_dict[
                                                                                            'calorific_value'] * \
                                                                                        self.consumption_detailed[
                                                                                            f'{Methane.name} ({self.product_unit})']

        self.production_detailed[f'{ElectricityTechno.energy_name} ({self.product_unit})'] = \
            (self.production_detailed[f'{mediumtemperatureheat.name} ({self.product_unit})'] /
             (1 - self.techno_infos_dict['efficiency'])) - self.production_detailed[
                f'{mediumtemperatureheat.name} ({self.product_unit})']

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
