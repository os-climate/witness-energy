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

import pandas as pd
import numpy as np
from energy_models.core.techno_type.disciplines.carbon_capture_techno_disc import CCTechnoDiscipline
from energy_models.models.carbon_capture.flue_gas_capture.mono_ethanol_amine.mono_ethanol_amine import MonoEthanolAmine


class MonoEthanolAmineDiscipline(CCTechnoDiscipline):
    """**EnergyModelsDiscipline** is the :class:`~gems.core.discipline.MDODiscipline`
    implementing the computation of Energy Models outputs."""

    techno_name = 'flue_gas_capture.MonoEthanolAmine'
    lifetime = 25  # SAEECCT Coal USC plant lifetime
    construction_delay = 1

    # Most of the data from this model come from :
    # Guandalini, G., Romano, M.C., Ho, M., Wiley, D., Rubin, E.S. and Abanades, J.C., 2019.
    # A sequential approach for the economic evaluation of new CO2 capture technologies for power plants.
    # International Journal of Greenhouse Gas Control, 84, pp.219-231.
    # https://www.sciencedirect.com/science/article/pii/S1750583618307461?via%3Dihub#fig0040
    # Refered in this code as SAEECCT

    heat_to_power_lost = 0.243
    heat_duty = 2559  # SAEECCT - MJ/tCO2
    elec_demand_capture = 122  # SAEECCT - MJ/tCO2
    mj_to_kwh_factor = 0.277778
    # Hypothesis for max CO2 captured SAEECCT, USC plant 790 Kg/MWh CO2
    # emission and net power output 550 MW
    c02_capacity_year = 790.2 * 0.85 * 8760 * 550
    carbon_capture_efficiency = 0.90

    techno_infos_dict_default = {'lifetime': lifetime,
                                 'lifetime_unit': 'years',
                                 'capacity_factor': 0.85,  # SAEECCT - Coal capacity factor
                                 'maturity': 0,
                                 'Opex_percentage': 0.032,  # SAEECCT 62.6M$ -> 1921M$
                                 'learning_rate': 0,
                                 # Breyer, C., Fasihi, M. and Aghahosseini, A., 2020.
                                 # Carbon dioxide direct air capture for effective climate change mitigation based
                                 # on renewable electricity: a new type of energy system sector coupling.
                                 # Mitigation and Adaptation Strategies for
                                 # Global Change, 25(1), pp.43-65.
                                 'WACC': 0.07,

                                 # SAEECCT - 1921 M$
                                 'Capex_init': 1921000000 / (c02_capacity_year * carbon_capture_efficiency),
                                 'Capex_init_unit': '$/kgCO2',

                                 'elec_demand': elec_demand_capture * mj_to_kwh_factor / 1000,
                                 'elec_demand_unit': 'kWh/kgCO2',

                                 'heat_demand': heat_duty * heat_to_power_lost * mj_to_kwh_factor / 1000,
                                 'heat_demand_unit': 'kWh/kgCO2',

                                 'CO2_capacity_peryear': c02_capacity_year,  # kg CO2 /year
                                 'CO2_capacity_peryear_unit': 'kg CO2/year',

                                 'carbon_capture_efficiency': carbon_capture_efficiency,  # SAEECCT - USC Mea

                                 'real_factor_CO2': 1.0,

                                 'techno_evo_eff': 'no',
                                 'efficiency': 1.0,
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 'construction_delay': construction_delay, }

    techno_info_dict = techno_infos_dict_default

    initial_capture = 15  # Mt

    # We assume 0.5 MT increase per year, with a capex ~ 40$/ton
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), 'invest': [0.6]})

    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime - 1),
                                             'distrib': [10.0, 10.0, 10.0, 10.0, 10.0,
                                                         10.0, 10.0, 10.0,
                                                         10.0, 10.0, 0.0,
                                                         0.0, 0.0, 0.0,
                                                         0.0, 0.0, 0.0,
                                                         0.0, 0.0, 0.0,
                                                         0.0, 0.0, 0.0]
                                             })

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default},
               'initial_production': {'type': 'float', 'unit': 'MtCO2', 'default': initial_capture},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'age': ('int',  [0, 100], False),
                                                                'distrib': ('float',  None, True)},
                                       'dataframe_edition_locked': False},
               'flue_gas_mean': {'type': 'dataframe', 'namespace': 'ns_flue_gas',
                                 'visibility': CCTechnoDiscipline.SHARED_VISIBILITY},
               'invest_before_ystart': {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int',  [-20, -1], False),
                                                                 'invest': ('float',  None, True)},
                                        'dataframe_edition_locked': False}}
    # -- add specific techno outputs to this
    DESC_IN.update(CCTechnoDiscipline.DESC_IN)

    DESC_OUT = CCTechnoDiscipline.DESC_OUT

    _maturity = 'Research'

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = MonoEthanolAmine(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)

    def compute_sos_jacobian(self):
        # Grad of price vs energyprice

        CCTechnoDiscipline.compute_sos_jacobian(self)

        grad_dict = self.techno_model.grad_price_vs_energy_price()

        self.set_partial_derivatives_techno(
            grad_dict, None)

        self.set_partial_derivatives_flue_gas()
