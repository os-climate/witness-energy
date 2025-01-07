'''
Copyright 2022 Airbus SAS
Modifications on 2023/09/30-2023/11/16 Copyright 2023 Capgemini

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

from energy_models.core.techno_type.disciplines.fossil_techno_disc import (
    FossilTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.fossil.fossil_simple_techno.fossil_simple_techno import (
    FossilSimpleTechno,
)
from energy_models.models.liquid_fuel.refinery.refinery_disc import RefineryDiscipline
from energy_models.models.methane.fossil_gas.fossil_gas_disc import FossilGasDiscipline
from energy_models.models.solid_fuel.coal_extraction.coal_extraction_disc import (
    CoalExtractionDiscipline,
)


class FossilSimpleTechnoDiscipline(FossilTechnoDiscipline):
    """
        Generic Fossil Techno used in the WITNESS Coarse process
        It has a low price per kWh without CO2 but a high CO2 emissions per kWh
        It has properties similar to the coal generation techno
    """

    # ontology information
    _ontology_data = {
        'label': 'Fossil Technology Model ',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-smog fa-fw',
        'version': '',
    }
    techno_name = GlossaryEnergy.FossilSimpleTechno


    prod_solid_fuel = 45000.  # TWh
    prod_liquid_fuel = 53000.  # TWh
    prod_methane = 39106.77  # TWh
    prod_fossil = prod_solid_fuel + prod_liquid_fuel + prod_methane
    #     capex_coal = 8.3
    #     capex_oil = 42.4
    #     capex_methane = 32.2
    #     capex = (capex_coal * prod_solid_fuel +
    #              capex_oil * prod_liquid_fuel +
    #              capex_methane * prod_methane) / prod_fossil
    co2_from_prod = (RefineryDiscipline.techno_infos_dict_default['CO2_from_production'] * prod_liquid_fuel +
                     CoalExtractionDiscipline.techno_infos_dict_default['CO2_from_production'] * prod_solid_fuel +
                     FossilGasDiscipline.techno_infos_dict_default['CO2_from_production'] * prod_methane) / prod_fossil

    techno_infos_dict_default = {'maturity': 0,
                                 'Opex_percentage': 0.299,
                                 'WACC': 0.058,
                                 'learning_rate': 0.00,
                                 'Capex_init': 222.64,
                                 'Capex_init_unit': '$/MWh',
                                 'techno_evo_eff': 'no',
                                 'efficiency': 1.0,
                                 'CO2_from_production': co2_from_prod,
                                 'CO2_from_production_unit': 'kg/kg',
                                 'resource_price': 35.0,
                                 'resource_price_unit': '$/MWh',
                                 'CH4_venting_emission_factor': (21.9 + 7.2) / 50731.,
                                 'CH4_flaring_emission_factor': (1.4 + 6.9) / 50731.,
                                 'CH4_unintended_leakage_emission_factor': (0.6 + 1.7) / 50731.,
                                 'CH4_emission_factor_unit': 'Mt/TWh',
                                 }

    techno_info_dict = techno_infos_dict_default
    # net production = 90717.76   TWh
    initial_production = 136917.16  # TWh

    
    FLUE_GAS_RATIO = np.array([0.12])

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
                      }

    # -- add specific techno outputs to this
    DESC_IN.update(FossilTechnoDiscipline.DESC_IN)

    _maturity = 'Research'

    def init_execution(self):
        self.techno_model = FossilSimpleTechno(self.techno_name)
