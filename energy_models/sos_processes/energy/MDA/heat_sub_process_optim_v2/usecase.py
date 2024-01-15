import pandas as pd
import numpy as np

from sostrades_core.study_manager.study_manager import StudyManager
from energy_models.sos_processes.energy.MDA.heat_process_v0.usecase import Study as UCHeatMix
from sostrades_core.execution_engine.func_manager.func_manager_disc import FunctionManagerDisc
from sostrades_core.execution_engine.design_var.design_var_disc import DesignVarDiscipline
from sostrades_core.execution_engine.func_manager.func_manager import FunctionManager
# from energy_asset_portfolio.sos_processes.portfolio_optim_subprocess.process import ProcessBuilder as OptSubProc
from energy_models.core.energy_process_builder import INVEST_DISCIPLINE_DEFAULT, INVEST_DISCIPLINE_OPTIONS
from energy_models.sos_processes.witness_heat_sub_process_builder import WITNESSSubProcessBuilder as OptSubProc
from energy_asset_portfolio.glossary_eap import Glossary
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.core.energy_study_manager import ENERGY_TYPE, EnergyStudyManager
from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from energy_models.core.stream_type.energy_models.heat import lowtemperatureheat
from energy_models.core.stream_type.energy_models.heat import mediumtemperatureheat
from energy_models.sos_processes.energy.techno_mix.hightemperatureheat_mix.usecase import \
    TECHNOLOGIES_LIST_DEV as hightemperatureheat_technos_dev
from energy_models.sos_processes.energy.techno_mix.lowtemperatureheat_mix.usecase import \
    TECHNOLOGIES_LIST_DEV as lowtemperatureheat_technos_dev
from energy_models.sos_processes.energy.techno_mix.mediumtemperatureheat_mix.usecase import \
    TECHNOLOGIES_LIST_DEV as mediumtemperatureheat_technos_dev
DEFAULT_TECHNO_DICT = {
                       hightemperatureheat.name: {'type': ENERGY_TYPE, 'value': hightemperatureheat_technos_dev},
                       mediumtemperatureheat.name: {'type': ENERGY_TYPE, 'value': mediumtemperatureheat_technos_dev},
                       lowtemperatureheat.name: {'type': ENERGY_TYPE, 'value': lowtemperatureheat_technos_dev},
                       }



OBJECTIVE = FunctionManagerDisc.OBJECTIVE
INEQ_CONSTRAINT = FunctionManagerDisc.INEQ_CONSTRAINT
EQ_CONSTRAINT = FunctionManagerDisc.EQ_CONSTRAINT
OBJECTIVE_LAGR = FunctionManagerDisc.OBJECTIVE_LAGR
FUNC_DF = FunctionManagerDisc.FUNC_DF
AGGR_TYPE = FunctionManagerDisc.AGGR_TYPE
AGGR_TYPE_SUM = FunctionManager.AGGR_TYPE_SUM
AGGR_TYPE_SMAX = FunctionManager.AGGR_TYPE_SMAX


