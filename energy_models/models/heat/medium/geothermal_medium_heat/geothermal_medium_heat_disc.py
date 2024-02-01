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

import numpy as np
import pandas as pd

from energy_models.core.stream_type.energy_models.heat import mediumtemperatureheat
from energy_models.core.techno_type.disciplines.heat_techno_disc import MediumHeatTechnoDiscipline
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.heat.medium.geothermal_medium_heat.geothermal_medium_heat import GeothermalHeat
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart


class GeothermalMediumHeatDiscipline(MediumHeatTechnoDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Geothermal Medium Heat Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-gas-pump fa-fw',
        'version': '',
    }
    # -- add specific techno inputs to this
    techno_name = 'GeothermalMediumHeat'
    energy_name = mediumtemperatureheat.name

    lifetime = 25  # in years # https://www.energy.gov/eere/geothermal/articles/life-cycle-analysis-results-geothermal-systems-comparison-other-power

    construction_delay = 1  # in years
    techno_infos_dict_default = {
        'Capex_init': 3830,
        # https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2017/Aug/IRENA_Geothermal_Power_2017.pdf
        'Capex_init_unit': '$/kW',
        'Opex_percentage': 0.0287,
        # https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2017/Aug/IRENA_Geothermal_Power_2017.pdf
        'lifetime': lifetime,
        'lifetime_unit': GlossaryEnergy.Years,
        GlossaryEnergy.ConstructionDelay: construction_delay,
        'construction_delay_unit': GlossaryEnergy.Years,
        'efficiency': 1,  # consumptions and productions already have efficiency included
        'CO2_from_production': 0.122,
        # high GHG concentrations in the reservoir fluid # https://documents1.worldbank.org/curated/en/875761592973336676/pdf/Greenhouse-Gas-Emissions-from-Geothermal-Power-Production.pdf
        'CO2_from_production_unit': 'kg/kWh',
        'maturity': 5,
        'learning_rate': 0.00,
        'full_load_hours': 8760.0,
        'WACC': 0.075,
        'techno_evo_eff': 'no',
        'output_temperature': 250,
        # Average Medium Temperature, Page Number 152, #https://www.medeas.eu/system/files/documentation/files/D8.11%28D35%29%20Model%20Users%20Manual.pdf
        'mean_temperature': 200,
        'output_temperature_unit': 'K',
        'mean_temperature_unit': 'K',
        'steel_needs': 968,
        # Page:21 #https://www.energy.gov/eere/geothermal/articles/life-cycle-analysis-results-geothermal-systems-comparison-other-power
    }

    # geothermal_high_heat Heat production
    # production in 2019 #https://en.wikipedia.org/wiki/Geothermal_power
    # in TWh
    initial_production = 182500 / 3  # Equally split for High, low and Medium Heat production, #https://www.iea.org/data-and-statistics/charts/direct-use-of-geothermal-energy-world-2012-2024

    distrib = [9.677419355, 7.52688172, 0,
               5.376344086, 4.301075269, 5.376344086, 11.82795699, 21.50537634,
               13.97849462, 9.677419355, 7.52688172, 1.075268817,
               2.150537634, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': 100 / sum(distrib) * np.array(distrib)})  # to review

    invest_before_year_start = pd.DataFrame(
        {'past years': np.array(-construction_delay), GlossaryEnergy.InvestValue: 3830/(25*8760) * np.array([182500/3])})

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'age': ('int', [0, 100], False),
                                                                'distrib': ('float', None, True)},
                                       'dataframe_edition_locked': False},
               GlossaryEnergy.InvestmentBeforeYearStartValue: {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int',  [-20, -1], False),
                                                                 GlossaryEnergy.InvestValue: ('float',  None, True)},
                                        'dataframe_edition_locked': False},

               }
    DESC_IN.update(MediumHeatTechnoDiscipline.DESC_IN)
    # -- add specific techno outputs to this
    DESC_OUT = MediumHeatTechnoDiscipline.DESC_OUT
    _maturity = 'Research'

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = GeothermalHeat(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)

#     def setup_sos_disciplines(self):
#         super().setup_sos_disciplines()
#
#     def run(self):
#         '''
#         Run for all energy disciplines
# self.get_sosdisc_inputs()
#         self.techno_model.config        '''
#         MediumHeatTechnoDiscipline.run(self)

