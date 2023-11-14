'''
Copyright 2022 Airbus SAS
Modifications on 2023/09/19-2023/11/03 Copyright 2023 Capgemini

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
import pandas as pd
import numpy as np

from climateeconomics.glossarycore import GlossaryCore
from energy_models.models.carbon_capture.direct_air_capture.calcium_potassium_scrubbing.calcium_potassium_scrubbing import CalciumPotassium
from energy_models.core.techno_type.disciplines.carbon_capture_techno_disc import CCTechnoDiscipline


class CalciumPotassiumScrubbingDiscipline(CCTechnoDiscipline):
    """**EnergyModelsDiscipline** is the :class:`~gems.core.discipline.MDODiscipline`
    implementing the computation of Energy Models outputs."""

    # ontology information
    _ontology_data = {
        'label': 'Calcium Potassium Scrubbing Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-globe-europe fa-fw',
        'version': '',
    }
    techno_name = 'direct_air_capture.CalciumPotassiumScrubbing'
    lifetime = 35
    construction_delay = 3
    techno_infos_dict_default = {'maturity': 0,
                                 'reaction_part_1': 'CO2 + 2KOH --> H2O + K2CO3',
                                 'reaction_part_2': 'K2CO3 + Ca(OH)2 --> 2KOH + CaCO3',
                                 'reaction_part_2': 'CaCO3 (calciner)--> CaO +CO2',
                                 'Opex_percentage': 0.04,
                                 'elec_demand': 0.1,
                                 'elec_demand_unit': 'kWh/kgCO2',
                                 # Fasihi, M., Efimova, O. and Breyer, C., 2019.
                                 # Techno-economic assessment of CO2 direct air capture plants.
                                 # Journal of cleaner production, 224, pp.957-980.
                                 # for now constant in time but should increase
                                 # with time 10%/10year according to Fasihi2019
                                 'heat_demand': 1.75,
                                 'heat_demand_unit': 'kWh/kgCO2',
                                 'WACC': 0.1,  # Weighted averaged cost of capital for the carbon capture plant
                                 'learning_rate': 0.1,
                                 'maximum_learning_capex_ratio': 0.5,
                                 'lifetime': lifetime,  # should be modified
                                 'lifetime_unit': GlossaryCore.Years,
                                 'Capex_init': 0.8,  #
                                 'Capex_init_unit': '$/kgCO2',
                                 'efficiency': 0.9,
                                 'CO2_capacity_peryear': 1.0E+9,  # kg CO2 /year
                                 'CO2_capacity_peryear_unit': 'kg CO2/year',
                                 'real_factor_CO2': 1.0,
                                 GlossaryCore.TransportCostValue: 0.0,
                                 'transport_cost_unit': '$/kgCO2',
                                 # Keith, D.W., Holmes, G., Angelo, D.S. and Heidel, K., 2018.
                                 # A process for capturing CO2 from the atmosphere.
                                 # Joule, 2(8), pp.1573-1594.
                                 # Vo, T.T., Wall, D.M., Ring, D., Rajendran, K. and Murphy, J.D., 2018.
                                 # Techno-economic analysis of biogas upgrading via amine scrubber, carbon capture and ex-situ methanation.
                                 # Applied energy, 212, pp.1191-1202.
                                 # from Keith2018 3.18 GJ/tCaO in theory 5.25
                                 # GJ/tCO2 in practice (Climeworks)
                                 # according to Vo2018 4GJ/tCO2 or Fasihi2016:
                                 # 1.51 in practice
                                 'enthalpy': 1.124,
                                 'enthalpy_unit': 'kWh/kgC02',
                                 GlossaryCore.EnergyEfficiency: 0.78,
                                 GlossaryCore.ConstructionDelay: construction_delay,
                                 'techno_evo_eff': 'no',
                                 'calcium_refound_efficiency': 0.98,
                                 'potassium_refound_efficiency': 0.98,
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 }

    techno_info_dict = techno_infos_dict_default

    initial_capture = 5.0e-3  # in Mt at year_start
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), GlossaryCore.InvestValue: np.array([0.05093, 0.05093, 15.0930]) * 0.8 / 3000})

    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': [10.0, 10.0, 10.0, 10.0, 10.0,
                                                         10.0, 10.0, 10.0,
                                                         10.0, 10.0, 0.0,
                                                         0.0, 0.0, 0.0,
                                                         0.0, 0.0, 0.0,
                                                         0.0, 0.0, 0.0,
                                                         0.0, 0.0, 0.0,
                                                         0.0, 0.0, 0.0,
                                                         0.0, 0.0, 0.0,
                                                         0.0, 0.0, 0.0,
                                                         0.0, 0.0]
                                             })

    # use the same flue gas ratio as gas turbine one
    FLUE_GAS_RATIO = np.array([0.0350])
    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_production': {'type': 'float', 'unit': 'MtCO2', 'default': initial_capture},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'age': ('int',  [0, 100], False),
                                                                'distrib': ('float',  None, True)},
                                       'dataframe_edition_locked': False},
               GlossaryCore.InvestmentBeforeYearStartValue: {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int',  [-20, -1], False),
                                                                 GlossaryCore.InvestValue: ('float',  None, True)},
                                        'dataframe_edition_locked': False}}
    # -- add specific techno outputs to this
    DESC_IN.update(CCTechnoDiscipline.DESC_IN)

    DESC_OUT = CCTechnoDiscipline.DESC_OUT

    _maturity = 'Research'

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = CalciumPotassium(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)

    def compute_sos_jacobian(self):
        # Grad of price vs energyprice
        CCTechnoDiscipline.compute_sos_jacobian(self)

        grad_dict = self.techno_model.grad_price_vs_energy_price()
        grad_dict_resources = self.techno_model.grad_price_vs_resources_price()
        carbon_emissions = self.get_sosdisc_outputs(GlossaryCore.CO2EmissionsValue)
        self.set_partial_derivatives_techno(
            grad_dict, carbon_emissions, grad_dict_resources)
