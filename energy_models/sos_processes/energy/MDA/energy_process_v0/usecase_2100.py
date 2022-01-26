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

import numpy as np
import pandas as pd
import scipy.interpolate as sc


from energy_models.core.energy_mix.energy_mix import EnergyMix

from energy_models.core.stream_type.energy_models.gaseous_hydrogen import GaseousHydrogen
from energy_models.core.stream_type.energy_models.liquid_fuel import LiquidFuel
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.energy_models.biogas import BioGas
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.solid_fuel import SolidFuel
from energy_models.core.stream_type.energy_models.biodiesel import BioDiesel
from energy_models.core.stream_type.energy_models.syngas import Syngas
from energy_models.core.demand.demand_mix import DemandMix
from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
from energy_models.core.stream_type.energy_models.liquid_hydrogen import LiquidHydrogen
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.carbon_models.carbon_storage import CarbonStorage
from energy_models.core.energy_study_manager import EnergyStudyManager,\
    DEFAULT_TECHNO_DICT, CCUS_TYPE, ENERGY_TYPE
from energy_models.sos_processes.energy.techno_mix.carbon_capture_mix.usecase import DEFAULT_FLUE_GAS_LIST
from energy_models.core.stream_type.carbon_models.flue_gas import FlueGas
from energy_models.core.energy_process_builder import INVEST_DISCIPLINE_DEFAULT,\
    INVEST_DISCIPLINE_OPTIONS

DEFAULT_ENERGY_LIST = [Methane.name, GaseousHydrogen.name, BioGas.name,
                       Syngas.name, LiquidFuel.name, SolidFuel.name, BiomassDry.name, Electricity.name, BioDiesel.name, LiquidHydrogen.name]
DEFAULT_CCS_LIST = [CarbonCapture.name, CarbonStorage.name]
CCS_NAME = 'CCUS'
INVEST_DISC_NAME = 'InvestmentDistribution'


