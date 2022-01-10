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
from energy_models.models.electricity.wind_onshore.wind_onshore import WindOnshore


class WindOnshoreDiscipline(ElectricityTechnoDiscipline):
    """**EnergyModelsDiscipline** is the :class:`~gems.core.discipline.MDODiscipline`
    implementing the computation of Energy Models outputs."""

    techno_name = 'WindOnshore'
    lifetime = 30  # ATB NREL 2020
    construction_delay = 3  # ATB NREL 2020

    techno_infos_dict_default = {'maturity': 0,
                                 'Opex_percentage': 0.022,  # ATB NREL 2020, average value
                                 'WACC': 0.05,  # Weighted averaged cost of capital / ATB NREL 2020
                                 'learning_rate':  0.05,  # Cost development of low carbon energy technologies
                                 'lifetime': lifetime,
                                 'lifetime_unit': 'years',
                                 'Capex_init': 1497,  # Irena Future of wind 2019
                                 'Capex_init_unit': '$/kW',
                                 'full_load_hours': 8760.0,  # Full year hours
                                 'capacity_factor': 0.34,  # Irena Future of wind 2019
                                 'capacity_factor_at_year_end': 0.45,  # Irena Future of wind 2019
                                 'techno_evo_eff': 'no',
                                 'efficiency': 1.0,
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 'construction_delay': construction_delay, }

    techno_info_dict = techno_infos_dict_default
    # Initial production in TWh at year_start, 621 GW / GWEC
    # Annual-Wind-Report_2019_digital_final_2r
    # initial_production = 0.621 * techno_infos_dict_default['full_load_hours'] * \
    #     techno_infos_dict_default['capacity_factor']
    initial_production = 1323  # IEA in 2019
    # Invest in 2019 => 138.2 bn less 29.6 bn offshore => 108.6 bn
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), 'invest': [98.1, 92.7, 108.6]})

    # Age distribution => GWEC Annual-Wind-Report_2019_digital_final_2r
    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': [
                                                 8.73, 7.46, 7.89, 8.49, 9.73, 8.08, 5.56, 7.07,
                                                 6.41, 6.15, 6.10, 4.27, 3.22, 2.35, 1.84, 1.30,
                                                 1.27, 1.14, 1.03, 0.96, 0.95, 0, 0, 0, 0, 0, 0, 0, 0]
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
        self.techno_model = WindOnshore(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
