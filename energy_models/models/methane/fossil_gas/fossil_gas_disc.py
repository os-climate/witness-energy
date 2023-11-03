'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/14-2023/11/03 Copyright 2023 Capgemini

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

from energy_models.core.techno_type.disciplines.methane_techno_disc import MethaneTechnoDiscipline
from energy_models.models.methane.fossil_gas.fossil_gas import FossilGas


class FossilGasDiscipline(MethaneTechnoDiscipline):

    # ontology information
    _ontology_data = {
        'label': 'Fossil Gas Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-gas-pump fa-fw',
        'version': '',
    }
    # -- add specific techno inputs to this

    techno_name = 'FossilGas'
    lifetime = 23
    construction_delay = 3  # years
    techno_infos_dict_default = {'available_power': 15000000,
                                 'available_power_unit': 'm^3',
                                 'capacity_factor': 0.4,
                                 'full_load_hours': 8760,
                                 'Opex_percentage': 0.34,
                                 'CO2_from_production': 0.123,
                                 'CO2_from_production_unit': 'kg/kg',
                                 # 0.142 kt/PJ (mean) in
                                 # https://previous.iiasa.ac.at/web/home/research/researchPrograms/air/IR54-GAINS-CH4.pdf
                                 'CH4_emission_factor': 0.142e-3 / 0.277,
                                 'CH4_emission_factor_unit': 'Mt/TWh',
                                 'lifetime': lifetime,  # for now constant in time but should increase with time
                                 'fuel_demand': 1,
                                 'fuel_demand_unit': 'kWh/kWh',
                                 'elec_demand': 0.00735,
                                 'elec_demand_unit': 'kWh/kWh',
                                 'lifetime_unit': 'years',
                                 'Capex_init': 3641780,  # Capex initial
                                 # Sarhosis, V., Jaya, A.A., Hosking, L., Koj, A. and Thomas, H.R., 2015.
                                 # Techno-economics for coalbed methane production in the South Wales coalfield.
                                 # https://eprint.ncl.ac.uk/file_store/production/219105/A20E5895-2DAF-4D6F-91DF-79776D756247.pdf
                                 'Capex_init_unit': 'euro',
                                 'euro_dollar': 1.214,
                                 'techno_evo_eff': 'no',
                                 'learning_rate': 0,
                                 'WACC': 0.0878,
                                 'efficiency': 0.4, # https://geospatial.blogs.com/geospatial/2010/01/energy-efficiency-of-fossil-fuel-power-generation.html#:~:text=The%20average%20efficiencies%20of%20power,up%20the%20stack%22%20as%20heat.
                                 'construction_delay': construction_delay,  # in kWh/kg
                                 'maturity': 5
                                 }
    energy_own_use = 3732.83  # TWh
    # in TWh in 2019 in ourworldindata gas production
    initial_production = 39893. - energy_own_use

    # From World gas production of ourworldindata
    # We take the variation for the last 25 years (which is new factories - old factories) and not new factories
    # and we add the missing factories to go to 100 equally
    distrib_our_world_indata = np.array([2.52, 1.43, 1.61, 2.28, 1.44, 1.41, 2.26,
                                         2.13, 1.6, 2.35, 1.83,
                                         0.0, 5.29, 2.65,
                                         1.68, 0.9, 1.7,
                                         1.87, 0.9, 3.3,
                                         4.63, 3.3])
    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': distrib_our_world_indata * 100.0 / distrib_our_world_indata.sum()})  # to do

    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), 'invest': [0.0, 31.2, 31.2]})
    FLUE_GAS_RATIO = np.array([0.085])

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'years': ('float', None, True),
                                                                'age': ('float', None, True),
                                                                'distrib': ('float', None, True)}
                                       },
               'invest_before_ystart': {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int',  [-20, -1], False),
                                                                 'invest': ('float',  None, True)},
                                        'dataframe_edition_locked': False}}

    DESC_IN.update(MethaneTechnoDiscipline.DESC_IN)

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = FossilGas(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
