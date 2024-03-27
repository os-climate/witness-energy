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

from energy_models.core.techno_type.disciplines.solid_fuel_techno_disc import SolidFuelTechnoDiscipline
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.solid_fuel.pelletizing.pelletizing import Pelletizing


class PelletizingDiscipline(SolidFuelTechnoDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Solid Fuel Pelletizing Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-circle fa-fw',
        'version': '',
    }

    techno_name = GlossaryEnergy.Pelletizing
    # Wang, Y., Li, G., Liu, Z., Cui, P., Zhu, Z. and Yang, S., 2019.
    # Techno-economic analysis of biomass-to-hydrogen process in comparison with coal-to-hydrogen process.
    # Energy, 185, pp.1063-1075.
    # Rosenfeld, D.C., B�hm, H., Lindorfer, J. and Lehner, M., 2020.
    # Scenario analysis of implementing a power-to-gas and biomass gasification system in an integrated steel plant:
    # A techno-economic and environmental study. Renewable energy, 147,
    # pp.1511-1524.
    lifetime = 25  # Wang2019 Rosenfeld2020 says 20
    construction_delay = 3  # years
    techno_infos_dict_default = {'maturity': 5,
                                 'Opex_percentage': 0.0625,
                                 # production of CO2 in kg per kg of pellets
                                 # Wiley, A., 2009. Energy and Carbon Balance in Wood Pellet Manufacture.
                                 # Hunt, Guillot and Associates, Ruston,
                                 # Louisiana. https://www. hga-llc.
                                 # com/images/2014.
                                 'CO2_from_production': 0.116,
                                 'CO2_from_production_unit': 'kg/kg',
                                 # electricity to product 1kg of pellets
                                 'elec_demand': 0.1062,
                                 'elec_demand_unit': 'kWh/kg',
                                 'WACC': 0.01,
                                 'learning_rate': 0.2,
                                 'lifetime': lifetime,  # for now constant in time but should increase with time
                                 'lifetime_unit': GlossaryEnergy.Years,
                                 # Capex in $
                                 'Capex_init': 29287037.04,
                                 'Capex_init_unit': 'euro',
                                 'full_load_hours': 8000.0,
                                 'euro_dollar': 1.08,
                                 'available_power': 400000000,  # 400000 ton/year
                                 'available_power_unit': 'kg/year',
                                 'efficiency': 0.85,  # boiler efficiency
                                 'techno_evo_eff': 'no',  # yes or no
                                 GlossaryEnergy.ConstructionDelay: construction_delay}
    # We do not invest on biomass gasification yet
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), GlossaryEnergy.InvestValue: [7.6745661, 8.9729523, 104.91]})
    # initial production : 45,21 million tonnes => x calorific value and
    # conversion in TWh
    initial_production = 217.04
    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': [10.39, 11.93, 1.13, 7.97, 7.14,
                                                         6.4, 5.73, 11.66, 11.66, 0.89,
                                                         0.89, 3.55, 3.55, 4.56, 2.53,
                                                         2.53, 1.27, 0.63, 0.63, 1.01,
                                                         1.01, 1.01, 1.01, 0.92]})
    FLUE_GAS_RATIO = np.array([0.12])

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                                'age': ('float', None, True),
                                                                'distrib': ('float', None, True)}
                                       },
               GlossaryEnergy.InvestmentBeforeYearStartValue: {'type': 'dataframe', 'unit': 'G$',
                                                               'default': invest_before_year_start,
                                                               'dataframe_descriptor': {
                                                                   'past years': ('int', [-20, -1], False),
                                                                   GlossaryEnergy.InvestValue: ('float', None, True)},
                                                               'dataframe_edition_locked': False}}
    # -- add specific techno inputs to this
    DESC_IN.update(SolidFuelTechnoDiscipline.DESC_IN)

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = Pelletizing(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
