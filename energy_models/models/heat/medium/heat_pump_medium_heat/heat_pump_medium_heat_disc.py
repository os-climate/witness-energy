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


from energy_models.core.stream_type.energy_models.heat import mediumtemperatureheat
from energy_models.core.techno_type.disciplines.heat_techno_disc import (
    MediumHeatTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.heat.medium.heat_pump_medium_heat.heat_pump_medium_heat import (
    HeatPump,
)


class HeatPumpMediumHeatDiscipline(MediumHeatTechnoDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Heat Pump Medium Heat Model',
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
    techno_name = GlossaryEnergy.HeatPumpMediumHeat
    stream_name = mediumtemperatureheat.name

    # Heat pumps offer an energy-efficient alternative to furnaces and air conditioners for all climates.
    # Heat pump can reduce your electricity use for heating by approximately 50% compared to
    # electric resistance heating such as furnaces and baseboard heaters.

    # https://en.wikipedia.org/wiki/Heat_pump
    # With 1 kWh of electricity, heat pump can transfer 3 to 6 kWh of thermal energy into a building.
    # Heat pumps could satisfy over 80% of global space and water heating needs with a lower carbon
    # footprint than gas-fired condensing boilers: however, in 2021 they only met 10%

    techno_infos_dict_default = {
        'Capex_init': 718 / (25 * 8760),
        # 660euro/kW/(lifetime * Number of hours in year) # Source:- https://europeanclimate.org/wp-content/uploads/2019/11/14-03-2019-ffe-2050-cost-assumptions.xlsx
        'Capex_init_unit': '$/kWh',
        'Opex_percentage': 0.04,
        # https://europeanclimate.org/wp-content/uploads/2019/11/14-03-2019-ffe-2050-cost-assumptions.xlsx
        'efficiency': 1,  # consumptions and productions already have efficiency included
        'CO2_from_production': 0.0,
        'CO2_from_production_unit': 'kg/kg',
        # 'elec_demand': (1.0 / COP), #*(0.13/100), # Electricity cost 13cent/hr #https://www.perchenergy.com/energy-calculators/heat-pump-electricity-use-cost
        # 'elec_demand_unit': 'kWh/kWh',
        # 'heating_space': 92.9,
        # 'heating_space_unit': 'm^2',
        # 'heat_required_per_meter_square': 0.00879, #https://carbonswitch.com/heat-pump-sizing-guide/#:~:text=If%20you%20Google%20%E2%80%9Cheat%20pump,a%2060%2C000%20BTU%20heat%20pump.
        # 'heat_required_per_meter_square_unit': 'kW/m^2',
        # 'maturity': 5,
        'learning_rate': 0.00,
        'full_load_hours': 8760.0,
        'WACC': 0.075,
        'techno_evo_eff': 'no',
        'output_temperature': 250,
        # Average Medium Temperature, Page Number 152, #https://www.medeas.eu/system/files/documentation/files/D8.11%28D35%29%20Model%20Users%20Manual.pdf
        'mean_temperature': 20,
        'output_temperature_unit': '°C',
        'mean_temperature_unit': '°C',
    }

    # heat_pump_high_heat Heat production
    # production in 2021 #https://www.iea.org/reports/heat-pumps
    # in TWh
    initial_production = 1 * 8760 / 3  # 1000GW * Number of Hours in a Year /(Equally split for High, low and Medium Heat production)

    # Renewable Fuels Association [online]
    # https://ethanolrfa.org/markets-and-statistics/annual-ethanol-production
    flux_input_dict = {'land_rate': 14000, 'land_rate_unit': '$/Gha', }
    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},

               'flux_input_dict': {'type': 'dict', 'default': flux_input_dict, 'unit': 'defined in dict'},
               }
    DESC_IN.update(MediumHeatTechnoDiscipline.DESC_IN)
    # -- add specific techno outputs to this
    DESC_OUT = MediumHeatTechnoDiscipline.DESC_OUT
    _maturity = 'Research'

    def init_execution(self):
        self.model = HeatPump(self.techno_name)
