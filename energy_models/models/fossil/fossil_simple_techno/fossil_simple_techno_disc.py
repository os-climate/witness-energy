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
from energy_models.core.techno_type.disciplines.fossil_techno_disc import FossilTechnoDiscipline
from energy_models.models.fossil.fossil_simple_techno.fossil_simple_techno import FossilSimpleTechno


class FossilSimpleTechnoDiscipline(FossilTechnoDiscipline):
    """
        Generic Fossil Techno used in the WITNESS Coarse process
        It has a low price per kWh without CO2 but a high CO2 emissions per kWh
        It has properties similar to the coal generation techno
    """


    # ontology information
    _ontology_data = {
        'label': 'Fossil Technology Model ',
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
    techno_name = 'FossilSimpleTechno'
    lifetime = 25
    construction_delay = 3

    techno_infos_dict_default = {'maturity': 0,
                                 'Opex_percentage': 0.024,
                                 'WACC': 0.058,
                                 'learning_rate': 0.00,
                                 'lifetime': lifetime,
                                 'lifetime_unit': 'years',
                                 'Capex_init': 6000,
                                 'Capex_init_unit': '$/kW',
                                 'full_load_hours': 8760.0,  # Full year hours
                                 'capacity_factor': 0.90,
                                 'techno_evo_eff': 'no',
                                 'efficiency': 1.0,
                                 'CO2_from_production': 0.5,
                                 'CO2_from_production_unit': 'kg/kg',
                                 'construction_delay': construction_delay, }

    techno_info_dict = techno_infos_dict_default
    initial_production = 152000
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), 'invest': [1481.48, 1483.79, 1489.95]})

    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': [5.12627214, 7.68940822, 3.43007916, 8.5563513, 8.5563513,
                                                         4.25932906, 3.43007916, 2.56313607, 5.99321523, 4.25932906,
                                                         1.69619299, 2.56313607, 1.69619299, 3.43007916, 4.25932906,
                                                         1.69619299, 5.12627214, 2.56313607, 5.12627214, 3.43007916,
                                                         3.43007916, 2.56313607, 5.12627214, 3.43007916]
                                             })

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
                                        'dataframe_edition_locked': False}}
    # -- add specific techno outputs to this
    DESC_IN.update(FossilTechnoDiscipline.DESC_IN)
    fossil_flue_gas_ratio = np.array([0.12])
    DESC_OUT = {'flue_gas_co2_ratio': {
        'type': 'array', 'default': fossil_flue_gas_ratio}}
    DESC_OUT.update(FossilTechnoDiscipline.DESC_OUT)

    _maturity = 'Research'

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = FossilSimpleTechno(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
