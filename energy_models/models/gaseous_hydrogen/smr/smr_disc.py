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

from energy_models.core.techno_type.disciplines.gaseous_hydrogen_techno_disc import GaseousHydrogenTechnoDiscipline
from energy_models.models.gaseous_hydrogen.smr.smr import SMR


class SMRDiscipline(GaseousHydrogenTechnoDiscipline):

    # ontology information
    _ontology_data = {
        'label': 'Hydrogen SMR Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-burn fa-fw',
        'version': '',
    }

    techno_name = 'SMR'
    lifetime = 25
    construction_delay = 3  # years
    techno_infos_dict_default = {'reaction': 'CH4 + 2H20 = CO2 + 4H2',
                                 'maturity': 5,
                                 'product': 'H2',
                                 'Opex_percentage': 0.04,
                                 # Diglio, G., Hanak, D.P., Bareschino, P., Mancusi, E., Pepe, F., Montagnaro, F. and Manovic, V., 2017.
                                 # Techno-economic analysis of sorption-enhanced steam methane reforming in a fixed bed reactor network integrated with fuel cell.
                                 # Journal of Power Sources, 364, pp.41-51.
                                 # Diglio2017 : (Esofc - Enet) / E_H2 --> kW/kW
                                 'elec_demand': 0.2,
                                 'elec_demand_unit': 'kWh/kWh',
                                 'WACC': 0.0878,  # Weighted averaged cost of capital for the carbon capture plant
                                 'learning_rate': 0.0,  # 0.2,
                                 'lifetime': lifetime,  # for now constant in time but should increase with time
                                 'lifetime_unit': 'years',
                                 'Capex_init': 1320000.0,  # Capex initial at year 2020
                                 'Capex_init_unit': 'euro',
                                 'euro_dollar': 1.114,
                                 'full_load_hours': 8760.0,
                                 'available_power': 1500.0,
                                 'available_power_unit': 'kW',
                                 'capacity_factor': 0.80,
                                 'efficiency': 0.8,
                                 'techno_evo_eff': 'no',  # yes or no
                                 'construction_delay': construction_delay}

    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), 'invest': [4.43575, 4.43575, 4.43575]})
    # From Future of hydrogen : accounting for around three quarters of the
    # annual global dedicated hydrogen production of around 70 million tonnes.
    initial_production = 70.0 * 33.3 * \
        0.75  # in TWh at year_start MT*kWh/kg = TWh
    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': [3.317804973859207, 6.975128305927281, 4.333201737255864,
                                                         3.2499013031833868, 1.5096723255070685, 1.7575996841282722,
                                                         4.208448479896288, 2.7398341887870643, 5.228582707722979,
                                                         10.057639166085064, 0.0, 2.313462297352473, 6.2755625737595535,
                                                         5.609159099363739, 6.3782076592711885, 8.704303197679629,
                                                         6.1950256610618135, 3.7836557445596464, 1.7560205289962763,
                                                         4.366363995027777, 3.3114883533312236, 1.250690879995941,
                                                         1.7907619419001841, 4.88748519534807]})

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
    DESC_IN.update(GaseousHydrogenTechnoDiscipline.DESC_IN)

    # -- add specific techno outputs to this
    DESC_OUT = GaseousHydrogenTechnoDiscipline.DESC_OUT

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = SMR(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
