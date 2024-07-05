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

from copy import deepcopy

import numpy as np
import pandas as pd

from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.core.techno_type.base_techno_models.biomass_dry_techno import (
    BiomassDryTechno,
)
from energy_models.glossaryenergy import GlossaryEnergy


class CropEnergy(BiomassDryTechno):
    LAND_SURFACE_FOR_FOOD_DF = 'land_surface_for_food_df'

    def __init__(self, name):
        BiomassDryTechno.__init__(self, name)
        self.invest_crop_industry = None
        self.land_surface_for_food = None
        self.residue_prod_from_food_surface = None
        self.production_mix = None
        self.price_mix = None

    def configure_parameters_update(self, inputs_dict):
        '''
        Configure with inputs_dict from the discipline and specifically the invest for food
        '''
        BiomassDryTechno.configure_parameters_update(self, inputs_dict)

        self.land_surface_for_food = inputs_dict[self.LAND_SURFACE_FOR_FOOD_DF]

    def compute_production(self):
        name_residue = f'{self.energy_name}_residue (TWh)'
        name_crop = f'{self.energy_name}_crop (TWh)'
        name_non_energy = f'{self.energy_name}_non_energy (TWh)'
        name_residue_non_energy = f'{self.energy_name}_residue_non_energy (TWh)'
        name_tot = f'{self.energy_name}_tot (TWh)'

        self.production_mix = pd.DataFrame({GlossaryEnergy.Years: self.years})

        # This model compute the production of crop and residue for energy
        crop_residue_energy_production = deepcopy(
            self.production_detailed[f'{BiomassDryTechno.energy_name} ({self.product_unit})'])

        # production of residue is the production from food surface and from
        # crop energy
        self.residue_prod_from_food_surface = self.compute_residue_from_food_investment()
        self.production_mix[name_residue] = self.residue_prod_from_food_surface + \
                                            self.techno_infos_dict['residue_density_percentage'] * \
                                            crop_residue_energy_production

        # compute production dedicated to energy from crop
        self.production_mix[name_crop] = crop_residue_energy_production * \
                                         (1 - self.techno_infos_dict['residue_density_percentage'])

        # compute production dedicated to non energy
        self.production_mix[name_non_energy] = self.land_surface_for_food['Agriculture total (Gha)'] * \
                                               self.techno_infos_dict['density_per_ha'] * \
                                               self.data_energy_dict['high_calorific_value'] * \
                                               (1 - self.techno_infos_dict['residue_density_percentage'])
        self.production_mix[name_residue_non_energy] = self.land_surface_for_food['Agriculture total (Gha)'] * \
                                                       self.techno_infos_dict['density_per_ha'] * \
                                                       self.data_energy_dict['high_calorific_value'] * \
                                                       (1 - self.techno_infos_dict['residue_percentage_for_energy']) * \
                                                       self.techno_infos_dict['residue_density_percentage']

        self.production_mix[name_tot] = self.production_mix[name_non_energy] + \
                                        self.production_mix[name_crop] + self.production_mix[name_residue]

        # compute output production dedicated to energy
        self.production_detailed[f'{BiomassDryTechno.energy_name} ({self.product_unit})'] = self.production_mix[
                                                                                                       name_residue] + \
                                                                                                   self.production_mix[
                                                                                                       name_crop]

    def compute_land_use(self):
        """
        Compute land use only for the crop energy (production * (1-residue_density))
        """
        density_per_ha = self.techno_infos_dict['density_per_ha']

        self.land_use[f'{self.name} (Gha)'] = \
            self.production_detailed[f'{self.energy_name} ({self.product_unit})'] * \
            (1 - self.techno_infos_dict['residue_density_percentage']) / \
            self.data_energy_dict['calorific_value'] / \
            density_per_ha

    def compute_price(self):
        '''
        Compute detailed price of  and residue
        '''
        prices = BiomassDryTechno.compute_price(self)

        # this model compute the crop + residue price for energy crop
        # Price_tot = Price_residue * residue_density_percentage + Price_crop * (1-residue_density_percentage)
        # Price_residue = Price_crop * crop_residue_price_percent_dif
        price_tot = self.cost_details[self.name]
        price_crop = price_tot / \
                     (1 + self.techno_infos_dict['residue_density_percentage'] *
                      (self.techno_infos_dict['crop_residue_price_percent_dif'] - 1))

        price_residue = price_crop * \
                        self.techno_infos_dict['crop_residue_price_percent_dif']

        # Price_residue = crop_residue_ratio * Price_crop

        # => Price_crop = Price_tot / ((1-ratio_prices)*crop_residue_ratio + ratio_prices)
        self.price_mix = pd.DataFrame({GlossaryEnergy.Years: self.years})
        self.price_mix[f'{BiomassDryTechno.energy_name}_crop'] = price_crop
        self.price_mix[f'{BiomassDryTechno.energy_name}_residue'] = price_residue

        return prices

    def compute_residue_from_food_investment(self):
        '''
        Compute residue part from the land surface for food.

        '''
        # compute residue part from food land surface for energy sector in Twh
        residue_production = self.land_surface_for_food['Agriculture total (Gha)'] * \
                             self.techno_infos_dict['residue_density_percentage'] * \
                             self.techno_infos_dict['density_per_ha'] * \
                             self.data_energy_dict['high_calorific_value'] * \
                             self.techno_infos_dict['residue_percentage_for_energy']

        return residue_production

    def compute_grad_dprod_dland_for_food(self):
        '''
        Compute gradient of production from land surface from food
        an identity matrice with the same scalar on diagonal

        '''
        # production = residue production from food + crop energy production
        # residue production from food = compute_residue_from_food_investment
        d_prod_dland_for_food = np.identity(len(self.years)) * \
                                self.techno_infos_dict['residue_density_percentage'] * \
                                self.techno_infos_dict['density_per_ha'] * \
                                self.data_energy_dict['high_calorific_value'] * \
                                self.techno_infos_dict['residue_percentage_for_energy']
        return d_prod_dland_for_food

    def compute_grad_dconso_dland_for_food(self):
        '''
        Compute gradient of production from land surface from food
        an identity matrice with the same scalar on diagonal

        '''
        # production = residue production from food + crop energy production
        # residue production from food = compute_residue_from_food_investment
        d_condo_dland_for_food = np.identity(len(self.years)) * \
                                 -self.techno_infos_dict['CO2_from_production'] * \
                                 self.techno_infos_dict['residue_density_percentage'] * \
                                 self.techno_infos_dict['density_per_ha'] * \
                                 self.techno_infos_dict['residue_percentage_for_energy']
        return d_condo_dland_for_food

    def compute_dlanduse_dinvest(self):
        """
        compute grad d_land_use / d_invest
        """

        dlanduse_dinvest = np.identity(len(self.years)) * 0
        for key in self.land_use:
            if key.startswith(self.name):
                if not (self.land_use[key] == np.array([0] * len(self.years))).all():
                    dlanduse_dinvest = self.dprod_dinvest * \
                                       (1 - self.techno_infos_dict['residue_density_percentage']) / \
                                       self.data_energy_dict['calorific_value'] / \
                                       self.techno_infos_dict['density_per_ha']

        return dlanduse_dinvest

    def compute_resources_needs(self):
        self.cost_details[f'{CO2.name}_needs'] = -self.techno_infos_dict['CO2_from_production'] / self.data_energy_dict['high_calorific_value']