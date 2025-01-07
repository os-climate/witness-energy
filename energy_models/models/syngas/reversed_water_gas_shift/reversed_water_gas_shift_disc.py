'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2024/03/27 Copyright 2023 Capgemini

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

from energy_models.core.techno_type.disciplines.syngas_techno_disc import (
    SyngasTechnoDiscipline,
)
from energy_models.core.techno_type.techno_disc import TechnoDiscipline
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.syngas.reversed_water_gas_shift.reversed_water_gas_shift import (
    RWGS,
)


class ReversedWaterGasShiftDiscipline(SyngasTechnoDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Reversed Water Gas Shift Model',
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

    techno_name = GlossaryEnergy.RWGS

    techno_infos_dict_default = {'maturity': 5,
                                 'reaction': 'dCO2 + e(H2+r1C0) = syngas(H2+r2CO) + cH20',
                                 'CO2_from_production': 0.0,
                                 'Opex_percentage': 0.01,
                                 # Giuliano, A., Freda, C. and Catizzone, E., 2020.
                                 # Techno-economic assessment of bio-syngas production for methanol synthesis: A focus on the water-gas shift and carbon capture sections.
                                 # Bioengineering, 7(3), p.70.
                                 # Giuliano2020 : the elec demand is more or
                                 # less constant 6.6 MW for WGS over the 8.6

                                 'WACC': 0.0878,  # Weighted averaged cost of capital for the carbon capture plant
                                 'learning_rate': 0.2,
                                 # Capex at table 3 and 8
                                 'Capex_init_vs_CO_H2_ratio': [37.47e6, 113.45e6],
                                 'Capex_init_vs_CO_H2_ratio_unit': '$',
                                 # Capex initial at year 2020
                                 'CO_H2_ratio': [1.0, 0.5],
                                 'available_power': [4000.0e3, 22500.0e3],
                                 'available_power_unit': 'mol/h',
                                 # price for elec divided by elec price in the
                                 # paper
                                 'elec_demand': [13e6 / 0.07, 61.8e6 / 0.07],
                                 'elec_demand_unit': 'kWh',
                                 # Rezaei, E. and Dzuryk, S., 2019.
                                 # Techno-economic comparison of reverse water gas shift reaction to steam and
                                 # dry methane reforming reactions for syngas production.
                                 # Chemical engineering research and design,
                                 # 144, pp.354-369.
                                 'full_load_hours': 8240,  # p357 rezaei2019

                                 'efficiency': 0.75,  # pump + compressor efficiency Rezaei2019
                                 'techno_evo_eff': 'no',  # yes or no
                                 }

    # Fake investments (not found in the litterature...)
        # From Future of hydrogen : accounting for around three quarters of the
    # annual global dedicated hydrogen production of around 70 million tonnes. and 23+ from coal gasification
    # that means that WGS is used for 98% of the hydrogen production
    initial_production = 0.0

    # Fake initial age distrib (not found in the litterature...)
    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
                      
               'syngas_ratio': {'type': 'array', 'unit': '%'},
               'needed_syngas_ratio': {'type': 'float', 'unit': '%'}
               }
    # -- add specific techno inputs to this
    DESC_IN.update(SyngasTechnoDiscipline.DESC_IN)
    DESC_OUT = TechnoDiscipline.DESC_OUT

    # -- add specific techno outputs to this

    def init_execution(self):
        self.techno_model = RWGS(self.techno_name)
