'''
Copyright 2024 Capgemini
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


from energy_models.core.techno_type.disciplines.clean_energy_disc import (
    CleanEnergyTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.clean_energy.clean_energy_simple_techno.clean_energy_simple_techno import (
    CleanEnergySimpleTechno,
)


class CleanEnergySimpleTechnoDiscipline(CleanEnergyTechnoDiscipline):
    """
        Generic Clean Techno used in the WITNESS Coarse process
        It has a high price per kWh without CO2 but a low CO2 emissions per kWh
        Its meant to model technos likes solar, wind, nuclear, biomass, hyropower in Witness COARSE.
        It has properties similar to electricity technologies
    """

    # ontology information
    _ontology_data = {
        'label': 'Clean Energy Technology Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-fan fa-fw',
        'version': '',
    }
    techno_name = GlossaryEnergy.CleanEnergySimpleTechno

    # net production = 25385.78 TWh
    initial_production = 31552.17  # TWh
    # from witness full study
    clean_energy_capital = 12.414  # trillion dollars

    techno_infos_dict_default = {'maturity': 0,
                                 'Opex_percentage': 0.06,
                                 'WACC': 0.058,
                                 'learning_rate': 0.01,
                                 'Capex_init': 572.,
                                 'Capex_init_unit': '$/MWh',
                                 'techno_evo_eff': 'no',
                                 'efficiency': 1.0,
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 'resource_price': 10.0,
                                 'resource_price_unit': '$/MWh'}

    techno_info_dict = techno_infos_dict_default

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
                      }
    # -- add specific techno outputs to this
    DESC_IN.update(CleanEnergyTechnoDiscipline.DESC_IN)

    DESC_OUT = CleanEnergyTechnoDiscipline.DESC_OUT

    _maturity = 'Research'

    def init_execution(self):
        self.model = CleanEnergySimpleTechno(self.techno_name)
