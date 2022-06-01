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
from copy import deepcopy

import pandas as pd
import numpy as np
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
from energy_models.core.techno_type.disciplines.electricity_techno_disc import ElectricityTechnoDiscipline
from energy_models.models.electricity.wind_offshore.wind_offshore import WindOffshore
from sos_trades_core.tools.post_processing.charts.two_axes_instanciated_chart import TwoAxesInstanciatedChart, \
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
                                 'lifetime_unit': 'years',
                                 'Capex_init': 4353,  # Irena Future of wind 2019
                                 'Capex_init_unit': '$/kW',
                                 'full_load_hours': 8760.0,  # Full year hours
                                 'capacity_factor': 0.43,  # Irena Future of wind 2019
                                 'capacity_factor_at_year_end': 0.54,  # Irena Future of wind 2019
                                 'techno_evo_eff': 'no',
                                 'efficiency': 1.0,
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 'construction_delay': construction_delay, }

    techno_info_dict = techno_infos_dict_default
    # Initial production in TWh at year_start, 28.9 GW / GWEC
    # Annual-Wind-Report_2019_digital_final_2r
    # initial_production = 0.0289 * techno_infos_dict_default['full_load_hours'] * \
    #     techno_infos_dict_default['capacity_factor']
    initial_production = 89  # IEA in 2019
    # Invest in 2019 => 29.6 bn
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), 'invest': [21.6, 25.6, 29.6]})

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
               'invest_before_ystart': {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int', [-20, -1], False),
                                                                 'invest': ('float', None, True)},
                                        'dataframe_edition_locked': False}}
    # -- add specific techno outputs to this
    DESC_IN.update(ElectricityTechnoDiscipline.DESC_IN)
    # Add specific transport cost for Offshore technology
    DESC_IN = deepcopy(DESC_IN)
    DESC_IN['transport_cost']['visibility'] = ElectricityTechnoDiscipline.LOCAL_VISIBILITY

    DESC_OUT = ElectricityTechnoDiscipline.DESC_OUT

    _maturity = 'Research'

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = WindOffshore(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)

    def get_charts_consumption_and_production(self):
        instanciated_charts = []
        # Charts for consumption and prod
        techno_consumption = self.get_sosdisc_outputs(
            'techno_detailed_consumption')
        techno_production = self.get_sosdisc_outputs(
            'techno_detailed_production')
        chart_name = f'{self.techno_name} technology energy Production & consumption<br>with input investments'

        new_chart = TwoAxesInstanciatedChart('years', 'Energy [TWh]',
                                             chart_name=chart_name.capitalize(), stacked_bar=True)

        for reactant in techno_consumption.columns:
            if reactant != 'years' and reactant.endswith('(TWh)'):
                energy_twh = -techno_consumption[reactant].values
                legend_title = f'{reactant} consumption'.replace(
                    "(TWh)", "")
                serie = InstanciatedSeries(
                    techno_consumption['years'].values.tolist(),
                    energy_twh.tolist(), legend_title, 'bar')

                new_chart.series.append(serie)

        for products in techno_production.columns:
            if products != 'years' and products.endswith('(TWh)'):
                energy_twh = techno_production[products].values
                legend_title = f'{products} production'.replace(
                    "(TWh)", "")
                serie = InstanciatedSeries(
                    techno_production['years'].values.tolist(),
                    energy_twh.tolist(), legend_title, 'bar')

                new_chart.series.append(serie)
        instanciated_charts.append(new_chart)

        new_chart_copper = None
        for product in techno_consumption.columns:

            if product != 'years' and product.endswith(f'(Mt)'):
                if ResourceGlossary.Copper['name'] in product :
                    chart_name = f'Mass consumption of copper for the {self.techno_name} technology with input investments'
                    new_chart_copper = TwoAxesInstanciatedChart(
                        'years', 'Mass [t]', chart_name=chart_name, stacked_bar=True)

        for reactant in techno_consumption.columns:
            if ResourceGlossary.Copper['name'] in reactant:
                legend_title = f'{reactant} consumption'.replace(
                    ' (Mt)', "")
                mass = techno_consumption[reactant].values * 1000 * 1000 #convert Mt in t for more readable post-proc
                serie = InstanciatedSeries(
                    techno_consumption['years'].values.tolist(),
                    mass.tolist(), legend_title, 'bar')
                new_chart_copper.series.append(serie)

        instanciated_charts.append(new_chart_copper)

        return instanciated_charts