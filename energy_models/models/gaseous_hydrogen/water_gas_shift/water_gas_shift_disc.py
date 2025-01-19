'''
Copyright 2022 Airbus SAS
Modifications on 2023/10/10-2023/11/16 Copyright 2023 Capgemini

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

from copy import deepcopy

import numpy as np
import pandas as pd

from energy_models.core.stream_type.carbon_models.carbon_dioxyde import CO2
from energy_models.core.stream_type.energy_models.syngas import (
    compute_calorific_value as compute_syngas_calorific_value,
)
from energy_models.core.stream_type.energy_models.syngas import (
    compute_molar_mass as compute_syngas_molar_mass,
)
from energy_models.core.techno_type.disciplines.gaseous_hydrogen_techno_disc import (
    GaseousHydrogenTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.gaseous_hydrogen.water_gas_shift.water_gas_shift import WGS


class WaterGasShiftDiscipline(GaseousHydrogenTechnoDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Water Gas Shift Model',
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

    techno_name = GlossaryEnergy.WaterGasShift
    # Giuliano, A., Freda, C. and Catizzone, E., 2020.
    # Techno-economic assessment of bio-syngas production for methanol synthesis: A focus on the water gas shift and carbon capture sections.
    # Bioengineering, 7(3), p.70.

    techno_infos_dict_default = {'maturity': 5,
                                 'reaction': 'syngas(H2+r1CO) + cH20  = dCO2 + e(H2+r2C0)',
                                 # p8 of Giuliano2020 : Maintenance and labor costs were associated to the capital costs and
                                 # estimated as 10% of the annual total capital
                                 # costs
                                 'Opex_percentage': 0.1,
                                 # Giuliano2020 : the elec demand is more or
                                 # less constant 6.6 MW for WGS over the 8.6
                                 'elec_demand': 6.6e3,
                                 'elec_demand_unit': 'kW',
                                 'WACC': 0.0878,  # Weighted averaged cost of capital for the carbon capture plant
                                 'learning_rate': 0.2,
                                 # Capex initial at year 2020
                                 'Capex_init_vs_CO_conversion': [5.0e6, 9.2e6],
                                 'Capex_init_vs_CO_conversion_unit': 'euro',
                                 'low_heat_production': (41 / 46.016) * 1000 * 2.77778e-13,
                                 # CO+H2O→CO2+H2ΔH°=−41kJ/mol, Co2(44g/mol),H2(2.016g/mol)
                                 'low_heat_production_unit': 'TWh/kg',
                                 # Capex initial at year 2020
                                 'CO_conversion': [36.0, 100.0],
                                 'CO_conversion_unit': '%',
                                 'euro_dollar': 1.12,  # in June 2020
                                 'full_load_hours': 7920,
                                 'input_power': 861.0e3,
                                 # Wang, Y., Li, G., Liu, Z., Cui, P., Zhu, Z. and Yang, S., 2019.
                                 # Techno-economic analysis of biomass-to-hydrogen process in comparison with coal-to-hydrogen process.
                                 # Energy, 185, pp.1063-1075.
                                 # From Wang2019 Fig 10 ratio of energies
                                 'efficiency': 80.787 / (80.787 + 8.37),
                                 # perfectly efficient
                                 'input_power_unit': 'mol/h',
                                 'techno_evo_eff': 'no',  # yes or no
                                 }

    # Fake investments (not found in the litterature...)
        # From Future of hydrogen : accounting for around three quarters of the
    # annual global dedicated hydrogen production of around 70 million tonnes. and 23+ from coal gasification
    # that means that WGS is used for 98% of the hydrogen production
    initial_production = 70.0 * 33.3 * \
                         0.98  # in TWh at year_start MT*kWh/kg = TWh

    # Fake initial age distrib (not found in the litterature...)
    FLUE_GAS_RATIO = np.array([0.175])

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
                      
               'syngas_ratio': {'type': 'array', 'unit': '%',
                                'visibility': GaseousHydrogenTechnoDiscipline.SHARED_VISIBILITY,
                                'namespace': 'ns_syngas'},
               'needed_syngas_ratio': {'type': 'float', 'default': 0.0, 'unit': '%'}
               }
    # -- add specific techno inputs to this
    DESC_IN.update(GaseousHydrogenTechnoDiscipline.DESC_IN)

    def init_execution(self):
        self.model = WGS(self.techno_name)

    def specific_run(self):

        # -- get inputs
        inputs_dict = deepcopy(self.get_sosdisc_inputs())
        years = np.arange(inputs_dict[GlossaryEnergy.YearStart],
                          inputs_dict[GlossaryEnergy.YearEnd] + 1)
        detailed_prod_syngas_prices = pd.DataFrame(
            {GlossaryEnergy.Years: years})
        for techno in inputs_dict['energy_detailed_techno_prices']:
            if techno != GlossaryEnergy.Years:
                techno_model = WGS(self.techno_name)
                # Update init values syngas price and syngas_ratio
                inputs_dict[GlossaryEnergy.StreamPricesValue][GlossaryEnergy.syngas] = \
                    inputs_dict['energy_detailed_techno_prices'][
                        techno]
                inputs_dict['syngas_ratio'] = np.ones(
                    len(years)) * inputs_dict['syngas_ratio_technos'][techno]
                # -- configure class with inputs
                techno_model.configure_parameters(inputs_dict)
                techno_model.configure_parameters_update(inputs_dict)
                # -- compute informations

                # Compute the price with these new values
                techno_syngas_price = techno_model.compute_price()
                # Store only the overall price

                global_techno = f'{techno} + WGS'
                detailed_prod_syngas_prices[global_techno] = techno_syngas_price[self.techno_name]

        self.store_sos_outputs_values(
            {'detailed_prod_syngas_prices': detailed_prod_syngas_prices})
