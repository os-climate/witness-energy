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

from energy_models.core.techno_type.disciplines.wet_biomass_techno_disc import WetBiomassTechnoDiscipline
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.wet_biomass.animal_manure.animal_manure import AnimalManure


class AnimalManureDiscipline(WetBiomassTechnoDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Animal Manure Biomass Model',
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

    # wood residues comes from forestry residues
    # prices come from harvest, transport, chipping, drying (depending from
    # where it comes)

    techno_name = GlossaryEnergy.AnimalManure
    lifetime = 25
    construction_delay = 3  # years
    techno_infos_dict_default = {'maturity': 5,
                                 'moisture': 0.85,

                                 # To be defined, but is nearly 0
                                 'Opex_percentage': 0.36,
                                 # 1 tonne of tree absorbs 1.8t of CO2 in one
                                 # year
                                 'CO2_from_production': -2.86,  # same as biomass_dry
                                 'CO2_from_production_unit': 'kg/kg',
                                 'elec_demand': 0,
                                 'elec_demand_unit': 'kWh/kWh',
                                 'WACC': 0.07,  # ?
                                 'learning_rate': 0.2,  # augmentation of forests ha per year?
                                 'lifetime': lifetime,  # for now constant in time but should increase with time
                                 'lifetime_unit': GlossaryEnergy.Years,
                                 # To be defined, should be nearly 0
                                 'Capex_init': 59.48,
                                 'Capex_init_unit': 'euro/ha',
                                 'full_load_hours': 8760.0,
                                 'euro_dollar': 1.2195,  # in 2021, date of the paper
                                 # WBA-World Bioenergy Association, 2021. Global bioenergy statistics.
                                 # To be defined
                                 'available_power': 0,  # average, worldbioenergy.org
                                 'available_power_unit': 'kg',
                                 'efficiency': 0.0,
                                 'techno_evo_eff': 'no',  # yes or no

                                 GlossaryEnergy.ConstructionDelay: construction_delay}
    # invest: 7% of ha are planted each year at 13047.328euro/ha
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), GlossaryEnergy.InvestValue: [0.0, 0.0, 0.0]})
    # To be defined
    initial_production = 1e-12  # in Twh
    # to be defined
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
                                       'dataframe_descriptor': {
                                           GlossaryEnergy.Years: ('int', [1900, GlossaryEnergy.YearEndDefaultCore], False),
                                           'age': ('float', None, True),
                                           'distrib': ('float', None, True),
                                           }
                                       },
               GlossaryEnergy.InvestmentBeforeYearStartValue: {'type': 'dataframe', 'unit': 'G$',
                                                               'default': invest_before_year_start,
                                                               'dataframe_descriptor': {
                                                                   'past years': ('int', [-20, -1], False),
                                                                   GlossaryEnergy.InvestValue: ('float', None, True)},
                                                               'dataframe_edition_locked': False}}
    # -- add specific techno inputs to this
    DESC_IN.update(WetBiomassTechnoDiscipline.DESC_IN)

    # -- add specific techno outputs to this
    DESC_OUT = WetBiomassTechnoDiscipline.DESC_OUT

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = AnimalManure(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
