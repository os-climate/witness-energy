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
import copy

import pandas as pd
import numpy as np

from energy_models.core.techno_type.disciplines.gaseous_hydrogen_techno_disc import GaseousHydrogenTechnoDiscipline
from energy_models.models.gaseous_hydrogen.electrolysis.pem.electrolysis_pem import ElectrolysisPEM


class ElectrolysisPEMDiscipline(GaseousHydrogenTechnoDiscipline):
    """
    Electrolysis PEM Discipline
    """

    # ontology information
    _ontology_data = {
        'label': 'Hydrogen Electrolysis PEM Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-hospital-symbol fa-fw',
        'version': '',
    }
    techno_name = 'Electrolysis.PEM'
    # Fuel Cells and Hydrogen 2 Joint Undertaking 2018
    # LAUNCH OF REFHYNE, WORLD'S LARGEST ELECTROLYSIS PLANT IN RHINELAND REFINERY
    # https://www.fch.europa.eu/news/launch-refhyne-worlds-largest-electrolysis-plant-rhineland-refinery
    construction_delay = 2  # year
    lifetime = 11  # Around 90000 operating hours with 8000 hours a year
    techno_infos_dict_default = {'maturity': 5,
                                 'Opex_percentage': 0.025,
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 'WACC': 0.05,
                                 'learning_rate':  0.15,
                                 'maximum_learning_capex_ratio': 500.0 / 1012.5,  # 500 euro/kw minimum capex
                                 'lifetime': lifetime,
                                 'lifetime_unit': 'years',
                                 'stack_lifetime': 100000,
                                 'stack_lifetime_unit': 'hours',
                                 'Capex_init': 1012.5,  # for a power input of 2MW, decreases for 10 MW
                                 'Capex_init_unit': 'euro/kW',
                                 'euro_dollar': 1.114,
                                 'full_load_hours': 8000,
                                 'techno_evo_eff': 'yes',
                                 'techno_evo_time': 10,
                                 'efficiency evolution slope': 0.5,
                                 # electric efficiency that we will use to
                                 # compute elec needs
                                 'efficiency': 0.65,
                                 'efficiency_max': 0.75,
                                 'construction_delay': construction_delay}

    # Around 50MW of nominal power *8000 hours per year
    initial_production = 0.4
    # Industrial plants started to emerge around 2015
    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': [25, 25, 20, 15, 15] + [0.0] * 5
                                             })
# Public investment in Europe through FCH JU : 156 MEuro or 190M$
# We assume half is for PEM .
# Worldwide the investment of europe for PEM is 36%   190/2*100/36 = 263.9 M$
# https://www.euractiv.com/section/energy/news/europe-china-battle-for-global-supremacy-on-electrolyser-manufacturing/
    invest_before_year_start = pd.DataFrame({'past years': np.arange(-construction_delay, 0),
                                             'invest': [0.264, 0.264]})

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default},
               'initial_production': {'type': 'float',
                                      'unit': 'TWh', 'default': initial_production},
               'initial_age_distrib': {'type': 'dataframe',
                                       'unit': '%', 'default': initial_age_distribution},
               'invest_before_ystart': {'type': 'dataframe',
                                        'unit': 'G$',
                                        'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int',  [-20, -1], False),
                                                                 'invest': ('float',  None, True)},
                                        'dataframe_edition_locked': False}}
    DESC_IN.update(GaseousHydrogenTechnoDiscipline.DESC_IN)

    # -- add specific techno outputs to this
    DESC_OUT = GaseousHydrogenTechnoDiscipline.DESC_OUT

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = ElectrolysisPEM(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
