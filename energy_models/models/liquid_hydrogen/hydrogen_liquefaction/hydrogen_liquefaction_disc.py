'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/14-2023/11/16 Copyright 2023 Capgemini

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

from energy_models.core.techno_type.disciplines.liquid_hydrogen_techno_disc import LiquidHydrogenTechnoDiscipline
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.liquid_hydrogen.hydrogen_liquefaction.hydrogen_liquefaction import HydrogenLiquefaction


class HydrogenLiquefactionDiscipline(LiquidHydrogenTechnoDiscipline):
    """
    HydrogenLiquefaction Discipline
    """

    # ontology information
    _ontology_data = {
        'label': 'Hydrogen Liquefaction Model',
        'type': '',
        'source': '',
        'validated': '',
        'validated_by': '',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-tint fa-fw',
        'version': '',
    }
    techno_name = 'HydrogenLiquefaction'
    construction_delay = 2  # year
    lifetime = 40
    techno_infos_dict_default = {'maturity': 5,
                                 'Opex_percentage': 0.0127,
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 'elec_demand': 8,
                                 'elec_demand_unit': 'kWh/kg',
                                 'efficiency': 0.98,
                                 'techno_evo_eff': 'no',
                                 'WACC': 0.1,
                                 # 'heat_recovery_factor': 0.8,
                                 'learning_rate': 0.2,
                                 'lifetime': lifetime,
                                 'lifetime_unit': GlossaryEnergy.Years,
                                 'stack_lifetime': 100000,
                                 'stack_lifetime_unit': 'hours',
                                 'Capex_init': 500000000,
                                 'Capex_init_unit': 'euro',
                                 'euro_dollar': 1.114,
                                 'available_power': 73000000,
                                 'available_power_unit': 'kg/year',
                                 GlossaryEnergy.ConstructionDelay: construction_delay}

    initial_production = 70.0 * 33.3 * 0.001

    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': np.asarray(
                                                 [0, 0, 0, 0, 0, 0, 0, 1, 2, 0, 0, 1, 1, 0, 1, 1, 4, 3, 1, 2, 2, 1, 1,
                                                  0, 1, 2, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 2]) * 100.0 / 30.0})

    invest_before_year_start = pd.DataFrame({'past years': np.arange(-construction_delay, 0),
                                             GlossaryEnergy.InvestValue: [0.0443575, 0.0443575]})

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_production': {'type': 'float',
                                      'unit': 'TWh', 'default': initial_production},
               'initial_age_distrib': {'type': 'dataframe',
                                       'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                                'age': ('float', None, True),
                                                                'distrib': ('float', None, True)}
                                       },
               GlossaryEnergy.InvestmentBeforeYearStartValue: {'type': 'dataframe',
                                                               'unit': 'G$',
                                                               'default': invest_before_year_start,
                                                               'dataframe_descriptor': {
                                                                   GlossaryEnergy.Years: ('float', None, True),
                                                                   'past years': ('float', None, True),
                                                                   GlossaryEnergy.InvestValue: ('float', None, True)}
                                                               }}
    DESC_IN.update(LiquidHydrogenTechnoDiscipline.DESC_IN)

    # -- add specific techno outputs to this
    DESC_OUT = LiquidHydrogenTechnoDiscipline.DESC_OUT

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = HydrogenLiquefaction(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)

    # def compute_sos_jacobian(self):
    #     inputs_dict = self.get_sosdisc_inputs()
    #     self.techno_model.configure_parameters(inputs_dict)
    #     LiquidHydrogenTechnoDiscipline.compute_sos_jacobian(self)

    # # the generic gradient for production column is not working because of
    # # abandoned mines not proportional to production
    #
    # scaling_factor_invest_level, scaling_factor_techno_production = self.get_sosdisc_inputs(
    #     ['scaling_factor_invest_level', 'scaling_factor_techno_production'])
    # applied_ratio = self.get_sosdisc_outputs(
    #     'applied_ratio')['applied_ratio'].values
    #
    # dprod_name_dinvest = (self.dprod_dinvest.T * applied_ratio).T * scaling_factor_invest_level / scaling_factor_techno_production
    # production_gradient = self.techno_consumption_derivative[f'{Electricity.name} ({self.techno_model.product_energy_unit})']
    # m = self.set_partial_derivative_for_other_types(
    #     (GlossaryEnergy.TechnoProductionValue,
    #      f'{lowtemperatureheat.name} ({self.techno_model.product_energy_unit})'), (GlossaryEnergy.InvestLevelValue, GlossaryEnergy.InvestValue),
    #     (production_gradient - dprod_name_dinvest))
