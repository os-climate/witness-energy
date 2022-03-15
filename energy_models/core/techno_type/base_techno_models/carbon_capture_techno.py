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
from abc import abstractmethod
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.techno_type.techno_type import TechnoType
import scipy.interpolate as sc
from scipy.stats import linregress
import numpy as np


class CCTechno(TechnoType):
    energy_name = CarbonCapture.name

    def __init__(self, name):
        TechnoType.__init__(self, name)
        self.product_energy_unit = 'Mt'
        self.energy_unit = 'TWh'

    def check_capex_unity(self, data_tocheck):
        """
        Put all capex in $/kgCO2
        """

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

    @abstractmethod
    def compute_other_primary_energy_costs(self):
        '''
        Compute other energy costs which will depend on the techno reaction (elec for electrolysis or methane for SMR by example)
        '''

    @abstractmethod
    def get_theoretical_co2_prod(self, unit='kg/kWh'):
        ''' 
        Get the theoretical CO2 production for a given technology,
        Need to be overloaded in each technology model (example in SMR)
        '''
        return 0.0

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

    def compute_dcapex_dfg_ratio(self, fg_mean_ratio, invest_list, data_config, fg_ratio_effect):

        if fg_ratio_effect:
            co2_concentration_list = [0.035, 0.092, 0.13, 0.186, 0.44, 0.99]
            capex_capture_list = [1234, 629, 479.8, 396.8, 263.3, 117]

            slopes = []
            for fg in fg_mean_ratio:
                co2_concentration_list_with_fg = co2_concentration_list + [fg]
                co2_concentration_list_with_fg.sort()
                position = co2_concentration_list_with_fg.index(fg)
                if position == 0:
                    position = 1
                elif position == len(co2_concentration_list_with_fg):
                    position = len(co2_concentration_list)
                if fg in co2_concentration_list:
                    position = position + 1

                slope = linregress(
                    co2_concentration_list[position - 1:position + 1], capex_capture_list[position - 1:position + 1])[0]
                if np.isnan(slope):
                    slope = 0.0
                slopes.append(slope)

            capex = super().compute_capex(invest_list, data_config)
            grad = np.array(slopes)[:, np.newaxis] * \
                np.array(capex)[:, np.newaxis] / 479.8

        else:
            grad = 0.0

        return np.identity(len(fg_mean_ratio)) * grad

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

    def compute_delec_dfg_ratio(self, fg_mean_ratio, fg_ratio_effect, energy_name='electricity'):

        if fg_ratio_effect:
            co2_concentration_list = [0.035, 0.092, 0.13, 0.186, 0.44, 0.99]
            elec_demand_list = [23.2, 10.5, 8.5, 6.6, 4.5, 8.5]

            slopes = []
            for fg in fg_mean_ratio:
                co2_concentration_list_with_fg = co2_concentration_list + [fg]
                co2_concentration_list_with_fg.sort()
                position = co2_concentration_list_with_fg.index(fg)
                if position == 0:
                    position = 1
                elif position == len(co2_concentration_list_with_fg):
                    position = len(co2_concentration_list)

                if fg in co2_concentration_list:
                    position = position + 1
                slope = linregress(
                    co2_concentration_list[position - 1:position + 1], elec_demand_list[position - 1:position + 1])[0]
                if np.isnan(slope):
                    slope = 0.0
                slopes.append(slope)
            elec_needs = self.get_electricity_needs()

            grad = np.array(slopes)[:, np.newaxis] \
                * elec_needs / 8.5 / self.techno_infos_dict['efficiency'] *\
                self.prices[energy_name][:, np.newaxis]
        else:
            grad = 0.0
        return np.identity(len(fg_mean_ratio)) * grad

    def compute_dprod_dfluegas(self,  capex_list, invest_list, invest_before_year_start, techno_dict, dcapexdfluegas):

        dprod_dcapex = self.compute_dprod_dcapex(
            capex_list, invest_list, techno_dict, invest_before_year_start)

        #dprod_dfluegas = dpprod_dpfluegas + dprod_dcapex * dcapexdfluegas
        if 'complex128' in [dcapexdfluegas.dtype, dprod_dcapex.dtype]:
            arr_type = 'complex128'
        else:
            arr_type = 'float64'

        dprod_dfluegas = np.zeros(dprod_dcapex.shape, dtype=arr_type)

        for line in range(dprod_dcapex.shape[0]):
            for column in range(dprod_dcapex.shape[1]):
                dprod_dfluegas[line, column] = np.matmul(
                    dprod_dcapex[line, :], dcapexdfluegas[:, column])

        return dprod_dfluegas
