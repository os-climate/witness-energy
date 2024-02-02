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
from energy_models.core.energy_ghg_emissions.energy_ghg_emissions_disc import EnergyGHGEmissionsDiscipline
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.energy_process_builder import INVEST_DISCIPLINE_OPTIONS
from energy_models.core.energy_study_manager import AGRI_TYPE
from energy_models.core.energy_study_manager import DEFAULT_COARSE_ENERGY_LIST, DEFAULT_COARSE_TECHNO_DICT, \
    DEFAULT_COARSE_CCS_LIST
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.sos_processes.energy.MDA.energy_mix_optim_sub_process.process import \
    ProcessBuilder as ProcessBuilderEnergyMixOptimSubProcessFull
from energy_models.sos_processes.energy.MDA.energy_process_v0.usecase import INVEST_DISC_NAME


class ProcessBuilder(ProcessBuilderEnergyMixOptimSubProcessFull):
    # ontology information
    _ontology_data = {
        'label': 'Energy Mix Coarse Optim sub process',
        'description': '',
        'category': '',
        'version': '',
    }

    def __init__(self, ee):
        super(ProcessBuilder, self).__init__(ee)
        self.techno_dict = DEFAULT_COARSE_TECHNO_DICT
        self.energy_list = DEFAULT_COARSE_ENERGY_LIST
        self.ccs_list = DEFAULT_COARSE_CCS_LIST

    def get_builders(self):

        ns_study = self.ee.study_name

        energy_mix = EnergyMix.name
        ccus_name = CCUS.name

        builder_list = []
        energy_builder_list = []
        # use energy list to import the builders
        for energy_name in self.energy_list:
            dot_list = energy_name.split('.')
            short_name = dot_list[-1]
            if self.techno_dict[energy_name]['type'] != AGRI_TYPE:
                energy_builder_list = self.ee.factory.get_builder_from_process(
                    'energy_models.sos_processes.energy.techno_mix',
                    f'{short_name}_mix',
                    techno_list=self.techno_dict[energy_name]['value'],
                    invest_discipline=self.invest_discipline,
                    associate_namespace=False,
                )

            builder_list.extend(energy_builder_list)

        ns_dict = {GlossaryEnergy.NS_WITNESS: ns_study}
        emissions_mod_dict = {
            EnergyGHGEmissionsDiscipline.name: 'energy_models.core.energy_ghg_emissions.energy_ghg_emissions_disc.EnergyGHGEmissionsDiscipline'
        }
        builder_emission_list = self.create_builder_list(emissions_mod_dict, ns_dict=ns_dict, associate_namespace=False)
        builder_list.extend(builder_emission_list)

        mods_dict = {
            energy_mix: 'energy_models.core.energy_mix.energy_mix_disc.Energy_Mix_Discipline',
            ccus_name: 'energy_models.core.ccus.ccus_disc.CCUS_Discipline',
        }

        builder_other_list = self.create_builder_list(mods_dict, ns_dict=ns_dict, associate_namespace=False)
        builder_list.extend(builder_other_list)

        if self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[1]:
            ns_dict = {}
            mods_dict = {
                INVEST_DISC_NAME: 'energy_models.core.investments.disciplines.one_invest_disc.OneInvestDiscipline',
            }

            builder_invest = self.create_builder_list(mods_dict, ns_dict=ns_dict, associate_namespace=False)
            builder_list.extend(builder_invest)

        elif self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[2]:
            ns_dict = {
                'ns_forest': f'{self.ee.study_name}.InvestmentDistribution',
                'ns_crop': f'{self.ee.study_name}.InvestmentDistribution',
                'ns_invest': f'{self.ee.study_name}.InvestmentDistribution',
            }
            if not self.energy_invest_input_in_abs_value:
                # add a discipline to handle correct investment split in case of mda (ie no optimizer to handle the split properly)
                mods_dict = {
                    INVEST_DISC_NAME: 'energy_models.core.investments.disciplines.investments_redistribution_disc.InvestmentsRedistributionDisicpline',
                }
            else:
                mods_dict = {
                    INVEST_DISC_NAME: 'energy_models.core.investments.disciplines.independent_invest_disc.IndependentInvestDiscipline',
                }

            builder_invest = self.create_builder_list(mods_dict, ns_dict=ns_dict, associate_namespace=False)
            builder_list.extend(builder_invest)
        else:
            raise Exception(
                f'Wrong option for invest_discipline : {self.invest_discipline} should be in {INVEST_DISCIPLINE_OPTIONS}'
            )

        for ccs_name in self.ccs_list:
            dot_list = ccs_name.split('.')
            short_name = dot_list[-1]
            proc_builder = self.ee.factory.get_pb_ist_from_process(
                'energy_models.sos_processes.energy.techno_mix', f'{short_name}_mix'
            )
            proc_builder.prefix_name = GlossaryEnergy.CCUS
            if hasattr(self, 'techno_dict') and hasattr(self, 'invest_discipline'):
                proc_builder.setup_process(
                    techno_list=self.techno_dict[ccs_name]['value'],
                    invest_discipline=self.invest_discipline,
                    associate_namespace=False,
                )
            energy_builder_list = proc_builder.get_builders()
            builder_list.extend(energy_builder_list)

        post_proc_mod = 'energy_models.sos_processes.post_processing.post_proc_energy_mix'
        self.ee.post_processing_manager.add_post_processing_module_to_namespace(
            GlossaryEnergy.NS_ENERGY_MIX, post_proc_mod
        )

        post_proc_mod = 'energy_models.sos_processes.post_processing.post_proc_technology_mix'
        self.ee.post_processing_manager.add_post_processing_module_to_namespace(
            GlossaryEnergy.NS_ENERGY_MIX, post_proc_mod
        )

        post_proc_mod = 'energy_models.sos_processes.post_processing.post_proc_stream_CO2_breakdown'
        for energy in self.energy_list:
            self.ee.post_processing_manager.add_post_processing_module_to_namespace(f'ns_{energy}', post_proc_mod)

        post_proc_mod = 'energy_models.sos_processes.post_processing.post_proc_capex_opex'
        for energy in self.energy_list:
            self.ee.post_processing_manager.add_post_processing_module_to_namespace(f'ns_{energy}', post_proc_mod)

        return builder_list
