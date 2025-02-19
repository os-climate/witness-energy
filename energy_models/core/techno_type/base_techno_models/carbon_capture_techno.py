'''
Copyright 2022 Airbus SAS
Modifications on 23/11/2023 Copyright 2023 Capgemini

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
import scipy.interpolate as sc

from energy_models.core.techno_type.techno_type import TechnoType
from energy_models.glossaryenergy import GlossaryEnergy


class CCTechno(TechnoType):
    stream_name = GlossaryEnergy.carbon_captured
    product_unit = "Mt"

    def compute_scope_1_ghg_intensity(self):
        """
        Compute scope 1 ghg intensity (Mt/TWh): due to production

        For CC technos, unit of production 1 removed ton of CO2 so
        """
        self.outputs[f'ghg_intensity_scope_1:{GlossaryEnergy.Years}'] = self.zeros_array
        self.outputs[f'ghg_intensity_scope_1:{GlossaryEnergy.CO2}'] = self.zeros_array - 1.

        # CO2
        for ghg in [GlossaryEnergy.CH4, GlossaryEnergy.N2O]:
            ghg_intensity = self.zeros_array

            self.outputs[f'ghg_intensity_scope_1:{ghg}'] = ghg_intensity
    def capex_unity_harmonizer(self):
        """
        Put all capex in $/tCO2
        """
        data_tocheck = self.inputs['techno_infos_dict']
        if data_tocheck['Capex_init_unit'] == '$/kgCO2':

            capex_init = data_tocheck['Capex_init']
        # add elif unit conversion if necessary

        else:
            capex_unit = data_tocheck['Capex_init_unit']
            raise Exception(
                f'The CAPEX unity {capex_unit} is not handled yet in techno_type')
        # return $/tCO2
        return capex_init * 1000.0

    def check_energy_demand_unit(self, energy_demand_unit, energy_demand):
        """
        Compute energy demand in kWh/kgCO2
        """
        # Based on formula 1 of the Fasihi2016 PtL paper
        # self.data['demand']=self.scenario_demand['elec_demand']

        if energy_demand_unit == 'kWh/kgCO2':
            pass
        # add elif unit conversion if necessary
        else:
            raise Exception(
                f'The unity of the energy demand {energy_demand_unit} is not handled with conversions')

        return energy_demand

    

    @staticmethod
    def compute_capex_variation_from_fg_ratio(fg_mean_ratio, fg_ratio_effect):

        if fg_ratio_effect:
            c02_concentration_base = 0.13
            co2_concentration_list = [0.035, 0.092, 0.13, 0.186, 0.44, 0.99]
            capex_capture_list = [1234, 629, 479.8, 396.8, 263.3, 117]

            func_capex_with_fg_ratio = sc.interp1d(co2_concentration_list, capex_capture_list,
                                                   kind='linear', fill_value='extrapolate')

            real_ratio = func_capex_with_fg_ratio(
                fg_mean_ratio) / func_capex_with_fg_ratio(c02_concentration_base)
        else:
            real_ratio = np.ones(len(fg_mean_ratio))

        return real_ratio

    @staticmethod
    def compute_electricity_variation_from_fg_ratio(fg_mean_ratio, fg_ratio_effect):

        if fg_ratio_effect:
            c02_concentration_base = 0.13
            co2_concentration_list = [0.035, 0.092, 0.13, 0.186, 0.44, 0.99]
            elec_demand_list = [23.2, 10.5, 8.5, 6.6, 4.5, 8.5]

            func_elec_demand_with_fg_ratio = sc.interp1d(co2_concentration_list, elec_demand_list,
                                                         kind='linear', fill_value='extrapolate')

            real_ratio = func_elec_demand_with_fg_ratio(fg_mean_ratio) / \
                         func_elec_demand_with_fg_ratio(c02_concentration_base)
        else:
            real_ratio = np.ones(len(fg_mean_ratio))

        return real_ratio

