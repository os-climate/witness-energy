'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/14-2024/03/27 Copyright 2023 Capgemini

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

from energy_models.core.techno_type.disciplines.solid_fuel_techno_disc import (
    SolidFuelTechnoDiscipline,
)
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
    # Rosenfeld, D.C., Böhm, H., Lindorfer, J. and Lehner, M., 2020.
    # Scenario analysis of implementing a power-to-gas and biomass gasification system in an integrated steel plant:
    # A techno-economic and environmental study. Renewable energy, 147,
    # pp.1511-1524.

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
                                 # Capex in $
                                 'Capex_init': 29287037.04,
                                 'Capex_init_unit': 'euro',
                                 'full_load_hours': 8000.0,
                                 'euro_dollar': 1.08,
                                 'available_power': 400000000,  # 400000 ton/year
                                 'available_power_unit': 'kg/year',
                                 'efficiency': 0.85,  # boiler efficiency
                                 'techno_evo_eff': 'no',  # yes or no
                                 }
    # We do not invest on biomass gasification yet
        # initial production : 45,21 million tonnes => x calorific value and
    # conversion in TWh
    initial_production = 217.04
    FLUE_GAS_RATIO = np.array([0.12])

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
    }
    # -- add specific techno inputs to this
    DESC_IN.update(SolidFuelTechnoDiscipline.DESC_IN)

    def init_execution(self):
        self.model = Pelletizing(self.techno_name)
