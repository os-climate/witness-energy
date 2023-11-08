'''
Copyright 2022 Airbus SAS

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
from energy_models.core.stream_type.energy_models.ultralowsulfurdiesel import UltraLowSulfurDiesel


class UltraLowSulfurDieselDiscipline(EnergyDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Ultra Low Sulfur Diesel Model',
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

    DESC_IN = {
        GlossaryCore.techno_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'}, 'possible_values': ['Refinery'],
                              'visibility': EnergyDiscipline.SHARED_VISIBILITY,
                              'namespace': 'ns_kerosene',
                              'structuring': True,
                              'unit': '-'},
        'data_fuel_dict': {'type': 'dict',
                           'visibility': EnergyDiscipline.SHARED_VISIBILITY,
                           'namespace': 'ns_kerosene',
                           'default': UltraLowSulfurDiesel.data_energy_dict,
                           'unit': 'define in dict'},
    }
    DESC_IN.update(EnergyDiscipline.DESC_IN)

    energy_name = UltraLowSulfurDiesel.name

    DESC_OUT = EnergyDiscipline.DESC_OUT  # -- add specific techno outputs to this

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.energy_model = UltraLowSulfurDiesel(self.energy_name)
        self.energy_model.configure_parameters(inputs_dict)
