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
from sos_trades_core.study_manager.study_manager import StudyManager
from importlib import import_module
from sos_trades_core.tools.bspline.bspline_methods import bspline_method

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

from energy_models.sos_processes.energy.techno_mix.methane_mix.usecase import TECHNOLOGIES_LIST_FOR_OPT as Methane_technos
from energy_models.sos_processes.energy.techno_mix.gaseous_hydrogen_mix.usecase import TECHNOLOGIES_LIST_FOR_OPT as GaseousHydrogen_technos
from energy_models.sos_processes.energy.techno_mix.gaseous_hydrogen_mix.usecase import TECHNOLOGIES_LIST_COARSE_MIN_TECH as gaseoushydrogen_technos_coarse_integration
from energy_models.sos_processes.energy.techno_mix.biogas_mix.usecase import TECHNOLOGIES_LIST_FOR_OPT as BioGas_technos
from energy_models.sos_processes.energy.techno_mix.syngas_mix.usecase import TECHNOLOGIES_LIST_FOR_OPT as Syngas_technos
from energy_models.sos_processes.energy.techno_mix.syngas_mix.usecase import TECHNOLOGIES_LIST_COARSE_MIN_TECH as syngas_technos_coarse_integration

from energy_models.sos_processes.energy.techno_mix.liquid_fuel_mix.usecase import TECHNOLOGIES_LIST_FOR_OPT as LiquidFuel_technos
from energy_models.sos_processes.energy.techno_mix.liquid_fuel_mix.usecase import TECHNOLOGIES_LIST_COARSE_MIN_TECH as liquidfuel_technos_coarse_integration
from energy_models.sos_processes.energy.techno_mix.hydrotreated_oil_fuel_mix.usecase import TECHNOLOGIES_LIST_FOR_OPT as HydrotreatedOilFuel_technos
from energy_models.sos_processes.energy.techno_mix.solid_fuel_mix.usecase import TECHNOLOGIES_LIST_FOR_OPT as SolidFuel_technos
from energy_models.sos_processes.energy.techno_mix.solid_fuel_mix.usecase import TECHNOLOGIES_LIST_COARSE_MIN_TECH as solidfuel_technos_coarse_integration
from energy_models.sos_processes.energy.techno_mix.biomass_dry_mix.usecase import TECHNOLOGIES_LIST_FOR_OPT as BiomassDry_technos
from energy_models.sos_processes.energy.techno_mix.electricity_mix.usecase import TECHNOLOGIES_LIST_FOR_OPT as Electricity_technos
from energy_models.sos_processes.energy.techno_mix.electricity_mix.usecase import TECHNOLOGIES_LIST_COARSE_MIN_TECH as electricity_technos_coarse_integration
from energy_models.sos_processes.energy.techno_mix.biodiesel_mix.usecase import TECHNOLOGIES_LIST_FOR_OPT as BioDiesel_technos
from energy_models.sos_processes.energy.techno_mix.liquid_hydrogen_mix.usecase import TECHNOLOGIES_LIST_FOR_OPT as LiquidHydrogen_technos
from energy_models.sos_processes.energy.techno_mix.carbon_capture_mix.usecase import TECHNOLOGIES_LIST_FOR_OPT as CarbonCapture_technos
from energy_models.sos_processes.energy.techno_mix.carbon_storage_mix.usecase import TECHNOLOGIES_LIST_FOR_OPT as CarbonStorage_technos
from energy_models.core.stream_type.energy_models.renewable import Renewable
from energy_models.sos_processes.energy.techno_mix.renewable_mix.usecase import TECHNOLOGIES_LIST_FOR_OPT as Renewable_technos
from energy_models.sos_processes.energy.techno_mix.renewable_mix.usecase import TECHNOLOGIES_LIST_FOR_OPT as Renewable_technos

