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
'''
mode: python; py-indent-offset: 4; tab-width: 8; coding: utf-8
'''
import pandas as pd
import numpy as np

from energy_models.core.techno_type.disciplines.electricity_techno_disc import ElectricityTechnoDiscipline
from energy_models.models.electricity.gas.biogas_fired.biogas_fired import BiogasFired
from sos_trades_core.tools.post_processing.charts.two_axes_instanciated_chart import TwoAxesInstanciatedChart, \
    InstanciatedSeries
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary


class BiogasFiredDiscipline(ElectricityTechnoDiscipline):

    # ontology information
    _ontology_data = {
        'label': 'Biogas Fired Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-burn fa-fw',
        'version': '',
    }

    techno_name = 'BiogasFired'
    lifetime = 20   # Value for CHP units
    construction_delay = 2  # years

    # IEA 2022, Data Tables,
    # https://www.iea.org/data-and-statistics/data-tables?country=WORLD&energy=Renewables%20%26%20waste&year=2019
    # License: CC BY 4.0.
    # Gross. elec. prod.: 88751 GWh
    # Electricity plants consumption: 448717 TJ net -> 448717 / 3.6 GWh
    biogas_needs = (448717 / 3.6) / 88751  # ratio without dimension

    # IRENA Power Generation Cost 2019 Report
    # https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2020/Jun/IRENA_Power_Generation_Costs_2019.pdf
    # pages 110 to 119

    techno_infos_dict_default = {'maturity': 5,
                                 # IRENA (mean of 2% - 6%)
                                 'Opex_percentage': 0.04,
                                 'WACC': 0.075,
                                 'learning_rate': 0,
                                 'lifetime': lifetime,
                                 'lifetime_unit': 'years',
                                 # IRENA (value from Figure 7.1, page 111)
                                 'Capex_init': 2141,
                                 'Capex_init_unit': '$/kW',
                                 # IRENA (value from Figure 7.1, page 111)
                                 'capacity_factor': 0.70,
                                 'biogas_needs': biogas_needs,
                                 'efficiency': 1,
                                 'techno_evo_eff': 'no',  # yes or no
                                 'construction_delay': construction_delay,
                                 'full_load_hours': 8760,
                                 'copper_needs': 1100,  #no data, assuming it needs at least enough copper for a generator (such as the gas_turbine)
                                 }

    # Source: IEA 2022, Data and Statistics,
    # https://www.iea.org/data-and-statistics/charts/biogas-installed-power-generation-capacity-2010-2018
    # License: CC BY 4.0.
    # (17.7-9.4)/8 = 1.0375 GW per year increase
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), 'invest': [1.0375 * 2141 / 1000, 1.0375 * 2141 / 1000]})
    # In G$

    # Source for Initial prod in TWh (2019):
    # IEA 2022, Data Tables,
    # https://www.iea.org/data-and-statistics/data-tables?country=WORLD&energy=Renewables%20%26%20waste&year=2019
    # License: CC BY 4.0.
    initial_production = 88.751

    # Source: IEA 2022, Data and Statistics
    # https://www.iea.org/data-and-statistics/charts/biogas-installed-power-generation-capacity-2010-2018
    # License: CC BY 4.0.
    # (17.7-9.4)/8 = 1.0375 GW per year increase
    # 1.0375 / 17.7 ~= 5.8% added production each year (linear approximation)
    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': [100 - 17 * 5.8, 5.8, 5.8, 5.8, 5.8,
                                                         5.8, 5.8, 5.8, 5.8, 5.8,
                                                         5.8, 5.8, 5.8, 5.8, 5.8,
                                                         5.8, 5.8, 5.8, 0.0]})

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'age': ('int',  [0, 100], False),
                                                                'distrib': ('float',  None, True)},
                                       'dataframe_edition_locked': False},
               'invest_before_ystart': {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int',  [-20, -1], False),
                                                                 'invest': ('float',  None, True)},
                                        'dataframe_edition_locked': False},
               }
    # -- add specific techno inputs to this
    DESC_IN.update(ElectricityTechnoDiscipline.DESC_IN)

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = BiogasFired(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
    
    def get_charts_consumption_and_production(self):
        "Adds the chart specific for resources needed for construction"
        instanciated_chart = super().get_charts_consumption_and_production()
        techno_consumption = self.get_sosdisc_outputs(
            'techno_detailed_consumption')

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
        instanciated_chart.append(new_chart_copper)

        return instanciated_chart
