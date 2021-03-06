'''
Copyright 2022 Airbus SAS

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

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.ccus.ccus import CCUS

from energy_models.models.carbon_storage.pure_carbon_solid_storage.pure_carbon_solid_storage import PureCarbonSS
from energy_models.core.stream_type.energy_disciplines.fuel_disc import FuelDiscipline
from energy_models.sos_processes.energy.MDA.energy_process_v0.usecase import CCS_NAME, INVEST_DISC_NAME
from energy_models.sos_processes.witness_sub_process_builder import WITNESSSubProcessBuilder
from energy_models.core.energy_process_builder import INVEST_DISCIPLINE_OPTIONS
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.demand.energy_demand_disc import EnergyDemandDiscipline
from energy_models.core.energy_ghg_emissions.energy_ghg_emissions_disc import EnergyGHGEmissionsDiscipline


class ProcessBuilder(WITNESSSubProcessBuilder):

    # ontology information
    _ontology_data = {
        'label': 'Energy v0 Process',
        'description': '',
        'category': '',
        'version': '',
    }

    def get_builders(self):

        ns_study = self.ee.study_name

        energy_mix = EnergyMix.name
        ccus_name = CCUS.name
        func_manager_name = "FunctionManagerDisc"

        carbon_storage = PureCarbonSS.energy_name
        builder_list = []
        # use energy list to import the builders

        for energy_name in self.energy_list:
            dot_list = energy_name.split('.')
            short_name = dot_list[-1]
            energy_builder_list = self.ee.factory.get_builder_from_process('energy_models.sos_processes.energy.techno_mix', f'{short_name}_mix',
                                                                           techno_list=self.techno_dict[energy_name]['value'], invest_discipline=self.invest_discipline)

            builder_list.extend(energy_builder_list)

        # Needed namespaces for the 3 disciplines below
        # All other namespaces are specified in each subprocess
        ns_dict = {'ns_functions': f'{ns_study}.{func_manager_name}',
                   'ns_energy': f'{ns_study}',
                   'ns_energy_mix': f'{ns_study}.{energy_mix}',
                   'ns_carb':  f'{ns_study}.{energy_mix}.{carbon_storage}.PureCarbonSolidStorage',
                   'ns_resource': f'{ns_study}.{energy_mix}.resource',
                   'ns_ref': f'{ns_study}.NormalizationReferences',
                   'ns_invest': f'{self.ee.study_name}.InvestmentDistribution'}

        if self.process_level == 'dev':
            emissions_mod_dict = {
                EnergyGHGEmissionsDiscipline.name: 'energy_models.core.energy_ghg_emissions.energy_ghg_emissions_disc.EnergyGHGEmissionsDiscipline'}
        else:
            emissions_mod_dict = {
                'consumptionco2': 'energy_models.core.consumption_CO2_emissions.consumption_CO2_emissions_disc.ConsumptionCO2EmissionsDiscipline'}
        builder_emission_list = self.create_builder_list(
            emissions_mod_dict, ns_dict=ns_dict)
        builder_list.extend(builder_emission_list)

        # Add demand, energymix and resources discipline

        mods_dict = {energy_mix: 'energy_models.core.energy_mix.energy_mix_disc.Energy_Mix_Discipline',
                     ccus_name: 'energy_models.core.ccus.ccus_disc.CCUS_Discipline'
                     }

        builder_other_list = self.create_builder_list(
            mods_dict, ns_dict=ns_dict)
        builder_list.extend(builder_other_list)
        chain_builders_resource = self.ee.factory.get_builder_from_process(
            'climateeconomics.sos_processes.iam.witness', 'resources_process')
        builder_list.extend(chain_builders_resource)

        if self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[0]:
            ns_dict = {'ns_public': f'{ns_study}',
                       'ns_energy_study': f'{ns_study}',
                       'ns_emissions': f'{ns_study}',
                       'ns_ccs': f'{ns_study}.{CCS_NAME}',
                       }
            mods_dict = {
                energy_mix: 'energy_models.core.investments.disciplines.energy_invest_disc.InvestEnergyDiscipline',
            }

            builder_invest = self.create_builder_list(
                mods_dict, ns_dict=ns_dict)
            builder_list.extend(builder_invest)

            mods_dict = {
                energy_mix: 'energy_models.core.investments.disciplines.energy_or_ccs_invest_disc.InvestCCSorEnergyDiscipline',
            }

            builder_invest = self.create_builder_list(mods_dict, ns_dict={})
            builder_list.extend(builder_invest)

            ns_dict = {'ns_public': f'{ns_study}',
                       'ns_energy_study': f'{ns_study}'}
            mods_dict = {
                CCS_NAME: 'energy_models.core.investments.disciplines.ccs_invest_disc.InvestCCSDiscipline',
            }

            builder_invest = self.create_builder_list(
                mods_dict, ns_dict=ns_dict)
            builder_list.extend(builder_invest)

        elif self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[1]:
            ns_dict = {'ns_public': f'{ns_study}',
                       'ns_energy_study': f'{ns_study}',
                       'ns_witness': f'{ns_study}',
                       'ns_ccs': f'{ns_study}.{CCS_NAME}'}
            mods_dict = {
                INVEST_DISC_NAME: 'energy_models.core.investments.disciplines.one_invest_disc.OneInvestDiscipline',
            }

            builder_invest = self.create_builder_list(
                mods_dict, ns_dict=ns_dict)
            builder_list.extend(builder_invest)

        elif self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[2]:
            ns_dict = {'ns_public': f'{ns_study}',
                       'ns_energy_study': f'{ns_study}',
                       'ns_emissions': f'{ns_study}',
                       'ns_witness': f'{ns_study}',
                       'ns_ccs': f'{ns_study}.{CCS_NAME}',
                       'ns_ref': f'{ns_study}.{energy_mix}.{carbon_storage}.NormalizationReferences',
                       'ns_functions': f'{ns_study}.{func_manager_name}', }
            mods_dict = {
                INVEST_DISC_NAME: 'energy_models.core.investments.disciplines.independent_invest_disc.IndependentInvestDiscipline',
            }

            builder_invest = self.create_builder_list(
                mods_dict, ns_dict=ns_dict)
            builder_list.extend(builder_invest)
        else:
            raise Exception(
                f'Wrong option for invest_discipline : {self.invest_discipline} should be in {INVEST_DISCIPLINE_OPTIONS}')

        for ccs_name in self.ccs_list:
            dot_list = ccs_name.split('.')
            short_name = dot_list[-1]
            proc_builder = self.ee.factory.get_pb_ist_from_process(
                'energy_models.sos_processes.energy.techno_mix', f'{short_name}_mix')
            proc_builder.prefix_name = 'CCUS'
            if hasattr(self, 'techno_dict') and hasattr(self, 'invest_discipline'):
                proc_builder.setup_process(
                    techno_list=self.techno_dict[ccs_name]['value'], invest_discipline=self.invest_discipline)
            energy_builder_list = proc_builder.get_builders()
            builder_list.extend(energy_builder_list)

        for energy in self.energy_list:
            if energy == 'hydrogen.gaseous_hydrogen':
                self.ee.post_processing_manager.add_post_processing_module_to_namespace(
                    f'ns_hydrogen',
                    'energy_models.sos_processes.post_processing.post_proc_stream_CO2_breakdown')
            if energy == 'hydrogen.liquid_hydrogen':
                self.ee.post_processing_manager.add_post_processing_module_to_namespace(
                    f'ns_liquid_hydrogen',
                    'energy_models.sos_processes.post_processing.post_proc_stream_CO2_breakdown')
            self.ee.post_processing_manager.add_post_processing_module_to_namespace(
                f'ns_{energy}',
                'energy_models.sos_processes.post_processing.post_proc_stream_CO2_breakdown')

        if len(set(FuelDiscipline.fuel_list).intersection(set(self.energy_list))) > 0:
            ns_dict = {'ns_fuel': f'{ns_study}.{energy_mix}.fuel'}
            mods_dict = {
                f'{energy_mix}.{FuelDiscipline.name}': 'energy_models.core.stream_type.energy_disciplines.fuel_disc.FuelDiscipline',
            }

            builder_fuel = self.create_builder_list(mods_dict, ns_dict=ns_dict)
            builder_list.extend(builder_fuel)

        # For now only electricity demand constraint is available in the energy
        # demand discipline
        if set(EnergyDemandDiscipline.energy_constraint_list).issubset(self.energy_list):
            mods_dict = {
                EnergyDemandDiscipline.name: 'energy_models.core.demand.energy_demand_disc.EnergyDemandDiscipline',
            }

            builder_demand = self.create_builder_list(
                mods_dict, ns_dict=ns_dict)
            builder_list.extend(builder_demand)
        return builder_list
