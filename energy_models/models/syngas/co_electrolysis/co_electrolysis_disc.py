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

from energy_models.core.techno_type.disciplines.syngas_techno_disc import (
    SyngasTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.syngas.co_electrolysis.co_electrolysis import CoElectrolysis


class CoElectrolysisDiscipline(SyngasTechnoDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Co-Electrolysis Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-bolt fa-fw',
        'version': '',
    }
    # -- add specific techno inputs to this
    DESC_IN = SyngasTechnoDiscipline.DESC_IN
    techno_name = GlossaryEnergy.CoElectrolysis
    lifetime = 40
    # 'reaction': 'H20 + CO2 = H2 + CO + O2',

    techno_infos_dict_default = {'CO2_from_production': 0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 'elec_demand': 8.82,
                                 'elec_demand_unit': 'kWh/kg',
                                 'Opex_percentage': 0.07,
                                 'Capex_init': 600,
                                 'Capex_init_unit': '$/kW',
                                 'maturity': 5,
                                 'learning_rate': 0.2,
                                 'available_power': 50000,
                                 'available_power_unit': 'kW',
                                 'capacity_factor': 0.65,
                                 'euro_dollar': 1.114,
                                 'full_load_hours': 8000.0,
                                 'WACC': 0.0878,
                                 'techno_evo_eff': 'no',
                                 'efficiency': 0.8,
                                 }

    syngas_ratio = CoElectrolysis.syngas_COH2_ratio

        # From Future of hydrogen : accounting for around three quarters of the
    # annual global dedicated hydrogen production of around 70 million tonnes.
    initial_production = 0.0
    initial_age_distribution = pd.DataFrame({'age': np.arange(1, 2),
                                             'distrib': [100.0]})

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
                      'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'age': ('float', None, True),
                                                                'distrib': ('float', None, True)}
                                       },
               }

    DESC_IN.update(SyngasTechnoDiscipline.DESC_IN)

    DESC_OUT = SyngasTechnoDiscipline.DESC_OUT

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = CoElectrolysis(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
