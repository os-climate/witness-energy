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

from energy_models.core.techno_type.disciplines.methane_techno_disc import MethaneTechnoDiscipline
from energy_models.models.methane.upgrading_biogas.upgrading_biogas import UpgradingBiogas


class UpgradingBiogasDiscipline(MethaneTechnoDiscipline):
    # -- add specific techno inputs to this

    techno_name = 'UpgradingBiogas'
    lifetime = 20
    construction_delay = 2  # years
    #'reaction': 'CnHaOb + (n-a/4-b/2)H20 = (n/2+a/8-b/4) CH4 + (n/2-a/8+b/4) CO2',

    techno_infos_dict_default = {'Opex_percentage': 0.04,
                                 'lifetime': lifetime,  # for now constant in time but should increase with time
                                 'lifetime_unit': 'years',
                                 'Capex_init': 1570000.0,  # CAPEX p27 only for upgrading by amine
                                 'Capex_init_unit': 'euro',
                                 'available_power': 3440000.0,
                                 'available_power_unit': 'm^3',
                                 'euro_dollar': 1.114,
                                 'efficiency': 0.83,
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 # biogas demand represent needed biogas to obtain 1 m^3 of methane here 6201 t of biogas for 3.44
                                 #p25 in graphs
                                 'biogas_demand': 6.46 / 3.44,
                                 'biogas_demand_unit': 'm^3/m^3',
                                 #MEA : MonoEthanolAmine
                                 'MEA_needs': 205.0 / 3440.0,
                                 'MEA_needs_unit': 'kg/m^3',
                                 'elec_demand': 1.0,
                                 'elec_demand_unit': 'kWh/m^3',
                                 'maturity': 3,
                                 'learning_rate': 0.2,
                                 'WACC': 0.0878,
                                 'techno_evo_eff': 'no',
                                 'construction_delay': construction_delay  # in kWh/kg
                                 }

    # At present, about  3.5 Mtoe of biomethane is produced around the world and 92.3% are from upgrading biogas, rest is biomass gasification 0.27mtoe
    # 1 Mtoe = 11.63 TWh
    initial_production = 3.5 * 0.923 * 11.63  # in TWh at year_start
    # Same as anaerobic digestion since most of biogas from anaerobic
    # digestion is converted into bioCH4
    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 4.085787594423131, 11.083221775965836, 9.906291833479699,
                                                         11.264502455357881, 15.372601517593951, 10.940986166952394,
                                                         6.682284695273031, 3.1012940652355083, 7.711401160086531,
                                                         5.848393573822739, 2.2088353407762535, 3.162650601721087,
                                                         8.631749219311956]})  # to review

    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), 'invest': [4.43575, 4.43575]})
    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default},
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution},
               'invest_before_ystart': {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int',  [-20, -1], False),
                                                                 'invest': ('float',  None, True)},
                                        'dataframe_edition_locked': False}}

    DESC_IN.update(MethaneTechnoDiscipline.DESC_IN)
    # -- add specific techno outputs to this
    DESC_OUT = MethaneTechnoDiscipline.DESC_OUT

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = UpgradingBiogas(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
