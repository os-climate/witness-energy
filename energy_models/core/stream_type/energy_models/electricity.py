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
import pandas as pd

from energy_models.core.stream_type.energy_type import EnergyType
from energy_models.glossaryenergy import GlossaryEnergy


class Electricity(EnergyType):
    name = GlossaryEnergy.electricity
    hydropower_name = 'Hydropower'
    default_techno_list = ['WindOffshore', 'WindOnshore', 'SolarPv', 'SolarThermal', 'Hydropower',
                           'CoalGen', 'OilGen', 'Nuclear', 'CombinedCycleGasTurbine',
                           'GasTurbine', 'BiogasFired', 'BiomassFired',
                           'Geothermal']

    def __init__(self, name):
        super().__init__(name)
        self.hydropower_production_current = None
        self.hydropower_constraint_ref = None
        self.hydropower_constraint = None

    def configure_parameters(self, inputs_dict):
        '''
        Overide configure parameters of EnergyType
        '''
        self.hydropower_production_current = inputs_dict['hydropower_production_current']
        self.hydropower_constraint_ref = inputs_dict['hydropower_constraint_ref']
        EnergyType.configure_parameters(self, inputs_dict)

    def compute_hydropower_constraint(self):
        '''
        Compute hydropower production constraint so that 
        '''
        self.hydropower_constraint = pd.DataFrame(
            {GlossaryEnergy.Years: self.production[GlossaryEnergy.Years]})

        self.hydropower_constraint['hydropower_constraint'] = - (
                self.production_by_techno[
                    f'{self.name} {self.hydropower_name} ({self.unit})'] - self.hydropower_production_current) / self.hydropower_constraint_ref
