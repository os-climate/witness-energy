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


from energy_models.core.techno_type.disciplines.gaseous_hydrogen_techno_disc import (
    GaseousHydrogenTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.gaseous_hydrogen.electrolysis.awe.electrolysis_awe import (
    ElectrolysisAWE,
)


class ElectrolysisAWEDiscipline(GaseousHydrogenTechnoDiscipline):
    """
    Electrolysis AWE Discipline
    """

    # ontology information
    _ontology_data = {
        'label': 'Hydrogen Electrolysis AWE Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-hospital-symbol fa-fw',
        'version': '',
    }
    techno_name = GlossaryEnergy.ElectrolysisAWE
    # David, M., Ocampo-Martinez, C. and Sanchez-Pena, R., 2019.
    # Advances in alkaline water electrolyzers: A review.
    # Journal of Energy Storage, 23, pp.392-403.

    techno_infos_dict_default = {'maturity': 5,
                                 'Opex_percentage': 0.05,
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 'WACC': 0.05,
                                 'learning_rate': 0.05,
                                 'maximum_learning_capex_ratio': 200 / 581.25,
                                 'stack_lifetime': 100000,
                                 'stack_lifetime_unit': 'hours',
                                 'Capex_init': 581.25,  # for a power input of 2MW, decreases for 10 MW
                                 'Capex_init_unit': 'euro/kW',
                                 'euro_dollar': 1.114,
                                 'full_load_hours': 8000,
                                 'techno_evo_eff': 'yes',
                                 'techno_evo_time': 10,
                                 'efficiency evolution slope': 0.5,
                                 # electric efficiency that we will use to
                                 # compute elec needs
                                 'efficiency': 0.60,
                                 'efficiency_max': 0.70,
                                 }
    # see doc
    initial_production = 1.6 - 0.4
    # Industrial plants started to emerge around 2015
    # We assume no investments
    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_production': {'type': 'float',
                                      'unit': 'TWh', 'default': initial_production},
               }
    DESC_IN.update(GaseousHydrogenTechnoDiscipline.DESC_IN)

    # -- add specific techno outputs to this
    DESC_OUT = GaseousHydrogenTechnoDiscipline.DESC_OUT

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = ElectrolysisAWE(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