class Study(EnergyStudyManager):

    def __init__(self, year_start=2020, year_end=2050, time_step=1, lower_bound_techno=1.0e-6, upper_bound_techno=100.,
                 techno_dict=DEFAULT_TECHNO_DICT,
                 main_study=True, bspline=True, execution_engine=None, invest_discipline=INVEST_DISCIPLINE_DEFAULT,
                 energy_invest_input_in_abs_value=True, this_process=True):
        self.year_start = year_start
        self.year_end = year_end
        self.time_step = time_step
        self.years = np.arange(self.year_start, self.year_end + 1)
        
        if invest_discipline == INVEST_DISCIPLINE_OPTIONS[2]:
            self.lower_bound_techno = 1.0e-6
            self.upper_bound_techno = 3000

        else:
            self.lower_bound_techno = lower_bound_techno
            self.upper_bound_techno = upper_bound_techno
        self.sub_study_dict = None
        self.sub_study_path_dict = None

        self.energy_list = list(DEFAULT_TECHNO_DICT.keys()) # [hightemperatureheat.name, mediumtemperatureheat.name, lowtemperatureheat.name]
        
        super().__init__(__file__, main_study=main_study,
                         execution_engine=execution_engine, techno_dict=techno_dict)

        self.create_study_list()
        self.bspline = bspline
        self.invest_discipline = invest_discipline
        self.energy_invest_input_in_abs_value = energy_invest_input_in_abs_value
        
        if this_process:
            # to allow using the study with a modified process like 4t1a
            super().__init__(__file__, execution_engine=execution_engine)
            #self.coupling_name = OptSubProc.COUPLING_NAME
            self.heat_mix_uc = UCHeatMix()

        self.designvariable_name = "DesignVariables"
        self.func_manager_name = "FunctionsManager"
        self.heat_techno_list = self.heat_mix_uc.energy_list
        self.heatmix_name = 'EnergyMix'
        self.year_start = self.heat_mix_uc.year_start
        self.year_end = self.heat_mix_uc.year_end
        self.years = self.heat_mix_uc.years
        # last year where we want to modify our invest share, after that we compute only consequences of investment made before this year
        self.end_decision_year = 2050
        # By default, initialize share values defined in self.setup_dvar .
        self.init_from_subusecase = False
        # by default, does not use bsplines
        self.bspline_poles_number = len(self.years)

    def create_study_list(self):
        self.sub_study_dict = {}
        self.sub_study_path_dict = {}
        for energy in self.energy_list:
            cls, path = self.get_energy_mix_study_cls(energy)
            self.sub_study_dict[energy] = cls
            self.sub_study_path_dict[energy] = path
    def setup_usecase(self):
        if self.init_from_subusecase is True and self.bspline_poles_number != len(self.years):
            raise ValueError(
                f'To init Share values from the values defined in the subusecases, bsplines must have {len(self.years)} poles. '
                'Otherwise set self.init_from_subusecase=False to initiatize Share values as defined in '
                'usecase_portfolio_optim_subprocess')
        # self.heat_mix_uc.study_name = f'{self.study_name}.{self.coupling_name}'
        heat_mix_data_list = self.heat_mix_uc.setup_usecase()
        self.techno_asset_dict = self.heat_mix_uc.techno_dict
        setup_data_list = heat_mix_data_list

        values_dict = self.setup_limit_and_ranges_for_constraints()
        # setup of the optimisation functions that will be used

        self.setup_dvar(heat_mix_data_list)
        # buildd the func_df depending on objectives names and namespaces
        self.func_df = self.setup_objectives()

        values_dict[f'{self.study_name}.{self.func_manager_name}.{FUNC_DF}'] = self.func_df
        values_dict[
            f'{self.study_name}.{self.designvariable_name}.design_var_descriptor'] = self.design_var_descriptor

        # Update the design space to fit the sstructure
        dspace_df_columns = ['variable', 'value', 'lower_bnd',
                             'upper_bnd', 'enable_variable']
        dspace_df = pd.DataFrame(columns=dspace_df_columns)
        for key, elem in self.dspace.items():
            dict_var = {'variable': key}
            dict_var.update(elem)
            dspace_df = dspace_df.append(dict_var, ignore_index=True)
        self.dspace = dspace_df
        values_dict[f'{self.study_name}.design_space'] = self.dspace

        # Update all values_dict before the update dm
        setup_data_list.append(values_dict)
        setup_data_list.append(self.dv_arrays_dict)

        return setup_data_list

    def setup_limit_and_ranges_for_constraints(self):

        values_dict = {}
        # TODO: update as values change...
        target_year = 2050
        # +10% of prod in 2030 compared to 2023
        target_prod_percentage = 10.0
        target_year_prod = 2030

        # -20% of CO2emissions in 2030 compared to 2023
        target_co2_percentage = -20.
        target_year_CO2 = 2030

        if self.init_from_subusecase:
            co2_init = 1729452.4396839456  # tCO2 taken from study usecase in GUI
            prod_init = 8.042841404  # TWh taken from study usecase in GUI
        else:
            co2_init = 5.904083e6  # tCO2 taken from study usecase in GUI EAP_initial_point_7t15a
            prod_init = 21.23988  # TWh taken from study usecase in GUI EAP_initial_point_7t15a

        # prod2030 -prod2023/(2030-2023) = (1.1*prod2023 - prod2023
        prod_growth_rate = (prod_init * target_prod_percentage / 100.) / (target_year_prod - self.year_start)
        co2_growth_rate = (co2_init * target_co2_percentage / 100.) / (target_year_CO2 - self.year_start)
        years = self.heat_mix_uc.years
        prod_limit = prod_growth_rate * (years[1:] - years[0]) + prod_init
        co2_limit = co2_growth_rate * (years[1:] - years[0]) + co2_init
        values_dict.update({
            f"{self.heat_mix_uc.ns_functions}.{Glossary.ComputeOptimisationFunctions['var_name']}": True,
            f"{self.heat_mix_uc.ns_functions}.{Glossary.TargetYear['var_name']}": target_year,
            f"{self.heat_mix_uc.ns_functions}.{Glossary.NPVFunctionRange['var_name']}": np.array([1.e4,
                                                                                                   -3.231e4]),
            f"{self.heat_mix_uc.ns_functions}.{Glossary.CumulativeInvestmentFunctionRange['var_name']}": np.array(
                [0., 8.423e4]),
            f"{self.heat_mix_uc.ns_functions}.{Glossary.CO2EmissionsFunctionRange['var_name']}": np.array(
                [0.0,
                 co2_init / 100.]),
            f"{self.heat_mix_uc.ns_functions}.{Glossary.EnergyProductionFunctionRange['var_name']}": np.array(
                [0.,
                 -prod_init / 100.]),
            f"{self.heat_mix_uc.ns_functions}.{Glossary.CO2EmissionsIncrementsFunctionRange['var_name']}": np.array(
                [0.,
                 -co2_growth_rate]),
            f"{self.heat_mix_uc.ns_functions}.{Glossary.EnergyProductionIncrementsFunctionRange['var_name']}": np.array(
                [0.,
                 -prod_growth_rate]),
            # its a delta so we have 1 value less than the number of years
            f"{self.heat_mix_uc.ns_functions}.{Glossary.CO2EmissionsIncrementsGrowthRate['var_name']}": np.array(
                [co2_growth_rate] * (len(self.years) - 1)),
            f"{self.heat_mix_uc.ns_functions}.{Glossary.EnergyProductionIncrementsGrowthRate['var_name']}": np.array(
                [prod_growth_rate] * (len(self.years) - 1)),

            f"{self.heat_mix_uc.ns_functions}.{Glossary.EnergyProductionFunctionLimit['var_name']}": np.array(
                [prod_init] + list(prod_limit)),
            f"{self.heat_mix_uc.ns_functions}.{Glossary.CO2EmissionsFunctionLimit['var_name']}": np.array(
                [co2_init] + list(co2_limit)),
        })
        return values_dict

    def setup_dvar(self, asset_mix_data_list):
        # initiate all dicts
        self.dspace = {}

        self.dv_arrays_dict = {}

        self.design_var_descriptor = {}

        self.share_percentage_init = {

            # Gas Turbine
            'Ohio': np.array([40.] * self.bspline_poles_number),
            'New York': np.array([60.] * self.bspline_poles_number),
            'Mirepoix': np.array([100.] * self.bspline_poles_number),
            # CCGas Turbine
            'Fort Myers': np.array([100.] * self.bspline_poles_number),
            'Peterhead': np.array([20.] * self.bspline_poles_number),
            # Nuclear
            'Byron': np.array([20.] * self.bspline_poles_number),
            'Hinkley point C': np.array([1.e-6] * self.bspline_poles_number),
            'EPR2': np.array([1.e-6] * self.bspline_poles_number),
            # SolarPv
            'New York': np.array([10.] * self.bspline_poles_number),
            'Solar Star': np.array([1.e-6] * self.bspline_poles_number),
            'Sweihan': np.array([1.e-6] * self.bspline_poles_number),
            # WindOnShore
            'Milligan 1': np.array([40.] * self.bspline_poles_number),
            # WindOffShore
            'Dudgeon': np.array([50.] * self.bspline_poles_number),
            'London Array': np.array([30.] * self.bspline_poles_number),
            # Coalfired
            'Cordemais': np.array([70.] * self.bspline_poles_number)}

        # # we deactivate year start then it is not a decision year
        # decision_time = self.end_decision_year - self.year_start - 1 + 1
        # lower and upper bound for share percentage 0 to 100

        lower_bound = np.ones(self.bspline_poles_number) * 1e-6
        upper_bound = np.ones(self.bspline_poles_number) * 100.
        # Activate only element before the end year decision time and deactivate first year
        activated_elem = [False] + [True] * (self.bspline_poles_number - 1)
        # activated_elem = [True] * self.bspline_poles_number
        for techno, techno_asset_list in self.techno_asset_dict.items():
            for asset in techno_asset_list:

                if self.init_from_subusecase:
                    # initial_value comes from subsub usecases for each techno
                    sharepercentage_key = f"{self.study_name}.{self.coupling_name}.{self.assetmix_name}.{techno}.{Glossary.SharePercentage['var_name']}"
                    init_value_df = asset_mix_data_list[0][sharepercentage_key]
                    value_bspline = init_value_df[init_value_df[Glossary.AssetName] == asset][
                        Glossary.ShareValue].values
                else:
                    value_bspline = self.share_percentage_init[asset]

                design_var_name = f'{techno}.{asset}.share_design_var'
                self.dspace[design_var_name] = {'value': value_bspline,
                                                'lower_bnd': lower_bound, 'upper_bnd': upper_bound,
                                                'enable_variable': True, 'activated_elem': activated_elem}
                # Add design var _value in the dm for the subprocess to work (no need in optim usecase)
                activated_value = np.array(
                    [elem for i, elem in enumerate(self.dspace[design_var_name]['value']) if activated_elem[i]])
                self.dv_arrays_dict[
                    f'{self.study_name}.{self.coupling_name}.{self.assetmix_name}.{design_var_name}'] = activated_value
                # Build the design var descriptor for each variable
                self.design_var_descriptor[f'{techno}.{asset}.share_design_var'] = {
                    'out_name': f"{techno}.{Glossary.SharePercentage['var_name']}",
                    'out_type': 'dataframe',
                    'key': f'{asset}',
                    'index': self.years,
                    'index_name': 'years',
                    'namespace_in': Glossary.NS_MIX_NAME,
                    'namespace_out': Glossary.NS_MIX_NAME,
                    DesignVarDiscipline.DATAFRAME_FILL: DesignVarDiscipline.DATAFRAME_FILL_POSSIBLE_VALUES[1],
                    DesignVarDiscipline.COLUMNS_NAMES: [Glossary.AssetName, Glossary.ShareValue]
                }

    def setup_objectives(self):
        '''

        Method to setup the objectives in the func_df, Weight is one for both to start

        '''
        func_df = pd.DataFrame(
            columns=['variable', 'parent', 'ftype', 'weight', AGGR_TYPE, 'namespace'])
        func_df['variable'] = [Glossary.CumulativeInvestmentFunction['var_name'],
                               Glossary.NPVFunction['var_name'],
                               Glossary.CO2EmissionsFunction['var_name'],
                               Glossary.EnergyProductionFunction['var_name'],
                               Glossary.CO2EmissionsIncrementsFunction['var_name'],
                               Glossary.EnergyProductionIncrementsFunction['var_name']
                               ]
        func_df['parent'] = [OBJECTIVE_LAGR, OBJECTIVE_LAGR, '', '', '', '']  # no parent constraint for the constraints
        func_df['ftype'] = [
            OBJECTIVE, OBJECTIVE, INEQ_CONSTRAINT, INEQ_CONSTRAINT, INEQ_CONSTRAINT, INEQ_CONSTRAINT]
        func_df['weight'] = [4.0, 1.0, 1.0, 1.0, 1.0,
                             1.0]  # fonctions are normalized so that constraints are met when c<0
        # -1 for the prod constraint in order to have c<0 --> dprod > growth_rate = dprod-growth_rate>0 so -1
        func_df[AGGR_TYPE] = [AGGR_TYPE_SUM, AGGR_TYPE_SUM, AGGR_TYPE_SMAX, AGGR_TYPE_SMAX, AGGR_TYPE_SMAX,
                              AGGR_TYPE_SMAX]  # obj_func and constraints are scalars => no impact
        func_df['namespace'] = [Glossary.CumulativeInvestmentFunction['namespace'],
                                Glossary.NPVFunction['namespace'],
                                Glossary.CO2EmissionsFunction['namespace'],
                                Glossary.EnergyProductionFunction['namespace'],
                                Glossary.CO2EmissionsIncrementsFunction['namespace'],
                                Glossary.EnergyProductionIncrementsFunction['namespace']
                                ]

        return func_df


if '__main__' == __name__:
    uc_cls = Study()
    uc_cls.load_data()
    uc_cls.run()
    # start_time = time.time()
    # for i in range(0, 100):
    #     uc_cls.end_decision_year += 2030 + round(random.random())
    #     uc_cls.run()
    # end_time = time.time()
    # print(f'## Wall clock time = {(end_time - start_time)/100.} [s]')
