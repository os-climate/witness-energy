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

from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.core.stream_type.carbon_models.carbon_monoxyde import CO
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import (
    GaseousHydrogen,
)
from energy_models.core.stream_type.energy_models.syngas import Syngas
from energy_models.core.stream_type.energy_models.syngas import (
    compute_calorific_value as compute_syngas_calorific_value,
)
from energy_models.core.stream_type.energy_models.syngas import (
    compute_molar_mass as compute_syngas_molar_mass,
)
from energy_models.core.stream_type.resources_models.resource_glossary import (
    ResourceGlossary,
)
from energy_models.core.stream_type.resources_models.water import Water
from energy_models.core.techno_type.base_techno_models.syngas_techno import SyngasTechno
from energy_models.glossaryenergy import GlossaryEnergy


class RWGS(SyngasTechno):

    def __init__(self, name):
        super().__init__(name)
        self.esk = None
        self.needed_syngas_ratio = None
        self.syngas_ratio: float = 0.0
        self.needed_syngas_ratio = None
        self.inputs_dict = None
        self.available_power = None
        self.slope_capex: float = 0.0
        self.slope_elec_demand: float = 0.0

    def configure_parameters(self, inputs_dict):

        # We need these lines if both configure because syngas is the coupling variable (so in configure_parameters_update)
        # but is also used in configure energy data for physical parameters (
        # so in configure parameters)
        self.syngas_ratio = np.array(inputs_dict['syngas_ratio']) / 100.0
        self.needed_syngas_ratio = inputs_dict['needed_syngas_ratio'] / 100.0
        self.syngas_COH2_ratio = inputs_dict['syngas_ratio'] / 100.0

        SyngasTechno.configure_parameters(self, inputs_dict)

    def configure_parameters_update(self, inputs_dict):

        # We need these lines if both configure because syngas is the coupling variable (so in configure_parameters_update)
        # but is also used in configure energy data for physical parameters (
        # so in configure parameters)
        self.syngas_ratio = np.array(inputs_dict['syngas_ratio']) / 100.0
        self.needed_syngas_ratio = inputs_dict['needed_syngas_ratio'] / 100.0
        self.syngas_COH2_ratio = inputs_dict['syngas_ratio'] / 100.0

        self.inputs_dict = inputs_dict
        SyngasTechno.configure_parameters_update(self, inputs_dict)

    def check_capex_unity(self, data_config):
        '''
        Overload the check_capex_unity for this particular model 
        '''
        capex_list = np.array(data_config['Capex_init_vs_CO_H2_ratio'])

        # input power was in mol/h
        # We multiply by molar mass and calorific value of the paper to get
        # input power in kW

        final_syngas_ratio = np.array(data_config['CO_H2_ratio'])

        # molar mass is in g/mol !!
        syngas_molar_mass = compute_syngas_molar_mass(final_syngas_ratio)
        syngas_calorific_value = compute_syngas_calorific_value(
            final_syngas_ratio)

        # Available power is now in kW
        self.available_power = np.array(
            data_config['available_power']) * syngas_molar_mass / 1000.0 * syngas_calorific_value
        # Need to convertcapex_list in $/kWh
        capex_list = capex_list / self.available_power / \
                     data_config['full_load_hours']

        initial_syngas_ratio = 0.0
        delta_syngas_ratio = final_syngas_ratio - initial_syngas_ratio

        self.slope_capex = (
                                   capex_list[0] - capex_list[1]) / (delta_syngas_ratio[0] - delta_syngas_ratio[1])
        b = capex_list[0] - self.slope_capex * delta_syngas_ratio[0]

        def func_capex(delta_sg_ratio):
            return self.slope_capex * delta_sg_ratio + b

        # func_capex = sc.interp1d(delta_sg_ratio, capex_list,
        #                         kind='linear', fill_value='extrapolate')

        # func_capex = sc.interp1d(delta_syngas_ratio, capex_list,
        #                         kind='linear', fill_value='extrapolate')

        capex_init = func_capex(
            self.needed_syngas_ratio - self.syngas_ratio[0])

        return capex_init

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
        dinvest_sum = -1.0 * self.initial_production * self.slope_capex
        capex_year = capex_init
        capex_grad[0][0] = -self.slope_capex
        invest_list = self.cost_details[GlossaryEnergy.InvestValue].values
        if min(invest_list.real) < 0:
            invest_list = np.maximum(0.0, invest_list)
        for i, invest in enumerate(invest_list):

            if invest_sum.real < 10.0 or i == 0.0:
                capex_year = capex_init
                capex_grad[i][0] = - self.slope_capex

            else:

                q = ((invest_sum + invest) / invest_sum) ** (-expo_factor)

                #                 dq = -expo_factor * ((invest_sum + invest) / invest_sum) ** (-expo_factor -
                # 1.0) * (-dinvest_sum * invest / (invest_sum * invest_sum))
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

    def compute_dprod_dsyngas_ratio(self, capex_list, invest_list, invest_before_year_start, techno_dict,
                                    dcapexdsyngas):

        # dpprod_dpfluegas = np.zeros(dcapexdfluegas.shape())

        dprod_dcapex = self.compute_dprod_dcapex(
            capex_list, invest_list, techno_dict, invest_before_year_start)
        # dprod_dfluegas = dpprod_dpfluegas + dprod_dcapex * dcapexdfluegas
        if 'complex128' in [capex_list.dtype, invest_list.dtype, invest_before_year_start.dtype, dcapexdsyngas.dtype]:
            arr_type = 'complex128'
        else:
            arr_type = 'float64'
        dprod_dfluegas = np.zeros(dprod_dcapex.shape, dtype=arr_type)
        for line in range(dprod_dcapex.shape[0]):
            for column in range(dprod_dcapex.shape[1]):
                dprod_dfluegas[line, column] = np.matmul(
                    dprod_dcapex[line, :], dcapexdsyngas[:, column])

        return dprod_dfluegas

    def compute_drwgs_dsyngas_ratio(self):

        # compute d energy cost : delectricity + dsyngas + dwater

        dsyngas_price_dsyngas_ratio = self.compute_dsyngas_price_dsyngas_ratio()

        delectricity_price_dsyngas_ratio = self.compute_delectricity_price_dsyngas_ratio()

        dco2_price_dsyngas_ratio = self.compute_dco2_price_dsyngas_ratio()

        margin = self.margin[GlossaryEnergy.MarginValue].values

        denergy_cost_dsyngas_ratio = dsyngas_price_dsyngas_ratio + \
                                     delectricity_price_dsyngas_ratio + \
                                     dco2_price_dsyngas_ratio / (margin / 100)
        # compute d rwgs_factory
        drwgs_factory_dsyngas_ratio = self.compute_drwgs_factory_dsyngas_ratio()

        # compute d transport

        # compute d co2_taxes_factory
        return denergy_cost_dsyngas_ratio + drwgs_factory_dsyngas_ratio

    def compute_drwgs_dsyngas_ratio_wo_taxes(self):

        # compute d energy cost : delectricity + dsyngas + dwater

        dsyngas_price_dsyngas_ratio = self.compute_dsyngas_price_dsyngas_ratio()

        delectricity_price_dsyngas_ratio = self.compute_delectricity_price_dsyngas_ratio()

        denergy_cost_dsyngas_ratio = dsyngas_price_dsyngas_ratio + \
                                     delectricity_price_dsyngas_ratio
        # compute d rwgs_factory
        drwgs_factory_dsyngas_ratio = self.compute_drwgs_factory_dsyngas_ratio()

        # compute d transport

        # compute d co2_taxes_factory
        return denergy_cost_dsyngas_ratio + drwgs_factory_dsyngas_ratio

    def compute_drwgs_factory_dsyngas_ratio(self):

        capex_grad = self.compute_dcapex_dsyngas_ratio()

        crf = self.compute_capital_recovery_factor(self.techno_infos_dict)
        factory_grad = capex_grad * \
                       (crf + self.techno_infos_dict['Opex_percentage'])

        return factory_grad

    def compute_dsyngas_price_dsyngas_ratio(self):

        dsyngas_needs_dsyngas_ratio = self.compute_dsyngas_needs_dsyngas_ratio()

        efficiency = self.compute_efficiency()

        dsyngas_price_dsyngas_ratio = np.identity(len(
            self.years)) * dsyngas_needs_dsyngas_ratio * self.energy_prices[Syngas.name].to_numpy() / efficiency[:,
                                                                                               np.newaxis]

        return dsyngas_price_dsyngas_ratio

    def compute_delectricity_price_dsyngas_ratio(self):
        delectricity_needs_dsyngas_ratio = - np.identity(
            len(self.years)) * self.slope_elec_demand

        delectricity_price_dsyngas_ratio = delectricity_needs_dsyngas_ratio * \
                                           self.energy_prices[Electricity.name].to_numpy()

        return delectricity_price_dsyngas_ratio

    def dtotal_co2_emissions_dsyngas_ratio(self):

        # co2_taxes = (co2_prod + co2_input_energies)

        efficiency = self.compute_efficiency()

        dco2_needs_dsyngas_ratio = self.compute_dco2_needs_dsyngas_ratio() / \
                                   efficiency

        dco2_electricity_dsynags_ratio = -self.slope_elec_demand * \
                                         self.energy_CO2_emissions[Electricity.name].values

        dco2_syngas_dsynags_ratio = (self.compute_dsyngas_needs_dsyngas_ratio(
        ) * self.energy_CO2_emissions[Syngas.name].values / efficiency)

        return dco2_syngas_dsynags_ratio - dco2_needs_dsyngas_ratio + dco2_electricity_dsynags_ratio

    def dco2_taxes_dsyngas_ratio(self):

        # co2_taxes = (co2_prod + co2_input_energies) * co2_taxes

        dco2_emissions_dsyngas_ratio = self.dtotal_co2_emissions_dsyngas_ratio()

        return dco2_emissions_dsyngas_ratio * self.CO2_taxes[GlossaryEnergy.CO2Tax].values

    def compute_dco2_price_dsyngas_ratio(self):
        dco2_needs_dsyngas_ratio = self.compute_dco2_needs_dsyngas_ratio()

        efficiency = self.compute_efficiency()

        dco2_price_dsyngas_ratio = np.identity(len(
            self.years)) * dco2_needs_dsyngas_ratio * self.resources_prices[
                                       ResourceGlossary.CO2Resource].to_numpy() / efficiency[:, np.newaxis]

        return dco2_price_dsyngas_ratio

    def compute_dco2_needs_dsyngas_ratio(self):
        mol_H2 = 1.0

        mol_CO2_up = - self.syngas_ratio * (1.0 + self.needed_syngas_ratio)
        dmol_CO2_up = - (1.0 + self.needed_syngas_ratio)

        mol_CO2_down = (1.0 + self.syngas_ratio)
        dmol_CO2_down = 1.0

        dmol_CO2_dsyngas_ratio = (
                                         dmol_CO2_up * mol_CO2_down - dmol_CO2_down * mol_CO2_up) / mol_CO2_down ** 2

        co2_data = CO2.data_energy_dict

        # needed syngas_ratio could be 0 in this case syngas is H2
        needed_syngas_molar_mass = compute_syngas_molar_mass(
            self.needed_syngas_ratio)
        needed_calorific_value = compute_syngas_calorific_value(
            self.needed_syngas_ratio)

        dco2_needs_dsyngas_ratio = dmol_CO2_dsyngas_ratio * co2_data['molar_mass'] / \
                                   (mol_H2 * needed_syngas_molar_mass *
                                    needed_calorific_value)

        return dco2_needs_dsyngas_ratio

    def compute_dprice_RWGS_dsyngas_ratio(self):
        efficiency = self.compute_efficiency()
        years = np.arange(
            self.inputs_dict[GlossaryEnergy.YearStart], self.inputs_dict[GlossaryEnergy.YearEnd] + 1)
        margin = self.inputs_dict[GlossaryEnergy.MarginValue][GlossaryEnergy.MarginValue].values
        factory_grad = self.compute_drwgs_factory_dsyngas_ratio()

        dsyngas_dsyngas_ratio = np.identity(len(years)) * self.compute_dsyngas_needs_dsyngas_ratio() * \
                                self.energy_prices[Syngas.name].to_numpy() / efficiency.values[:, np.newaxis]

        dprice_dco2_price_dsyngas_ratio = np.identity(
            len(years)) * self.compute_dco2_price_dsyngas_ratio()

        delectricity_price_dsyngas_ratio = np.identity(
            len(years)) * self.compute_delectricity_price_dsyngas_ratio()
        # now syngas is in % grad is divided by 100
        dprice_dsyngas = (
                                 factory_grad + dsyngas_dsyngas_ratio + dprice_dco2_price_dsyngas_ratio + delectricity_price_dsyngas_ratio) \
                         * np.split(margin, len(margin)) / 100.0

        return dprice_dsyngas

    def compute_dprice_RWGS_wo_taxes_dsyngas_ratio(self):
        efficiency = self.compute_efficiency()
        years = np.arange(
            self.inputs_dict[GlossaryEnergy.YearStart], self.inputs_dict[GlossaryEnergy.YearEnd] + 1)
        margin = self.inputs_dict[GlossaryEnergy.MarginValue][GlossaryEnergy.MarginValue].values
        factory_grad = self.compute_drwgs_factory_dsyngas_ratio()

        dsyngas_dsyngas_ratio = np.identity(len(years)) * self.compute_dsyngas_needs_dsyngas_ratio() * \
                                self.energy_prices[Syngas.name].to_numpy() / efficiency[:, np.newaxis]

        dprice_dco2_price_dsyngas_ratio = np.identity(
            len(years)) * self.compute_dco2_price_dsyngas_ratio()

        delectricity_price_dsyngas_ratio = np.identity(
            len(years)) * self.compute_delectricity_price_dsyngas_ratio()
        # now syngas is in % grad is divided by 100
        dprice_dsyngas = (
                                 factory_grad + dsyngas_dsyngas_ratio + dprice_dco2_price_dsyngas_ratio + delectricity_price_dsyngas_ratio) \
                         * np.split(margin, len(margin)) / 100.0

        return dprice_dsyngas

    def get_electricity_needs(self):

        elec_demand = self.techno_infos_dict['elec_demand'] / \
                      self.available_power / self.techno_infos_dict['full_load_hours']
        final_syngas_ratio = np.array(self.techno_infos_dict['CO_H2_ratio'])
        initial_syngas_ratio = 0.0
        delta_syngas_ratio = final_syngas_ratio - initial_syngas_ratio

        self.slope_elec_demand = (elec_demand[0] - elec_demand[1]) / \
                                 (delta_syngas_ratio[0] - delta_syngas_ratio[1])
        b = elec_demand[0] - self.slope_elec_demand * delta_syngas_ratio[0]

        def func_elec_demand(syngas_ratio):
            return self.slope_elec_demand * syngas_ratio + b

        # func_elec_demand = sc.interp1d(delta_syngas_ratio, elec_demand,
        # kind='linear', fill_value='extrapolate')

        elec_demand = func_elec_demand(
            self.needed_syngas_ratio - self.syngas_ratio)
        return elec_demand

    def compute_resources_needs(self):
        self.cost_details[f"{ResourceGlossary.CO2Resource}_needs"] = self.get_theoretical_co2_needs() / self.cost_details['efficiency']

    def compute_other_energies_needs(self):
        self.cost_details[f'{GlossaryEnergy.electricity}_needs'] = self.get_electricity_needs()

        # Cost of methane for 1 kWH of H2
        self.cost_details['syngas_needs'] = self.get_theoretical_syngas_needs(self.syngas_ratio) / self.cost_details['efficiency']


    def compute_production(self):
        th_water_prod = self.get_theoretical_water_prod()

        self.production_detailed[f'{Water.name} ({self.mass_unit})'] = th_water_prod * \
                                                                       self.production_detailed[
                                                                           f'{SyngasTechno.energy_name} ({self.product_energy_unit})']

    def compute_energies_consumption(self):
        """
        Compute the consumption and the production of the technology for a given investment
        Maybe add efficiency in consumption computation ? 
        """

        super().compute_energies_consumption()

        self.consumption_detailed[f'{CarbonCapture.name} ({self.mass_unit})'] = self.cost_details[f"{ResourceGlossary.CO2Resource}_needs"] * \
                                                                                self.production_detailed[
                                                                                    f'{SyngasTechno.energy_name} ({self.product_energy_unit})']  # in kg

    def compute_dprod_water_dsyngas_ratio(self, dprodenergy_dsyngas_ratio, prod_energy):
        dwater_prod_dsyngas_ratio = self.compute_dwater_prod_dsynags_ratio()
        th_water_prod = self.get_theoretical_water_prod()
        return th_water_prod * dprodenergy_dsyngas_ratio + np.identity(
            len(self.years)) * dwater_prod_dsyngas_ratio * prod_energy

    def compute_dcons_electricity_dsyngas_ratio(self, dprodenergy_dsyngas_ratio, prod_energy):
        delectricity_needs_dsyngas_ratio = - np.identity(
            len(self.years)) * self.slope_elec_demand
        electricity_prod = self.get_electricity_needs()

        return delectricity_needs_dsyngas_ratio * prod_energy + electricity_prod * dprodenergy_dsyngas_ratio

    def compute_dco2_emissions_electricity_dsyngas_ratio(self):
        delectricity_needs_dsyngas_ratio = - np.identity(
            len(self.years)) * self.slope_elec_demand
        dco2_emissions_dsyngas_ratio = delectricity_needs_dsyngas_ratio * self.energy_CO2_emissions[
                                                                              Electricity.name].values[:, np.newaxis]

        return dco2_emissions_dsyngas_ratio

    def compute_dcons_co2_dsyngas_ratio(self, dprodenergy_dsyngas_ratio, prod_energy):
        dcons_needs_dsyngas_ratio = self.compute_dco2_needs_dsyngas_ratio()
        co2_prod = self.get_theoretical_co2_needs()
        efficiency = self.compute_efficiency()
        return (np.identity(
            len(self.years)) * dcons_needs_dsyngas_ratio * prod_energy + co2_prod * dprodenergy_dsyngas_ratio) / efficiency[
                                                                                                                 :np.newaxis]

    def compute_dcons_syngas_dsyngas_ratio(self, dprodenergy_dsyngas_ratio, prod_energy):
        dcons_syngas_dsyngas_ratio = self.compute_dsyngas_needs_dsyngas_ratio()
        syngas_prod = self.get_theoretical_syngas_needs(self.syngas_ratio)
        efficiency = self.compute_efficiency()
        return (np.identity(
            len(self.years)) * dcons_syngas_dsyngas_ratio * prod_energy + syngas_prod * dprodenergy_dsyngas_ratio) / efficiency[
                                                                                                                     :np.newaxis]

    def compute_dco2_emissions_syngas_dsyngas_ratio(self):
        dcons_syngas_dsyngas_ratio = self.compute_dsyngas_needs_dsyngas_ratio()
        dco2_emissions_dsyngas_ratio = dcons_syngas_dsyngas_ratio * self.energy_CO2_emissions[
                                                                        Syngas.name].values[:, np.newaxis]

        return dco2_emissions_dsyngas_ratio

    def compute_dco2_emissions_dsyngas_ratio(self):
        dco2_needs_dsyngas_ratio = self.compute_dco2_needs_dsyngas_ratio()
        dco2_emissions_dsyngas_ratio = self.resources_CO2_emissions[
                                           ResourceGlossary.CO2Resource] * dco2_needs_dsyngas_ratio

        return dco2_emissions_dsyngas_ratio

    def get_theoretical_syngas_needs(self, syngas_ratio):
        ''' 
        dCO2 + e(H2 +r1CO)-->  (H2 +r2CO) + cH20 

        e = (1+r2)/(1+r1)
        c = (r2-r1)/(1+r1)
        d = r2 - r1(1+r2)/(1+r1)
        '''
        mol_syngas_in = (1.0 + self.needed_syngas_ratio) / \
                        (1.0 + syngas_ratio)
        mol_syngas_out = 1.0

        syngas_molar_mass_in = compute_syngas_molar_mass(syngas_ratio)
        syngas_calorific_value_in = compute_syngas_calorific_value(
            syngas_ratio)

        # needed syngas_ratio could be 0 in this case syngas is H2
        syngas_molar_mass_out = compute_syngas_molar_mass(
            self.needed_syngas_ratio)
        calorific_value_out = compute_syngas_calorific_value(
            self.needed_syngas_ratio)

        syngas_needs = mol_syngas_in * syngas_molar_mass_in * syngas_calorific_value_in / \
                       (mol_syngas_out * syngas_molar_mass_out *
                        calorific_value_out)

        return syngas_needs

    def compute_dsyngas_needs_dsyngas_ratio(self):

        #############

        dmol_syngas_in_dsyngas_ratio = - \
                                           (1.0 + self.needed_syngas_ratio) / (1.0 + self.syngas_ratio) ** 2

        ####

        # syngas_molar_mass_in (self.syngas_ratio * CO.data_energy_dict['molar_mass'] +
        # Hydrogen.data_energy_dict['molar_mass']) / (1.0 + self.syngas_ratio)
        syngas_molar_mass_in_up = (self.syngas_ratio * CO.data_energy_dict['molar_mass'] +
                                   GaseousHydrogen.data_energy_dict['molar_mass'])

        dsyngas_molar_mass_in_up_dsynags_ratio = CO.data_energy_dict['molar_mass']

        syngas_molar_mass_in_down = (1.0 + self.syngas_ratio)

        dsyngas_molar_mass_in_down_dsyngas_ratio = 1.0

        dsyngas_molar_mass_in_dsyngas_ratio = (dsyngas_molar_mass_in_up_dsynags_ratio * syngas_molar_mass_in_down -
                                               syngas_molar_mass_in_up * dsyngas_molar_mass_in_down_dsyngas_ratio) / syngas_molar_mass_in_down ** 2

        ######
        # (syngas_ratio * CO.data_energy_dict['molar_mass'] * CO.data_energy_dict['calorific_value'] +
        # Hydrogen.data_energy_dict['molar_mass'] *
        # Hydrogen.data_energy_dict['calorific_value']) /
        # (Hydrogen.data_energy_dict['molar_mass'] + syngas_ratio *
        # CO.data_energy_dict['molar_mass'])

        syngas_calorific_value_in_up = (
                self.syngas_ratio * CO.data_energy_dict['molar_mass'] * CO.data_energy_dict['calorific_value'] +
                GaseousHydrogen.data_energy_dict['molar_mass'] * GaseousHydrogen.data_energy_dict[
                    'calorific_value'])

        dsyngas_calorific_value_in_up_dsyngas_ratio = CO.data_energy_dict[
                                                          'molar_mass'] * CO.data_energy_dict['calorific_value']

        syngas_calorific_value_in_down = (
                GaseousHydrogen.data_energy_dict['molar_mass'] + self.syngas_ratio * CO.data_energy_dict['molar_mass'])

        dsyngas_calorific_value_in_down_dsyngas_ratio = CO.data_energy_dict['molar_mass']

        dsyngas_calorific_value_in_dysngas_ratio = (
                                                           dsyngas_calorific_value_in_up_dsyngas_ratio * syngas_calorific_value_in_down -
                                                           syngas_calorific_value_in_up * dsyngas_calorific_value_in_down_dsyngas_ratio) / syngas_calorific_value_in_down ** 2

        ########

        mol_syngas_in = (1.0 + self.needed_syngas_ratio) / \
                        (1.0 + self.syngas_ratio)
        mol_syngas_out = 1.0

        syngas_molar_mass_in = compute_syngas_molar_mass(self.syngas_ratio)
        syngas_calorific_value_in = compute_syngas_calorific_value(
            self.syngas_ratio)

        # needed syngas_ratio could be 0 in this case syngas is H2
        syngas_molar_mass_out = compute_syngas_molar_mass(
            self.needed_syngas_ratio)
        calorific_value_out = compute_syngas_calorific_value(
            self.needed_syngas_ratio)

        dsyngas_needs_dsyngas_ratio = (
                                              dmol_syngas_in_dsyngas_ratio * syngas_molar_mass_in * syngas_calorific_value_in + mol_syngas_in *
                                              dsyngas_molar_mass_in_dsyngas_ratio * syngas_calorific_value_in +
                                              mol_syngas_in * syngas_molar_mass_in * dsyngas_calorific_value_in_dysngas_ratio) / (
                                              mol_syngas_out * syngas_molar_mass_out *
                                              calorific_value_out)

        return dsyngas_needs_dsyngas_ratio

    def get_theoretical_water_prod(self):
        ''' 
        dCO2 + e(H2 +r1CO)-->  (H2 +r2CO) + cH20 

        e = (1+r2)/(1+r1)
        c = (r2-r1)/(1+r1)
        d = r2 - r1(1+r2)/(1+r1)
        '''

        mol_H20 = (self.needed_syngas_ratio - self.syngas_ratio) / \
                  (1.0 + self.syngas_ratio)
        mol_H2 = 1.0

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

    def compute_dwater_prod_dsynags_ratio(self):
        mol_H20_up = (self.needed_syngas_ratio - self.syngas_ratio)

        dmol_H20_up = -1.0

        mol_H20_down = (1.0 + self.syngas_ratio)

        dmol_H20_down = 1.0

        dmol_H20_dsyngas_ratio = (
                                         dmol_H20_up * mol_H20_down - dmol_H20_down * mol_H20_up) / mol_H20_down ** 2

        mol_H2 = 1.0

        # needed syngas_ratio could be 0 in this case syngas is H2
        needed_syngas_molar_mass = compute_syngas_molar_mass(
            self.needed_syngas_ratio)
        needed_calorific_value = compute_syngas_calorific_value(
            self.needed_syngas_ratio)

        water_data = Water.data_energy_dict

        dwater_needs_dsyngas_ratio = dmol_H20_dsyngas_ratio * water_data['molar_mass'] / \
                                     (mol_H2 * needed_syngas_molar_mass *
                                      needed_calorific_value)

        return dwater_needs_dsyngas_ratio

    def get_theoretical_co2_needs(self, unit='kg/kWh'):
        ''' 
        dCO2 + e(H2 +r1CO)-->  (H2 +r2CO) + cH20 

        e = (1+r2)/(1+r1)
        c = (r2-r1)/(1+r1)
        d = r2 - r1(1+r2)/(1+r1)
        '''

        mol_H2 = 1.0
        mol_CO2 = self.needed_syngas_ratio - self.syngas_ratio * (1.0 + self.needed_syngas_ratio) / \
                  (1.0 + self.syngas_ratio)

        co2_data = CO2.data_energy_dict

        # needed syngas_ratio could be 0 in this case syngas is H2
        needed_syngas_molar_mass = compute_syngas_molar_mass(
            self.needed_syngas_ratio)
        needed_calorific_value = compute_syngas_calorific_value(
            self.needed_syngas_ratio)

        if unit == 'kg/kWh':
            co2_needs = mol_CO2 * co2_data['molar_mass'] / \
                        (mol_H2 * needed_syngas_molar_mass *
                         needed_calorific_value)
        elif unit == 'kg/kg':
            co2_needs = mol_CO2 * co2_data['molar_mass'] / \
                        (mol_H2 * needed_syngas_molar_mass)
        else:
            raise Exception("The unit is not handled")
        return co2_needs
