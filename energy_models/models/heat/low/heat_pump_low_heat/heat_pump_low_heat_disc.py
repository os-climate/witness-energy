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

from energy_models.core.stream_type.energy_models.heat import lowtemperatureheat
from energy_models.core.techno_type.disciplines.heat_techno_disc import LowHeatTechnoDiscipline
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.heat.low.heat_pump_low_heat.heat_pump_low_heat import HeatPump
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart


class HeatPumpLowHeatDiscipline(LowHeatTechnoDiscipline):

    # ontology information
    _ontology_data = {
        'label': 'Heat Pump Low Heat Model',
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
    techno_name = 'HeatPumpLowHeat'
    energy_name = lowtemperatureheat.name

    lifetime = 25           # years
    # https://www.energy.gov/energysaver/heat-pump-systems
    # Heat pumps offer an energy-efficient alternative to furnaces and air conditioners for all climates.
    # Heat pump can reduce your electricity use for heating by approximately 50% compared to
    # electric resistance heating such as furnaces and baseboard heaters.

    # https://en.wikipedia.org/wiki/Heat_pump
    # With 1 kWh of electricity, heat pump can transfer 3 to 6 kWh of thermal energy into a building.
    # Heat pumps could satisfy over 80% of global space and water heating needs with a lower carbon
    # footprint than gas-fired condensing boilers: however, in 2021 they only met 10%
    construction_delay = 1  # years

    techno_infos_dict_default = {

        'Capex_init': 718/(25*8760), #660euro/kW/(lifetime * Number of hours in year) # Source:- https://europeanclimate.org/wp-content/uploads/2019/11/14-03-2019-ffe-2050-cost-assumptions.xlsx
        'Capex_init_unit': '$/kWh',
        'Opex_percentage': 0.04, ## https://europeanclimate.org/wp-content/uploads/2019/11/14-03-2019-ffe-2050-cost-assumptions.xlsx
        'lifetime': lifetime,
        'lifetime_unit': GlossaryEnergy.Years,
        GlossaryEnergy.ConstructionDelay: construction_delay,
        'construction_delay_unit': GlossaryEnergy.Years,
        'efficiency': 1,    # consumptions and productions already have efficiency included
        'CO2_from_production': 0.0,
        'CO2_from_production_unit': 'kg/kg',
        'maturity': 5,
        'learning_rate': 0.1,
        'full_load_hours': 8760.0,
        'WACC': 0.075,
        'techno_evo_eff': 'no',
        'output_temperature': 60, # Average Low Temperature, Page Number 152, #https://www.medeas.eu/system/files/documentation/files/D8.11%28D35%29%20Model%20Users%20Manual.pdf
        'mean_temperature': 20,
        'output_temperature_unit': '°C',
        'mean_temperature_unit': '°C',
    }

    # heat_pump_high_heat Heat production
    # production in 2021 #https://www.iea.org/reports/heat-pumps
    # in TWh
    initial_production = 1*8760/3 # 1000GW * Number of Hours in a Year /(Equally split for High, low and Medium Heat production)

    distrib = [9.677419355, 7.52688172, 0,
               5.376344086, 4.301075269, 5.376344086, 11.82795699, 21.50537634,
               13.97849462, 9.677419355,   7.52688172,   1.075268817,
               2.150537634,  0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0]

    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': 100 / sum(distrib) * np.array(distrib)})  # to review
    invest_before_year_start = pd.DataFrame(
        {'past years': np.array(-construction_delay), GlossaryEnergy.InvestValue: 0 * np.array([1*8760*0.5*0.5/3])}) # Invest before year start is 0
    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'age': ('int',  [0, 100], False),
                                                                'distrib': ('float',  None, True)},
                                       'dataframe_edition_locked': False},
               GlossaryEnergy.InvestmentBeforeYearStartValue: {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int',  [-20, -1], False),
                                                                 GlossaryEnergy.InvestValue: ('float',  None, True)},
                                        'dataframe_edition_locked': False},
               }
    DESC_IN.update(LowHeatTechnoDiscipline.DESC_IN)
    # -- add specific techno outputs to this
    DESC_OUT = LowHeatTechnoDiscipline.DESC_OUT
    _maturity = 'Research'

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = HeatPump(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)

#     def setup_sos_disciplines(self):
#         super().setup_sos_disciplines()
#
#     def run(self):
#         '''
#         Run for all energy disciplines
#         '''
#
#         inputs_dict = self.get_sosdisc_inputs()
#         self.techno_model.configure_parameters_update(inputs_dict)
#         super().run()
#
# #