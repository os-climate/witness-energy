
import pandas as pd
import numpy as np
from energy_models.core.techno_type.disciplines.heat_techno_disc import HighHeatTechnoDiscipline
from energy_models.core.stream_type.energy_models.heat import HighTemperatureHeat
from energy_models.models.heat.high.natural_gas.natural_gas import NaturalGasHighHeat


class HighTemperatureHeatDiscipline(HighHeatTechnoDiscipline):

    # ontology information
    _ontology_data = {
        'label': 'Natural Gas Model',
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
    techno_name = 'NaturalGas'
    energy_name = HighTemperatureHeat.name

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

        'Capex_init': 199.8,
        'Capex_init_unit': '$/kW',
        'Opex_init': 10.565,
        'Opex_init_unit': '$/kW',
        'lifetime': lifetime,
        'lifetime_unit': 'years',
        'construction_delay': construction_delay,
        'construction_delay_unit': 'years',
        'efficiency': 0.8,    # consumptions and productions already have efficiency included
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
        'methane_demand': 4.40,              #https://www.google.com/search?q=How+much+natural+gas+is+required+to+produce+1+kWh+of+heat&rlz=1C1UEAD_enIN1000IN1000&biw=1280&bih=601&sxsrf=APwXEddkE5qRhRRbGSHtQirxZW_RtyyzWw%3A1683733882525&ei=er1bZIrJH8yYseMPjN-D0AQ&ved=0ahUKEwiK7tq_jev-AhVMTGwGHYzvAEoQ4dUDCA8&uact=5&oq=How+much+natural+gas+is+required+to+produce+1+kWh+of+heat&gs_lcp=Cgxnd3Mtd2l6LXNlcnAQA0oECEEYAFAAWABgAGgAcAF4AIABAIgBAJIBAJgBAKABAQ&sclient=gws-wiz-serp
                                             #https://www.kylesconverter.com/energy,-work,-and-heat/cubic-feet-of-natural-gas-to-kilowatt--hours
        'methane_demand_unit': 'kWh/kWh',
        'density': 0.83,                       #https://cdn.intechopen.com/pdfs/11474/InTech-Environmental_technology_assessment_of_natural_gas_compared_to_biogas.pdf
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
    # production in 2020: 51000 million gallons
    # in TWh
    # initial production i.e. total heat produced by NG is 55 MJ/kg = 1.53 e8 TWh =>153000000 TWh/kg = 153000 TWh

    initial_production = 51000        # https://world-nuclear.org/information-library/facts-and-figures/heat-values-of-various-fuels.aspx
                                      # https://www.google.com/search?q=how+much+heat+produced+by+natural+gas&rlz=1C1UEAD_enIN1000IN1000&sxsrf=APwXEde4P7ReCphsNRB9zNWCtf5KizY1Wg%3A1684144512917&ei=gAFiZKjMN5_i4-EPvK6LmAI&ved=0ahUKEwiojMWbh_f-AhUf8TgGHTzXAiMQ4dUDCA8&uact=5&oq=how+much+heat+produced+by+natural+gas&gs_lcp=Cgxnd3Mtd2l6LXNlcnAQAzIFCAAQogQyBQgAEKIEMgUIABCiBDIFCAAQogQ6CggAEEcQ1gQQsAM6CgghEKABEMMEEAo6CAghEKABEMMESgQIQRgAULsIWPF0YOq0AWgBcAB4AIABnAGIAb0NkgEEMS4xNJgBAKABAcgBCMABAQ&sclient=gws-wiz-serp


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
    DESC_IN.update(HighHeatTechnoDiscipline.DESC_IN)
    # -- add specific techno outputs to this
    DESC_OUT = HighHeatTechnoDiscipline.DESC_OUT

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = NaturalGasHighHeat(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
