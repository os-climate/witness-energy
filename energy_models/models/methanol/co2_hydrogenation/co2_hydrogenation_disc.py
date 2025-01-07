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


from energy_models.core.stream_type.energy_models.methanol import Methanol
from energy_models.core.techno_type.disciplines.methanol_techno_disc import (
    MethanolTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.methanol.co2_hydrogenation.co2_hydrogenation import (
    CO2Hydrogenation,
)


class CO2HydrogenationDiscipline(MethanolTechnoDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'CO2 Hydrogenation Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-gas-pump fa-fw',
        'version': '',
    }
    # -- add specific techno inputs to this
    techno_name = GlossaryEnergy.CO2Hydrogenation
    energy_name = Methanol.name

    # energy data
    methanol_density = Methanol.data_energy_dict['density']
    methanol_calorific_value = Methanol.data_energy_dict['calorific_value']



    techno_infos_dict_default = {
        'Capex_init': 35.58 / (20 * 50) / 5.54,
        # Total capital [M$] / (annual production * lifetime) [kt] / conversion factor [kWh/kg] = [$/kWh]
        'Capex_init_unit': '$/kWh',
        'Opex_percentage': 0.06,
        'efficiency': 1,
        'CO2_from_production': 0.0,
        'CO2_from_production_unit': 'kg/kg',
        'carbon_capture_demand': 1.4,
        'carbon_capture_demand_unit': 'kg/kg',
        'hydrogen_demand': 0.196,
        'hydrogen_demand_unit': 'kg/kg',
        'elec_demand': 0.174,
        'elec_demand_unit': 'kWh/kg',
        'water_demand': 267.7,
        'water_demand_unit': 'kg/kg',
        'maturity': 5,
        'learning_rate': 0.15,
        # Tentative learning rate, no data found but potential to improve seems to exists based on literature
        'full_load_hours': 8000.0,
        'WACC': 0.06,
        'techno_evo_eff': 'no',
    }

    initial_production = 543  # 543 TWh

    DESC_IN = {'techno_infos_dict': {'type': 'dict', 'default': techno_infos_dict_default, 'unit': 'defined in dict'},
                      }
    DESC_IN.update(MethanolTechnoDiscipline.DESC_IN)
    # -- add specific techno outputs to this
    DESC_OUT = MethanolTechnoDiscipline.DESC_OUT

    def init_execution(self):
        self.techno_model = CO2Hydrogenation(self.techno_name)
