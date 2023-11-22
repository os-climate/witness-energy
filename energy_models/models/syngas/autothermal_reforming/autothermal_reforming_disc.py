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

from climateeconomics.glossarycore import GlossaryCore
from energy_models.core.techno_type.disciplines.syngas_techno_disc import SyngasTechnoDiscipline
from energy_models.models.syngas.autothermal_reforming.autothermal_reforming import AuthothermalReforming


class AutothermalReformingDiscipline(SyngasTechnoDiscipline):

    # ontology information
    _ontology_data = {
        'label': 'Authothermal Reforming Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-fire fa-fw',
        'version': '',
    }
    # -- add specific techno inputs to this

    techno_name = 'AutothermalReforming'
    lifetime = 15
    construction_delay = 3  # years
    #'reaction': '2CH4 + CO2 + O2 = 3H2 + 3CO + H2O',
    techno_infos_dict_default = {'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 'Opex_percentage': 0.02,
                                 'lifetime': lifetime,  # for now constant in time but should increase with time
                                 'lifetime_unit': GlossaryCore.Years,
                                 # Cormos, A.M., Szima, S., Fogarasi, S. and Cormos, C.C., 2018.
                                 # Economic assessments of hydrogen production processes based on natural gas reforming with carbon capture.
                                 # Chem. Eng. Trans, 70, pp.1231-1236.
                                 'Capex_init': 130.0,  # Capex initial Cormos2018 estimation for ATR without CCS
                                 'Capex_init_unit': 'euro/kW',
                                 # Kalamaras, C.M. and Efstathiou, A.M., 2013.
                                 # Hydrogen production technologies: current state and future developments.
                                 # In Conference papers in science (Vol. 2013).
                                 # Hindawi.
                                 'efficiency': 0.6,
                                 'maturity': 5,
                                 'learning_rate': 0.2,
                                 'available_power': 6000,
                                 'available_power_unit': 'kW',
                                 'euro_dollar': 1.114,
                                 'full_load_hours': 8000.0,
                                 'WACC': 0.0878,
                                 'techno_evo_eff': 'no',
                                 GlossaryCore.ConstructionDelay: construction_delay  # in kWh/kg
                                 }

    syngas_ratio = AuthothermalReforming.syngas_COH2_ratio

    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), GlossaryCore.InvestValue: [0.0, 0.0, 0.0]})
    # From Future of hydrogen : accounting for around three quarters of the
    # annual global dedicated hydrogen production of around 70 million tonnes.
    initial_production = 0.0
    initial_age_distribution = pd.DataFrame({'age': np.arange(1, 2),
                                             'distrib': [100.0]})
    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {GlossaryCore.Years: ('float', None, True),
                                                                'age': ('float', None, True),
                                                                'distrib': ('float', None, True)}
                                       },
               GlossaryCore.InvestmentBeforeYearStartValue: {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int',  [-20, -1], False),
                                                                 GlossaryCore.InvestValue: ('float',  None, True)},
                                        'dataframe_edition_locked': False}}

    DESC_IN.update(SyngasTechnoDiscipline.DESC_IN)

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = AuthothermalReforming(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
