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
import pandas as pd

from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from energy_models.core.techno_type.base_techno_models.electricity_techno import (
    ElectricityTechno,
)
from energy_models.glossaryenergy import GlossaryEnergy


class Nuclear(ElectricityTechno):
    URANIUM_RESOURCE_NAME = GlossaryEnergy.UraniumResource

    def compute_resources_needs(self):
        self.cost_details[f'{self.URANIUM_RESOURCE_NAME}_needs'] = self.get_theoretical_uranium_fuel_needs()
        self.cost_details[f"{GlossaryEnergy.WaterResource}_needs"] = self.get_theoretical_water_needs()

    def compute_specifif_costs_of_technos(self):
        self.specific_costs = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            'waste_disposal': self.compute_nuclear_waste_disposal_cost()
        })

    def compute_byproducts_production(self):
        self.production_detailed[f'{hightemperatureheat.name} ({self.product_unit})'] = 24000000.00 * \
                                                                                               self.consumption_detailed[
                                                                                                   f'{self.URANIUM_RESOURCE_NAME} ({GlossaryEnergy.mass_unit})']

        # self.production[f'{hightemperatureheat.name} ({self.product_unit})'] = (self.techno_infos_dict['heat_recovery_factor'] * \
        #       self.production[f'{ElectricityTechno.energy_name} ({self.product_unit})']) / \
        #       self.techno_infos_dict['efficiency']

    def get_theoretical_uranium_fuel_needs(self):
        """
        Get Uranium fuel needs in kg Uranium fuel /kWh electricty
        World Nuclear Association
        https://www.world-nuclear.org/information-library/economic-aspects/economics-of-nuclear-power.aspx
        * Prices are approximate and as of March 2017.
        At 45,000 MWd/t burn-up this gives 360,000 kWh electrical per kg, hence fuel cost = 0.39 ¢/kWh.

        One tonne of natural uranium feed might end up: as 120-130 kg of uranium for power reactor fuel
        => 1 kg of fuel => 8.33 kg of ore
        With a complete  fission, approx around 24,000,000 kWh of heat can be generated from 1 kg of uranium-235
        """
        uranium_fuel_needs = 1.0 / (24000000.00 * self.techno_infos_dict[
            'efficiency'])  # kg of uranium_fuel needed for 1 kWh of electric

        return uranium_fuel_needs

    @staticmethod
    def get_theoretical_water_needs():
        """
        The Nuclear Energy Institute estimates that, per megawatt-hour, a nuclear power reactor
        consumes between 1,514 and 2,725 litres of water.
        """
        water_needs = (1541 + 2725) / 2 / 1000

        return water_needs

    def compute_nuclear_waste_disposal_cost(self):
        """
        Computes the cost of waste disposal and decommissioning per kWh of produced electricity.
        Sources:
            - World Nuclear Association
            (https://world-nuclear.org/information-library/nuclear-fuel-cycle/nuclear-wastes/radioactive-waste-management.aspx,
        """
        waste_disposal_levy = self.techno_infos_dict['waste_disposal_levy']
        return waste_disposal_levy

    def compute_capex(self, invest_list, data_config):
        """
        overloads check_capex_unity that return the capex in $/MW to add the decommissioning cost
        decommissioning_cost unit is $/kW
        """
        expo_factor = self.compute_expo_factor(data_config)
        capex_init = self.check_capex_unity(data_config)

        # add decommissioning_cost
        capex_init += self.techno_infos_dict['decommissioning_cost'] * 1.0e3 \
                      / self.techno_infos_dict['full_load_hours'] \
                      / self.techno_infos_dict['capacity_factor']

        if expo_factor != 0.0:
            capacity_factor_list = None
            if 'capacity_factor_at_year_end' in data_config \
                    and 'capacity_factor' in data_config:
                capacity_factor_list = np.linspace(data_config['capacity_factor'],
                                                   data_config['capacity_factor_at_year_end'],
                                                   len(invest_list))

            capex_calc_list = []
            invest_sum = self.initial_production * capex_init
            capex_year = capex_init

            for i, invest in enumerate(invest_list):

                # below 1M$ investments has no influence on learning rate for capex
                # decrease
                if invest_sum.real < 10.0 or i == 0.0:
                    capex_year = capex_init
                    # first capex calculation
                else:
                    np.seterr('raise')
                    if capacity_factor_list is not None:
                        try:
                            ratio_invest = ((invest_sum + invest) / invest_sum *
                                            (capacity_factor_list[i] / data_config['capacity_factor'])) \
                                           ** (-expo_factor)

                        except:
                            raise Exception(
                                f'invest is {invest} and invest sum {invest_sum} on techno {self.name}')

                    else:
                        np.seterr('raise')
                        try:
                            # try to calculate capex_year "normally"
                            ratio_invest = ((invest_sum + invest) /
                                            invest_sum) ** (-expo_factor)

                            pass

                        except FloatingPointError:
                            # set invest as a complex to calculate capex_year as a
                            # complex
                            ratio_invest = ((invest_sum + np.complex128(invest)) /
                                            invest_sum) ** (-expo_factor)

                            pass
                        np.seterr('warn')

                    # Check that the ratio is always above 0.95 but no strict threshold for
                    # optim is equal to 0.92 when tends to zero:
                    if ratio_invest.real < 0.95:
                        ratio_invest = 0.9 + \
                                       0.05 * np.exp(ratio_invest - 0.9)
                    capex_year = capex_year * ratio_invest

                capex_calc_list.append(capex_year)
                invest_sum += invest

            if 'maximum_learning_capex_ratio' in data_config:
                maximum_learning_capex_ratio = data_config['maximum_learning_capex_ratio']
            else:
                # if maximum learning_capex_ratio is not specified, the learning
                # rate on capex ratio cannot decrease the initial capex mor ethan
                # 10%
                maximum_learning_capex_ratio = 0.9

            capex_calc_list = capex_init * (maximum_learning_capex_ratio + (
                    1.0 - maximum_learning_capex_ratio) * np.array(capex_calc_list) / capex_init)
        else:
            capex_calc_list = capex_init * np.ones(len(invest_list))

        return capex_calc_list.tolist()
