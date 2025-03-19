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


from energy_models.core.techno_type.disciplines.methane_techno_disc import (
    MethaneTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.methane.methanation.methanation import Methanation


class MethanationDiscipline(MethaneTechnoDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Methanation Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-bong fa-fw',
        'version': '',
    }
    # -- add specific techno inputs to this

    techno_name = GlossaryEnergy.Methanation

    techno_infos_dict_default = {'reaction': 'CO2 + 4H2 = CH4 + 2 H20',
                                 'Opex_percentage': 0.02,
                                 # Rosenfeld, D.C., Böhm, H., Lindorfer, J. and Lehner, M., 2020.
                                 # Scenario analysis of implementing a power-to-gas and biomass gasification system in an integrated steel plant:
                                 # A techno-economic and environmental study.
                                 # Renewable energy, 147, pp.1511-1524.
                                 'Capex_init': 660.0,  # Capex initial at year 2020 p6 Rosenfeld2020
                                 'Capex_init_unit': 'euro/kW',
                                 'efficiency': 0.4,
                                 'maturity': 3,
                                 'learning_rate': 0.2,
                                 'available_power': 6300,
                                 'available_power_unit': 'kW',
                                 'euro_dollar': 1.114,
                                 'full_load_hours': 8000.0,
                                 'WACC': 0.0878,
                                     'techno_evo_eff': 'no',  # in kWh/kg
                                 }

    # Methanation is mostly used in PtG plants
    # In early 2019, a production capacity for methane is about 590 m3/h
    # from Power-to-Gas: Electrolysis and methanation status review M. Thema,
    # F. Bauer, M. Sterner Technical University of Applied Sciences (OTH)

    initial_production = 590.0 * 8760.0 * 13.9 * \
                         0.657 * 1.0e-9  # in TWh at year_start

    # from Power-to-Gas: Electrolysis and methanation status review M. Thema,
    # F. Bauer, M. Sterner Technical University of Applied Sciences (OTH)
    # Fig10
    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
    }

    DESC_IN.update(MethaneTechnoDiscipline.DESC_IN)
    # -- add specific techno outputs to this
    DESC_OUT = MethaneTechnoDiscipline.DESC_OUT

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = Methanation(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
