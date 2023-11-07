'''
Copyright 2022 Airbus SAS
Modifications on 2023/09/30-2023/11/03 Copyright 2023 Capgemini

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

from climateeconomics.glossarycore import GlossaryCore
from energy_models.core.techno_type.disciplines.renewable_techno_disc import RenewableTechnoDiscipline
from energy_models.models.renewable.renewable_simple_techno.renewable_simple_techno import RenewableSimpleTechno


class RenewableSimpleTechnoDiscipline(RenewableTechnoDiscipline):
    """
        Generic Renewable Techno used in the WITNESS Coarse process
        It has a high price per kWh without CO2 but a low CO2 emissions per kWh
        It has properties similar to electricity technologies
    """

    # ontology information
    _ontology_data = {
        'label': 'Renewable Technology Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-fan fa-fw',
        'version': '',
    }
    techno_name = 'RenewableSimpleTechno'
    lifetime = 30
    construction_delay = 3
    # net production = 25385.78 TWh
    initial_production = 31552.17  # TWh
    # from witness full study
    renewable_energy_capital = 12.414  # trillion dollars

    techno_infos_dict_default = {'maturity': 0,
                                 'Opex_percentage': 0.12,
                                 'WACC': 0.058,
                                 'learning_rate': 0.00,
                                 'lifetime': lifetime,
                                 'lifetime_unit': GlossaryCore.Years,
                                 'Capex_init': 230.0,
                                 'Capex_init_unit': '$/MWh',
                                 'techno_evo_eff': 'no',
                                 'efficiency': 1.0,
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 'construction_delay': construction_delay,
                                 'resource_price': 70.0,
                                 'resource_price_unit': '$/MWh'}

    techno_info_dict = techno_infos_dict_default

    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), GlossaryCore.InvestValue: [0.0, 635.0, 638.0]})

    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': [4.14634146, 6.2195122, 2.77439024, 6.92073171, 6.92073171,
                                                         3.44512195, 2.77439024, 2.07317073, 4.84756098, 3.44512195,
                                                         1.37195122, 2.07317073, 1.37195122, 2.77439024, 3.44512195,
                                                         1.37195122, 4.14634146, 2.07317073, 4.14634146, 2.77439024,
                                                         2.77439024, 2.07317073, 4.14634146, 2.77439024, 3.44512195,
                                                         6.2195122, 4.14634140, 2.77439024, 2.5304878],
                                             })

    invest_before_year_start_var = GlossaryCore.InvestmentBeforeYearStartDf
    invest_before_year_start_var['default'] = invest_before_year_start
    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'age': ('int',  [0, 100], False),
                                                                'distrib': ('float',  None, True)},
                                       'dataframe_edition_locked': False},
               GlossaryCore.InvestmentBeforeYearStartValue: invest_before_year_start_var
               }
    # -- add specific techno outputs to this
    DESC_IN.update(RenewableTechnoDiscipline.DESC_IN)

    DESC_OUT = RenewableTechnoDiscipline.DESC_OUT

    _maturity = 'Research'

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = RenewableSimpleTechno(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
