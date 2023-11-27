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
from copy import deepcopy

import numpy as np
import pandas as pd

from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
from energy_models.core.techno_type.disciplines.electricity_techno_disc import ElectricityTechnoDiscipline
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.electricity.wind_offshore.wind_offshore import WindOffshore
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import TwoAxesInstanciatedChart, \
    InstanciatedSeries


class WindOffshoreDiscipline(ElectricityTechnoDiscipline):
    """**EnergyModelsDiscipline** is the :class:`~gems.core.discipline.MDODiscipline`
    implementing the computation of Energy Models outputs."""

    # ontology information
    _ontology_data = {
        'label': 'Offshore Wind Energy Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-fan fa-fw',
        'version': '',
    }
    techno_name = 'WindOffshore'
    lifetime = 30  # ATB NREL 2020
    construction_delay = 3  # ATB NREL 2020

    techno_infos_dict_default = {'maturity': 0,
                                 'Opex_percentage': 0.022,  # ATB NREL 2020, average value
                                 'WACC': 0.052,  # Weighted averaged cost of capital / ATB NREL 2020
                                 'learning_rate': 0.07,  # Cost development of low carbon energy technologies
                                 'lifetime': lifetime,
                                 'lifetime_unit': GlossaryEnergy.Years,
                                 'Capex_init': 4353,  # Irena Future of wind 2019
                                 'Capex_init_unit': '$/kW',
                                 'full_load_hours': 8760.0,  # Full year hours
                                 'capacity_factor': 0.43,  # Irena Future of wind 2019
                                 'capacity_factor_at_year_end': 0.54,  # Irena Future of wind 2019
                                 'techno_evo_eff': 'no',
                                 'efficiency': 1.0,
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 GlossaryEnergy.ConstructionDelay: construction_delay,
                                 'copper_needs': 8000, #IEA Executive summary - Role of critical minerals in clean energy transitions 2022
                                 }

    techno_info_dict = techno_infos_dict_default
    # Initial production in TWh at year_start, 28.9 GW / GWEC
    # Annual-Wind-Report_2019_digital_final_2r
    # initial_production = 0.0289 * techno_infos_dict_default['full_load_hours'] * \
    #     techno_infos_dict_default['capacity_factor']
    initial_production = 89  # IEA in 2019
    # Invest in 2019 => 29.6 bn
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), GlossaryEnergy.InvestValue: [21.6, 25.6, 29.6]})

    # Age distribution => GWEC Annual-Wind-Report_2019_digital_final_2r
    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': [
                                                 21.1073, 15.2249, 15.5709, 7.61246, 11.7647, 5.53633, 5.19031, 4.15225,
                                                 3.11419, 3.11419, 2.07612, 1.38408, 1.03806, 0.34602, 0.34602,
                                                 0.34602, 1.03806, 0.69204, 0.34602, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    ]
    })

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'age': ('int', [0, 100], False),
                                                                'distrib': ('float', None, True)},
                                       'dataframe_edition_locked': False},
               GlossaryEnergy.InvestmentBeforeYearStartValue: {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int', [-20, -1], False),
                                                                 GlossaryEnergy.InvestValue: ('float', None, True)},
                                        'dataframe_edition_locked': False}}
    # -- add specific techno outputs to this
    DESC_IN.update(ElectricityTechnoDiscipline.DESC_IN)
    # Add specific transport cost for Offshore technology
    DESC_IN = deepcopy(DESC_IN)
    DESC_IN[GlossaryEnergy.TransportCostValue]['visibility'] = ElectricityTechnoDiscipline.LOCAL_VISIBILITY

    DESC_OUT = ElectricityTechnoDiscipline.DESC_OUT

    _maturity = 'Research'

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = WindOffshore(self.techno_name)
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