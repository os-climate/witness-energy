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
from energy_models.core.techno_type.base_techno_models.biomass_dry_techno import BiomassDryTechno
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
import pandas as pd
import numpy as np
from copy import deepcopy


class ManagedWood(BiomassDryTechno):

    def compute_other_primary_energy_costs(self):
        """
        Compute primary costs to produce 1kg of wood
        """

        self.cost_details['elec_needs'] = self.get_electricity_needs()
        self.cost_details[f'{Electricity.name}'] = list(
            self.prices[f'{Electricity.name}'] * self.cost_details['elec_needs'])

        return self.cost_details[f'{Electricity.name}']

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices 
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        elec_needs = self.get_electricity_needs()

        return {Electricity.name: np.identity(len(self.years)) * elec_needs}

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """
        name_residue = f'{self.energy_name}_residue (TWh)'
        name_wood = f'{self.energy_name}_wood (TWh)'
        name_non_energy = f'{self.energy_name}_non_energy (TWh)'
        name_tot = f'{self.energy_name}_tot (TWh)'

        self.compute_primary_energy_production()

        self.production_mix = pd.DataFrame({'years': self.years})

        managed_production = deepcopy(
            self.production[f'{BiomassDryTechno.energy_name} ({self.product_energy_unit})'])

        # compute production for non energy at year start with percentages
        residue_year_start_production = managed_production[0] * self.techno_infos_dict['residue_density_percentage'] * \
            (1 - self.techno_infos_dict['residue_percentage_for_energy'])
        wood_year_start_production = managed_production[0] * self.techno_infos_dict['non_residue_density_percentage'] * \
            (1 - self.techno_infos_dict['wood_percentage_for_energy'])

        # compute production dedicated to energy from residue
        self.production_mix[name_residue] = managed_production *\
            self.techno_infos_dict['residue_density_percentage'] - \
            residue_year_start_production
        # compute production dedicated to energy from wood
        self.production_mix[name_wood] = managed_production *\
            self.techno_infos_dict['non_residue_density_percentage'] - \
            wood_year_start_production
        # compute production dedicated to non energy
        self.production_mix[name_non_energy] = managed_production - \
            self.production_mix[name_residue] - \
            self.production_mix[name_wood]

        self.production_mix[name_tot] = managed_production

        # compute output production dedicated to energy
        self.production[f'{BiomassDryTechno.energy_name} ({self.product_energy_unit})'] = self.production_mix[name_residue] +\
            self.production_mix[name_wood]

        # compute electricity and consumption CO2 from biomass_dry for energy
        self.consumption[f'{Electricity.name} ({self.product_energy_unit})'] = self.cost_details['elec_needs'] * \
            self.production[f'{BiomassDryTechno.energy_name} ({self.product_energy_unit})']  # in kWH

        self.consumption[f'{CO2.name} ({self.mass_unit})'] = -self.techno_infos_dict['CO2_from_production'] / \
            self.data_energy_dict['high_calorific_value'] * \
            self.production[f'{BiomassDryTechno.energy_name} ({self.product_energy_unit})']

    def compute_CO2_emissions_from_input_resources(self):
        '''
        Need to take into account  CO2 from electricity/fuel production
        '''

        self.carbon_emissions[f'{Electricity.name}'] = self.energy_CO2_emissions[f'{Electricity.name}'] * \
            self.cost_details['elec_needs']

        return self.carbon_emissions[f'{Electricity.name}']

    def compute_price(self):
        prices = BiomassDryTechno.compute_price(self)
        managed_price = deepcopy(self.cost_details[self.name])

        residue_percent = self.techno_infos_dict['residue_density_percentage']
        wood_percent = self.techno_infos_dict['non_residue_density_percentage']

        wood_residue_percent = self.techno_infos_dict['wood_residue_price_percent_dif']

        # Price_tot = Price_residue * %res + Price_wood * %wood
        # Price_residue = %res_wood * Price_wood
        self.price_mix = pd.DataFrame({'years': self.years})
        self.price_mix[f'{BiomassDryTechno.energy_name}_wood'] = managed_price / \
            (wood_residue_percent * residue_percent + wood_percent)
        self.price_mix[f'{BiomassDryTechno.energy_name}_residue'] = wood_residue_percent * \
            self.price_mix[f'{BiomassDryTechno.energy_name}_wood']

        return prices

    def get_mean_age_over_years(self):

        mean_age_df = pd.DataFrame({'years': self.years})

        self.age_distrib_prod_df['age_x_prod'] = self.age_distrib_prod_df['age'] * \
            self.age_distrib_prod_df[f'distrib_prod ({self.product_energy_unit})']

        production = self.production_woratio[f'{self.energy_name} ({self.product_energy_unit})']

        # compute production for non energy at year start with percentages
        residue_year_start_production = production[0] * self.techno_infos_dict['residue_density_percentage'] * \
            (1 - self.techno_infos_dict['residue_percentage_for_energy'])
        wood_year_start_production = production[0] * self.techno_infos_dict['non_residue_density_percentage'] * \
            (1 - self.techno_infos_dict['wood_percentage_for_energy'])

        mean_age_df['mean age'] = self.age_distrib_prod_df.groupby(
            ['years'], as_index=False).agg({'age_x_prod': 'sum'})['age_x_prod'] / \
            (production + residue_year_start_production + wood_year_start_production)
        mean_age_df.replace([np.inf, -np.inf], np.nan, inplace=True)
        mean_age_df.fillna(0.0, inplace=True)

        return mean_age_df
