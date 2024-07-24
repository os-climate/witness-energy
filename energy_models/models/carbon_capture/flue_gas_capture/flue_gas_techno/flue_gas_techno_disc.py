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

from energy_models.core.techno_type.disciplines.carbon_capture_techno_disc import (
    CCTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.carbon_capture.flue_gas_capture.flue_gas_techno.flue_gas_techno import (
    FlueGasTechno,
)


class FlueGasTechnoDiscipline(CCTechnoDiscipline):
    """
    Generic Flue Gas techno for WITNESS Coarse process
    Modeled after calcium looping
    """

    # ontology information
    _ontology_data = {
        'label': 'Flue Gas Technology Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fa-solid fa-cloud fa-fw',
        'version': '',
    }
    techno_name = f'{GlossaryEnergy.flue_gas_capture}.{GlossaryEnergy.FlueGasTechno}'
    lifetime = 25
    construction_delay = 1

    heat_to_power_lost = 0.243
    heat_duty = 18
    elec_demand_capture = 338
    mj_to_kwh_factor = 0.277778
    c02_capacity_year = 790.2 * 0.85 * 8760 * 550
    carbon_capture_efficiency = 0.90

    techno_infos_dict_default = {'lifetime': lifetime,
                                 'capacity_factor': 0.85,
                                 'maturity': 0,
                                 'Opex_percentage': 0,
                                 'learning_rate': 0,
                                 'WACC': 0.07,
                                 'Capex_init': 1313000000 / (c02_capacity_year * carbon_capture_efficiency),
                                 'Capex_init_unit': '$/kgCO2',

                                 'elec_demand': elec_demand_capture * mj_to_kwh_factor / 1000,
                                 'elec_demand_unit': 'kWh/kgCO2',

                                 'heat_demand': heat_duty * heat_to_power_lost * mj_to_kwh_factor / 1000,
                                 'heat_demand_unit': 'kWh/kgCO2',

                                 'CO2_capacity_peryear': c02_capacity_year,  # kg CO2 /year
                                 'CO2_capacity_peryear_unit': 'kg CO2/year',

                                 'carbon_capture_efficiency': carbon_capture_efficiency,

                                 'real_factor_CO2': 1.0,

                                 'techno_evo_eff': 'no',
                                 'efficiency': 1.0,
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 GlossaryEnergy.ConstructionDelay: construction_delay, }

    techno_info_dict = techno_infos_dict_default

    initial_capture = 5  # Mt

    
    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime - 1),
                                             'distrib': [10.0, 10.0, 10.0, 10.0, 10.0,
                                                         10.0, 10.0, 10.0,
                                                         10.0, 10.0, 0.0,
                                                         0.0, 0.0, 0.0,
                                                         0.0, 0.0, 0.0,
                                                         0.0, 0.0, 0.0,
                                                         0.0, 0.0, 0.0]
                                             })

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_production': {'type': 'float', 'unit': 'MtCO2', 'default': initial_capture},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'age': ('int', [0, 100], False),
                                                                'distrib': ('float', None, True)},
                                       'dataframe_edition_locked': False},
               GlossaryEnergy.FlueGasMean: {'type': 'dataframe', 'namespace': 'ns_flue_gas',
                                            'visibility': CCTechnoDiscipline.SHARED_VISIBILITY, 'unit': '',
                                            'dataframe_descriptor': {GlossaryEnergy.Years: ('float', None, True),
                                                                     GlossaryEnergy.FlueGasMean: (
                                                                     'float', None, True), }
                                            },
               }
    # -- add specific techno outputs to this
    DESC_IN.update(CCTechnoDiscipline.DESC_IN)

    DESC_OUT = CCTechnoDiscipline.DESC_OUT

    _maturity = 'Research'

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = FlueGasTechno(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)

    def compute_sos_jacobian(self):
        # Grad of price vs energyprice
        CCTechnoDiscipline.compute_sos_jacobian(self)

        grad_dict = self.techno_model.grad_price_vs_stream_price()

        self.set_partial_derivatives_techno(
            grad_dict, None)

        self.set_partial_derivatives_flue_gas(GlossaryEnergy.renewable)
