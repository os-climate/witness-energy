'''
Copyright 2022 Airbus SAS
Modifications on 2023/09/19-2023/11/16 Copyright 2023 Capgemini

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


from energy_models.core.techno_type.disciplines.carbon_storage_techno_disc import (
    CSTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.carbon_storage.biomass_burying_fossilization.biomass_burying_fossilization import (
    BiomassBuryingFossilization,
)


class BiomassBuryingFossilizationDiscipline(CSTechnoDiscipline):
    """**EnergyModelsDiscipline** is the :class:`~gems.core.discipline.MDODiscipline`
    implementing the computation of Energy Models outputs."""

    # ontology information
    _ontology_data = {
        'label': 'Biomass Burying Fossilization Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': '',
        'version': '',
    }
    techno_name = GlossaryEnergy.BiomassBuryingFossilization

    techno_infos_dict_default = {'maturity': 0,
                                 'Opex_percentage': 0,
                                 'WACC': 0.1,  # Weighted averaged cost of capital for the carbon storage plant
                                 'learning_rate': 0,
                                 'Capex_init': 0.0175,
                                 'Capex_init_unit': '$/kgCO2',
                                 'efficiency': 1,
                                 'CO2_capacity_peryear': 3.6E+8,  # kg CO2 /year
                                 'CO2_capacity_peryear_unit': 'kg CO2/year',
                                 'real_factor_CO2': 1.0,
                                 GlossaryEnergy.TransportCostValue: 0.0,
                                 'transport_cost_unit': '$/kgCO2',
                                 'enthalpy': 1.124,
                                 'enthalpy_unit': 'kWh/kgC02',
                                 GlossaryEnergy.EnergyEfficiency: 1,
                                 'techno_evo_eff': 'no',
                                 }

    techno_info_dict = techno_infos_dict_default

    initial_storage = 0  # in kg at year_start

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               }
    # -- add specific techno outputs to this
    DESC_IN.update(CSTechnoDiscipline.DESC_IN)

    DESC_OUT = CSTechnoDiscipline.DESC_OUT

    _maturity = 'Research'

    def init_execution(self):
        self.model = BiomassBuryingFossilization(self.techno_name)
