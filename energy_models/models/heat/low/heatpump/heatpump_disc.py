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
from energy_models.core.techno_type.disciplines.heat_techno_disc import LowHeatTechnoDiscipline
from energy_models.core.stream_type.energy_models.heat import LowTemperatureHeat
from energy_models.models.heat.low.heatpump.heatpump import HeatPump


class HeatPumpDiscipline(LowHeatTechnoDiscipline):

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
    techno_name = 'LowHeatPump'
    energy_name = LowTemperatureHeat.name

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
    COP = 3.5

    techno_infos_dict_default = {

        # Gubicza K, Nieves IU, Sagues WJ, Barta Z, Shanmugam KT, Ingram LO.Techno - economic analysis of ethanol
        # production from sugarcane bagasse using a Liquefaction plus Simultaneous Saccharification and co -
        # Fermentation process.Bioresour Technol. 2016
        # from table 6: capex 1.95$/liter
        'Capex_init': 1051, # https://europeanclimate.org/wp-content/uploads/2019/11/14-03-2019-ffe-2050-cost-assumptions.xlsx
        'Capex_init_unit': '$/kW',
        'Opex_percentage': 0.04, ## https://europeanclimate.org/wp-content/uploads/2019/11/14-03-2019-ffe-2050-cost-assumptions.xlsx
        'lifetime': lifetime,
        'lifetime_unit': 'years',
        'construction_delay': construction_delay,
        'construction_delay_unit': 'years',
        'efficiency': 1,    # consumptions and productions already have efficiency included
        'CO2_from_production': 0.0,
        'CO2_from_production_unit': 'kg/kg',
        'elec_demand': (1.0 / COP),  #*(0.13/100), # Electricity cost 13cent/hr #https://www.perchenergy.com/energy-calculators/heat-pump-electricity-use-cost
        'elec_demand_unit': 'kWh/kW',
        'heating_space': 92.9,
        'heating_space_unit': 'm^2',
        'heat_required_per_meter_square': 0.00879,
        # https://carbonswitch.com/heat-pump-sizing-guide/#:~:text=If%20you%20Google%20%E2%80%9Cheat%20pump,a%2060%2C000%20BTU%20heat%20pump.
        'heat_required_per_meter_square_unit': 'kW/m^2',
##        'water_demand':  3.5,
##        'water_demand_unit': 'm3/m3',
##        'biomass_dry_demand': 56 * pound_to_kg / (2.9 * gallon_to_m3),
##        'biomass_dry_demand_unit': 'kg/m3',
        # 'co2_captured__production': 17 * pound_to_kg / (2.9 * gallon_to_m3),
        # 'co2_captured__production_unit': 'kg/m3',
        'maturity': 5,
        'learning_rate': 0.1,
        'full_load_hours': 8760.0,
        'WACC': 0.075,
        'techno_evo_eff': 'no',
    }

    # heatpump Heat production
    # production in 2021 #https://www.iea.org/reports/heat-pumps
    # in TWh
    initial_production = 1.452777

    distrib = [9.677419355, 7.52688172, 0,
               5.376344086, 4.301075269, 5.376344086, 11.82795699, 21.50537634,
               13.97849462, 9.677419355,   7.52688172,   1.075268817,
               2.150537634,  0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0]

    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': 100 / sum(distrib) * np.array(distrib)})  # to review

    # Renewable Fuels Association [online]
    # https://ethanolrfa.org/markets-and-statistics/annual-ethanol-production
    invest_before_year_start = pd.DataFrame(
        {'past years': np.array(-construction_delay), 'invest': 1051 * np.array([1062000000])})

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'age': ('int',  [0, 100], False),
                                                                'distrib': ('float',  None, True)},
                                       'dataframe_edition_locked': False},
               'invest_before_ystart': {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int',  [-20, -1], False),
                                                                 'invest': ('float',  None, True)},
                                        'dataframe_edition_locked': False}}
    DESC_IN.update(LowHeatTechnoDiscipline.DESC_IN)
    # -- add specific techno outputs to this
    DESC_OUT = LowHeatTechnoDiscipline.DESC_OUT
    _maturity = 'Research'

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = HeatPump(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
