'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/09-2023/11/14 Copyright 2023 Capgemini

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

from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.energy_models.fossil import Fossil
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.techno_type.base_techno_models.fossil_techno import FossilTechno
from energy_models.glossaryenergy import GlossaryEnergy


class FossilSimpleTechno(FossilTechno):


    def compute_specifif_costs_of_technos(self):
        self.specific_costs = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            GlossaryEnergy.ResourcesPriceValue: self.techno_infos_dict['resource_price']
        })

    def compute_production(self):
        # co2_from_raw_to_net will represent the co2 emitted from the use of
        # the fossil energy into other fossil energies. For example generation
        # of fossil electricity from fossil fuels
        co2_per_use = self.data_energy_dict[GlossaryEnergy.CO2PerUse] / \
                      self.data_energy_dict['calorific_value']
        co2_from_raw_to_net = self.production_detailed[
                                  f'{FossilTechno.energy_name} ({self.product_energy_unit})'].values * (
                                      1.0 - Fossil.raw_to_net_production) * co2_per_use

        self.production_detailed[f'{CarbonCapture.flue_gas_name} ({self.mass_unit})'] = self.techno_infos_dict[
                                                                                            'CO2_from_production'] / \
                                                                                        self.data_energy_dict[
                                                                                            'calorific_value'] * \
                                                                                        self.production_detailed[
                                                                                            f'{FossilTechno.energy_name} ({self.product_energy_unit})'] + \
                                                                                        co2_from_raw_to_net
        '''
        Method to compute CH4 emissions from gas production
        The proposed V0 only depends on production.
        Equation is taken from the GAINS model for crude oil
        https://previous.iiasa.ac.at/web/home/research/researchPrograms/air/IR54-GAINS-CH4.pdf
        CH4 emissions can be separated in three categories : flaring,venting and unintended leakage
        emission_factor is in Mt/TWh
        '''
        emission_factor = self.techno_infos_dict['CH4_flaring_emission_factor'] + \
                          self.techno_infos_dict['CH4_venting_emission_factor'] + \
                          self.techno_infos_dict['CH4_unintended_leakage_emission_factor']

        self.production_detailed[f'{Methane.emission_name} ({self.mass_unit})'] = emission_factor * \
                                                                                  self.production_detailed[
                                                                                      f'{FossilTechno.energy_name} ({self.product_energy_unit})'].values
