'''
Copyright 2022 Airbus SAS
Modifications on 2023/09/25-2023/11/16 Copyright 2023 Capgemini

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

from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.energy_models.biogas import BioGas
from energy_models.core.techno_type.base_techno_models.electricity_techno import (
    ElectricityTechno,
)
from energy_models.glossaryenergy import GlossaryEnergy


class BiogasFired(ElectricityTechno):

    def compute_other_streams_needs(self):
        self.outputs[f'{GlossaryEnergy.TechnoDetailedPricesValue}:{BioGas.name}_needs'] = self.inputs['techno_infos_dict'][f'{BioGas.name}_needs']

    def compute_byproducts_production(self):
        co2_prod = self.get_theoretical_co2_prod()
        self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:{CarbonCapture.flue_gas_name} ({GlossaryEnergy.mass_unit})'] =\
            co2_prod * self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:{self.stream_name} ({self.product_unit})']

        self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:{GlossaryEnergy.hightemperatureheat_energyname} ({self.product_unit})'] = \
            self.outputs[f'{GlossaryEnergy.TechnoEnergyDemandsValue}:{BioGas.name} ({self.product_unit})'] - \
            self.outputs[f'{GlossaryEnergy.TechnoTargetProductionValue}:{self.stream_name} ({self.product_unit})']

    def get_theoretical_co2_prod(self, unit='kg/kWh'):
        ''' 
        Get co2 needs in kg co2 /kWh 
        '''
        biogas_data = BioGas.data_energy_dict
        # kg of C02 per kWh of biogas burnt
        biogas_co2 = biogas_data[GlossaryEnergy.CO2PerUse]
        # Amount of biogas in kwh for 1 kwh of elec
        biogas_need = self.inputs['techno_infos_dict'][f'{BioGas.name}_needs']

        co2_prod = biogas_co2 * biogas_need
        return co2_prod
