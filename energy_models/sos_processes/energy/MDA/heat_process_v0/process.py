'''
Copyright 2024 Capgemini

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

from energy_models.core.ccus.ccus import CCUS
from energy_models.core.demand.energy_demand_disc import EnergyDemandDiscipline
from energy_models.core.energy_ghg_emissions.energy_ghg_emissions_disc import EnergyGHGEmissionsDiscipline
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.energy_process_builder import INVEST_DISCIPLINE_OPTIONS
from energy_models.core.energy_study_manager import AGRI_TYPE
from energy_models.core.stream_type.energy_disciplines.fuel_disc import FuelDiscipline
from energy_models.core.stream_type.energy_disciplines.heat_disc import HeatDiscipline
from energy_models.models.carbon_storage.pure_carbon_solid_storage.pure_carbon_solid_storage import PureCarbonSS
from energy_models.sos_processes.energy.MDA.energy_process_v0.usecase import CCS_NAME, INVEST_DISC_NAME
from energy_models.sos_processes.witness_sub_process_builder import WITNESSSubProcessBuilder
from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from energy_models.core.stream_type.energy_models.heat import lowtemperatureheat
from energy_models.core.stream_type.energy_models.heat import mediumtemperatureheat
from energy_models.sos_processes.energy.heat_techno_mix.hightemperatureheat_mix.usecase import \
    TECHNOLOGIES_LIST_DEV as hightemperatureheat_technos_dev
from energy_models.sos_processes.energy.heat_techno_mix.lowtemperatureheat_mix.usecase import \
    TECHNOLOGIES_LIST_DEV as lowtemperatureheat_technos_dev
from energy_models.sos_processes.energy.heat_techno_mix.mediumtemperatureheat_mix.usecase import \
    TECHNOLOGIES_LIST_DEV as mediumtemperatureheat_technos_dev
from energy_models.core.energy_study_manager import AGRI_TYPE, ENERGY_TYPE
from energy_models.sos_processes.energy.techno_mix.methane_mix.usecase import \
    TECHNOLOGIES_LIST_DEV as Methane_technos_dev
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.sos_processes.energy.techno_mix.electricity_mix.usecase import \
    TECHNOLOGIES_LIST_DEV as Electricity_technos_dev
from energy_models.core.stream_type.energy_models.electricity import Electricity
DEFAULT_TECHNO_DICT = {
                       # Electricity.name: {'type': ENERGY_TYPE, 'value': Electricity_technos_dev},
                       # Methane.name: {'type': ENERGY_TYPE, 'value': Methane_technos_dev},
                       hightemperatureheat.name: {'type': ENERGY_TYPE, 'value': hightemperatureheat_technos_dev},
                       mediumtemperatureheat.name: {'type': ENERGY_TYPE, 'value': mediumtemperatureheat_technos_dev},
                       lowtemperatureheat.name: {'type': ENERGY_TYPE, 'value': lowtemperatureheat_technos_dev},
                       }

class ProcessBuilder(WITNESSSubProcessBuilder):
    # ontology information
    _ontology_data = {
        'label': 'Heat v0 Process',
        'description': '',
        'category': '',
        'version': '',
    }

    def get_builders(self):

        ns_study = self.ee.study_name

        energy_mix = 'HeatMix' #EnergyMix.name
        ccus_name = CCUS.name
        func_manager_name = "FunctionManagerDisc"

        carbon_storage = PureCarbonSS.energy_name
        builder_list = []

        self.energy_list = DEFAULT_TECHNO_DICT
        # use energy list to import the builders
        for energy_name in self.energy_list:
            dot_list = energy_name.split('.')
            short_name = dot_list[-1]
            if self.techno_dict[energy_name]['type'] != AGRI_TYPE:
                energy_builder_list = self.ee.factory.get_builder_from_process(
                    'energy_models.sos_processes.energy.heat_techno_mix', f'{short_name}_mix',
                    techno_list=self.techno_dict[energy_name]['value'], invest_discipline=self.invest_discipline,
                    associate_namespace=False
                )

            builder_list.extend(energy_builder_list)

        # Needed namespaces for the 3 disciplines below
        # All other namespaces are specified in each subprocess
        ns_dict = {'ns_functions': f'{ns_study}.{func_manager_name}',
                   'ns_energy': f'{ns_study}',
                   'ns_energy_mix': f'{ns_study}.{energy_mix}',
                   'ns_carb': f'{ns_study}.{energy_mix}.{carbon_storage}.PureCarbonSolidStorage',
                   # 'ns_resource': f'{ns_study}.{energy_mix}.resource',
                   'ns_ref': f'{ns_study}.NormalizationReferences',
                   'ns_invest': f'{self.ee.study_name}.InvestmentDistribution',
                   'ns_witness': f'{ns_study}'}

        # Add demand, energymix and resources discipline

        # mods_dict = {energy_mix: 'energy_models.core.energy_mix.energy_mix_disc.Energy_Mix_Discipline',
        #              }

        # mods_dict = {energy_mix: 'energy_models.core.energy_mix.energy_mix_disc.Energy_Mix_Discipline',
        #              }
        mods_dict = {energy_mix: 'energy_models.core.heat_mix.heat_mix_disc.Heat_Mix_Discipline',
                     }
        builder_other_list = self.create_builder_list(
            mods_dict, ns_dict=ns_dict, associate_namespace=False)
        builder_list.extend(builder_other_list)
        # chain_builders_resource = self.ee.factory.get_builder_from_process(
        #     'climateeconomics.sos_processes.iam.witness', 'resources_process', associate_namespace=False)
        # builder_list.extend(chain_builders_resource)

        if self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[1]:
            ns_dict = {'ns_public': f'{ns_study}',
                       'ns_energy_study': f'{ns_study}',
                       'ns_witness': f'{ns_study}',
                       'ns_energy': f'{ns_study}.{energy_mix}',
                       'ns_ccs': f'{ns_study}.{CCS_NAME}'}
            mods_dict = {
                INVEST_DISC_NAME: 'energy_models.core.investments.disciplines.one_invest_disc.OneInvestDiscipline',
            }

            builder_invest = self.create_builder_list(
                mods_dict, ns_dict=ns_dict, associate_namespace=False)
            builder_list.extend(builder_invest)

        return builder_list