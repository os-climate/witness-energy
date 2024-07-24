'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/14-2023/11/16 Copyright 2023 Capgemini

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

import numpy as np
import pandas as pd

from energy_models.core.stream_type.energy_models.ethanol import Ethanol
from energy_models.core.techno_type.disciplines.ethanol_techno_disc import (
    EthanolTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.ethanol.biomass_fermentation.biomass_fermentation import (
    BiomassFermentation,
)


class BiomassFermentationDiscipline(EthanolTechnoDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Biomass Fermentation Model',
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
    techno_name = GlossaryEnergy.BiomassFermentation
    energy_name = Ethanol.name

    # Conversions
    pound_to_kg = 0.45359237
    gallon_to_m3 = 0.00378541
    liter_per_gallon = 3.78541178

    # energy data
    ethanol_density = Ethanol.data_energy_dict['density']
    ethanol_calorific_value = Ethanol.data_energy_dict['calorific_value']

    # Ethanol Producer [Online]
    # http://www.ethanolproducer.com/articles/2005/time-testing#:~:text=Most%20experts%20suggest%20dry%2Dmill,of%20%22useful%22%20life%20expectancy.
    lifetime = 45  # years
    # Economic and Technical Analysis of Ethanol Dry Milling: Model Description.
    # Rhys T.Dale and Wallace E.Tyner Staff Paper
    # 06-04 April 2006
    # Agricultural Economics Department Purdue University
    construction_delay = 2  # years

    techno_infos_dict_default = {

        # Gubicza K, Nieves IU, Sagues WJ, Barta Z, Shanmugam KT, Ingram LO.Techno - economic analysis of ethanol
        # production from sugarcane bagasse using a Liquefaction plus Simultaneous Saccharification and co -
        # Fermentation process.Bioresour Technol. 2016
        # from table 6: capex 1.95$/liter
        'Capex_init': 1.95 * 1000 / 789 / 7.42,
        'Capex_init_unit': '$/kWh',
        'Opex_percentage': 0.02,
        'lifetime': lifetime,
        'lifetime_unit': GlossaryEnergy.Years,
        GlossaryEnergy.ConstructionDelay: construction_delay,
        'construction_delay_unit': GlossaryEnergy.Years,
        'efficiency': 1,  # consumptions and productions already have efficiency included
        'CO2_from_production': 0.0,
        'CO2_from_production_unit': 'kg/kg',
        'elec_demand': 0.70 / gallon_to_m3,
        'elec_demand_unit': 'kWh/m3',
        'water_demand': 3.5,
        'water_demand_unit': 'm3/m3',
        'biomass_dry_demand': 56 * pound_to_kg / (2.9 * gallon_to_m3),
        'biomass_dry_demand_unit': 'kg/m3',
        'co2_captured__production': 17 * pound_to_kg / (2.9 * gallon_to_m3),
        'co2_captured__production_unit': 'kg/m3',
        'maturity': 5,
        'learning_rate': 0.1,
        'full_load_hours': 8760.0,
        'WACC': 0.075,
        'techno_evo_eff': 'no',
    }

    # Renewable Fuels Association [online]
    # https://ethanolrfa.org/markets-and-statistics/annual-ethanol-production
    # production in 2019: 29330 million gallons
    # in TWh
    initial_production = 29330 * 1e6 * \
                         (gallon_to_m3 * ethanol_density * ethanol_calorific_value) * 1e-9

    distrib = [40.0, 40.0, 20.0, 20.0, 20.0, 12.0, 12.0, 12.0, 12.0, 12.0,
               8.0, 8.0, 8.0, 8.0, 8.0, 5.0, 5.0, 5.0, 5.0, 5.0,
               3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0,
               2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0,
               1.0, 1.0, 1.0, 1.0,
               ]

    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': 100 / sum(distrib) * np.array(distrib)})  # to review

    # Renewable Fuels Association [online]
    # https://ethanolrfa.org/markets-and-statistics/annual-ethanol-production
    DESC_IN = {'techno_infos_dict': {'type': 'dict', 'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'age': ('float', None, True),
                                                                'distrib': ('float', None, True)}},
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},
               }
    DESC_IN.update(EthanolTechnoDiscipline.DESC_IN)
    # -- add specific techno outputs to this
    DESC_OUT = EthanolTechnoDiscipline.DESC_OUT

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = BiomassFermentation(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
