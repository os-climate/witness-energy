'''
Copyright 2022 Airbus SAS

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

from energy_models.core.techno_type.disciplines.syngas_techno_disc import SyngasTechnoDiscipline
from energy_models.models.syngas.biomass_gasification.biomass_gasification import BiomassGasification
from energy_models.core.stream_type.energy_models.syngas import compute_calorific_value
from energy_models.core.stream_type.energy_models.liquid_fuel import LiquidFuel
from energy_models.core.stream_type.energy_models.methane import Methane


class BiomassGasificationDiscipline(SyngasTechnoDiscipline):

    # ontology information
    _ontology_data = {
        'label': 'Biomass Gasification Model',
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

    techno_name = 'BiomassGasification'
    # Wang, Y., Li, G., Liu, Z., Cui, P., Zhu, Z. and Yang, S., 2019.
    # Techno-economic analysis of biomass-to-hydrogen process in comparison with coal-to-hydrogen process.
    # Energy, 185, pp.1063-1075.
    # Rosenfeld, D.C., B�hm, H., Lindorfer, J. and Lehner, M., 2020.
    # Scenario analysis of implementing a power-to-gas and biomass gasification system in an integrated steel plant:
    # A techno-economic and environmental study. Renewable energy, 147,
    # pp.1511-1524.
    lifetime = 25  # Wang2019 Rosenfeld2020 says 20
    construction_delay = 3  # years
    techno_infos_dict_default = {'maturity': 5,
                                 'Opex_percentage': 0.015,  # Rosenfeld2020
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 # https://www.ipcc-nggip.iges.or.jp/public/2019rf/pdf/2_Volume2/19R_V2_4_Ch04_Fugitive_Emissions.pdf
                                 # 18.3 kg/TJ
                                 'CH4_emission_factor': 18.3e-9 / 0.277e-3,
                                 'CH4_emission_factor_unit': 'Mt/TWh',
                                 # Wang2019 : 9.932 MW of electricity to
                                 # product 88.841 of syngas
                                 'elec_demand': 9.932 / 88.841,
                                 'elec_demand_unit': 'kWh/kWh',
                                 # Mustafa, A., Calay, R.K. and Mustafa, M.Y., 2017.
                                 # A techno-economic study of a biomass gasification plant for the
                                 # production of transport biofuel for small communities.
                                 # Energy Procedia, 112, pp.529-536.
                                 # 2.4kg syngas/ kgbiomass (Albara2017) => 0.42 tbiomass/tsyngas
                                 # 10.99 tbiomass/tH2 in Wang2019 with
                                 # calorific value of biomass of 19MJ/kg or
                                 # 19*0.28kWh/kg
                                 'biomass_demand': 135.93 / 88.841,
                                 'biomass_demand_unit': 'kWh/kWh',
                                 # Sara, H.R., Enrico, B., Mauro, V. and Vincenzo, N., 2016.
                                 # Techno-economic analysis of hydrogen production using biomass gasification-a small scale power plant study.
                                 # Energy Procedia, 101, pp.806-813.
                                 'WACC': 0.07,  # WACC Saraa2016
                                 'learning_rate': 0.2,
                                 'lifetime': lifetime,  # for now constant in time but should increase with time
                                 'lifetime_unit': 'years',
                                 # Capex in kEuro in Sara2016 we divide by 2
                                 # for the PPS cost reduction aimed in the
                                 # paper
                                 # 370.96 => gasifier
                                 # 270.63  2 => portable purification system
                                 # => gasifier = 73% total capex
                                 #'Capex_init': (370.96 + 270.63 / 2.0) * 1000.0,
                                 #'Capex_init_unit': 'euro',
                                 'Capex_init': 2400.0 * 0.73,  # Rosenfeld 2020 + ratio from Sarra2016
                                 'Capex_init_unit': 'euro/kW',
                                 'full_load_hours': 8760.0,
                                 'euro_dollar': 1.12,  # in Sept2016 date of the paper
                                 # 10.6 ton/year in best scenario for a total
                                 # capex
                                 'available_power': 10600.0,
                                 'available_power_unit': 'kg/year',
                                 'efficiency': 1.0,
                                 'techno_evo_eff': 'no',  # yes or no
                                 # Wang2019 + ratio water + ratio masse syngas
                                 # / masse H2
                                 'kgH20_perkgSyngas': 157.75 / (10.99 / 0.42),
                                 'construction_delay': construction_delay}
    # We do not invest on biomass gasification yet
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), 'invest': [0.0, 0.0, 0.0]})

    syngas_ratio = BiomassGasification.syngas_COH2_ratio

    # 24 plants for liquid fuel production with global production of liquid fuel from biomass-derived syngas
    # 750,000 t/year of liquid fuel
    # 8 plants for gaseous fuel production (SNG and H2), with global
    # production of gaseous fuel from biomass-derived syngas 3.2e8 Nm3/year
    syngas_needs_for_ft = 1.883
    initial_production = 0.75 * \
        LiquidFuel.data_energy_dict['calorific_value'] * syngas_needs_for_ft + 3.2e8 * \
        Methane.data_energy_dict['density'] * \
        Methane.data_energy_dict['calorific_value'] / 1e9

    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': [3.317804973859207, 6.975128305927281, 4.333201737255864,
                                                         3.2499013031833868, 1.5096723255070685, 1.7575996841282722,
                                                         4.208448479896288, 2.7398341887870643, 5.228582707722979,
                                                         10.057639166085064, 0.0, 2.313462297352473, 6.2755625737595535,
                                                         5.609159099363739, 6.3782076592711885, 8.704303197679629,
                                                         6.1950256610618135, 3.7836557445596464, 1.7560205289962763,
                                                         4.366363995027777, 3.3114883533312236, 1.250690879995941,
                                                         1.7907619419001841, 4.88748519534807]})

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'years': ('float', None, True),
                                                                'age': ('float', None, True),
                                                                'distrib': ('float', None, True)}
                                       },
               'invest_before_ystart': {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int',  [-20, -1], False),
                                                                 'invest': ('float',  None, True)},
                                        'dataframe_edition_locked': False}}
    # -- add specific techno inputs to this
    DESC_IN.update(SyngasTechnoDiscipline.DESC_IN)

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = BiomassGasification(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
