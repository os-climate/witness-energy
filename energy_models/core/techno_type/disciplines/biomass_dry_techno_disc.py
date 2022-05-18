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

from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
from energy_models.core.techno_type.techno_disc import TechnoDiscipline


class BiomassDryTechnoDiscipline(TechnoDiscipline):

    # ontology information
    _ontology_data = {
        'label': 'Dry Biomass Technology Model',
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
    DESC_IN = {'transport_cost': {'type': 'dataframe', 'unit': '$/t', 'visibility': TechnoDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_biomass_dry',
                                  'dataframe_descriptor': {'years': ('int',  [1900, 2100], False),
                                                           'transport': ('float',  None, True)},
                                  'dataframe_edition_locked': False},
               'transport_margin': {'type': 'dataframe', 'unit': '%', 'visibility': TechnoDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_biomass_dry',
                                    'dataframe_descriptor': {'years': ('int',  [1900, 2100], False),
                                                             'margin': ('float',  None, True)},
                                    'dataframe_edition_locked': False},
               'data_fuel_dict': {'type': 'dict', 'visibility': TechnoDiscipline.SHARED_VISIBILITY,
                                  'namespace': 'ns_biomass_dry', 'default': BiomassDry.data_energy_dict,
                                  'unit': 'defined in dict'},
               }
    DESC_IN.update(TechnoDiscipline.DESC_IN)

    _maturity = 'Research'

    energy_name = BiomassDry.name