from energy_models.core.stream_type.energy_models.fossil import Fossil
from energy_models.sos_processes.energy.techno_mix.electricity_mix.usecase import TECHNOLOGIES_LIST_FOR_OPT_COARSE as Electricity_technos_coarse
from energy_models.sos_processes.energy.techno_mix.carbon_capture_mix.usecase import TECHNOLOGIES_FLUE_GAS_LIST_COARSE as CarbonCapture_technos_coarse
from energy_models.sos_processes.energy.techno_mix.methane_mix.usecase import TECHNOLOGIES_LIST_FOR_OPT_COARSE as Methane_technos_coarse
from energy_models.sos_processes.energy.techno_mix.electricity_mix.usecase import TECHNOLOGIES_LIST_FOR_OPT_COARSE_0 as Electricity_technos_coarse_0
from energy_models.sos_processes.energy.techno_mix.electricity_mix.usecase import TECHNOLOGIES_LIST_FOR_OPT_COARSE_3 as Electricity_technos_coarse_3

import numpy as np
from sos_trades_core.tools.base_functions.specific_check import specific_check_years


ENERGY_TYPE = 'energy'
CCUS_TYPE = 'CCUS'
DEFAULT_TECHNO_DICT = {Methane.name: {'type': ENERGY_TYPE, 'value': Methane_technos},
                       GaseousHydrogen.name: {'type': ENERGY_TYPE, 'value': GaseousHydrogen_technos},
                       BioGas.name: {'type': ENERGY_TYPE, 'value': BioGas_technos},
                       Syngas.name: {'type': ENERGY_TYPE, 'value': Syngas_technos},
                       LiquidFuel.name: {'type': ENERGY_TYPE, 'value': LiquidFuel_technos},
                       HydrotreatedOilFuel.name: {'type': ENERGY_TYPE, 'value': HydrotreatedOilFuel_technos},
                       SolidFuel.name: {'type': ENERGY_TYPE, 'value': SolidFuel_technos},
                       BiomassDry.name: {'type': ENERGY_TYPE, 'value': BiomassDry_technos},
                       Electricity.name: {'type': ENERGY_TYPE, 'value': Electricity_technos},
                       BioDiesel.name: {'type': ENERGY_TYPE, 'value': BioDiesel_technos},
                       LiquidHydrogen.name: {'type': ENERGY_TYPE, 'value': LiquidHydrogen_technos},
                       CarbonCapture.name: {'type': CCUS_TYPE, 'value': CarbonCapture_technos},
                       CarbonStorage.name: {'type': CCUS_TYPE, 'value': CarbonStorage_technos}}

DEFAULT_TECHNO_DICT_DEV = {Methane.name: {'type': ENERGY_TYPE, 'value': Methane_technos},
                           GaseousHydrogen.name: {'type': ENERGY_TYPE, 'value': GaseousHydrogen_technos},
                           BioGas.name: {'type': ENERGY_TYPE, 'value': BioGas_technos},
                           Syngas.name: {'type': ENERGY_TYPE, 'value': Syngas_technos},
                           LiquidFuel.name: {'type': ENERGY_TYPE, 'value': LiquidFuel_technos},
                           HydrotreatedOilFuel.name: {'type': ENERGY_TYPE, 'value': HydrotreatedOilFuel_technos},
                           SolidFuel.name: {'type': ENERGY_TYPE, 'value': SolidFuel_technos},
                           BiomassDry.name: {'type': ENERGY_TYPE, 'value': BiomassDry_technos},
                           Electricity.name: {'type': ENERGY_TYPE, 'value': Electricity_technos},
                           BioDiesel.name: {'type': ENERGY_TYPE, 'value': BioDiesel_technos},
                           LiquidHydrogen.name: {'type': ENERGY_TYPE, 'value': LiquidHydrogen_technos},
                           CarbonCapture.name: {'type': CCUS_TYPE, 'value': CarbonCapture_technos},
                           CarbonStorage.name: {'type': CCUS_TYPE, 'value': CarbonStorage_technos}}

