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

import pandas as pd
import numpy as np
from energy_models.core.techno_type.disciplines.electricity_techno_disc import ElectricityTechnoDiscipline
from energy_models.models.electricity.nuclear.nuclear import Nuclear
from energy_models.core.stream_type.ressources_models.water import Water
from sos_trades_core.tools.post_processing.charts.two_axes_instanciated_chart import TwoAxesInstanciatedChart, \
    InstanciatedSeries


class NuclearDiscipline(ElectricityTechnoDiscipline):
    """**EnergyModelsDiscipline** is the :class:`~gems.core.discipline.MDODiscipline`
    implementing the computation of Energy Models outputs."""

    techno_name = 'Nuclear'
    # Cole, W.J., Gates, N., Mai, T.T., Greer, D. and Das, P., 2020.
    # 2019 standard scenarios report: a US electric sector outlook (No. NREL/PR-6A20-75798).
    # National Renewable Energy Lab.(NREL), Golden, CO (United States).
    lifetime = 60
    # Timilsina, G.R., 2020. Demystifying the Costs of Electricity Generation
    # Technologies., average
    construction_delay = 6

    techno_infos_dict_default = {'maturity': 0,
                                 'Opex_percentage': 0.024,
                                 # Fixed 1.9 and recurrent 0.5 %
                                 # Demystifying-the-Costs-of-Electricity-Generation-Technologies, average
                                 'WACC': 0.058,  # Weighted averaged cost of capital / ATB NREL 2020
                                 'learning_rate': 0.00,  # Cost development of low carbon energy technologies
                                 'lifetime': lifetime,
                                 'lifetime_unit': 'years',
                                 # Demystifying-the-Costs-of-Electricity-Generation-Technologies, average
                                 'Capex_init': 6765,
                                 'Capex_init_unit': '$/kW',
                                 'full_load_hours': 8760.0,  # Full year hours
                                 # Demystifying-the-Costs-of-Electricity-Generation-Technologies, average
                                 'capacity_factor': 0.90,
                                 'techno_evo_eff': 'no',
                                 'efficiency': 1.0,
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 'construction_delay': construction_delay,
                                 'waste_disposal_levy': 0.1 * 1e-2 * 1e3,   # conversion from c/kWh to $/MWh
                                 'decommissioning_percentage': 0.15 / lifetime,
                                 # World Nuclear Waste Report 2019, Chapter 6 (https://worldnuclearwastereport.org)
                                 # average of 1000 $/kW
                                 }

    techno_info_dict = techno_infos_dict_default
    # Initial production in TWh at year_start IAEA - IAEA_Energy Electricity
    # and Nuclear Power Estimates up to 2050
    initial_production = 2657.0
    # Invest in 2019 => 29.6 bn
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), 'invest': [30.0, 29.0, 33.0,
                                                                     34.0, 33.0, 39.0]})

    # Age distribution => IAEA OPEX Nuclear 2020 - Number of Reactors by Age
    # (as of 1 January 2020)
    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': [
                                                 1.36, 2.04, 0.91, 2.27, 2.27, 1.13, 0.91, 0.68, 1.59, 1.13, 0.45, 0.68,
                                                 0.45, 0.91, 1.13, 0.45, 1.36, 0.68, 1.36, 0.91, 0.91, 0.68, 1.36, 0.91,
                                                 1.13, 2.04, 1.36, 0.91, 2.27, 2.49, 3.17, 4.76, 5.22, 7.26, 6.80, 3.85,
                                                 3.40, 4.31, 4.08, 1.13, 2.04, 1.59, 3.17, 2.27, 3.40, 2.04, 1.59, 1.36,
                                                 0.68, 1.15, 0, 0, 0, 0, 0, 0, 0, 0, 0
    ]
    })

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default},
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'age': ('int',  [0, 100], False),
                                                                'distrib': ('float',  None, True)},
                                       'dataframe_edition_locked': False},
               'invest_before_ystart': {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int',  [-20, -1], False),
                                                                 'invest': ('float',  None, True)},
                                        'dataframe_edition_locked': False}}
    # -- add specific techno outputs to this
    DESC_IN.update(ElectricityTechnoDiscipline.DESC_IN)

    DESC_OUT = ElectricityTechnoDiscipline.DESC_OUT

    _maturity = 'Research'

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = Nuclear(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)

    def get_charts_consumption_and_production(self):
        instanciated_charts = []
        # Charts for consumption and prod
        techno_consumption = self.get_sosdisc_outputs(
            'techno_detailed_consumption')
        techno_production = self.get_sosdisc_outputs(
            'techno_detailed_production')
        chart_name = f'Energy Production and consumption of the {self.techno_name} technology with input investments'

        new_chart = TwoAxesInstanciatedChart('years', 'Energy [TWh]',
                                             chart_name=chart_name, stacked_bar=True)

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

        new_chart_water = None
        new_chart_uranium = None
        for product in techno_consumption.columns:

            if product != 'years' and product.endswith(f'(Mt)'):
                if Water.name in product:
                    chart_name = f'Mass consumption of water for the Nuclear technology with input investments'
                    new_chart_water = TwoAxesInstanciatedChart(
                        'years', 'Mass [Gt]', chart_name=chart_name, stacked_bar=True)
                else:
                    chart_name = f'Mass consumption of uranium for the Nuclear technology with input investments'
                    new_chart_uranium = TwoAxesInstanciatedChart(
                        'years', 'Mass [tons]', chart_name=chart_name, stacked_bar=True)

        for reactant in techno_consumption.columns:
            if Water.name in reactant:
                legend_title = f'water consumption'.replace(
                    ' (Mt)', "")
                # 1GT = 1e9T = 1e12 kg
                mass = techno_consumption[reactant].values
                serie = InstanciatedSeries(
                    techno_consumption['years'].values.tolist(),
                    mass.tolist(), legend_title, 'bar')
                new_chart_water.series.append(serie)
            elif 'years' not in reactant:
                legend_title = f'{reactant} consumption'.replace(
                    f' (Mt)', "")
                # 1T= 10e6Mt
                mass = techno_consumption[reactant].values
                serie = InstanciatedSeries(
                    techno_consumption['years'].values.tolist(),
                    mass.tolist(), legend_title, 'bar')
                new_chart_uranium.series.append(serie)

        instanciated_charts.append(new_chart_water)
        instanciated_charts.append(new_chart_uranium)

        return instanciated_charts
