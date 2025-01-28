'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2023/11/09 Copyright 2023 Capgemini

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

from energy_models.core.stream_type.energy_models.syngas import (
    compute_calorific_value,
    compute_density,
    compute_molar_mass,
)
from energy_models.core.techno_type.techno_type import TechnoType
from energy_models.glossaryenergy import GlossaryEnergy


class SyngasTechno(TechnoType):
    stream_name = GlossaryEnergy.syngas
    syngas_COH2_ratio = None

    def compute(self):
        super().compute()
        self.outputs[f'syngas_ratio:{GlossaryEnergy.Years}'] = self.years
        self.outputs['syngas_ratio:syngas_ratio'] = self.zeros_array + self.syngas_COH2_ratio

    def configure_energy_data(self):
        self.inputs['data_energy_dict'] = self.inputs['data_fuel_dict']

        molar_mass = compute_molar_mass(self.syngas_COH2_ratio / 100.)
        calorific_value = compute_calorific_value(
            self.syngas_COH2_ratio / 100.)
        density = compute_density(self.syngas_COH2_ratio / 100.)

        self.inputs['data_energy_dict']['molar_mass'] = molar_mass
        self.inputs['data_energy_dict']['calorific_value'] = calorific_value
        self.inputs['data_energy_dict']['high_calorific_value'] = calorific_value
        self.inputs['data_energy_dict']['density'] = density

    

    def compute_transport(self):
        # Electricity has no Calorific value overload
        # Warning transport cost unit must $/kWh
        transport_cost = self.inputs[f'{GlossaryEnergy.TransportCostValue}:transport'] * \
                         self.inputs[f'{GlossaryEnergy.TransportMarginValue}:{GlossaryEnergy.MarginValue}'] / 100.0

        return transport_cost