DEFAULT_COARSE_TECHNO_DICT = {'renewable': {'type': ENERGY_TYPE, 'value': ['RenewableSimpleTechno']},
                              'fossil': {'type': ENERGY_TYPE, 'value': ['FossilSimpleTechno']},
                              'carbon_capture': {'type': CCUS_TYPE, 'value': ['direct_air_capture.DirectAirCaptureTechno', 'flue_gas_capture.FlueGasTechno']},
                              'carbon_storage': {'type': CCUS_TYPE, 'value': ['CarbonStorageTechno']}}

DEFAULT_COARSE_TECHNO_DICT_elec = {Electricity.name: {'type': ENERGY_TYPE, 'value': Electricity_technos_coarse},
                                   'fossil': {'type': ENERGY_TYPE, 'value': ['FossilSimpleTechno']},
                                   'carbon_capture': {'type': CCUS_TYPE, 'value': ['direct_air_capture.CalciumPotassiumScrubbing', 'flue_gas_capture.CalciumLooping']},
                                   'carbon_storage': {'type': CCUS_TYPE, 'value': ['CarbonStorageTechno']}}

DEFAULT_COARSE_TECHNO_DICT_ccs = {Electricity.name: {'type': ENERGY_TYPE, 'value': Electricity_technos_coarse_0},
                                  'fossil': {'type': ENERGY_TYPE, 'value': ['FossilSimpleTechno']},
                                  'carbon_capture': {'type': CCUS_TYPE, 'value': CarbonCapture_technos},
                                  'carbon_storage': {'type': CCUS_TYPE, 'value': CarbonStorage_technos}}

DEFAULT_COARSE_TECHNO_DICT_ccs_05 = {Electricity.name: {'type': ENERGY_TYPE, 'value': Electricity_technos_coarse},
                                     'fossil': {'type': ENERGY_TYPE, 'value': ['FossilSimpleTechno']},
                                     'carbon_capture': {'type': CCUS_TYPE, 'value': CarbonCapture_technos},
                                     'carbon_storage': {'type': CCUS_TYPE, 'value': CarbonStorage_technos}}

DEFAULT_COARSE_TECHNO_DICT_ccs_2 = {Electricity.name: {'type': ENERGY_TYPE, 'value': Electricity_technos_coarse},
                                    LiquidFuel.name: {'type': ENERGY_TYPE, 'value': ['Refinery']},
                                    Methane.name: {'type': ENERGY_TYPE, 'value': ['FossilGas']},
                                    SolidFuel.name: {'type': ENERGY_TYPE, 'value': ['CoalExtraction']},
                                    'carbon_capture': {'type': CCUS_TYPE, 'value': CarbonCapture_technos},
                                    'carbon_storage': {'type': CCUS_TYPE, 'value': CarbonStorage_technos}}

DEFAULT_COARSE_TECHNO_DICT_ccs_3 = {Electricity.name: {'type': ENERGY_TYPE, 'value': Electricity_technos_coarse_3},
                                    LiquidFuel.name: {'type': ENERGY_TYPE, 'value': ['Refinery']},
                                    Methane.name: {'type': ENERGY_TYPE, 'value': ['FossilGas']},
                                    SolidFuel.name: {'type': ENERGY_TYPE, 'value': ['CoalExtraction']},
                                    'carbon_capture': {'type': CCUS_TYPE, 'value': CarbonCapture_technos},
                                    'carbon_storage': {'type': CCUS_TYPE, 'value': CarbonStorage_technos}}

