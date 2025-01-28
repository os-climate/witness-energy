'''
Copyright 2022 Airbus SAS
Modifications on 2023/03/29-2024/06/24 Copyright 2023 Capgemini

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
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import (
    InstanciatedSeries,
    TwoAxesInstanciatedChart,
)

from energy_models.core.stream_type.carbon_models.carbon_storage import CarbonStorage
from energy_models.core.stream_type.stream_disc import StreamDiscipline
from energy_models.glossaryenergy import GlossaryEnergy


class CarbonStorageDiscipline(StreamDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Carbon Storage Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-truck-loading fa-fw',
        'version': '',
    }
    unit = "Mt"
    DESC_IN = {GlossaryEnergy.techno_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                                            'possible_values': CarbonStorage.default_techno_list,
                                            'visibility': 'Shared',
                                            'unit': '-',
                                            'namespace': 'ns_carbon_storage', 'structuring': True},
               'data_fuel_dict': {'type': 'dict', 'visibility': 'Shared',
                                  'namespace': 'ns_carbon_storage', 'default': CarbonStorage.data_energy_dict,
                                  'unit': 'defined in dict'},
               }

    DESC_IN.update(StreamDiscipline.DESC_IN.copy())

    stream_name = GlossaryEnergy.carbon_storage

    DESC_OUT = StreamDiscipline.DESC_OUT.copy()  # -- add specific techno outputs to this

    def init_execution(self):
        super().init_execution()
        self.model = CarbonStorage(self.stream_name)

