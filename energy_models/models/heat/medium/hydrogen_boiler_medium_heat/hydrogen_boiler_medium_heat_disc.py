
import pandas as pd
import numpy as np
from energy_models.core.techno_type.disciplines.heat_techno_disc import MediumHeatTechnoDiscipline
from energy_models.core.stream_type.energy_models.heat import mediumtemperatureheat
from energy_models.models.heat.medium.hydrogen_boiler_medium_heat.hydrogen_boiler_medium_heat import HydrogenBoilerMediumHeat
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart

class HydrogenBoilerMediumHeatDiscipline(MediumHeatTechnoDiscipline):

    # ontology information

    _ontology_data = {
        'label': 'Hydrogen Boiler Model',
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
    techno_name = 'HydrogenBoilerMediumHeat'
    energy_name = mediumtemperatureheat.name

    # Conversions
    pound_to_kg = 0.45359237
    gallon_to_m3 = 0.00378541
    liter_per_gallon = 3.78541178

    # Heat Producer [Online]
    # https://heatable.co.uk/boiler-advice/hydrogen-boilers
    lifetime = 15          # years
    # Economic and Technical Analysis of Heat Dry Milling: Model Description.
    # Rhys T.Dale and Wallace E.Tyner Staff Paper
    # Agricultural Economics Department Purdue University
    construction_delay = 2  # years

    techno_infos_dict_default = {

        'Capex_init': 250,      #https://iea.blob.core.windows.net/assets/2ceb17b8-474f-4154-aab5-4d898f735c17/IEAGHRassumptions_final.pdf
        'Capex_init_unit': '$/kW',
        'lifetime': lifetime,
        'lifetime_unit': 'years',
        'construction_delay': construction_delay,
        'construction_delay_unit': 'years',
        'efficiency': 0.95,     # https://iea.blob.core.windows.net/assets/2ceb17b8-474f-4154-aab5-4d898f735c17/IEAGHRassumptions_final.pdf
        'hydrogen_calorific_val': 150000, #https://www.google.com/search?q=hydrogen+calorific+value+kj%2Fkg&rlz=1C1UEAD_enIN1000IN1000&oq=hydrogen+colorific+value+&gs_lcrp=EgZjaHJvbWUqCQgCEAAYDRiABDIGCAAQRRg5MgkIARAAGA0YgAQyCQgCEAAYDRiABDIJCAMQABgNGIAEMgkIBBAAGA0YgAQyCQgFEAAYDRiABDIJCAYQABgNGIAEMgkIBxAAGA0YgAQyCAgIEAAYFhgeMgoICRAAGA8YFhge0gEJMTI3MDhqMGo3qAIAsAIA&sourceid=chrome&ie=UTF-8
        'hydrogen_calorific_val_unit': 'kJ/kg',
        'hydrogen_demand': 1.47,   #https://www.google.com/search?q=hydrogen+boiler,+hydrogen+required+to+produce+1kwh+of+heat&source=lmns&bih=585&biw=925&rlz=1C1UEAD_enIN1000IN1000&hl=en&sa=X&ved=2ahUKEwiE14bTn5OCAxWN2jgGHfZqCYYQ_AUoAHoECAEQAA
        'hydrogen_demand_unit': 'kWh/kWh',
        'co2_captured__production': 0.332, # page number: 677   # https://pdf.sciencedirectassets.com/277910/1-s2.0-S1876610211X00036/1-s2.0-S1876610211001068/main.pdf?X-Amz-Security-Token=IQoJb3JpZ2luX2VjEAUaCXVzLWVhc3QtMSJIMEYCIQCUi66H3VrBTb6xyGLn18jpCIItw65A6P1%2FkW%2FjVrE7zAIhAK0ywvPnEvVgX1fbRA8OcbqHqL0TYWrGtQ5PUD8eyROZKrMFCC4QBRoMMDU5MDAzNTQ2ODY1IgzkIfP0pfgKA52ndc0qkAUzGiakLN40DPDwey%2FU%2FfWQ1qBWce%2Ba%2BkdL4d7oxyhY4IdiOH%2BA2c4gLSLfvSOQwVL8z19cLYOOQ36D3v%2FVyj62GQdbBqHOerFwcg6wJ4GCidql%2B9mygUP9Llq5rEWZn4%2F5bUDCQnDHdOqOrTKnFcNpjYYBkiGd%2FD0e3cF%2Bg%2BIg9jWPZc4HE6W3EwJDZz00hzQ%2FOh4%2FPYuBu6FfsAV1wsj%2BE6LNpq%2FSkx0D1K3CVRKByrnbpjBngzEHQKCpLS1gRMezfJtOovZu5nQQj7Ly88QkGbI8DtwVwxI%2BlG2HzI2%2B%2BggZ37crUByCCbJ8Fe1WKQC7%2BEf8hc1t3inUBO7c957aCB%2BkMGBQqWCjhm3J2yFesHiT%2BLccZkgHFBrA6UZLxpnBmwSM%2F6Iz7%2BvT%2FicUw1K0d6amvrdh4SIMHkg%2Bb3UiqWe31FsMGFh%2BMbz8GfGV%2FKqmKSx%2FBrxG4DbF%2Bhh4lwigjrKdqM3doWz8cnMQgO3hYSBWpSTlbJ9hscZcFJVv7sK0p84KMNKjry6DYZo9jwpGlHhFcG%2FU2wfatdAczaWfjhyH46Vh2p%2FXQeJaTHsnzcuKQu%2BWscUFf1iPc3XnNOFLThKAQZ2Xm6zJTIO6veNBUs48yg2KiCRLwYjHfKfl9zpx2dZrD4VaqlBI6eAnDRXqOjpp3hillYc3u9%2BF1UxIIRl12oHYCwEK0ZEwWyJNBv00YuAJcgsBfdo8%2BM3zudWft0KdxXBuEPn8RF6xPtTJFv89vM5NflsTg6%2BejzBjL6XLNwA854IOnZ3eyDvCWwpcaUkdBm%2F8jtTXVJTpwAll85FnVQg5xGd6RV%2BSMwLAgLDMnG%2FvHH%2BdlU7sxekyqVeFA88BrmTJRUlBozqJbVcITzDyytmpBjqwAXB5dkkY1eZbEeSNj67F9GfFLb7hbT7tqYWZ5Szot4u0K5IQH393LiZqbg1O9uaGvtAskvMZIfu%2FdS5mdt%2FYPgf4hpYazTo5dSAI67fCNvBQyj6UeGVKVH5U41crl5GSALufhDs6yf9TsEXMNW6DgU7DUGw7vnscz79S93FnxJhonhood4LIHefhZFLd%2BgSJ7IaKvSxkKF4UkBA%2F8EQEAaIfYk89gJu29YqCQVy36mNn&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20231023T131231Z&X-Amz-SignedHeaders=host&X-Amz-Expires=300&X-Amz-Credential=ASIAQ3PHCVTYSWNP35JB%2F20231023%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Signature=0cb9cbc9090430e18f013f76a7ca55a07307408b9c2793ee047c2331082b80c1&hash=d533087c739f70b2638246e53a35b75f3f322b72886f09435b3b3a39371e9e77&host=68042c943591013ac2b2430a89b270f6af2c76d8dfd086a07176afe7c76c2c61&pii=S1876610211001068&tid=spdf-aea0f009-0421-4850-ac55-309a65cf06c0&sid=bf477a3b6856d342ee2be2c696267d6598edgxrqb&type=client&tsoh=d3d3LnNjaWVuY2VkaXJlY3QuY29t&ua=13085c5407045402520208&rr=81aa3b6bfdbb3c0c&cc=in
        'co2_captured__production_unit': 'kg/kWh',
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
    # production in 2021: 541.6666667/3 = 180.55 million gallons  #https://www.sciencedirect.com/science/article/pii/S0360319914031383
    # in TWh
    # initial production i.e. total heat produced by Hydrogen Boiler is 13 million metric tons(Mt)= 13000000 Mt = 13000000000 Kg * cal_value(kJ/kg) = 1.95E+15 KJ = 541.6666667 TWh

    initial_production = 180.55       # https://www2.deloitte.com/content/dam/Deloitte/us/Documents/Advisory/us-advisory-assessment-of-green-hydrogen-for-industrial-heat.pdf
                                      # page 17
    distrib = [40.0, 40.0, 20.0, 20.0, 20.0, 12.0, 12.0, 12.0, 12.0, 12.0,
               8.0, 8.0, 8.0, 8.0,
               ]

    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': 100 / sum(distrib) * np.array(distrib)})

    # Renewable Methane Association [online]
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), 'invest': 250/(16 * 8760) * np.array([0, 180.55])})
    DESC_IN = {'techno_infos_dict': {'type': 'dict', 'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'years': ('int', [1900, 2100], False),
                                                                'age': ('float', None, True),
                                                                'distrib': ('float', None, True),
                                                                }
                                       },
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},
               'invest_before_ystart': {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int',  [-20, -1], False),
                                                                 'invest': ('float',  None, True)},
                                        'dataframe_edition_locked': False},
               }
    DESC_IN.update(MediumHeatTechnoDiscipline.DESC_IN)
    # -- add specific techno outputs to this
    DESC_OUT = MediumHeatTechnoDiscipline.DESC_OUT

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = HydrogenBoilerMediumHeat(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)

    def setup_sos_disciplines(self):
        super().setup_sos_disciplines()

    def run(self):
        '''
        Run for all energy disciplines
        '''

        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model.configure_parameters_update(inputs_dict)
        MediumHeatTechnoDiscipline.run(self)
