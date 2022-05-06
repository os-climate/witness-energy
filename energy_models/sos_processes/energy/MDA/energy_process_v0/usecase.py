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

from energy_models.core.energy_study_manager import AGRI_TYPE, EnergyStudyManager,\
    DEFAULT_TECHNO_DICT, CCUS_TYPE, ENERGY_TYPE
from sos_trades_core.tools.post_processing.post_processing_factory import PostProcessingFactory
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.models.carbon_storage.pure_carbon_solid_storage.pure_carbon_solid_storage import PureCarbonSS

from energy_models.core.stream_type.energy_models.gaseous_hydrogen import GaseousHydrogen
from energy_models.core.stream_type.energy_models.liquid_fuel import LiquidFuel
from energy_models.core.stream_type.energy_models.hydrotreated_oil_fuel import HydrotreatedOilFuel
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.energy_models.biogas import BioGas
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.solid_fuel import SolidFuel
from energy_models.core.stream_type.energy_models.biodiesel import BioDiesel
from energy_models.core.stream_type.energy_models.syngas import Syngas
from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
from energy_models.core.stream_type.energy_models.liquid_hydrogen import LiquidHydrogen
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.carbon_models.carbon_storage import CarbonStorage

from sos_trades_core.execution_engine.func_manager.func_manager_disc import FunctionManagerDisc
from sos_trades_core.execution_engine.func_manager.func_manager import FunctionManager


from energy_models.core.stream_type.energy_models.renewable import Renewable
from energy_models.core.stream_type.energy_models.fossil import Fossil
from energy_models.core.stream_type.carbon_models.flue_gas import FlueGas
from energy_models.sos_processes.energy.techno_mix.carbon_capture_mix.usecase import DEFAULT_FLUE_GAS_LIST
from energy_models.core.energy_process_builder import INVEST_DISCIPLINE_DEFAULT,\
    INVEST_DISCIPLINE_OPTIONS
from energy_models.core.stream_type.resources_data_disc import get_static_CO2_emissions, get_static_prices
from climateeconomics.sos_processes.iam.witness.resources_process.usecase import Study as datacase_resource
from energy_models.core.demand.energy_demand_disc import EnergyDemandDiscipline


CCS_NAME = 'CCUS'
OBJECTIVE = FunctionManagerDisc.OBJECTIVE
INEQ_CONSTRAINT = FunctionManagerDisc.INEQ_CONSTRAINT
EQ_CONSTRAINT = FunctionManagerDisc.EQ_CONSTRAINT
OBJECTIVE_LAGR = FunctionManagerDisc.OBJECTIVE_LAGR
AGGR_TYPE = FunctionManagerDisc.AGGR_TYPE
AGGR_TYPE_SMAX = FunctionManager.AGGR_TYPE_SMAX
AGGR_TYPE_SUM = FunctionManager.AGGR_TYPE_SUM
AGGR_TYPE_DELTA = FunctionManager.AGGR_TYPE_DELTA
FUNC_DF = FunctionManagerDisc.FUNC_DF
CO2_TAX_MINUS_CCS_CONSTRAINT_DF = EnergyMix.CO2_TAX_MINUS_CCS_CONSTRAINT_DF
CARBON_TO_BE_STORED_CONSTRAINT = PureCarbonSS.CARBON_TO_BE_STORED_CONSTRAINT
TOTAL_PROD_MINUS_MIN_PROD_CONSTRAINT_DF = EnergyMix.TOTAL_PROD_MINUS_MIN_PROD_CONSTRAINT_DF
INVEST_DISC_NAME = 'InvestmentDistribution'
hydropower_name = Electricity.hydropower_name


