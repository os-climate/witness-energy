
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

    # energy data
    #heat_density = HighTemperatureHeat.data_energy_dict['density']
    #heat_calorific_value = HighTemperatureHeat.data_energy_dict['calorific_value']

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
        # 'area': 3000,
        # 'area_unit': 'm2',
        # 'volume': 10000,
        # 'volume_unit': 'm3',
        # 'water_demand': 3.5,
        # 'water_demand_unit': 'm3/m3',
        # 'water_flow_rate':  8000,
        # 'water_flow_rate_unit': 'kg/h',
        # 'water_wetness_fraction': 0.5,
        # 'air_flow_rate': 1000,
        # 'air_flow_rate_unit': 'kg/h',
        # 'air_temp': 200,
        # 'air_temp_unit': 'c',
        # 'excess_air_ratio': 0.11,
        # 'steam_flow_rate': 8000,
        # 'steam_flow_rate_unit': 'kg/h',
        # 'steam_flow_temp': 180,
        # 'steam_flow_temp_unit': 'c',
        # 'steam_pressure': 980665,
        # 'steam_pressure_unit': 'Pa',
        'methane_demand': 92,                   #https://www.iea.org/reports/global-methane-tracker-2022/overview
        'methane_demand_unit': 'kWh/kWh',
        # 'elec_demand': 0.70 / gallon_to_m3,
        # 'elec_demand_unit': 'kWh/m3',
        'density': 0.83,                         #https://cdn.intechopen.com/pdfs/11474/InTech-Environmental_technology_assessment_of_natural_gas_compared_to_biogas.pdf
        #'maturity': 0,
        'CO2_from_production': 0.21,        #kg per kWh of heat
        'unit' : 'kg/kwh',
                             #https://www.google.com/search?q=co2+captured+production+to+produce+heat+in+natural+gas+boiler&rlz=1C1UEAD_enIN1000IN1000&oq=co2+captured+production+to+produce+heat+in+natural+gas+boiler&aqs=chrome..69i57.37619j0j7&sourceid=chrome&ie=UTF-8
        'calorific_value': 15.27,                #https://www.google.com/search?q=What+is+the+calorific+value+of+methane+to+burn+kWh+in+natural+gas+boiler&rlz=1C1UEAD_enIN1000IN1000&biw=1280&bih=601&sxsrf=APwXEdeVw3daWU9daM6lZi591JsDcc5TWQ%3A1683144074088&ei=ir1SZIaFBae84-EPkOWS8AI&ved=0ahUKEwiG8pCl-Nn-AhUn3jgGHZCyBC4Q4dUDCA8&uact=5&oq=What+is+the+calorific+value+of+methane+to+burn+kWh+in+natural+gas+boiler&gs_lcp=Cgxnd3Mtd2l6LXNlcnAQA0oECEEYAFAAWABgAGgAcAB4AIABAIgBAJIBAJgBAKABAQ&sclient=gws-wiz-serp
        'calorific_value_unit': 'kWh/kg',        #https://www.google.com/search?q=mj+to+kwh&rlz=1C1UEAD_enIN1000IN1000&oq=MJ+to+&aqs=chrome.1.69i57j0i20i131i263i433i512j0i67i650j0i67i131i433i650j0i67i650l5j0i512.5384j0j7&sourceid=chrome&ie=UTF-8
                                 'Opex_percentage': 0.024,
                                 # Fixed 1.9 and recurrent 0.5 %
                                 # Demystifying-the-Costs-of-Electricity-Generation-Technologies, average
                                 'WACC': 0.058,  # Weighted averaged cost of capital / ATB NREL 2020
                                 'learning_rate': 0.00,  # Cost development of low carbon energy technologies
                                 'full_load_hours': 8760.0,  # Full year hours
                                 # Demystifying-the-Costs-of-Electricity-Generation-Technologies, average
                                 'capacity_factor': 0.90,
                                 'techno_evo_eff': 'no',
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/k,g'

    }

    # Renewable Fuels Association [online]
    # https://heatrfa.org/markets-and-statistics/annual-heat-production
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

    # Renewable Fuels Association [online]
    # https://heatrfa.org/markets-and-statistics/annual-heat-production
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
