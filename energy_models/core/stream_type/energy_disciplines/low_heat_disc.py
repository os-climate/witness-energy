'''
Copyright 2023 Capgemini

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
from energy_models.core.stream_type.energy_disc import EnergyDiscipline
from energy_models.core.stream_type.energy_models.heat import lowtemperatureheat
from energy_models.glossaryenergy import GlossaryEnergy


class LowHeatDiscipline(EnergyDiscipline):
    # ontology information
    _ontology_data = {
        'label': ' Low Heat Energy Model',
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

    DESC_IN = {GlossaryEnergy.techno_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                                            'possible_values': lowtemperatureheat.default_techno_list,
                                            'default': lowtemperatureheat.default_techno_list,
                                            'visibility': EnergyDiscipline.SHARED_VISIBILITY,
                                            'namespace': 'ns_heat_low',
                                            'structuring': True, 'unit': '-'
                                            },
               'data_fuel_dict': {'type': 'dict', 'visibility': EnergyDiscipline.SHARED_VISIBILITY,
                                  'unit': 'defined in dict',
                                  'namespace': 'ns_heat_low', 'default': lowtemperatureheat.data_energy_dict},
               }
    DESC_IN.update(EnergyDiscipline.DESC_IN)
    energy_name = lowtemperatureheat.name

    DESC_OUT = EnergyDiscipline.DESC_OUT  # -- add specific techno outputs to this

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.energy_model = lowtemperatureheat(self.energy_name)
        self.energy_model.configure_parameters(inputs_dict)

