'''
Copyright 2022 Airbus SAS
Modifications on 2023/10/10-2023/11/16 Copyright 2023 Capgemini

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
from energy_models.core.stream_type.energy_models.syngas import \
    compute_calorific_value as compute_syngas_calorific_value
from energy_models.core.stream_type.energy_models.syngas import compute_molar_mass as compute_syngas_molar_mass
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
from energy_models.core.techno_type.disciplines.gaseous_hydrogen_techno_disc import GaseousHydrogenTechnoDiscipline
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.gaseous_hydrogen.water_gas_shift.water_gas_shift import WGS


class WaterGasShiftDiscipline(GaseousHydrogenTechnoDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Water Gas Shift Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-burn fa-fw',
        'version': '',
    }

    techno_name = 'WaterGasShift'
    # Giuliano, A., Freda, C. and Catizzone, E., 2020.
    # Techno-economic assessment of bio-syngas production for methanol synthesis: A focus on the water gas shift and carbon capture sections.
    # Bioengineering, 7(3), p.70.
    lifetime = 20  # Giuliano2020 amortized on 20 years
    construction_delay = 2  # years in Giuliano2020
    techno_infos_dict_default = {'maturity': 5,
                                 'reaction': 'syngas(H2+r1CO) + cH20  = dCO2 + e(H2+r2C0)',
                                 # p8 of Giuliano2020 : Maintenance and labor costs were associated to the capital costs and
                                 # estimated as 10% of the annual total capital
                                 # costs
                                 'Opex_percentage': 0.1,
                                 # Giuliano2020 : the elec demand is more or
                                 # less constant 6.6 MW for WGS over the 8.6
                                 'elec_demand': 6.6e3,
                                 'elec_demand_unit': 'kW',
                                 'WACC': 0.0878,  # Weighted averaged cost of capital for the carbon capture plant
                                 'learning_rate': 0.2,
                                 'lifetime': lifetime,  # for now constant in time but should increase with time
                                 'lifetime_unit': GlossaryEnergy.Years,
                                 # Capex initial at year 2020
                                 'Capex_init_vs_CO_conversion': [5.0e6, 9.2e6],
                                 'Capex_init_vs_CO_conversion_unit': 'euro',
                                 'low_heat_production': (41 / 46.016) * 1000 * 2.77778e-13,
                                 # CO+H2O→CO2+H2ΔH°=−41kJ/mol, Co2(44g/mol),H2(2.016g/mol)
                                 'low_heat_production_unit': 'TWh/kg',
                                 # Capex initial at year 2020
                                 'CO_conversion': [36.0, 100.0],
                                 'CO_conversion_unit': '%',
                                 'euro_dollar': 1.12,  # in June 2020
                                 'full_load_hours': 7920,
                                 'input_power': 861.0e3,
                                 # Wang, Y., Li, G., Liu, Z., Cui, P., Zhu, Z. and Yang, S., 2019.
                                 # Techno-economic analysis of biomass-to-hydrogen process in comparison with coal-to-hydrogen process.
                                 # Energy, 185, pp.1063-1075.
                                 # From Wang2019 Fig 10 ratio of energies
                                 'efficiency': 80.787 / (80.787 + 8.37),
                                 # perfectly efficient
                                 'input_power_unit': 'mol/h',
                                 'techno_evo_eff': 'no',  # yes or no
                                 GlossaryEnergy.ConstructionDelay: construction_delay}

    # Fake investments (not found in the litterature...)
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), GlossaryEnergy.InvestValue: [0.1715, 0.1715]})
    # From Future of hydrogen : accounting for around three quarters of the
    # annual global dedicated hydrogen production of around 70 million tonnes. and 23+ from coal gasification
    # that means that WGS is used for 98% of the hydrogen production
    initial_production = 70.0 * 33.3 * \
                         0.98  # in TWh at year_start MT*kWh/kg = TWh

    # Fake initial age distrib (not found in the litterature...)
    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': np.array(
                                                 [3.317804973859207, 6.975128305927281, 4.333201737255864,
                                                  3.2499013031833868, 1.5096723255070685, 1.7575996841282722,
                                                  4.208448479896288, 2.7398341887870643, 5.228582707722979,
                                                  10.057639166085064, 0.0, 2.313462297352473, 6.2755625737595535,
                                                  5.609159099363739, 6.3782076592711885, 8.704303197679629,
                                                  6.1950256610618135, 3.7836557445596464, 1.7560205289962763,
                                                  ]) + 0.82141})
    FLUE_GAS_RATIO = np.array([0.175])

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'age': ('int', [0, 100], False),
                                                                'distrib': ('float', None, True)},
                                       'dataframe_edition_locked': False},
               GlossaryEnergy.InvestmentBeforeYearStartValue: {'type': 'dataframe', 'unit': 'G$',
                                                               'default': invest_before_year_start,
                                                               'dataframe_descriptor': {
                                                                   'past years': ('int', [-20, -1], False),
                                                                   GlossaryEnergy.InvestValue: ('float', None, True)},
                                                               'dataframe_edition_locked': False},
               'syngas_ratio': {'type': 'array', 'unit': '%',
                                'visibility': GaseousHydrogenTechnoDiscipline.SHARED_VISIBILITY,
                                'namespace': 'ns_syngas'},
               'needed_syngas_ratio': {'type': 'float', 'default': 0.0, 'unit': '%'}
               }
    # -- add specific techno inputs to this
    DESC_IN.update(GaseousHydrogenTechnoDiscipline.DESC_IN)

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = WGS(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)

    def compute_sos_jacobian(self):
        # Grad of price vs energyprice

        GaseousHydrogenTechnoDiscipline.compute_sos_jacobian(self)

        syngas_ratio = self.techno_model.syngas_ratio

        inputs_dict = self.get_sosdisc_inputs()
        ##############
        needed_syngas_molar_mass = compute_syngas_molar_mass(
            self.techno_model.needed_syngas_ratio)
        needed_calorific_value = compute_syngas_calorific_value(
            self.techno_model.needed_syngas_ratio)

        ###################

        dsyngas_needs_dsyngas_ratio = self.techno_model.compute_dsyngas_needs_dsyngas_ratio()

        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoDetailedPricesValue, 'syngas_needs'), ('syngas_ratio',),
            np.identity(len(self.techno_model.years)) * dsyngas_needs_dsyngas_ratio / 100.0)

        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoDetailedPricesValue, 'elec_needs'), ('syngas_ratio',),
            np.zeros(len(self.techno_model.years), ) * dsyngas_needs_dsyngas_ratio / 100.0)

        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoDetailedPricesValue, 'transport'), ('syngas_ratio',),
            np.zeros(len(self.techno_model.years), ) * dsyngas_needs_dsyngas_ratio / 100.0)

        capex_grad = self.techno_model.compute_dcapex_dsyngas_ratio()
        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoDetailedPricesValue, 'Capex_WaterGasShift'), ('syngas_ratio',), capex_grad / 100.0)

        dwater_needs_dsyngas_ratio = self.techno_model.compute_dwater_needs_dsyngas_ratio()

        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoDetailedPricesValue, 'water_needs'), ('syngas_ratio',),
            np.identity(len(self.techno_model.years)) * dwater_needs_dsyngas_ratio / 100.0)

        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoDetailedPricesValue, GlossaryEnergy.electricity), ('syngas_ratio',),
            np.zeros(len(self.techno_model.years), ))

        efficiency = self.techno_model.configure_efficiency()
        dsyngas_dsyngas_ratio = np.identity(len(
            self.techno_model.years)) * dsyngas_needs_dsyngas_ratio * self.techno_model.prices[
                                    GlossaryEnergy.syngas].to_numpy() / efficiency[:, np.newaxis]
        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoDetailedPricesValue, GlossaryEnergy.syngas), ('syngas_ratio',), dsyngas_dsyngas_ratio / 100.0)

        dwater_dsyngas_ratio = np.identity(len(
            self.techno_model.years)) * dwater_needs_dsyngas_ratio * self.techno_model.resources_prices[
                                   ResourceGlossary.Water['name']].to_numpy() / efficiency[:, np.newaxis]

        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoDetailedPricesValue, ResourceGlossary.Water['name']), ('syngas_ratio',),
            dwater_dsyngas_ratio / 100.0)

        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoDetailedPricesValue, 'energy_costs'), ('syngas_ratio',),
            (dsyngas_dsyngas_ratio + dwater_dsyngas_ratio) / 100.0)

        mol_H2 = (1.0 + syngas_ratio) / \
                 (1.0 + self.techno_model.needed_syngas_ratio)

        dmol_H2up = 1.0

        mol_H2down = (1.0 + self.techno_model.needed_syngas_ratio)

        dmol_H2_dsyngas_ratio = (dmol_H2up * mol_H2down) / mol_H2down ** 2

        # # CO2 emissions
        co2_data = CO2.data_energy_dict
        mol_CO2 = syngas_ratio - self.techno_model.needed_syngas_ratio * mol_H2

        dmol_CO2_dsyngas_ratio = 1 - \
                                 self.techno_model.needed_syngas_ratio * dmol_H2_dsyngas_ratio

        #         co2_prod = mol_CO2 * co2_data['molar_mass'] / \
        #             (mol_H2 * needed_syngas_molar_mass *
        #              needed_calorific_value)

        dco2_prod_dsyngas_ratio = self.techno_model.compute_dco2_prod_dsyngas_ratio(
            mol_CO2, mol_H2, co2_data['molar_mass'], needed_syngas_molar_mass, needed_calorific_value,
            dmol_CO2_dsyngas_ratio, dmol_H2_dsyngas_ratio)

        #         self.set_partial_derivative_for_other_types(
        #             (GlossaryEnergy.CO2EmissionsValue, 'production'),  ('syngas_ratio',), np.identity(len(self.techno_model.years)) * dco2_prod_dsyngas_ratio)

        dco2_syngas_dsyngas_ratio = self.techno_model.dco2_syngas_dsyngas_ratio()

        #         self.set_partial_derivative_for_other_types(
        #             (GlossaryEnergy.CO2EmissionsValue, GlossaryEnergy.syngas),  ('syngas_ratio',), np.identity(len(self.techno_model.years)) * dco2_syngas_dsyngas_ratio)
        #
        #         self.set_partial_derivative_for_other_types(
        #             (GlossaryEnergy.CO2EmissionsValue, GlossaryEnergy.electricity),  ('syngas_ratio',), np.zeros(len(self.techno_model.years),))

        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.CO2EmissionsValue, 'WaterGasShift'), ('syngas_ratio',),
            np.identity(len(self.techno_model.years)) * (dco2_prod_dsyngas_ratio + dco2_syngas_dsyngas_ratio) / 100.0)

        CO2_emissions_is_positive = np.maximum(0.0, np.sign(
            self.techno_model.carbon_intensity['WaterGasShift'].values))
        dprice_CO2_fact = np.identity(
            len(self.techno_model.years)) * (dco2_prod_dsyngas_ratio + dco2_syngas_dsyngas_ratio) * \
                          self.techno_model.CO2_taxes.loc[self.techno_model.CO2_taxes[GlossaryEnergy.Years]
                                                          <= self.techno_model.year_end][
                              GlossaryEnergy.CO2Tax].values * CO2_emissions_is_positive

        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoDetailedPricesValue, 'CO2_taxes_factory'), ('syngas_ratio',),
            np.identity(len(self.techno_model.years)) * dprice_CO2_fact / 100.0)

        capex = self.get_sosdisc_outputs(GlossaryEnergy.TechnoDetailedPricesValue)[
            f'Capex_{self.techno_name}'].values

        dprodenergy_dsyngas_ratio = self.techno_model.compute_dprod_dfluegas(
            capex, self.techno_model.invest_level[GlossaryEnergy.InvestValue].values,
            self.techno_model.invest_before_ystart[GlossaryEnergy.InvestValue].values,
            self.techno_model.techno_infos_dict, capex_grad)
        scaling_factor_techno_production = inputs_dict[
            'scaling_factor_techno_production']

        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoProductionValue, f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen} (TWh)'), ('syngas_ratio',),
            dprodenergy_dsyngas_ratio * self.techno_model.applied_ratio['applied_ratio'].values[:,
                                        np.newaxis] / 100.0 / scaling_factor_techno_production)

        production_energy = self.get_sosdisc_outputs(
            GlossaryEnergy.TechnoProductionValue)[f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen} (TWh)']

        co2_prod = self.techno_model.get_theoretical_co2_prod()

        # co2_flue_gas = co2_prod * production_energy

        dco2_flue_gas_dsyngas_ratio = co2_prod[:, np.newaxis] * dprodenergy_dsyngas_ratio * \
                                      self.techno_model.applied_ratio['applied_ratio'].values[:,
                                      np.newaxis] / scaling_factor_techno_production + \
                                      np.identity(len(self.techno_model.years)) * dco2_prod_dsyngas_ratio * \
                                      production_energy.to_numpy()
        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoProductionValue, 'CO2 from Flue Gas (Mt)'), ('syngas_ratio',),
            dco2_flue_gas_dsyngas_ratio / 100.0)

        #######################################

        # electricity

        scaling_factor_techno_consumption = inputs_dict['scaling_factor_techno_consumption']

        delec_consumption_dsyngas_ratio = self.techno_model.compute_delec_needs_dsyngas_ratio(
            dprodenergy_dsyngas_ratio * self.techno_model.applied_ratio['applied_ratio'].values[:,
                                        np.newaxis] / scaling_factor_techno_consumption)
        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoConsumptionValue, f'{GlossaryEnergy.electricity} (TWh)'), ('syngas_ratio',),
            delec_consumption_dsyngas_ratio / 100.0)

        delec_consumption_woratio_dsyngas_ratio = self.techno_model.compute_delec_needs_dsyngas_ratio(
            dprodenergy_dsyngas_ratio / scaling_factor_techno_consumption)
        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoConsumptionWithoutRatioValue, f'{GlossaryEnergy.electricity} (TWh)'), ('syngas_ratio',),
            delec_consumption_woratio_dsyngas_ratio / 100.0)

        dsyngas_consumption_dsyngas_ratio = self.techno_model.compute_dsyngas_consumption_dsyngas_ratio(
            dsyngas_needs_dsyngas_ratio,
            dprodenergy_dsyngas_ratio * self.techno_model.applied_ratio['applied_ratio'].values[:,
                                        np.newaxis] / scaling_factor_techno_consumption,
            production_energy * scaling_factor_techno_production / scaling_factor_techno_consumption)
        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoConsumptionValue, f'{GlossaryEnergy.syngas} (TWh)'), ('syngas_ratio',),
            dsyngas_consumption_dsyngas_ratio / 100.0)

        production_energy_woratio = self.techno_model.production_woratio[
            f'{GlossaryEnergy.hydrogen}.{GlossaryEnergy.gaseous_hydrogen} (TWh)']
        dsyngas_consumption_woratio_dsyngas_ratio = self.techno_model.compute_dsyngas_consumption_dsyngas_ratio(
            dsyngas_needs_dsyngas_ratio, dprodenergy_dsyngas_ratio / scaling_factor_techno_consumption,
                                         production_energy_woratio * scaling_factor_techno_production / scaling_factor_techno_consumption)
        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoConsumptionWithoutRatioValue, f'{GlossaryEnergy.syngas} (TWh)'), ('syngas_ratio',),
            dsyngas_consumption_woratio_dsyngas_ratio / 100.0)

        dwater_consumption_dsyngas_ratio = self.techno_model.compute_dwater_consumption_dsyngas_ratio(
            dwater_needs_dsyngas_ratio,
            dprodenergy_dsyngas_ratio * self.techno_model.applied_ratio['applied_ratio'].values[:,
                                        np.newaxis] / scaling_factor_techno_consumption,
            production_energy * scaling_factor_techno_production / scaling_factor_techno_consumption)
        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoConsumptionValue, f"{ResourceGlossary.Water['name']} (Mt)"), ('syngas_ratio',),
            dwater_consumption_dsyngas_ratio / 100.0)
        dwater_consumption_woratio_dsyngas_ratio = self.techno_model.compute_dwater_consumption_dsyngas_ratio(
            dwater_needs_dsyngas_ratio, dprodenergy_dsyngas_ratio / scaling_factor_techno_consumption,
                                        production_energy_woratio * scaling_factor_techno_production / scaling_factor_techno_consumption)
        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoConsumptionWithoutRatioValue, f"{ResourceGlossary.Water['name']} (Mt)"),
            ('syngas_ratio',), dwater_consumption_woratio_dsyngas_ratio / 100.0)

        ###################################

        dprice_dsyngas = self.techno_model.compute_dprice_WGS_dsyngas_ratio()
        dprice_wotaxes_dsyngas = self.techno_model.compute_dprice_WGS_wo_taxes_dsyngas_ratio()

        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoPricesValue, f'{self.techno_name}'), ('syngas_ratio',), dprice_dsyngas / 100.0)
        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoPricesValue, f'{self.techno_name}_wotaxes'), ('syngas_ratio',),
            dprice_wotaxes_dsyngas / 100.0)

        # We use the function of the invest for the syngas ratio
        # We assume :# we do not divide by / self.scaling_factor_invest_level because invest
        # and non_use_capital are in G$
        # Here the gradient is vs the syngas ratio then we need to divide by self.scaling_factor_invest_level
        # division by 100 because syngas ratio is in %
        dnon_use_capital_dsyngas_ratio, dtechnocapital_dsyngas_ratio = self.techno_model.compute_dnon_usecapital_dinvest(
            capex_grad, dprodenergy_dsyngas_ratio)
        scaling_factor_invest_level = inputs_dict['scaling_factor_invest_level']
        self.set_partial_derivative_for_other_types(
            ('non_use_capital', self.techno_model.name), ('syngas_ratio',),
            dnon_use_capital_dsyngas_ratio / 100.0 / scaling_factor_invest_level)

        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoCapitalValue, GlossaryEnergy.Capital), ('syngas_ratio',),
            dtechnocapital_dsyngas_ratio / 100.0 / scaling_factor_invest_level)

    def specific_run(self):

        # -- get inputs
        inputs_dict = deepcopy(self.get_sosdisc_inputs())
        years = np.arange(inputs_dict[GlossaryEnergy.YearStart],
                          inputs_dict[GlossaryEnergy.YearEnd] + 1)
        detailed_prod_syngas_prices = pd.DataFrame(
            {GlossaryEnergy.Years: years})
        for techno in inputs_dict['energy_detailed_techno_prices']:
            if techno != GlossaryEnergy.Years:
                techno_model = WGS(self.techno_name)
                # Update init values syngas price and syngas_ratio
                inputs_dict[GlossaryEnergy.EnergyPricesValue][GlossaryEnergy.syngas] = inputs_dict['energy_detailed_techno_prices'][
                    techno]
                inputs_dict['syngas_ratio'] = np.ones(
                    len(years)) * inputs_dict['syngas_ratio_technos'][techno]
                # -- configure class with inputs
                techno_model.configure_parameters(inputs_dict)
                techno_model.configure_parameters_update(inputs_dict)
                # -- compute informations

                # Compute the price with these new values
                techno_syngas_price = techno_model.compute_price()
                # Store only the overall price

                global_techno = f'{techno} + WGS'
                detailed_prod_syngas_prices[global_techno] = techno_syngas_price[self.techno_name]

        self.store_sos_outputs_values(
            {'detailed_prod_syngas_prices': detailed_prod_syngas_prices})
