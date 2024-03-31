'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/09-2023/11/15 Copyright 2023 Capgemini

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

from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.resources_models.water import Water
from energy_models.core.techno_type.base_techno_models.syngas_techno import SyngasTechno
from energy_models.glossaryenergy import GlossaryEnergy


class BiomassGasification(SyngasTechno):
    syngas_COH2_ratio = 26.0 / 31.0 * 100.0  # in %

    def compute_other_energies_needs(self):
        self.cost_details[f'{GlossaryEnergy.electricity}_needs'] = self.get_electricity_needs()
        # in kwh of fuel by kwh of syngas

        self.cost_details[f'{BiomassDry.name}_needs'] = self.techno_infos_dict['biomass_demand']


    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs which depends on the technology 
        """

        super().compute_other_primary_energy_costs()

        return self.cost_of_energies_usage[Electricity.name] + self.cost_of_energies_usage[BiomassDry.name]

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices 
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        elec_needs = self.get_electricity_needs()
        biomass_needs = self.techno_infos_dict['biomass_demand']

        efficiency = self.compute_efficiency()

        # methane_needs = self.get_theoretical_methane_needs()
        return {Electricity.name: np.identity(len(self.years)) * elec_needs,
                BiomassDry.name: np.diag(biomass_needs / efficiency)
                }

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """

        # Consumption
        self.consumption_detailed[f'{Electricity.name} ({self.product_energy_unit})'] = self.cost_details[
                                                                                            f'{GlossaryEnergy.electricity}_needs'] * \
                                                                                        self.production_detailed[
                                                                                            f'{SyngasTechno.energy_name} ({self.product_energy_unit})']  # in kWH
        self.consumption_detailed[f'{BiomassDry.name} ({self.product_energy_unit})'] = self.cost_details[
                                                                                           f'{BiomassDry.name}_needs'] * \
                                                                                       self.production_detailed[
                                                                                           f'{SyngasTechno.energy_name} ({self.product_energy_unit})']  # in kWH
        self.consumption_detailed[f'{Water.name} ({self.mass_unit})'] = self.techno_infos_dict['kgH20_perkgSyngas'] / \
                                                                        self.data_energy_dict['calorific_value'] * \
                                                                        self.production_detailed[
                                                                            f'{SyngasTechno.energy_name} ({self.product_energy_unit})']  # in kg

        self.compute_ghg_emissions(Methane.emission_name)

    def compute_CO2_emissions_from_input_resources(self):
        ''' 
        Need to take into account negative CO2 from biomass and positive from elec
        '''

        self.carbon_intensity[Electricity.name] = self.energy_CO2_emissions[Electricity.name] * \
                                                  self.cost_details[f'{GlossaryEnergy.electricity}_needs']

        self.carbon_intensity[BiomassDry.name] = self.energy_CO2_emissions[BiomassDry.name] * \
                                                 self.cost_details[f'{BiomassDry.name}_needs']

        return self.carbon_intensity[Electricity.name] + self.carbon_intensity[BiomassDry.name]
