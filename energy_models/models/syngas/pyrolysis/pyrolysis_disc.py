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

from energy_models.models.syngas.pyrolysis.pyrolysis import Pyrolysis
from energy_models.core.techno_type.disciplines.syngas_techno_disc import SyngasTechnoDiscipline


class PyrolysisDiscipline(SyngasTechnoDiscipline):
    """**EnergyModelsDiscipline** is the :class:`~gems.core.discipline.MDODiscipline`
    implementing the computation of Energy Models outputs."""

    # ontology information
    _ontology_data = {
        'label': 'Syngas Pyrolysis Model',
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
    syngas_ratio = Pyrolysis.syngas_COH2_ratio

    techno_name = 'Pyrolysis'
    lifetime = 20
    construction_delay = 2
    techno_infos_dict_default = {'maturity': 0,
                                 'product': 'syngas',
                                 'Opex_percentage': 0.06,
                                 'CO2_from_production': 0.2,
                                 'CO2_from_production_unit': 'kg/kg',
                                 'WACC': 0.075,  # Weighted averaged cost of capital for the carbon capture plant
                                 'lifetime': lifetime,
                                 'lifetime_unit': 'years',
                                 # 1600T/day of wood capacity, 180M$ of Capital
                                 # cost, 20 years lifetime, 70% syngas yield
                                 'Capex_init': 0.012,
                                 'Capex_init_unit': '$/kWh',
                                 'efficiency': 1.0,  # No need of efficiency here
                                 'construction_delay': construction_delay,
                                 'learning_rate': 0.0,
                                 'techno_evo_eff': 'no',
                                 'syngas_yield': 0.7,  # with 1kg of wood
                                 'char_yield': 0.15,  # with 1kg of wood
                                 'bio_oil_yield': 0.15,  # with 1kg of wood,
                                 'temperature': 1000,
                                 'temperature_unit': 'oC'

                                 }

    techno_info_dict = techno_infos_dict_default

    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), 'invest': [0.0, 0.0]})
    # From Future of hydrogen : accounting for around three quarters of the
    # annual global dedicated hydrogen production of around 70 million tonnes.
    initial_production = 1e-12  # in TWh at year_start MT*kWh/kg = TWh
    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': [4.75611097, 4.44546605, 6.78106804, 4.57186564, 6.66476688,
                                                         3.4997533, 4.00989891, 5.10571635, 4.81945507, 4.87417378,
                                                         4.2461254, 5.41593564, 6.62282244, 6.29274159, 6.69463399,
                                                         4.5047143, 4.52828241, 4.75677933, 7.40968989]})
    pyrolysis_gas_flue_gas_ratio = np.array([0.13])

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
                                        'dataframe_edition_locked': False},
               'flue_gas_co2_ratio': {'type': 'array', 'default': pyrolysis_gas_flue_gas_ratio}
               }
    # -- add specific techno outputs to this
    DESC_IN.update(SyngasTechnoDiscipline.DESC_IN)

    _maturity = 'Research'

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = Pyrolysis(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
