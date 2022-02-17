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

from energy_models.models.electricity.hydropower.hydropower import Hydropower
from energy_models.core.techno_type.disciplines.electricity_techno_disc import ElectricityTechnoDiscipline


class HydropowerDiscipline(ElectricityTechnoDiscipline):
    """**EnergyModelsDiscipline** is the :class:`~gems.core.discipline.MDODiscipline`
    implementing the computation of Energy Models outputs."""


    # ontology information
    _ontology_data = {
        'label': 'Hydropower Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-water fa-fw',
        'version': '',
    }
    techno_name = 'Hydropower'
    lifetime = 50
    construction_delay = 3
    techno_infos_dict_default = {'type': 'electricity_creation',
                                 'maturity': 0,
                                 'product': 'electricity',
                                 # IRENA, 2021
                                 # Renewable Power Generation Costs in 2020
                                 # https://www.irena.org/publications/2021/Jun/Renewable-Power-Costs-in-2020
                                 'Opex_percentage': 0.025,
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 'electricity': 'hydropower',
                                 'WACC': 0.075,  # Weighted averaged cost of capital for the carbon capture plant
                                 'lifetime': lifetime,  # should be modified
                                 'lifetime_unit': 'years',
                                 'Capex_init': 1704,  # IRENA
                                 'Capex_init_unit': '$/kW',
                                 'full_load_hours': 8760.0,
                                 'capacity_factor': 0.46,  # IRENA
                                 'efficiency': 1.0,  # No need of efficiency here
                                 'construction_delay': construction_delay,
                                 'learning_rate': 0.0,
                                 'techno_evo_eff': 'no', }

    techno_info_dict = techno_infos_dict_default

    initial_production = 4222.0  # in TWh at year_start source IEA 2019
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), 'invest': [2.5, 2.5, 2.5
                                                                     ]})

    # Global power plant database 2018, https://github.com/wri/global-power-plant-database
    # Also in
    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime + 1),
                                             'distrib': [0.05, 0.94, 2.06, 2.78, 2.33, 3.28, 4.00, 3.82, 3.95, 3.46, 3.28, 2.30, 2.47, 1.75, 1.61, 1.75, 1.71, 1.40, 1.13, 1.40, 1.40, 1.13, 1.31, 1.58, 2.16, 2.30, 1.76, 1.53, 2.16, 2.70, 2.97, 2.57, 3.38, 3.20, 2.34, 2.16, 2.12, 1.58, 1.49, 1.26, 1.67, 1.04, 0.72, 1.62, 1.08, 1.53, 0.86, 1.17, 2.16, 1.58]})

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
    DESC_IN.update(ElectricityTechnoDiscipline.DESC_IN)

    DESC_OUT = ElectricityTechnoDiscipline.DESC_OUT

    _maturity = 'Research'

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = Hydropower(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
