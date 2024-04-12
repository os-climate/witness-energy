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

from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.core.stream_type.carbon_models.carbon_monoxyde import CO
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import GaseousHydrogen
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.energy_models.syngas import Syngas
from energy_models.core.stream_type.energy_models.syngas import \
    compute_calorific_value as compute_syngas_calorific_value
from energy_models.core.stream_type.energy_models.syngas import compute_molar_mass as compute_syngas_molar_mass
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
from energy_models.core.stream_type.resources_models.water import Water
from energy_models.core.techno_type.base_techno_models.gaseous_hydrogen_techno import GaseousHydrogenTechno
from energy_models.glossaryenergy import GlossaryEnergy
from sostrades_core.tools.base_functions.exp_min import compute_dfunc_with_exp_min


class WGS(GaseousHydrogenTechno):

    def __init__(self, name):
        super().__init__(name)
        self.syngas_ratio = None
        self.needed_syngas_ratio = None
        self.inputs_dict = None
        self.available_power = None
        self.slope_capex = None
        self.syngas_ratio = None

    def configure_parameters_update(self, inputs_dict):
        GaseousHydrogenTechno.configure_parameters_update(self, inputs_dict)
        self.syngas_ratio = np.array(inputs_dict['syngas_ratio']) / 100.0
        self.needed_syngas_ratio = inputs_dict['needed_syngas_ratio'] / 100.0
        self.inputs_dict = inputs_dict

    def check_capex_unity(self, data_config):
        '''
        Overload the check_capex_unity for this particular model 
        '''
        capex_list = np.array(data_config['Capex_init_vs_CO_conversion'])

        # input power was in mol/h
        # We multiply by molar mass and calorific value of the paper to get input power in kW
        # in the paper 0.3 H2 0.3 of CO 0.25 of CO2 0.1 of CH4 and 0.05 of N2

        nitrogen_molar_mass = 2 * 14
        input_molar_mass = 0.3 * self.data_energy_dict['molar_mass'] + 0.3 * CO.data_energy_dict['molar_mass'] + \
                           0.25 * CO2.data_energy_dict['molar_mass'] + 0.1 * Methane.data_energy_dict['molar_mass'] \
                           + 0.05 * nitrogen_molar_mass

        input_calorific_value = 0.3 * self.data_energy_dict['calorific_value'] + 0.3 * CO.data_energy_dict[
            'calorific_value'] + \
                                0.25 * CO2.data_energy_dict['calorific_value'] + \
                                0.1 * Methane.data_energy_dict['calorific_value']

        # molar mass is in g/mol
        input_power = data_config['input_power'] * \
                      input_molar_mass / 1000.0 * input_calorific_value

        syngas_needs = self.get_theoretical_syngas_needs(1.0)

        self.available_power = input_power * data_config['full_load_hours'] / \
                               syngas_needs * data_config['efficiency']

        capex_list = capex_list * \
                     data_config['euro_dollar'] / self.available_power
        # Need to convertcapex_list in $/kWh
        final_sg_ratio = 1.0 - np.array(data_config['CO_conversion']) / 100.0
        initial_sg_ratio = 0.3 / 0.3
        delta_sg_ratio = initial_sg_ratio - final_sg_ratio

        self.slope_capex = (
                                   capex_list[0] - capex_list[1]) / (delta_sg_ratio[0] - delta_sg_ratio[1])
        b = capex_list[0] - self.slope_capex * delta_sg_ratio[0]

        def func_capex(delta_sg_ratio):
            return self.slope_capex * delta_sg_ratio + b

        #         func_capex_a = sc.interp1d(delta_sg_ratio, capex_list,
        #                                    kind='linear', fill_value='extrapolate')

        capex_init = func_capex(
            self.syngas_ratio[0] - self.needed_syngas_ratio)

        return capex_init * 1000.0

    def get_electricity_needs(self):

        elec_power = self.techno_infos_dict['elec_demand']

        elec_demand = elec_power * \
                      self.techno_infos_dict['full_load_hours'] / self.available_power

        return elec_demand

    def compute_dsyngas_needs_dsyngas_ratio(self):
        """
        Compute dsyngas_needs_dsyngas_ratio
        """
        mol_syngas = 1.0
        mol_H2 = (1.0 + self.syngas_ratio) / \
                 (1.0 + self.needed_syngas_ratio)

        needed_syngas_molar_mass = compute_syngas_molar_mass(
            self.needed_syngas_ratio)
        needed_calorific_value = compute_syngas_calorific_value(
            self.needed_syngas_ratio)

        molar_mass = (self.syngas_ratio * CO.data_energy_dict['molar_mass'] +
                      GaseousHydrogen.data_energy_dict['molar_mass']) / (1.0 + self.syngas_ratio)

        molmassup = (self.syngas_ratio * CO.data_energy_dict['molar_mass'] +
                     GaseousHydrogen.data_energy_dict['molar_mass'])

        molmassdown = (1.0 + self.syngas_ratio)

        dmolmassup = CO.data_energy_dict['molar_mass']

        dmolmassdown = 1.0

        dmolarmass_dsyngas = (dmolmassup * molmassdown -
                              dmolmassdown * molmassup) / molmassdown ** 2

        calorific_value = (self.syngas_ratio * CO.data_energy_dict['molar_mass'] * CO.data_energy_dict[
            'calorific_value'] +
                           GaseousHydrogen.data_energy_dict['molar_mass'] * GaseousHydrogen.data_energy_dict[
                               'calorific_value']) / (
                                  GaseousHydrogen.data_energy_dict['molar_mass'] + self.syngas_ratio *
                                  CO.data_energy_dict['molar_mass'])

        calup = (self.syngas_ratio * CO.data_energy_dict['molar_mass'] * CO.data_energy_dict['calorific_value'] +
                 GaseousHydrogen.data_energy_dict['molar_mass'] * GaseousHydrogen.data_energy_dict['calorific_value'])

        caldown = (GaseousHydrogen.data_energy_dict['molar_mass'] +
                   self.syngas_ratio * CO.data_energy_dict['molar_mass'])

        dcalup = CO.data_energy_dict['molar_mass'] * \
                 CO.data_energy_dict['calorific_value']

        dcaldown = CO.data_energy_dict['molar_mass']

        dcalorific_val_dsyngas = (
                                         dcalup * caldown - dcaldown * calup) / (caldown ** 2)

        syngasup = mol_syngas * molar_mass * calorific_value
        dsyngasup1 = mol_syngas * \
                     (dmolarmass_dsyngas * calorific_value +
                      molar_mass * dcalorific_val_dsyngas)

        syngasdown = mol_H2 * needed_syngas_molar_mass * needed_calorific_value

        dsyngasdown = needed_syngas_molar_mass * needed_calorific_value / \
                      (1.0 + self.needed_syngas_ratio)

        dsyngas_needs_dsyngas_ratio = (dsyngasup1 * syngasdown -
                                       syngasup * dsyngasdown) / syngasdown ** 2

        return dsyngas_needs_dsyngas_ratio

    def compute_dwater_needs_dsyngas_ratio(self):
        """
        Compute dsyngas_needs_dsyngas_ratio
        """

        mol_H20 = (self.syngas_ratio - self.needed_syngas_ratio) / \
                  (1.0 + self.needed_syngas_ratio)

        # needed syngas_ratio could be 0 in this case syngas is H2
        needed_syngas_molar_mass = compute_syngas_molar_mass(
            self.needed_syngas_ratio)
        needed_calorific_value = compute_syngas_calorific_value(
            self.needed_syngas_ratio)

        mol_H20up = (self.syngas_ratio - self.needed_syngas_ratio)
        dmol_H20up = 1

        molH20down = (1.0 + self.needed_syngas_ratio)
        dmolH20down = 0.0

        dmol_H20_dsyngas_ratio = (
                                         dmol_H20up * molH20down - dmolH20down * mol_H20up) / molH20down ** 2

        mol_H2 = (1.0 + self.syngas_ratio) / \
                 (1.0 + self.needed_syngas_ratio)

        dmol_H2up = 1.0

        mol_H2down = (1.0 + self.needed_syngas_ratio)

        dmol_H2_dsyngas_ratio = (dmol_H2up * mol_H2down) / mol_H2down ** 2

        water_data = Water.data_energy_dict
        waterup = mol_H20 * water_data['molar_mass']
        dwaterup = water_data['molar_mass'] * dmol_H20_dsyngas_ratio

        waterdown = (mol_H2 * needed_syngas_molar_mass *
                     needed_calorific_value)
        dwaterdown = needed_syngas_molar_mass * \
                     needed_calorific_value * dmol_H2_dsyngas_ratio

        dwater_needs_dsyngas_ratio = (
                                             dwaterup * waterdown - dwaterdown * waterup) / waterdown ** 2

        return dwater_needs_dsyngas_ratio

    def compute_delec_needs_dsyngas_ratio(self, dprod_dsyngas):
        """
        Compute delec_needs_dsyngas_ratio
        """
        elec_needs = self.get_electricity_needs()

        delec_consumption_dsyngas_ratio = dprod_dsyngas * elec_needs

        return delec_consumption_dsyngas_ratio

    def compute_dsyngas_consumption_dsyngas_ratio(self, dsyngas_needs_dsyngas_ratio, dprod_dsyngas_ratio,
                                                  production_energy):

        efficiency = self.compute_efficiency()
        syngas_needs = self.get_theoretical_syngas_needs(
            self.syngas_ratio)

        return (np.identity(
            len(self.years)) * production_energy.to_numpy() * dsyngas_needs_dsyngas_ratio + syngas_needs[:,
                                                                                            np.newaxis] * dprod_dsyngas_ratio) / efficiency[
                                                                                                                                 :,
                                                                                                                                 np.newaxis]

    def compute_dwater_consumption_dsyngas_ratio(self, dwater_needs_dsyngas_ratio, dprod_dsyngas_ratio,
                                                 production_energy):

        efficiency = self.compute_efficiency()
        water_needs = self.get_theoretical_water_needs()

        return (np.identity(len(self.years)) * production_energy.to_numpy() * dwater_needs_dsyngas_ratio + water_needs[
                                                                                                           :,
                                                                                                           np.newaxis] * dprod_dsyngas_ratio) / efficiency[
                                                                                                                                                :,
                                                                                                                                                np.newaxis]

    def compute_dco2_prod_dsyngas_ratio(self, mol_CO2, mol_H2, co2_molar_mass, needed_syngas_molar_mass,
                                        needed_calorific_value, dmol_CO2_dsyngas_ratio, dmol_H2_dsyngas_ratio):

        co2_prod_up = mol_CO2 * co2_molar_mass

        co2_prod_down = (mol_H2 * needed_syngas_molar_mass *
                         needed_calorific_value)

        dco2_prod_up_dsyngas_ratio = dmol_CO2_dsyngas_ratio * \
                                     co2_molar_mass
        dco2_prod_down_dsyngas_ratio = dmol_H2_dsyngas_ratio * \
                                       needed_syngas_molar_mass * needed_calorific_value

        return (dco2_prod_up_dsyngas_ratio * co2_prod_down -
                dco2_prod_down_dsyngas_ratio * co2_prod_up) / co2_prod_down ** 2

    def compute_dcapex_dsyngas_ratio(self):

        capex_init = self.check_capex_unity(
            self.techno_infos_dict)

        if 'complex128' in [type(self.initial_production), type(self.slope_capex), capex_init.dtype,
                            self.cost_details[GlossaryEnergy.InvestValue].values.dtype]:
            arr_type = 'complex128'
        else:
            arr_type = 'float64'
        capex_grad = np.zeros(
            (len(self.years), len(self.years)), dtype=arr_type)

        expo_factor = self.compute_expo_factor(
            self.techno_infos_dict)

        dqlist = []
        qlist = []
        invest_sum = self.initial_production * capex_init
        dinvest_sum = self.initial_production * 1000.0 * self.slope_capex
        capex_year = capex_init
        capex_grad[0][0] = 1000.0 * self.slope_capex
        invest_list = self.cost_details[GlossaryEnergy.InvestValue].values
        if min(invest_list.real) < 0:
            invest_list_2 = np.maximum(1e-12, invest_list)

        else:
            invest_list_2 = invest_list.copy()
        invest_list_sign = np.sign(invest_list.real)
        for i, invest in enumerate(invest_list_2):

            if invest_sum.real < 10.0 or i == 0.0:
                capex_year = capex_init
                capex_grad[i][0] = 1000.0 * self.slope_capex

            else:

                q = ((invest_sum + invest) / invest_sum) ** (-expo_factor)

                #                 dq = -expo_factor * ((invest_sum + invest) / invest_sum) ** (-expo_factor -
                # 1.0) * (-dinvest_sum * invest / (invest_sum * invest_sum))
                if invest_list_sign[i] == -1:
                    dq = 0.0
                else:
                    dq = dinvest_sum * expo_factor * invest * \
                         q / (invest_sum * (invest_sum + invest))

                if q.real < 0.95:
                    dq = 0.05 * np.exp(q - 0.9) * dq
                    q = 0.9 + 0.05 * np.exp(q - 0.9)

                dqlist.append(dq)
                qlist.append(q)

                capex_grad[i][0] = q * capex_grad[i - 1][0] + dq * capex_year

                capex_year = capex_year * q

            invest_sum += invest

        if 'maximum_learning_capex_ratio' in self.techno_infos_dict:
            maximum_learning_capex_ratio = self.techno_infos_dict['maximum_learning_capex_ratio']
        else:
            maximum_learning_capex_ratio = 0.9
        # dcapex = maximum_learning_capex_ratio*dcapex_init + (1.0 - maximum_learning_capex_ratio)*dcapex
        capex_grad = maximum_learning_capex_ratio * capex_grad[0][0] * np.insert(
            np.zeros((len(self.years), len(self.years) - 1)), 0, np.ones(len(self.years)), axis=1) + \
                     (1.0 - maximum_learning_capex_ratio) * capex_grad
        return capex_grad

    def compute_dprice_CO2_fact_dsyngas_ratio(self):

        co2_data = CO2.data_energy_dict
        needed_syngas_molar_mass = compute_syngas_molar_mass(
            self.needed_syngas_ratio)
        needed_calorific_value = compute_syngas_calorific_value(
            self.needed_syngas_ratio)
        mol_H2 = (1.0 + self.syngas_ratio) / \
                 (1.0 + self.needed_syngas_ratio)
        mol_CO2 = self.syngas_ratio - self.needed_syngas_ratio * mol_H2

        dmol_H2up = 1.0

        mol_H2down = (1.0 + self.needed_syngas_ratio)

        dmol_H2_dsyngas_ratio = (dmol_H2up * mol_H2down) / mol_H2down ** 2

        dmol_CO2_dsyngas_ratio = 1 - self.needed_syngas_ratio * dmol_H2_dsyngas_ratio

        co2_prod_up = mol_CO2 * co2_data['molar_mass']
        dco2_prod_up_dsyngas_ratio = dmol_CO2_dsyngas_ratio * \
                                     co2_data['molar_mass']

        co2_prod_down = (mol_H2 * needed_syngas_molar_mass *
                         needed_calorific_value)

        dco2_prod_down_dsyngas_ratio = dmol_H2_dsyngas_ratio * \
                                       needed_syngas_molar_mass * needed_calorific_value

        dco2_prod_syngas_ratio = (dco2_prod_up_dsyngas_ratio * co2_prod_down -
                                  dco2_prod_down_dsyngas_ratio * co2_prod_up) / co2_prod_down ** 2

        #         dprice_CO2_fact = dco2_prod_syngas_ratio * \
        #             self.inputs_dict[GlossaryEnergy.CO2TaxesValue].loc[self.inputs_dict[GlossaryEnergy.CO2TaxesValue][GlossaryEnergy.Years]
        #                                               <= self.cost_details[GlossaryEnergy.Years].max()][GlossaryEnergy.CO2Tax].values

        return dco2_prod_syngas_ratio

    def dtotal_co2_emissions_dsyngas_ratio(self):

        # co2_taxes = (co2_prod + co2_input_energies)
        dco2_prod_dsyngas_ratio = self.compute_dprice_CO2_fact_dsyngas_ratio()

        efficiency = self.compute_efficiency()

        dco2_syngas_dsynags_ratio = self.compute_dsyngas_needs_dsyngas_ratio() \
                                    * self.energy_CO2_emissions.loc[self.energy_CO2_emissions[GlossaryEnergy.Years]
                                                                    <= self.cost_details[GlossaryEnergy.Years].max()][
                                        Syngas.name].values / efficiency

        dco2_water_dsynags_ratio = self.compute_dwater_needs_dsyngas_ratio() \
                                   * self.resources_CO2_emissions.loc[self.resources_CO2_emissions[GlossaryEnergy.Years]
                                                                      <= self.cost_details[GlossaryEnergy.Years].max()][
                                       Water.name].values / efficiency

        return dco2_syngas_dsynags_ratio + dco2_prod_dsyngas_ratio + dco2_water_dsynags_ratio

    def dco2_taxes_dsyngas_ratio(self):

        dtot_co2_emissions_dsyngas_ratio = self.dtotal_co2_emissions_dsyngas_ratio()

        dco2_taxes_dsg_ratio = dtot_co2_emissions_dsyngas_ratio * \
                               self.CO2_taxes.loc[self.CO2_taxes[GlossaryEnergy.Years]
                                                  <= self.cost_details[GlossaryEnergy.Years].max()][
                                   GlossaryEnergy.CO2Tax].values

        return dco2_taxes_dsg_ratio

    def dco2_syngas_dsyngas_ratio(self):

        efficiency = self.compute_efficiency()

        return (self.compute_dsyngas_needs_dsyngas_ratio(
        ) * self.energy_CO2_emissions[Syngas.name].values / efficiency)

    def compute_dfactory_dsyngas_ratio(self):
        crf = self.compute_capital_recovery_factor(self.inputs_dict['techno_infos_dict'])
        capex_grad = self.compute_dcapex_dsyngas_ratio()
        factory_grad = capex_grad * \
                       (crf + self.inputs_dict['techno_infos_dict']['Opex_percentage'])

        return factory_grad

    def compute_dprice_WGS_dsyngas_ratio(self):

        efficiency = self.compute_efficiency()
        years = np.arange(
            self.inputs_dict[GlossaryEnergy.YearStart], self.inputs_dict[GlossaryEnergy.YearEnd] + 1)
        margin = self.inputs_dict[GlossaryEnergy.MarginValue].loc[
            self.inputs_dict[GlossaryEnergy.MarginValue][GlossaryEnergy.Years]
            <= self.inputs_dict[GlossaryEnergy.YearEnd]][GlossaryEnergy.MarginValue].values
        factory_grad = self.compute_dfactory_dsyngas_ratio()

        dsyngas_dsyngas_ratio = np.identity(len(years)) * self.compute_dsyngas_needs_dsyngas_ratio() * \
                                self.energy_prices[Syngas.name].to_numpy() / efficiency[:, np.newaxis]
        dwater_dsyngas_ratio = np.identity(len(years)) * self.compute_dwater_needs_dsyngas_ratio() * \
                               self.resources_prices[Water.name].to_numpy(
                               ) / efficiency[:, np.newaxis]

        mol_H2 = (1.0 + self.syngas_ratio) / \
                 (1.0 + self.needed_syngas_ratio)

        dmol_H2up = 1.0

        mol_H2down = (1.0 + self.needed_syngas_ratio)

        dmol_H2_dsyngas_ratio = (dmol_H2up * mol_H2down) / mol_H2down ** 2

        needed_syngas_molar_mass = compute_syngas_molar_mass(
            self.needed_syngas_ratio)
        needed_calorific_value = compute_syngas_calorific_value(
            self.needed_syngas_ratio)
        # # CO2 emissions
        co2_data = CO2.data_energy_dict
        mol_CO2 = self.syngas_ratio - self.needed_syngas_ratio * mol_H2

        dmol_CO2_dsyngas_ratio = 1 - \
                                 self.needed_syngas_ratio * dmol_H2_dsyngas_ratio

        dco2_prod_dsyngas_ratio = self.compute_dco2_prod_dsyngas_ratio(
            mol_CO2, mol_H2, co2_data['molar_mass'], needed_syngas_molar_mass, needed_calorific_value,
            dmol_CO2_dsyngas_ratio, dmol_H2_dsyngas_ratio)

        dco2_syngas_dsyngas_ratio = self.dco2_syngas_dsyngas_ratio()

        CO2_emissions_is_positive = np.maximum(0.0, np.sign(
            self.carbon_intensity['WaterGasShift'].values))
        dprice_CO2_fact = np.identity(
            len(self.years)) * (dco2_prod_dsyngas_ratio + dco2_syngas_dsyngas_ratio) * \
                          self.CO2_taxes.loc[self.CO2_taxes[GlossaryEnergy.Years]
                                             <= self.year_end][GlossaryEnergy.CO2Tax].values * CO2_emissions_is_positive

        # now syngas is in % grad is divided by 100
        dprice_dsyngas = (factory_grad + dsyngas_dsyngas_ratio +
                          dwater_dsyngas_ratio) * (margin / 100.0) + dprice_CO2_fact

        return dprice_dsyngas

    def compute_dprice_WGS_wo_taxes_dsyngas_ratio(self):
        efficiency = self.compute_efficiency()
        years = np.arange(
            self.inputs_dict[GlossaryEnergy.YearStart], self.inputs_dict[GlossaryEnergy.YearEnd] + 1)
        margin = self.inputs_dict[GlossaryEnergy.MarginValue].loc[
            self.inputs_dict[GlossaryEnergy.MarginValue][GlossaryEnergy.Years]
            <= self.inputs_dict[GlossaryEnergy.YearEnd]][GlossaryEnergy.MarginValue].values
        factory_grad = self.compute_dfactory_dsyngas_ratio()

        dsyngas_dsyngas_ratio = np.identity(len(years)) * self.compute_dsyngas_needs_dsyngas_ratio() * \
                                self.energy_prices[Syngas.name].to_numpy() / efficiency[:, np.newaxis]
        dwater_dsyngas_ratio = np.identity(len(years)) * self.compute_dwater_needs_dsyngas_ratio() * \
                               self.resources_prices[Water.name].to_numpy(
                               ) / efficiency[:, np.newaxis]
        # now syngas is in % grad is divided by 100
        dprice_dsyngas = (factory_grad + dsyngas_dsyngas_ratio + dwater_dsyngas_ratio) \
                         * np.split(margin, len(margin)) / 100.0

        return dprice_dsyngas

    def compute_resources_needs(self):
        # need in kg
        self.cost_details[f"{ResourceGlossary.WaterResource}_needs"] = self.get_theoretical_water_needs()/ self.cost_details['efficiency']

    def compute_other_energies_needs(self):
        self.cost_details[f'{GlossaryEnergy.electricity}_needs'] = self.get_electricity_needs()
        # in kwh of fuel by kwh of H2
        self.syngas_ratio = self.syngas_ratio[0:len(
            self.cost_details[GlossaryEnergy.Years])]

        self.cost_details['syngas_needs'] = self.get_theoretical_syngas_needs(self.syngas_ratio) / self.cost_details['efficiency']

    def compute_dprod_dfluegas(self, capex_list, invest_list, invest_before_year_start, techno_dict, dcapexdfluegas):

        # dpprod_dpfluegas = np.zeros(dcapexdfluegas.shape())

        dprod_dcapex = self.compute_dprod_dcapex(
            capex_list, invest_list, techno_dict, invest_before_year_start)

        if 'complex128' in [dprod_dcapex.dtype]:
            arr_type = 'complex128'
        else:
            arr_type = 'float64'

        # dprod_dfluegas = dpprod_dpfluegas + dprod_dcapex * dcapexdfluegas
        dprod_dfluegas = np.zeros(dprod_dcapex.shape, dtype=arr_type)
        dinvest_exp_min = compute_dfunc_with_exp_min(invest_list, 1e-12)

        dcapexdfluegas *= dinvest_exp_min
        for line in range(dprod_dcapex.shape[0]):
            for column in range(dprod_dcapex.shape[1]):
                dprod_dfluegas[line, column] = np.matmul(
                    dprod_dcapex[line, :], dcapexdfluegas[:, column])

        return dprod_dfluegas

    def compute_production(self):
        co2_prod = self.get_theoretical_co2_prod()
        self.production_detailed[f'{CarbonCapture.flue_gas_name} ({self.mass_unit})'] = co2_prod * \
                                                                                        self.production_detailed[
                                                                                            f'{GaseousHydrogenTechno.energy_name} ({self.product_energy_unit})']

        # production
        # self.production[f'{lowheattechno.energy_name} ({self.product_energy_unit})'] = \
        #     self.techno_infos_dict['low_heat_production'] * \
        #     self.production[f'{GaseousHydrogenTechno.energy_name} ({self.product_energy_unit})']  # in TWH

    def compute_consumption(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """
        # Consumption
        self.consumption_detailed[f'{Electricity.name} ({self.product_energy_unit})'] = self.cost_details[
                                                                                            f'{GlossaryEnergy.electricity}_needs'] * \
                                                                                        self.production_detailed[
                                                                                            f'{GaseousHydrogenTechno.energy_name} ({self.product_energy_unit})']  # in kWH
        self.consumption_detailed[f'{Syngas.name} ({self.product_energy_unit})'] = self.cost_details['syngas_needs'] * \
                                                                                   self.production_detailed[
                                                                                       f'{GaseousHydrogenTechno.energy_name} ({self.product_energy_unit})'] # in kWH

    def get_theoretical_syngas_needs(self, syngas_ratio):
        ''' 
        (H2 +r1CO) + cH20 --> dCO2 + e(H2 +r2CO)

        e = (1+r1)/(1+r2)
        c = (r1-r2)/(1+r2)
        d = r1 - r2(1+r1)/(1+r2)
        '''

        mol_H2 = (1.0 + syngas_ratio) / (1.0 + self.needed_syngas_ratio)
        mol_syngas = 1.0

        # r1*mmCO + mmH2/(1+r1)
        syngas_molar_mass = compute_syngas_molar_mass(syngas_ratio)
        syngas_calorific_value = compute_syngas_calorific_value(
            syngas_ratio)

        # needed syngas_ratio could be 0 in this case syngas is H2
        needed_syngas_molar_mass = compute_syngas_molar_mass(
            self.needed_syngas_ratio)
        needed_calorific_value = compute_syngas_calorific_value(
            self.needed_syngas_ratio)
        syngas_needs = mol_syngas * syngas_molar_mass * syngas_calorific_value / \
                       (mol_H2 * needed_syngas_molar_mass *
                        needed_calorific_value)

        return syngas_needs

    def get_theoretical_water_needs(self):
        ''' 
        (H2 +r1CO) + cH20 --> dCO2 + e(H2 +r2CO)

        e = (1+r1)/(1+r2)
        c = (r1-r2)/(1+r2)
        d = r1 - r2(1+r1)/(1+r2)
        '''

        mol_H20 = (self.syngas_ratio - self.needed_syngas_ratio) / \
                  (1.0 + self.needed_syngas_ratio)
        mol_H2 = (1.0 + self.syngas_ratio) / (1.0 + self.needed_syngas_ratio)

        # needed syngas_ratio could be 0 in this case syngas is H2
        needed_syngas_molar_mass = compute_syngas_molar_mass(
            self.needed_syngas_ratio)
        needed_calorific_value = compute_syngas_calorific_value(
            self.needed_syngas_ratio)

        water_data = Water.data_energy_dict
        water_needs = mol_H20 * water_data['molar_mass'] / \
                      (mol_H2 * needed_syngas_molar_mass *
                       needed_calorific_value)

        return water_needs

    def get_theoretical_co2_prod(self, unit='kg/kWh'):
        ''' 
        Get co2 needs in kg co2 /kWh H2
        1 mol of CO2 for 4 mol of H2
        Warning : molar mass is in g/mol but we divide and multiply by one
        '''

        mol_H2 = (1.0 + self.syngas_ratio) / (1.0 + self.needed_syngas_ratio)
        mol_CO2 = self.syngas_ratio - self.needed_syngas_ratio * mol_H2

        co2_data = CO2.data_energy_dict

        # needed syngas_ratio could be 0 in this case syngas is H2
        needed_syngas_molar_mass = compute_syngas_molar_mass(
            self.needed_syngas_ratio)
        needed_calorific_value = compute_syngas_calorific_value(
            self.needed_syngas_ratio)

        if unit == 'kg/kWh':
            co2_prod = mol_CO2 * co2_data['molar_mass'] / \
                       (mol_H2 * needed_syngas_molar_mass *
                        needed_calorific_value)
        elif unit == 'kg/kg':
            co2_prod = mol_CO2 * co2_data['molar_mass'] / \
                       (mol_H2 * needed_syngas_molar_mass)

        return co2_prod
