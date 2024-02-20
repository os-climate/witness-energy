'''
Copyright 2022 Airbus SAS
Modifications on 2023/04/19-2023/11/16 Copyright 2023 Capgemini

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
from importlib import import_module

from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.core.stream_type.carbon_models.carbon_storage import CarbonStorage
from energy_models.core.stream_type.carbon_models.carbon_utilization import CarbonUtilization
from energy_models.core.stream_type.energy_models.biodiesel import BioDiesel
from energy_models.core.stream_type.energy_models.biogas import BioGas
from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.stream_type.energy_models.ethanol import Ethanol
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import (
    GaseousHydrogen,
)
from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from energy_models.core.stream_type.energy_models.heat import lowtemperatureheat
from energy_models.core.stream_type.energy_models.heat import mediumtemperatureheat
from energy_models.core.stream_type.energy_models.hydrotreated_oil_fuel import (
    HydrotreatedOilFuel,
)
from energy_models.core.stream_type.energy_models.liquid_fuel import LiquidFuel
from energy_models.core.stream_type.energy_models.liquid_hydrogen import LiquidHydrogen
from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.stream_type.energy_models.solid_fuel import SolidFuel
from energy_models.core.stream_type.energy_models.syngas import Syngas
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.sos_processes.energy.techno_mix.biodiesel_mix.usecase import (
    TECHNOLOGIES_LIST_DEV as BioDiesel_technos_dev,
)
from energy_models.sos_processes.energy.techno_mix.biogas_mix.usecase import (
    TECHNOLOGIES_LIST_DEV as BioGas_technos_dev,
)
from energy_models.sos_processes.energy.techno_mix.biomass_dry_mix.usecase import (
    TECHNOLOGIES_LIST_DEV as BiomassDry_technos_dev,
)
from energy_models.sos_processes.energy.techno_mix.carbon_capture_mix.usecase import (
    TECHNOLOGIES_LIST_DEV as CarbonCapture_technos_dev,
)
from energy_models.sos_processes.energy.techno_mix.carbon_utilization_mix.usecase import (
    TECHNOLOGIES_LIST_DEV as CarbonUtilization_technos_dev,
)

from energy_models.sos_processes.energy.techno_mix.carbon_storage_mix.usecase import (
    TECHNOLOGIES_LIST_DEV as CarbonStorage_technos_dev,
)

from energy_models.sos_processes.energy.techno_mix.electricity_mix.usecase import (
    TECHNOLOGIES_LIST_DEV as Electricity_technos_dev,
)
from energy_models.sos_processes.energy.techno_mix.ethanol_mix.usecase import (
    TECHNOLOGIES_LIST_DEV as Ethanol_technos_dev,
)
from energy_models.sos_processes.energy.techno_mix.gaseous_hydrogen_mix.usecase import (
    TECHNOLOGIES_LIST_DEV as GaseousHydrogen_technos_dev,
)
from energy_models.sos_processes.energy.techno_mix.hightemperatureheat_mix.usecase import (
    TECHNOLOGIES_LIST_DEV as hightemperatureheat_technos_dev,
)
from energy_models.sos_processes.energy.techno_mix.hydrotreated_oil_fuel_mix.usecase import (
    TECHNOLOGIES_LIST_DEV as HydrotreatedOilFuel_technos_dev,
)
from energy_models.sos_processes.energy.techno_mix.liquid_fuel_mix.usecase import (
    TECHNOLOGIES_LIST_DEV as LiquidFuel_technos_dev,
)
from energy_models.sos_processes.energy.techno_mix.liquid_hydrogen_mix.usecase import (
    TECHNOLOGIES_LIST_DEV as LiquidHydrogen_technos_dev,
)
from energy_models.sos_processes.energy.techno_mix.lowtemperatureheat_mix.usecase import (
    TECHNOLOGIES_LIST_DEV as lowtemperatureheat_technos_dev,
)
from energy_models.sos_processes.energy.techno_mix.mediumtemperatureheat_mix.usecase import (
    TECHNOLOGIES_LIST_DEV as mediumtemperatureheat_technos_dev,
)
from energy_models.sos_processes.energy.techno_mix.methane_mix.usecase import (
    TECHNOLOGIES_LIST_DEV as Methane_technos_dev,
)
from energy_models.sos_processes.energy.techno_mix.solid_fuel_mix.usecase import (
    TECHNOLOGIES_LIST_DEV as SolidFuel_technos_dev,
)
from energy_models.sos_processes.energy.techno_mix.syngas_mix.usecase import (
    TECHNOLOGIES_LIST_DEV as Syngas_technos_dev,
)
from sostrades_core.study_manager.study_manager import StudyManager
from sostrades_core.tools.base_functions.specific_check import specific_check_years
from sostrades_core.tools.bspline.bspline_methods import bspline_method


ENERGY_TYPE = 'energy'
CCUS_TYPE = 'CCUS'
AGRI_TYPE = 'agriculture'
DEFAULT_TECHNO_DICT = {Methane.name: {'type': ENERGY_TYPE, 'value': Methane_technos_dev},
                       GaseousHydrogen.name: {'type': ENERGY_TYPE, 'value': GaseousHydrogen_technos_dev},
                       BioGas.name: {'type': ENERGY_TYPE, 'value': BioGas_technos_dev},
                       Syngas.name: {'type': ENERGY_TYPE, 'value': Syngas_technos_dev},
                       LiquidFuel.name: {'type': ENERGY_TYPE, 'value': LiquidFuel_technos_dev},
                       hightemperatureheat.name: {'type': ENERGY_TYPE, 'value': hightemperatureheat_technos_dev},
                       mediumtemperatureheat.name: {'type': ENERGY_TYPE, 'value': mediumtemperatureheat_technos_dev},
                       lowtemperatureheat.name: {'type': ENERGY_TYPE, 'value': lowtemperatureheat_technos_dev},
                       HydrotreatedOilFuel.name: {'type': ENERGY_TYPE, 'value': HydrotreatedOilFuel_technos_dev},
                       SolidFuel.name: {'type': ENERGY_TYPE, 'value': SolidFuel_technos_dev},
                       BiomassDry.name: {'type': AGRI_TYPE, 'value': BiomassDry_technos_dev},
                       Electricity.name: {'type': ENERGY_TYPE, 'value': Electricity_technos_dev},
                       BioDiesel.name: {'type': ENERGY_TYPE, 'value': BioDiesel_technos_dev},
                       Ethanol.name: {'type': ENERGY_TYPE, 'value': Ethanol_technos_dev},
                       LiquidHydrogen.name: {'type': ENERGY_TYPE, 'value': LiquidHydrogen_technos_dev},
                       CarbonCapture.name: {'type': CCUS_TYPE, 'value': CarbonCapture_technos_dev},
                       CarbonStorage.name: {'type': CCUS_TYPE, 'value': CarbonStorage_technos_dev},
                       CarbonUtilization.name: {'type': CCUS_TYPE, 'value': CarbonUtilization_technos_dev},
                       }

DEFAULT_TECHNO_DICT_DEV = {
    Methane.name: {"type": ENERGY_TYPE, "value": Methane_technos_dev},
    GaseousHydrogen.name: {"type": ENERGY_TYPE, "value": GaseousHydrogen_technos_dev},
    BioGas.name: {"type": ENERGY_TYPE, "value": BioGas_technos_dev},
    Syngas.name: {"type": ENERGY_TYPE, "value": Syngas_technos_dev},
    LiquidFuel.name: {"type": ENERGY_TYPE, "value": LiquidFuel_technos_dev},
    hightemperatureheat.name: {
        "type": ENERGY_TYPE,
        "value": hightemperatureheat_technos_dev,
    },
    mediumtemperatureheat.name: {
        "type": ENERGY_TYPE,
        "value": mediumtemperatureheat_technos_dev,
    },
    lowtemperatureheat.name: {
        "type": ENERGY_TYPE,
        "value": lowtemperatureheat_technos_dev,
    },
    HydrotreatedOilFuel.name: {
        "type": ENERGY_TYPE,
        "value": HydrotreatedOilFuel_technos_dev,
    },
    SolidFuel.name: {"type": ENERGY_TYPE, "value": SolidFuel_technos_dev},
    BiomassDry.name: {"type": AGRI_TYPE, "value": BiomassDry_technos_dev},
    Electricity.name: {"type": ENERGY_TYPE, "value": Electricity_technos_dev},
    BioDiesel.name: {"type": ENERGY_TYPE, "value": BioDiesel_technos_dev},
    Ethanol.name: {"type": ENERGY_TYPE, "value": Ethanol_technos_dev},
    LiquidHydrogen.name: {"type": ENERGY_TYPE, "value": LiquidHydrogen_technos_dev},
    CarbonCapture.name: {"type": CCUS_TYPE, "value": CarbonCapture_technos_dev},
    CarbonStorage.name: {"type": CCUS_TYPE, "value": CarbonStorage_technos_dev},
    CarbonUtilization.name: {'type': CCUS_TYPE, 'value': CarbonUtilization_technos_dev},
}

DEFAULT_COARSE_TECHNO_DICT = {
    "renewable": {"type": ENERGY_TYPE, "value": [GlossaryEnergy.RenewableSimpleTechno]},
    GlossaryEnergy.fossil: {"type": ENERGY_TYPE, "value": [GlossaryEnergy.FossilSimpleTechno]},
    "carbon_capture": {
        "type": CCUS_TYPE,
        "value": [GlossaryEnergy.DirectAirCapture, GlossaryEnergy.FlueGasCapture],
    },
    "carbon_storage": {
        "type": CCUS_TYPE,
        "value": [GlossaryEnergy.CarbonStorageTechno],
    },
}

DEFAULT_ENERGY_LIST = [
    key
    for key, value in DEFAULT_TECHNO_DICT.items()
    if value["type"] in ["energy", "agriculture"]
]
DEFAULT_CCS_LIST = [
    key for key, value in DEFAULT_TECHNO_DICT.items() if value["type"] == GlossaryEnergy.CCUS
]

DEFAULT_COARSE_ENERGY_LIST = [
    key
    for key, value in DEFAULT_COARSE_TECHNO_DICT.items()
    if value["type"] in ["energy", "agriculture"]
]
DEFAULT_COARSE_CCS_LIST = [
    key for key, value in DEFAULT_COARSE_TECHNO_DICT.items() if value["type"] == GlossaryEnergy.CCUS
]


class EnergyStudyManager(StudyManager):
    """
    classdocs
    """

    def __init__(
            self,
            file_path,
            run_usecase=True,
            main_study=True,
            execution_engine=None,
            techno_dict=DEFAULT_TECHNO_DICT,
    ):
        """
        Constructor
        """
        super().__init__(
            file_path, run_usecase=run_usecase, execution_engine=execution_engine
        )
        self.main_study = main_study
        self.techno_dict = techno_dict
        self.energy_list = [
            key
            for key, value in self.techno_dict.items()
            if value["type"] in ["energy", "agriculture"]
        ]
        self.coarse_mode: bool = set(self.energy_list) == set(DEFAULT_COARSE_ENERGY_LIST)
        self.ccs_list = [
            key for key, value in self.techno_dict.items() if value["type"] == GlossaryEnergy.CCUS
        ]

    def get_energy_mix_study_cls(self, energy_name, add_name=None):
        dot_split = energy_name.split(".")  # -- case hydrogen.liquid_hydrogen
        lower_name = dot_split[-1].lower()
        if add_name is None:
            path = (
                    "energy_models.sos_processes.energy.techno_mix."
                    + lower_name
                    + "_mix.usecase"
            )
        else:
            path = (
                    "energy_models.sos_processes.energy.techno_mix."
                    + lower_name
                    + f"_{add_name}"
                    + "_mix.usecase"
                    + f"_{add_name}"
            )
        study_cls = getattr(import_module(path), "Study")
        return study_cls, path

    def invest_bspline(self, ctrl_pts, len_years):
        """
        Method to evaluate investment per year from control points
        """

        return bspline_method(ctrl_pts, len_years)

    def specific_check(self):
        # check all elements of data dict
        specific_check_years(self.execution_engine.dm)
