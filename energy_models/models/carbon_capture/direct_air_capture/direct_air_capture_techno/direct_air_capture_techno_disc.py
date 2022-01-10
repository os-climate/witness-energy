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

from energy_models.models.carbon_capture.direct_air_capture.direct_air_capture_techno.direct_air_capture_techno import DirectAirCaptureTechno
from energy_models.core.techno_type.disciplines.carbon_capture_techno_disc import CCTechnoDiscipline


class DirectAirCaptureTechnoDiscipline(CCTechnoDiscipline):
    """
    Generic Direct Air Capture technology for WITNESS Coarse process
    Modeled after amine scrubbing
    """

    techno_name = 'direct_air_capture.DirectAirCaptureTechno'
    lifetime = 35
    construction_delay = 3
    techno_infos_dict_default = {'maturity': 0,
                                 'Opex_percentage': 0.25,
                                 'CO2_per_energy': 0.65,
                                 'CO2_per_energy_unit': 'kg/kg',
                                 'elec_demand': 0.25,
                                 'elec_demand_unit': 'kWh/kgCO2',
                                 'heat_demand': 1.75,
                                 'heat_demand_unit': 'kWh/kgCO2',
                                 'WACC': 0.1,
                                 'learning_rate': 0.1,
                                 'maximum_learning_capex_ratio': 0.33,
                                 'lifetime': lifetime,
                                 'lifetime_unit': 'years',
                                 'Capex_init': 0.88,
                                 'Capex_init_unit': '$/kgCO2',
                                 'efficiency': 0.9,
                                 'CO2_capacity_peryear': 3.6E+8,
                                 'CO2_capacity_peryear_unit': 'kg CO2/year',
                                 'real_factor_CO2': 1.0,
                                 'transport_cost': 0.0,
                                 'transport_cost_unit': '$/kgCO2',
                                 'enthalpy': 1.124,
                                 'enthalpy_unit': 'kWh/kgC02',
                                 'energy_efficiency': 0.78,
                                 'construction_delay': construction_delay,
                                 'techno_evo_eff': 'no',
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 }

    techno_info_dict = techno_infos_dict_default

    initial_capture = 5.0e-3  # in Mt at year_start
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), 'invest': np.array([0.05093, 0.05093, 15.0930]) * 0.8 / 3000})

    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime - 1),
                                             'distrib': [10.0, 10.0, 10.0, 10.0, 10.0,
                                                         10.0, 10.0, 10.0,
                                                         10.0, 10.0, 0.0,
                                                         0.0, 0.0, 0.0,
                                                         0.0, 0.0, 0.0,
                                                         0.0, 0.0, 0.0,
                                                         0.0, 0.0, 0.0,
                                                         0.0, 0.0, 0.0,
                                                         0.0, 0.0, 0.0,
                                                         0.0, 0.0, 0.0,
                                                         0.0]
                                             })

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default},
               'initial_production': {'type': 'float', 'unit': 'MtCO2', 'default': initial_capture},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'age': ('int',  [0, 100], False),
                                                                'distrib': ('float',  None, True)},
                                       'dataframe_edition_locked': False},
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
        self.techno_model = DirectAirCaptureTechno(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)

    def compute_sos_jacobian(self):
        # Grad of price vs energyprice

        CCTechnoDiscipline.compute_sos_jacobian(self)

        grad_dict = self.techno_model.grad_price_vs_energy_price()

        self.set_partial_derivatives_techno(
            grad_dict, None)