class Study(EnergyStudyManager):
    def __init__(self, year_start=2020, year_end=2050, time_step=1, lower_bound_techno=1.0e-6, upper_bound_techno=100., techno_dict=DEFAULT_TECHNO_DICT,
                 main_study=True, bspline=True, execution_engine=None, invest_discipline=INVEST_DISCIPLINE_DEFAULT):
        self.year_start = year_start
        self.year_end = year_end
        self.time_step = time_step
        self.years = np.arange(self.year_start, self.year_end + 1)

        if invest_discipline == INVEST_DISCIPLINE_OPTIONS[2]:
            self.lower_bound_techno = 1.0e-6
            self.upper_bound_techno = 3000.0

        else:
            self.lower_bound_techno = lower_bound_techno
            self.upper_bound_techno = upper_bound_techno
        self.sub_study_dict = None
        self.sub_study_path_dict = None

        #-- Call class constructor after attributes have been set for setup_process usage
        # EnergyStudyManager init will compute energy_list and ccs_list with
        # the techno_dict
        super().__init__(__file__, main_study=main_study,
                         execution_engine=execution_engine, techno_dict=techno_dict)

        self.create_study_list()
        self.bspline = bspline
        self.invest_discipline = invest_discipline

    def create_study_list(self):
        self.sub_study_dict = {}
        self.sub_study_path_dict = {}
        for energy in self.energy_list + self.ccs_list:
            cls, path = self.get_energy_mix_study_cls(energy)
            self.sub_study_dict[energy] = cls
            self.sub_study_path_dict[energy] = path

    def setup_objectives(self):

        func_df = pd.DataFrame(
            columns=['variable', 'parent', 'ftype', 'weight', AGGR_TYPE])
        list_var = []
        list_parent = []
        list_ftype = []
        list_weight = []
        list_aggr_type = []
        list_ns = []
        #-- add objectives to func_manager
        list_var.extend([f'energy_production_objective',
                         'syngas_prod_objective'])
        list_parent.extend(['objectives',
                            'objectives'])
        list_ftype.extend([OBJECTIVE,  OBJECTIVE])
        if Syngas.name in self.energy_list:
            list_weight.extend([0.,  0.])
        else:
            list_weight.extend([0., 0.])
        list_aggr_type.extend(
            [AGGR_TYPE_SUM,  AGGR_TYPE_SUM])
        list_ns.extend(['ns_functions',
                        'ns_functions'])

        if self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[2]:
            list_var.extend(['invest_objective', 'invest_objective_sum'])
            list_parent.extend(['objectives', 'objectives'])
            list_ftype.extend([OBJECTIVE, OBJECTIVE])
            list_weight.extend([0.0, 0.0])
            list_aggr_type.extend([AGGR_TYPE_SUM, AGGR_TYPE_SUM])
            list_ns.extend(['ns_functions', 'ns_functions'])

        func_df['variable'] = list_var
        func_df['parent'] = list_parent
        func_df['ftype'] = list_ftype
        func_df['weight'] = list_weight
        func_df[AGGR_TYPE] = list_aggr_type
        func_df['namespace'] = list_ns
        return func_df

    def setup_constraints(self):

        func_df = pd.DataFrame(
            columns=['variable', 'parent', 'ftype', 'weight', AGGR_TYPE])
        list_var = []
        list_parent = []
        list_ftype = []
        list_weight = []
        list_aggr_type = []
        list_namespaces = []

        if LiquidFuel.name in self.energy_list and GaseousHydrogen.name in self.energy_list and LiquidHydrogen.name in self.energy_list:
            list_var.append('primary_energies_production')
            list_parent.append('Energy_constraints')
            list_ftype.append(INEQ_CONSTRAINT)
            list_weight.append(0.)
            list_aggr_type.append(
                AGGR_TYPE_SMAX)
            list_namespaces.append('ns_functions')

        if GaseousHydrogen.name in self.energy_list:
            if 'PlasmaCracking' in self.dict_technos[GaseousHydrogen.name]:
                list_var.extend(
                    [CARBON_TO_BE_STORED_CONSTRAINT])
                list_parent.extend(['Carbon_to_be_stored_constraints'])
                list_ftype.extend([INEQ_CONSTRAINT])
                list_weight.extend([0.])
                list_aggr_type.append(
                    AGGR_TYPE_SMAX)
                list_namespaces.append('ns_functions')

        if CarbonStorage.name in self.ccs_list:
            list_var.extend(
                ['carbon_storage_constraint'])
            list_parent.extend([''])
            list_ftype.extend([INEQ_CONSTRAINT])
            list_weight.extend([0.])
            list_aggr_type.append(
                AGGR_TYPE_SMAX)
            list_namespaces.append('ns_functions')

        list_var.extend(
            [TOTAL_PROD_MINUS_MIN_PROD_CONSTRAINT_DF])
        list_parent.extend(['Energy_constraints'])
        list_ftype.extend([INEQ_CONSTRAINT])
        list_weight.extend([-1.])
        list_aggr_type.append(
            AGGR_TYPE_SMAX)
        list_namespaces.append('ns_functions')

        if Electricity.name in self.energy_list:
            if hydropower_name in self.dict_technos[Electricity.name]:
                list_var.extend(
                    ['prod_hydropower_constraint'])
                list_parent.extend(['Energy_constraints'])
                list_ftype.extend([INEQ_CONSTRAINT])
                list_weight.extend([-1.])
                list_aggr_type.append(
                    AGGR_TYPE_SMAX)
                list_namespaces.append('ns_functions')

        if SolidFuel.name in self.energy_list:
            list_var.extend(
                ['total_prod_solid_fuel_elec'])
            list_parent.extend(['Energy_constraints'])
            list_ftype.extend([INEQ_CONSTRAINT])
            list_weight.extend([0.])
            list_aggr_type.append(
                AGGR_TYPE_SMAX)
            list_namespaces.append('ns_functions')

        if LiquidHydrogen.name in self.energy_list:
            list_var.extend(
                ['total_prod_h2_liquid'])
            list_parent.extend(['Energy_constraints'])
            list_ftype.extend([INEQ_CONSTRAINT])
            list_weight.extend([0.])
            list_aggr_type.append(
                AGGR_TYPE_SMAX)
            list_namespaces.append('ns_functions')

        if Syngas.name in self.energy_list:
            list_var.extend(
                ['syngas_prod_constraint'])
            list_parent.extend(['Energy_constraints'])
            list_ftype.extend([INEQ_CONSTRAINT])
            list_weight.extend([-1.0])
            list_aggr_type.append(
                AGGR_TYPE_SMAX)
            list_namespaces.append('ns_functions')

        if self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[2]:
            list_var.extend(
                ['invest_constraint', 'invest_sum_cons', 'invest_sum_cons_dc', 'invest_sum_eq_cons'])
            list_parent.extend(['invests_constraints', 'invests_constraints', 'invests_constraints', 'invests_constraints'])
            list_ftype.extend([INEQ_CONSTRAINT, INEQ_CONSTRAINT, INEQ_CONSTRAINT, EQ_CONSTRAINT])
            list_weight.extend([0., -1.0, 0., 0.])
            list_aggr_type.extend(
                [AGGR_TYPE_SMAX, AGGR_TYPE_SMAX, AGGR_TYPE_SMAX, AGGR_TYPE_DELTA])
            list_namespaces.extend(['ns_functions', 'ns_functions', 'ns_functions', 'ns_functions'])

        if set(EnergyDemandDiscipline.energy_constraint_list).issubset(self.energy_list):

            list_var.extend(
                ['electricity_demand_constraint','transport_demand_constraint'])
            list_parent.extend(['demand_constraint', 'demand_constraint'])
            list_ftype.extend([INEQ_CONSTRAINT, INEQ_CONSTRAINT])
            list_weight.extend([-1., -1.])
            list_aggr_type.extend(
                [AGGR_TYPE_SUM, AGGR_TYPE_SUM])
            list_namespaces.extend(['ns_functions', 'ns_functions'])

        func_df['variable'] = list_var
        func_df['parent'] = list_parent
        func_df['ftype'] = list_ftype
        func_df['weight'] = list_weight
        func_df[AGGR_TYPE] = list_aggr_type
        func_df['namespace'] = list_namespaces

        return func_df

    def update_dv_arrays(self):
        """
        Update design variable arrays
        """
        invest_mix_dict = self.get_investments_mix_custom()
        invest_ccs_mix_dict = self.get_investments_ccs_mix_custom()

        for energy in self.energy_list:
            energy_wo_dot = energy.replace('.', '_')
            self.update_dspace_dict_with(
                f'{energy}.{energy_wo_dot}_array_mix',
                list(np.maximum(self.lower_bound_techno,
                                invest_mix_dict[energy].values)),
                self.lower_bound_techno, self.upper_bound_techno)

        for ccs in self.ccs_list:
            ccs_wo_dot = ccs.replace('.', '_')
            self.update_dspace_dict_with(
                f'{ccs}.{ccs_wo_dot}_array_mix',
                list(np.maximum(self.lower_bound_techno,
                                invest_ccs_mix_dict[ccs].values)),
                self.lower_bound_techno, self.upper_bound_techno)

        dim_a = 8

        activated_elem_list = [False] + 7 * [True]

        ccs_percentage = np.array([0, 1, 1, 1, 1, 1, 1, 1])
        lbnd1 = [0.0] * dim_a
        ubnd1 = [50.0] * dim_a  # Maximum 20% of investment into ccs
        self.update_dspace_dict_with(
            'ccs_percentage_array', list(ccs_percentage), lbnd1, ubnd1, activated_elem=activated_elem_list)

    def update_dv_arrays_technos(self, invest_mix_df):
        """
        Update design variable arrays for all technologies in the case where we have only one investment discipline
        """
        invest_mix_df_wo_years = invest_mix_df.drop(
            'years', axis=1)
        for column in invest_mix_df_wo_years.columns:
            techno_wo_dot = column.replace('.', '_')
            self.update_dspace_dict_with(
                f'{column}.{techno_wo_dot}_array_mix', np.minimum(np.maximum(
                    self.lower_bound_techno, invest_mix_df_wo_years[column].values), self.upper_bound_techno),
                self.lower_bound_techno, self.upper_bound_techno)

    def get_investments_mix(self):

        # Invest from ref: WEI2020_DataUpdate_Oct2020
        # Take variation from 2015 to 2019 (2020 is a covid year)
        # And assume a variation per year with this
        # invest of ref are 1295-electricity_networks- crude oil (only liquid_fuel
        # is taken into account)

        # invest from WEI 2020 miss hydrogen
        invest_energy_mix_dict = {}
        l_ctrl = np.arange(0, 8)
        invest_energy_mix_dict['years'] = l_ctrl

        invest_energy_mix_dict[Electricity.name] = [
            4.490 + 0.4 * i for i in l_ctrl]

        invest_energy_mix_dict[BioGas.name] = [
            0.05 * (1 + 0.054)**i for i in l_ctrl]
        invest_energy_mix_dict[BiomassDry.name] = [
            0.003 + 0.00025 * i for i in l_ctrl]
        invest_energy_mix_dict[Methane.name] = np.linspace(
            1.2, 0.5, len(l_ctrl)).tolist()
        invest_energy_mix_dict[GaseousHydrogen.name] = [
            0.02 * (1 + 0.03)**i for i in l_ctrl]
        # investment on refinery not in oil extraction !
        invest_energy_mix_dict[LiquidFuel.name] = [
            3.15 * (1 - 0.1374)**i for i in l_ctrl]
        invest_energy_mix_dict[SolidFuel.name] = [
            0.00001, 0.0006] + [0.00005] * (len(l_ctrl) - 2)
        invest_energy_mix_dict[BioDiesel.name] = [
            0.02 * (1 - 0.1)**i for i in l_ctrl]
        invest_energy_mix_dict[Syngas.name] = [
            1.0050 + 0.02 * i for i in l_ctrl]
        invest_energy_mix_dict[LiquidHydrogen.name] = [
            0.4 + 0.0006 * i for i in l_ctrl]

        if self.bspline:

            invest_energy_mix_dict['years'] = self.years
            for energy in self.energy_list:
                invest_energy_mix_dict[energy], _ = self.invest_bspline(
                    invest_energy_mix_dict[energy], len(self.years))

        energy_mix_invest_df = pd.DataFrame(invest_energy_mix_dict)

        return energy_mix_invest_df

    def get_investments_mix_custom(self):
        """
        put a X0 tested on optim subprocess that satisfy all constraints
        """

        # Invest from ref: WEI2020_DataUpdate_Oct2020
        # Take variation from 2015 to 2019 (2020 is a covid year)
        # And assume a variation per year with this
        # invest of ref are 1295-electricity_networks- crude oil (only liquid_fuel
        # is taken into account)

        # invest from WEI 2020 miss hydrogen
        invest_energy_mix_dict = {}
        years = np.arange(0, 8)
        invest_energy_mix_dict['years'] = years
        invest_energy_mix_dict[Electricity.name] = [
            4.49, 35, 35, 35, 35, 35, 35, 35]
        invest_energy_mix_dict[BioGas.name] = [
            0.05, 2.0, 1.8, 1.3, 1.0, 0.1, 0.01, 0.01]
        invest_energy_mix_dict[BiomassDry.name] = [
            0.003, 0.5, 1.0, 1.0, 1.0, 0.8, 0.8, 0.8]
        invest_energy_mix_dict[Methane.name] = [
            1.2, 0.5, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0]
        invest_energy_mix_dict[GaseousHydrogen.name] = [
            0.02, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        # investment on refinery not in oil extraction !
        invest_energy_mix_dict[LiquidFuel.name] = [
            3.15, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        invest_energy_mix_dict[SolidFuel.name] = [
            0.00001, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01]
        invest_energy_mix_dict[BioDiesel.name] = [
            0.02, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        invest_energy_mix_dict[Syngas.name] = [
            1.005, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        invest_energy_mix_dict[LiquidHydrogen.name] = [
            0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        invest_energy_mix_dict[Renewable.name] = np.linspace(
            1.0, 15.625, len(years))
        invest_energy_mix_dict[Fossil.name] = np.linspace(
            100, 77.5, len(years))
        invest_energy_mix_dict[HydrotreatedOilFuel.name] = [
            3.15, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        if self.bspline:
            invest_energy_mix_dict['years'] = self.years

            for energy in self.energy_list:
                invest_energy_mix_dict[energy], _ = self.invest_bspline(
                    invest_energy_mix_dict[energy], len(self.years))

        energy_mix_invest_df = pd.DataFrame(
            {key: value for key, value in invest_energy_mix_dict.items() if key in self.energy_list or key == 'years'})

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
        invest_ccs_mix_dict['years'] = l_ctrl
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

    def get_investments_ccs_mix_custom(self):

        # Invest from ref: WEI2020_DataUpdate_Oct2020
        # Take variation from 2015 to 2019 (2020 is a covid year)
        # And assume a variation per year with this
        # invest of ref are 1295-electricity_networks- crude oil (only liquid_fuel
        # is taken into account)

        # invest from WEI 2020 miss hydrogen
        invest_ccs_mix_dict = {}
        invest_ccs_mix_dict['years'] = np.arange(0, 8)

        invest_ccs_mix_dict[CarbonCapture.name] = [
            2.0, 25, 25, 25, 25, 25, 25, 25]
        invest_ccs_mix_dict[CarbonStorage.name] = [0.003, 5, 5, 5, 5, 5, 5, 5]

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
        energy_mix = self.get_investments_mix_custom()
        invest_mix_df = pd.DataFrame({'years': energy_mix['years'].values})
        norm_energy_mix = energy_mix.drop(
            'years', axis=1).sum(axis=1).values

        if self.bspline:
            ccs_percentage_array = ccs_percentage['ccs_percentage'].values
        else:
            ccs_percentage_array = np.ones_like(norm_energy_mix) * 25.0

        ccs_mix = self.get_investments_ccs_mix_custom()
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

        energy_invest_poles = energy_invest['energy_investment'].values[[i for i in range(
            len(energy_invest['energy_investment'].values)) if i % 10 == 0]][0:-1]
        for column in invest_mix_df.columns:
            if column != 'years':
                if len(invest_mix_df['years'].values) == len(energy_invest_poles):
                    indep_invest_df[column] = invest_mix_df[column].values * \
                        energy_invest_poles * \
                        energy_invest_factor
                else:
                    indep_invest_df[column] = invest_mix_df[column].values * \
                        energy_invest['energy_investment'].values * \
                        energy_invest_factor

        return indep_invest_df

    def get_co2_taxes_df(self):

        co2_taxes = np.asarray([50.] * len(self.years))
        co2_taxes_df = pd.DataFrame(
            {'years': self.years, 'CO2_tax': co2_taxes}, index=self.years)

        return co2_taxes_df

    def get_co2_taxes_df_custom(self):

        co2_taxes = np.linspace(750, 750, len(self.years))
        co2_taxes_df = pd.DataFrame(
            {'years': self.years, 'CO2_tax': co2_taxes}, index=self.years)

        return co2_taxes_df

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
            elif self.techno_dict[sub_study_name]['type'] == AGRI_TYPE:
                pass
            else:
                raise Exception(
                    f"The type of {sub_study_name} : {self.techno_dict[sub_study_name]['type']} is not in [{ENERGY_TYPE},{CCUS_TYPE},{AGRI_TYPE}]")
            if self.techno_dict[sub_study_name]['type'] != AGRI_TYPE:
                instance_sub_study.configure_ds_boundaries(lower_bound_techno=self.lower_bound_techno,
                                                        upper_bound_techno=self.upper_bound_techno,)
                instance_sub_study.study_name = self.study_name
                data_dict = instance_sub_study.setup_usecase()
                values_dict_list.extend(data_dict)
                instanced_sub_studies.append(instance_sub_study)
                dspace_list.append(instance_sub_study.dspace)
        return values_dict_list, dspace_list,  instanced_sub_studies

    def create_technolist_per_energy(self, instanciated_studies):
        self.dict_technos = {}
        dict_studies = dict(
            zip(self.energy_list + self.ccs_list, instanciated_studies))

        for energy_name, study_val in dict_studies.items():
            self.dict_technos[energy_name] = study_val.technologies_list

    def setup_usecase(self):

        hydrogen_name = GaseousHydrogen.name
        liquid_fuel_name = LiquidFuel.name
        hvo_name = HydrotreatedOilFuel.name
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

        renewable_name = Renewable.name
        fossil_name = Fossil.name
        energy_mix_name = EnergyMix.name
        energy_price_dict = {'years': self.years,
                             electricity_name: 9.0,
                             biomass_dry_name: 68.12 / 3.36,
                             biogas_name: 90,
                             methane_name:  34.0,
                             solid_fuel_name: 8.6,
                             hydrogen_name: 90.0,
                             liquid_fuel_name: 70.0,
                             syngas_name: 40.0,
                             carbon_capture_name: 0.0,
                             carbon_storage_name: 0.0,
                             biodiesel_name: 210.0,
                             liquid_hydrogen_name: 120.0,
                             renewable_name: 90.0,
                             fossil_name: 110.0,
                             hvo_name: 70.0,
                             }

        # price in $/MWh
        self.energy_prices = pd.DataFrame({key: value for key, value in energy_price_dict.items(
        ) if key in self.techno_dict or key == 'years'})

        self.co2_taxes = self.get_co2_taxes_df_custom()

        energy_carbon_emissions_dict = {'years': self.years,
                                        electricity_name: 0.0,
                                        biomass_dry_name: - 0.425 * 44.01 / 12.0 / 3.36,
                                        biogas_name: -0.618,
                                        methane_name:  0.123 / 15.4,
                                        solid_fuel_name: 0.64 / 4.86,
                                        hydrogen_name:  0.0,
                                        liquid_fuel_name: 0.0,
                                        syngas_name: 0.0,
                                        carbon_capture_name: 0.0,
                                        carbon_storage_name: 0.0,
                                        biodiesel_name: 0.0,
                                        liquid_hydrogen_name: 0.0,
                                        renewable_name: 0.0,
                                        fossil_name: 0.64 / 4.86,
                                        hvo_name: 0.0,
                                        }
        # price in $/MWh
        self.energy_carbon_emissions = pd.DataFrame(
            {key: value for key, value in energy_carbon_emissions_dict.items() if key in self.techno_dict or key == 'years'})

        #--- resources price and co2 emissions
        self.resources_CO2_emissions = get_static_CO2_emissions(self.years)
        self.resources_prices = get_static_prices(self.years)

        demand_ratio_dict = dict(
            zip(self.energy_list, np.ones((len(self.years), len(self.years)))*100.))
        demand_ratio_dict['years'] = self.years

        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)

        ratio_available_resource_dict = dict(
            zip(EnergyMix.RESOURCE_LIST, np.ones((len(self.years), len(self.years)))*100.))
        ratio_available_resource_dict['years'] = self.years
        self.all_resource_ratio_usable_demand = pd.DataFrame(
            ratio_available_resource_dict)

        invest_ref = 10.55    # 100G$
        invest = np.ones(len(self.years)) * invest_ref
        invest[0] = invest_ref
        for i in range(1, len(self.years)):
            invest[i] = (1.0 - 0.0253) * invest[i - 1]
        invest_df = pd.DataFrame(
            {'years': self.years, 'energy_investment': invest})
        invest_df.index = self.years
        scaling_factor_energy_investment = 100.0
        # init land surface for food for biomass dry crop energy
        land_surface_for_food = pd.DataFrame({'years': self.years,
                                              'Agriculture total (Gha)': np.ones(len(self.years)) * 4.8})

        ccs_percentage = pd.DataFrame(
            {'years': self.years, 'ccs_percentage': 25.0})
        co2_emissions_from_energy_mix = pd.DataFrame(
            {'years': self.years, 'carbon_capture from energy mix (Mt)': 25.0})

        population_df = pd.DataFrame(
            {"years": self.years, "population": np.linspace(7886.69358, 9000., len(self.years))})
        transport_demand=pd.DataFrame({'years': self.years,
                                'transport_demand': np.linspace(33600., 30000., len(self.years))})
        values_dict = {f'{self.study_name}.energy_investment': invest_df,
                       f'{self.study_name}.year_start': self.year_start,
                       f'{self.study_name}.year_end': self.year_end,
                       f'{self.study_name}.energy_list': self.energy_list,
                       f'{self.study_name}.ccs_list': self.ccs_list,
                       f'{self.study_name}.energy_prices': self.energy_prices,
                       f'{self.study_name}.{energy_mix_name}.energy_prices': self.energy_prices,
                       f'{self.study_name}.land_surface_for_food_df': land_surface_for_food,
                       f'{self.study_name}.CO2_taxes': self.co2_taxes,
                       f'{self.study_name}.energy_CO2_emissions': self.energy_carbon_emissions,
                       f'{self.study_name}.scaling_factor_energy_investment': scaling_factor_energy_investment,
                       f'{self.study_name}.{energy_mix_name}.energy_CO2_emissions': self.energy_carbon_emissions,
                       f'{self.study_name}.{energy_mix_name}.all_streams_demand_ratio': self.all_streams_demand_ratio,
                       f'{self.study_name}.{energy_mix_name}.all_resource_ratio_usable_demand': self.all_resource_ratio_usable_demand,
                       f'{self.study_name}.{energy_mix_name}.co2_emissions_from_energy_mix': co2_emissions_from_energy_mix,
                       f'{self.study_name}.is_stream_demand': True,
                       f'{self.study_name}.max_mda_iter': 200,
                       f'{self.study_name}.sub_mda_class': 'MDAGaussSeidel',
                       f'{self.study_name}.NormalizationReferences.liquid_hydrogen_percentage': np.concatenate((np.ones(5) * 1e-4, np.ones(len(self.years) - 5) / 4), axis=None),
                       f'{self.study_name}.{energy_mix_name}.resources_CO2_emissions': self.resources_CO2_emissions,
                       f'{self.study_name}.{energy_mix_name}.resources_price': self.resources_prices,
                       f'{self.study_name}.population_df': population_df,
                       f'{self.study_name}.Energy_demand.transport_demand' : transport_demand,
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

        # IF coarse process no need of heat loss percentage (raw prod is net prod)
        # IF renewable and fossil in energy_list then coarse process
        if renewable_name in self.energy_list and fossil_name in self.energy_list:
            values_dict.update(
                {f'{self.study_name}.EnergyMix.heat_losses_percentage': 0.0})
        if self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[0]:
            energy_mix_invest_df = self.get_investments_mix_custom()
            invest_ccs_mix = self.get_investments_ccs_mix_custom()
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
            self.update_dv_arrays_technos(invest_mix_df)
        elif self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[2]:

            invest_mix_df = self.get_absolute_total_mix(
                instanciated_studies, ccs_percentage, invest_df, scaling_factor_energy_investment)
            values_dict.update(
                {f'{self.study_name}.{INVEST_DISC_NAME}.invest_mix': invest_mix_df})
            self.update_dv_arrays_technos(invest_mix_df)

        values_dict_list.append(values_dict)

        # if not self.main_study:
        if self.invest_discipline == INVEST_DISCIPLINE_OPTIONS[0]:
            self.update_dv_arrays()
        self.create_technolist_per_energy(instanciated_studies)

        #-- load data from resource

        dc_resource = datacase_resource(
            self.year_start, self.year_end)
        dc_resource.study_name = self.study_name
        resource_input_list = dc_resource.setup_usecase()
        values_dict_list.extend(resource_input_list)
        return values_dict_list


if '__main__' == __name__:
    uc_cls = Study()
    uc_cls.load_data()
    # uc_cls.execution_engine.display_treeview_nodes(display_variables=True)
    print(len(uc_cls.execution_engine.root_process.sos_disciplines))
    uc_cls.run()

    # ppf = PostProcessingFactory()
    # for disc in uc_cls.execution_engine.root_process.sos_disciplines:
    #     filters = ppf.get_post_processing_filters_by_discipline(
    #         disc)
    #     graph_list = ppf.get_post_processing_by_discipline(
    #         disc, filters, as_json=False)
    #     if disc.sos_name == 'EnergyMix.fuel':
    #         for graph in graph_list:
    #             graph.to_plotly().show()
