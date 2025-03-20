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
from energy_models.models.gaseous_hydrogen.electrolysis.soec.electrolysis_soec import (
    ElectrolysisSOEC,
)


class ElectrolysisSOECDiscipline(GaseousHydrogenTechnoDiscipline):
    """
    Electrolysis SOEC Discipline
    """

    # ontology information
    _ontology_data = {
        'label': 'Hydrogen Electrolysis SOEC Model',
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
    techno_name = GlossaryEnergy.ElectrolysisSOEC

    techno_infos_dict_default = {'maturity': 5,
                                 'Opex_percentage': 0.03,
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 'WACC': 0.1,
                                 'learning_rate': 0.2,
                                 'maximum_learning_capex_ratio': 500.0 / 2800,
                                 'Capex_init': 2800,
                                 'Capex_init_unit': '$/kW',
                                 'euro_dollar': 1.114,
                                 'full_load_hours': 8000,
                                 'techno_evo_eff': 'yes',
                                 'techno_evo_time': 10,
                                 'efficiency evolution slope': 0.5,
                                 # electric efficiency that we will use to
                                 # compute elec needs
                                 'efficiency': 0.84,
                                 'efficiency_max': 0.92,  # because of topsoe
                                 }

    initial_production = 0.0

    # Public investment in Europe through FCH JU : 156 MEuro or 190M$
    # We assume half is for SOEC .
    # Worldwide the investment of europe for PEM is 36%   190/2*100/32 = 297 M$
    # https://www.euractiv.com/section/energy/news/europe-china-battle-for-global-supremacy-on-electrolyser-manufacturing/
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
        self.techno_model = ElectrolysisSOEC(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
