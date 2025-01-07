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

from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import (
    InstanciatedSeries,
    TwoAxesInstanciatedChart,
)

from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from energy_models.core.techno_type.disciplines.heat_techno_disc import (
    HighHeatTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.heat.high.natural_gas_boiler_high_heat.natural_gas_boiler_high_heat import (
    NaturalGasBoilerHighHeat,
)


class NaturalGasBoilerHighHeatDiscipline(HighHeatTechnoDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Natural Gas Boiler Model',
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
    techno_name = GlossaryEnergy.NaturalGasBoilerHighHeat
    energy_name = hightemperatureheat.name

    # Conversions
    pound_to_kg = 0.45359237
    gallon_to_m3 = 0.00378541
    liter_per_gallon = 3.78541178

    # Heat Producer [Online]
    # https://www.serviceone.com/blog/article/how-long-does-a-home-boiler-last#:~:text=Estimated%20lifespan,most%20parts%20of%20the%20nation.

    # Economic and Technical Analysis of Heat Dry Milling: Model Description.
    # Rhys T.Dale and Wallace E.Tyner Staff Paper
    # Agricultural Economics Department Purdue University

    techno_infos_dict_default = {

        'Capex_init': 199.8,
        'Capex_init_unit': '$/kW',
        'Opex_init': 10.565,
        'Opex_init_unit': '$/kW',
        'efficiency': 0.8,  # consumptions and productions already have efficiency included
        'natural_gas_calorific_val': 53600,
        'natural_gas_calorific_val_unit': 'kJ/kg',
        'natural_gas_flow_rate': 100,
        'natural_gas_flow_rate_unit': 'kg/h',
        'natural_gas_temp': 25,
        'natural_gas_temp_unit': 'c',
        'stoichiometric_ratio': 10,
        'gas_fired_boiler': 2.051,
        'gas_fired_boiler_unit': 'kW/kWh',
        'wall_temp': 300,
        'wall_temp_unit': 'c',
        'methane_demand': 1.35,
        # https://www.google.com/search?q=how+much+KWh+of+methane+required+in+natural+gas+boiler+to+produce+1KWh+of+heat&rlz=1C1UEAD_enIN1000IN1000&oq=how+much+KWh+of+methane+required+in+natural+gas+boiler+to+produce+1KWh+of+heat+&aqs=chrome..69i57.90503j0j7&sourceid=chrome&ie=UTF-8
        'methane_demand_unit': 'kWh/kWh',
        'co2_captured__production': 0.25,  # per kg kWh
        # https://www.google.com/search?q=co2+captured+production+to+produce+heat+in+natural+gas+boiler&rlz=1C1UEAD_enIN1000IN1000&oq=co2+captured+production+to+produce+heat+in+natural+gas+boiler&aqs=chrome..69i57.37619j0j7&sourceid=chrome&ie=UTF-8
        # https://www.google.com/search?q=how+much+KWh+of+methane+required+in+natural+gas+boiler+to+produce+1KWh+of+heat&rlz=1C1UEAD_enIN1000IN1000&oq=how+much+KWh+of+methane+required+in+natural+gas+boiler+to+produce+1KWh+of+heat+&aqs=chrome..69i57.90503j0j7&sourceid=chrome&ie=UTF-8
        'Opex_percentage': 0.024,
        # Fixed 1.9 and recurrent 0.5 %
        # Demystifying-the-Costs-of-Electricity-Generation-Technologies, average
        'WACC': 0.058,  # Weighted averaged cost of capital / ATB NREL 2020
        'learning_rate': 0.00,  # Cost development of low carbon energy technologies
        'full_load_hours': 8760.0,  # Full year hours
        # Demystifying-the-Costs-of-Electricity-Generation-Technologies, average
        'capacity_factor': 0.90,
        'techno_evo_eff': 'no'

    }

    # Renewable Methane Association [online]
    # production in 2020: 561 million gallons
    # in TWh
    # initial production i.e. total heat produced by NG is 6236731 TJ = 1683 TWh

    initial_production = 561  # https://www.iea.org/data-and-statistics/data-tools/energy-statistics-data-browser?country=WORLD&fuel=Electricity%20and%20heat&indicator=HeatGenByFuel
    # https://www.google.com/search?q=TJ+to+TWh&rlz=1C1UEAD_enIN1000IN1000&oq=TJ+to+TWh&aqs=chrome..69i57.35591j0j7&sourceid=chrome&ie=UTF-8

    # Renewable Methane Association [online]
    flux_input_dict = {'land_rate': 20000, 'land_rate_unit': '$/Gha', }
    DESC_IN = {'techno_infos_dict': {'type': 'dict', 'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               
                      'flux_input_dict': {'type': 'dict', 'default': flux_input_dict, 'unit': 'defined in dict'},
               }
    DESC_IN.update(HighHeatTechnoDiscipline.DESC_IN)
    # -- add specific techno outputs to this
    DESC_OUT = HighHeatTechnoDiscipline.DESC_OUT

    def init_execution(self):
        self.techno_model = NaturalGasBoilerHighHeat(self.techno_name)


