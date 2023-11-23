'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2023/11/16 Copyright 2023 Capgemini

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

from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
from energy_models.core.techno_type.disciplines.electricity_techno_disc import ElectricityTechnoDiscipline
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.electricity.hydropower.hydropower import Hydropower
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import TwoAxesInstanciatedChart, \
    InstanciatedSeries


class HydropowerDiscipline(ElectricityTechnoDiscipline):
    """**EnergyModelsDiscipline** is the :class:`~gems.core.discipline.MDODiscipline`
    implementing the computation of Energy Models outputs."""

    # ontology information
    _ontology_data = {
        'label': 'Hydropower Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-water fa-fw',
        'version': '',
    }
    techno_name = 'Hydropower'
    lifetime = 50
    construction_delay = 3
    techno_infos_dict_default = {'type': 'electricity_creation',
                                 'maturity': 0,
                                 'product': 'electricity',
                                 # IRENA, 2021
                                 # Renewable Power Generation Costs in 2020
                                 # https://www.irena.org/publications/2021/Jun/Renewable-Power-Costs-in-2020
                                 'Opex_percentage': 0.025,
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 'electricity': 'hydropower',
                                 'WACC': 0.075,  # Weighted averaged cost of capital for the carbon capture plant
                                 'lifetime': lifetime,  # should be modified
                                 'lifetime_unit': GlossaryEnergy.Years,
                                 'Capex_init': 1704,  # IRENA
                                 'Capex_init_unit': '$/kW',
                                 'full_load_hours': 8760.0,
                                 'capacity_factor': 0.46,  # IRENA
                                 'efficiency': 1.0,  # No need of efficiency here
                                 GlossaryEnergy.ConstructionDelay: construction_delay,
                                 'learning_rate': 0.0,
                                 'techno_evo_eff': 'no',
                                 'copper_needs': 1100,  #no data, assuming it needs at least enough copper for a generator (such as the gas_turbine)
                                  }

    techno_info_dict = techno_infos_dict_default

    initial_production = 4222.0  # in TWh at year_start source IEA 2019
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), GlossaryEnergy.InvestValue: [2.5, 2.5, 2.5
                                                                     ]})

    # Global power plant database 2018, https://github.com/wri/global-power-plant-database
    # Also in
    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime + 1),
                                             'distrib': [0.05, 0.94, 2.06, 2.78, 2.33, 3.28, 4.00, 3.82, 3.95, 3.46, 3.28, 2.30, 2.47, 1.75, 1.61, 1.75, 1.71, 1.40, 1.13, 1.40, 1.40, 1.13, 1.31, 1.58, 2.16, 2.30, 1.76, 1.53, 2.16, 2.70, 2.97, 2.57, 3.38, 3.20, 2.34, 2.16, 2.12, 1.58, 1.49, 1.26, 1.67, 1.04, 0.72, 1.62, 1.08, 1.53, 0.86, 1.17, 2.16, 1.58]})

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'age': ('int',  [0, 100], False),
                                                                'distrib': ('float',  None, True)},
                                       'dataframe_edition_locked': False},
               GlossaryEnergy.InvestmentBeforeYearStartValue: {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int',  [-20, -1], False),
                                                                 GlossaryEnergy.InvestValue: ('float',  None, True)},
                                        'dataframe_edition_locked': False}}
    # -- add specific techno outputs to this
    DESC_IN.update(ElectricityTechnoDiscipline.DESC_IN)

    DESC_OUT = ElectricityTechnoDiscipline.DESC_OUT

    _maturity = 'Research'

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = Hydropower(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)

    def get_charts_consumption_and_production(self):
        "Adds the chart specific for resources needed for construction"
        instanciated_chart = super().get_charts_consumption_and_production()
        techno_consumption = self.get_sosdisc_outputs(
            GlossaryEnergy.TechnoDetailedConsumptionValue)

        new_chart_copper = None
        for product in techno_consumption.columns:

            if product != GlossaryEnergy.Years and product.endswith(f'(Mt)'):
                if ResourceGlossary.Copper['name'] in product :
                    chart_name = f'Mass consumption of copper for the {self.techno_name} technology with input investments'
                    new_chart_copper = TwoAxesInstanciatedChart(
                        GlossaryEnergy.Years, 'Mass [t]', chart_name=chart_name, stacked_bar=True)

        for reactant in techno_consumption.columns:
            if ResourceGlossary.Copper['name'] in reactant:
                legend_title = f'{reactant} consumption'.replace(
                    ' (Mt)', "")
                mass = techno_consumption[reactant].values * 1000 * 1000 #convert Mt in t for more readable post-proc
                serie = InstanciatedSeries(
                    techno_consumption[GlossaryEnergy.Years].values.tolist(),
                    mass.tolist(), legend_title, 'bar')
                new_chart_copper.series.append(serie)
        instanciated_chart.append(new_chart_copper)
        
        return instanciated_chart