DEFAULT_MIN_TECH_DICT = {Electricity.name: {'type': ENERGY_TYPE, 'value': electricity_technos_coarse_integration},
                         LiquidFuel.name: {'type': ENERGY_TYPE, 'value': ['Refinery']},
                         SolidFuel.name: {'type': ENERGY_TYPE, 'value': solidfuel_technos_coarse_integration},
                         BiomassDry.name: {'type': ENERGY_TYPE, 'value': BiomassDry_technos},
                         Syngas.name: {'type': ENERGY_TYPE, 'value': syngas_technos_coarse_integration},
                         LiquidHydrogen.name: {'type': ENERGY_TYPE, 'value': LiquidHydrogen_technos},
                         GaseousHydrogen.name: {'type': ENERGY_TYPE, 'value': gaseoushydrogen_technos_coarse_integration},
                         Methane.name: {'type': ENERGY_TYPE, 'value': ['FossilGas']},
                                'carbon_capture': {'type': CCUS_TYPE, 'value': ['direct_air_capture.AmineScrubbing', 'flue_gas_capture.MonoEthanolAmine']},
                                'carbon_storage': {'type': CCUS_TYPE, 'value': ['PureCarbonSolidStorage', 'Reforestation']}}

# DEFAULT_MIN_TECH_DEV_DICT, same as DEFAULT_MIN_TECH_DICT but with deepSalineFormation into carbon_storage
DEFAULT_MIN_TECH_DEV_DICT = {Electricity.name: {'type': ENERGY_TYPE, 'value': electricity_technos_coarse_integration},
                         LiquidFuel.name: {'type': ENERGY_TYPE, 'value': ['Refinery']},
                         SolidFuel.name: {'type': ENERGY_TYPE, 'value': solidfuel_technos_coarse_integration},
                         BiomassDry.name: {'type': ENERGY_TYPE, 'value': BiomassDry_technos},
                         Syngas.name: {'type': ENERGY_TYPE, 'value': syngas_technos_coarse_integration},
                         LiquidHydrogen.name: {'type': ENERGY_TYPE, 'value': LiquidHydrogen_technos},
                         GaseousHydrogen.name: {'type': ENERGY_TYPE, 'value': gaseoushydrogen_technos_coarse_integration},
                         Methane.name: {'type': ENERGY_TYPE, 'value': ['FossilGas']},
                                'carbon_capture': {'type': CCUS_TYPE, 'value': ['direct_air_capture.AmineScrubbing', 'flue_gas_capture.MonoEthanolAmine']},
                                'carbon_storage': {'type': CCUS_TYPE, 'value': ['PureCarbonSolidStorage', 'Reforestation', 'DeepSalineFormation']}}

DEFAULT_ENERGY_LIST = [key for key, value in DEFAULT_TECHNO_DICT.items(
) if value['type'] == 'energy']
DEFAULT_CCS_LIST = [key for key, value in DEFAULT_TECHNO_DICT.items(
) if value['type'] == 'CCUS']


class EnergyStudyManager(StudyManager):
    '''
    classdocs
    '''

    def __init__(self, file_path, run_usecase=True, main_study=True, execution_engine=None, techno_dict=DEFAULT_TECHNO_DICT):
        '''
        Constructor
        '''
        super().__init__(file_path, run_usecase=run_usecase, execution_engine=execution_engine)
        self.main_study = main_study
        self.techno_dict = techno_dict
        self.energy_list = [key for key, value in self.techno_dict.items(
        ) if value['type'] == 'energy']
        self.ccs_list = [key for key, value in self.techno_dict.items(
        ) if value['type'] == 'CCUS']

    def get_energy_mix_study_cls(self, energy_name, add_name=None):
        dot_split = energy_name.split('.')  # -- case hydrogen.liquid_hydrogen
        lower_name = dot_split[-1].lower()
        if add_name is None:
            path = 'energy_models.sos_processes.energy.techno_mix.' + \
                lower_name + '_mix.usecase'
        else:
            path = 'energy_models.sos_processes.energy.techno_mix.' + \
                lower_name + f'_{add_name}' + '_mix.usecase' + f'_{add_name}'
        study_cls = getattr(import_module(path), 'Study')
        return study_cls, path

    def invest_bspline(self, ctrl_pts, len_years):
        '''
        Method to evaluate investment per year from control points
        '''

        return bspline_method(ctrl_pts, len_years)

    def specific_check(self):
        # check all elements of data dict
        specific_check_years(self.execution_engine.dm)
