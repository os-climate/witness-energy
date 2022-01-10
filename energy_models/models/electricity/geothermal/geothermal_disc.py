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
from energy_models.core.techno_type.disciplines.electricity_techno_disc import ElectricityTechnoDiscipline
from energy_models.models.electricity.geothermal.geothermal import Geothermal


class GeothermalDiscipline(ElectricityTechnoDiscipline):
    """**EnergyModelsDiscipline** is the :class:`~gems.core.discipline.MDODiscipline`
    implementing the computation of Energy Models outputs."""

    techno_name = 'Geothermal'
    # Tsiropoulos, I., Tarvydas, D. and Zucker, A., 2018.
    # Cost development of low carbon energy technologies-Scenario-based cost trajectories to 2050, 2017 Edition.
    # Publications Office of the European Union, Luxemburgo.
    lifetime = 30
    # Cole, W.J., Gates, N., Mai, T.T., Greer, D. and Das, P., 2020.
    # 2019 standard scenarios report: a US electric sector outlook (No. NREL/PR-6A20-75798).
    # National Renewable Energy Lab.(NREL), Golden, CO (United States).
    construction_delay = 7

    techno_infos_dict_default = {'maturity': 0,
                                 'Opex_percentage': 0.045,
                                 # Fixed 4.0% and recurrent 0.5 %
                                 # Demystifying-the-Costs-of-Electricity-Generation-Technologies, average
                                 'WACC': 0.048,  # Weighted averaged cost of capital / ATB NREL 2020
                                 'learning_rate': 0.05,  # https://publications.jrc.ec.europa.eu/repository/bitstream/JRC109894/cost_development_of_low_carbon_energy_technologies_v2.2_final_online.pdf
                                 'lifetime': lifetime,
                                 'lifetime_unit': 'years',
                                 # Demystifying-the-Costs-of-Electricity-Generation-Technologies, average
                                 'Capex_init': 4275,
                                 'Capex_init_unit': '$/kW',
                                 'full_load_hours': 8760.0,  # Full year hours
                                 # Demystifying-the-Costs-of-Electricity-Generation-Technologies
                                 'capacity_factor': 0.85,
                                 'techno_evo_eff': 'no',
                                 'efficiency': 1.0,
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 'construction_delay': construction_delay, }

    techno_info_dict = techno_infos_dict_default
    # Initial production in TWh at year_start, 621 GW / GWEC
    # Annual-Wind-Report_2019_digital_final_2r
    initial_production = 92

    # Invest from IRENA
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), 'invest': [2.4, 2.9, 2.5,
                                                                     2.7, 2.4, 2.5,
                                                                     1.2]})

    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': [
                                                 9.800600043, 7.549068948, 6.398734632, 5.909842548, 8.986986843,
                                                 6.916385074, 3.867999137, 6.614422316, 0, 3.192177727, 6.326838738,
                                                 4.600337264, 3.177798548, 3.335969516, 2.05622259, 2.05622259,
                                                 2.05622259, 1.567330505, 2.530735495, 3.2784528, 3.2784528,
                                                 3.2784528, 3.220936085, 0, 0, 0, 0, 0, 0]
                                             })

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default},
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'age': ('int',  [0, 100], False),
                                                                'distrib': ('float',  None, True)},
                                       'dataframe_edition_locked': False},
               'invest_before_ystart': {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int',  [-20, -1], False),
                                                                 'invest': ('float',  None, True)},
                                        'dataframe_edition_locked': False}}
    # -- add specific techno outputs to this
    DESC_IN.update(ElectricityTechnoDiscipline.DESC_IN)

    DESC_OUT = ElectricityTechnoDiscipline.DESC_OUT

    _maturity = 'Research'

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = Geothermal(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
