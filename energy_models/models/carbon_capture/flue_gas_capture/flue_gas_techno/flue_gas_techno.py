'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2023/11/16 Copyright 2023 Capgemini

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

from energy_models.core.stream_type.energy_models.renewable import Renewable
from energy_models.core.techno_type.base_techno_models.carbon_capture_techno import CCTechno
from energy_models.glossaryenergy import GlossaryEnergy


class FlueGasTechno(CCTechno):

    def __init__(self, name):
        super().__init__(name)
        self.flue_gas_ratio = None
        self.fg_ratio_effect = None

    def get_electricity_needs(self):
        """
        Overloads techno type method to use electricity in coarse technologies for heat
        Get the electricity needs for 1 kwh of the energy producted by the technology
        """
        if self.techno_infos_dict['elec_demand'] != 0.0:
            elec_need = self.check_energy_demand_unit(self.techno_infos_dict['elec_demand_unit'],
                                                      self.techno_infos_dict['elec_demand'])

        else:
            elec_need = 0.0

        if 'heat_demand' in self.techno_infos_dict:
            heat_need = self.check_energy_demand_unit(self.techno_infos_dict['heat_demand_unit'],
                                                      self.techno_infos_dict['heat_demand'])

        else:
            heat_need = 0.0

        return elec_need + heat_need

    def configure_parameters_update(self, inputs_dict):

        CCTechno.configure_parameters_update(self, inputs_dict)
        self.flue_gas_ratio = inputs_dict[GlossaryEnergy.FlueGasMean].loc[
            inputs_dict[GlossaryEnergy.FlueGasMean][GlossaryEnergy.Years]
            <= self.year_end]
        # To deal quickly with l0 test
        if 'fg_ratio_effect' in inputs_dict:
            self.fg_ratio_effect = inputs_dict['fg_ratio_effect']
        else:
            self.fg_ratio_effect = True

    def compute_cost_of_other_energies_usage(self):
        self.cost_details[Renewable.name] = list(self.prices[Renewable.name] * self.cost_details['elec_needs'])

        self.cost_details[Renewable.name] *= self.compute_electricity_variation_from_fg_ratio(
            self.flue_gas_ratio[GlossaryEnergy.FlueGasMean].values, self.fg_ratio_effect)
    
    def compute_other_energies_needs(self):
        self.cost_details['elec_needs'] = self.get_electricity_needs() / self.cost_details['efficiency']

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs which depends on the technology
        """
        super().compute_other_primary_energy_costs()

        return self.cost_details[Renewable.name]

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices 
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        elec_needs = self.get_electricity_needs()
        efficency = self.compute_efficiency()

        return {Renewable.name: np.identity(
            len(self.years)) * elec_needs / efficency * self.compute_electricity_variation_from_fg_ratio(
            self.flue_gas_ratio[GlossaryEnergy.FlueGasMean].values, self.fg_ratio_effect),
                }

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        """

        # Consumption
        self.consumption_detailed[f'{Renewable.name} ({self.energy_unit})'] = self.cost_details['elec_needs'] * \
                                                                              self.production_detailed[
                                                                                  f'{CCTechno.energy_name} ({self.product_energy_unit})']

    def compute_capex(self, invest_list, data_config):
        capex_calc_list = super().compute_capex(invest_list, data_config)
        capex_calc_list *= self.compute_capex_variation_from_fg_ratio(
            self.flue_gas_ratio[GlossaryEnergy.FlueGasMean].values, self.fg_ratio_effect)

        return capex_calc_list
