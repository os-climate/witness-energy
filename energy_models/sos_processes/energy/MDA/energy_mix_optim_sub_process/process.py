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
from climateeconomics.sos_wrapping.sos_wrapping_emissions.ghgemissions.ghgemissions_discipline import (
    GHGemissionsDiscipline,
)

from energy_models.core.energy_ghg_emissions.energy_ghg_emissions_disc import (
    EnergyGHGEmissionsDiscipline,
)
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.energy_process_builder import INVEST_DISCIPLINE_OPTIONS
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.carbon_storage.pure_carbon_solid_storage.pure_carbon_solid_storage import (
    PureCarbonSS,
)
from energy_models.sos_processes.energy.MDA.energy_process_v0.usecase import (
    INVEST_DISC_NAME,
)
from energy_models.sos_processes.techno_dict.data.techno_dicts import techno_dict_midway
from energy_models.sos_processes.witness_sub_process_builder import (
    WITNESSSubProcessBuilder,
)


class ProcessBuilder(WITNESSSubProcessBuilder):
    # ontology information
    _ontology_data = {
        'label': 'Energy Mix Optim sub process',
        'description': '',
        'category': '',
        'version': '',
    }

    def __init__(self, ee):
        super(ProcessBuilder, self).__init__(ee)
        self.invest_discipline = INVEST_DISCIPLINE_OPTIONS[2]
        self.techno_dict = techno_dict_midway

    def get_builders(self):
        coupling_name = "MDA"
        designvariable_name = "DesignVariables"
        func_manager_name = "FunctionsManager"
        ns_study = self.ee.study_name
        energy_mix = EnergyMix.name
        carbon_storage = PureCarbonSS.energy_name

        builder_list = []

        # ---------------------------------------------
        for energy_name in self.energy_list:
            dot_list = energy_name.split('.')
            short_name = dot_list[-1]
            if self.techno_dict[energy_name]['type'] != GlossaryEnergy.agriculture_type:
                energy_builder_list = self.ee.factory.get_builder_from_process(
                    'energy_models.sos_processes.energy.techno_mix',
                    f'{short_name}_mix',
                    techno_list=self.techno_dict[energy_name]['value'],
                    invest_discipline=self.invest_discipline,
                    associate_namespace=False,
                )

                builder_list.extend(energy_builder_list)

        # ---------------------------------------------
        for ccs_name in self.ccs_list:
            dot_list = ccs_name.split('.')
            short_name = dot_list[-1]
            proc_builder = self.ee.factory.get_pb_ist_from_process(
                'energy_models.sos_processes.energy.techno_mix', f'{short_name}_mix'
            )
            proc_builder.prefix_name = GlossaryEnergy.ccus_type
            if hasattr(self, 'techno_dict') and hasattr(self, 'invest_discipline'):
                proc_builder.setup_process(
                    techno_list=self.techno_dict[ccs_name]['value'],
                    invest_discipline=self.invest_discipline,
                    associate_namespace=False,
                )
            energy_builder_list = proc_builder.get_builders()
            builder_list.extend(energy_builder_list)

        self.ee.ns_manager.update_namespace_list_with_extra_ns(coupling_name,
                                                               after_name=self.ee.study_name,
                                                               clean_existing=False)


        # ---------------------------------------------
        mods_dict = {
            energy_mix: 'energy_models.core.energy_mix.energy_mix_disc.Energy_Mix_Discipline',
            GlossaryEnergy.ccus_type: 'energy_models.core.ccus.ccus_disc.CCUS_Discipline',
        }

        ns_dict = {
            GlossaryEnergy.NS_FUNCTIONS: f'{self.ee.study_name}.{coupling_name}.{func_manager_name}',
            'ns_energy': f'{ns_study}.{energy_mix}',
            GlossaryEnergy.NS_ENERGY_MIX: f'{ns_study}.{coupling_name}.{energy_mix}',
            'ns_carb': f'{ns_study}.{coupling_name}.{GlossaryEnergy.ccus_type}.{carbon_storage}.PureCarbonSolidStorage',
            'ns_resource': f'{ns_study}',
            GlossaryEnergy.NS_REFERENCE: f'{ns_study}.NormalizationReferences',
            'ns_invest': f'{self.ee.study_name}.InvestmentDistribution',
        }

        builder_other_list = self.create_builder_list(mods_dict, ns_dict=ns_dict, associate_namespace=False)
        builder_list.extend(builder_other_list)

        # ---------------------------------------------
        ns_dict = {
            GlossaryEnergy.NS_FUNCTIONS: f'{self.ee.study_name}.{coupling_name}.{func_manager_name}',
            'ns_energy': f'{ns_study}.{energy_mix}',
            GlossaryEnergy.NS_ENERGY_MIX: f'{ns_study}.{coupling_name}.{energy_mix}',
            'ns_carb': f'{ns_study}.{coupling_name}.{GlossaryEnergy.ccus_type}.{carbon_storage}.PureCarbonSolidStorage',
            'ns_resource': f'{ns_study}',
            GlossaryEnergy.NS_REFERENCE: f'{ns_study}.NormalizationReferences',
            'ns_invest': f'{self.ee.study_name}.InvestmentDistribution',
            GlossaryEnergy.NS_GHGEMISSIONS: f'{self.ee.study_name}.{coupling_name}.{GHGemissionsDiscipline.name}',
        }

        emissions_mod_dict = {
            GHGemissionsDiscipline.name: 'climateeconomics.sos_wrapping.sos_wrapping_emissions.ghgemissions.ghgemissions_discipline.GHGemissionsDiscipline',
            EnergyGHGEmissionsDiscipline.name: 'energy_models.core.energy_ghg_emissions.energy_ghg_emissions_disc.EnergyGHGEmissionsDiscipline'
        }
        builder_emission_list = self.create_builder_list(emissions_mod_dict, ns_dict=ns_dict, associate_namespace=False)
        builder_list.extend(builder_emission_list)

        # ---------------------------------------------
        if self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[1]:
            ns_dict = {
                'ns_public': f'{ns_study}',
                'ns_energy_study': f'{ns_study}',
                GlossaryEnergy.NS_WITNESS: f'{ns_study}.{coupling_name}',
                'ns_energy': f'{ns_study}.{energy_mix}',
                GlossaryEnergy.NS_CCS: f'{ns_study}.{coupling_name}.{GlossaryEnergy.ccus_type}',
            }
            mods_dict = {
                INVEST_DISC_NAME: 'energy_models.core.investments.disciplines.one_invest_disc.OneInvestDiscipline',
            }

            builder_invest = self.create_builder_list(mods_dict, ns_dict=ns_dict, associate_namespace=False)
            builder_list.extend(builder_invest)

        elif self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[2]:
            ns_dict = {
                'ns_public': f'{ns_study}',
                'ns_energy_study': f'{ns_study}',
                'ns_emissions': f'{ns_study}',
                'ns_energy': f'{ns_study}',
                GlossaryEnergy.NS_WITNESS: f'{ns_study}.{coupling_name}',
                GlossaryEnergy.NS_CCS: f'{ns_study}.{coupling_name}.{GlossaryEnergy.ccus_type}',
                GlossaryEnergy.NS_REFERENCE: f'{ns_study}.{energy_mix}.{carbon_storage}.NormalizationReferences',
                GlossaryEnergy.NS_FUNCTIONS: f'{self.ee.study_name}.{coupling_name}.{func_manager_name}',
                'ns_forest': f"{ns_study}.{coupling_name}.{INVEST_DISC_NAME}",
                'ns_crop': f"{ns_study}.{coupling_name}.{INVEST_DISC_NAME}",
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

        # ---------------------------------------------

        """
        if len(set(FuelDiscipline.fuel_list).intersection(set(self.energy_list))) > 0:
            ns_dict = {'ns_fuel': f'{ns_study}.{coupling_name}.{energy_mix}.fuel'}
            mods_dict = {
                f'{energy_mix}.{FuelDiscipline.name}': 'energy_models.core.stream_type.energy_disciplines.fuel_disc.FuelDiscipline',
            }

            builder_fuel = self.create_builder_list(mods_dict, ns_dict=ns_dict, associate_namespace=False)
            builder_list.extend(builder_fuel)

        """
        ns_dict = {'ns_energy': f'{ns_study}.{coupling_name}.{energy_mix}',
                   'ns_emissions': f'{ns_study}.{energy_mix}',
                   'ns_land_use': f'{self.ee.study_name}.EnergyMix',
                   GlossaryEnergy.NS_FUNCTIONS: f'{self.ee.study_name}.{coupling_name}.{func_manager_name}',
                   GlossaryEnergy.NS_REFERENCE: f'{self.ee.study_name}.NormalizationReferences',
                   'ns_invest': f'{self.ee.study_name}.{coupling_name}.{INVEST_DISC_NAME}'}

        self.ee.ns_manager.add_ns_def(ns_dict)


        # ---------------------------------------------
        # design variables builder
        design_var_path = 'sostrades_core.execution_engine.design_var.design_var_disc.DesignVarDiscipline'
        design_var_builder = self.ee.factory.get_builder_from_module(
            f'{designvariable_name}', design_var_path)
        builder_list.append(design_var_builder)

        # function manager builder
        fmanager_path = 'sostrades_core.execution_engine.func_manager.func_manager_disc.FunctionManagerDisc'
        fmanager_builder = self.ee.factory.get_builder_from_module(
            f'{func_manager_name}', fmanager_path)
        builder_list.append(fmanager_builder)

        ns_dict = {GlossaryEnergy.NS_FUNCTIONS: f'{self.ee.study_name}.{coupling_name}.{func_manager_name}',
                   'ns_public': f'{self.ee.study_name}',
                   'ns_optim': f'{self.ee.study_name}',
                   GlossaryEnergy.NS_REFERENCE: f'{self.ee.study_name}.NormalizationReferences',
                   'ns_invest': f'{self.ee.study_name}.{coupling_name}.{INVEST_DISC_NAME}', }
        self.ee.ns_manager.add_ns_def(ns_dict)

        # ---------------------------------------------

        # create coupling builder
        coupling_builder = self.ee.factory.create_builder_coupling(coupling_name)
        coupling_builder.set_builder_info('cls_builder', builder_list)

        return coupling_builder
