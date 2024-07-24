'''
Copyright 2022 Airbus SAS
Modifications on 2023/09/19-2023/11/16 Copyright 2023 Capgemini

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

from energy_models.core.stream_type.energy_models.methane import Methane
from energy_models.core.techno_type.disciplines.solid_fuel_techno_disc import (
    SolidFuelTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.solid_fuel.coal_extraction.coal_extraction import (
    CoalExtraction,
)


class CoalExtractionDiscipline(SolidFuelTechnoDiscipline):
    """**EnergyModelsDiscipline** is the :class:`~gems.core.discipline.MDODiscipline`
    implementing the computation of Energy Models outputs."""

    # ontology information
    _ontology_data = {
        'label': 'Coal Extraction Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-cube fa-fw',
        'version': '',
    }
    techno_name = GlossaryEnergy.CoalExtraction
    lifetime = 35
    construction_delay = 3

    # Most coal seams are too deep underground for opencast mining and require
    # underground mining, a method that currently accounts for about 60
    # percent of world coal production. Wikipedia source :
    # https://en.wikipedia.org/wiki/Coal_mining
    # https://globalenergymonitor.org/wp-content/uploads/2021/03/Coal-Mine-Methane-On-the-Brink.pdf
    # Gas content mean for surface mining is 2.25m3/t
    # Gas content mean for underground mining is 11.5m3/t
    techno_infos_dict_default = {'maturity': 0,
                                 'product': '',
                                 'Opex_percentage': 0.20,
                                 # Pandey, B., Gautam, M. and Agrawal, M., 2018.
                                 # Greenhouse gas emissions from coal mining activities and their possible mitigation strategies.
                                 # In Environmental carbon footprints (pp.
                                 # 259-294). Butterworth-Heinemann.
                                 'CO2_from_production': 0.64,
                                 'CO2_from_production_unit': 'kg/kg',
                                 'underground_mining_gas_content': 11.5,
                                 'surface_mining_gas_content': 2.25,
                                 'gas_content_unit': 'm3/t',
                                 'underground_mining_percentage': 60.,
                                 'emission_factor_coefficient': 1.6,
                                 'ch4_from_abandoned_mines': 15.,
                                 'ch4_from_abandoned_mines_unit': 'Mt',
                                 'fuel_demand': 0.0040,
                                 'fuel_demand_unit': 'kWh/kWh',
                                 # CF : Crude oil refinery on bibliography folder
                                 # ratio elec use / kerosene product
                                 'elec_demand': 0.01,
                                 'elec_demand_unit': 'kWh/kWh',
                                 GlossaryEnergy.electricity: 'solar',
                                 'heat_demand': 0.0,
                                 'heat_demand_unit': 'kWh/kWh',
                                 'WACC': 0.1,  # Weighted averaged cost of capital for the carbon capture plant
                                 'learning_rate': 0.0,  # 0.15,
                                 'lifetime': lifetime,  # should be modified
                                 # Estimating average total cost of open pit coal mines in Australia
                                 # Average : 5Mtcoal/year for 258M Australian$
                                 #  -- 1AU$ = 0.77$
                                 'Capex_init': 0.0083,
                                 'Capex_init_unit': '$/kWh',
                                 'efficiency': 1.0,  # No need of efficiency here
                                 'CO2_capacity_peryear': 3.6E+8,  # kg CO2 /year
                                 'CO2_capacity_peryear_unit': 'kg CO2/year',
                                 'real_factor_CO2': 1.0,
                                 'water_demand': 0.0,
                                 'water_demand_unit': '',
                                 'produced_energy': 0.0,
                                 'direct_energy': 0.0,
                                 GlossaryEnergy.TransportCostValue: 0.0,
                                 'transport_cost_unit': '$/kgcoal',
                                 'enthalpy': 0.0,
                                 'techno_evo_eff': 'no',
                                 'enthalpy_unit': 'kWh/m^3',
                                 GlossaryEnergy.EnergyEfficiency: 1.0,
                                 GlossaryEnergy.ConstructionDelay: construction_delay,
                                 'pourcentage_of_total': 0.09,
                                 'energy_burn': 'no'}

    techno_info_dict = techno_infos_dict_default

    energy_own_use = 952.78  # TWh
    # From ourworldindata
    initial_production = 43752. - energy_own_use
    # First invest is zero to get exactly the initial production in 2020
    
    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime - 1),
                                             'distrib': [2.49, 0.55, 0.0, 0.0, 2.64, 0.55, 6.75, 6.74, 0.0, 1.97, 7.87,
                                                         7.34, 10.19, 9.47, 11.9, 5.55, 2.3, 4.8, 0.89, 0.0, 0.0, 3.42,
                                                         1.02, 0.56, 0.71, 0.0, 0.0, 0.0, 1.39, 3.21, 3.0, 1.65, 3.04]
                                             })

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'age': ('int', [0, 100], False),
                                                                'distrib': ('float', None, True)},
                                       'dataframe_edition_locked': False},
               }
    # -- add specific techno outputs to this
    DESC_IN.update(SolidFuelTechnoDiscipline.DESC_IN)

    DESC_OUT = SolidFuelTechnoDiscipline.DESC_OUT

    _maturity = 'Research'

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = CoalExtraction(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)

    def compute_sos_jacobian(self):
        SolidFuelTechnoDiscipline.compute_sos_jacobian(self)

        # the generic gradient for production column is not working because of
        # abandoned mines not proportional to production

        scaling_factor_invest_level, scaling_factor_techno_production = self.get_sosdisc_inputs(
            ['scaling_factor_invest_level', 'scaling_factor_techno_production'])
        applied_ratio = self.get_sosdisc_outputs(
            'applied_ratio')['applied_ratio'].values

        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoProductionValue,
             f'{Methane.emission_name} ({GlossaryEnergy.mass_unit})'),
            (GlossaryEnergy.InvestLevelValue, GlossaryEnergy.InvestValue),
            (
                        self.dprod_dinvest.T * self.techno_model.emission_factor_mt_twh * applied_ratio).T * scaling_factor_invest_level / scaling_factor_techno_production)
