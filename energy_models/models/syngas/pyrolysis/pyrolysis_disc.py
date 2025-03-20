'''
Copyright 2022 Airbus SAS
Modifications on 2023/10/10-2023/11/16 Copyright 2023 Capgemini

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
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.syngas.pyrolysis.pyrolysis import Pyrolysis


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

    techno_name = GlossaryEnergy.Pyrolysis

    techno_infos_dict_default = {'maturity': 0,
                                 'product': GlossaryEnergy.syngas,
                                 'Opex_percentage': 0.06,
                                 'CO2_from_production': 0.2,
                                 'CO2_from_production_unit': 'kg/kg',
                                 'WACC': 0.075,  # Weighted averaged cost of capital for the carbon capture plant
                                 # 1600T/day of wood capacity, 180M$ of Capital
                                 # cost, 20 years lifetime, 70% syngas yield
                                 'Capex_init': 0.012,
                                 'Capex_init_unit': '$/kWh',
                                 'medium_heat_production': (131 / (28.01 + 2.016)) * 1000 * 2.77778e-13,
                                 # C+H2O→H2+CO   ΔH =+131kJ/mol  # Co(28.01 g/mol),H2(2.016 g/mol)
                                 # https://www.sciencedirect.com/topics/earth-and-planetary-sciences/pyrolysis#:~:text=For%20slow%20pyrolysis%2C%20the%20heating,respectively%20%5B15%2C21%5D.
                                 'medium_heat_production_unit': 'TWh/kg',
                                 'efficiency': 1.0,  # No need of efficiency here
                                 'learning_rate': 0.0,
                                 'techno_evo_eff': 'no',
                                 'syngas_yield': 0.7,  # with 1kg of wood
                                 'char_yield': 0.15,  # with 1kg of wood
                                 'bio_oil_yield': 0.15,  # with 1kg of wood,
                                 'temperature': 1000,
                                 'temperature_unit': 'oC'

                                 }

    techno_info_dict = techno_infos_dict_default

        # From Future of hydrogen : accounting for around three quarters of the
    # annual global dedicated hydrogen production of around 70 million tonnes.
    initial_production = 1e-12  # in TWh at year_start MT*kWh/kg = TWh
    FLUE_GAS_RATIO = np.array([0.13])

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},

               }
    # -- add specific techno outputs to this
    DESC_IN.update(SyngasTechnoDiscipline.DESC_IN)

    _maturity = 'Research'

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = Pyrolysis(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
