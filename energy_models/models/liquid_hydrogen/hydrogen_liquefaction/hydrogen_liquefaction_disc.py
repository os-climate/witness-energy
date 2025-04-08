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


from energy_models.core.techno_type.disciplines.liquid_hydrogen_techno_disc import (
    LiquidHydrogenTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.liquid_hydrogen.hydrogen_liquefaction.hydrogen_liquefaction import (
    HydrogenLiquefaction,
)


class HydrogenLiquefactionDiscipline(LiquidHydrogenTechnoDiscipline):
    """
    HydrogenLiquefaction Discipline
    """

    # ontology information
    _ontology_data = {
        'label': 'Hydrogen Liquefaction Model',
        'type': '',
        'source': '',
        'validated': '',
        'validated_by': '',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-tint fa-fw',
        'version': '',
    }
    techno_name = GlossaryEnergy.HydrogenLiquefaction

    techno_infos_dict_default = {'maturity': 5,
                                 'Opex_percentage': 0.0127,
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 'elec_demand': 8,
                                 'elec_demand_unit': 'kWh/kg',
                                 'efficiency': 0.98,
                                 'techno_evo_eff': 'no',
                                 'WACC': 0.1,
                                 # 'heat_recovery_factor': 0.8,
                                 'learning_rate': 0.2,
                                 'stack_lifetime': 100000,
                                 'stack_lifetime_unit': 'hours',
                                 'Capex_init': 500000000,
                                 'Capex_init_unit': 'euro',
                                 'euro_dollar': 1.114,
                                 'available_power': 73000000,
                                 'available_power_unit': 'kg/year',
                                 }

    initial_production = 70.0 * 33.3 * 0.001

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_production': {'type': 'float',
                                      'unit': 'TWh', 'default': initial_production},

               }
    DESC_IN.update(LiquidHydrogenTechnoDiscipline.DESC_IN)

    # -- add specific techno outputs to this
    DESC_OUT = LiquidHydrogenTechnoDiscipline.DESC_OUT

    def init_execution(self):
        self.model = HydrogenLiquefaction(self.techno_name)