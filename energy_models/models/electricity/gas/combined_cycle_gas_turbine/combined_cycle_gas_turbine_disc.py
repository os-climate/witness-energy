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

from energy_models.core.techno_type.disciplines.electricity_techno_disc import ElectricityTechnoDiscipline
from energy_models.models.electricity.gas.gas_elec import GasElec


class CombinedCycleGasTurbineDiscipline(ElectricityTechnoDiscipline):

    techno_name = 'CombinedCycleGasTurbine'
    lifetime = 30  # Source: U.S. Energy Information Administration 2020
    construction_delay = 2  # years
    # Taud, R., Karg, J. and O�Leary, D., 1999.
    # Gas turbine based power plants: technology and market status.
    # The World Bank Energy Issues, (20).
    # https://documents1.worldbank.org/curated/en/640981468780885410/pdf/263500Energy0issues020.pdf
    heat_rate = 6.5  # Gj/Mwh = Mj/kwh from World bank
    # Convert heat rate into kwh/kwh
    methane_needs = heat_rate / 3.6
    techno_infos_dict_default = {'maturity': 5,
                                 'Opex_percentage': 0.017,  # World bank
                                 # C. KOST, S. SHAMMUGAM, V. FLURI, D. PEPER, A.D. MEMAR, T. SCHLEGL,
                                 # FRAUNHOFER INSTITUTE FOR SOLAR ENERGY SYSTEMS ISE
                                 # LEVELIZED COST OF ELECTRICITY RENEWABLE
                                 # ENERGY TECHNOLOGIES, June 2021
                                 'WACC': 0.075,  # fraunhofer
                                 'learning_rate': 0,  # fraunhofer
                                 'lifetime': lifetime,  # for now constant in time but should increase with time
                                 'lifetime_unit': 'years',
                                 # Source: U.S. Energy Information Administration, 2020
                                 # Capital Cost and Performance Characteristic Estimates for Utility Scale Electric Power Generating Technologies,
                                 # https://www.eia.gov/analysis/studies/powerplants/capitalcost/pdf/capital_cost_AEO2020.pdf
                                 'Capex_init': 1084,
                                 'Capex_init_unit': '$/kW',
                                 'capacity_factor': 0.85,  # World bank
                                 'kwh_methane/kwh': methane_needs,
                                 'efficiency': 1,
                                 'techno_evo_eff': 'no',  # yes or no
                                 'construction_delay': construction_delay,
                                 'full_load_hours': 8760}

    # Major hypothesis: 25% of invest in gas go into gas turbine, 75% into CCGT
    share = 0.75
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), 'invest': [41.0 * share, 51.0 * share]})
# For initial production: MAJOR hypothesis, took IEA WEO 2019 production for 2018
# In US according to EIA 53% of capa from CCGT and 47 for GT in 2017
    share_ccgt = 0.55
    # Initial prod in TWh
    initial_production = share_ccgt * 6118
    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': [2.8, 2.4, 4.3, 2, 1.5, 1.3, 0.9, 1.3, 4.8, 7.1, 14.6, 14.2,
                                                         6.7, 4.9, 2.9, 2, 1.8, 2, 1.8, 2.9, 2.7, 1.5, 2.3, 1.4,
                                                         1.3, 2.1, 3.6, 1.3, 1.6]})

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default},
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'age': ('int',  [0, 100], False),
                                                                'distrib': ('float',  None, True)},
                                       'dataframe_edition_locked': False},
               'invest_before_ystart': {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int',  [-20, -1], False),
                                                                 'invest': ('float',  None, True)},
                                        'dataframe_edition_locked': False}


               }
    # -- add specific techno inputs to this
    DESC_IN.update(ElectricityTechnoDiscipline.DESC_IN)

    gas_turbine_flue_gas_ratio = np.array([0.0350])
    DESC_OUT = {
        'flue_gas_co2_ratio': {'type': 'array', 'default': gas_turbine_flue_gas_ratio}
    }
    # -- add specific techno outputs to this
    DESC_OUT.update(ElectricityTechnoDiscipline.DESC_OUT)

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = GasElec(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
