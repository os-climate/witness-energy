'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2024/03/27 Copyright 2023 Capgemini

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

from energy_models.core.techno_type.disciplines.syngas_techno_disc import (
    SyngasTechnoDiscipline,
)
from energy_models.core.techno_type.techno_disc import TechnoDiscipline
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.syngas.reversed_water_gas_shift.reversed_water_gas_shift import (
    RWGS,
)


class RWGSDiscipline(SyngasTechnoDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Reversed Water Gas Shift Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': '',
        'version': '',
    }

    techno_name = GlossaryEnergy.ReversedWaterGasShift
    lifetime = 20
    techno_infos_dict_default = {'maturity': 5,
                                 'reaction': 'dCO2 + e(H2+r1C0) = syngas(H2+r2CO) + cH20',
                                 'CO2_from_production': 0.0,
                                 'Opex_percentage': 0.01,
                                 # Giuliano, A., Freda, C. and Catizzone, E., 2020.
                                 # Techno-economic assessment of bio-syngas production for methanol synthesis: A focus on the water-gas shift and carbon capture sections.
                                 # Bioengineering, 7(3), p.70.
                                 # Giuliano2020 : the elec demand is more or
                                 # less constant 6.6 MW for WGS over the 8.6

                                 'WACC': 0.0878,  # Weighted averaged cost of capital for the carbon capture plant
                                 'learning_rate': 0.2,
                                 'lifetime': lifetime,  # for now constant in time but should increase with time
                                 # Capex at table 3 and 8
                                 'Capex_init_vs_CO_H2_ratio': [37.47e6, 113.45e6],
                                 'Capex_init_vs_CO_H2_ratio_unit': '$',
                                 # Capex initial at year 2020
                                 'CO_H2_ratio': [1.0, 0.5],
                                 'available_power': [4000.0e3, 22500.0e3],
                                 'available_power_unit': 'mol/h',
                                 # price for elec divided by elec price in the
                                 # paper
                                 'elec_demand': [13e6 / 0.07, 61.8e6 / 0.07],
                                 'elec_demand_unit': 'kWh',
                                 # Rezaei, E. and Dzuryk, S., 2019.
                                 # Techno-economic comparison of reverse water gas shift reaction to steam and
                                 # dry methane reforming reactions for syngas production.
                                 # Chemical engineering research and design,
                                 # 144, pp.354-369.
                                 'full_load_hours': 8240,  # p357 rezaei2019

                                 'efficiency': 0.75,  # pump + compressor efficiency Rezaei2019
                                 'techno_evo_eff': 'no',  # yes or no
                                 }

    # Fake investments (not found in the litterature...)
        # From Future of hydrogen : accounting for around three quarters of the
    # annual global dedicated hydrogen production of around 70 million tonnes. and 23+ from coal gasification
    # that means that WGS is used for 98% of the hydrogen production
    initial_production = 0.0

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

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
                      'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'age': ('int', [0, 100], False),
                                                                'distrib': ('float', None, True)},
                                       'dataframe_edition_locked': False},
               
               'syngas_ratio': {'type': 'array', 'unit': '%'},
               'needed_syngas_ratio': {'type': 'float', 'unit': '%'}
               }
    # -- add specific techno inputs to this
    DESC_IN.update(SyngasTechnoDiscipline.DESC_IN)
    DESC_OUT = TechnoDiscipline.DESC_OUT

    # -- add specific techno outputs to this

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = RWGS(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)

    def run(self):
        TechnoDiscipline.run(self)

    def compute_sos_jacobian(self):
        # Grad of price vs energyprice
        inputs_dict = self.get_sosdisc_inputs()

        # self.techno_model.compute_price()
        SyngasTechnoDiscipline.compute_sos_jacobian(self)

        grad_dict = self.techno_model.grad_price_vs_stream_price()

        carbon_emissions = self.get_sosdisc_outputs(GlossaryEnergy.CO2EmissionsValue)

        self.set_partial_derivatives_techno(
            grad_dict, carbon_emissions)

        years = np.arange(inputs_dict[GlossaryEnergy.YearStart],
                          inputs_dict[GlossaryEnergy.YearEnd] + 1)

        dsyngas_needs_dsyngas_ratio = self.techno_model.compute_dsyngas_needs_dsyngas_ratio()

        margin = self.techno_model.margin[GlossaryEnergy.MarginValue].values
        # now syngas is in % grad is divided by 100
        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoDetailedPricesValue, 'syngas_needs'), ('syngas_ratio',),
            np.identity(len(years)) * dsyngas_needs_dsyngas_ratio / 100.0)

        # now syngas is in % grad is divided by 100
        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoDetailedPricesValue, f'{GlossaryEnergy.electricity}_needs'), ('syngas_ratio',), -np.identity(
                len(years)) * self.techno_model.slope_elec_demand / 100.0)

        dprice_techno_dsyngas_ratio = self.techno_model.compute_drwgs_dsyngas_ratio()
        # now syngas is in % grad is divided by 100
        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoPricesValue, f'{self.techno_name}'), ('syngas_ratio',),
            dprice_techno_dsyngas_ratio * np.split(margin, len(margin)) / 100.0 / 100.0)

        dprice_techno_dsyngas_ratio_wo_taxes = self.techno_model.compute_drwgs_dsyngas_ratio_wo_taxes()
        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoPricesValue, f'{self.techno_name}_wotaxes'), ('syngas_ratio',),
            dprice_techno_dsyngas_ratio_wo_taxes * np.split(margin, len(margin)) / 100.0 / 100.0)

        dprice_techno_wotaxes_dsyngas_ratio = self.techno_model.compute_drwgs_dsyngas_ratio()
        # now syngas is in % grad is divided by 100
        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoPricesValue, f'{self.techno_name}_wotaxes'), ('syngas_ratio',),
            dprice_techno_wotaxes_dsyngas_ratio * np.split(margin, len(margin)) / 100.0 / 100.0)
        # now syngas is in % grad is divided by 100
        drwgs_factory_dsyngas_ratio = self.techno_model.compute_drwgs_factory_dsyngas_ratio()
        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoDetailedPricesValue, f'{self.techno_name}_factory'), ('syngas_ratio',),
            drwgs_factory_dsyngas_ratio / 100.0)
        # now syngas is in % grad is divided by 100
        dprice_CO2 = self.techno_model.compute_dco2_needs_dsyngas_ratio()
        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoDetailedPricesValue, f"{GlossaryEnergy.CO2Resource}_needs"), ('syngas_ratio',),
            np.identity(len(years)) * dprice_CO2 / 100.0)

        #         self.set_partial_derivative_for_other_types(
        #             (GlossaryEnergy.CO2EmissionsValue, 'production'),  ('syngas_ratio',), np.zeros(len(years),))

        capex = self.get_sosdisc_outputs(GlossaryEnergy.TechnoDetailedPricesValue)[
            f'Capex_{self.techno_name}'].values

        capex_grad = self.techno_model.compute_dcapex_dsyngas_ratio()
        dprodenergy_dsyngas_ratio = self.techno_model.compute_dprod_dsyngas_ratio(
            capex, inputs_dict[GlossaryEnergy.InvestLevelValue][GlossaryEnergy.InvestValue].values,
            inputs_dict[GlossaryEnergy.InvestmentBeforeYearStartValue][GlossaryEnergy.InvestValue].values,
            inputs_dict['techno_infos_dict'], capex_grad)
        prod_energy = self.get_sosdisc_outputs(
            GlossaryEnergy.TechnoProductionValue)[f'{GlossaryEnergy.syngas} ({GlossaryEnergy.energy_unit})'].to_numpy()

        dco2_emissions_dsyngas_ratio = self.techno_model.compute_dco2_emissions_dsyngas_ratio()
        dcons_syngas_dsyngas_ratio = self.techno_model.compute_dco2_emissions_syngas_dsyngas_ratio()
        dcons_electricity_dsyngas_ratio = self.techno_model.compute_dco2_emissions_electricity_dsyngas_ratio()
        efficiency = self.techno_model.compute_efficiency()

        scaling_factor_techno_consumption = self.get_sosdisc_inputs(
            'scaling_factor_techno_consumption')
        scaling_factor_techno_production = self.get_sosdisc_inputs(
            'scaling_factor_techno_production')

        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.CO2EmissionsValue, GlossaryEnergy.ReversedWaterGasShift), ('syngas_ratio',),
            np.identity(len(years)) / 100.0 * (dco2_emissions_dsyngas_ratio.to_numpy() +
                                               dcons_syngas_dsyngas_ratio) / efficiency[:, np.newaxis]
            + dcons_electricity_dsyngas_ratio)

        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoDetailedPricesValue, f'Capex_{self.techno_name}'), ('syngas_ratio',),
            capex_grad / 100.0)

        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoProductionValue, f'{GlossaryEnergy.syngas} ({GlossaryEnergy.energy_unit})'), ('syngas_ratio',),
            dprodenergy_dsyngas_ratio / 100.0 / scaling_factor_techno_production)

        dwater_prod_dsyngas_ratio = self.techno_model.compute_dprod_water_dsyngas_ratio(
            dprodenergy_dsyngas_ratio, prod_energy)

        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoProductionValue, f"{GlossaryEnergy.WaterResource} ({GlossaryEnergy.mass_unit})"), ('syngas_ratio',),
            dwater_prod_dsyngas_ratio / 100.0 / scaling_factor_techno_production)

        dcons_electricity_dsyngas_ratio = self.techno_model.compute_dcons_electricity_dsyngas_ratio(
            dprodenergy_dsyngas_ratio, prod_energy)

        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoConsumptionValue, f'{GlossaryEnergy.electricity} ({GlossaryEnergy.energy_unit})'), ('syngas_ratio',),
            dcons_electricity_dsyngas_ratio / 100.0 / scaling_factor_techno_consumption)

        dcons_syngas_dsyngas_ratio = self.techno_model.compute_dcons_syngas_dsyngas_ratio(
            dprodenergy_dsyngas_ratio, prod_energy)

        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoConsumptionValue, f'{GlossaryEnergy.syngas} ({GlossaryEnergy.energy_unit})'), ('syngas_ratio',),
            dcons_syngas_dsyngas_ratio / 100.0 / scaling_factor_techno_consumption)

        dcons_co2_dsyngas_ratio = self.techno_model.compute_dcons_co2_dsyngas_ratio(
            dprodenergy_dsyngas_ratio, prod_energy)

        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoConsumptionValue, f'{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit})'), ('syngas_ratio',),
            dcons_co2_dsyngas_ratio / 100.0 / scaling_factor_techno_consumption)
