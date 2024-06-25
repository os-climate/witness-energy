'''
Copyright 2022 Airbus SAS
Modifications on 2023/04/19-2024/06/24 Copyright 2023 Capgemini

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

from sostrades_core.study_manager.study_manager import StudyManager
from sostrades_core.tools.base_functions.specific_check import specific_check_years
from sostrades_core.tools.bspline.bspline_methods import bspline_method

from energy_models.glossaryenergy import GlossaryEnergy

ENERGY_TYPE = "energy"
CCUS_TYPE = GlossaryEnergy.CCUS
AGRI_TYPE = "agriculture"


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
            techno_dict={},
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
        self.coarse_mode: bool = set(self.techno_dict.keys()) == set(GlossaryEnergy.DEFAULT_COARSE_TECHNO_DICT.keys())
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

    def specific_check_inputs(self):
        # check all elements of data dict
        specific_check_years(self.execution_engine.dm)
