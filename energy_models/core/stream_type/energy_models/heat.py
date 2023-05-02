
from energy_models.core.techno_type.techno_type import TechnoType


class LowTemperatureHeat(TechnoType):
    name = 'heat.lowheat'
    short_name = 'lowheat'
    default_techno_list = ['NaturalGas']
    data_energy_dict = {'maturity': 5,
                        'density': 100,
                        'Highest_Temp': 100,
                        'Temp_unit': 'c',
                        'COP': 3.5,
                        'Lowest_Temp': 400,
                        'CO2_per_use': 1.91,
                        'CO2_per_use_unit': 'kg/kg',
                        'density_unit': 'kg/m^3',
                        'molar_mass': 46.069,
                        'molar_mass_unit': 'g/mol',
                        'viscosity': 1.056E-6,
                        'viscosity_unit': 'mm2/s',
                        'cetane_number': 54.0,
                        'lower_heating_value': 26.7,
                        'lower_heating_value_unit': 'MJ/kg',
                        'higher_heating_value': 29.7,
                        'higher_heating_value_unit': 'MJ/kg',
                        'calorific_value': 7.42,
                        'calorific_value_unit': 'kWh/kg',
                        'high_calorific_value': 8.25,
                        'high_calorific_value_unit': 'kWh/kg'
                        }


class MediumTemperatureHeat(TechnoType):
    name = 'heat.mediumheat'
    short_name = 'mediumheat'
    default_techno_list = ['NaturalGas']
    data_energy_dict = {'maturity': 5,
                        'Highest_Temp': 400,
                        'Lowest_Temp': 100,
                        'Temp_unit': 'c',
                        'COP': 3.5,
                        'density': 100,
                        'CO2_per_use': 1.91,
                        'CO2_per_use_unit': 'kg/kg',
                        'density_unit': 'kg/m^3',
                        'molar_mass': 46.069,
                        'molar_mass_unit': 'g/mol',
                        'viscosity': 1.056E-6,
                        'viscosity_unit': 'mm2/s',
                        'cetane_number': 54.0,
                        'lower_heating_value': 26.7,
                        'lower_heating_value_unit': 'MJ/kg',
                        'higher_heating_value': 29.7,
                        'higher_heating_value_unit': 'MJ/kg',
                        'calorific_value': 7.42,
                        'calorific_value_unit': 'kWh/kg',
                        'high_calorific_value': 8.25,
                        'high_calorific_value_unit': 'kWh/kg'
                        }


class HighTemperatureHeat(TechnoType):
    name = 'heat.highheat'
    short_name = 'highheat'
    default_techno_list = ['NaturalGas']
    data_energy_dict = {'maturity': 5,
                        'density': 100,
                        'Lowest_Temp': 400,
                        'Temp_unit': 'c',
                        'COP': 3.5,
                        'CO2_per_use': 1.91,
                        'CO2_per_use_unit': 'kg/kg',
                        'density_unit': 'kg/m^3',
                        'molar_mass': 46.069,
                        'molar_mass_unit': 'g/mol',
                        'viscosity': 1.056E-6,
                        'viscosity_unit': 'mm2/s',
                        'cetane_number': 54.0,
                        'lower_heating_value': 26.7,
                        'lower_heating_value_unit': 'MJ/kg',
                        'higher_heating_value': 29.7,
                        'higher_heating_value_unit': 'MJ/kg',
                        'calorific_value': 7.42,
                        'calorific_value_unit': 'kWh/kg',
                        'high_calorific_value': 8.25,
                        'high_calorific_value_unit': 'kWh/kg'
                        }
