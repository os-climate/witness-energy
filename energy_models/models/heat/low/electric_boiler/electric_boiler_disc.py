
import pandas as pd
import numpy as np
from energy_models.core.techno_type.disciplines.heat_techno_disc import LowHeatTechnoDiscipline
from energy_models.core.stream_type.energy_models.heat import LowTemperatureHeat
from energy_models.models.heat.low.electric_boiler.electric_boiler import ElectricBoilerHeat


class LowTemperatureHeatDiscipline(LowHeatTechnoDiscipline):

    # ontology information
    _ontology_data = {
        'label': 'Electric Boiler Model',
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
    techno_name = 'ElectricBoiler'
    energy_name = LowTemperatureHeat.name

    # Conversions
    pound_to_kg = 0.45359237
    gallon_to_m3 = 0.00378541
    liter_per_gallon = 3.78541178

    # Heat Producer [Online]
    # https://www.serviceone.com/blog/article/how-long-does-a-home-boiler-last#:~:text=Estimated%20lifespan,most%20parts%20of%20the%20nation.
    lifetime = 45          # years
    # Economic and Technical Analysis of Heat Dry Milling: Model Description.
    # Rhys T.Dale and Wallace E.Tyner Staff Paper
    # Agricultural Economics Department Purdue University
    construction_delay = 2  # years

    techno_infos_dict_default = {

        'Capex_init': 2000,
        'Capex_init_unit': '$/kW',    # $ per kW of electricity
        'Opex_percentage': 0.15,
        'lifetime': lifetime,
        'lifetime_unit': 'years',
        'construction_delay': construction_delay,
        'construction_delay_unit': 'years',
        'efficiency': 1,    # consumptions and productions already have efficiency included
        'elec_demand': 40,
        'elec_demand_unit': 'kWh/h',
        'water_demand': 1.13,
        'water_demand_unit': 'm3/h',
        'learning_rate': 0.56,
        'full_load_hours': 8760.0,
        'WACC': 0.062,
        'techno_evo_eff': 'no',
    }

    # Renewable Methane Association [online]
    # production in 2019: 29330 million gallons
    # in TWh
    initial_production = 29330

    distrib = [40.0, 40.0, 20.0, 20.0, 20.0, 12.0, 12.0, 12.0, 12.0, 12.0,
               8.0, 8.0, 8.0, 8.0, 8.0, 5.0, 5.0, 5.0, 5.0, 5.0,
               3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0,
               2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0,
               1.0, 1.0, 1.0, 1.0,
               ]

    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': 100 / sum(distrib) * np.array(distrib)})  # to review

    # Renewable Methane Association [online]
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), 'invest': 1.95 * liter_per_gallon * np.array([0, 29.330 - 28.630])})

    DESC_IN = {'techno_infos_dict': {'type': 'dict', 'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution},
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},
               'invest_before_ystart': {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int',  [-20, -1], False),
                                                                 'invest': ('float',  None, True)},
                                        'dataframe_edition_locked': False}}
    DESC_IN.update(LowHeatTechnoDiscipline.DESC_IN)
    # -- add specific techno outputs to this
    DESC_OUT = LowHeatTechnoDiscipline.DESC_OUT

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = ElectricBoilerHeat(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