class Study(EnergyStudyManager):
    def __init__(self, year_start=2020, year_end=2100, time_step=1, lower_bound_techno=1.0e-6, upper_bound_techno=100., techno_dict=DEFAULT_TECHNO_DICT,
                 main_study=True, bspline=True, execution_engine=None, invest_discipline=INVEST_DISCIPLINE_DEFAULT):
        super().__init__(__file__, main_study=main_study,
                         execution_engine=execution_engine, techno_dict=techno_dict)
        self.year_start = year_start
        self.year_end = year_end
        self.time_step = time_step
        self.years = np.arange(self.year_start, self.year_end + 1)

        self.lower_bound_techno = lower_bound_techno
        self.upper_bound_techno = upper_bound_techno

        self.sub_study_dict = None
        self.sub_study_path_dict = None
        self.create_study_list()
        self.main_study = main_study

        self.dict_technos = {}
        self.bspline = bspline
        self.invest_discipline = invest_discipline

    def create_study_list(self):
        self.sub_study_dict = {}
        self.sub_study_path_dict = {}
        for energy in self.energy_list + self.ccs_list:
            cls, path = self.get_energy_mix_study_cls(energy)
            self.sub_study_dict[energy] = cls
            self.sub_study_path_dict[energy] = path

    def get_dv_arrays(self):
        invest_mix_dict = self.get_investments_mix()

        for energy in self.energy_list:
            self.update_dspace_with(
                energy, invest_mix_dict[energy].values, self.lower_bound_techno, self.upper_bound_techno)

    def get_investments_mix(self):

        # Invest from ref: WEI2020_DataUpdate_Oct2020
        # Take variation from 2015 to 2019 (2020 is a covid year)
        # And assume a variation per year with this
        # invest of ref are 1295-electricity_networks- crude oil (only liquid_fuel
        # is taken into account)

        # invest from WEI 2020 miss hydrogen
        invest_energy_mix_dict = {}
        invest_energy_mix_dict['years'] = self.years
        invest_energy_mix_dict[Electricity.name] = [
            449.0 * (1 - 0.003)**i for i in range(len(self.years))]

        invest_energy_mix_dict[BioGas.name] = [
            5.0 * (1 + 0.054)**i for i in range(len(self.years))]
        invest_energy_mix_dict[BiomassDry.name] = [
            5.0 * (1 + 0.054)**i for i in range(len(self.years))]
        invest_energy_mix_dict[Methane.name] = [
            188.0 * (1 - 0.039)**i for i in range(len(self.years))]
        # Guess was not in WEI for hydrogen
        invest_energy_mix_dict[GaseousHydrogen.name] = [
            2.0 * (1 + 0.03)**i for i in range(len(self.years))]
        # investment on refinery not in oil extraction !
        invest_energy_mix_dict[LiquidFuel.name] = [
            315.0 * (1 - 0.1374)**i for i in range(len(self.years))]
        invest_energy_mix_dict[SolidFuel.name] = [
            76.0 * (1 - 0.14365)**i for i in range(len(self.years))]
        invest_energy_mix_dict[BioDiesel.name] = [
            2.0 * (1 - 0.1)**i for i in range(len(self.years))]
        invest_energy_mix_dict[Syngas.name] = [
            20.0 * (1 + 0.01)**i for i in range(len(self.years))]
        invest_energy_mix_dict[LiquidHydrogen.name] = [
            0.4 + 0.0006 * i for i in range(len(self.years))]

        if self.bspline:
            for energy in self.energy_list:
                invest_energy_mix_dict[energy], _ = self.invest_bspline(
                    invest_energy_mix_dict[energy], len(self.years))

        energy_mix_invest_df = pd.DataFrame(invest_energy_mix_dict)

        return energy_mix_invest_df

        energy_mix_invest_df = pd.DataFrame(invest_energy_mix_dict)

        return energy_mix_invest_df

    def get_investments_ccs_mix(self):

        # Invest from ref: WEI2020_DataUpdate_Oct2020
        # Take variation from 2015 to 2019 (2020 is a covid year)
        # And assume a variation per year with this
        # invest of ref are 1295-electricity_networks- crude oil (only liquid_fuel
        # is taken into account)

        # invest from WEI 2020 miss hydrogen
        invest_ccs_mix_dict = {}
        l_ctrl = np.arange(0, 8)

        invest_ccs_mix_dict[CarbonCapture.name] = [
            2.0 + i for i in l_ctrl]
        invest_ccs_mix_dict[CarbonStorage.name] = [
            0.003 + 0.00025 * i for i in l_ctrl]

        if self.bspline:
            invest_ccs_mix_dict['years'] = self.years

            for ccs in self.ccs_list:
                invest_ccs_mix_dict[ccs], _ = self.invest_bspline(
                    invest_ccs_mix_dict[ccs], len(self.years))

        ccs_mix_invest_df = pd.DataFrame(invest_ccs_mix_dict)

        return ccs_mix_invest_df

    def get_total_mix(self, instanciated_studies, ccs_percentage):
        '''
        Get the total mix of each techno with the invest distribution discipline
         with ccs percentage, mixes by energy and by techno 
        '''
        energy_mix = self.get_investments_mix()
        invest_mix_df = pd.DataFrame({'years': energy_mix['years'].values})
        norm_energy_mix = energy_mix.drop(
            'years', axis=1).sum(axis=1).values

        if self.bspline:
            ccs_percentage_array = ccs_percentage['ccs_percentage'].values
        else:
            ccs_percentage_array = np.ones_like(norm_energy_mix) * 25.0

        ccs_mix = self.get_investments_ccs_mix()
        norm_ccs_mix = ccs_mix.drop(
            'years', axis=1).sum(axis=1)
        for study in instanciated_studies:
            invest_techno = study.get_investments()
            if 'years' in invest_techno.columns:
                norm_techno_mix = invest_techno.drop(
                    'years', axis=1).sum(axis=1)
            else:
                norm_techno_mix = invest_techno.sum(axis=1)
            energy = study.energy_name
            if energy in energy_mix.columns:
                mix_energy = energy_mix[energy].values / norm_energy_mix * \
                    (100.0 - ccs_percentage_array) / 100.0
            elif energy in ccs_mix.columns:
                mix_energy = ccs_mix[energy].values / norm_ccs_mix * \
                    ccs_percentage_array / 100.0
            else:
                raise Exception(f'{energy} not in investment_mixes')
            for techno in invest_techno.columns:
                if techno != 'years':
                    invest_mix_df[f'{energy}.{techno}'] = invest_techno[techno].values * \
                        mix_energy / norm_techno_mix

        return invest_mix_df

    def get_absolute_total_mix(self, instanciated_studies, ccs_percentage, energy_invest, energy_invest_factor):

        invest_mix_df = self.get_total_mix(
            instanciated_studies, ccs_percentage)

        indep_invest_df = pd.DataFrame(
            {'years': invest_mix_df['years'].values})

        energy_invest_poles = energy_invest['energy_investment'].values[[
            i for i in range(len(energy_invest['energy_investment'].values)) if i % 10 == 0]][0:-1]
        for column in invest_mix_df.columns:
            if column != 'years':
                indep_invest_df[column] = invest_mix_df[column].values * \
                    energy_invest_poles * energy_invest_factor

        return indep_invest_df

    def setup_usecase_sub_study_list(self):
        """
        Instantiate sub studies and values dict from setup_usecase
        """
        values_dict_list = []
        instanced_sub_studies = []
        dspace_list = []
        for sub_study_name, sub_study in self.sub_study_dict.items():
            if self.techno_dict[sub_study_name]['type'] == CCUS_TYPE:
                prefix_name = 'CCUS'
                instance_sub_study = sub_study(
                    self.year_start, self.year_end, self.time_step, bspline=self.bspline, main_study=False, prefix_name=prefix_name, execution_engine=self.execution_engine,
                    invest_discipline=self.invest_discipline, technologies_list=self.techno_dict[sub_study_name]['value'])
            elif self.techno_dict[sub_study_name]['type'] == ENERGY_TYPE:
                prefix_name = 'EnergyMix'
                instance_sub_study = sub_study(
                    self.year_start, self.year_end, self.time_step, bspline=self.bspline, main_study=False, execution_engine=self.execution_engine,
                    invest_discipline=self.invest_discipline, technologies_list=self.techno_dict[sub_study_name]['value'])
            else:
                raise Exception(
                    f"The type of {sub_study_name} : {self.techno_dict[sub_study_name]['type']} is not in [{ENERGY_TYPE},{CCUS_TYPE}]")

            instance_sub_study.configure_ds_boundaries(lower_bound_techno=self.lower_bound_techno,
                                                       upper_bound_techno=self.upper_bound_techno,)
            instance_sub_study.study_name = self.study_name
            data_dict = instance_sub_study.setup_usecase()
            values_dict_list.extend(data_dict)
            instanced_sub_studies.append(instance_sub_study)
            dspace_list.append(instance_sub_study.dspace)
        return values_dict_list, dspace_list,  instanced_sub_studies

    def create_technolist_per_energy(self, instanciated_studies):

        dict_studies = dict(zip(self.energy_list, instanciated_studies))

        for energy_name, study_val in dict_studies.items():
            self.dict_technos[energy_name] = study_val.technologies_list

    def setup_usecase(self):

        hydrogen_name = GaseousHydrogen.name
        liquid_fuel_name = LiquidFuel.name
        methane_name = Methane.name
        biogas_name = BioGas.name
        biomass_dry_name = BiomassDry.name
        electricity_name = Electricity.name
        solid_fuel_name = SolidFuel.name
        biodiesel_name = BioDiesel.name
        syngas_name = Syngas.name
        carbon_capture_name = CarbonCapture.name
        carbon_storage_name = CarbonStorage.name
        liquid_hydrogen_name = LiquidHydrogen.name
        demand_name = DemandMix.name
        energy_mix_name = EnergyMix.name

        # price in $/MWh
        self.energy_prices = pd.DataFrame({'years': self.years,
                                           electricity_name: np.linspace(90.0, 80.0, len(self.years)),
                                           biomass_dry_name: np.linspace(68.12 / 3.36, 68.12 / 3.36 / 2.0, len(self.years)),
                                           biogas_name: np.linspace(90, 75, len(self.years)),
                                           methane_name: np.linspace(34, 25, len(self.years)),
                                           solid_fuel_name: np.linspace(8.6, 7, len(self.years)),
                                           hydrogen_name: np.linspace(90, 80, len(self.years)),
                                           liquid_fuel_name: np.linspace(70, 60, len(self.years)),
                                           syngas_name: np.linspace(40.0, 30, len(self.years)),
                                           carbon_capture_name: 0.0,
                                           carbon_storage_name: 0.0,
                                           biodiesel_name: np.linspace(210.0, 210.0 / 2.0, len(self.years)),
                                           liquid_hydrogen_name: np.linspace(120.0, 120.0 / 2.0, len(self.years))})

        co2_taxes_year = [2018, 2020, 2025, 2030, 2035,
                          2040, 2045, 2050, 2060, 2070, 2080, 2090, 2100]
        co2_taxes = [14.86, 17.22, 20.27,
                     29.01,  34.05,   39.08,  44.69,   50.29, 60, 70, 80, 90, 100]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {'years': self.years, 'CO2_tax': func(self.years)})

        self.energy_carbon_emissions = pd.DataFrame(
            {'years': self.years, biomass_dry_name: - 0.425 * 44.01 / 12.0 / 3.36, solid_fuel_name: 0.64 / 4.86,
             electricity_name: 0.0, methane_name: 0.123 / 15.4, syngas_name: 0.0,
             hydrogen_name: 0.0, carbon_capture_name: 0.0, carbon_storage_name: 0.0,
             biogas_name: -0.618, liquid_hydrogen_name: 0.0})

        # Relax constraint for 15 first years
        self.CCS_constraint_factor = np.concatenate(
            (np.linspace(0.5, 0.5, 20), np.asarray([1.1] * (len(self.years) - 20))))

        #-- energy demand mix and total demand
        # all coeffs at 0 excepted electricity : 1
        self.energy_demand_mix = {}
        self.energy_demand_mix[f'{hydrogen_name}.energy_demand_mix'] = pd.DataFrame({'years': self.years,
                                                                                     'mix': np.zeros(len(self.years))})
        self.energy_demand_mix[f'{methane_name}.energy_demand_mix'] = pd.DataFrame({'years': self.years,
                                                                                    'mix': np.zeros(len(self.years))})
        self.energy_demand_mix[f'{biogas_name}.energy_demand_mix'] = pd.DataFrame({'years': self.years,
                                                                                   'mix': np.zeros(len(self.years))})
        self.energy_demand_mix[f'{biodiesel_name}.energy_demand_mix'] = pd.DataFrame({'years': self.years,
                                                                                      'mix': np.zeros(len(self.years))})
        self.energy_demand_mix[f'{electricity_name}.energy_demand_mix'] = pd.DataFrame({'years': self.years,
                                                                                        'mix': np.ones(len(self.years)) * 100.0})
        self.energy_demand_mix[f'{liquid_fuel_name}.energy_demand_mix'] = pd.DataFrame({'years': self.years,
                                                                                        'mix': np.zeros(len(self.years))})
        self.energy_demand_mix[f'{solid_fuel_name}.energy_demand_mix'] = pd.DataFrame({'years': self.years,
                                                                                       'mix': np.zeros(len(self.years))})
        self.energy_demand_mix[f'{syngas_name}.energy_demand_mix'] = pd.DataFrame({'years': self.years,
                                                                                   'mix': np.zeros(len(self.years))})
        self.energy_demand_mix[f'{biomass_dry_name}.energy_demand_mix'] = pd.DataFrame({'years': self.years,
                                                                                        'mix': np.zeros(len(self.years))})
        self.energy_demand_mix[f'{carbon_capture_name}.energy_demand_mix'] = pd.DataFrame({'years': self.years,
                                                                                           'mix': np.zeros(len(self.years))})
        self.energy_demand_mix[f'{carbon_storage_name}.energy_demand_mix'] = pd.DataFrame({'years': self.years,
                                                                                           'mix': np.zeros(len(self.years))})
        self.energy_demand_mix[f'{liquid_hydrogen_name}.energy_demand_mix'] = pd.DataFrame({'years': self.years,
                                                                                            'mix': np.zeros(len(self.years))})
        self.total_energy_demand = pd.DataFrame(
            {'years': self.years, 'demand': 25000 * np.linspace(1, 1.5, len(self.years))})  # 25679 TWh electricity prod in 2017 http://www.mineralinfo.fr/ecomine/production-mondiale-delectricite-empreinte-matiere-en-transition

        # init land surface for food for biomass dry crop energy
        land_surface_for_food = pd.DataFrame({'years': self.years,
                                              'Agriculture total (Gha)': np.ones(len(self.years)) * 4.8})

        # invest inputs
        energy_mix_invest_df = self.get_investments_mix()
        invest_ccs_mix = self.get_investments_ccs_mix()
        invest_ref = 1055.0    # G$
        invest = np.ones(len(self.years)) * invest_ref
        invest[0] = invest_ref
        for i in range(1, len(self.years)):
            invest[i] = (1.0 - 0.0253) * invest[i - 1]
        invest_df = pd.DataFrame(
            {'years': self.years, 'energy_investment': invest})
        scaling_factor_energy_investment = 100.0
        ccs_percentage = pd.DataFrame(
            {'years': self.years, 'ccs_percentage': 10.0})

        values_dict = {f'{self.study_name}.linearization_mode': 'adjoint',
                       f'{self.study_name}.sub_mda_class': 'MDANewtonRaphson',
                       f'{self.study_name}.{energy_mix_name}.invest_energy_mix': energy_mix_invest_df,
                       f'{self.study_name}.{CCS_NAME}.ccs_percentage': ccs_percentage,
                       f'{self.study_name}.{CCS_NAME}.invest_ccs_mix': invest_ccs_mix,
                       f'{self.study_name}.energy_investment': invest_df,
                       f'{self.study_name}.year_start': self.year_start,
                       f'{self.study_name}.year_end': self.year_end,
                       f'{self.study_name}.energy_list': self.energy_list,
                       f'{self.study_name}.energy_prices': self.energy_prices,
                       f'{self.study_name}.{energy_mix_name}.energy_prices': self.energy_prices,
                       f'{self.study_name}.land_surface_for_food_df': land_surface_for_food,
                       f'{self.study_name}.CO2_taxes': self.co2_taxes,
                       f'{self.study_name}.energy_CO2_emissions': self.energy_carbon_emissions,
                       f'{self.study_name}.{energy_mix_name}.energy_CO2_emissions': self.energy_carbon_emissions,
                       f'{self.study_name}.{demand_name}.total_energy_demand': self.total_energy_demand,
                       f'{self.study_name}.{energy_mix_name}.CCS_constraint_factor': self.CCS_constraint_factor,
                       f'{self.study_name}.{energy_mix_name}.{hydrogen_name}.energy_demand_mix': self.energy_demand_mix[f'{hydrogen_name}.energy_demand_mix'],
                       f'{self.study_name}.{energy_mix_name}.{methane_name}.energy_demand_mix': self.energy_demand_mix[f'{methane_name}.energy_demand_mix'],
                       f'{self.study_name}.{energy_mix_name}.{biogas_name}.energy_demand_mix': self.energy_demand_mix[f'{biogas_name}.energy_demand_mix'],
                       f'{self.study_name}.{energy_mix_name}.{biodiesel_name}.energy_demand_mix': self.energy_demand_mix[f'{biodiesel_name}.energy_demand_mix'],
                       f'{self.study_name}.{energy_mix_name}.{electricity_name}.energy_demand_mix': self.energy_demand_mix[f'{electricity_name}.energy_demand_mix'],
                       f'{self.study_name}.{energy_mix_name}.{liquid_fuel_name}.energy_demand_mix': self.energy_demand_mix[f'{liquid_fuel_name}.energy_demand_mix'],
                       f'{self.study_name}.{energy_mix_name}.{solid_fuel_name}.energy_demand_mix': self.energy_demand_mix[f'{solid_fuel_name}.energy_demand_mix'],
                       f'{self.study_name}.{energy_mix_name}.{syngas_name}.energy_demand_mix': self.energy_demand_mix[f'{syngas_name}.energy_demand_mix'],
                       f'{self.study_name}.{energy_mix_name}.{biomass_dry_name}.energy_demand_mix': self.energy_demand_mix[f'{biomass_dry_name}.energy_demand_mix'],
                       f'{self.study_name}.{CCS_NAME}.{carbon_capture_name}.energy_demand_mix': self.energy_demand_mix[f'{carbon_capture_name}.energy_demand_mix'],
                       f'{self.study_name}.{CCS_NAME}.{carbon_storage_name}.energy_demand_mix': self.energy_demand_mix[f'{carbon_storage_name}.energy_demand_mix'],
                       f'{self.study_name}.{energy_mix_name}.{liquid_hydrogen_name}.energy_demand_mix': self.energy_demand_mix[f'{liquid_hydrogen_name}.energy_demand_mix']
                       }

        values_dict_list, dspace_list, instanciated_studies = self.setup_usecase_sub_study_list(
        )

        # The flue gas list will depend on technologies present in the
        # techno_dict
        possible_technos = [f'{energy}.{techno}' for energy, tech_dict in self.techno_dict.items(
        ) for techno in tech_dict['value']]
        flue_gas_list = [
            techno for techno in DEFAULT_FLUE_GAS_LIST if techno in possible_technos]

        if CarbonCapture.name in DEFAULT_TECHNO_DICT:
            values_dict[f'{self.study_name}.{CCS_NAME}.{CarbonCapture.name}.{FlueGas.node_name}.technologies_list'] = flue_gas_list

        if self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[0]:
            energy_mix_invest_df = self.get_investments_mix()
            invest_ccs_mix = self.get_investments_ccs_mix()
            values_dict.update({f'{self.study_name}.{energy_mix_name}.invest_energy_mix': energy_mix_invest_df,
                                f'{self.study_name}.{CCS_NAME}.ccs_percentage': ccs_percentage,
                                f'{self.study_name}.{CCS_NAME}.invest_ccs_mix': invest_ccs_mix})

        # merge design spaces
            self.merge_design_spaces(dspace_list)
        elif self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[1]:

            invest_mix_df = self.get_total_mix(
                instanciated_studies, ccs_percentage)
            values_dict.update(
                {f'{self.study_name}.{INVEST_DISC_NAME}.invest_mix': invest_mix_df})

        elif self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[2]:

            invest_mix_df = self.get_absolute_total_mix(
                instanciated_studies, ccs_percentage, invest_df, scaling_factor_energy_investment)
            values_dict.update(
                {f'{self.study_name}.{INVEST_DISC_NAME}.invest_mix': invest_mix_df})

        # merge design spaces
        self.merge_design_spaces(dspace_list)

        values_dict_list.append(values_dict)

        if not self.main_study:
            self.get_dv_arrays()
            self.create_technolist_per_energy(instanciated_studies)

        return values_dict_list


if '__main__' == __name__:
    uc_cls = Study()
    uc_cls.load_data()
    uc_cls.execution_engine.display_treeview_nodes(display_variables=True)
    uc_cls.run()
