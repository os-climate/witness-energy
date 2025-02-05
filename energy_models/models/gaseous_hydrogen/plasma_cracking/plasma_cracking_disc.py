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

from energy_models.core.techno_type.disciplines.gaseous_hydrogen_techno_disc import (
    GaseousHydrogenTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.gaseous_hydrogen.plasma_cracking.plasma_cracking import (
    PlasmaCracking,
)


class PlasmaCrackingDiscipline(GaseousHydrogenTechnoDiscipline):
    """
    PLasmacracking discipline
    """

    # ontology information
    _ontology_data = {
        'label': 'Hydrogen Plasma Cracking Model',
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
    techno_name = GlossaryEnergy.PlasmaCracking

    techno_infos_dict_default = {'reaction': 'CH4 = C + 2H2',
                                 'maturity': 5,
                                 'Opex_percentage': 0.2,
                                 'CO2_from_production': 0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 'elec_demand': 8.325,
                                 'elec_demand_unit': 'kWh/kg',
                                 'WACC': 0.1,
                                 'learning_rate': 0.25,
                                 'maximum_learning_capex_ratio': 0.33,
                                 'Capex_init': 12440000.0,
                                 'Capex_init_unit': 'pounds',
                                 'pounds_dollar': 1.32,
                                 'full_load_hours': 8410.0,
                                 'available_power': 150,
                                 'available_power_unit': 'kg/h',
                                 'techno_evo_eff': 'yes',
                                 'techno_evo_time': 4,
                                 'efficiency': 0.15,
                                 'efficiency_max': 0.6,
                                 'nb_years_amort_capex': 10.,
                                 }

    initial_production = 1e-12
    CO2_credits = pd.DataFrame({GlossaryEnergy.Years: range(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1),
                                'CO2_credits': 50.})

    market_demand = pd.DataFrame(
        {GlossaryEnergy.Years: range(GlossaryEnergy.YearStartDefault, GlossaryEnergy.YearEndDefault + 1), 'carbon_demand': 5e-2})

    # DESC_IN.update(
    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_production': {'type': 'float',
                                      'unit': 'TWh', 'default': initial_production},

               'CO2_credits': {'type': 'dataframe', 'default': CO2_credits, 'unit': '$/t/year', 'structuring': True,
                               'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                        'CO2_credits': ('float', None, True), }
                               },
               'market_demand': {'type': 'dataframe', 'default': market_demand, 'unit': 'Mt/year', 'structuring': True,
                                 'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                          'carbon_demand': ('float', None, True),}
                                 }
               }

    # -- add specific techno inputs to this
    DESC_IN.update(GaseousHydrogenTechnoDiscipline.DESC_IN)

    # -- add specific techno outputs to this
    # DESC_OUT = HydrogenTechnoDiscipline.DESC_OUT
    DESC_OUT = {'percentage_resource': {'type': 'dataframe', 'unit': '%'},
                'carbon_quantity_to_be_stored': {'type': 'dataframe', 'unit': 'Mt', 'namespace': 'ns_carb',
                                                 'visibility': 'Shared'}}
    DESC_OUT.update(GaseousHydrogenTechnoDiscipline.DESC_OUT)

    def add_additionnal_dynamic_variables(self):

        if self.get_data_in() is not None:
            if GlossaryEnergy.YearStart in self.get_data_in():
                year_start, year_end = self.get_sosdisc_inputs([GlossaryEnergy.YearStart, GlossaryEnergy.YearEnd])
                if year_start is not None and year_end is not None:
                    years = np.arange(year_start, year_end + 1)

                    if self.get_sosdisc_inputs('CO2_credits')[GlossaryEnergy.Years].values.tolist() != list(years):
                        self.update_default_value(
                            'CO2_credits', self.IO_TYPE_IN, pd.DataFrame({GlossaryEnergy.Years: years, 'CO2_credits': 50.}))

                    if self.get_sosdisc_inputs('market_demand')[GlossaryEnergy.Years].values.tolist() != list(years):
                        self.update_default_value(
                            'market_demand', self.IO_TYPE_IN,
                            pd.DataFrame({GlossaryEnergy.Years: years, 'carbon_demand': 5e-2}))

        return {}, {}

    def init_execution(self):
        self.model = PlasmaCracking(self.techno_name)
