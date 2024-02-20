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

from sostrades_core.sos_processes.base_process_builder import BaseProcessBuilder
from energy_models.core.energy_process_builder import INVEST_DISCIPLINE_OPTIONS
from energy_asset_portfolio.glossary_eap import Glossary
from energy_models.models.carbon_storage.pure_carbon_solid_storage.pure_carbon_solid_storage import PureCarbonSS
from energy_models.sos_processes.energy.MDA.energy_process_v0.usecase import CCS_NAME, INVEST_DISC_NAME
from energy_models.sos_processes.witness_sub_process_builder import WITNESSSubProcessBuilder
from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from energy_models.core.stream_type.energy_models.heat import lowtemperatureheat
from energy_models.core.stream_type.energy_models.heat import mediumtemperatureheat
from energy_models.sos_processes.energy.techno_mix.hightemperatureheat_mix.usecase import \
    TECHNOLOGIES_LIST_DEV as hightemperatureheat_technos_dev
from energy_models.sos_processes.energy.techno_mix.lowtemperatureheat_mix.usecase import \
    TECHNOLOGIES_LIST_DEV as lowtemperatureheat_technos_dev
from energy_models.sos_processes.energy.techno_mix.mediumtemperatureheat_mix.usecase import \
    TECHNOLOGIES_LIST_DEV as mediumtemperatureheat_technos_dev
from energy_models.core.energy_study_manager import AGRI_TYPE, ENERGY_TYPE

DEFAULT_TECHNO_DICT = {
                       hightemperatureheat.name: {'type': ENERGY_TYPE, 'value': hightemperatureheat_technos_dev},
                       mediumtemperatureheat.name: {'type': ENERGY_TYPE, 'value': mediumtemperatureheat_technos_dev},
                       lowtemperatureheat.name: {'type': ENERGY_TYPE, 'value': lowtemperatureheat_technos_dev},
                       }

class ProcessBuilder(WITNESSSubProcessBuilder):
    # ontology information
    _ontology_data = {
        'label': 'Heat mix disc',
        'description': '',
        'category': '',
        'version': '',
    }

    def get_builder_with_associated_ns(self,
                                       disc_name,
                                       disc_mod,
                                       ns_to_associate,
                                       ):
        """
        Utility function to get a builder after performing shared namespace association for it
        :param disc_name: short name of the discipline
        :param disc_mod: discipline class module
        :param ns_to_associate: dict ns_name: ns_value for the shared namespaces to associate to the builder
        :return: SoSBuilder of the discipline
        """
        ns_ids_list = list(map(self.ee.ns_manager.add_ns,
                               ns_to_associate.keys(),
                               ns_to_associate.values()))
        disc_builder = self.ee.factory.get_builder_from_module(disc_name,
                                                               disc_mod)
        disc_builder.associate_namespaces(ns_ids_list)
        return disc_builder

    def get_builders(self):
        energy_mix = 'EnergyMix'
        ns_study = self.ee.study_name
        func_manager_name = "FunctionManagerDisc"
        # declare technology name: discipline module
        # technos_mods = {
        #     Glossary.GasTurbineTechnology:
        #         "energy_asset_portfolio.models.electricity_models.gas_turbine.gas_turbine_disc.GasTurbineDiscipline",
        #     Glossary.CCGasTurbineTechnology:
        #         "energy_asset_portfolio.models.electricity_models.cc_gas_turbine.cc_gas_turbine_disc.CCGasTurbineDiscipline",
        #     Glossary.NuclearTechnology:
        #         "energy_asset_portfolio.models.electricity_models.nuclear.nuclear_disc.NuclearDiscipline",
        #     Glossary.SolarPVTechnology:
        #         "energy_asset_portfolio.models.electricity_models.solar_pv.solar_pv_disc.SolarPVDiscipline",
        #     Glossary.WindOnshoreTechnology:
        #         "energy_asset_portfolio.models.electricity_models.wind_onshore.wind_onshore_disc.WindOnshoreDiscipline",
        #     Glossary.WindOffshoreTechnology:
        #         "energy_asset_portfolio.models.electricity_models.wind_offshore.wind_offshore_disc.WindOffshoreDiscipline",
        #     Glossary.CoalFiredTechnology:
        #         "energy_asset_portfolio.models.electricity_models.coal_fired.coal_fired_disc.CoalFiredDiscipline",
        # }

        # process-constant namespaces
        ns_public_value = self.ee.study_name
        ns_mix_value = f"{self.ee.study_name}.{energy_mix}"

        # ns_dict = {Glossary.NS_MIX_NAME: ns_mix_value,
        #            Glossary.NS_PUBLIC_NAME: ns_public_value,
        #            Glossary.NS_FUNCTIONS: ns_mix_value
        #            }

        ns_dict = {'ns_functions': f'{ns_study}.{func_manager_name}',
                   'ns_energy': f'{ns_study}',
                   'ns_energy_study': f'{ns_study}',
                   'ns_public': f'{ns_study}',
                   'ns_resource': f'{ns_study}',
                   'ns_energy_mix': f'{ns_study}.{energy_mix}',
                   'ns_ref': f'{ns_study}.NormalizationReferences',
                   'ns_invest': f'{self.ee.study_name}.InvestmentDistribution',
                   'ns_witness': f'{ns_study}'}


        # asset mix
        mods_dict = {
            energy_mix: 'energy_models.core.heat_mix.heat_mix_disc.Heat_Mix_Discipline',
        }

        builder_list = self.create_builder_list(
            mods_dict, ns_dict=ns_dict)

        self.energy_list = DEFAULT_TECHNO_DICT
        # use energy list to import the builders
        self.techno_dict = self.energy_list
        for energy_name in self.energy_list:
            dot_list = energy_name.split('.')
            short_name = dot_list[-1]
            if self.techno_dict[energy_name]['type'] != AGRI_TYPE:
                energy_builder_list = self.ee.factory.get_builder_from_process(
                    'energy_models.sos_processes.energy.techno_mix', f'{short_name}_mix',
                    techno_list=self.techno_dict[energy_name]['value'],
                    associate_namespace=False
                )

            builder_list.extend(energy_builder_list)


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

        # append builders of technos with associated namespaces

        # for techno, techno_mod in technos_mods.items():
        #     disc_name = f"{asset_mix}.{techno}"
        #     disc_full_name = f"{ns_mix_value}.{techno}"
        #     builder_list.append(self.get_builder_with_associated_ns(disc_name=disc_name,
        #                                                             disc_mod=techno_mod,
        #                                                             ns_to_associate={
        #                                                                 Glossary.NS_ASSET_NAME: disc_full_name}))

        return builder_list
