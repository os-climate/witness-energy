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

import pandas as pd
import numpy as np

from climateeconomics.glossarycore import GlossaryCore
from energy_models.core.techno_type.disciplines.carbon_storage_techno_disc import CSTechnoDiscipline
from energy_models.models.carbon_storage.reforestation.reforestation import Reforestation
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, TwoAxesInstanciatedChart
from copy import deepcopy


class ReforestationDiscipline(CSTechnoDiscipline):

    # ontology information
    _ontology_data = {
        'label': 'Reforestation Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-tree fa-fw',
        'version': '',
    }

    # Reforestation is the cost of planting tree with no managing nor cutting
    # Eighteen percent of the world�s forests are now located within
    # protected areas

    techno_name = 'Reforestation'
    lifetime = 150
    construction_delay = 3  # years
    techno_infos_dict_default = {'maturity': 0,
                                 #
                                 'Opex_percentage': 0.0,
                                 # 1 tree absorbs in average 30kgCO2/year.
                                 # In the world (ourworldindata) the average of
                                 # tree per ha is 225.4
                                 'CO2_capacity_peryear': 6762.1,
                                 'CO2_capacity_peryear_unit': 'kg CO2/ha/year',
                                 'elec_demand': 0,
                                 'elec_demand_unit': 'kWh/kWh',
                                 'WACC': 0.07,  # ?
                                 'learning_rate': 0.0,
                                 'lifetime': lifetime,  # for now constant in time but should increase with time
                                 'lifetime_unit': GlossaryCore.Years,
                                 # Capex init: 12000 $/ha to buy the land (CCUS-report_V1.30)
                                 # + 2564.128 euro/ha (ground preparation, planting) (www.teagasc.ie)
                                 # 76.553 ans is computed on the forests distribution of those 150 last years
                                 # 1USD = 0,87360 euro in 2019
                                 'Capex_init': 13047.328 * 1.1447 / 6762.1 / 79.553,
                                 'Capex_init_unit': '$/kgCO2',
                                 'euro_dollar': 1.1447,  # in 2019, date of the paper

                                 # available land for forest plantation : 0.9 Milliard ha
                                 # protected land are 25% of global forests
                                 # area (1008Mha)
                                 'available_land': 1008000000,  # FAO
                                 'available_land_unit': 'ha',

                                 'enthalpy': 1.124,
                                 'enthalpy_unit': 'kWh/kgC02',

                                 'density_per_ha': 117.0,  # m3/ha, FAO
                                 'density_per_ha_unit': 'm^3/ha',
                                 'density': 1188.0,  # kg/m3, FAO 139 t/ha
                                 'efficiency': 1.0,
                                 'techno_evo_eff': 'no',  # yes or no

                                 'construction_delay': construction_delay}

    # invest: 0.1 Mha are planted each year at 13047.328euro/ha
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), GlossaryCore.InvestValue: [0, 0, 0]})
    #
    initial_storage = 0   # in MtCO2
    # distrib computed, for planted forests since 150 years
    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': [0.51, 0.51, 0.51, 0.51, 0.51, 0.51, 0.51, 0.51, 0.51, 0.51,
                                                         0.51, 0.51, 0.51, 0.52, 0.51, 0.52, 0.52, 0.52, 0.52, 0.52,
                                                         0.52, 0.53, 0.53, 0.53, 0.53, 0.53, 0.53, 0.54, 0.54, 0.54,
                                                         0.54, 0.54, 0.54, 0.54, 0.55, 0.55, 0.55, 0.55, 0.55, 1.52,
                                                         0.55, 0.56, 0.56, 0.56, 0.56, 0.56, 0.56, 0.56, 0.57, 0.57,
                                                         1.52, 1.52, 0.57, 0.57, 0.57, 0.57, 0.58, 0.58, 0.58, 0.58,
                                                         0.58, 0.58, 0.58, 0.59, 0.59, 0.59, 0.59, 0.59, 0.59, 0.59,
                                                         1.52, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.61, 0.61, 0.61, 0.61,
                                                         0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.71, 0.7, 0.7, 0.71, 0.71,
                                                         0.63, 0.63, 0.64, 0.64, 0.64, 0.64, 0.64, 0.65, 0.65, 0.65,
                                                         0.65, 0.65, 0.65, 0.65, 0.66, 0.66, 0.66, 0.66, 0.66, 0.66,
                                                         0.66, 0.67, 0.67, 0.67, 0.67, 0.67, 0.67, 0.67, 0.68, 0.68,
                                                         0.68, 0.68, 0.68, 0.68, 0.68, 0.69, 0.69, 0.69, 0.69, 0.69,
                                                         0.69, 1.53, 0.69, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.71,
                                                         4.98, 0.71, 0.71, 0.71, 0.71, 0.71]})

#

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default},
               'initial_production': {'type': 'float', 'unit': 'MtCO2', 'default': initial_storage},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {GlossaryCore.Years: ('int', [1900, 2100], False),
                                                                'age': ('float', None, True),
                                                                'distrib': ('float', None, True),
                                                                }
                                       },
               GlossaryCore.InvestmentBeforeYearStartValue: {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int',  [-20, -1], False),
                                                                 GlossaryCore.InvestValue: ('float',  None, True)},
                                        'dataframe_edition_locked': False}}
    # -- add specific techno inputs to this
    DESC_IN.update(CSTechnoDiscipline.DESC_IN)

    # -- add specific techno outputs to this
    DESC_OUT = CSTechnoDiscipline.DESC_OUT

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = Reforestation(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)

    def get_post_processing_list(self, filters=None):

        generic_filter = CSTechnoDiscipline.get_chart_filter_list(self)
        instanciated_charts = CSTechnoDiscipline.get_post_processing_list(
            self, generic_filter)

        available_land = self.get_sosdisc_outputs(GlossaryCore.LandUseRequiredValue)
        year_start = self.get_sosdisc_inputs(GlossaryCore.YearStart)
        year_end = self.get_sosdisc_inputs(GlossaryCore.YearEnd)
        years = np.arange(year_start, year_end + 1)
        minimum = min(
            available_land[f'{self.techno_name} (Gha)'].values.tolist())
        maximum = max(
            available_land[f'{self.techno_name} (Gha)'].values.tolist())

        new_chart = TwoAxesInstanciatedChart(GlossaryCore.Years, 'Land use required (Gha)', [year_start, year_end], [minimum, maximum],
                                             chart_name=f'Land use required for {self.techno_name}')

        # Add total price
        serie = InstanciatedSeries(
            available_land[GlossaryCore.Years].values.tolist(),
            available_land[f'{self.techno_name} (Gha)'].values.tolist(), '', 'lines')

        new_chart.series.append(serie)
        instanciated_charts.append(new_chart)

        return instanciated_charts
