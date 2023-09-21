
import pandas as pd
import numpy as np
from energy_models.core.techno_type.disciplines.heat_techno_disc import MediumHeatTechnoDiscipline
from energy_models.core.stream_type.energy_models.heat import mediumtemperatureheat
from energy_models.models.heat.medium.chpmediumheat.chpmediumheat import CHPMediumHeat


class CHPMediumHeatDiscipline(MediumHeatTechnoDiscipline):

    # ontology information
    _ontology_data = {
        'label': 'CHP Model',
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
    techno_name = 'CHPMediumHeat'
    energy_name = mediumtemperatureheat.name

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
        'Capex_init': 2.145,              #file:///C:/Users/KAJBORKA/Downloads/PriyankaChintada_final_thesis%20(5).pdf
        'Capex_init_unit': '$/kWh',       #https://www.google.com/search?q=eur+to+dollar+conversion&rlz=1C1UEAD_enIN1000IN1000&oq=eur+to+d&aqs=chrome.3.69i57j0i131i433i512l2j0i20i263i512l2j0i10i512j0i512l4.7800j1j7&sourceid=chrome&ie=UTF-8
        'lifetime': lifetime,
        'lifetime_unit': 'years',
        'construction_delay': construction_delay,
        'construction_delay_unit': 'years',
        'efficiency': 0.52,                # consumptions and productions already have efficiency included
                                           #https://www.epa.gov/chp/chp-benefits#:~:text=By%20recovering%20and%20using%20heat,of%2065%20to%2080%20percent.
        'chp_calorific_val': 22000,        #https://ec.europa.eu/eurostat/documents/38154/42195/Final_CHP_reporting_instructions_reference_year_2016_onwards_30052017.pdf/f114b673-aef3-499b-bf38-f58998b40fe6
        'chp_calorific_val_unit': 'kJ/kg',
        'elec_demand': 1,                  #https://www.carboncommentary.com/blog/2007/10/01/domestic-combined-heat-and-power
        'elec_demand_unit': 'KWh',
        'methane_demand': 2.65,            #https://www.nfuenergy.co.uk/news/combined-heat-and-power-could-reduce-your-electricity-costs-half
        'methane_demand_unit': 'kWh/kWh',
        'co2_captured__production': 0.11,  # kg/kWh
                                           # https://odr.chalmers.se/server/api/core/bitstreams/65470fdd-f00a-4607-8d0f-59152df05ea8/content
                                           # https://www.unitconverters.net/energy/megajoule-to-kilowatt-hour.htm
        'co2_captured__production_unit': 'kg/kWh',
        'Opex_percentage': 0.2,            #page 28  #https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/961322/Part_5_CHP_Finance_BEIS_v03.pdf
                                           # Fixed 1.9 and recurrent 0.5 %
                                           # Demystifying-the-Costs-of-Electricity-Generation-Technologies, average
        'WACC': 0.058,  # Weighted averaged cost of capital / ATB NREL 2020
        'learning_rate': 0.00,  # Cost development of low carbon energy technologies
        'full_load_hours': 8760.0,  # Full year hours
        # Demystifying-the-Costs-of-Electricity-Generation-Technologies, average
        'capacity_factor': 0.90,
        'techno_evo_eff': 'no'
    }

    # Renewable Association [online]
    # production in 2021: 2608 million gallons
    # in TWh
    # initial production i.e. total heat produced by CHP = 117 TWh    # 117/3 = 39 TWh

    initial_production = 39  # https://www.umweltbundesamt.de/en/data/environmental-indicators/indicator-combined-heat-power-chp#at-a-glance

    initial_production = ((117/0.52)/3)*(1-0.52)  # https://www.statista.com/statistics/678192/chp-electricity-generation-germany/

    distrib = [40.0, 40.0, 20.0, 20.0, 20.0, 12.0, 12.0, 12.0, 12.0, 12.0,
                   8.0, 8.0, 8.0, 8.0, 8.0, 5.0, 5.0, 5.0, 5.0, 5.0,
                   3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0,
                   2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0,
                   1.0, 1.0, 1.0, 1.0,
                   ]

    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': 100 / sum(distrib) * np.array(distrib)})

    # Renewable Methane Association [online]
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), 'invest': 2.145/(16 * 8760) * np.array([0, 0.2608])})

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
                                        'dataframe_edition_locked': False}}
    DESC_IN.update(MediumHeatTechnoDiscipline.DESC_IN)
    # -- add specific techno outputs to this
    DESC_OUT = MediumHeatTechnoDiscipline.DESC_OUT

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = CHPMediumHeat(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
