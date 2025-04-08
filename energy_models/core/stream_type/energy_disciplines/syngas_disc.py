'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/15-2024/06/24 Copyright 2023 Capgemini

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
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import (
    InstanciatedSeries,
    TwoAxesInstanciatedChart,
)
from sostrades_optimization_plugins.models.autodifferentiated_discipline import (
    AutodifferentiedDisc,
)

from energy_models.core.stream_type.energy_disc import EnergyDiscipline
from energy_models.core.stream_type.energy_models.syngas import (
    Syngas,
)
from energy_models.glossaryenergy import GlossaryEnergy


class SyngasDiscipline(EnergyDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Syngas Energy Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-burn fa-fw',
        'version': '',
    }

    DESC_IN = {GlossaryEnergy.techno_list: {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                                            'possible_values': Syngas.default_techno_list,

                                            'visibility': EnergyDiscipline.SHARED_VISIBILITY,
                                            'namespace': 'ns_syngas', 'structuring': True,
                                            'unit': '-'},

               'data_fuel_dict': {'type': 'dict',
                                  'visibility': EnergyDiscipline.SHARED_VISIBILITY,
                                  'namespace': 'ns_syngas',
                                  'default': Syngas.data_energy_dict,
                                  'unit': 'defined in dict'},
               }
    DESC_IN.update(EnergyDiscipline.DESC_IN)

    stream_name = GlossaryEnergy.syngas

    DESC_OUT = {'syngas_ratio': {'type': 'array', 'unit': '%', EnergyDiscipline.GRADIENTS: True,
                                 'visibility': EnergyDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_syngas'},
                'syngas_ratio_technos': {'type': 'dict', 'unit': '%', 'subtype_descriptor': {'dict': 'float'},
                                         'visibility': EnergyDiscipline.SHARED_VISIBILITY, 'namespace': 'ns_syngas'},
                }

    # -- add specific techno outputs to this
    DESC_OUT.update(EnergyDiscipline.DESC_OUT)

    def init_execution(self):
        super().init_execution()
        self.model = Syngas(self.stream_name)


    def add_additionnal_dynamic_variables(self):
        dynamic_inputs, dynamic_outputs = EnergyDiscipline.add_additionnal_dynamic_variables(self)

        if GlossaryEnergy.techno_list in self.get_data_in():
            techno_list = self.get_sosdisc_inputs(GlossaryEnergy.techno_list)
            if techno_list is not None:
                for techno in techno_list:
                    dynamic_inputs[f'{techno}.syngas_ratio'] = {'type': 'array', 'unit': '%', AutodifferentiedDisc.GRADIENTS: True,}

        return dynamic_inputs, dynamic_outputs


    def get_post_processing_list(self, filters=None):

        generic_filter = EnergyDiscipline.get_chart_filter_list(self)
        instanciated_charts = EnergyDiscipline.get_post_processing_list(
            self, generic_filter)

        year_start, year_end = self.get_sosdisc_inputs(
            [GlossaryEnergy.YearStart, GlossaryEnergy.YearEnd])
        years = np.arange(year_start, year_end + 1)
        syngas_ratio = self.get_sosdisc_outputs(
            'syngas_ratio')
        syngas_ratio_technos = self.get_sosdisc_outputs(
            'syngas_ratio_technos')
        chart_name = 'Molar syngas CO over H2 ratio for the global mix'

        new_chart = TwoAxesInstanciatedChart(GlossaryEnergy.Years, 'CO over H2 molar ratio', [], [],
                                             chart_name=chart_name)

        for techno in syngas_ratio_technos:
            serie = InstanciatedSeries(years, [syngas_ratio_technos[techno]] * len(years), techno, 'lines')

            new_chart.series.append(serie)

        serie = InstanciatedSeries(years, syngas_ratio, f'{GlossaryEnergy.syngas} mix', 'lines')

        new_chart.series.append(serie)

        instanciated_charts.append(new_chart)
        return instanciated_charts
