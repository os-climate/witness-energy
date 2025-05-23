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

from energy_models.core.stream_type.energy_type import EnergyType
from energy_models.glossaryenergy import GlossaryEnergy


class Electricity(EnergyType):
    name = GlossaryEnergy.electricity
    hydropower_name = GlossaryEnergy.Hydropower
    default_techno_list = ['WindOffshore', GlossaryEnergy.WindOnshore, GlossaryEnergy.SolarPv, 'SolarThermal', GlossaryEnergy.Hydropower,
                           GlossaryEnergy.CoalGen, 'OilGen', 'Nuclear', 'CombinedCycleGasTurbine',
                           GlossaryEnergy.GasTurbine, 'BiogasFired', 'BiomassFired',
                           # è'Geothermal'
                           ]


    def compute(self):
        super().compute()
        self.compute_hydropower_constraint()

    def compute_hydropower_constraint(self):
        '''
        Compute hydropower production constraint so that
        '''
        if GlossaryEnergy.Hydropower in self.inputs[GlossaryEnergy.techno_list]:
            self.outputs[f'prod_hydropower_constraint:{GlossaryEnergy.Years}'] = self.years
            self.outputs['prod_hydropower_constraint:hydropower_constraint'] = - (
                    self.inputs[f'{GlossaryEnergy.Hydropower}.{GlossaryEnergy.TechnoProductionValue}:{self.name}'] -
                    self.inputs['hydropower_production_current']) / self.inputs['hydropower_constraint_ref']
