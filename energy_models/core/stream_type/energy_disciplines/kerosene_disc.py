'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2023/11/16 Copyright 2023 Capgemini

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
from energy_models.core.stream_type.energy_models.kerosene import Kerosene
from energy_models.glossaryenergy import GlossaryEnergy


class KeroseneDiscipline(EnergyDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Kerosene Energy Model',
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

    DESC_IN = {GlossaryEnergy.techno_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                                            'possible_values': ['AlcoholToFuel', 'BioFuel', 'EOR',
                                                                GlossaryEnergy.Refinery, 'HEFA', GlossaryEnergy.FischerTropsch],
                                            'visibility': EnergyDiscipline.SHARED_VISIBILITY,
                                            'namespace': 'ns_liquid_fuel',
                                            'structuring': True, 'unit': '-'},
               'data_fuel_dict': {'type': 'dict',
                                  'visibility': EnergyDiscipline.SHARED_VISIBILITY,
                                  'namespace': 'ns_liquid_fuel',
                                  'default': Kerosene.data_energy_dict},
               }
    DESC_IN.update(EnergyDiscipline.DESC_IN)

    stream_name = Kerosene.name

    DESC_OUT = EnergyDiscipline.DESC_OUT  # -- add specific techno outputs to this

    def init_execution(self):
        super().init_execution()
        self.model = Kerosene(self.stream_name)

