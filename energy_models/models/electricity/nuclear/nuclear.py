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

from energy_models.core.techno_type.base_techno_models.electricity_techno import ElectricityTechno
from energy_models.core.stream_type.ressources_models.water import Water


class Nuclear(ElectricityTechno):

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs which depends on the technology
        """
        self.cost_details['uranium_fuel_needs'] = self.get_theoretical_uranium_fuel_needs(
        )
        self.cost_details['uranium fuel'] = list(self.ressources_prices['uranium fuel'] *
                                                 self.cost_details['uranium_fuel_needs'])

        self.cost_details['water_needs'] = self.get_theoretical_water_needs()
        self.cost_details[Water.name] = list(self.ressources_prices[Water.name] *
                                             self.cost_details['water_needs'])

        self.cost_details['waste_disposal'] = self.compute_nuclear_waste_disposal_cost()

        return self.cost_details['uranium fuel'] + self.cost_details[Water.name] + self.cost_details['waste_disposal']

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ?
        """
        self.compute_primary_energy_production()

        self.consumption[f'uranium fuel ({self.mass_unit})'] = self.cost_details['uranium_fuel_needs'] * \
            self.production[f'{ElectricityTechno.energy_name} ({self.product_energy_unit})']
        '''
        One tonne of natural uranium feed might end up: as 120-130 kg of uranium for power reactor fuel
        => 1 kg of fuel => 8.33 kg of ore
        '''
        self.consumption[f'uranium_resource'] = self.consumption[
            f'uranium fuel ({self.mass_unit})'] * 8.33
        water_needs = self.get_theoretical_water_needs()

        # uranium consumption
        self.consumption[f'{Water.name} ({self.mass_unit})'] = water_needs * \
            self.production[f'{ElectricityTechno.energy_name} ({self.product_energy_unit})']  # in Mt

    @staticmethod
    def get_theoretical_uranium_fuel_needs():
        """
        Get Uranium fuel needs in kg Uranium fuel /kWh electricty
        World Nuclear Association
        https://www.world-nuclear.org/information-library/economic-aspects/economics-of-nuclear-power.aspx
        * Prices are approximate and as of March 2017.
        At 45,000 MWd/t burn-up this gives 360,000 kWh electrical per kg, hence fuel cost = 0.39 ¢/kWh.

        One tonne of natural uranium feed might end up: as 120-130 kg of uranium for power reactor fuel
        => 1 kg of fuel => 8.33 kg of ore
        """
        uranium_fuel_needs = 1.0 / 360000  # kg of uranium_fuel needed for 1 kWh of electric

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

    def compute_price(self):
        """
        overloads techno_type compute price method to add the decommissioning_cost to Capex_init
        """
        self.techno_infos_dict['Capex_init'] += self.techno_infos_dict['decommissioning_cost']
        costs = ElectricityTechno.compute_price(self)
        return costs

