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

from energy_models.models.electricity.solar_thermal.solar_thermal import SolarThermal
from energy_models.core.techno_type.disciplines.electricity_techno_disc import ElectricityTechnoDiscipline

from sos_trades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, TwoAxesInstanciatedChart
from sos_trades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sos_trades_core.tools.post_processing.pie_charts.instanciated_pie_chart import InstanciatedPieChart


class SolarThermalDiscipline(ElectricityTechnoDiscipline):
    """**EnergyModelsDiscipline** is the :class:`~gems.core.discipline.MDODiscipline`
    implementing the computation of Energy Models outputs."""

    # mean values for plant with 8 hours storage

    techno_name = 'SolarThermal'
    lifetime = 25  # JRC, IRENA, SolarPACES
    construction_delay = 3  # JRC, ATB NREL, database https://solarpaces.nrel.gov/
    techno_infos_dict_default = {'maturity': 0,
                                 'product': 'electricity',
                                 # OPEX : lmean of lazard / JRC / ATB NREL
                                 'Opex_percentage': 0.015,
                                 # WACC : mean of Frauhofer / IRENA / ATB NREL
                                 'WACC': 0.062,
                                 'learning_rate':  0.07,  # JRC
                                 'lifetime': lifetime,
                                 'lifetime_unit': 'years',
                                 # Capex : mean of JRC / IRENA /ATB NREL / ...
                                 'Capex_init': 5000,
                                 'Capex_init_unit': '$/kW',
                                 'techno_evo_eff': 'no',
                                 'efficiency': 1.0,
                                 'full_load_hours': 8760,  # max value
                                 # capacity factor actual mean JRC / ATC NREL
                                 # and reverse calculation from IRENA values
                                 # (6.3 GW and 15.6 TWh)
                                 'capacity_factor': 0.4,
                                 'capacity_factor_at_year_end': 0.50,  # value IRENA / ATB NREL
                                 'density_per_ha': 346564.9,  # 10% less space than solar pv
                                 'density_per_ha_unit': 'kWh/ha',
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 'construction_delay': construction_delay}

    techno_info_dict = techno_infos_dict_default
    initial_production = 15.6  # in TWh at year_start (IEA)
    # Invest before year start
    # from
    # https://www.irena.org/Statistics/View-Data-by-Topic/Finance-and-Investment/Investment-Trends
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), 'invest': [1.41, 14.0, 14.0]})

    # from database https://solarpaces.nrel.gov/
    # Nb plants 'Operational' and not pilot/demo/proto
    # only commercial or production
    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': [9.677419355, 7.52688172, 0,
                                                         5.376344086, 4.301075269, 5.376344086, 11.82795699, 21.50537634,
                                                         13.97849462, 9.677419355,   7.52688172,   1.075268817,
                                                         2.150537634,  0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0]
                                             })

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default},
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'age': ('int',  [0, 100], False),
                                                                'distrib': ('float',  None, True)},
                                       'dataframe_edition_locked': False},
               'invest_before_ystart': {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int',  [-20, -1], False),
                                                                 'invest': ('float',  None, True)},
                                        'dataframe_edition_locked': False}}
    # -- add specific techno outputs to this
    DESC_IN.update(ElectricityTechnoDiscipline.DESC_IN)

    DESC_OUT = ElectricityTechnoDiscipline.DESC_OUT

    _maturity = 'Research'

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = SolarThermal(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
