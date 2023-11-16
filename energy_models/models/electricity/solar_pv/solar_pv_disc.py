'''
Copyright 2022 Airbus SAS

Modifications on 2023/09/19-2023/11/09 Copyright 2023 Capgemini

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
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
from energy_models.models.electricity.solar_pv.solar_pv import SolarPv
from energy_models.core.techno_type.disciplines.electricity_techno_disc import ElectricityTechnoDiscipline
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import TwoAxesInstanciatedChart, \
    InstanciatedSeries


class SolarPvDiscipline(ElectricityTechnoDiscipline):
    """**EnergyModelsDiscipline** is the :class:`~gems.core.discipline.MDODiscipline`
    implementing the computation of Energy Models outputs."""

    # ontology information
    _ontology_data = {
        'label': 'Solar Photovoltaic Energy Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-solar-panel fa-fw',
        'version': '',
    }
    techno_name = 'SolarPv'
    lifetime = 25  # IRENA, EOLES model
    construction_delay = 1
    # Source for Opex percentage, Capex init, capacity factor:
    # IEA 2022, World Energy Outlook 2019,
    # https://www.iea.org/reports/world-energy-outlook-2019, License: CC BY
    # 4.0.
    techno_infos_dict_default = {'maturity': 0,
                                 'product': 'electricity',
                                 'Opex_percentage': 0.021,  # Mean of IEA 2019, EOLES data and others
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 'fuel_demand': 0.0,
                                 'fuel_demand_unit': 'kWh/kWh',
                                 'elec_demand': 0.0,
                                 'elec_demand_unit': 'kWh/kWh',
                                 'heat_demand': 0.0,
                                 'heat_demand_unit': 'kWh/kgCO2',
                                 'WACC': 0.075,  # Weighted averaged cost of capital. Source IRENA
                                 'learning_rate':  0.18,  # IEA 2011
                                 'lifetime': lifetime,  # should be modified
                                 'lifetime_unit': GlossaryCore.Years,
                                 'Capex_init': 1077,  # IEA 2019 Mean of regional value
                                 'Capex_init_unit': '$/kW',
                                 'efficiency': 1.0,  # No need of efficiency here
                                 'full_load_hours': 8760,  # 1577, #Source Audi ?
                                 'water_demand': 0.0,
                                 'water_demand_unit': '',
                                 # IEA Average annual capacity factors by
                                 # technology, 2018 10-21%, IRENA 2019: 18%
                                 'capacity_factor': 0.2,
                                 'density_per_ha': 315059,
                                 'density_per_ha_unit': 'kWh/ha',
                                 'transport_cost_unit': '$/kg',  # check if pertient
                                 'techno_evo_eff': 'no',
                                 GlossaryCore.EnergyEfficiency: 1.0,
                                 GlossaryCore.ConstructionDelay: construction_delay, 
                                 'copper_needs': 2822, #IEA Executive summary - Role of critical minerals in clean energy transitions 2022
                                 }

    techno_info_dict = techno_infos_dict_default
    initial_production = 700  # in TWh at year_start source IEA 2019
    # Invest before year start in $ source IEA 2019
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), GlossaryCore.InvestValue: [108.0]})

    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': [20.4, 18.8, 15.2, 10.1, 8.0, 7.6, 5.9, 6, 3.4, 1.5, 1.3, 0.25, 0.19, 0.18,
                                                         0.17, 0.16, 0.15, 0.14, 0.13, 0.12, 0.10, 0.1, 0.1, 0.01]
                                             })

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'age': ('int',  [0, 100], False),
                                                                'distrib': ('float',  None, True)},
                                       'dataframe_edition_locked': False},
               GlossaryCore.InvestmentBeforeYearStartValue: {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int',  [-20, -1], False),
                                                                 GlossaryCore.InvestValue: ('float',  None, True)},
                                        'dataframe_edition_locked': False}}
    # -- add specific techno outputs to this
    DESC_IN.update(ElectricityTechnoDiscipline.DESC_IN)

    DESC_OUT = ElectricityTechnoDiscipline.DESC_OUT

    _maturity = 'Research'

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = SolarPv(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
    
    def get_charts_consumption_and_production(self):
        "Adds the chart specific for resources needed for construction"
        instanciated_chart = super().get_charts_consumption_and_production()
        techno_consumption = self.get_sosdisc_outputs(
            GlossaryCore.TechnoDetailedConsumptionValue)

        new_chart_copper = None
        for product in techno_consumption.columns:

            if product != GlossaryCore.Years and product.endswith(f'(Mt)'):
                if ResourceGlossary.Copper['name'] in product :
                    chart_name = f'Mass consumption of copper for the {self.techno_name} technology with input investments'
                    new_chart_copper = TwoAxesInstanciatedChart(
                        GlossaryCore.Years, 'Mass [t]', chart_name=chart_name, stacked_bar=True)

        for reactant in techno_consumption.columns:
            if ResourceGlossary.Copper['name'] in reactant:
                legend_title = f'{reactant} consumption'.replace(
                    ' (Mt)', "")
                mass = techno_consumption[reactant].values * 1000 * 1000 #convert Mt in t for more readable post-proc
                serie = InstanciatedSeries(
                    techno_consumption[GlossaryCore.Years].values.tolist(),
                    mass.tolist(), legend_title, 'bar')
                new_chart_copper.series.append(serie)
        instanciated_chart.append(new_chart_copper)
        
        return instanciated_chart
