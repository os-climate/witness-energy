'''
mode: python; py-indent-offset: 4; tab-width: 8; coding: utf-8
Copyright (c) 2020 Airbus SAS.
All rights reserved.
'''
import copy

import pandas as pd
import numpy as np

from energy_models.core.techno_type.disciplines.gaseous_hydrogen_techno_disc import GaseousHydrogenTechnoDiscipline
from energy_models.models.gaseous_hydrogen.electrolysis.awe.electrolysis_awe import ElectrolysisAWE


class ElectrolysisAWEDiscipline(GaseousHydrogenTechnoDiscipline):
    """
    Electrolysis AWE Discipline
    """

    # ontology information
    _ontology_data = {
        'label': 'Hydrogen Electrolysis AWE Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-hospital-symbol fa-fw',
        'version': '',
    }
    techno_name = 'Electrolysis.AWE'
    construction_delay = 1  # year
    # David, M., Ocampo-Martinez, C. and Sanchez-Pena, R., 2019.
    # Advances in alkaline water electrolyzers: A review.
    # Journal of Energy Storage, 23, pp.392-403.
    lifetime = 25  # Around 20 and 30 years
    techno_infos_dict_default = {'maturity': 5,
                                 'Opex_percentage': 0.05,
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 'WACC': 0.05,
                                 'learning_rate': 0.05,
                                 'maximum_learning_capex_ratio': 200 / 581.25,
                                 'lifetime': lifetime,
                                 'lifetime_unit': 'years',
                                 'stack_lifetime': 100000,
                                 'stack_lifetime_unit': 'hours',
                                 'Capex_init': 581.25,  # for a power input of 2MW, decreases for 10 MW
                                 'Capex_init_unit': 'euro/kW',
                                 'euro_dollar': 1.114,
                                 'full_load_hours': 8000,
                                 'techno_evo_eff': 'yes',
                                 'techno_evo_time': 10,
                                 'efficiency evolution slope': 0.5,
                                 # electric efficiency that we will use to
                                 # compute elec needs
                                 'efficiency': 0.60,
                                 'efficiency_max': 0.70,
                                 'construction_delay': construction_delay}
    # see doc
    initial_production = 1.6 - 0.4
    # Industrial plants started to emerge around 2015
    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': [50, 15, 15, 15, 5] + [0.0] * (lifetime - 6)
                                             })

    # We assume no investments
    invest_before_year_start = pd.DataFrame({'past years': np.arange(-construction_delay, 0),
                                             'invest': [0.0]})

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default},
               'initial_production': {'type': 'float',
                                      'unit': 'TWh', 'default': initial_production},
               'initial_age_distrib': {'type': 'dataframe',
                                       'unit': '%', 'default': initial_age_distribution},
               'invest_before_ystart': {'type': 'dataframe',
                                        'unit': 'G$',
                                        'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int',  [-20, -1], False),
                                                                 'invest': ('float',  None, True)},
                                        'dataframe_edition_locked': False}}
    DESC_IN.update(GaseousHydrogenTechnoDiscipline.DESC_IN)

    # -- add specific techno outputs to this
    DESC_OUT = GaseousHydrogenTechnoDiscipline.DESC_OUT

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = ElectrolysisAWE(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
