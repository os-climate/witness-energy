'''
Copyright 2022 Airbus SAS
Modifications on 2023/10/23-2023/11/16 Copyright 2023 Capgemini

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

from energy_models.core.stream_type.base_stream import BaseStream
from energy_models.glossaryenergy import GlossaryEnergy


class CarbonUtilization(BaseStream):
    name = 'carbon_utilization'
    food_storage_name = 'CO2 from Food Storage'
    unit = 'Mt'
    default_techno_list = ['food_storage_applications.AlgaeCultivation',
                           'food_storage_applications.BeverageCarbonation',
                           'food_storage_applications.CarbonatedWater',
                           'food_storage_applications.FoodStorageApplicationsTechno',
                           ]
    # Data dict from CO2 dioxyde
    data_energy_dict = {'maturity': 5,
                        'density': 1.98,
                        'density_unit': 'kg/m^3',
                        'molar_mass': 44.01,
                        'molar_mass_unit': 'g/mol',
                        # Calorific values set to 1.0 for the calculation of transport cost (in $/kWh)
                        # Since it is not used as an energy source
                        'calorific_value': 1.0,
                        'calorific_value_unit': 'kWh/kg',
                        'high_calorific_value': 1.0,
                        'high_calorific_value_unit': 'kWh/kg'}

    def __init__(self, name):
        BaseStream.__init__(self, name)

        self.food_storage_percentage = None
        self.carbon_utilization_type = None
        self.food_storage_production = None
        self.food_storage_prod_ratio = None
        self.fs_ratio = None
        self.subelements_list_fgc = []
        self.subelements_list_dac = []
        # self.production_f = None
        # self.consumption_fgc = None
        self.sub_production_dict = {}
        self.sub_consumption_dict = {}
        self.production_fsa = None
        self.consumption_fsa = None

    def configure_parameters_update(self, inputs_dict):
        self.subelements_list = inputs_dict[GlossaryEnergy.techno_list]
        BaseStream.configure_parameters_update(self, inputs_dict)
        self.food_storage_production = inputs_dict['food_storage_production'][self.food_storage_name].values
        self.food_storage_prod_ratio = inputs_dict['food_storage_prod_ratio']

        self.subelements_list_fgc = []
        self.subelements_list_dac = []
        for itm in self.subelements_list:
            if 'food_storage' in itm:
                self.subelements_list_fgc.append(itm)
            else:
                self.subelements_list_dac.append(itm)

    def compute(self, inputs, exp_min=True):
        '''
        Specific compute to handle the number of values in the return out of compute_production
        '''

        _, self.consumption_woratio, _, self.carbon_utilization_type_woratio, self.food_storage_percentage_woratio, self.fs_ratio_woratio = self.compute_production(
            self.sub_production_dict, self.sub_consumption_woratio_dict)

        self.production, self.consumption, self.production_by_techno, self.carbon_utilization_type, self.food_storage_percentage, self.fs_ratio = self.compute_production(
            self.sub_production_dict, self.sub_consumption_dict)

        self.production_fsa, self.consumption_fsa = self.compute_production_fsa(
            self.sub_production_dict, self.sub_consumption_dict)

        self.compute_price(exp_min=exp_min)

        self.aggregate_land_use_required()

        self.compute_energy_type_capital(inputs)

        return self.total_prices, self.production, self.consumption, self.consumption_woratio, self.mix_weights



    def compute_production_fsa(self,sub_production_dict, sub_consumption_dict):
        # sub_production_dict = self.sub_production_dict
        # sub_consumption_dict = self.sub_consumption_dict
        base_df = pd.DataFrame({GlossaryEnergy.Years: self.years})
        # production_fsa = base_df.copy(deep=True)
        # consumption_fsa = base_df.copy(deep=True)
        production_by_techno_fsa = base_df.copy(deep=True)

        production_fsa = base_df.copy(deep=True)
        consumption_fsa = base_df.copy(deep=True)
        production_by_techno_dac = base_df.copy(deep=True)
        carbon_utilization_type = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                             'food storage': 0.0,
                                             'FSA': 0.0,
                                             'food_storage_limited': 0.0})
        food_storage_percentage = None
        fs_ratio = None
        diff_food_storage = self.food_storage_production - \
                       carbon_utilization_type['food storage'].values
        if min(diff_food_storage.real) < 0:
            if carbon_utilization_type['food storage'].values.dtype != self.food_storage_production.dtype:
                self.food_storage_production = self.food_storage_production.astype(
                    carbon_utilization_type['food storage'].values.dtype)
            fs_ratio = np.divide(
                self.food_storage_production, carbon_utilization_type['food storage'].values, where=carbon_utilization_type['food storage'].values != 0.0, out=np.zeros_like(self.food_storage_production))
            food_storage_percentage = self.compute_food_storage_with_exp_min(
                fs_ratio)

        else:
            carbon_utilization_type['food storage limited'] = carbon_utilization_type['food storage']

        for element in self.subelements_list_fgc:

            if element.startswith('food_storage_applications') and min(diff_food_storage.real) < 0:
                factor = food_storage_percentage
            else:
                factor = 1.0
            production_fsa, consumption_fsa = self.compute_other_consumption_production(
                element, sub_production_dict, sub_consumption_dict, production_fsa, consumption_fsa, factor=factor)

        for element in self.subelements_list_dac:
            if element.startswith('food_storage_applications') and min(diff_food_storage.real) < 0:
                factor = food_storage_percentage
            else:
                factor = 1.0
            production_fsa, consumption_fsa = self.compute_other_consumption_production(
                element, sub_production_dict, sub_consumption_dict, production_fsa, consumption_fsa, factor=factor)
        return production_fsa, consumption_fsa
    def compute_production(self, sub_production_dict, sub_consumption_dict):
        '''
        Specific compute energy production where we compute carbon captured from flue gas
        '''

        # Initialize dataframe out
        base_df = pd.DataFrame({GlossaryEnergy.Years: self.years})
        production = base_df.copy(deep=True)
        consumption = base_df.copy(deep=True)
        production_by_techno = base_df.copy(deep=True)

        carbon_utilization_type = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                             'food storage': 0.0,
                                             'FSA': 0.0,
                                             'food_storage_limited': 0.0})
        food_storage_percentage = None
        fs_ratio = None

        production[f'{self.name}'] = 0.
        for element in self.subelements_list:
            production_by_techno[f'{self.name} {element} ({self.unit})'] = sub_production_dict[
                element][f'{self.name} ({self.unit})'].values
            production[
                f'{self.name}'] += production_by_techno[f'{self.name} {element} ({self.unit})'].values

            if element.startswith('food_storage_applications'):
                carbon_utilization_type['food storage'] += production_by_techno[
                    f'{self.name} {element} ({self.unit})'].values
            # else:
            #     carbon_utilization_type['DAC'] += production_by_techno[
            #         f'{self.name} {element} ({self.unit})'].values

        diff_food_storage = self.food_storage_production - \
            carbon_utilization_type['food storage'].values

        # Means that we capture more flue gas than available
        if min(diff_food_storage.real) < 0:
            if carbon_utilization_type['food storage'].values.dtype != self.food_storage_production.dtype:
                self.food_storage_production = self.food_storage_production.astype(
                    carbon_utilization_type['food storage'].values.dtype)
            fs_ratio = np.divide(
                self.food_storage_production, carbon_utilization_type['food storage'].values, where=carbon_utilization_type['food storage'].values != 0.0, out=np.zeros_like(self.food_storage_production))
            food_storage_percentage = self.compute_food_storage_with_exp_min(
                fs_ratio)
            carbon_utilization_type['food storage limited'] = carbon_utilization_type['food storage'] * \
                food_storage_percentage
            production[f'{self.name}'] = carbon_utilization_type['food storage limited'] + \
                carbon_utilization_type['FSA']

        else:
            carbon_utilization_type['food storage limited'] = carbon_utilization_type['food storage']

        # Divide the prod or the cons  if element is carbon capture
        for element in self.subelements_list:
            if element.startswith('food_storage_applications') and min(diff_food_storage.real) < 0:
                factor = food_storage_percentage
            else:
                factor = 1.0
            production_by_techno[f'{self.name} {element} ({self.unit})'] = sub_production_dict[
                element][f'{self.name} ({self.unit})'].values * factor
            production, consumption = self.compute_other_consumption_production(
                element, sub_production_dict, sub_consumption_dict, production, consumption, factor=factor)

        return production, consumption, production_by_techno, carbon_utilization_type, food_storage_percentage, fs_ratio



    def compute_food_storage_with_exp_min(self, fs_perc):

        f = 1.0 - fs_perc
        min_prod = 0.001
        f[f < np.log(1e-30) * min_prod] = np.log(1e-30) * min_prod

        f_limited = np.maximum(min_prod / 10.0 * (9.0 + np.exp(np.minimum(f, min_prod) / min_prod)
                                                  * np.exp(-1)), f)
        return 1.0 - f_limited

    def compute_dfood_storage_with_exp_min(self, fs_ratio):

        f = 1.0 - fs_ratio
        min_prod = 0.001
        dfood_storage = np.ones(len(fs_ratio))
        if f.min() < min_prod:
            f[f < np.log(1e-30) * min_prod] = np.log(1e-30) * min_prod
            dfood_storage[f < min_prod] = np.exp(
                f[f < min_prod] / min_prod) * np.exp(-1) / 10.0
        return dfood_storage

    def aggregate_land_use_required(self):
        '''
        Aggregate into an unique dataframe of information of sub technology about land use required
        '''

        for element in self.sub_land_use_required_dict.values():

            element_columns = list(element)
            element_columns.remove(GlossaryEnergy.Years)

            for column_df in element_columns:
                if column_df.startswith('food_storage_applications') and self.food_storage_percentage is not None:
                    self.land_use_required[column_df] = element[column_df] * \
                        self.food_storage_percentage
                else:
                    self.land_use_required[column_df] = element[column_df]

    def compute_grad_element_mix_vs_prod(self, production_by_techno, elements_dict, exp_min=True, min_prod=1e-3):
        '''
        Ex : p1, p2 and p3 only p1 and p2 are flue gas , p1 is prod used for techno mix and prod1 is the disc input
        techno_mix(p1) = p1/(p1+p2+p3)
        ptot = p1 + p2 + p3
        for dpi/dpi
            Old : dtechno_mix(p1)/dprod1 = dp1(ptot-p1)/ptot**2
                with p1 = fexp(prod1)
                    dp1/dprod1 = 1.0*f'exp(prod1)
                    dp2/dprod1 = 0.0
            New : dtechno_mix(p1)/dprod1 = dp1/ptot-(dp1+dp2)p1/ptot**2 = dp1(ptot-p1)/ptot**2 -dp2p1/ptot**2
                with p1 = fexp(pbis1)
                    pbis1 = prod1*fg_perc = prod1*fexpp(fg_prod/(prod1+prod2))
                    dp1/dprod1 = f'exp(pbis1)*dpbis1 = f'exp(pbis1)*(fexpp(fg_ratio) + prod1*f'expp(fg_ratio)*dfg_ratio
                               = dp1old * (fexpp(fg_ratio) + prod1*f'expp(fg_ratio)*dfg_ratio
                    dfg_ratio = -fg_prod/(prod1+prod2)**2
                    dp2/dprod1 != 0.0
                    dp2/dprod1 = f'exp(pbis2)*dpbis2 =f'exp(pbis2)*prod2*f'expp(fg_ratio)*dfg_ratio

            dtechno_mix(p1)/dprod1 = dtechno_mix(p1)/dprod1old*(fexpp(fg_ratio) + prod1*f'expp(fg_ratio)*dfg_ratio -dp2p1/ptot**2

        for dpi/dpj

            Old : dtechno_mix(p2)/dprod1 = -p2dp1/ptot**2
                with dp1/dprod1 = 1.0*f'exp(prod1)
            New :  dtechno_mix(p2)/dprod1 = -p2dp1/ptot**2 -p2dp2/ptot**2

                with
                dp1/dprod1 = f'exp(pbis1)*dpbis1 = f'exp(pbis1)*(fexpp(fg_ratio) + prod1*f'expp(fg_ratio)*dfg_ratio
                               = dp2old * (fexpp(fg_ratio) + prod1*f'expp(fg_ratio)*dfg_ratio
                dp2/dprod1 = f'exp(pbis2)*dpbis2 =f'exp(pbis2)*prod2*f'expp(fg_ratio)*dfg_ratio

            dtechno_mix(p1)/dprod2 = dtechno_mix(p1)/dprod2old*(fexpp(fg_ratio) + prod2*f'expp(fg_ratio)*dfg_ratio -p1dp1/ptot**2

        pbis = production_bytechno
        prodi = self.sub_production_dict
        pi = prod_element_dict
        '''
        if exp_min:
            prod_element_dict, prod_total_for_mix_weight = self.compute_prod_with_exp_min(
                production_by_techno, elements_dict, min_prod)
            dprod_element_dict = self.compute_dprod_with_exp_min(
                production_by_techno, elements_dict, min_prod)
        else:
            prod_element_dict, prod_total_for_mix_weight = self.compute_prod_wcutoff(
                production_by_techno, elements_dict, min_prod)
            dprod_element_dict = self.compute_dprod_wcutoff(
                production_by_techno, elements_dict, min_prod)

        if self.food_storage_percentage is not None:
            dfoodstorage = self.compute_dfood_storage_with_exp_min(
                self.fs_ratio)
            dfs_ratio = -1.0 * self.food_storage_production / \
                (self.carbon_utilization_type['food storage'].values)**2
            dfs_ratio_dfs_prod = 1.0 / \
                self.carbon_utilization_type['food storage'].values
        grad_element_mix_vs_prod = {}

        for element in elements_dict.keys():

            grad_element_mix_vs_prod[f'{element}'] = dprod_element_dict[element] * (
                prod_total_for_mix_weight - prod_element_dict[element]) / prod_total_for_mix_weight**2

            if self.food_storage_percentage is not None:
                if element.startswith('food_storage_applications'):
                    #(fexpp(fg_ratio) + prod1*f'expp(fg_ratio)*dfg_ratio
                    prodi = self.sub_production_dict[element][
                        f'{self.name} ({self.unit})'].values
                    ratio_on_old = self.food_storage_percentage + prodi * dfoodstorage * dfs_ratio

                    grad_element_mix_vs_prod[f'{element}'] = grad_element_mix_vs_prod[f'{element}'] * ratio_on_old

                    # compute gradient vs flue gas production
                    # dtechno_mix/dflue gas prod = dpi/ptot -pidpj/ptot**2 for j in flue gas capture
                    # first we add  dpi/ptot only if  if i in flue gas capture
                    grad_element_mix_vs_prod[f'fg_prod {element}'] = dprod_element_dict[element] * \
                        prodi * dfoodstorage * dfs_ratio_dfs_prod / prod_total_for_mix_weight
                else:
                    grad_element_mix_vs_prod[f'fg_prod {element}'] = np.zeros(
                        len(dfs_ratio_dfs_prod))

            for element_other in elements_dict.keys():
                # compute gradient vs flue gas production
                # dtechno_mix/dflue gas prod = dpi/ptot -pidpj/ptot**2 for j in flue gas capture
                # then  we add  -pidpj/ptot**2 for j in flue gas capture no
                # matter if i is flue gas capture
                if element_other.startswith('food_storage_applications') and self.food_storage_percentage is not None:
                    prodj = self.sub_production_dict[element_other][
                        f'{self.name} ({self.unit})'].values
                    grad_element_mix_vs_prod[f'fs_prod {element}'] -= dprod_element_dict[element_other] * prodj * \
                        dfoodstorage * dfs_ratio_dfs_prod * \
                        prod_element_dict[element] / \
                        prod_total_for_mix_weight**2
                if element_other != element:
                    # dtechno_mix(p2)/dprod1 = -p2dp1/ptot**2
                    grad_element_mix_vs_prod[f'{element} {element_other}'] = -dprod_element_dict[element] * \
                        prod_element_dict[element_other] / \
                        prod_total_for_mix_weight**2

                    if element.startswith('food_storage_applications') and self.food_storage_percentage is not None:

                        #(fexpp(fg_ratio) + prod1*f'expp(fg_ratio)*dfg_ratio
                        prodi = self.sub_production_dict[element][
                            f'{self.name} ({self.unit})'].values
                        ratio_on_old = self.food_storage_percentage + prodi * dfoodstorage * dfs_ratio

                        grad_element_mix_vs_prod[f'{element} {element_other}'] = grad_element_mix_vs_prod[
                            f'{element} {element_other}'] * ratio_on_old

                        for element_bis in elements_dict:
                            if element_bis not in [element, element_other] and element_bis.startswith('food_storage_applications'):
                                prodk = self.sub_production_dict[element_bis][
                                    f'{self.name} ({self.unit})'].values
                                # dp2 = f'exp(pbis2)*prod2*dfluegas*dfg_ratio
                                dp2 = dprod_element_dict[element_bis] * \
                                    prodk * dfs_ratio * dfoodstorage
                                new_grad = dp2 * prod_element_dict[element_other] / \
                                    prod_total_for_mix_weight**2
                                grad_element_mix_vs_prod[f'{element} {element_other}'] = grad_element_mix_vs_prod[
                                    f'{element} {element_other}'] - new_grad

                    # dp2p1/ptot**2
                    # if more than one other flue gas disc then dp2 = sum(dpi)
                    if element_other.startswith('food_storage_applications') and element.startswith('food_storage_applications') and self.food_storage_percentage is not None:
                        # for dpi/dpi
                        prodj = self.sub_production_dict[element_other][
                            f'{self.name} ({self.unit})'].values
                        # dp2 = f'exp(pbis2)*prod2*dfluegas*dfg_ratio
                        dp2 = dprod_element_dict[element_other] * \
                            prodj * dfs_ratio * dfoodstorage
                        new_grad = dp2 * prod_element_dict[element] / \
                            prod_total_for_mix_weight**2
                        grad_element_mix_vs_prod[f'{element}'] = grad_element_mix_vs_prod[f'{element}'] - new_grad

                        # for dpi/dpj
                        # p2dp2/ptot**2
                        new_grad = dp2 * (prod_total_for_mix_weight - prod_element_dict[element_other]) / \
                            prod_total_for_mix_weight**2
                        grad_element_mix_vs_prod[f'{element} {element_other}'] = grad_element_mix_vs_prod[
                            f'{element} {element_other}'] + new_grad
        return grad_element_mix_vs_prod
