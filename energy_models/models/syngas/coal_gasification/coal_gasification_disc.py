'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/14-2023/11/07 Copyright 2023 Capgemini

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

import pandas as pd
import numpy as np

from climateeconomics.glossarycore import GlossaryCore
from energy_models.core.techno_type.disciplines.syngas_techno_disc import SyngasTechnoDiscipline
from energy_models.models.syngas.coal_gasification.coal_gasification import CoalGasification
from energy_models.core.stream_type.energy_models.syngas import compute_calorific_value


class CoalGasificationDiscipline(SyngasTechnoDiscipline):

    # ontology information
    _ontology_data = {
        'label': 'Coal Gasification Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-burn fa-fw',
        'version': '',
    }

    techno_name = 'CoalGasification'
    lifetime = 20
    construction_delay = 4  # years
    techno_infos_dict_default = {'maturity': 5,
                                 'Opex_percentage': 0.15,
                                 # Source for CO2_from_production: IEA 2022, IEA ETSAP 2010
                                 # https://iea-etsap.org/E-TechDS/PDF/P05-Coal-gasification-GS-gct-AD_gs.pdf
                                 # License: CC BY 4.0.
                                 'CO2_from_production': 1.94,  # ETSAP IEA indicates 50kT CO2 /PJ syngas
                                 'CO2_from_production_unit': 'kg/kg',
                                 # IPCC report Chap4 2019  https://www.ipcc-nggip.iges.or.jp/public/2019rf/pdf/2_Volume2/19R_V2_4_Ch04_Fugitive_Emissions.pdf
                                 # 6.1 kg/TJ
                                 'CH4_emission_factor': 6.1e-9 / 0.277e-3,
                                 'CH4_emission_factor_unit': 'Mt/TWh',
                                 'elec_demand': 0,
                                 'elec_demand_unit': 'kWh/kWh',
                                 'fuel_demand': 1.19,
                                 'fuel_demand_unit': 'kWh/kWh',
                                 'WACC': 0.07,
                                 'learning_rate': 0.2,
                                 'lifetime': lifetime,
                                 'lifetime_unit': GlossaryCore.Years,
                                 'Capex_init': 0.05,
                                 'Capex_init_unit': '$/kWh',
                                 'euro_dollar': 1.12,
                                 'efficiency': 1.0,
                                 'techno_evo_eff': 'no',
                                 'construction_delay': construction_delay}
    # We do not invest on coal gasification yet
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), GlossaryCore.InvestValue: [2.636, 2.636, 2.636, 2.636]})

    syngas_ratio = CoalGasification.syngas_COH2_ratio

    # From Future of hydrogen : Around 70 Mt of dedicated hydrogen are produced today, 76% from natural gas and
    # almost all the rest (23%) from coal.
    # 70 MT of hydrogen then 70*33.3 TWh of hydrogen we need approximately
    # 1.639 kWh of syngas to produce one of hydrogen (see WGS results)
    #initial_production = 70.0 * 33.3 * 1.639 * 0.23

    # IEA says 3333 TWh of coal is transformed into syngas (other
    # transformation). Source: IEA 2022, Data Tables, https://www.iea.org/data-and-statistics/data-tables?country=WORLD&energy=Balances&year=2019, License: CC BY 4.0.
    # It contains application to hydrogen (WGS), oil products
    # (FT) and Direct Reduced Iron in industry
    # We need 1.19 kWH of coal for 1 KWh of syngas then:
    initial_production = (3333. + 264.72) / 1.19
    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': np.array([3.317804973859207, 6.975128305927281, 4.333201737255864,
                                                                  3.2499013031833868, 1.5096723255070685, 1.7575996841282722,
                                                                  4.208448479896288, 2.7398341887870643, 5.228582707722979,
                                                                  10.057639166085064, 0.0, 2.313462297352473, 6.2755625737595535,
                                                                  5.609159099363739, 6.3782076592711885, 8.704303197679629,
                                                                  6.1950256610618135, 3.7836557445596464, 1.7560205289962763,
                                                                  ]) + 0.82141})
    FLUE_GAS_RATIO = np.array([0.13])

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {GlossaryCore.Years: ('float', None, True),
                                                                'age': ('float', None, True),
                                                                'distrib': ('float', None, True)}
                                       },
               GlossaryCore.InvestmentBeforeYearStartValue: {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int',  [-20, -1], False),
                                                                 GlossaryCore.InvestValue: ('float',  None, True)},
                                        'dataframe_edition_locked': False}}

    DESC_IN.update(SyngasTechnoDiscipline.DESC_IN)

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = CoalGasification(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
